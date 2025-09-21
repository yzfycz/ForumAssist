# -*- coding: utf-8 -*-
"""
论坛客户端
负责与论坛API交互，获取论坛数据
"""

import requests
from config.api_config import API_ENDPOINTS, ORDERBY_OPTIONS
from .utils.html_parser import HTMLParser

class ForumClient:
    """论坛客户端"""

    def __init__(self, auth_manager):
        """
        初始化论坛客户端

        Args:
            auth_manager: 认证管理器实例
        """
        self.auth_manager = auth_manager
        self.html_parser = HTMLParser()

    def get_forum_list(self, forum_name):
        """
        获取论坛板块列表

        Args:
            forum_name: 论坛名称

        Returns:
            list: 板块列表
        """
        session = self.auth_manager.get_session(forum_name)
        if not session:
            return []

        forum_config = self.auth_manager.get_user_info(forum_name)
        if not forum_config:
            return []

        try:
            forum_url = forum_config.get('url', '')
            if not forum_url:
                return []

            forum_list_url = f"{forum_url.rstrip('/')}/{API_ENDPOINTS['forum_list']}"
            params = {"format": "json"}

            response = session.get(forum_list_url, params=params)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 1:
                    return result.get('data', {}).get('forumlist', [])

        except Exception as e:
            print(f"获取论坛列表失败: {e}")

        return []

    def get_home_content(self, forum_name, orderby="latest"):
        """
        获取首页内容

        Args:
            forum_name: 论坛名称
            orderby: 排序方式

        Returns:
            list: 主题列表
        """
        session = self.auth_manager.get_session(forum_name)
        if not session:
            return []

        forum_config = self.auth_manager.get_user_info(forum_name)
        if not forum_config:
            return []

        try:
            forum_url = forum_config.get('url', '')
            if not forum_url:
                return []

            home_url = f"{forum_url.rstrip('/')}/{API_ENDPOINTS['home_content']}"
            params = {
                "format": "json",
                "orderby": ORDERBY_OPTIONS.get(orderby, "tid")
            }

            response = session.get(home_url, params=params)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 1:
                    return result.get('data', {}).get('threadlist', [])

        except Exception as e:
            print(f"获取首页内容失败: {e}")

        return []

    def get_thread_list(self, forum_name, fid, page=1):
        """
        获取帖子列表

        Args:
            forum_name: 论坛名称
            fid: 板块ID
            page: 页码

        Returns:
            dict: 包含帖子列表和分页信息的字典
        """
        session = self.auth_manager.get_session(forum_name)
        if not session:
            return {"threadlist": [], "pagination": {}}

        forum_config = self.auth_manager.get_user_info(forum_name)
        if not forum_config:
            return {"threadlist": [], "pagination": {}}

        try:
            forum_url = forum_config.get('url', '')
            if not forum_url:
                return {"threadlist": [], "pagination": {}}

            thread_url = f"{forum_url.rstrip('/')}/{API_ENDPOINTS['thread_list']}"
            params = {
                "format": "json",
                "fid": fid,
                "page": page
            }

            response = session.get(thread_url, params=params)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 1:
                    data = result.get('data', {})
                    return {
                        "threadlist": data.get('threadlist', []),
                        "pagination": data.get('pagination', {})
                    }

        except Exception as e:
            print(f"获取帖子列表失败: {e}")

        return {"threadlist": [], "pagination": {}}

    def get_thread_detail(self, forum_name, tid, page=1):
        """
        获取帖子详情

        Args:
            forum_name: 论坛名称
            tid: 帖子ID
            page: 页码

        Returns:
            dict: 包含帖子详情和分页信息的字典
        """
        session = self.auth_manager.get_session(forum_name)
        if not session:
            return {"postlist": [], "pagination": {}}

        forum_config = self.auth_manager.get_user_info(forum_name)
        if not forum_config:
            return {"postlist": [], "pagination": {}}

        try:
            forum_url = forum_config.get('url', '')
            if not forum_url:
                return {"postlist": [], "pagination": {}}

            detail_url = f"{forum_url.rstrip('/')}/{API_ENDPOINTS['thread_detail']}"
            params = {
                "format": "json",
                "tid": tid,
                "page": page
            }

            response = session.get(detail_url, params=params)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 1:
                    data = result.get('data', {})
                    return {
                        "postlist": data.get('postlist', []),
                        "pagination": data.get('pagination', {}),
                        "thread_info": data.get('thread', {})
                    }

        except Exception as e:
            print(f"获取帖子详情失败: {e}")

        return {"postlist": [], "pagination": {}}

    def get_user_threads(self, forum_name, uid, page=1):
        """
        获取用户发表的帖子

        Args:
            forum_name: 论坛名称
            uid: 用户ID
            page: 页码

        Returns:
            dict: 包含帖子列表和分页信息的字典
        """
        session = self.auth_manager.get_session(forum_name)
        if not session:
            return {"threadlist": [], "pagination": {}}

        forum_config = self.auth_manager.get_user_info(forum_name)
        if not forum_config:
            return {"threadlist": [], "pagination": {}}

        try:
            forum_url = forum_config.get('url', '')
            if not forum_url:
                return {"threadlist": [], "pagination": {}}

            user_threads_url = f"{forum_url.rstrip('/')}/{API_ENDPOINTS['user_threads']}"
            params = {
                "format": "json",
                "uid": uid,
                "page": page
            }

            response = session.get(user_threads_url, params=params)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 1:
                    data = result.get('data', {})
                    return {
                        "threadlist": data.get('threadlist', []),
                        "pagination": data.get('pagination', {})
                    }

        except Exception as e:
            print(f"获取用户帖子失败: {e}")

        return {"threadlist": [], "pagination": {}}

    def get_user_posts(self, forum_name, uid, page=1):
        """
        获取用户的回复

        Args:
            forum_name: 论坛名称
            uid: 用户ID
            page: 页码

        Returns:
            dict: 包含回复列表和分页信息的字典
        """
        session = self.auth_manager.get_session(forum_name)
        if not session:
            return {"postlist": [], "pagination": {}}

        forum_config = self.auth_manager.get_user_info(forum_name)
        if not forum_config:
            return {"postlist": [], "pagination": {}}

        try:
            forum_url = forum_config.get('url', '')
            if not forum_url:
                return {"postlist": [], "pagination": {}}

            user_posts_url = f"{forum_url.rstrip('/')}/{API_ENDPOINTS['user_posts']}"
            params = {
                "format": "json",
                "uid": uid,
                "page": page
            }

            response = session.get(user_posts_url, params=params)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 1:
                    data = result.get('data', {})
                    return {
                        "postlist": data.get('postlist', []),
                        "pagination": data.get('pagination', {})
                    }

        except Exception as e:
            print(f"获取用户回复失败: {e}")

        return {"postlist": [], "pagination": {}}

    def search(self, forum_name, keyword, page=1):
        """
        搜索内容

        Args:
            forum_name: 论坛名称
            keyword: 搜索关键词
            page: 页码

        Returns:
            dict: 包含搜索结果和分页信息的字典
        """
        session = self.auth_manager.get_session(forum_name)
        if not session:
            return {"threadlist": [], "pagination": {}}

        forum_config = self.auth_manager.get_user_info(forum_name)
        if not forum_config:
            return {"threadlist": [], "pagination": {}}

        try:
            forum_url = forum_config.get('url', '')
            if not forum_url:
                return {"threadlist": [], "pagination": {}}

            search_url = f"{forum_url.rstrip('/')}/{API_ENDPOINTS['search']}"
            params = {
                "format": "json",
                "keyword": keyword,
                "page": page
            }

            response = session.get(search_url, params=params)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 1:
                    data = result.get('data', {})
                    return {
                        "threadlist": data.get('threadlist', []),
                        "pagination": data.get('pagination', {})
                    }

        except Exception as e:
            print(f"搜索失败: {e}")

        return {"threadlist": [], "pagination": {}}

    def post_reply(self, forum_name, tid, content):
        """
        发表回复

        Args:
            forum_name: 论坛名称
            tid: 帖子ID
            content: 回复内容

        Returns:
            bool: 是否发表成功
        """
        session = self.auth_manager.get_session(forum_name)
        if not session:
            return False

        forum_config = self.auth_manager.get_user_info(forum_name)
        if not forum_config:
            return False

        try:
            forum_url = forum_config.get('url', '')
            if not forum_url:
                return False

            post_url = f"{forum_url.rstrip('/')}/{API_ENDPOINTS['post_reply']}"
            data = {
                "format": "json",
                "tid": tid,
                "message": content
            }

            response = session.post(post_url, data=data)
            if response.status_code == 200:
                result = response.json()
                return result.get('status') == 1

        except Exception as e:
            print(f"发表回复失败: {e}")

        return False

    def get_message_list(self, forum_name):
        """
        获取消息列表

        Args:
            forum_name: 论坛名称

        Returns:
            list: 消息列表
        """
        session = self.auth_manager.get_session(forum_name)
        if not session:
            return []

        forum_config = self.auth_manager.get_user_info(forum_name)
        if not forum_config:
            return []

        try:
            forum_url = forum_config.get('url', '')
            if not forum_url:
                return []

            # 获取消息列表页面
            message_url = f"{forum_url.rstrip('/')}/pm?type=to"
            response = session.get(message_url)

            if response.status_code == 200:
                # 解析HTML获取消息列表
                return self.html_parser.parse_message_list(response.text)

        except Exception as e:
            print(f"获取消息列表失败: {e}")

        return []

    def get_message_detail(self, forum_name, touid):
        """
        获取消息详情

        Args:
            forum_name: 论坛名称
            touid: 对方用户ID

        Returns:
            list: 消息详情列表
        """
        session = self.auth_manager.get_session(forum_name)
        if not session:
            return []

        forum_config = self.auth_manager.get_user_info(forum_name)
        if not forum_config:
            return []

        try:
            forum_url = forum_config.get('url', '')
            if not forum_url:
                return []

            # 获取消息详情页面
            message_url = f"{forum_url.rstrip('/')}/pm/view?touid={touid}"
            response = session.get(message_url)

            if response.status_code == 200:
                # 解析HTML获取消息详情
                return self.html_parser.parse_message_detail(response.text)

        except Exception as e:
            print(f"获取消息详情失败: {e}")

        return []

    def send_message(self, forum_name, touid, subject, message):
        """
        发送消息

        Args:
            forum_name: 论坛名称
            touid: 对方用户ID
            subject: 消息主题
            message: 消息内容

        Returns:
            bool: 是否发送成功
        """
        session = self.auth_manager.get_session(forum_name)
        if not session:
            return False

        forum_config = self.auth_manager.get_user_info(forum_name)
        if not forum_config:
            return False

        try:
            forum_url = forum_config.get('url', '')
            if not forum_url:
                return False

            # 发送消息
            message_url = f"{forum_url.rstrip('/')}/pm/create"
            data = {
                "touid": touid,
                "subject": subject,
                "message": message
            }

            response = session.post(message_url, data=data)
            return response.status_code == 200

        except Exception as e:
            print(f"发送消息失败: {e}")

        return False