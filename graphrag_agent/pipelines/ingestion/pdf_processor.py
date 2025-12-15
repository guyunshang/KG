import sys
from pathlib import Path
# 在文件开头添加项目根目录到系统路径
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(BASE_DIR))

import fitz
from tqdm import tqdm
from bs4 import BeautifulSoup
import re
import difflib
from typing import Optional

def text_similarity(text1: str, text2: str) -> float:
    """
    计算文本相似度（使用编辑距离和Jaccard相似度结合）
    """
    if not text1 or not text2:
        return 0

    # 如果两个字符串都是纯数字，使用数字相似度计算
    if text1.isdigit() and text2.isdigit():
        num1 = int(text1)
        num2 = int(text2)
        # 数字相差1以内认为是高度相似
        if abs(num1 - num2) <= 1:
            return 1.0
        else:
            return 0.5 if abs(num1 - num2) <= 10 else 0.1

    # 对于非纯数字文本，使用序列匹配器计算相似度
    seq_matcher = difflib.SequenceMatcher(None, text1, text2)
    return seq_matcher.ratio()

def pdf_to_html(input_path: str, header_footer_threshold: float = 0.4) -> str:
    """
    将PDF转换为HTML字符串，识别并过滤页眉页脚
    """
    doc = fitz.open(input_path)
    total_pages = len(doc)

    # 存储所有页面的页眉页脚候选
    header_candidates = []
    footer_candidates = []
    page_widths = []  # 存储每页的宽度

    # 第一遍：收集所有页面的页眉页脚候选
    for page_num, page in enumerate(doc):
        page_rect = page.rect
        page_width = page_rect.width
        page_height = page_rect.height
        page_widths.append(page_width)

        header_region = (0, 0, page_width, page_height * 0.1)  # 顶部10%
        footer_region = (0, page_height * 0.9, page_width, page_height)  # 底部10%

        blocks = page.get_text("dict")["blocks"]

        header_blocks = []
        footer_blocks = []
        header_text = ""
        footer_text = ""

        for block in blocks:
            if block["type"] == 0:  # 文本块
                block_bbox = block["bbox"]
                block_width = block_bbox[2] - block_bbox[0]
                block_y = block_bbox[1]  # 块的Y坐标

                # 检查是否在页眉区域
                if (block_bbox[1] >= header_region[1] and
                        block_bbox[3] <= header_region[3] and
                        block_bbox[3] - block_bbox[1] > 0):
                    block_text = ""
                    for line in block["lines"]:
                        for span in line["spans"]:
                            block_text += span["text"] + " "
                    block_text = block_text.strip()

                    if block_text:
                        header_blocks.append({
                            "text": block_text,
                            "width": block_width,
                            "char_count": len(block_text),
                            "y": block_y
                        })
                        header_text += block_text + " "

                # 检查是否在页脚区域
                elif (block_bbox[1] >= footer_region[1] and
                      block_bbox[3] <= footer_region[3] and
                      block_bbox[3] - block_bbox[1] > 0):
                    block_text = ""
                    for line in block["lines"]:
                        for span in line["spans"]:
                            block_text += span["text"] + " "
                    block_text = block_text.strip()

                    if block_text:
                        footer_blocks.append({
                            "text": block_text,
                            "width": block_width,
                            "char_count": len(block_text),
                            "y": block_y
                        })
                        footer_text += block_text + " "

        header_blocks.sort(key=lambda x: x["y"])
        footer_blocks.sort(key=lambda x: x["y"])

        header_candidates.append({
            "text": header_text.strip(),
            "blocks": header_blocks
        })

        footer_candidates.append({
            "text": footer_text.strip(),
            "blocks": footer_blocks
        })

    # 确定要移除的页眉页脚
    headers_to_remove = set()
    footers_to_remove = set()

    if total_pages == 1:
        # 单页文档的处理逻辑
        page_header = header_candidates[0]
        page_footer = footer_candidates[0]
        page_width = page_widths[0]

        if page_header["blocks"]:
            is_header = True
            for block in page_header["blocks"]:
                if block["width"] >= page_width / 2 or block["char_count"] >= 20:
                    is_header = False
                    break
            if is_header:
                headers_to_remove.add(page_header["text"])

        if page_footer["blocks"]:
            is_footer = True
            for block in page_footer["blocks"]:
                if block["width"] >= page_width / 2 or block["char_count"] >= 20:
                    is_footer = False
                    break
            if is_footer:
                footers_to_remove.add(page_footer["text"])
    else:
        # 多页文档的处理逻辑 - 相邻页对比
        header_representatives = []
        footer_representatives = []

        for i in range(total_pages):
            if header_candidates[i]["blocks"]:
                top_header = min(header_candidates[i]["blocks"], key=lambda x: x["y"])
                header_representatives.append({
                    "text": top_header["text"],
                    "width": top_header["width"],
                    "char_count": top_header["char_count"]
                })
            else:
                header_representatives.append(None)

            if footer_candidates[i]["blocks"]:
                bottom_footer = max(footer_candidates[i]["blocks"], key=lambda x: x["y"])
                footer_representatives.append({
                    "text": bottom_footer["text"],
                    "width": bottom_footer["width"],
                    "char_count": bottom_footer["char_count"]
                })
            else:
                footer_representatives.append(None)

        header_matches = set()
        for i in range(total_pages):
            if header_representatives[i] is None:
                continue
            if i == 0:
                if header_representatives[1] is not None:
                    similarity = text_similarity(
                        header_representatives[i]["text"],
                        header_representatives[1]["text"]
                    )
                    if similarity >= header_footer_threshold:
                        headers_to_remove.add(header_representatives[i]["text"])
                        headers_to_remove.add(header_representatives[1]["text"])
                        header_matches.add(i)
                        header_matches.add(1)
            elif i == total_pages - 1:
                if header_representatives[total_pages - 2] is not None and i not in header_matches:
                    similarity = text_similarity(
                        header_representatives[i]["text"],
                        header_representatives[total_pages - 2]["text"]
                    )
                    if similarity >= header_footer_threshold:
                        headers_to_remove.add(header_representatives[i]["text"])
                        headers_to_remove.add(header_representatives[total_pages - 2]["text"])
                        header_matches.add(i)
                        header_matches.add(total_pages - 2)
            else:
                if i not in header_matches:
                    if header_representatives[i - 1] is not None:
                        similarity_prev = text_similarity(
                            header_representatives[i]["text"],
                            header_representatives[i - 1]["text"]
                        )
                        if similarity_prev >= header_footer_threshold:
                            headers_to_remove.add(header_representatives[i]["text"])
                            headers_to_remove.add(header_representatives[i - 1]["text"])
                            header_matches.add(i)
                            header_matches.add(i - 1)
                            continue
                    if i + 1 < total_pages and header_representatives[i + 1] is not None:
                        similarity_next = text_similarity(
                            header_representatives[i]["text"],
                            header_representatives[i + 1]["text"]
                        )
                        if similarity_next >= header_footer_threshold:
                            headers_to_remove.add(header_representatives[i]["text"])
                            headers_to_remove.add(header_representatives[i + 1]["text"])
                            header_matches.add(i)
                            header_matches.add(i + 1)

        footer_matches = set()
        for i in range(total_pages):
            if footer_representatives[i] is None:
                continue
            if i == 0:
                if footer_representatives[1] is not None:
                    similarity = text_similarity(
                        footer_representatives[i]["text"],
                        footer_representatives[1]["text"]
                    )
                    if similarity >= header_footer_threshold:
                        footers_to_remove.add(footer_representatives[i]["text"])
                        footers_to_remove.add(footer_representatives[1]["text"])
                        footer_matches.add(i)
                        footer_matches.add(1)
            elif i == total_pages - 1:
                if footer_representatives[total_pages - 2] is not None and i not in footer_matches:
                    similarity = text_similarity(
                        footer_representatives[i]["text"],
                        footer_representatives[total_pages - 2]["text"]
                    )
                    if similarity >= header_footer_threshold:
                        footers_to_remove.add(footer_representatives[i]["text"])
                        footers_to_remove.add(footer_representatives[total_pages - 2]["text"])
                        footer_matches.add(i)
                        footer_matches.add(total_pages - 2)
            else:
                if i not in footer_matches:
                    if footer_representatives[i - 1] is not None:
                        similarity_prev = text_similarity(
                            footer_representatives[i]["text"],
                            footer_representatives[i - 1]["text"]
                        )
                        if similarity_prev >= header_footer_threshold:
                            footers_to_remove.add(footer_representatives[i]["text"])
                            footers_to_remove.add(footer_representatives[i - 1]["text"])
                            footer_matches.add(i)
                            footer_matches.add(i - 1)
                            continue
                    if i + 1 < total_pages and footer_representatives[i + 1] is not None:
                        similarity_next = text_similarity(
                            footer_representatives[i]["text"],
                            footer_representatives[i + 1]["text"]
                        )
                        if similarity_next >= header_footer_threshold:
                            footers_to_remove.add(footer_representatives[i]["text"])
                            footers_to_remove.add(footer_representatives[i + 1]["text"])
                            footer_matches.add(i)
                            footer_matches.add(i + 1)

    # 创建基本的HTML结构
    html_content = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>PDF Extract</title>
        <style>
            body { font-family: Arial, sans-serif; }
            .page { margin-bottom: 20px; }
            .paragraph { margin-bottom: 12px; }
        </style>
    </head>
    <body>
    '''

    # 第二遍：处理页面内容，过滤页眉页脚
    for page_num, page in enumerate(tqdm(doc, desc="转换进度")):
        page_height = page.rect.height
        header_region = (0, 0, page.rect.width, page_height * 0.1)
        footer_region = (0, page_height * 0.9, page.rect.width, page_height)

        blocks = page.get_text("dict")["blocks"]

        html_content += f'<div class="page" id="page-{page_num + 1}">\n'

        current_paragraph = ""
        prev_block_bottom = None
        paragraph_started = False

        for block in blocks:
            if block["type"] == 0:  # 文本块
                block_bbox = block["bbox"]
                block_text = ""

                in_header = (block_bbox[1] >= header_region[1] and
                             block_bbox[3] <= header_region[3] and
                             block_bbox[3] - block_bbox[1] > 0)
                in_footer = (block_bbox[1] >= footer_region[1] and
                             block_bbox[3] <= footer_region[3] and
                             block_bbox[3] - block_bbox[1] > 0)

                temp_text = ""
                for line in block["lines"]:
                    for span in line["spans"]:
                        temp_text += span["text"] + " "
                temp_text = temp_text.strip()

                skip_block = False
                if in_header and temp_text and any(temp_text in header_text for header_text in headers_to_remove):
                    skip_block = True
                elif in_footer and temp_text and any(temp_text in footer_text for footer_text in footers_to_remove):
                    skip_block = True

                if skip_block:
                    continue

                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"]
                        font = span["font"]
                        size = span["size"]
                        color = span["color"]
                        block_text += f'<span style="font-family: {font}; font-size: {size}pt; color: #{color:06x};">{text}</span>'
                    block_text += " "

                is_new_paragraph = False
                if prev_block_bottom is not None:
                    if block["bbox"][1] - prev_block_bottom > size * 1.5:
                        is_new_paragraph = True

                if is_new_paragraph or not paragraph_started:
                    if current_paragraph:
                        html_content += f'<div class="paragraph">{current_paragraph}</div>\n'
                    current_paragraph = block_text
                    paragraph_started = True
                else:
                    current_paragraph += block_text

                prev_block_bottom = block["bbox"][3]

        if current_paragraph:
            html_content += f'<div class="paragraph">{current_paragraph}</div>\n'

        html_content += '</div>\n'

    html_content += "</body></html>"
    doc.close()
    return html_content

def html_to_text(html_content: str) -> str:
    """
    从HTML字符串提取纯文本并智能处理段落
    """
    soup = BeautifulSoup(html_content, "html.parser")
    paragraphs = soup.find_all('div', class_='paragraph')
    cleaned_lines = []
    for para in paragraphs:
        text = para.get_text()
        text = re.sub(r'\s+', ' ', text).strip()
        if text:
            cleaned_lines.append(text)
    return '\n'.join(cleaned_lines)

def pdf_to_text(input_path: str, header_footer_threshold: float = 0.4) -> str:
    """
    将PDF文件转换为文本，处理页眉页脚和布局
    """
    html_content = pdf_to_html(input_path, header_footer_threshold)
    text = html_to_text(html_content)
    return text