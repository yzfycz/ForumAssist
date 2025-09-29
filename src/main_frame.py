# -*- coding: utf-8 -*-
"""
主窗口框架
程序的主界面框架
"""

import wx
import wx.lib.newevent
import re
from .auth_manager import AuthenticationManager
from .forum_client import ForumClient
from .account_manager import AccountManager
from .message_manager import MessageManager, MessageDialog, MessageListDialog

# 创建自定义事件
AccountSelectedEvent, EVT_ACCOUNT_SELECTED = wx.lib.newevent.NewEvent()

class MainFrame(wx.Frame):
    """主窗口框架"""

    def __init__(self, config_manager):
        """
        初始化主窗口

        Args:
            config_manager: 配置管理器实例
        """
        # 初始化组件
        self.config_manager = config_manager
        self.auth_manager = AuthenticationManager()
        self.forum_client = ForumClient(self.auth_manager)
        self.message_manager = MessageManager(self.forum_client, self.auth_manager)
        self.current_forum = None

        # 获取账户列表
        self.accounts = self.config_manager.get_forum_list()

        # 创建主窗口
        super().__init__(None, title="论坛助手", size=(1024, 768))

        # 绑定事件
        self.Bind(EVT_ACCOUNT_SELECTED, self.on_account_selected)

        # 创建UI
        self.create_ui()
        self.create_menu()

        # 如果没有账户，显示账户管理界面
        if not self.accounts:
            self.show_account_manager()
        else:
            # 显示账户选择界面
            self.show_account_selection()

    def create_ui(self):
        """创建用户界面"""
        # 创建主面板
        self.main_panel = wx.Panel(self)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 创建主要内容区域（先创建以确保获得焦点）
        self.create_content_area()

        # 创建顶部搜索区域
        self.create_search_area()

        self.main_panel.SetSizer(self.main_sizer)

        # 设置窗口图标
        self.set_window_icon()

        # 设置窗口样式
        self.set_window_style()

        # 设置初始焦点到树视图
        self.tree_ctrl.SetFocus()

    def create_search_area(self):
        """创建搜索区域"""
        search_panel = wx.Panel(self.main_panel)
        search_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 搜索框
        self.search_ctrl = wx.SearchCtrl(search_panel, value="输入搜索关键词...", style=wx.TE_PROCESS_ENTER)
        self.search_ctrl.Bind(wx.EVT_TEXT_ENTER, self.on_search)
        self.search_ctrl.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.on_search)

        # 搜索按钮
        search_button = wx.Button(search_panel, label="搜索")
        search_button.Bind(wx.EVT_BUTTON, self.on_search)

        search_sizer.Add(self.search_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        search_sizer.Add(search_button, 0, wx.ALL | wx.EXPAND, 5)

        search_panel.SetSizer(search_sizer)
        self.main_sizer.Add(search_panel, 0, wx.ALL | wx.EXPAND, 5)

    def create_content_area(self):
        """创建主要内容区域"""
        # 创建分割窗口
        self.splitter = wx.SplitterWindow(self.main_panel, style=wx.SP_3D | wx.SP_LIVE_UPDATE)

        # 创建左侧树视图
        self.create_tree_view()

        # 创建右侧列表视图
        self.create_list_view()

        # 设置分割窗口
        self.splitter.SplitVertically(self.tree_panel, self.list_panel, 300)
        self.splitter.SetMinimumPaneSize(200)

        self.main_sizer.Add(self.splitter, 1, wx.ALL | wx.EXPAND, 5)

    def create_tree_view(self):
        """创建树视图"""
        self.tree_panel = wx.Panel(self.splitter)
        tree_sizer = wx.BoxSizer(wx.VERTICAL)

        # 创建树控件 - 使用隐藏根节点的样式
        self.tree_ctrl = wx.TreeCtrl(
            self.tree_panel,
            style=wx.TR_DEFAULT_STYLE | wx.TR_SINGLE | wx.TR_HIDE_ROOT | wx.TR_NO_BUTTONS
        )
        self.tree_ctrl.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_tree_selection)
        self.tree_ctrl.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_tree_activated)
        self.tree_ctrl.Bind(wx.EVT_KEY_DOWN, self.on_tree_key_down)

        tree_sizer.Add(self.tree_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        self.tree_panel.SetSizer(tree_sizer)

    def create_list_view(self):
        """创建列表视图"""
        self.list_panel = wx.Panel(self.splitter)
        list_sizer = wx.BoxSizer(wx.VERTICAL)

        # 创建列表控件
        self.list_ctrl = wx.ListCtrl(self.list_panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_list_selection)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_list_activated)
        self.list_ctrl.Bind(wx.EVT_KEY_DOWN, self.on_list_key_down)

        list_sizer.Add(self.list_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        self.list_panel.SetSizer(list_sizer)

    def create_menu(self):
        """创建菜单栏"""
        menubar = wx.MenuBar()

        # 文件菜单
        file_menu = wx.Menu()
        account_item = file_menu.Append(wx.ID_ANY, "账户管理", "管理论坛账户")
        self.Bind(wx.EVT_MENU, self.on_account_management, account_item)

        exit_item = file_menu.Append(wx.ID_EXIT, "退出", "退出程序")
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)

        menubar.Append(file_menu, "文件")

        # 帮助菜单
        help_menu = wx.Menu()
        about_item = help_menu.Append(wx.ID_ABOUT, "关于", "关于论坛助手")
        self.Bind(wx.EVT_MENU, self.on_about, about_item)

        menubar.Append(help_menu, "帮助")

        self.SetMenuBar(menubar)

    def show_account_selection(self):
        """显示账户选择界面"""
        # 创建账户选择对话框
        dialog = wx.Dialog(self, title="选择账户", size=(400, 300))

        # 创建主面板
        panel = wx.Panel(dialog)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # 创建列表
        list_ctrl = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        list_ctrl.InsertColumn(0, "论坛名称", width=150)
        list_ctrl.InsertColumn(1, "用户名", width=150)
        list_ctrl.InsertColumn(2, "昵称", width=150)

        # 添加账户
        for i, account in enumerate(self.accounts):
            list_ctrl.InsertItem(i, account.get('name', ''))
            list_ctrl.SetItem(i, 1, account.get('username', ''))
            list_ctrl.SetItem(i, 2, account.get('nickname', ''))

        # 创建按钮区域
        button_panel = wx.Panel(panel)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 创建按钮
        ok_button = wx.Button(button_panel, id=wx.ID_OK, label="确定")
        cancel_button = wx.Button(button_panel, id=wx.ID_CANCEL, label="取消")

        # 添加按钮到布局
        button_sizer.Add(ok_button, 0, wx.ALL, 5)
        button_sizer.Add(cancel_button, 0, wx.ALL, 5)

        button_panel.SetSizer(button_sizer)

        # 布局
        sizer.Add(list_ctrl, 1, wx.ALL | wx.EXPAND, 10)
        sizer.Add(button_panel, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        panel.SetSizer(sizer)

        # 绑定事件
        list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, lambda event: self.on_account_selected_activated(list_ctrl, dialog, event))

        # 设置焦点和默认选择
        if self.accounts:
            list_ctrl.SetItemState(0, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
            list_ctrl.SetFocus()

        # 显示对话框
        result = dialog.ShowModal()
        if result == wx.ID_OK:
            selected = list_ctrl.GetFirstSelected()
            if selected != -1:
                account = self.accounts[selected]
                self.select_account(account)

        dialog.Destroy()

    def on_account_selected_activated(self, list_ctrl, dialog, event):
        """账户列表项激活事件（回车键）"""
        selected = list_ctrl.GetFirstSelected()
        if selected != -1:
            account = self.accounts[selected]
            self.select_account(account)
            dialog.EndModal(wx.ID_OK)

    def select_account(self, account):
        """选择账户"""
        # 登录到论坛
        if self.auth_manager.login_to_forum(account):
            self.current_forum = account['name']
            self.update_window_title()
            self.load_forum_data()
        else:
            wx.MessageBox("登录失败，请检查账户信息", "错误", wx.OK | wx.ICON_ERROR)

    def update_window_title(self):
        """更新窗口标题"""
        if self.current_forum:
            user_info = self.auth_manager.get_user_info(self.current_forum)
            nickname = user_info.get('username', '未知用户')
            forum_name = self.current_forum
            self.SetTitle(f"{nickname}-{forum_name}-论坛助手")

    def load_forum_data(self):
        """加载论坛数据"""
        if not self.current_forum:
            return

        # 清空树视图
        self.tree_ctrl.DeleteAllItems()

        # 添加隐藏的根节点
        root = self.tree_ctrl.AddRoot("")

        # 添加常用节点（零级，直接显示）
        self.latest_threads_item = self.tree_ctrl.AppendItem(root, "最新发表")
        self.latest_replies_item = self.tree_ctrl.AppendItem(root, "最新回复")
        self.my_threads_item = self.tree_ctrl.AppendItem(root, "我的发表")
        self.my_posts_item = self.tree_ctrl.AppendItem(root, "我的回复")
        self.messages_item = self.tree_ctrl.AppendItem(root, "我的消息")

        # 添加论坛板块
        forum_list = self.forum_client.get_forum_list(self.current_forum)
        for forum in forum_list:
            forum_name = forum.get('name', '')
            forum_id = forum.get('fid', '')

            # 检查是否有子板块
            sub_list = forum.get('sublist', [])

            if sub_list:
                # 有子板块，添加为一级节点（可展开）
                forum_item = self.tree_ctrl.AppendItem(root, forum_name)
                # 存储板块ID（虽然有子板块，但父板块本身也可能有内容）
                self.tree_ctrl.SetItemData(forum_item, forum_id)

                # 添加子板块（二级节点）
                for sub_forum in sub_list:
                    sub_name = sub_forum.get('name', '')
                    sub_fid = sub_forum.get('fid', '')
                    sub_item = self.tree_ctrl.AppendItem(forum_item, sub_name)
                    self.tree_ctrl.SetItemData(sub_item, sub_fid)
            else:
                # 没有子板块，直接添加为一级节点（零级显示）
                forum_item = self.tree_ctrl.AppendItem(root, forum_name)
                self.tree_ctrl.SetItemData(forum_item, forum_id)

        # 设置焦点到树视图
        self.tree_ctrl.SetFocus()

        # 默认选择"最新发表"
        if self.latest_threads_item.IsOk():
            self.tree_ctrl.SelectItem(self.latest_threads_item)
            self.tree_ctrl.EnsureVisible(self.latest_threads_item)
            # 触发选择事件来加载内容
            self.load_content("最新发表")

    def on_account_selected(self, event):
        """账户选择事件"""
        account = event.account
        self.select_account(account)

    def on_tree_selection(self, event):
        """树视图选择事件 - 阻止自动加载，只有回车键才加载"""
        # 阻止自动加载，让用户通过回车键主动加载
        event.Skip()

    def on_tree_activated(self, event):
        """树视图激活事件"""
        try:
            item = event.GetItem()
            if not item.IsOk():
                return

            text = self.tree_ctrl.GetItemText(item)

            # 获取存储在item data中的板块ID
            item_data = self.tree_ctrl.GetItemData(item)
            fid = item_data if item_data else None

            self.load_content(text, fid)
        except Exception as e:
            print(f"树视图激活事件错误: {e}")

    def on_tree_key_down(self, event):
        """树视图键盘事件处理"""
        keycode = event.GetKeyCode()

        if keycode == wx.WXK_RETURN:
            # 回车键：执行加载操作
            selected_item = self.tree_ctrl.GetSelection()
            if selected_item and selected_item.IsOk():
                self.handle_tree_selection(selected_item)
        elif keycode == wx.WXK_UP or keycode == wx.WXK_DOWN:
            # 上下箭头键：允许导航但不自动加载
            event.Skip()
        elif keycode == wx.WXK_HOME:
            # Home键：移动到第一个项目
            self.move_to_first_item()
        elif keycode == wx.WXK_END:
            # End键：移动到最后一个项目
            self.move_to_last_item()
        elif keycode == wx.WXK_PAGEUP:
            # PageUp键：向上翻页
            self.move_page_up()
        elif keycode == wx.WXK_PAGEDOWN:
            # PageDown键：向下翻页
            self.move_page_down()
        else:
            # 其他按键：默认处理
            event.Skip()

    def on_list_key_down(self, event):
        """列表键盘事件处理"""
        keycode = event.GetKeyCode()

        if keycode == wx.WXK_BACK:
            # 退格键：在帖子详情时返回之前的列表
            if hasattr(self, 'current_content_type') and self.current_content_type == 'thread_detail':
                self.go_back_to_previous_list()
            elif hasattr(self, 'current_content_type') and self.current_content_type == 'message_detail':
                # 在消息详情时返回消息列表
                self.load_messages()
            else:
                event.Skip()
        elif keycode == wx.WXK_RETURN:
            # 回车键：激活当前选中项
            selected = self.list_ctrl.GetNextItem(-1, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
            if selected != -1:
                # 模拟激活事件
                activation_event = wx.ListEvent(wx.wxEVT_LIST_ITEM_ACTIVATED, self.list_ctrl.GetId())
                activation_event.SetIndex(selected)
                self.on_list_activated(activation_event)
            else:
                event.Skip()
        else:
            event.Skip()

    def go_back_to_previous_list(self):
        """返回之前的列表"""
        try:
            if hasattr(self, 'previous_content_type') and hasattr(self, 'previous_content_params'):
                # 恢复之前的内容类型和参数
                content_type = self.previous_content_type
                params = self.previous_content_params

                # 先恢复内容，然后再恢复焦点
                if content_type == 'thread_list' and 'fid' in params:
                    self.load_forum_section_and_restore_focus(params.get('forum_name', ''), params['fid'])
                elif content_type == 'user_threads':
                    self.load_my_threads_and_restore_focus()
                elif content_type == 'user_posts':
                    self.load_my_posts_and_restore_focus()
                elif content_type == 'search_result' and 'keyword' in params:
                    self.search_content_and_restore_focus(params['keyword'])
                elif content_type == 'home_content':
                    if params.get('orderby') == 'latest':
                        self.load_latest_threads_and_restore_focus()
                    elif params.get('orderby') == 'lastpost':
                        self.load_latest_replies_and_restore_focus()
                else:
                    # 默认返回最新发表
                    self.load_latest_threads_and_restore_focus()
            else:
                # 没有之前的状态，返回最新发表
                self.load_latest_threads_and_restore_focus()

        except Exception as e:
            print(f"返回列表错误: {e}")
            self.load_latest_threads_and_restore_focus()

    def load_forum_section_and_restore_focus(self, forum_name, fid):
        """加载板块内容并恢复焦点"""
        try:
            result = self.forum_client.get_thread_list(self.current_forum, fid)
            threads = result.get('threadlist', [])
            pagination = result.get('pagination', {})

            # 获取板块名称用于标题
            forum_name_text = forum_name if forum_name else self.current_forum
            self.SetTitle(f"{forum_name_text}-{self.get_user_nickname()}-论坛助手")

            # 显示内容
            self.display_threads_and_restore_focus(threads, pagination, 'thread_list')
        except Exception as e:
            print(f"加载板块内容错误: {e}")

    def load_latest_threads_and_restore_focus(self):
        """加载最新发表并恢复焦点"""
        result = self.forum_client.get_home_content(self.current_forum, "latest")
        self.SetTitle(f"最新发表-{self.get_user_nickname()}-论坛助手")
        self.display_threads_and_restore_focus(result.get('threadlist', []), result.get('pagination', {}), 'home_content')
        self.current_orderby = 'latest'

    def load_latest_replies_and_restore_focus(self):
        """加载最新回复并恢复焦点"""
        result = self.forum_client.get_home_content(self.current_forum, "lastpost")
        self.SetTitle(f"最新回复-{self.get_user_nickname()}-论坛助手")
        self.display_threads_and_restore_focus(result.get('threadlist', []), result.get('pagination', {}), 'home_content')
        self.current_orderby = 'lastpost'

    def load_my_threads_and_restore_focus(self):
        """加载我的发表并恢复焦点"""
        user_info = self.auth_manager.get_user_info(self.current_forum)
        if user_info:
            uid = user_info.get('uid')
            if uid:
                self.current_uid = uid
                result = self.forum_client.get_user_threads(self.current_forum, uid)
                # API返回的是threadlist格式，每个item本身就是thread对象
                threadlist = result.get('threadlist', [])
                formatted_threads = []
                for item in threadlist:
                    if item:
                        formatted_thread = {
                            'tid': item.get('tid'),
                            'subject': item.get('subject', ''),
                            'username': item.get('username', ''),
                            'uid': item.get('uid'),
                            'dateline_fmt': item.get('dateline_fmt', ''),
                            'views': item.get('views', 0),
                            'posts': item.get('posts', 0),
                            'forumname': item.get('forumname', '')
                        }
                        formatted_threads.append(formatted_thread)

                self.SetTitle(f"我的发表-{self.get_user_nickname()}-论坛助手")
                self.display_threads_and_restore_focus(formatted_threads, result.get('pagination', {}), 'user_threads')

    def load_my_posts_and_restore_focus(self):
        """加载我的回复并恢复焦点"""
        user_info = self.auth_manager.get_user_info(self.current_forum)
        if user_info:
            uid = user_info.get('uid')
            if uid:
                self.current_uid = uid
                result = self.forum_client.get_user_posts(self.current_forum, uid)
                # API返回的是threadlist格式，每个项目包含thread和post信息
                # 需要转换为display_threads期望的格式，显示为回复列表
                threadlist = result.get('threadlist', [])
                formatted_threads = []
                for item in threadlist:
                    thread_info = item.get('thread', {})
                    post_info = item.get('post', {})
                    if thread_info and post_info:
                        # 构造显示为回复的格式，按照新的显示格式要求
                        formatted_thread = {
                            'tid': thread_info.get('tid'),
                            'subject': thread_info.get('subject', ''),
                            'username': thread_info.get('username', ''),
                            'uid': thread_info.get('uid'),
                            'dateline_fmt': thread_info.get('dateline_fmt', ''),  # 帖子发表时间
                            'views': thread_info.get('views', 0),
                            'posts': thread_info.get('posts', 0),
                            'forumname': item.get('forumname', ''),
                            'lastpost_fmt': post_info.get('dateline_fmt', ''),  # 回复时间作为最后回复时间
                            'lastusername': post_info.get('username', '') or thread_info.get('lastusername', '')  # 优先使用回复者，否则使用帖子最后回复者
                        }
                        formatted_threads.append(formatted_thread)

                self.SetTitle(f"我的回复-{self.get_user_nickname()}-论坛助手")
                self.display_threads_and_restore_focus(formatted_threads, result.get('pagination', {}), 'user_posts')

    def search_content_and_restore_focus(self, keyword):
        """搜索内容并恢复焦点"""
        result = self.forum_client.search(self.current_forum, keyword)
        self.SetTitle(f"搜索: {keyword}-{self.get_user_nickname()}-论坛助手")
        self.display_threads_and_restore_focus(result.get('threadlist', []), result.get('pagination', {}), 'search_result')

    def display_threads_and_restore_focus(self, threads, pagination=None, content_type='thread_list'):
        """显示帖子列表并恢复焦点"""
        # 先显示内容
        self.display_threads(threads, pagination, content_type)

        # 然后恢复焦点
        if hasattr(self, 'previous_selected_index') and hasattr(self, 'previous_selected_tid'):
            # 尝试通过tid找到对应的项目（只在实际的帖子中查找，不包括分页控制项）
            found_index = -1
            for i in range(self.list_ctrl.GetItemCount()):
                item_tid = self.list_ctrl.GetItemData(i)
                # 排除分页控制项（它们的TID是负数）
                if item_tid > 0 and item_tid == self.previous_selected_tid:
                    found_index = i
                    break

            if found_index != -1:
                # 选中之前的项目
                self.list_ctrl.SetItemState(found_index, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
                self.list_ctrl.EnsureVisible(found_index)
                # 将焦点设置到列表上
                self.list_ctrl.SetFocus()
            else:
                # 如果没找到，尝试通过索引恢复（但需要考虑分页控制项的影响）
                # 计算实际的帖子数量（排除分页控制项）
                actual_thread_count = len(threads)
                if self.previous_selected_index < actual_thread_count:
                    self.list_ctrl.SetItemState(self.previous_selected_index, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
                    self.list_ctrl.EnsureVisible(self.previous_selected_index)
                    self.list_ctrl.SetFocus()

    def get_user_nickname(self):
        """获取用户昵称"""
        try:
            user_info = self.auth_manager.get_user_info(self.current_forum)
            if user_info:
                return user_info.get('nickname', user_info.get('username', '用户'))
            return '用户'
        except Exception as e:
            print(f"获取用户昵称错误: {e}")
            return '用户'

    def handle_tree_selection(self, selected_item):
        """处理树视图选择并加载内容"""
        try:
            if not selected_item.IsOk():
                return

            text = self.tree_ctrl.GetItemText(selected_item)

            # 获取存储在item data中的板块ID
            item_data = self.tree_ctrl.GetItemData(selected_item)
            fid = item_data if item_data else None

            # 加载对应内容
            self.load_content(text, fid)

            # 加载完成后将焦点转移到列表视图
            if hasattr(self, 'list_ctrl'):
                self.list_ctrl.SetFocus()

        except Exception as e:
            print(f"处理树视图选择错误: {e}")

    def move_to_first_item(self):
        """移动到第一个项目"""
        try:
            root = self.tree_ctrl.GetRootItem()
            if root.IsOk():
                first_child, cookie = self.tree_ctrl.GetFirstChild(root)
                if first_child.IsOk():
                    self.tree_ctrl.SelectItem(first_child)
                    self.tree_ctrl.EnsureVisible(first_child)
        except Exception as e:
            print(f"移动到第一项错误: {e}")

    def move_to_last_item(self):
        """移动到最后一个项目"""
        try:
            root = self.tree_ctrl.GetRootItem()
            if root.IsOk():
                # 遍历找到最后一个子项目
                last_item = None
                item, cookie = self.tree_ctrl.GetFirstChild(root)
                while item.IsOk():
                    last_item = item
                    item, cookie = self.tree_ctrl.GetNextChild(root, cookie)

                if last_item and last_item.IsOk():
                    self.tree_ctrl.SelectItem(last_item)
                    self.tree_ctrl.EnsureVisible(last_item)
        except Exception as e:
            print(f"移动到最后一项错误: {e}")

    def move_page_up(self):
        """向上翻页（移动5项）"""
        try:
            selected = self.tree_ctrl.GetSelection()
            if not selected.IsOk():
                return

            root = self.tree_ctrl.GetRootItem()
            if not root.IsOk():
                return

            # 获取当前项目在子项目中的位置
            target_item = selected
            for _ in range(5):  # 向上移动5项
                prev_item = self.tree_ctrl.GetPrevSibling(target_item)
                if prev_item.IsOk():
                    target_item = prev_item
                else:
                    break

            if target_item.IsOk():
                self.tree_ctrl.SelectItem(target_item)
                self.tree_ctrl.EnsureVisible(target_item)
        except Exception as e:
            print(f"向上翻页错误: {e}")

    def move_page_down(self):
        """向下翻页（移动5项）"""
        try:
            selected = self.tree_ctrl.GetSelection()
            if not selected.IsOk():
                return

            root = self.tree_ctrl.GetRootItem()
            if not root.IsOk():
                return

            # 获取当前项目在子项目中的位置
            target_item = selected
            for _ in range(5):  # 向下移动5项
                next_item = self.tree_ctrl.GetNextSibling(target_item)
                if next_item.IsOk():
                    target_item = next_item
                else:
                    break

            if target_item.IsOk():
                self.tree_ctrl.SelectItem(target_item)
                self.tree_ctrl.EnsureVisible(target_item)
        except Exception as e:
            print(f"向下翻页错误: {e}")

    def on_list_selection(self, event):
        """列表选择事件"""
        # 处理列表选择
        event.Skip()

    def on_list_activated(self, event):
        """列表激活事件 - 处理分页控制和帖子详情加载"""
        try:
            selected = event.GetIndex()
            if selected == -1:
                return

            # 获取项目数据，判断是否是分页控制项
            item_data = self.list_ctrl.GetItemData(selected)

            if item_data == -1:  # 上一页
                self.load_previous_page()
            elif item_data == -2:  # 下一页
                self.load_next_page()
            elif item_data == -3:  # 页码跳转
                self.show_page_jump_dialog()
            elif item_data == -4:  # 回复帖子
                self.show_reply_dialog()
            else:  # 普通帖子项或消息项
                # 根据内容类型处理不同的操作
                if hasattr(self, 'current_content_type'):
                    if self.current_content_type in ['thread_list', 'search_result', 'user_threads', 'home_content']:
                        # 加载帖子详情
                        tid = item_data
                        if tid and tid > 0:
                            self.load_thread_detail(tid)
                    elif self.current_content_type == 'message_list':
                        # 加载消息详情
                        touid = item_data
                        if touid and touid > 0:
                            self.load_message_detail(touid)
                    elif self.current_content_type == 'thread_detail':
                        # 帖子详情中的楼层编辑
                        self.show_floor_editor(selected)

        except Exception as e:
            print(f"列表激活事件处理错误: {e}")
            event.Skip()

    def on_search(self, event):
        """搜索事件"""
        keyword = self.search_ctrl.GetValue().strip()
        if keyword:
            self.search_content(keyword)

    def on_account_management(self, event):
        """账户管理事件"""
        self.show_account_manager()

    def on_exit(self, event):
        """退出事件"""
        self.Close()

    def on_about(self, event):
        """关于事件"""
        wx.MessageBox("论坛助手 v1.0\n\n专为视障用户设计的无障碍论坛客户端", "关于", wx.OK | wx.ICON_INFORMATION)

    def load_content(self, text, fid=None):
        """加载内容"""
        # 清理消息界面（如果存在）
        self.hide_message_interface()

        # 根据选择的树节点加载相应内容
        if text == "最新发表":
            self.load_latest_threads()
        elif text == "最新回复":
            self.load_latest_replies()
        elif text == "我的发表":
            self.load_my_threads()
        elif text == "我的回复":
            self.load_my_posts()
        elif text == "我的消息":
            self.load_messages()
        else:
            # 加载指定板块的内容
            self.load_forum_section(text, fid)

    def hide_message_interface(self):
        """隐藏消息界面"""
        try:
            # 删除消息输入面板
            if hasattr(self, 'message_input_panel'):
                self.message_input_panel.Destroy()
                delattr(self, 'message_input_panel')

            # 重置消息相关状态
            if hasattr(self, 'current_touid'):
                delattr(self, 'current_touid')
            if hasattr(self, 'current_content_type') and self.current_content_type in ['message_list', 'message_detail']:
                delattr(self, 'current_content_type')

        except Exception as e:
            print(f"隐藏消息界面错误: {e}")

    def load_latest_threads(self):
        """加载最新发表"""
        result = self.forum_client.get_home_content(self.current_forum, "latest")
        self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'home_content')
        # 保存当前排序方式，用于分页
        self.current_orderby = 'latest'

    def load_latest_replies(self):
        """加载最新回复"""
        result = self.forum_client.get_home_content(self.current_forum, "lastpost")
        self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'home_content')
        # 保存当前排序方式，用于分页
        self.current_orderby = 'lastpost'

    def load_my_threads(self):
        """加载我的发表"""
        user_info = self.auth_manager.get_user_info(self.current_forum)
        if user_info:
            uid = user_info.get('uid')
            if uid:
                self.current_uid = uid
                result = self.forum_client.get_user_threads(self.current_forum, uid)
                # API返回的是threadlist格式，每个item本身就是thread对象
                threadlist = result.get('threadlist', [])
                # 直接使用item作为thread对象
                formatted_threads = []
                for item in threadlist:
                    if item:
                        # 构造display_threads期望的格式
                        formatted_thread = {
                            'tid': item.get('tid'),
                            'subject': item.get('subject', ''),
                            'username': item.get('username', ''),
                            'uid': item.get('uid'),
                            'dateline_fmt': item.get('dateline_fmt', ''),
                            'views': item.get('views', 0),
                            'posts': item.get('posts', 0),
                            'forumname': item.get('forumname', '')
                        }
                        formatted_threads.append(formatted_thread)
                self.display_threads(formatted_threads, result.get('pagination', {}), 'user_threads')

    def load_my_posts(self):
        """加载我的回复"""
        user_info = self.auth_manager.get_user_info(self.current_forum)
        if user_info:
            uid = user_info.get('uid')
            if uid:
                self.current_uid = uid
                result = self.forum_client.get_user_posts(self.current_forum, uid)
                # API返回的是threadlist格式，每个项目包含thread和post信息
                # 需要转换为display_threads期望的格式，显示为回复列表
                threadlist = result.get('threadlist', [])
                formatted_threads = []
                for item in threadlist:
                    thread_info = item.get('thread', {})
                    post_info = item.get('post', {})
                    if thread_info and post_info:
                        # 构造显示为回复的格式，按照新的显示格式要求
                        formatted_thread = {
                            'tid': thread_info.get('tid'),
                            'subject': thread_info.get('subject', ''),
                            'username': thread_info.get('username', ''),
                            'uid': thread_info.get('uid'),
                            'dateline_fmt': thread_info.get('dateline_fmt', ''),  # 帖子发表时间
                            'views': thread_info.get('views', 0),
                            'posts': thread_info.get('posts', 0),
                            'forumname': item.get('forumname', ''),
                            'lastpost_fmt': post_info.get('dateline_fmt', ''),  # 回复时间作为最后回复时间
                            'lastusername': post_info.get('username', '') or thread_info.get('lastusername', '')  # 优先使用回复者，否则使用帖子最后回复者
                        }
                        formatted_threads.append(formatted_thread)

                # 设置内容类型
                self.current_content_type = 'user_posts'

                # 使用display_threads显示回复列表
                self.display_threads(formatted_threads, result.get('pagination', {}), 'user_posts')

    def load_messages(self):
        """加载消息 - 直接在列表中显示"""
        try:
            # 设置内容类型为消息列表
            self.current_content_type = 'message_list'

            # 获取消息列表
            messages = self.message_manager.get_message_list(self.current_forum)
            self.display_messages(messages)

        except Exception as e:
            print(f"加载消息错误: {e}")
            wx.MessageBox("加载消息失败", "错误", wx.OK | wx.ICON_ERROR)

    def load_forum_section(self, section_name, fid=None):
        """加载论坛板块"""
        if not fid:
            return

        self.current_fid = fid
        result = self.forum_client.get_thread_list(self.current_forum, fid)
        self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'thread_list')

    def search_content(self, keyword):
        """搜索内容"""
        self.current_keyword = keyword
        result = self.forum_client.search(self.current_forum, keyword)
        self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'search_result')

    def display_threads(self, threads, pagination=None, content_type='thread_list'):
        """显示帖子列表"""
        self.list_ctrl.DeleteAllItems()
        # 调整列宽以适应新的显示格式，设置为2000像素确保完整显示
        self.list_ctrl.InsertColumn(0, "内容", width=2000)

        # 保存当前内容类型和分页信息
        self.current_content_type = content_type
        self.current_pagination = pagination or {}
        self.current_threads = threads

        for i, thread in enumerate(threads):
            # 构建新的显示格式
            subject = thread.get('subject', '')
            username = thread.get('username', '')
            views = thread.get('views', 0)
            forumname = thread.get('forumname', '')
            dateline_fmt = thread.get('dateline_fmt', '')
            posts = thread.get('posts', 0)
            lastpost_fmt = thread.get('lastpost_fmt', '')
            lastusername = thread.get('lastusername', '')

            # 按照要求的格式拼接：标题 作者:用户名;浏览:数量;板块:板块名;发表时间:时间;回复:数量;回复时间:时间;最后回复:用户名
            display_text = f"{subject} 作者:{username};浏览:{views};板块:{forumname};发表时间:{dateline_fmt};回复:{posts};回复时间:{lastpost_fmt};最后回复:{lastusername}"

            index = self.list_ctrl.InsertItem(i, display_text)

            # 将帖子ID存储为项目数据
            self.list_ctrl.SetItemData(index, int(thread.get('tid', 0)))

        # 根据设计文档添加4个分页控制项
        # 如果没有分页信息，创建默认分页信息
        if not pagination or not isinstance(pagination, dict):
            pagination = {'page': 1, 'totalpage': 1}

        # 总是添加分页控制，即使只有一页
        self.add_pagination_controls(pagination)

    def add_pagination_controls(self, pagination):
        """根据设计文档添加4个分页控制项"""
        current_page = pagination.get('page', 1)
        total_page = pagination.get('totalpage', 1)

        # 1. 上一页控制项
        if current_page > 1:
            prev_text = f"上一页({current_page - 1})"
            prev_index = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), prev_text)
            self.list_ctrl.SetItemData(prev_index, -1)  # 特殊标记：上一页

        # 2. 下一页控制项
        if current_page < total_page:
            next_text = f"下一页({current_page + 1})"
            next_index = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), next_text)
            self.list_ctrl.SetItemData(next_index, -2)  # 特殊标记：下一页

        # 3. 当前页码跳转控制项
        jump_text = f"第{current_page}页/共{total_page}页 (回车跳转)"
        jump_index = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), jump_text)
        self.list_ctrl.SetItemData(jump_index, -3)  # 特殊标记：页码跳转

        # 4. 回复帖子控制项（仅在帖子详情时显示）
        if self.current_content_type == 'thread_detail':
            reply_index = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), "回复帖子")
            self.list_ctrl.SetItemData(reply_index, -4)  # 特殊标记：回复帖子

    def load_thread_detail(self, tid):
        """加载帖子详情"""
        try:
            # 保存当前状态，用于退格键返回
            if hasattr(self, 'current_content_type'):
                self.previous_content_type = self.current_content_type
                self.previous_content_params = {
                    'forum_name': getattr(self, 'current_forum', ''),
                    'fid': getattr(self, 'current_fid', None),
                    'keyword': getattr(self, 'current_keyword', ''),
                    'orderby': getattr(self, 'current_orderby', 'latest')
                }

                # 保存当前选中的项目索引
                selected = self.list_ctrl.GetNextItem(-1, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
                if selected != -1:
                    self.previous_selected_index = selected
                    self.previous_selected_tid = self.list_ctrl.GetItemData(selected)

            self.current_tid = tid
            result = self.forum_client.get_thread_detail(self.current_forum, tid)
            posts = result.get('postlist', [])
            pagination = result.get('pagination', {})
            thread_info = result.get('thread_info', {})

            # 显示帖子详情
            self.display_posts(posts, pagination, thread_info)

        except Exception as e:
            print(f"加载帖子详情错误: {e}")
            wx.MessageBox("加载帖子详情失败", "错误", wx.OK | wx.ICON_ERROR)

    def load_next_page(self):
        """加载下一页"""
        try:
            if not hasattr(self, 'current_content_type') or not hasattr(self, 'current_pagination'):
                return

            current_page = self.current_pagination.get('page', 1)
            total_page = self.current_pagination.get('totalpage', 1)

            if current_page >= total_page:
                return

            next_page = current_page + 1

            # 根据当前内容类型加载下一页
            if self.current_content_type == 'thread_list' and hasattr(self, 'current_fid'):
                result = self.forum_client.get_thread_list(self.current_forum, self.current_fid, next_page)
                self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'thread_list')
            elif self.current_content_type == 'search_result' and hasattr(self, 'current_keyword'):
                result = self.forum_client.search(self.current_forum, self.current_keyword, next_page)
                self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'search_result')
            elif self.current_content_type == 'user_threads' and hasattr(self, 'current_uid'):
                result = self.forum_client.get_user_threads(self.current_forum, self.current_uid, next_page)
                self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'user_threads')
            elif self.current_content_type == 'user_posts' and hasattr(self, 'current_uid'):
                result = self.forum_client.get_user_posts(self.current_forum, self.current_uid, next_page)
                # 处理 threadlist 格式，转换为新的显示格式
                threadlist = result.get('threadlist', [])
                formatted_threads = []
                for item in threadlist:
                    thread_info = item.get('thread', {})
                    post_info = item.get('post', {})
                    if thread_info and post_info:
                        formatted_thread = {
                            'tid': thread_info.get('tid'),
                            'subject': thread_info.get('subject', ''),
                            'username': thread_info.get('username', ''),
                            'uid': thread_info.get('uid'),
                            'dateline_fmt': thread_info.get('dateline_fmt', ''),  # 帖子发表时间
                            'views': thread_info.get('views', 0),
                            'posts': thread_info.get('posts', 0),
                            'forumname': item.get('forumname', ''),
                            'lastpost_fmt': post_info.get('dateline_fmt', ''),  # 回复时间作为最后回复时间
                            'lastusername': post_info.get('username', '') or thread_info.get('lastusername', '')  # 优先使用回复者，否则使用帖子最后回复者
                        }
                        formatted_threads.append(formatted_thread)

                self.display_threads(formatted_threads, result.get('pagination', {}), 'user_posts')
            elif self.current_content_type == 'home_content' and hasattr(self, 'current_orderby'):
                # 添加首页内容的分页支持
                result = self.forum_client.get_home_content(self.current_forum, self.current_orderby, next_page)
                self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'home_content')

        except Exception as e:
            print(f"加载下一页错误: {e}")
            wx.MessageBox("加载下一页失败", "错误", wx.OK | wx.ICON_ERROR)

    def clean_html_tags(self, html_content):
        """
        清理HTML标签，只保留纯文本内容，但保留换行符

        Args:
            html_content: 包含HTML标签的内容

        Returns:
            str: 清理后的纯文本内容
        """
        if not html_content:
            return ''

        # 首先处理换行相关的HTML标签
        # 将<br>、<br/>、<br />等替换为换行符
        clean_text = re.sub(r'<br\s*/?>', '\n', html_content, flags=re.IGNORECASE)

        # 将<p>、</p>、<div>、</div>等块级标签替换为换行符
        clean_text = re.sub(r'</?(p|div|h[1-6]|blockquote|li)[^>]*>', '\n', clean_text, flags=re.IGNORECASE)

        # 将<tr>、</tr>替换为换行符
        clean_text = re.sub(r'</?tr[^>]*>', '\n', clean_text, flags=re.IGNORECASE)

        # 将</td>、</th>替换为制表符或空格
        clean_text = re.sub(r'</(td|th)[^>]*>', '\t', clean_text, flags=re.IGNORECASE)

        # 移除剩余的HTML标签
        clean_text = re.sub(r'<[^>]+>', '', clean_text)

        # 处理HTML实体
        html_entities = {
            '&nbsp;': ' ',
            '&lt;': '<',
            '&gt;': '>',
            '&amp;': '&',
            '&quot;': '"',
            '&apos;': "'",
            '&copy;': '©',
            '&reg;': '®',
            '&hellip;': '…',
            '&ndash;': '–',
            '&mdash;': '—',
            '&ldquo;': '"',
            '&rdquo;': '"',
            '&lsquo;': "'",
            '&rsquo;': "'"
        }

        for entity, replacement in html_entities.items():
            clean_text = clean_text.replace(entity, replacement)

        # 清理多余的空白字符，但保留换行符
        # 将多个空格合并为一个，但保留换行符
        lines = clean_text.split('\n')
        cleaned_lines = []
        for line in lines:
            # 清理每行中的多余空格
            cleaned_line = re.sub(r'[ \t]+', ' ', line).strip()
            if cleaned_line:  # 只保留非空行
                cleaned_lines.append(cleaned_line)

        # 重新组合，保留段落结构
        clean_text = '\n'.join(cleaned_lines)

        return clean_text.strip()

    def display_posts(self, posts, pagination=None, thread_info=None):
        """显示回复列表"""
        self.list_ctrl.DeleteAllItems()
        self.list_ctrl.InsertColumn(0, "内容", width=800)

        # 如果是帖子详情，显示标题并设置内容类型
        if thread_info:
            self.SetTitle(f"帖子详情: {thread_info.get('subject', '无标题')}")
            self.current_content_type = 'thread_detail'
            self.current_thread_info = thread_info

        self.current_posts = posts
        self.current_pagination = pagination or {}

        for i, post in enumerate(posts):
            # 获取楼层信息
            floor = i + 1  # 楼层从1开始
            username = post.get('username', '')
            content = self.clean_html_tags(post.get('message', ''))
            create_date = post.get('create_date_fmt', '')

            # 格式化显示
            if floor == 1:
                # 楼主
                formatted_content = f"楼主 {username} 说\n{content}\n发表时间：{create_date}"
            else:
                # 其他楼层
                formatted_content = f"{floor}楼 {username} 说\n{content}\n发表时间：{create_date}"

            index = self.list_ctrl.InsertItem(i, formatted_content)
            # 存储原始帖子数据用于编辑
            self.list_ctrl.SetItemData(index, i)

        # 根据设计文档添加4个分页控制项
        # 如果没有分页信息，创建默认分页信息
        if not pagination or not isinstance(pagination, dict):
            pagination = {'page': 1, 'totalpage': 1}

        # 总是添加分页控制，即使只有一页
        self.add_pagination_controls(pagination)

    def load_previous_page(self):
        """加载上一页"""
        try:
            if not hasattr(self, 'current_content_type') or not hasattr(self, 'current_pagination'):
                return

            current_page = self.current_pagination.get('page', 1)
            if current_page <= 1:
                return

            prev_page = current_page - 1

            # 根据当前内容类型加载上一页
            if self.current_content_type == 'thread_list' and hasattr(self, 'current_fid'):
                result = self.forum_client.get_thread_list(self.current_forum, self.current_fid, prev_page)
                self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'thread_list')
            elif self.current_content_type == 'search_result' and hasattr(self, 'current_keyword'):
                result = self.forum_client.search(self.current_forum, self.current_keyword, prev_page)
                self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'search_result')
            elif self.current_content_type == 'user_threads' and hasattr(self, 'current_uid'):
                result = self.forum_client.get_user_threads(self.current_forum, self.current_uid, prev_page)
                self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'user_threads')
            elif self.current_content_type == 'user_posts' and hasattr(self, 'current_uid'):
                result = self.forum_client.get_user_posts(self.current_forum, self.current_uid, prev_page)
                # 处理 threadlist 格式，转换为新的显示格式
                threadlist = result.get('threadlist', [])
                formatted_threads = []
                for item in threadlist:
                    thread_info = item.get('thread', {})
                    post_info = item.get('post', {})
                    if thread_info and post_info:
                        formatted_thread = {
                            'tid': thread_info.get('tid'),
                            'subject': thread_info.get('subject', ''),
                            'username': thread_info.get('username', ''),
                            'uid': thread_info.get('uid'),
                            'dateline_fmt': thread_info.get('dateline_fmt', ''),  # 帖子发表时间
                            'views': thread_info.get('views', 0),
                            'posts': thread_info.get('posts', 0),
                            'forumname': item.get('forumname', ''),
                            'lastpost_fmt': post_info.get('dateline_fmt', ''),  # 回复时间作为最后回复时间
                            'lastusername': post_info.get('username', '') or thread_info.get('lastusername', '')  # 优先使用回复者，否则使用帖子最后回复者
                        }
                        formatted_threads.append(formatted_thread)

                self.display_threads(formatted_threads, result.get('pagination', {}), 'user_posts')
            elif self.current_content_type == 'home_content' and hasattr(self, 'current_orderby'):
                # 添加首页内容的分页支持
                result = self.forum_client.get_home_content(self.current_forum, self.current_orderby, prev_page)
                self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'home_content')
            elif self.current_content_type == 'thread_detail' and hasattr(self, 'current_tid'):
                result = self.forum_client.get_thread_detail(self.current_forum, self.current_tid, prev_page)
                self.display_posts(result.get('postlist', []), result.get('pagination', {}))

        except Exception as e:
            print(f"加载上一页错误: {e}")
            wx.MessageBox("加载上一页失败", "错误", wx.OK | wx.ICON_ERROR)

    def show_page_jump_dialog(self):
        """显示页码跳转对话框"""
        try:
            if not hasattr(self, 'current_pagination'):
                return

            total_page = self.current_pagination.get('totalpage', 1)
            current_page = self.current_pagination.get('page', 1)

            # 创建输入对话框
            dialog = wx.TextEntryDialog(
                self,
                f"请输入目标页码 (1-{total_page}):",
                "页码跳转",
                str(current_page)
            )

            if dialog.ShowModal() == wx.ID_OK:
                page_str = dialog.GetValue().strip()
                try:
                    target_page = int(page_str)
                    if 1 <= target_page <= total_page:
                        self.jump_to_page(target_page)
                    else:
                        wx.MessageBox(f"页码必须在 1 到 {total_page} 之间", "输入错误", wx.OK | wx.ICON_WARNING)
                except ValueError:
                    wx.MessageBox("请输入有效的数字", "输入错误", wx.OK | wx.ICON_WARNING)

            dialog.Destroy()

        except Exception as e:
            print(f"页码跳转错误: {e}")

    def jump_to_page(self, target_page):
        """跳转到指定页码"""
        try:
            # 根据当前内容类型跳转页面
            if self.current_content_type == 'thread_list' and hasattr(self, 'current_fid'):
                result = self.forum_client.get_thread_list(self.current_forum, self.current_fid, target_page)
                self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'thread_list')
            elif self.current_content_type == 'search_result' and hasattr(self, 'current_keyword'):
                result = self.forum_client.search(self.current_forum, self.current_keyword, target_page)
                self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'search_result')
            elif self.current_content_type == 'user_threads' and hasattr(self, 'current_uid'):
                result = self.forum_client.get_user_threads(self.current_forum, self.current_uid, target_page)
                self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'user_threads')
            elif self.current_content_type == 'user_posts' and hasattr(self, 'current_uid'):
                result = self.forum_client.get_user_posts(self.current_forum, self.current_uid, target_page)
                # 处理 threadlist 格式，转换为新的显示格式
                threadlist = result.get('threadlist', [])
                formatted_threads = []
                for item in threadlist:
                    thread_info = item.get('thread', {})
                    post_info = item.get('post', {})
                    if thread_info and post_info:
                        formatted_thread = {
                            'tid': thread_info.get('tid'),
                            'subject': thread_info.get('subject', ''),
                            'username': thread_info.get('username', ''),
                            'uid': thread_info.get('uid'),
                            'dateline_fmt': thread_info.get('dateline_fmt', ''),  # 帖子发表时间
                            'views': thread_info.get('views', 0),
                            'posts': thread_info.get('posts', 0),
                            'forumname': item.get('forumname', ''),
                            'lastpost_fmt': post_info.get('dateline_fmt', ''),  # 回复时间作为最后回复时间
                            'lastusername': post_info.get('username', '') or thread_info.get('lastusername', '')  # 优先使用回复者，否则使用帖子最后回复者
                        }
                        formatted_threads.append(formatted_thread)

                self.display_threads(formatted_threads, result.get('pagination', {}), 'user_posts')
            elif self.current_content_type == 'home_content' and hasattr(self, 'current_orderby'):
                # 添加首页内容的分页支持
                result = self.forum_client.get_home_content(self.current_forum, self.current_orderby, target_page)
                self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'home_content')
            elif self.current_content_type == 'thread_detail' and hasattr(self, 'current_tid'):
                result = self.forum_client.get_thread_detail(self.current_forum, self.current_tid, target_page)
                self.display_posts(result.get('postlist', []), result.get('pagination', {}))

        except Exception as e:
            print(f"页面跳转错误: {e}")
            wx.MessageBox("页面跳转失败", "错误", wx.OK | wx.ICON_ERROR)

    def show_reply_dialog(self):
        """显示回复对话框"""
        try:
            if not hasattr(self, 'current_tid') or not self.current_tid:
                wx.MessageBox("请先选择要回复的帖子", "提示", wx.OK | wx.ICON_INFORMATION)
                return

            # 创建回复对话框
            dialog = wx.Dialog(self, title="回复帖子", size=(500, 300))
            panel = wx.Panel(dialog)
            sizer = wx.BoxSizer(wx.VERTICAL)

            # 标题（只读）
            title_label = wx.StaticText(panel, label="回复主题:")
            title_ctrl = wx.TextCtrl(panel, value=f"帖子ID: {self.current_tid}", style=wx.TE_READONLY)
            sizer.Add(title_label, 0, wx.ALL | wx.EXPAND, 5)
            sizer.Add(title_ctrl, 0, wx.ALL | wx.EXPAND, 5)

            # 内容输入框
            content_label = wx.StaticText(panel, label="回复内容:")
            content_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER)
            sizer.Add(content_label, 0, wx.ALL | wx.EXPAND, 5)
            sizer.Add(content_ctrl, 1, wx.ALL | wx.EXPAND, 5)

            # 按钮面板
            button_panel = wx.Panel(panel)
            button_sizer = wx.BoxSizer(wx.HORIZONTAL)
            ok_button = wx.Button(button_panel, id=wx.ID_OK, label="发送")
            cancel_button = wx.Button(button_panel, id=wx.ID_CANCEL, label="取消")
            button_sizer.Add(ok_button, 0, wx.ALL, 5)
            button_sizer.Add(cancel_button, 0, wx.ALL, 5)
            button_panel.SetSizer(button_sizer)
            sizer.Add(button_panel, 0, wx.ALL | wx.ALIGN_CENTER, 5)

            panel.SetSizer(sizer)

            # 显示对话框
            if dialog.ShowModal() == wx.ID_OK:
                content = content_ctrl.GetValue().strip()
                if content:
                    self.post_reply(content)
                else:
                    wx.MessageBox("回复内容不能为空", "提示", wx.OK | wx.ICON_WARNING)

            dialog.Destroy()

        except Exception as e:
            print(f"显示回复对话框错误: {e}")

    def post_reply(self, content):
        """发送回复"""
        try:
            if not hasattr(self, 'current_tid') or not self.current_tid:
                return

            success = self.forum_client.post_reply(self.current_forum, self.current_tid, content)
            if success:
                wx.MessageBox("回复发送成功", "成功", wx.OK | wx.ICON_INFORMATION)
                # 刷新当前页面
                self.load_thread_detail(self.current_tid)
            else:
                wx.MessageBox("回复发送失败", "错误", wx.OK | wx.ICON_ERROR)

        except Exception as e:
            print(f"发送回复错误: {e}")
            wx.MessageBox("回复发送失败", "错误", wx.OK | wx.ICON_ERROR)

    def display_messages(self, messages):
        """显示消息列表"""
        self.list_ctrl.DeleteAllItems()
        self.list_ctrl.InsertColumn(0, "用户名", width=200)
        self.list_ctrl.InsertColumn(1, "状态", width=100)

        # 保存消息列表
        self.current_messages = messages

        for i, message in enumerate(messages):
            username = message.get('username', '')
            status = message.get('status', '')
            touid = message.get('touid', '')

            index = self.list_ctrl.InsertItem(i, username)
            self.list_ctrl.SetItem(index, 1, status)

            # 将对方用户ID存储为项目数据（转换为整数）
            try:
                uid_value = int(touid) if touid else 0
            except (ValueError, TypeError):
                uid_value = 0
            self.list_ctrl.SetItemData(index, uid_value)

    def load_message_detail(self, touid):
        """加载消息详情"""
        try:
            self.current_touid = touid
            self.current_content_type = 'message_detail'

            # 获取消息详情
            messages = self.message_manager.get_message_detail(self.current_forum, touid)
            self.display_message_conversation(messages)

            # 创建消息输入界面
            self.create_message_input_panel()

        except Exception as e:
            print(f"加载消息详情错误: {e}")
            wx.MessageBox("加载消息详情失败", "错误", wx.OK | wx.ICON_ERROR)

    def display_message_conversation(self, messages):
        """显示消息对话"""
        self.list_ctrl.DeleteAllItems()
        self.list_ctrl.InsertColumn(0, "内容", width=600)
        self.list_ctrl.InsertColumn(1, "发送者", width=100)
        self.list_ctrl.InsertColumn(2, "时间", width=150)

        # 保存当前消息记录
        self.current_conversation = messages

        for i, message in enumerate(messages):
            content = message.get('message', '')
            sender = message.get('sender', '')
            time = message.get('time', '')

            if len(content) > 100:
                content = content[:100] + '...'

            index = self.list_ctrl.InsertItem(i, content)
            self.list_ctrl.SetItem(index, 1, sender)
            self.list_ctrl.SetItem(index, 2, time)

    def create_message_input_panel(self):
        """创建消息输入面板"""
        # 如果已有输入面板，先删除
        if hasattr(self, 'message_input_panel'):
            self.message_input_panel.Destroy()

        # 获取列表的父窗口
        list_parent = self.list_ctrl.GetParent()

        # 创建消息输入面板
        self.message_input_panel = wx.Panel(list_parent)
        input_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 消息输入框
        self.message_input_ctrl = wx.TextCtrl(self.message_input_panel, style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER)
        input_sizer.Add(self.message_input_ctrl, 1, wx.ALL | wx.EXPAND, 5)

        # 发送按钮
        self.send_button = wx.Button(self.message_input_panel, label="发送")
        self.send_button.Bind(wx.EVT_BUTTON, self.on_send_message)
        input_sizer.Add(self.send_button, 0, wx.ALL | wx.EXPAND, 5)

        # 关闭按钮
        self.close_button = wx.Button(self.message_input_panel, label="关闭")
        self.close_button.Bind(wx.EVT_BUTTON, self.on_close_message)
        input_sizer.Add(self.close_button, 0, wx.ALL | wx.EXPAND, 5)

        self.message_input_panel.SetSizer(input_sizer)

        # 重新布局窗口
        self.Layout()

        # 设置焦点到输入框
        self.message_input_ctrl.SetFocus()

    def on_send_message(self, event):
        """发送消息"""
        try:
            if not hasattr(self, 'current_touid') or not self.current_touid:
                wx.MessageBox("请先选择要发送消息的用户", "提示", wx.OK | wx.ICON_INFORMATION)
                return

            content = self.message_input_ctrl.GetValue().strip()
            if not content:
                wx.MessageBox("消息内容不能为空", "提示", wx.OK | wx.ICON_WARNING)
                return

            # 获取对方用户名
            username = ""
            if hasattr(self, 'current_messages'):
                for msg in self.current_messages:
                    if msg.get('touid') == self.current_touid:
                        username = msg.get('username', '')
                        break

            # 发送消息
            success = self.message_manager.send_message(
                self.current_forum,
                self.current_touid,
                f"回复: {content[:20]}..." if len(content) > 20 else content,
                content
            )

            if success:
                wx.MessageBox("消息发送成功", "成功", wx.OK | wx.ICON_INFORMATION)
                self.message_input_ctrl.Clear()
                # 刷新消息记录
                self.load_message_detail(self.current_touid)
            else:
                wx.MessageBox("消息发送失败", "错误", wx.OK | wx.ICON_ERROR)

        except Exception as e:
            print(f"发送消息错误: {e}")
            wx.MessageBox("消息发送失败", "错误", wx.OK | wx.ICON_ERROR)

    def show_floor_editor(self, floor_index):
        """显示楼层编辑器"""
        try:
            if not hasattr(self, 'current_posts') or floor_index >= len(self.current_posts):
                return

            post = self.current_posts[floor_index]
            original_content = post.get('message', '')
            username = post.get('username', '')
            floor = floor_index + 1

            # 创建编辑对话框
            dialog = wx.Dialog(self, title=f"编辑{floor}楼 - {username}", size=(600, 400))
            panel = wx.Panel(dialog)
            sizer = wx.BoxSizer(wx.VERTICAL)

            # 楼层信息（只读）
            info_label = wx.StaticText(panel, label=f"{floor}楼 {username} 的内容:")
            sizer.Add(info_label, 0, wx.ALL | wx.EXPAND, 5)

            # 内容编辑框
            content_ctrl = wx.TextCtrl(panel, value=original_content, style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER)
            sizer.Add(content_ctrl, 1, wx.ALL | wx.EXPAND, 5)

            # 按钮面板
            button_panel = wx.Panel(panel)
            button_sizer = wx.BoxSizer(wx.HORIZONTAL)
            save_button = wx.Button(button_panel, label="保存")
            cancel_button = wx.Button(button_panel, label="取消")
            button_sizer.Add(save_button, 0, wx.ALL, 5)
            button_sizer.Add(cancel_button, 0, wx.ALL, 5)
            button_panel.SetSizer(button_sizer)
            sizer.Add(button_panel, 0, wx.ALL | wx.ALIGN_CENTER, 5)

            panel.SetSizer(sizer)

            # 绑定键盘事件
            def on_char(event):
                keycode = event.GetKeyCode()
                if keycode == wx.WXK_ESCAPE:
                    dialog.EndModal(wx.ID_CANCEL)
                elif keycode == wx.WXK_BACK:
                    dialog.EndModal(wx.ID_CANCEL)
                else:
                    event.Skip()

            content_ctrl.Bind(wx.EVT_CHAR, on_char)
            save_button.Bind(wx.EVT_BUTTON, lambda e: dialog.EndModal(wx.ID_OK))
            cancel_button.Bind(wx.EVT_BUTTON, lambda e: dialog.EndModal(wx.ID_CANCEL))

            # 显示对话框
            if dialog.ShowModal() == wx.ID_OK:
                new_content = content_ctrl.GetValue().strip()
                if new_content != original_content:
                    # 这里可以添加保存编辑的逻辑
                    wx.MessageBox("编辑功能暂未实现", "提示", wx.OK | wx.ICON_INFORMATION)

            dialog.Destroy()

        except Exception as e:
            print(f"显示楼层编辑器错误: {e}")

    def on_close_message(self, event):
        """关闭消息界面"""
        try:
            # 删除消息输入面板
            if hasattr(self, 'message_input_panel'):
                self.message_input_panel.Destroy()
                delattr(self, 'message_input_panel')

            # 返回消息列表
            self.load_messages()

        except Exception as e:
            print(f"关闭消息界面错误: {e}")

    def show_account_manager(self):
        """显示账户管理界面"""
        account_manager = AccountManager(self.config_manager, self)
        account_manager.ShowModal()
        account_manager.Destroy()

        # 刷新账户列表
        self.accounts = self.config_manager.get_forum_list()

        # 如果没有账户，退出程序
        if not self.accounts:
            self.Close()
        elif self.current_forum is None:
            # 如果还没有选择论坛，显示账户选择界面
            self.show_account_selection()

    def set_window_icon(self):
        """设置窗口图标"""
        # 如果有图标文件，可以在这里设置
        pass

    def set_window_style(self):
        """设置窗口样式"""
        # 设置窗口样式，支持无障碍
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
        self.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))

    def __del__(self):
        """析构函数"""
        # 登出所有论坛
        self.auth_manager.logout_all()