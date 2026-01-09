import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

# 1. 自动定位项目根目录并处理导入路径
current_file = Path(__file__).resolve()
# 向上跳转至项目根目录 D:/project/graph-rag-agent-new/
BASE_DIR = current_file.parent.parent.parent.parent
sys.path.append(str(BASE_DIR))

# 2. 绕过数据库初始化依赖，防止因 Neo4j 未启动导致崩溃
sys.modules["langchain_neo4j"] = MagicMock()
sys.modules["graphrag_agent.config.neo4jdb"] = MagicMock()

# 3. 导入仓库中修改后的 pdf_to_html 函数
try:
    from graphrag_agent.pipelines.ingestion.pdf_processor import pdf_to_html

    print(">>> 成功绕过数据库并从仓库导入 pdf_to_html")
except ImportError as e:
    print(f">>> 导入失败，请检查脚本存放位置: {e}")
    sys.exit(1)


def run_verification():
    # --- 路径配置 ---
    # 输入文件路径
    input_pdf = r'E:\桌面\故障\供电系统中母线故障与检修_王永清.pdf'
    # 输出文件路径
    output_html_path = r'E:\桌面\验证结果.html'

    if not os.path.exists(input_pdf):
        print(f">>> 错误: 找不到 PDF 文件: {input_pdf}")
        return

    print(f">>> 开始调用仓库方法处理: {os.path.basename(input_pdf)}")

    try:
        # 4. 执行转换逻辑
        # 调用的是仓库 pdf_processor.py 中的代码
        html_content = pdf_to_html(input_pdf)

        # 5. 写入结果
        with open(output_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print("\n" + "=" * 50)
        print(f"验证完成！结果已保存至桌面。")
        print(f"路径: {output_html_path}")

    except Exception as e:
        print(f">>> 运行过程中出错: {e}")


if __name__ == "__main__":
    run_verification()