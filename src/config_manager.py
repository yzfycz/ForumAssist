# -*- coding: utf-8 -*-
"""
配置文件管理器
负责管理论坛账户配置文件的读写和加密
"""

import os
import configparser
from utils.crypto import CryptoManager

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
        accounts = []
        for section in self.config.sections():
            if section.startswith('Forum_'):
                forum_config = dict(self.config[section])
                forum_name = section[6:]  # 去掉 'Forum_' 前缀
                url = forum_config.get('url', '')

                # 查找所有用户名（跳过旧的username字段）
                for key, value in forum_config.items():
                    if key.startswith('username') and len(key) > 8:  # 确保是 username1, username2 等
                        # 提取用户名序号
                        user_num = key[8:]  # 去掉 'username' 前缀
                        nickname_key = f'nickname{user_num}'
                        password_key = f'password{user_num}'

                        # 解密密码
                        password_value = forum_config.get(password_key, '')
                        password = self.crypto.decrypt(password_value) if password_value else ''
                        nickname = forum_config.get(nickname_key, '')

                        accounts.append({
                            'name': forum_name,
                            'url': url,
                            'username': value,  # 存储的是用户名
                            'password': password,
                            'nickname': nickname
                        })
        return accounts

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

            # 检查论坛是否已存在
            if section_name not in self.config:
                # 新论坛，创建基础配置
                self.config[section_name] = {
                    'url': forum_data['url']
                }

            # 为该论坛的所有账户查找序号
            existing_accounts = self.get_forum_accounts(forum_data['name'])
            user_num = len(existing_accounts) + 1

            # 添加新账户
            self.config[section_name][f'username{user_num}'] = forum_data['username']
            self.config[section_name][f'nickname{user_num}'] = forum_data['nickname']

            # 加密密码
            if 'password' in forum_data:
                self.config[section_name][f'password{user_num}'] = self.crypto.encrypt(forum_data['password'])

            # 保存配置
            self.save_config()
            return True

        except Exception as e:
            return False

    def get_forum_accounts(self, forum_name):
        """
        获取指定论坛的所有账户

        Args:
            forum_name: 论坛名称

        Returns:
            list: 该论坛的账户列表
        """
        section_name = f"Forum_{forum_name}"
        if section_name not in self.config:
            return []

        accounts = []
        forum_config = dict(self.config[section_name])

        # 查找所有用户名（跳过旧的username字段）
        for key, value in forum_config.items():
            if key.startswith('username') and len(key) > 8:  # 确保是 username1, username2 等
                user_num = key[8:]  # 去掉 'username' 前缀
                accounts.append(value)  # 存储用户名

        return accounts

    def forum_account_exists(self, forum_name, username):
        """
        检查指定论坛的账户是否已存在

        Args:
            forum_name: 论坛名称
            username: 用户名

        Returns:
            bool: 是否存在
        """
        existing_accounts = self.get_forum_accounts(forum_name)
        return username in existing_accounts

    def delete_forum_account(self, forum_name, username):
        """
        删除指定论坛的特定账户

        Args:
            forum_name: 论坛名称
            username: 用户名

        Returns:
            bool: 是否删除成功
        """
        try:
            section_name = f"Forum_{forum_name}"
            if section_name not in self.config:
                return False

            # 查找要删除的账户
            forum_config = dict(self.config[section_name])
            key_to_delete = None

            for key, value in forum_config.items():
                if key.startswith('username') and len(key) > 8 and value == username:
                    user_num = key[8:]  # 去掉 'username' 前缀
                    key_to_delete = user_num
                    break

            if not key_to_delete:
                return False

            # 删除相关字段
            keys_to_remove = [f'username{key_to_delete}', f'password{key_to_delete}', f'nickname{key_to_delete}']
            for key in keys_to_remove:
                if key in self.config[section_name]:
                    del self.config[section_name][key]

            # 如果没有账户了，删除整个论坛
            remaining_accounts = self.get_forum_accounts(forum_name)
            if not remaining_accounts:
                self.config.remove_section(section_name)

            # 保存配置
            self.save_config()
            return True

        except Exception as e:
            return False

    def update_forum_account(self, forum_name, old_username, new_account_data):
        """
        更新指定论坛的特定账户

        Args:
            forum_name: 论坛名称
            old_username: 旧用户名
            new_account_data: 新的账户数据

        Returns:
            bool: 是否更新成功
        """
        try:
            section_name = f"Forum_{forum_name}"
            if section_name not in self.config:
                return False

            # 查找要更新的账户
            forum_config = dict(self.config[section_name])
            key_to_update = None

            for key, value in forum_config.items():
                if key.startswith('username') and len(key) > 8 and value == old_username:
                    user_num = key[8:]  # 去掉 'username' 前缀
                    key_to_update = user_num
                    break

            if not key_to_update:
                return False

            # 如果用户名改变，检查新用户名是否已存在
            if old_username != new_account_data['username']:
                if self.forum_account_exists(forum_name, new_account_data['username']):
                    return False

            # 更新账户信息
            self.config[section_name][f'username{key_to_update}'] = new_account_data['username']
            self.config[section_name][f'nickname{key_to_update}'] = new_account_data['nickname']

            # 加密密码
            if 'password' in new_account_data:
                self.config[section_name][f'password{key_to_update}'] = self.crypto.encrypt(new_account_data['password'])

            # 保存配置
            self.save_config()
            return True

        except Exception as e:
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

    def get_setting(self, key, default_value=None):
        """
        获取软件设置项

        Args:
            key: 设置键名
            default_value: 默认值

        Returns:
            设置值，如果不存在则返回默认值
        """
        section_name = "Settings"
        if section_name not in self.config:
            return default_value

        return self.config[section_name].get(key, default_value)

    def set_setting(self, key, value):
        """
        设置软件设置项

        Args:
            key: 设置键名
            value: 设置值

        Returns:
            bool: 是否设置成功
        """
        try:
            section_name = "Settings"
            if section_name not in self.config:
                self.config[section_name] = {}

            self.config[section_name][key] = str(value)
            self.save_config()
            return True
        except Exception as e:
            return False

    def get_show_list_numbers(self):
        """
        获取是否显示列表序号的设置

        Returns:
            bool: 是否显示列表序号
        """
        return self.get_setting("show_list_numbers", "false").lower() == "true"

    def set_show_list_numbers(self, show):
        """
        设置是否显示列表序号

        Args:
            show: 是否显示列表序号

        Returns:
            bool: 是否设置成功
        """
        return self.set_setting("show_list_numbers", show)