import sys
from pathlib import Path

# 在文件开头添加项目根目录到系统路径
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(BASE_DIR))

import fitz
from tqdm import tqdm
from bs4 import BeautifulSoup
import re
from typing import Optional


def pdf_to_html(input_path: str) -> str:
    """
    将PDF转换为HTML字符串，保留原始布局结构，不再过滤页眉页脚
    """
    doc = fitz.open(input_path)

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

    # 直接遍历页面处理内容
    for page_num, page in enumerate(tqdm(doc, desc="转换进度")):
        blocks = page.get_text("dict")["blocks"]
        html_content += f'<div class="page" id="page-{page_num + 1}">\n'

        current_paragraph = ""
        prev_block_bottom = None
        paragraph_started = False

        for block in blocks:
            if block["type"] == 0:  # 仅处理文本块
                block_text = ""

                # 提取当前块的所有文本和样式
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"]
                        font = span["font"]
                        size = span["size"]
                        color = span["color"]
                        block_text += f'<span style="font-family: {font}; font-size: {size}pt; color: #{color:06x};">{text}</span>'
                    block_text += " "

                # 判断是否是新的段落（基于与上一个块的垂直距离）
                is_new_paragraph = False
                if prev_block_bottom is not None:
                    # 获取当前跨度的大小作为参考，如果没有span则默认12
                    current_size = block["lines"][0]["spans"][0]["size"] if block["lines"] and block["lines"][0][
                        "spans"] else 12
                    if block["bbox"][1] - prev_block_bottom > current_size * 1.5:
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
        # 将多个空格替换为一个
        text = re.sub(r'\s+', ' ', text).strip()
        if text:
            cleaned_lines.append(text)
    return '\n'.join(cleaned_lines)


def pdf_to_text(input_path: str) -> str:
    """
    将PDF文件转换为文本，不再进行页眉页脚过滤
    """
    html_content = pdf_to_html(input_path)
    text = html_to_text(html_content)
    return text