# -*- coding: utf-8 -*-
"""
配置文件管理器
负责管理论坛账户配置文件的读写和加密
"""

import os
import configparser
from .utils.crypto import CryptoManager

class ConfigManager:
    """配置文件管理器"""

    def __init__(self, config_file=None):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        if config_file is None:
            # 默认配置文件路径
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_dir = os.path.join(base_dir, 'config')
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            config_file = os.path.join(config_dir, 'forums.ini')

        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.crypto = CryptoManager()

        # 加载配置文件
        self.load_config()

    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file, encoding='utf-8')

    def save_config(self):
        """保存配置文件"""
        # 确保配置目录存在
        config_dir = os.path.dirname(self.config_file)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        # 保存配置文件
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)

    def get_forum_list(self):
        """
        获取论坛账户列表

        Returns:
            list: 论坛账户列表，每个账户是一个字典
        """
        forums = []
        for section in self.config.sections():
            if section.startswith('Forum_'):
                forum_config = dict(self.config[section])
                # 解密密码
                if 'password' in forum_config:
                    forum_config['password'] = self.crypto.decrypt(forum_config['password'])
                forums.append(forum_config)
        return forums

    def add_forum(self, forum_data):
        """
        添加论坛账户

        Args:
            forum_data: 论坛账户数据，包含name, url, username, password, nickname等字段

        Returns:
            bool: 是否添加成功
        """
        try:
            # 生成配置节名
            section_name = f"Forum_{forum_data['name']}"

            # 加密密码
            forum_data_copy = forum_data.copy()
            if 'password' in forum_data_copy:
                forum_data_copy['password'] = self.crypto.encrypt(forum_data_copy['password'])

            # 添加到配置
            self.config[section_name] = forum_data_copy

            # 保存配置
            self.save_config()
            return True

        except Exception as e:
            print(f"添加论坛账户失败: {e}")
            return False

    def update_forum(self, forum_name, forum_data):
        """
        更新论坛账户

        Args:
            forum_name: 论坛名称
            forum_data: 新的论坛账户数据

        Returns:
            bool: 是否更新成功
        """
        try:
            section_name = f"Forum_{forum_name}"

            # 检查论坛是否存在
            if section_name not in self.config:
                return False

            # 加密密码
            forum_data_copy = forum_data.copy()
            if 'password' in forum_data_copy:
                forum_data_copy['password'] = self.crypto.encrypt(forum_data_copy['password'])

            # 更新配置
            self.config[section_name] = forum_data_copy

            # 保存配置
            self.save_config()
            return True

        except Exception as e:
            print(f"更新论坛账户失败: {e}")
            return False

    def delete_forum(self, forum_name):
        """
        删除论坛账户

        Args:
            forum_name: 论坛名称

        Returns:
            bool: 是否删除成功
        """
        try:
            section_name = f"Forum_{forum_name}"

            # 检查论坛是否存在
            if section_name not in self.config:
                return False

            # 删除配置
            self.config.remove_section(section_name)

            # 保存配置
            self.save_config()
            return True

        except Exception as e:
            print(f"删除论坛账户失败: {e}")
            return False

    def get_forum(self, forum_name):
        """
        获取指定论坛的配置

        Args:
            forum_name: 论坛名称

        Returns:
            dict: 论坛配置，如果不存在则返回None
        """
        section_name = f"Forum_{forum_name}"
        if section_name not in self.config:
            return None

        forum_config = dict(self.config[section_name])
        # 解密密码
        if 'password' in forum_config:
            forum_config['password'] = self.crypto.decrypt(forum_config['password'])

        return forum_config

    def forum_exists(self, forum_name):
        """
        检查论坛账户是否存在

        Args:
            forum_name: 论坛名称

        Returns:
            bool: 是否存在
        """
        section_name = f"Forum_{forum_name}"
        return section_name in self.config