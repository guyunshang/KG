import sys
from pathlib import Path

# 在文件开头添加项目根目录到系统路径
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(BASE_DIR))

import hanlp
import re
from typing import List, Tuple, Optional

# 保留原仓库的配置引用，维持项目一致性
from graphrag_agent.config.settings import CHUNK_SIZE, OVERLAP, MAX_TEXT_LENGTH


class ChineseTextChunker:
    """中文文本分块器：在指定窗口内按句末标点优先截断"""

    def __init__(self, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP, max_text_length: int = MAX_TEXT_LENGTH):
        """
        初始化分块器

        Args:
            chunk_size: 每个文本块的目标大小（tokens数量）
            overlap: 相邻文本块的重叠大小（tokens数量）
            max_text_length: (保留参数以兼容旧接口，新逻辑主要依赖流式处理)
        """
        if chunk_size <= overlap:
            raise ValueError("chunk_size必须大于overlap")

        self.chunk_size = chunk_size
        self.overlap = overlap
        self.max_text_length = max_text_length
        self.tokenizer = hanlp.load(hanlp.pretrained.tok.COARSE_ELECTRA_SMALL_ZH)

        # 句末标点集合：中英文、全角半角
        self._sentence_endings = {
            '。', '！', '？', '!', '?', '．', '.', '；', ';'
        }

    def process_files(self, file_contents: List[Tuple[str, str]]) -> List[Tuple[str, str, List[List[str]]]]:
        """
        处理多个文件的内容
        """
        results = []
        for filename, content in file_contents:
            chunks = self.chunk_text(content)
            results.append((filename, content, chunks))
        return results

    def chunk_text(self, text: str) -> List[List[str]]:
        """
        将单个文本分割成块（逻辑已修改为本地文件的 Buffer 模式，并修复了死循环bug）
        """
        # 处理空文本或太短的文本
        if not text or len(text) < self.chunk_size / 10:
            try:
                tokens = self.tokenizer(text)
                return [tokens] if tokens else []
            except Exception as e:
                print(f"分词失败：{str(e)}")
                # 保留原始文本中的空格
                return [text.split()] if text else []

        paragraphs = text.split('\n')
        chunks: List[List[str]] = []
        buffer: List[str] = []

        # 定义弹性窗口大小：chunk_size + 50
        target_max_size = self.chunk_size + 50

        i = 0
        while i < len(paragraphs):
            # 尽量填满到 target_max_size 附近再决策
            while len(buffer) < target_max_size and i < len(paragraphs):
                try:
                    tokens = self.tokenizer(paragraphs[i])
                    buffer.extend(tokens)
                except Exception as e:
                    print(f"分词失败 ({i}): {str(e)}")
                    buffer.extend(paragraphs[i].split())
                i += 1

            if not buffer:
                continue

            # 只要 buffer 达到最小截断阈值，就尝试按句末切块
            while len(buffer) >= self.chunk_size:
                # 使用动态计算的 max_size (self.chunk_size + 50)
                end_idx = self._find_chunk_boundary(buffer, self.chunk_size, target_max_size)

                # 【安全防护】防止 find_chunk_boundary 返回异常小的索引导致死循环
                if end_idx <= 0:
                    end_idx = self.chunk_size

                chunk = buffer[:end_idx]
                chunks.append(chunk)

                # 计算下一个块的起点：优先在 overlap 前的最近句末对齐
                start_next = self._find_previous_sentence_end(buffer, end_idx - self.overlap)

                # 如果找不到合适的重叠句末，尝试在切分点前找任意句末
                if start_next == 0:
                    start_next = self._find_previous_sentence_end(buffer, end_idx - 1)

                # 如果仍然找不到，直接按 overlap 硬切分
                if start_next == 0:
                    # 如果 end_idx 很小（小于 overlap），这种计算会导致 start_next <= 0
                    if end_idx > self.overlap:
                        start_next = end_idx - self.overlap
                    else:
                        # 如果当前块比重叠区还小，则不重叠，直接从当前位置继续
                        start_next = end_idx

                # 【死循环终极防护】确保 buffer 必定缩减
                if start_next <= 0:
                    # 强制前进一步，防止 buffer 永远不变化导致死循环
                    start_next = 1

                # 截断 buffer，进入下一次循环
                buffer = buffer[start_next:]

        # 收尾处理
        if buffer:
            # 最后一个块尽量也按句末收尾，但不强求
            if len(buffer) > 0:
                final_max = min(target_max_size, len(buffer))
                final_min = min(self.chunk_size, len(buffer))

                # 如果剩余长度小于 chunk_size，直接作为一个块
                if len(buffer) < self.chunk_size:
                    chunks.append(buffer)
                else:
                    end_idx = self._find_chunk_boundary(buffer, min_size=final_min, max_size=final_max)
                    # 同样的兜底检查
                    if end_idx <= 0:
                        end_idx = len(buffer)

                    chunks.append(buffer[:end_idx] if end_idx > 0 else buffer)

        return chunks

    # ================= 工具方法 =================

    def _is_sentence_end(self, token: str) -> bool:
        """判断token是否为句子结束符"""
        return token in self._sentence_endings

    def _find_next_sentence_end(self, tokens: List[str], start_pos: int) -> int:
        """从指定位置向后查找句子结束位置"""
        for i in range(start_pos, len(tokens)):
            if self._is_sentence_end(tokens[i]):
                return i + 1
        return len(tokens)

    def _find_previous_sentence_end(self, tokens: List[str], start_pos: int) -> int:
        """从指定位置向前查找句子结束位置"""
        # 注意边界检查
        if start_pos >= len(tokens):
            start_pos = len(tokens) - 1

        for i in range(start_pos, -1, -1):
            if self._is_sentence_end(tokens[i]):
                return i + 1
        return 0

    def tokens_to_text(self, tokens) -> str:
        """把分词结果拼回字符串，保留英文单词间的空格"""
        if not tokens:
            return ""

        # 预先编译正则表达式以提高效率
        ascii_pattern = re.compile(r'^[a-zA-Z0-9]+$')

        result = []
        prev_is_ascii = False

        for token in tokens:
            # 使用正则表达式快速检查是否为纯ASCII字母数字
            current_is_ascii = bool(ascii_pattern.match(token))

            # 如果前一个token是ASCII且当前也是ASCII，则在它们之间添加空格
            if prev_is_ascii and current_is_ascii:
                result.append(' ')

            result.append(token)
            prev_is_ascii = current_is_ascii

        return ''.join(result)

    def _find_chunk_boundary(self, tokens: List[str], min_size: int, max_size: int) -> int:
        """
        在 [min_size, max_size] 范围内寻找距离 min_size 最近的句末标点。
        """
        n = len(tokens)
        min_size = max(1, min_size)
        max_size = max(min_size, max_size)
        max_size = min(max_size, n)

        # 1) 窗口内从 min_size 向后找
        for i in range(min_size, max_size + 1):
            if i - 1 < n and self._is_sentence_end(tokens[i - 1]):
                return i

        # 2) 向前找最近句末
        prev_end = self._find_previous_sentence_end(tokens, min_size)
        if prev_end > 0:
            return prev_end

        # 3) 兜底：如果没有句末，但在最大范围内，强制截断
        if n >= max_size:
            return max_size

        # 4) 如果还不行，就返回整个长度（通常是最后一段）
        return n