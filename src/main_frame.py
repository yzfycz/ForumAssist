# -*- coding: utf-8 -*-
"""
主窗口框架
程序的主界面框架
"""

import wx
import wx.lib.newevent
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

        # 如果没有账户，显示账户管理界面
        if not self.accounts:
            self.show_account_manager()
            return

        # 创建主窗口
        super().__init__(None, title="论坛助手", size=(1024, 768))

        # 绑定事件
        self.Bind(EVT_ACCOUNT_SELECTED, self.on_account_selected)

        # 创建UI
        self.create_ui()
        self.create_menu()

        # 显示账户选择界面
        self.show_account_selection()

    def create_ui(self):
        """创建用户界面"""
        # 创建主面板
        self.main_panel = wx.Panel(self)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 创建顶部搜索区域
        self.create_search_area()

        # 创建主要内容区域
        self.create_content_area()

        self.main_panel.SetSizer(self.main_sizer)

        # 设置窗口图标
        self.set_window_icon()

        # 设置窗口样式
        self.set_window_style()

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

        # 创建树控件
        self.tree_ctrl = wx.TreeCtrl(self.tree_panel, style=wx.TR_DEFAULT_STYLE | wx.TR_SINGLE)
        self.tree_ctrl.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_tree_selection)
        self.tree_ctrl.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_tree_activated)

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

        # 创建列表
        list_ctrl = wx.ListCtrl(dialog, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        list_ctrl.InsertColumn(0, "论坛名称", width=150)
        list_ctrl.InsertColumn(1, "用户名", width=150)
        list_ctrl.InsertColumn(2, "昵称", width=150)

        # 添加账户
        for i, account in enumerate(self.accounts):
            list_ctrl.InsertItem(i, account.get('name', ''))
            list_ctrl.SetItem(i, 1, account.get('username', ''))
            list_ctrl.SetItem(i, 2, account.get('nickname', ''))

        # 创建按钮
        button_sizer = dialog.CreateButtonSizer(wx.OK | wx.CANCEL)

        # 布局
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(list_ctrl, 1, wx.ALL | wx.EXPAND, 10)
        sizer.Add(button_sizer, 0, wx.ALL | wx.EXPAND, 10)
        dialog.SetSizer(sizer)

        # 显示对话框
        if dialog.ShowModal() == wx.ID_OK:
            selected = list_ctrl.GetFirstSelected()
            if selected != -1:
                account = self.accounts[selected]
                self.select_account(account)

        dialog.Destroy()

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

        # 添加根节点
        root = self.tree_ctrl.AddRoot(self.current_forum)

        # 添加常用节点
        self.tree_ctrl.AppendItem(root, "最新发表")
        self.tree_ctrl.AppendItem(root, "最新回复")
        self.tree_ctrl.AppendItem(root, "我的发表")
        self.tree_ctrl.AppendItem(root, "我的回复")
        self.tree_ctrl.AppendItem(root, "我的消息")

        # 添加论坛板块
        forum_list = self.forum_client.get_forum_list(self.current_forum)
        for forum in forum_list:
            forum_item = self.tree_ctrl.AppendItem(root, forum.get('name', ''))
            # 如果有子板块，递归添加
            if 'sublist' in forum:
                for sub_forum in forum['sublist']:
                    self.tree_ctrl.AppendItem(forum_item, sub_forum.get('name', ''))

        # 展开根节点
        self.tree_ctrl.Expand(root)

    def on_account_selected(self, event):
        """账户选择事件"""
        account = event.account
        self.select_account(account)

    def on_tree_selection(self, event):
        """树视图选择事件"""
        item = event.GetItem()
        text = self.tree_ctrl.GetItemText(item)
        self.load_content(text)

    def on_tree_activated(self, event):
        """树视图激活事件"""
        item = event.GetItem()
        text = self.tree_ctrl.GetItemText(item)
        self.load_content(text)

    def on_list_selection(self, event):
        """列表选择事件"""
        # 处理列表选择
        pass

    def on_list_activated(self, event):
        """列表激活事件"""
        # 处理列表激活
        pass

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

    def load_content(self, text):
        """加载内容"""
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
            self.load_forum_section(text)

    def load_latest_threads(self):
        """加载最新发表"""
        threads = self.forum_client.get_home_content(self.current_forum, "latest")
        self.display_threads(threads)

    def load_latest_replies(self):
        """加载最新回复"""
        threads = self.forum_client.get_home_content(self.current_forum, "lastpost")
        self.display_threads(threads)

    def load_my_threads(self):
        """加载我的发表"""
        user_info = self.auth_manager.get_user_info(self.current_forum)
        if user_info:
            uid = user_info.get('uid')
            if uid:
                result = self.forum_client.get_user_threads(self.current_forum, uid)
                self.display_threads(result.get('threadlist', []))

    def load_my_posts(self):
        """加载我的回复"""
        user_info = self.auth_manager.get_user_info(self.current_forum)
        if user_info:
            uid = user_info.get('uid')
            if uid:
                result = self.forum_client.get_user_posts(self.current_forum, uid)
                self.display_posts(result.get('postlist', []))

    def load_messages(self):
        """加载消息"""
        # 显示消息列表对话框
        dialog = MessageListDialog(self, self.current_forum, self.message_manager)
        dialog.ShowModal()
        dialog.Destroy()

    def load_forum_section(self, section_name):
        """加载论坛板块"""
        # 实现板块内容加载
        pass

    def search_content(self, keyword):
        """搜索内容"""
        result = self.forum_client.search(self.current_forum, keyword)
        self.display_threads(result.get('threadlist', []))

    def display_threads(self, threads):
        """显示帖子列表"""
        self.list_ctrl.DeleteAllItems()
        self.list_ctrl.InsertColumn(0, "标题", width=400)
        self.list_ctrl.InsertColumn(1, "作者", width=100)
        self.list_ctrl.InsertColumn(2, "浏览", width=60)
        self.list_ctrl.InsertColumn(3, "回复", width=60)
        self.list_ctrl.InsertColumn(4, "时间", width=150)

        for i, thread in enumerate(threads):
            self.list_ctrl.InsertItem(i, thread.get('subject', ''))
            self.list_ctrl.SetItem(i, 1, thread.get('username', ''))
            self.list_ctrl.SetItem(i, 2, str(thread.get('views', 0)))
            self.list_ctrl.SetItem(i, 3, str(thread.get('posts', 0)))
            self.list_ctrl.SetItem(i, 4, thread.get('create_date_fmt', ''))

    def display_posts(self, posts):
        """显示回复列表"""
        self.list_ctrl.DeleteAllItems()
        self.list_ctrl.InsertColumn(0, "内容", width=600)
        self.list_ctrl.InsertColumn(1, "作者", width=100)
        self.list_ctrl.InsertColumn(2, "时间", width=150)

        for i, post in enumerate(posts):
            self.list_ctrl.InsertItem(i, post.get('message', '')[:100] + '...')
            self.list_ctrl.SetItem(i, 1, post.get('username', ''))
            self.list_ctrl.SetItem(i, 2, post.get('create_date_fmt', ''))

    def display_messages(self, messages):
        """显示消息列表"""
        self.list_ctrl.DeleteAllItems()
        self.list_ctrl.InsertColumn(0, "用户名", width=200)
        self.list_ctrl.InsertColumn(1, "状态", width=100)

        for i, message in enumerate(messages):
            self.list_ctrl.InsertItem(i, message.get('username', ''))
            self.list_ctrl.SetItem(i, 1, message.get('status', ''))

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