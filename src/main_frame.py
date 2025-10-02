# -*- coding: utf-8 -*-
"""
主窗口框架
程序的主界面框架
"""

import wx
import wx.dataview
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

        # 焦点管理
        self.saved_list_index = -1
        self.saved_page_info = None  # 保存页面信息：{page: int, content_type: str, params: dict}

        # 获取账户列表
        self.accounts = self.config_manager.get_forum_list()

        # 创建主窗口
        super().__init__(None, title="论坛助手", size=(1024, 768))

        # 最大化窗口
        self.Maximize()

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
        self.list_panel.SetName("列表面板")  # 设置面板名称
        list_sizer = wx.BoxSizer(wx.VERTICAL)

        # 创建数据视图列表控件 - 支持更好的文本处理和自动换行
        self.list_ctrl = wx.dataview.DataViewListCtrl(self.list_panel, style=wx.dataview.DV_SINGLE)
        # 设置控件标签
        self.list_ctrl.SetName("项目")
        self.list_ctrl.AppendTextColumn("内容", mode=wx.dataview.DATAVIEW_CELL_INERT, width=2000)
        # 创建数据存储字典，用于存储每行对应的帖子ID
        self.list_data = []  # 存储每行的数据信息
        self.list_ctrl.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self.on_list_selection)
        self.list_ctrl.Bind(wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self.on_list_activated)
        self.list_ctrl.Bind(wx.EVT_KEY_DOWN, self.on_list_key_down)
        self.list_ctrl.Bind(wx.EVT_SET_FOCUS, self.on_list_focus)

        list_sizer.Add(self.list_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        self.list_panel.SetSizer(list_sizer)

    def create_menu(self):
        """创建菜单栏"""
        menubar = wx.MenuBar()

        # 文件菜单
        file_menu = wx.Menu()
        account_item = file_menu.Append(wx.ID_ANY, "账户管理", "管理论坛账户")
        self.Bind(wx.EVT_MENU, self.on_account_management, account_item)

        switch_account_item = file_menu.Append(wx.ID_ANY, "切换账户", "切换到其他账户")
        self.Bind(wx.EVT_MENU, self.on_switch_account, switch_account_item)

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
            self.SetTitle(f"{forum_name}-<{nickname}>-论坛助手")

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
            forum_types = forum.get('types', {})

            # 添加论坛主分类
            forum_item = self.tree_ctrl.AppendItem(root, forum_name)

            # 存储论坛数据到节点
            forum_data = {
                'type': 'forum',
                'fid': forum_id,
                'name': forum_name
            }
            self.tree_ctrl.SetItemData(forum_item, forum_data)

            # 添加typeid1子分类
            typeid1_list = forum_types.get('typeid1', [])
            if typeid1_list:
                for type1 in typeid1_list:
                    type1_name = type1.get('name', '')
                    type1_id = type1.get('id', '')

                    # 过滤掉"分类▼"、"状态▼"和其他分类节点，以及id为0的项目
                    if ('▼' in type1_name or '分类' in type1_name or '状态' in type1_name or
                        '数据' in type1_name or '表' in type1_name or type1_id == 0):
                        continue

                    type1_item = self.tree_ctrl.AppendItem(forum_item, type1_name)

                    # 存储typeid1数据到节点
                    type1_data = {
                        'type': 'typeid1',
                        'fid': forum_id,
                        'typeid1': type1_id,
                        'name': type1_name,
                        'parent_name': forum_name
                    }
                    self.tree_ctrl.SetItemData(type1_item, type1_data)

                    # 添加typeid2子分类
                    typeid2_list = type1.get('typeid2', [])
                    if typeid2_list:
                        for type2 in typeid2_list:
                            type2_name = type2.get('name', '')
                            type2_id = type2.get('id', '')

                            # 过滤掉"状态▼"、"分类▼"和其他分类节点，以及id为0的项目
                            if ('▼' in type2_name or '分类' in type2_name or '状态' in type2_name or
                                '数据' in type2_name or '表' in type2_name or type2_id == 0):
                                continue

                            type2_item = self.tree_ctrl.AppendItem(type1_item, type2_name)

                            # 存储typeid2数据到节点
                            type2_data = {
                                'type': 'typeid2',
                                'fid': forum_id,
                                'typeid1': type1_id,
                                'typeid2': type2_id,
                                'name': type2_name,
                                'parent_name': type1_name
                            }
                            self.tree_ctrl.SetItemData(type2_item, type2_data)

            # 添加typeid3子分类（直接挂在论坛下）
            typeid3_list = forum_types.get('typeid3', [])
            if typeid3_list:
                for type3 in typeid3_list:
                    type3_name = type3.get('name', '')
                    type3_id = type3.get('id', '')

                    # 过滤掉"▼"、"分类"、"状态"和其他分类节点，以及id为0的项目
                    if ('▼' in type3_name or '分类' in type3_name or '状态' in type3_name or
                        '数据' in type3_name or '表' in type3_name or type3_id == 0):
                        continue

                    type3_item = self.tree_ctrl.AppendItem(forum_item, type3_name)

                    # 存储typeid3数据到节点
                    type3_data = {
                        'type': 'typeid3',
                        'fid': forum_id,
                        'typeid3': type3_id,
                        'name': type3_name,
                        'parent_name': forum_name
                    }
                    self.tree_ctrl.SetItemData(type3_item, type3_data)

            # 添加typeid4子分类（直接挂在论坛下）
            typeid4_list = forum_types.get('typeid4', [])
            if typeid4_list:
                for type4 in typeid4_list:
                    type4_name = type4.get('name', '')
                    type4_id = type4.get('id', '')

                    # 过滤掉"▼"、"分类"、"状态"和其他分类节点，以及id为0的项目
                    if ('▼' in type4_name or '分类' in type4_name or '状态' in type4_name or
                        '数据' in type4_name or '表' in type4_name or type4_id == 0):
                        continue

                    type4_item = self.tree_ctrl.AppendItem(forum_item, type4_name)

                    # 存储typeid4数据到节点
                    type4_data = {
                        'type': 'typeid4',
                        'fid': forum_id,
                        'typeid4': type4_id,
                        'name': type4_name,
                        'parent_name': forum_name
                    }
                    self.tree_ctrl.SetItemData(type4_item, type4_data)

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

            # 获取存储在item data中的板块信息
            item_data = self.tree_ctrl.GetItemData(item)

            # 处理不同类型的数据
            if isinstance(item_data, dict):
                # 新的层级结构数据
                data_type = item_data.get('type')
                fid = item_data.get('fid')

                if data_type == 'forum':
                    # 论坛主分类
                    self.load_content(text, fid)
                elif data_type in ['typeid1', 'typeid2', 'typeid3', 'typeid4']:
                    # 子分类，需要传递分类参数
                    self.load_content_with_type(text, item_data)
                else:
                    # 未知类型，默认处理
                    self.load_content(text, fid)
            else:
                # 旧的简单数据格式（直接是fid）
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
            selected = self.list_ctrl.GetSelectedRow()
            if selected != -1:
                # 直接调用激活逻辑，不需要创建复杂的事件对象
                self.handle_row_activation(selected)
            else:
                event.Skip()
        else:
            event.Skip()

    def go_back_to_previous_list(self):
        """返回之前的列表"""
        try:
            # 优先尝试恢复到保存的页面信息
            if self.saved_page_info and self.restore_to_correct_page():
                # 成功恢复到正确页面，现在恢复焦点
                if self.saved_list_index != -1 and self.saved_list_index < self.list_ctrl.GetItemCount():
                    wx.CallAfter(self.reset_keyboard_cursor, self.saved_list_index)
            elif hasattr(self, 'previous_content_type') and hasattr(self, 'previous_content_params'):
                # 回退到原来的恢复逻辑
                content_type = self.previous_content_type
                params = self.previous_content_params

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
            self.SetTitle(f"{forum_name_text}-<{self.get_user_nickname()}>-论坛助手")

            # 显示内容
            self.display_threads_and_restore_focus(threads, pagination, 'thread_list')
        except Exception as e:
            print(f"加载板块内容错误: {e}")

    def load_latest_threads_and_restore_focus(self):
        """加载最新发表并恢复焦点"""
        result = self.forum_client.get_home_content(self.current_forum, "latest")
        self.SetTitle(f"{self.current_forum}-<{self.get_user_nickname()}>-论坛助手")
        self.display_threads_and_restore_focus(result.get('threadlist', []), result.get('pagination', {}), 'home_content')
        self.current_orderby = 'latest'

    def load_latest_replies_and_restore_focus(self):
        """加载最新回复并恢复焦点"""
        result = self.forum_client.get_home_content(self.current_forum, "lastpost")
        self.SetTitle(f"{self.current_forum}-<{self.get_user_nickname()}>-论坛助手")
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

                self.SetTitle(f"{self.current_forum}-<{self.get_user_nickname()}>-论坛助手")
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

                self.SetTitle(f"{self.current_forum}-<{self.get_user_nickname()}>-论坛助手")
                self.display_threads_and_restore_focus(formatted_threads, result.get('pagination', {}), 'user_posts')

    def search_content_and_restore_focus(self, keyword):
        """搜索内容并恢复焦点"""
        result = self.forum_client.search(self.current_forum, keyword)
        self.SetTitle(f"{self.current_forum}-<{self.get_user_nickname()}>-论坛助手")
        self.display_threads_and_restore_focus(result.get('threadlist', []), result.get('pagination', {}), 'search_result')

    
  
    def reset_keyboard_cursor(self, target_index):
        """重置键盘游标位置到指定索引 - DataViewListCtrl版本"""
        try:
            if 0 <= target_index < self.list_ctrl.GetItemCount():
                # 取消所有选择
                self.list_ctrl.UnselectAll()

                # 选择目标项目
                self.list_ctrl.SelectRow(target_index)

                # DataViewListCtrl 的 EnsureVisible 需要 DataViewItem 对象
                # 这里暂时跳过 EnsureVisible，因为 SelectRow 应该会自动滚动到可见位置
                # self.list_ctrl.EnsureVisible(target_index)

                # 设置焦点到列表控件
                self.list_ctrl.SetFocus()

        except Exception as e:
            print(f"重置键盘游标错误: {e}")

    def get_current_page_params(self):
        """获取当前页面的参数"""
        params = {}
        if hasattr(self, 'current_content_type'):
            if self.current_content_type == 'thread_list' and hasattr(self, 'current_fid'):
                params['fid'] = self.current_fid
            elif self.current_content_type == 'user_threads' and hasattr(self, 'current_uid'):
                params['uid'] = self.current_uid
            elif self.current_content_type == 'user_posts' and hasattr(self, 'current_uid'):
                params['uid'] = self.current_uid
            elif self.current_content_type == 'search_result' and hasattr(self, 'current_keyword'):
                params['keyword'] = self.current_keyword
            elif self.current_content_type == 'home_content' and hasattr(self, 'current_orderby'):
                params['orderby'] = self.current_orderby
        return params

    def restore_to_correct_page(self):
        """恢复到正确的页面"""
        if not self.saved_page_info:
            return False

        try:
            page_info = self.saved_page_info
            content_type = page_info.get('content_type')
            page = page_info.get('page', 1)
            params = page_info.get('params', {})

            # 根据内容类型跳转到对应页面
            if content_type == 'thread_list' and 'fid' in params:
                # 跳转到指定板块的指定页面
                result = self.forum_client.get_thread_list(self.current_forum, params['fid'], page)
                self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'thread_list')
                return True
            elif content_type == 'user_threads' and 'uid' in params:
                # 跳转到用户发表的指定页面
                result = self.forum_client.get_user_threads(self.current_forum, params['uid'], page)
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
                self.display_threads(formatted_threads, result.get('pagination', {}), 'user_threads')
                return True
            elif content_type == 'user_posts' and 'uid' in params:
                # 跳转到用户回复的指定页面
                result = self.forum_client.get_user_posts(self.current_forum, params['uid'], page)
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
                            'dateline_fmt': thread_info.get('dateline_fmt', ''),
                            'views': thread_info.get('views', 0),
                            'posts': thread_info.get('posts', 0),
                            'forumname': item.get('forumname', ''),
                            'lastpost_fmt': post_info.get('dateline_fmt', ''),
                            'lastusername': post_info.get('username', '') or thread_info.get('lastusername', '')
                        }
                        formatted_threads.append(formatted_thread)
                self.display_threads(formatted_threads, result.get('pagination', {}), 'user_posts')
                return True
            elif content_type == 'search_result' and 'keyword' in params:
                # 跳转到搜索结果的指定页面
                result = self.forum_client.search(self.current_forum, params['keyword'], page)
                self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'search_result')
                return True
            elif content_type == 'home_content' and 'orderby' in params:
                # 跳转到首页内容的指定页面
                result = self.forum_client.get_home_content(self.current_forum, params['orderby'], page)
                self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'home_content')
                return True

        except Exception as e:
            print(f"恢复到正确页面错误: {e}")

        return False

    def display_threads_and_restore_focus(self, threads, pagination=None, content_type='thread_list'):
        """显示帖子列表并恢复焦点"""
        # 先显示内容
        self.display_threads(threads, pagination, content_type)

        # 恢复之前保存的索引
        if self.saved_list_index != -1 and self.saved_list_index < self.list_ctrl.GetItemCount():
            # 直接设置到保存的索引
            self.list_ctrl.SelectRow(self.saved_list_index)
            # DataViewListCtrl 的 SelectRow 应该会自动处理可见性
            self.list_ctrl.SetFocus()

            # 重置键盘游标位置到记忆的位置
            # 这是解决上下光标浏览从记忆位置开始的关键
            wx.CallAfter(self.reset_keyboard_cursor, self.saved_list_index)
        elif hasattr(self, 'previous_selected_index') and hasattr(self, 'previous_selected_tid'):
            # 回退到通过tid查找
            found_index = -1
            for i in range(self.list_ctrl.GetItemCount()):
                # 从 list_data 数组获取帖子ID
                if i < len(self.list_data):
                    item_tid = self.list_data[i].get('tid', 0)
                else:
                    item_tid = 0
                if item_tid > 0 and item_tid == self.previous_selected_tid:
                    found_index = i
                    break

            if found_index != -1:
                self.list_ctrl.SelectRow(found_index)
                # DataViewListCtrl 的 SelectRow 应该会自动处理可见性
                self.list_ctrl.SetFocus()
                # 重置键盘游标位置
                wx.CallAfter(self.reset_keyboard_cursor, found_index)

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

            # 获取存储在item data中的板块信息
            item_data = self.tree_ctrl.GetItemData(selected_item)

            # 处理不同类型的数据
            if isinstance(item_data, dict):
                # 新的层级结构数据
                data_type = item_data.get('type')
                fid = item_data.get('fid')

                if data_type == 'forum':
                    # 论坛主分类
                    self.load_content(text, fid)
                elif data_type in ['typeid1', 'typeid2', 'typeid3', 'typeid4']:
                    # 子分类，需要传递分类参数
                    self.load_content_with_type(text, item_data)
                else:
                    # 未知类型，默认处理
                    self.load_content(text, fid)
            else:
                # 旧的简单数据格式（直接是fid）
                fid = item_data if item_data else None
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

    def on_list_focus(self, event):
        """列表获得焦点事件 - 确保有选中项以便屏幕阅读器朗读"""
        try:
            # 如果列表有内容但没有选中项，自动选择第一项
            if self.list_ctrl.GetItemCount() > 0 and self.list_ctrl.GetSelectedRow() == -1:
                self.list_ctrl.SelectRow(0)
                self.list_ctrl.SetFocus()
        except Exception as e:
            print(f"列表焦点事件处理错误: {e}")
        event.Skip()

    def on_list_selection(self, event):
        """列表选择事件 - DataViewListCtrl版本"""
        try:
            # DataViewListCtrl 的选择事件处理
            pass
        except Exception as e:
            print(f"列表选择事件处理错误: {e}")
        event.Skip()

    def on_list_activated(self, event):
        """列表激活事件 - 处理分页控制和帖子详情加载"""
        try:
            selected_row = self.list_ctrl.GetSelectedRow()
            if selected_row != -1:
                self.handle_row_activation(selected_row)
        except Exception as e:
            print(f"列表激活事件处理错误: {e}")
        event.Skip()

    def handle_row_activation(self, selected_row):
        """处理行激活的通用逻辑"""
        try:
            # 检查行索引是否有效
            if selected_row < 0 or selected_row >= len(self.list_data):
                return

            # 从 list_data 数组获取项目数据
            item_data = self.list_data[selected_row]

            # 处理分页控制
            if item_data.get('type') == 'pagination':
                action = item_data.get('action')
                if action == 'prev':
                    self.load_previous_page()
                elif action == 'next':
                    self.load_next_page()
                elif action == 'jump':
                    self.show_page_jump_dialog()
                elif action == 'reply':
                    self.show_reply_dialog()
            else:  # 普通帖子项或消息项
                # 根据内容类型处理不同的操作
                if hasattr(self, 'current_content_type'):
                    if self.current_content_type in ['thread_list', 'search_result', 'user_threads', 'user_posts', 'home_content']:
                        # 加载帖子详情
                        tid = item_data.get('tid', 0)
                        if tid and tid > 0:
                            self.load_thread_detail(tid)
                    elif self.current_content_type == 'message_list':
                        # 加载消息详情
                        touid = item_data.get('touid', 0)
                        if touid and touid > 0:
                            self.load_message_detail(touid)
                    elif self.current_content_type == 'thread_detail':
                        # 帖子详情中的楼层编辑
                        self.show_floor_editor(selected_row)

        except Exception as e:
            print(f"处理行激活错误: {e}")

    def on_search(self, event):
        """搜索事件"""
        keyword = self.search_ctrl.GetValue().strip()
        if keyword:
            self.search_content(keyword)

    def on_account_management(self, event):
        """账户管理事件"""
        self.show_account_manager()

    def on_switch_account(self, event):
        """切换账户事件"""
        # 刷新账户列表
        self.accounts = self.config_manager.get_forum_list()

        # 如果没有账户，显示账户管理界面
        if not self.accounts:
            wx.MessageBox("暂无账户，请先添加账户", "提示", wx.OK | wx.ICON_INFORMATION)
            self.show_account_manager()
        else:
            # 显示账户选择界面
            self.show_account_selection()

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

    def load_content_with_type(self, text, type_data):
        """加载带有分类类型的内容"""
        # 清理消息界面（如果存在）
        self.hide_message_interface()

        # 获取分类参数
        data_type = type_data.get('type')
        fid = type_data.get('fid')

        # 构建API参数
        api_params = {
            'fid': fid
        }

        # 根据类型添加相应的分类ID
        if data_type == 'typeid1':
            api_params['typeid1'] = type_data.get('typeid1')
        elif data_type == 'typeid2':
            api_params['typeid1'] = type_data.get('typeid1')
            api_params['typeid2'] = type_data.get('typeid2')
        elif data_type == 'typeid3':
            api_params['typeid3'] = type_data.get('typeid3')
        elif data_type == 'typeid4':
            api_params['typeid4'] = type_data.get('typeid4')

        # 加载分类内容
        self.load_forum_section_with_type(text, api_params)

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

    def load_forum_section_with_type(self, section_name, api_params):
        """加载带有分类参数的论坛板块"""
        if not api_params.get('fid'):
            return

        self.current_fid = api_params.get('fid')
        result = self.forum_client.get_thread_list_with_type(self.current_forum, api_params)
        print(f"DEBUG: 加载分类板块 {section_name}, 参数: {api_params}, 返回结果: {result}")

        # 如果第一页为空但总页数大于1，自动查找有内容的第一页
        threadlist = result.get('threadlist', [])
        pagination = result.get('pagination', {})
        total_page = pagination.get('totalpage', 1)

        if not threadlist and total_page > 1:
            print(f"DEBUG: 第一页为空，自动查找有内容的第一页...")

            # 使用二分查找快速找到有内容的第一页
            first_content_page = self._find_first_content_page(api_params, total_page)

            if first_content_page > 1:
                print(f"DEBUG: 找到有内容的第一页: 第{first_content_page}页")
                result = self.forum_client.get_thread_list_with_type(self.current_forum, api_params, first_content_page)
                print(f"DEBUG: 第{first_content_page}页结果: {result}")

                # 保存偏移信息，用于显示逻辑
                pagination['page_offset'] = first_content_page - 1
                pagination['real_total_page'] = total_page
                pagination['totalpage'] = total_page - first_content_page + 1  # 调整显示的总页数
                pagination['page'] = 1  # 强制显示为第1页

                # 使用修改后的分页信息
                self.display_threads(result.get('threadlist', []), pagination, 'thread_list', api_params)
            else:
                print(f"DEBUG: 未找到有内容的页面")
                self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'thread_list', api_params)
        else:
            # 第一页有内容，正常显示
            self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'thread_list', api_params)

    def _find_first_content_page(self, api_params, total_page):
        """使用二分查找快速定位有内容的第一页"""
        try:
            print(f"DEBUG: 开始二分查找，总页数: {total_page}")

            left = 1
            right = total_page
            first_content_page = total_page + 1  # 默认为没有找到

            while left <= right:
                mid = (left + right) // 2
                print(f"DEBUG: 检查第{mid}页...")

                # 检查中间页是否有内容
                result = self.forum_client.get_thread_list_with_type(self.current_forum, api_params, mid)
                try:
                    print(f"DEBUG: 第{mid}页API返回: {result}")
                except Exception as e:
                    print(f"DEBUG: 第{mid}页API返回编码错误: {e}")

                if result and isinstance(result, dict):
                    # 检查不同的可能结果结构
                    if result.get('result') == 1:
                        # 新版本API结构
                        threadlist = result.get('message', {}).get('threadlist', [])
                    elif 'threadlist' in result:
                        # 旧版本API结构
                        threadlist = result.get('threadlist', [])
                    else:
                        print(f"DEBUG: 第{mid}页未知API结构，向右查找")
                        left = mid + 1
                        continue

                    if threadlist:  # 找到有内容的页面
                        first_content_page = mid
                        right = mid - 1  # 继续向左查找更早的有内容页面
                        print(f"DEBUG: 第{mid}页有内容({len(threadlist)}个帖子)，继续向左查找")
                    else:  # 没有内容，向右查找
                        left = mid + 1
                        print(f"DEBUG: 第{mid}页无内容，向右查找")
                else:
                    print(f"DEBUG: 第{mid}页API调用失败或返回格式错误，向右查找")
                    left = mid + 1

            if first_content_page <= total_page:
                print(f"DEBUG: 找到有内容的第一页: 第{first_content_page}页")
                return first_content_page
            else:
                print(f"DEBUG: 所有页面都没有内容，返回第1页")
                return 1

        except Exception as e:
            print(f"DEBUG: 查找第一页内容时出错: {e}")
            return 1  # 出错时返回第1页

    def search_content(self, keyword):
        """搜索内容"""
        self.current_keyword = keyword
        result = self.forum_client.search(self.current_forum, keyword)
        self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'search_result')

    def display_threads(self, threads, pagination=None, content_type='thread_list', api_params=None):
        """显示帖子列表 - DataViewListCtrl版本"""
        self.list_ctrl.DeleteAllItems()
        # 清空数据存储
        self.list_data = []

        # 保存当前内容类型和分页信息
        self.current_content_type = content_type
        self.current_pagination = pagination or {}
        self.current_threads = threads

        # 保存API参数用于分页操作
        self.current_api_params = api_params or {}

        for thread in threads:
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

            # 检查并清理任何包含"数据: XXX"的多余信息
            # 移除任何包含"数据:"的模式，包括中英文
            import re
            # 更强的正则表达式，处理各种可能的格式
            display_text = re.sub(r';?\s*数据:\s*\d+\s*', '', display_text)
            display_text = re.sub(r';?\s*data:\s*\d+\s*', '', display_text, flags=re.IGNORECASE)
            # 处理可能的分号分隔符格式
            display_text = re.sub(r';\s*数据:\s*\d+.*$', '', display_text)
            display_text = re.sub(r';\s*data:\s*\d+.*$', '', display_text, flags=re.IGNORECASE)
            # 如果数据信息在末尾没有分号分隔，也要处理
            display_text = re.sub(r'\s+数据:\s*\d+.*$', '', display_text)
            display_text = re.sub(r'\s+data:\s*\d+.*$', '', display_text, flags=re.IGNORECASE)
            # 清理末尾可能的分号和空格
            display_text = re.sub(r';+\s*$', '', display_text)
            display_text = display_text.strip()

            # 使用 DataViewListCtrl 的 AppendItem 方法，只显示内容列
            # 将帖子ID等信息存储在 list_data 数组中
            self.list_ctrl.AppendItem([display_text])
            self.list_data.append({
                'tid': thread.get('tid', 0),
                'type': 'thread'
            })

        # 根据设计文档添加4个分页控制项
        # 如果没有分页信息，创建默认分页信息
        if not pagination or not isinstance(pagination, dict):
            pagination = {'page': 1, 'totalpage': 1}

        # 总是添加分页控制，即使只有一页
        self.add_pagination_controls(pagination)

    
    def add_pagination_controls(self, pagination):
        """根据设计文档添加4个分页控制项 - DataViewListCtrl版本"""
        current_page = pagination.get('page', 1)
        total_page = pagination.get('totalpage', 1)

        # 1. 上一页控制项
        if current_page > 1:
            prev_text = f"上一页({current_page - 1})"
            # 应用数据清理逻辑，移除"数据: XXX"信息
            import re
            cleaned_text = re.sub(r';?\s*数据:\s*\d+\s*', '', prev_text)
            cleaned_text = re.sub(r';?\s*data:\s*\d+\s*', '', cleaned_text, flags=re.IGNORECASE)
            cleaned_text = re.sub(r';\s*数据:\s*\d+.*$', '', cleaned_text)
            cleaned_text = re.sub(r';\s*data:\s*\d+.*$', '', cleaned_text, flags=re.IGNORECASE)
            cleaned_text = re.sub(r'\s+数据:\s*\d+.*$', '', cleaned_text)
            cleaned_text = re.sub(r'\s+data:\s*\d+.*$', '', cleaned_text, flags=re.IGNORECASE)
            cleaned_text = re.sub(r';+\s*$', '', cleaned_text)
            cleaned_text = cleaned_text.strip()
            self.list_ctrl.AppendItem([cleaned_text])
            self.list_data.append({'type': 'pagination', 'action': 'prev', 'page': current_page - 1})

        # 2. 下一页控制项
        if current_page < total_page:
            next_text = f"下一页({current_page + 1})"
            # 应用数据清理逻辑，移除"数据: XXX"信息
            import re
            cleaned_text = re.sub(r';?\s*数据:\s*\d+\s*', '', next_text)
            cleaned_text = re.sub(r';?\s*data:\s*\d+\s*', '', cleaned_text, flags=re.IGNORECASE)
            cleaned_text = re.sub(r';\s*数据:\s*\d+.*$', '', cleaned_text)
            cleaned_text = re.sub(r';\s*data:\s*\d+.*$', '', cleaned_text, flags=re.IGNORECASE)
            cleaned_text = re.sub(r'\s+数据:\s*\d+.*$', '', cleaned_text)
            cleaned_text = re.sub(r'\s+data:\s*\d+.*$', '', cleaned_text, flags=re.IGNORECASE)
            cleaned_text = re.sub(r';+\s*$', '', cleaned_text)
            cleaned_text = cleaned_text.strip()
            self.list_ctrl.AppendItem([cleaned_text])
            self.list_data.append({'type': 'pagination', 'action': 'next', 'page': current_page + 1})

        # 3. 当前页码跳转控制项
        jump_text = f"第{current_page}页/共{total_page}页 (回车跳转)"
        # 应用数据清理逻辑，移除"数据: XXX"信息
        import re
        cleaned_text = re.sub(r';?\s*数据:\s*\d+\s*', '', jump_text)
        cleaned_text = re.sub(r';?\s*data:\s*\d+\s*', '', cleaned_text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r';\s*数据:\s*\d+.*$', '', cleaned_text)
        cleaned_text = re.sub(r';\s*data:\s*\d+.*$', '', cleaned_text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r'\s+数据:\s*\d+.*$', '', cleaned_text)
        cleaned_text = re.sub(r'\s+data:\s*\d+.*$', '', cleaned_text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r';+\s*$', '', cleaned_text)
        cleaned_text = cleaned_text.strip()
        self.list_ctrl.AppendItem([cleaned_text])
        self.list_data.append({'type': 'pagination', 'action': 'jump', 'current_page': current_page, 'total_page': total_page})

        # 4. 回复帖子控制项（仅在帖子详情时显示）
        if self.current_content_type == 'thread_detail':
            reply_text = "回复帖子"
            # 应用数据清理逻辑，移除"数据: XXX"信息
            import re
            cleaned_text = re.sub(r';?\s*数据:\s*\d+\s*', '', reply_text)
            cleaned_text = re.sub(r';?\s*data:\s*\d+\s*', '', cleaned_text, flags=re.IGNORECASE)
            cleaned_text = re.sub(r';\s*数据:\s*\d+.*$', '', cleaned_text)
            cleaned_text = re.sub(r';\s*data:\s*\d+.*$', '', cleaned_text, flags=re.IGNORECASE)
            cleaned_text = re.sub(r'\s+数据:\s*\d+.*$', '', cleaned_text)
            cleaned_text = re.sub(r'\s+data:\s*\d+.*$', '', cleaned_text, flags=re.IGNORECASE)
            cleaned_text = re.sub(r';+\s*$', '', cleaned_text)
            cleaned_text = cleaned_text.strip()
            self.list_ctrl.AppendItem([cleaned_text])
            self.list_data.append({'type': 'pagination', 'action': 'reply'})

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

                # 保存当前选中的项目索引和页面信息
                selected = self.list_ctrl.GetSelectedRow()
                if selected != -1 and selected < len(self.list_data):
                    self.previous_selected_index = selected
                    # 从 list_data 数组获取帖子ID
                    self.previous_selected_tid = self.list_data[selected].get('tid', 0)
                    # 保存当前索引和页面信息
                    self.saved_list_index = selected

                    # 保存当前页面信息，用于返回时精确定位
                    self.saved_page_info = {
                        'page': getattr(self, 'current_pagination', {}).get('page', 1),
                        'content_type': getattr(self, 'current_content_type', ''),
                        'params': self.get_current_page_params()
                    }

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

            # 计算真实的页面号（考虑偏移）
            page_offset = self.current_pagination.get('page_offset', 0)
            real_next_page = next_page + page_offset

            # 根据当前内容类型加载下一页
            if self.current_content_type == 'thread_list' and hasattr(self, 'current_fid'):
                if hasattr(self, 'current_api_params') and self.current_api_params:
                    # 使用API参数加载分类内容
                    result = self.forum_client.get_thread_list_with_type(self.current_forum, self.current_api_params, real_next_page)
                    # 保持页面偏移信息
                    new_pagination = result.get('pagination', {})
                    new_pagination['page_offset'] = page_offset
                    new_pagination['real_total_page'] = self.current_pagination.get('real_total_page', new_pagination.get('totalpage', 1))
                    new_pagination['totalpage'] = new_pagination.get('totalpage', 1) - page_offset
                    new_pagination['page'] = next_page
                    self.display_threads(result.get('threadlist', []), new_pagination, 'thread_list', self.current_api_params)
                else:
                    # 普通板块内容
                    result = self.forum_client.get_thread_list(self.current_forum, self.current_fid, real_next_page)
                    self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'thread_list')
                # 设置键盘游标到第一项
                wx.CallAfter(self.reset_keyboard_cursor, 0)
            elif self.current_content_type == 'search_result' and hasattr(self, 'current_keyword'):
                result = self.forum_client.search(self.current_forum, self.current_keyword, next_page)
                self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'search_result')
                # 设置键盘游标到第一项
                wx.CallAfter(self.reset_keyboard_cursor, 0)
            elif self.current_content_type == 'user_threads' and hasattr(self, 'current_uid'):
                result = self.forum_client.get_user_threads(self.current_forum, self.current_uid, next_page)
                self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'user_threads')
                # 设置键盘游标到第一项
                wx.CallAfter(self.reset_keyboard_cursor, 0)
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
                # 设置键盘游标到第一项
                wx.CallAfter(self.reset_keyboard_cursor, 0)
            elif self.current_content_type == 'home_content' and hasattr(self, 'current_orderby'):
                # 添加首页内容的分页支持
                result = self.forum_client.get_home_content(self.current_forum, self.current_orderby, next_page)
                self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'home_content')
                # 设置键盘游标到第一项
                wx.CallAfter(self.reset_keyboard_cursor, 0)
            elif self.current_content_type == 'thread_detail' and hasattr(self, 'current_tid'):
                # 添加帖子详情的分页支持
                result = self.forum_client.get_thread_detail(self.current_forum, self.current_tid, next_page)
                self.display_posts(result.get('postlist', []), result.get('pagination', {}), result.get('thread_info', {}))
                # 设置键盘游标到第一项（楼主）
                wx.CallAfter(self.reset_keyboard_cursor, 0)

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
        """显示回复列表 - DataViewListCtrl版本"""
        self.list_ctrl.DeleteAllItems()
        # 清空数据存储
        self.list_data = []

        # 如果是帖子详情，设置内容类型但不改变标题
        if thread_info:
            self.current_content_type = 'thread_detail'
            self.current_thread_info = thread_info

        self.current_posts = posts
        self.current_pagination = pagination or {}

        for i, post in enumerate(posts):
            # 获取楼层信息 - 需要考虑当前页码来计算正确的楼层
            current_page = pagination.get('page', 1) if pagination else 1
            posts_per_page = 20  # 假设每页显示20条
            floor_offset = (current_page - 1) * posts_per_page
            floor = i + 1 + floor_offset  # 实际楼层

            username = post.get('username', '')
            content = self.clean_html_tags(post.get('message', ''))
            create_date = post.get('dateline_fmt', '')

            # 格式化显示
            if floor == 1:
                # 楼主
                formatted_content = f"楼主 {username} 说\n{content}\n发表时间：{create_date}"
            else:
                # 其他楼层
                formatted_content = f"{floor}楼 {username} 说\n{content}\n发表时间：{create_date}"

            # 使用 DataViewListCtrl 的 AppendItem 方法，只显示内容列
            # 将索引信息存储在 list_data 数组中
            self.list_ctrl.AppendItem([formatted_content])
            self.list_data.append({
                'type': 'post',
                'index': i,
                'floor': floor,
                'post_data': post
            })

        # 根据设计文档添加4个分页控制项
        # 如果没有分页信息，创建默认分页信息
        if not pagination or not isinstance(pagination, dict):
            pagination = {'page': 1, 'totalpage': 1}
        else:
            pass  # 使用传入的分页信息

        # 总是添加分页控制，即使只有一页
        self.add_pagination_controls(pagination)

        # 设置焦点到索引0（楼主），确保屏幕阅读器能朗读
        if self.list_ctrl.GetItemCount() > 0:
            # 使用游标重置方式设置楼主焦点
            wx.CallAfter(self.reset_keyboard_cursor, 0)

    def load_previous_page(self):
        """加载上一页"""
        try:
            if not hasattr(self, 'current_content_type') or not hasattr(self, 'current_pagination'):
                return

            current_page = self.current_pagination.get('page', 1)
            if current_page <= 1:
                return

            prev_page = current_page - 1

            # 计算真实的页面号（考虑偏移）
            page_offset = self.current_pagination.get('page_offset', 0)
            real_prev_page = prev_page + page_offset

            # 根据当前内容类型加载上一页
            if self.current_content_type == 'thread_list' and hasattr(self, 'current_fid'):
                if hasattr(self, 'current_api_params') and self.current_api_params:
                    # 使用API参数加载分类内容
                    result = self.forum_client.get_thread_list_with_type(self.current_forum, self.current_api_params, real_prev_page)
                    # 保持页面偏移信息
                    new_pagination = result.get('pagination', {})
                    new_pagination['page_offset'] = page_offset
                    new_pagination['real_total_page'] = self.current_pagination.get('real_total_page', new_pagination.get('totalpage', 1))
                    new_pagination['totalpage'] = new_pagination.get('totalpage', 1) - page_offset
                    new_pagination['page'] = prev_page
                    self.display_threads(result.get('threadlist', []), new_pagination, 'thread_list', self.current_api_params)
                else:
                    # 普通板块内容
                    result = self.forum_client.get_thread_list(self.current_forum, self.current_fid, real_prev_page)
                    self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'thread_list')
                # 设置键盘游标到第一项
                wx.CallAfter(self.reset_keyboard_cursor, 0)
            elif self.current_content_type == 'search_result' and hasattr(self, 'current_keyword'):
                result = self.forum_client.search(self.current_forum, self.current_keyword, prev_page)
                self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'search_result')
                # 设置键盘游标到第一项
                wx.CallAfter(self.reset_keyboard_cursor, 0)
            elif self.current_content_type == 'user_threads' and hasattr(self, 'current_uid'):
                result = self.forum_client.get_user_threads(self.current_forum, self.current_uid, prev_page)
                self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'user_threads')
                # 设置键盘游标到第一项
                wx.CallAfter(self.reset_keyboard_cursor, 0)
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
                # 设置键盘游标到第一项
                wx.CallAfter(self.reset_keyboard_cursor, 0)
            elif self.current_content_type == 'home_content' and hasattr(self, 'current_orderby'):
                # 添加首页内容的分页支持
                result = self.forum_client.get_home_content(self.current_forum, self.current_orderby, prev_page)
                self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'home_content')
                # 设置键盘游标到第一项
                wx.CallAfter(self.reset_keyboard_cursor, 0)
            elif self.current_content_type == 'thread_detail' and hasattr(self, 'current_tid'):
                result = self.forum_client.get_thread_detail(self.current_forum, self.current_tid, prev_page)
                self.display_posts(result.get('postlist', []), result.get('pagination', {}), result.get('thread_info', {}))
                # 设置键盘游标到第一项（楼主）
                wx.CallAfter(self.reset_keyboard_cursor, 0)

        except Exception as e:
            print(f"加载上一页错误: {e}")
            wx.MessageBox("加载上一页失败", "错误", wx.OK | wx.ICON_ERROR)

    def show_page_jump_dialog(self):
        """显示页码跳转对话框"""
        try:
            # 防止重复打开对话框
            if hasattr(self, '_page_dialog_open') and self._page_dialog_open:
                return

            if not hasattr(self, 'current_pagination'):
                return

            # 标记对话框为打开状态
            self._page_dialog_open = True

            total_page = self.current_pagination.get('totalpage', 1)
            current_page = self.current_pagination.get('page', 1)

            # 创建自定义对话框来更好地控制回车键行为
            dialog = wx.Dialog(self, title="页码跳转", size=(300, 150))
            dialog.SetExtraStyle(wx.WS_EX_CONTEXTHELP)

            panel = wx.Panel(dialog)
            sizer = wx.BoxSizer(wx.VERTICAL)

            # 提示标签
            prompt_label = wx.StaticText(panel, label=f"请输入目标页码 (1-{total_page}):")
            sizer.Add(prompt_label, 0, wx.ALL | wx.EXPAND, 10)

            # 输入框
            page_input = wx.TextCtrl(panel, value=str(current_page), style=wx.TE_PROCESS_ENTER)
            sizer.Add(page_input, 0, wx.ALL | wx.EXPAND, 10)

            # 按钮面板
            button_panel = wx.Panel(panel)
            button_sizer = wx.BoxSizer(wx.HORIZONTAL)
            ok_button = wx.Button(button_panel, id=wx.ID_OK, label="确定")
            cancel_button = wx.Button(button_panel, id=wx.ID_CANCEL, label="取消")
            button_sizer.Add(ok_button, 0, wx.ALL, 5)
            button_sizer.Add(cancel_button, 0, wx.ALL, 5)
            button_panel.SetSizer(button_sizer)
            sizer.Add(button_panel, 0, wx.ALL | wx.ALIGN_CENTER, 10)

            panel.SetSizer(sizer)
            # 将panel作为对话框的主sizer
            dialog_sizer = wx.BoxSizer(wx.VERTICAL)
            dialog_sizer.Add(panel, 1, wx.EXPAND)
            dialog.SetSizerAndFit(dialog_sizer)

            # 绑定回车键事件到输入框
            def on_input_enter(event):
                dialog.EndModal(wx.ID_OK)
                event.Skip()

            # 绑定取消按钮事件以确保对话框正确关闭
            def on_cancel(event):
                dialog.EndModal(wx.ID_CANCEL)
                event.Skip()

            def on_dialog_close(event):
                # 重置对话框打开状态
                self._page_dialog_open = False
                event.Skip()

            page_input.Bind(wx.EVT_TEXT_ENTER, on_input_enter)
            cancel_button.Bind(wx.EVT_BUTTON, on_cancel)
            dialog.Bind(wx.EVT_CLOSE, on_dialog_close)

            # 设置焦点到输入框
            wx.CallAfter(page_input.SetFocus)
            wx.CallAfter(page_input.SelectAll)

            # 显示对话框
            result = dialog.ShowModal()
            # 重置对话框打开状态
            self._page_dialog_open = False

            if result == wx.ID_OK:
                page_str = page_input.GetValue().strip()
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
            # 确保在异常情况下也重置状态
            self._page_dialog_open = False
            print(f"页码跳转错误: {e}")

    def jump_to_page(self, target_page):
        """跳转到指定页码"""
        try:
            # 计算真实的页面号（考虑偏移）
            page_offset = getattr(self, 'current_pagination', {}).get('page_offset', 0)
            real_target_page = target_page + page_offset

            # 根据当前内容类型跳转页面
            if self.current_content_type == 'thread_list' and hasattr(self, 'current_fid'):
                if hasattr(self, 'current_api_params') and self.current_api_params:
                    # 使用API参数加载分类内容
                    result = self.forum_client.get_thread_list_with_type(self.current_forum, self.current_api_params, real_target_page)
                    # 保持页面偏移信息
                    new_pagination = result.get('pagination', {})
                    new_pagination['page_offset'] = page_offset
                    new_pagination['real_total_page'] = self.current_pagination.get('real_total_page', new_pagination.get('totalpage', 1))
                    new_pagination['totalpage'] = new_pagination.get('totalpage', 1) - page_offset
                    new_pagination['page'] = target_page
                    self.display_threads(result.get('threadlist', []), new_pagination, 'thread_list', self.current_api_params)
                else:
                    # 普通板块内容
                    result = self.forum_client.get_thread_list(self.current_forum, self.current_fid, real_target_page)
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
                self.display_posts(result.get('postlist', []), result.get('pagination', {}), result.get('thread_info', {}))

        except Exception as e:
            print(f"页面跳转错误: {e}")
            wx.MessageBox("页面跳转失败", "错误", wx.OK | wx.ICON_ERROR)

    def show_reply_dialog(self):
        """显示回复对话框"""
        try:
            # 防止重复打开对话框
            if hasattr(self, '_reply_dialog_open') and self._reply_dialog_open:
                return

            if not hasattr(self, 'current_tid') or not self.current_tid:
                wx.MessageBox("请先选择要回复的帖子", "提示", wx.OK | wx.ICON_INFORMATION)
                return

            # 标记对话框为打开状态
            self._reply_dialog_open = True

            # 创建回复对话框
            dialog = wx.Dialog(self, title="回复帖子", size=(500, 300))
            dialog.SetExtraStyle(wx.WS_EX_CONTEXTHELP)

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
            # 将panel作为对话框的主sizer
            dialog_sizer = wx.BoxSizer(wx.VERTICAL)
            dialog_sizer.Add(panel, 1, wx.EXPAND)
            dialog.SetSizerAndFit(dialog_sizer)

            # 设置焦点到内容输入框
            wx.CallAfter(content_ctrl.SetFocus)

            # 绑定取消按钮事件以确保对话框正确关闭
            def on_cancel(event):
                dialog.EndModal(wx.ID_CANCEL)
                event.Skip()

            def on_dialog_close(event):
                # 重置对话框打开状态
                self._reply_dialog_open = False
                event.Skip()

            cancel_button.Bind(wx.EVT_BUTTON, on_cancel)
            dialog.Bind(wx.EVT_CLOSE, on_dialog_close)

            # 显示对话框
            result = dialog.ShowModal()
            # 重置对话框打开状态
            self._reply_dialog_open = False

            if result == wx.ID_OK:
                content = content_ctrl.GetValue().strip()
                if content:
                    self.post_reply(content)
                else:
                    wx.MessageBox("回复内容不能为空", "提示", wx.OK | wx.ICON_WARNING)

            dialog.Destroy()

        except Exception as e:
            # 确保在异常情况下也重置状态
            self._reply_dialog_open = False
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
        """显示消息列表（只显示用户名，隐藏消息内容） - DataViewListCtrl版本"""
        self.list_ctrl.DeleteAllItems()
        # 清空数据存储
        self.list_data = []

        # 保存消息列表
        self.current_messages = messages

        for message in messages:
            username = message.get('username', '')
            touid = message.get('touid', '')

            # 将对方用户ID转换为整数
            try:
                uid_value = int(touid) if touid else 0
            except (ValueError, TypeError):
                uid_value = 0

            # 使用 DataViewListCtrl 的 AppendItem 方法，只显示内容列
            # 将用户ID信息存储在 list_data 数组中
            self.list_ctrl.AppendItem([username])
            self.list_data.append({
                'type': 'message',
                'touid': uid_value,
                'message_data': message
            })

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
        """显示消息对话（按时间升序：最老消息在最上面，最新消息在最下面）- DataViewListCtrl版本"""
        self.list_ctrl.DeleteAllItems()
        # 清空数据存储
        self.list_data = []

        # 保存当前消息记录
        self.current_conversation = messages

        # 按时间升序排列（最老的在上面，最新的在下面）
        # HTML解析器返回的消息是降序排列的（最新的在前面），需要反转
        messages = messages[::-1]

        for message in messages:
            # 字段名映射：HTML解析器返回的是content、username、datetime
            content = message.get('content', '')

            # 消息内容已经包含了用户名和时间信息，直接使用
            formatted_content = content

            # 如果内容太长，截断显示
            if len(formatted_content) > 200:
                formatted_content = formatted_content[:200] + '...'

            # 使用 DataViewListCtrl 的 AppendItem 方法，只显示内容列
            # 将消息信息存储在 list_data 数组中
            self.list_ctrl.AppendItem([formatted_content])
            self.list_data.append({
                'type': 'conversation',
                'message_data': message
            })

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
        """显示楼层内容浏览框"""
        try:
            # 检查是否已有对话框打开
            if hasattr(self, '_floor_dialog_open') and self._floor_dialog_open:
                return

            if not hasattr(self, 'current_posts') or floor_index >= len(self.current_posts):
                return

            post = self.current_posts[floor_index]
            original_content = post.get('message', '')
            username = post.get('username', '')
            floor = floor_index + 1

            # 设置对话框状态为打开
            self._floor_dialog_open = True

            # 创建浏览对话框
            dialog = wx.Dialog(self, title=f"浏览{floor}楼 - {username}", size=(600, 400))

            # 创建主sizer用于dialog
            main_sizer = wx.BoxSizer(wx.VERTICAL)

            panel = wx.Panel(dialog)
            sizer = wx.BoxSizer(wx.VERTICAL)

            # 楼层信息（只读）
            info_label = wx.StaticText(panel, label=f"{floor}楼 {username} 的内容:")
            sizer.Add(info_label, 0, wx.ALL | wx.EXPAND, 5)

            # 内容显示框（只读，不自动换行）
            content_ctrl = wx.TextCtrl(panel, value=original_content, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP)
            sizer.Add(content_ctrl, 1, wx.ALL | wx.EXPAND, 5)

            # 按钮面板
            button_panel = wx.Panel(panel)
            button_sizer = wx.BoxSizer(wx.HORIZONTAL)
            close_button = wx.Button(button_panel, id=wx.ID_CANCEL, label="关闭")
            button_sizer.Add(close_button, 0, wx.ALL, 5)
            button_panel.SetSizer(button_sizer)
            sizer.Add(button_panel, 0, wx.ALL | wx.ALIGN_CENTER, 5)

            panel.SetSizer(sizer)
            main_sizer.Add(panel, 1, wx.EXPAND)
            dialog.SetSizerAndFit(main_sizer)

            # 绑定键盘事件
            def on_char(event):
                keycode = event.GetKeyCode()
                if keycode == wx.WXK_ESCAPE or keycode == wx.WXK_BACK:
                    dialog.EndModal(wx.ID_CANCEL)
                else:
                    event.Skip()

            # 对话框关闭事件处理
            def on_dialog_close(event):
                self._floor_dialog_open = False
                event.Skip()

            # 按钮事件处理
            def on_close_button(event):
                dialog.EndModal(wx.ID_CANCEL)

            content_ctrl.Bind(wx.EVT_CHAR, on_char)
            close_button.Bind(wx.EVT_BUTTON, on_close_button)
            dialog.Bind(wx.EVT_CLOSE, on_dialog_close)

            # 使用wx.CallAfter设置焦点
            wx.CallAfter(content_ctrl.SetFocus)

            try:
                # 显示对话框
                dialog.ShowModal()
            except Exception as dialog_error:
                print(f"对话框显示错误: {dialog_error}")
            finally:
                # 确保状态被重置
                self._floor_dialog_open = False
                dialog.Destroy()

        except Exception as e:
            print(f"显示楼层浏览框错误: {e}")
            # 确保在错误情况下也重置状态
            self._floor_dialog_open = False

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