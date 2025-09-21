# -*- coding: utf-8 -*-
"""
争渡论坛API配置信息
"""

# 争渡论坛API配置
APPKEY = "24b22d1468"
SECKEY = "24b22d1468"
BASE_URL = "http://www.zd.hk/"

# 论坛信息
FORUM_INFO = {
    "zdsr": {
        "name": "争渡论坛",
        "url": BASE_URL,
        "display_name": "争渡论坛"
    }
}

# API接口地址
API_ENDPOINTS = {
    "login": "user-login.htm",
    "forum_list": "index-forumlist.htm",
    "home_content": "index-index.htm",
    "thread_list": "forum-index.htm",
    "thread_detail": "thread-index.htm",
    "user_threads": "user-thread.htm",
    "user_posts": "user-post.htm",
    "user_info": "user-index.htm",
    "search": "search-index.htm",
    "post_thread": "post-thread.htm",
    "post_reply": "post-post.htm",
    "attendance": "attendance-post.htm"
}

# 排序方式
ORDERBY_OPTIONS = {
    "latest": "tid",        # 最新主题
    "lastpost": "lastpost", # 最新回复
    "sofa": "sofa",       # 抢沙发
    "hot": "hot",         # 热门主题
    "digest": "digest"    # 精华主题
}