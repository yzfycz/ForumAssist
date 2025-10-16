# -*- coding: utf-8 -*-
"""
论坛客户端
负责与论坛API交互，获取论坛数据
"""

import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.api_config import API_ENDPOINTS, ORDERBY_OPTIONS
from src.utils.html_parser import HTMLParser

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
                    # 论坛列表在 message 中，不是 data.forumlist
                    forum_list = result.get('message', [])
                    return forum_list

        except Exception as e:
            pass

        return []

    def get_home_content(self, forum_name, orderby="latest", page=1):
        """
        获取首页内容

        Args:
            forum_name: 论坛名称
            orderby: 排序方式
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

            home_url = f"{forum_url.rstrip('/')}/{API_ENDPOINTS['home_content']}"
            params = {
                "format": "json",
                "orderby": ORDERBY_OPTIONS.get(orderby, "tid"),
                "page": page
            }

            response = session.get(home_url, params=params)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 1:
                    # 首页内容在 message.threadlist 中，不是 data.threadlist
                    message = result.get('message', {})
                    thread_list = message.get('threadlist', []) if isinstance(message, dict) else []
                    # 返回包含分页信息的字典
                    return {
                        "threadlist": thread_list,
                        "pagination": {
                            "page": message.get('page', page),
                            "totalpage": message.get('totalpage', 1)
                        }
                    }

        except Exception as e:
            pass

        return {"threadlist": [], "pagination": {}}

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
                    message = result.get('message', {})
                    return {
                        "threadlist": message.get('threadlist', []),
                        "pagination": {
                            "page": message.get('page', 1),
                            "totalpage": message.get('totalpage', 1)
                        }
                    }

        except Exception as e:
            pass

        return {"threadlist": [], "pagination": {}}

    def get_thread_list_with_type(self, forum_name, api_params, page=1):
        """
        获取带有分类参数的帖子列表

        Args:
            forum_name: 论坛名称
            api_params: API参数，包含fid和分类ID
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
                "page": page
            }

            # 添加所有API参数
            params.update(api_params)

            response = session.get(thread_url, params=params)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 1:
                    message = result.get('message', {})
                    return {
                        "threadlist": message.get('threadlist', []),
                        "pagination": {
                            "page": message.get('page', 1),
                            "totalpage": message.get('totalpage', 1)
                        }
                    }

        except Exception as e:
            pass

        return {"threadlist": [], "pagination": {}}

    def get_thread_detail(self, forum_name, tid, page=1, uid=None):
        """
        获取帖子详情

        Args:
            forum_name: 论坛名称
            tid: 帖子ID
            page: 页码
            uid: 用户ID（可选，用于筛选特定用户的回复）

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
                "page": page,
                "appkey": "24b22d1468",
                "seckey": "cb433ea43a"
            }

            # 如果指定了uid，添加筛选参数
            if uid:
                params['uid'] = uid
            # 尝试添加auth参数（如果有的话）
            user_info = self.auth_manager.get_user_info(forum_name)
            if user_info:
                auth = user_info.get('auth')
                if auth:
                    params['auth'] = auth

            response = session.get(detail_url, params=params)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 1:
                    # 帖子详情数据在 message 中，不是 data 中
                    message = result.get('message', {})
                    return {
                        "postlist": message.get('postlist', []),
                        "pagination": {
                            "page": message.get('page', 1),
                            "totalpage": message.get('totalpage', 1)
                        },
                        "thread_info": message.get('thread', {})
                    }
                else:
                    pass  # API返回状态不为1

        except Exception as e:
            pass

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
                    # 用户帖子数据在 message 中，不是 data 中
                    message = result.get('message', {})
                    return {
                        "threadlist": message.get('threadlist', []),
                        "pagination": {
                            "page": message.get('page', page),
                            "totalpage": message.get('totalpage', 1)
                        }
                    }

        except Exception as e:
            pass

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
            return {"threadlist": [], "pagination": {}}

        forum_config = self.auth_manager.get_user_info(forum_name)
        if not forum_config:
            return {"threadlist": [], "pagination": {}}

        try:
            forum_url = forum_config.get('url', '')
            if not forum_url:
                return {"threadlist": [], "pagination": {}}

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
                    # 用户回复数据在 message 中，不是 data 中
                    message = result.get('message', {})
                    return {
                        "threadlist": message.get('threadlist', []),
                        "pagination": {
                            "page": message.get('page', page),
                            "totalpage": message.get('totalpage', 1)
                        }
                    }

        except Exception as e:
            pass

        return {"threadlist": [], "pagination": {}}

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
                    # 搜索内容在 message.threadlist 中，不是 data.threadlist（与其他API一致）
                    message = result.get('message', {})
                    return {
                        "threadlist": message.get('threadlist', []),
                        "pagination": {
                            "page": message.get('page', page),
                            "totalpage": message.get('totalpage', 1)
                        }
                    }

        except Exception as e:
            pass

        return {"threadlist": [], "pagination": {}}

    def post_reply(self, forum_name, fid, tid, content, pid=None):
        """
        发表回复

        Args:
            forum_name: 论坛名称
            fid: 板块ID
            tid: 帖子ID
            content: 回复内容
            pid: 帖子ID（可选，用于回复特定楼层）

        Returns:
            dict: 包含成功状态和错误信息的字典
        """
        session = self.auth_manager.get_session(forum_name)
        if not session:
            return {"success": False, "error": "无法获取会话信息"}

        forum_config = self.auth_manager.get_user_info(forum_name)
        if not forum_config:
            return {"success": False, "error": "无法获取论坛配置"}

        try:
            forum_url = forum_config.get('url', '')
            if not forum_url:
                return {"success": False, "error": "论坛URL为空"}

            post_url = f"{forum_url.rstrip('/')}/{API_ENDPOINTS['post_reply']}"
            data = {
                "format": "json",
                "fid": fid,
                "tid": tid,
                "message": content
            }

            # 如果指定了pid，添加回复特定楼层的参数
            if pid:
                data['pid'] = pid

            response = session.post(post_url, data=data)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 1:
                    return {"success": True, "error": None}
                else:
                    # API返回错误信息
                    error_message = result.get('message', '回复发送失败')
                    return {"success": False, "error": error_message}
            else:
                return {"success": False, "error": f"HTTP错误: {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": f"网络异常: {str(e)}"}

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
            pass

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
            pass

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
            pass

        return False

    def get_user_profile(self, forum_name, uid):
        """
        获取用户个人资料
        Args:
            forum_name: 论坛名称
            uid: 用户ID
        Returns:
            dict: 用户资料数据
        """
        session = self.auth_manager.get_session(forum_name)
        if not session:
            return {}

        forum_config = self.auth_manager.get_user_info(forum_name)
        if not forum_config:
            return {}

        try:
            forum_url = forum_config.get('url', '')
            if not forum_url:
                return {}

            # 构造请求参数
            params = {
                'format': 'json',
                'appkey': '24b22d1468',
                'seckey': 'cb433ea43a',
                'uid': uid
            }

            # 发送请求
            profile_url = f"{forum_url.rstrip('/')}/user-index.htm"
            response = session.get(profile_url, params=params, timeout=10)

            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 1:
                    return result.get('message', {})
                else:
                    raise Exception(result.get('message', '获取用户资料失败'))
            else:
                raise Exception(f"HTTP错误: {response.status_code}")

        except Exception as e:
            raise Exception(f"获取用户资料失败: {str(e)}")

    def update_post(self, forum_name, edit_params):
        """
        编辑帖子
        Args:
            forum_name: 论坛名称
            edit_params: 编辑参数 {
                'fid': 板块ID,
                'pid': 帖子ID,
                'subject': 标题（可选，编辑楼主时需要）,
                'message': 内容,
                'typeid1': 分类ID1（可选）,
                'typeid2': 分类ID2（可选）,
                'typeid3': 分类ID3（可选）,
                'typeid4': 分类ID4（可选）
            }
        Returns:
            bool: 是否成功
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

            # 构造请求参数
            params = {
                'format': 'json',
                'appkey': '24b22d1468',
                'seckey': 'cb433ea43a',
                'auth': self.auth_manager.get_auth(forum_name)
            }

            # 添加编辑参数（必须参数）
            params['fid'] = edit_params.get('fid')
            params['pid'] = edit_params.get('pid')
            params['message'] = edit_params.get('message', '')

            # 如果是编辑楼主，添加标题和分类信息
            if edit_params.get('subject'):
                params['subject'] = edit_params['subject']
                # 添加分类信息（如果有）
                for type_id in ['typeid1', 'typeid2', 'typeid3', 'typeid4']:
                    if edit_params.get(type_id):
                        params[type_id] = edit_params[type_id]

            # 发送编辑请求
            update_url = f"{forum_url.rstrip('/')}/post-update.htm"
            response = session.post(update_url, data=params, timeout=10)

            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 1:
                    return True
                else:
                    raise Exception(result.get('message', '编辑失败'))
            else:
                raise Exception(f"HTTP错误: {response.status_code}")

        except Exception as e:
            raise Exception(f"编辑帖子失败: {str(e)}")

    def follow_user(self, forum_name, uid):
        """
        关注用户

        Args:
            forum_name: 论坛名称
            uid: 要关注的用户ID

        Returns:
            dict: 包含成功状态和错误信息的字典
        """
        session = self.auth_manager.get_session(forum_name)
        if not session:
            return {"success": False, "error": "无法获取会话信息"}

        forum_config = self.auth_manager.get_user_info(forum_name)
        if not forum_config:
            return {"success": False, "error": "无法获取论坛配置"}

        try:
            forum_url = forum_config.get('url', '')
            if not forum_url:
                return {"success": False, "error": "论坛URL为空"}

            follow_url = f"{forum_url.rstrip('/')}/follow-create.htm"
            params = {
                "format": "json",
                "appkey": "24b22d1468",
                "seckey": "cb433ea43a",
                "uid": uid
            }

            # 添加auth参数（如果有的话）
            user_info = self.auth_manager.get_user_info(forum_name)
            if user_info:
                auth = user_info.get('auth')
                if auth:
                    params['auth'] = auth

            response = session.get(follow_url, params=params)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 1:
                    return {"success": True, "error": None}
                else:
                    error_message = result.get('message', '关注失败')
                    return {"success": False, "error": error_message}
            else:
                return {"success": False, "error": f"HTTP错误: {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": f"网络异常: {str(e)}"}

    def unfollow_user(self, forum_name, uid):
        """
        取消关注用户

        Args:
            forum_name: 论坛名称
            uid: 要取消关注的用户ID

        Returns:
            dict: 包含成功状态和错误信息的字典
        """
        session = self.auth_manager.get_session(forum_name)
        if not session:
            return {"success": False, "error": "无法获取会话信息"}

        forum_config = self.auth_manager.get_user_info(forum_name)
        if not forum_config:
            return {"success": False, "error": "无法获取论坛配置"}

        try:
            forum_url = forum_config.get('url', '')
            if not forum_url:
                return {"success": False, "error": "论坛URL为空"}

            unfollow_url = f"{forum_url.rstrip('/')}/follow-delete.htm"
            params = {
                "format": "json",
                "appkey": "24b22d1468",
                "seckey": "cb433ea43a",
                "uid": uid
            }

            # 添加auth参数（如果有的话）
            user_info = self.auth_manager.get_user_info(forum_name)
            if user_info:
                auth = user_info.get('auth')
                if auth:
                    params['auth'] = auth

            response = session.get(unfollow_url, params=params)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 1:
                    return {"success": True, "error": None}
                else:
                    error_message = result.get('message', '取消关注失败')
                    return {"success": False, "error": error_message}
            else:
                return {"success": False, "error": f"HTTP错误: {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": f"网络异常: {str(e)}"}

    def get_user_following(self, forum_name, uid):
        """
        获取用户的关注列表

        Args:
            forum_name: 论坛名称
            uid: 用户ID

        Returns:
            list: 关注列表
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

            following_url = f"{forum_url.rstrip('/')}/user-friends.htm"
            params = {
                "format": "json",
                "appkey": "24b22d1468",
                "seckey": "cb433ea43a",
                "uid": uid
            }

            response = session.get(following_url, params=params)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 1:
                    return result.get('message', [])

        except Exception as e:
            pass

        return []

    def get_user_followers(self, forum_name, uid):
        """
        获取用户的粉丝列表

        Args:
            forum_name: 论坛名称
            uid: 用户ID

        Returns:
            list: 粉丝列表
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

            followers_url = f"{forum_url.rstrip('/')}/user-fans.htm"
            params = {
                "format": "json",
                "appkey": "24b22d1468",
                "seckey": "cb433ea43a",
                "uid": uid
            }

            response = session.get(followers_url, params=params)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 1:
                    return result.get('message', [])

        except Exception as e:
            pass

        return []