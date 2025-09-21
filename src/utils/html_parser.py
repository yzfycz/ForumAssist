# -*- coding: utf-8 -*-
"""
HTML解析工具模块
用于解析论坛的HTML页面内容
"""

import re
from bs4 import BeautifulSoup
import html

class HTMLParser:
    """HTML解析器"""

    def __init__(self):
        pass

    def clean_html(self, html_content):
        """
        清理HTML标签，保留文本内容和换行

        Args:
            html_content: HTML内容

        Returns:
            清理后的纯文本内容
        """
        if not html_content:
            return ""

        # 创建BeautifulSoup对象
        soup = BeautifulSoup(html_content, 'html.parser')

        # 移除不需要的标签
        for tag in soup(['script', 'style', 'link', 'meta']):
            tag.decompose()

        # 处理换行
        for tag in soup(['br', 'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            if tag.name == 'br':
                tag.replace_with('\n')
            else:
                tag.insert_before('\n')
                tag.insert_after('\n')

        # 获取文本并清理
        text = soup.get_text()

        # 清理多余的空白字符
        text = re.sub(r'\s+', ' ', text)  # 多个空白字符替换为一个空格
        text = text.replace(' \n ', '\n')  # 修复换行周围的空格
        text = text.replace('\n ', '\n')   # 移除换行后的空格
        text = text.replace(' \n', '\n')   # 移除换行前的空格

        # 分割成行并清理
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line:  # 只保留非空行
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def parse_message_list(self, html_content):
        """
        解析消息列表页面

        Args:
            html_content: 消息列表HTML内容

        Returns:
            消息列表，每个消息包含用户名和用户ID
        """
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        messages = []

        # 解析消息列表项
        for item in soup.select('.list-group-item a'):
            href = item.get('href', '')
            text = item.text.strip()

            # 从href中提取touid参数
            if 'touid=' in href:
                touid_match = re.search(r'touid=(\d+)', href)
                if touid_match:
                    touid = touid_match.group(1)
                    messages.append({
                        'username': text,
                        'touid': touid
                    })

        return messages

    def parse_message_detail(self, html_content):
        """
        解析消息详情页面

        Args:
            html_content: 消息详情HTML内容

        Returns:
            消息内容列表
        """
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        messages = []

        # 解析对话内容
        for media in soup.select('.pm-list .media'):
            try:
                # 提取用户名和时间
                header = media.select_one('h5').text
                # 格式: "用户名 (时间)"
                match = re.match(r'^(.+?)\s+\((.+?)\)$', header.strip())
                if match:
                    username = match.group(1)
                    datetime = match.group(2)

                    # 提取消息内容
                    content_div = media.select_one('.media-body')
                    content = self.clean_html(str(content_div))

                    messages.append({
                        'username': username,
                        'datetime': datetime,
                        'content': content
                    })
            except Exception:
                continue

        return messages

    def extract_touid_from_link(self, href):
        """
        从链接中提取touid参数

        Args:
            href: 链接URL

        Returns:
            用户ID字符串
        """
        if not href:
            return None

        match = re.search(r'touid=(\d+)', href)
        return match.group(1) if match else None

    def unescape_html(self, text):
        """
        HTML转义字符解码

        Args:
            text: 包含HTML转义字符的文本

        Returns:
            解码后的文本
        """
        if not text:
            return ""
        return html.unescape(text)