# -*- coding: utf-8 -*-
"""
认证管理器
负责论坛登录认证和会话管理
"""

import requests
from config.api_config import APPKEY, SECKEY

class AuthenticationManager:
    """认证管理器"""

    def __init__(self):
        """初始化认证管理器"""
        self.active_sessions = {}  # {forum_name: session}
        self.user_info = {}  # {forum_name: user_info}

    def login_to_forum(self, forum_config):
        """
        登录到指定论坛

        Args:
            forum_config: 论坛配置，包含url, username, password等字段

        Returns:
            bool: 是否登录成功
        """
        try:
            forum_name = forum_config['name']
            forum_url = forum_config['url']
            username = forum_config['username']
            password = forum_config['password']

            # 创建会话
            session = requests.Session()

            # 准备登录数据
            login_data = {
                "email": username,
                "password": password,
                "appkey": APPKEY,
                "seckey": SECKEY,
                "format": "json"
            }

            # 发送登录请求
            login_url = f"{forum_url.rstrip('/')}/user-login.htm"
            response = session.post(login_url, data=login_data)

            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 1:
                    # 登录成功，保存会话
                    self.active_sessions[forum_name] = session

                    # 用户ID在 message.user.uid 中
                    user_data = result.get('message', {}).get('user', {})
                    uid = user_data.get('uid')

                    # 提取auth参数（如果存在）
                    auth = result.get('message', {}).get('user', {}).get('auth')
                    if auth:
                        user_data['auth'] = auth
                        
                    # 如果从登录响应中获取到了用户信息，直接使用
                    if user_data and uid:
                        # 合并论坛配置和用户信息
                        self.user_info[forum_name] = {
                            **forum_config,  # 包含url, username, password等
                            **user_data      # 包含uid, nickname等
                        }
                    else:
                        # 尝试通过API获取用户信息
                        if uid:
                            user_info = self._get_user_info(session, forum_url, uid)
                            if user_info:
                                # 合并论坛配置和用户信息
                                self.user_info[forum_name] = {
                                    **forum_config,  # 包含url, username, password等
                                    **user_info     # 包含uid, nickname等
                                }

                    return True
                else:
                    return False
            else:
                return False

        except Exception as e:
            return False

    def logout_from_forum(self, forum_name):
        """
        从指定论坛登出

        Args:
            forum_name: 论坛名称
        """
        if forum_name in self.active_sessions:
            # 关闭会话
            self.active_sessions[forum_name].close()
            del self.active_sessions[forum_name]

        if forum_name in self.user_info:
            del self.user_info[forum_name]

    def get_session(self, forum_name):
        """
        获取指定论坛的会话

        Args:
            forum_name: 论坛名称

        Returns:
            requests.Session: 会话对象，如果不存在则返回None
        """
        return self.active_sessions.get(forum_name)

    def get_user_info(self, forum_name):
        """
        获取指定论坛的用户信息

        Args:
            forum_name: 论坛名称

        Returns:
            dict: 用户信息，如果不存在则返回None
        """
        return self.user_info.get(forum_name)

    def is_logged_in(self, forum_name):
        """
        检查是否已登录到指定论坛

        Args:
            forum_name: 论坛名称

        Returns:
            bool: 是否已登录
        """
        return forum_name in self.active_sessions

    def _get_user_info(self, session, forum_url, uid):
        """
        获取用户信息

        Args:
            session: 会话对象
            forum_url: 论坛URL
            uid: 用户ID

        Returns:
            dict: 用户信息
        """
        try:
            user_info_url = f"{forum_url.rstrip('/')}/user-index.htm"
            params = {
                "uid": uid,
                "format": "json"
            }

            response = session.get(user_info_url, params=params)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 1:
                    # 用户信息在 message 中，不是 data 中
                    return result.get('message', {})
        except Exception as e:
            pass

        return {}

    def refresh_session(self, forum_name, forum_config):
        """
        刷新指定论坛的会话

        Args:
            forum_name: 论坛名称
            forum_config: 论坛配置

        Returns:
            bool: 是否刷新成功
        """
        # 先登出
        self.logout_from_forum(forum_name)

        # 重新登录
        return self.login_to_forum(forum_config)

    def logout_all(self):
        """登出所有论坛"""
        for forum_name in list(self.active_sessions.keys()):
            self.logout_from_forum(forum_name)