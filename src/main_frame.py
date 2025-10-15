# -*- coding: utf-8 -*-
"""
主窗口框架
程序的主界面框架
"""

import wx
import wx.dataview
import wx.lib.newevent
import re
import webbrowser
from auth_manager import AuthenticationManager
from forum_client import ForumClient
from account_manager import AccountManager
from message_manager import MessageManager, MessageDialog, MessageListDialog

# 创建自定义事件
AccountSelectedEvent, EVT_ACCOUNT_SELECTED = wx.lib.newevent.NewEvent()

class CodeGeneratorDialog(wx.Dialog):
    """代码生成对话框"""

    def __init__(self, parent, title="添加代码"):
        """
        初始化代码生成对话框

        Args:
            parent: 父窗口
            title: 对话框标题
        """
        super().__init__(parent, title=title, size=(400, 250))

        self.generated_code = None  # 存储生成的代码

        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 代码类型选择
        type_label = wx.StaticText(panel, label="代码类型:")
        self.type_combo = wx.ComboBox(panel, choices=["超链接", "音频", "图片"], value="超链接", style=wx.CB_READONLY)
        self.type_combo.Bind(wx.EVT_COMBOBOX, self.on_type_changed)

        # 输入字段
        field_label_1 = wx.StaticText(panel, label="超链接名字:")
        self.field_1 = wx.TextCtrl(panel)

        field_label_2 = wx.StaticText(panel, label="超链接地址:")
        self.field_2 = wx.TextCtrl(panel)

        # 按钮
        button_panel = wx.Panel(panel)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(button_panel, id=wx.ID_OK, label="确定(&O)")
        cancel_button = wx.Button(button_panel, id=wx.ID_CANCEL, label="取消(&C)")
        button_sizer.Add(ok_button, 0, wx.ALL, 5)
        button_sizer.Add(cancel_button, 0, wx.ALL, 5)
        button_panel.SetSizer(button_sizer)

        # 使用GridBagSizer进行布局
        grid_sizer = wx.GridBagSizer(5, 5)
        grid_sizer.Add(type_label, pos=(0, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.type_combo, pos=(0, 1), flag=wx.EXPAND)
        grid_sizer.Add(field_label_1, pos=(1, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.field_1, pos=(1, 1), flag=wx.EXPAND)
        grid_sizer.Add(field_label_2, pos=(2, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.field_2, pos=(2, 1), flag=wx.EXPAND)

        # 设置行列增长
        grid_sizer.AddGrowableCol(1, 1)

        main_sizer.Add(grid_sizer, 1, wx.ALL | wx.EXPAND, 10)
        main_sizer.Add(button_panel, 0, wx.ALL | wx.ALIGN_CENTER, 5)

        panel.SetSizer(main_sizer)
        dialog_sizer = wx.BoxSizer(wx.VERTICAL)
        dialog_sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizerAndFit(dialog_sizer)

        # 保存标签控件的引用以便后续修改
        self.field_label_1 = field_label_1
        self.field_label_2 = field_label_2

        # 绑定确定按钮事件
        ok_button.Bind(wx.EVT_BUTTON, self.on_ok)

        # 设置焦点到第一个输入框
        self.Bind(wx.EVT_SHOW, self.on_dialog_show)

    def on_dialog_show(self, event):
        """对话框显示时设置焦点"""
        wx.CallAfter(self.type_combo.SetFocus)
        event.Skip()

    def on_type_changed(self, event):
        """处理代码类型改变事件"""
        selected_type = self.type_combo.GetValue()

        if selected_type == "超链接":
            self.field_label_1.SetLabel("超链接名字:")
            self.field_label_2.SetLabel("超链接地址:")
        elif selected_type == "图片":
            self.field_label_1.SetLabel("图片名称:")
            self.field_label_2.SetLabel("图片地址:")
        elif selected_type == "音频":
            self.field_label_1.SetLabel("音频名称:")
            self.field_label_2.SetLabel("音频地址:")

        # 清空输入框
        self.field_1.SetValue("")
        self.field_2.SetValue("")

        # 重新布局
        self.Layout()

    def on_ok(self, event):
        """处理确定按钮事件"""
        selected_type = self.type_combo.GetValue()
        field_1_value = self.field_1.GetValue().strip()
        field_2_value = self.field_2.GetValue().strip()

        if not field_1_value or not field_2_value:
            wx.MessageBox("请填写完整信息", "提示", wx.OK | wx.ICON_WARNING)
            return

        # 根据类型生成代码
        if selected_type == "超链接":
            self.generated_code = f'<a href="{field_2_value}">{field_1_value}</a>'
        elif selected_type == "图片":
            self.generated_code = f'<a href="{field_2_value}"><img alt="{field_1_value}" src="{field_2_value}" /></a>'
        elif selected_type == "音频":
            self.generated_code = f'<audio controls="controls" src="{field_2_value}" title="{field_1_value}"> </audio>'

        self.EndModal(wx.ID_OK)

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

        # 设置键盘快捷键
        self.setup_keyboard_shortcuts()

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
        search_sizer = wx.BoxSizer(wx.VERTICAL)

        # 使用2列网格布局，完全复制账户管理对话框的成功模式
        grid_sizer = wx.FlexGridSizer(2, 2, 5, 5)  # 2行2列，间距5像素
        grid_sizer.AddGrowableCol(1, 1)  # 第2列（搜索框列）可以扩展

        # 搜索标签 - 使用可见的StaticText标签，完全复制账户管理对话框的模式
        search_label = wx.StaticText(search_panel, label="输入搜索关键词:")

        # 搜索框 - 使用标准TextCtrl，避免SearchCtrl可能的问题
        self.search_ctrl = wx.TextCtrl(search_panel, style=wx.TE_PROCESS_ENTER)
        self.search_ctrl.Bind(wx.EVT_TEXT_ENTER, self.on_search)

        # 搜索按钮
        search_button = wx.Button(search_panel, label="搜索")
        search_button.Bind(wx.EVT_BUTTON, self.on_search)

        # 添加控件到网格布局 - 第1行：标签+搜索框
        grid_sizer.Add(search_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.search_ctrl, 0, wx.EXPAND)

        # 第2行：空标签+按钮（保持2列布局的一致性）
        empty_label = wx.StaticText(search_panel, label="")
        grid_sizer.Add(empty_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(search_button, 0, wx.ALIGN_LEFT)

        # 将网格布局添加到主布局
        search_sizer.Add(grid_sizer, 1, wx.ALL | wx.EXPAND, 5)

        search_panel.SetSizer(search_sizer)
        self.main_sizer.Add(search_panel, 0, wx.ALL | wx.EXPAND, 5)

    def setup_search_accessibility(self):
        """设置搜索框的无障碍属性"""
        try:
            # 设置搜索框的无障碍名称
            self.search_ctrl.SetName("输入搜索关键词")

            # 尝试使用Windows API设置无障碍属性
            import ctypes
            import os

            # 获取搜索框的HWND
            hwnd = self.search_ctrl.GetHandle()
            if hwnd:
                # 尝试设置控件的Accessible Name
                try:
                    # 使用user32.dll设置控件属性
                    user32 = ctypes.windll.user32
                    # 这里可以添加更多的Windows API调用来设置无障碍属性
                    pass
                except:
                    pass

        except Exception as e:
            pass

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
        self.list_ctrl.Bind(wx.dataview.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.on_list_context_menu)
        self.list_ctrl.Bind(wx.EVT_CONTEXT_MENU, self.on_list_context_menu)
        self.list_ctrl.Bind(wx.EVT_KEY_DOWN, self.on_list_key_down)
        self.list_ctrl.Bind(wx.EVT_SET_FOCUS, self.on_list_focus)

        list_sizer.Add(self.list_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        self.list_panel.SetSizer(list_sizer)

    def create_menu(self):
        """创建菜单栏"""
        menubar = wx.MenuBar()

        # 文件菜单
        file_menu = wx.Menu()
        account_item = file_menu.Append(wx.ID_ANY, "账户管理(&M)", "管理论坛账户\tCtrl+M")
        self.Bind(wx.EVT_MENU, self.on_account_management, account_item)

        switch_account_item = file_menu.Append(wx.ID_ANY, "切换账户(&Q)", "切换到其他账户\tCtrl+Q")
        self.Bind(wx.EVT_MENU, self.on_switch_account, switch_account_item)

        settings_item = file_menu.Append(wx.ID_ANY, "设置(&P)", "软件设置\tCtrl+P")
        self.Bind(wx.EVT_MENU, self.on_settings, settings_item)

        exit_item = file_menu.Append(wx.ID_EXIT, "退出(&X)", "退出程序\tAlt+F4")
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)

        menubar.Append(file_menu, "文件(&F)")

        # 帮助菜单
        help_menu = wx.Menu()
        about_item = help_menu.Append(wx.ID_ABOUT, "关于(&A)", "关于论坛助手\tF1")
        self.Bind(wx.EVT_MENU, self.on_about, about_item)

        menubar.Append(help_menu, "帮助(&H)")

        self.SetMenuBar(menubar)

    def setup_keyboard_shortcuts(self):
        """设置键盘快捷键"""
        # 定义快捷键表
        accelerator_table = [
            wx.AcceleratorEntry(wx.ACCEL_CTRL, ord('M'), 1001),  # Ctrl+M - 账户管理
            wx.AcceleratorEntry(wx.ACCEL_CTRL, ord('Q'), 1002),  # Ctrl+Q - 切换账户
            wx.AcceleratorEntry(wx.ACCEL_CTRL, ord('P'), 1003),  # Ctrl+P - 设置
            wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_F1, 1004),  # F1 - 关于
            wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_F5, 1005),  # F5 - 刷新
            wx.AcceleratorEntry(wx.ACCEL_CTRL, ord('W'), 1006),  # Ctrl+W - 网页打开
            wx.AcceleratorEntry(wx.ACCEL_CTRL, ord('C'), 1007),  # Ctrl+C - 拷贝帖子标题
            wx.AcceleratorEntry(wx.ACCEL_CTRL, ord('D'), 1008),  # Ctrl+D - 拷贝帖子地址
        ]

        # 创建加速器表
        accel_table = wx.AcceleratorTable(accelerator_table)
        self.SetAcceleratorTable(accel_table)

        # 绑定快捷键事件
        self.Bind(wx.EVT_MENU, self.on_account_management, id=1001)
        self.Bind(wx.EVT_MENU, self.on_switch_account, id=1002)
        self.Bind(wx.EVT_MENU, self.on_settings, id=1003)
        self.Bind(wx.EVT_MENU, self.on_about, id=1004)
        self.Bind(wx.EVT_MENU, self.on_refresh, id=1005)
        self.Bind(wx.EVT_MENU, self.on_open_in_browser, id=1006)
        self.Bind(wx.EVT_MENU, self.on_copy_title, id=1007)
        self.Bind(wx.EVT_MENU, self.on_copy_url, id=1008)

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
        ok_button = wx.Button(button_panel, id=wx.ID_OK, label="确定(&O)")
        cancel_button = wx.Button(button_panel, id=wx.ID_CANCEL, label="取消(&C)")

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

                    # 添加全局typeid2子分类（已解决/未解决）
                    typeid2_list = forum_types.get('typeid2', [])
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
            pass

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

        # 检查修饰键状态
        ctrl_down = event.ControlDown()
        shift_down = event.ShiftDown()

        if keycode == wx.WXK_BACK:
            # 退格键：优先处理筛选模式退出，然后是正常的返回逻辑
            if hasattr(self, 'filter_mode') and self.filter_mode:
                # 筛选模式：直接返回帖子列表，不回到帖子详情
                self.exit_filter_mode_to_list()
            elif hasattr(self, 'user_content_mode') and self.user_content_mode:
                # 退出用户内容查看模式，返回之前的帖子详情
                self.exit_user_content_mode()
            elif hasattr(self, 'current_content_type') and self.current_content_type == 'thread_detail':
                print(f"[DEBUG] Backspace in thread_detail")
                # 检查是否从用户内容进入的帖子详情
                if hasattr(self, 'user_content_state_before_thread') and self.user_content_state_before_thread:
                    print(f"[DEBUG] Returning to user content")
                    # 返回到用户内容页面
                    self.return_to_user_content()
                else:
                    print(f"[DEBUG] Normal return to list")
                    # 正常返回到列表
                    self.go_back_to_previous_list()
            elif hasattr(self, 'current_content_type') and self.current_content_type == 'message_detail':
                # 在消息详情时返回消息列表
                self.load_messages()
            else:
                event.Skip()
        elif keycode == wx.WXK_RETURN:
            if hasattr(self, 'current_content_type') and self.current_content_type == 'thread_detail':
                # 在帖子详情页面中处理所有回车键组合
                if ctrl_down:
                    # Ctrl+回车：回复此楼
                    selected = self.list_ctrl.GetSelectedRow()
                    if selected != -1 and selected < len(self.list_data):
                        self.handle_reply_to_floor(selected)
                    # 不调用 event.Skip()，阻止事件传播
                    return
                elif shift_down:
                    # Shift+回车：查看用户资料
                    selected = self.list_ctrl.GetSelectedRow()
                    if selected != -1 and selected < len(self.list_data):
                        self.handle_view_user_profile(selected)
                    # 不调用 event.Skip()，阻止事件传播
                    return
                else:
                    # 普通回车键：激活当前选中项（浏览楼层）
                    selected = self.list_ctrl.GetSelectedRow()
                    if selected != -1:
                        self.handle_row_activation(selected)
                    # 不调用 event.Skip()，阻止事件传播
                    return
            else:
                # 在其他页面中，保持原有逻辑
                if ctrl_down:
                    # Ctrl+回车：回复此楼（仅在帖子详情页面）
                    if hasattr(self, 'current_content_type') and self.current_content_type == 'thread_detail':
                        selected = self.list_ctrl.GetSelectedRow()
                        if selected != -1 and selected < len(self.list_data):
                            self.handle_reply_to_floor(selected)
                        else:
                            event.Skip()
                    else:
                        event.Skip()
                elif shift_down:
                    # Shift+回车：查看用户资料（仅在帖子详情页面）
                    if hasattr(self, 'current_content_type') and self.current_content_type == 'thread_detail':
                        selected = self.list_ctrl.GetSelectedRow()
                        if selected != -1 and selected < len(self.list_data):
                            self.handle_view_user_profile(selected)
                        else:
                            event.Skip()
                    else:
                        event.Skip()
                else:
                    # 普通回车键：激活当前选中项
                    selected = self.list_ctrl.GetSelectedRow()
                    if selected != -1:
                        # 直接调用激活逻辑，不需要创建复杂的事件对象
                        self.handle_row_activation(selected)
                    else:
                        event.Skip()
        elif keycode == ord('K') or keycode == ord('k'):
            # K键：只看他功能（仅在帖子详情页面）
            if hasattr(self, 'current_content_type') and self.current_content_type == 'thread_detail':
                selected = self.list_ctrl.GetSelectedRow()
                if selected != -1 and selected < len(self.list_data):
                    self.handle_filter_by_user(selected)
                    return  # 处理完成后直接返回，不调用event.Skip()
                else:
                    event.Skip()
            else:
                event.Skip()
        elif keycode == ord('T') or keycode == ord('t'):
            # T键：用户内容二级菜单（仅在帖子详情页面）
            if hasattr(self, 'current_content_type') and self.current_content_type == 'thread_detail':
                selected = self.list_ctrl.GetSelectedRow()
                if selected != -1 and selected < len(self.list_data):
                    self.handle_user_content_menu(selected)
                    return  # 处理完成后直接返回，不调用event.Skip()
                else:
                    event.Skip()
            else:
                event.Skip()
        elif keycode == ord('E') and ctrl_down:
            # Ctrl+E：编辑帖子（仅在帖子详情页面）
            if hasattr(self, 'current_content_type') and self.current_content_type == 'thread_detail':
                selected = self.list_ctrl.GetSelectedRow()
                if selected != -1 and selected < len(self.list_data):
                    self.handle_edit_post(selected)
                    return  # 处理完成后直接返回，不调用event.Skip()
                else:
                    event.Skip()
            else:
                event.Skip()
        else:
            event.Skip()

    def go_back_to_previous_list(self):
        """返回之前的列表"""
        try:
            print(f"[DEBUG] go_back_to_previous_list() called")
            print(f"[DEBUG] current_content_type: {getattr(self, 'current_content_type', 'None')}")

            # 确保清除用户内容状态，避免影响后续导航
            self.user_content_state_before_thread = None

            # 优先尝试恢复保存的完整列表状态（不刷新）
            if hasattr(self, 'saved_list_state') and self.saved_list_state:
                state = self.saved_list_state
                content_type = state.get('current_content_type', '')
                print(f"[DEBUG] Found saved_list_state with content_type: {content_type}")

                # 对于用户内容，强制重新加载以确保数据最新
                if content_type in ['user_threads', 'user_posts']:
                    print(f"[DEBUG] User content detected, forcing reload")
                    # 清除保存的状态，强制重新加载
                    self.saved_list_state = None
                    # 继续到下面的逻辑重新加载
                else:
                    print(f"[DEBUG] Non-user content, restoring saved state")
                    # 对于其他内容类型，直接恢复保存的列表状态（不重新加载）
                    self.restore_saved_list_state()
                    return
            # 其次尝试恢复到保存的页面信息
            elif self.saved_page_info and self.restore_to_correct_page():
                # 成功恢复到正确页面，现在恢复焦点
                if self.saved_list_index != -1 and self.saved_list_index < self.list_ctrl.GetItemCount():
                    wx.CallAfter(self.reset_keyboard_cursor, self.saved_list_index)
            elif hasattr(self, 'previous_content_type') and hasattr(self, 'previous_content_params'):
                # 回退到原来的恢复逻辑
                content_type = self.previous_content_type
                params = self.previous_content_params
                print(f"[DEBUG] Using previous_content_type: {content_type}")

                if content_type == 'thread_list' and 'fid' in params:
                    print(f"[DEBUG] Loading forum section")
                    self.load_forum_section_and_restore_focus(params.get('forum_name', ''), params['fid'])
                elif content_type == 'user_threads':
                    print(f"[DEBUG] Loading my threads")
                    self.load_my_threads_and_restore_focus()
                elif content_type == 'user_posts':
                    print(f"[DEBUG] Loading my posts")
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
            pass
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
            pass

    def load_latest_threads_and_restore_focus(self):
        """加载最新发表并恢复焦点"""
        result = self.forum_client.get_home_content(self.current_forum, "latest")
        self.SetTitle(f"{self.current_forum}-<{self.get_user_nickname()}>-论坛助手")
        self.display_threads_and_restore_focus(result.get('threadlist', []), result.get('pagination', {}), 'home_content')
        self.current_orderby = 'latest'

        # 在内容加载后保存状态，确保 current_content_type 已正确设置
        self.save_current_state()

    def load_latest_replies_and_restore_focus(self):
        """加载最新回复并恢复焦点"""
        result = self.forum_client.get_home_content(self.current_forum, "lastpost")
        self.SetTitle(f"{self.current_forum}-<{self.get_user_nickname()}>-论坛助手")
        self.display_threads_and_restore_focus(result.get('threadlist', []), result.get('pagination', {}), 'home_content')
        self.current_orderby = 'lastpost'

        # 在内容加载后保存状态，确保 current_content_type 已正确设置
        self.save_current_state()

    def load_my_threads_and_restore_focus(self):
        """加载我的发表并恢复焦点"""
        print(f"[DEBUG] load_my_threads_and_restore_focus() called")
        user_info = self.auth_manager.get_user_info(self.current_forum)
        if user_info:
            uid = user_info.get('uid')
            if uid:
                self.current_uid = uid
                result = self.forum_client.get_user_threads(self.current_forum, uid)
                self.SetTitle(f"{self.current_forum}-<{self.get_user_nickname()}>-论坛助手")
                self.display_threads_and_restore_focus(result.get('threadlist', []), result.get('pagination', {}), 'user_threads')
                self.current_orderby = 'latest'

                # 在内容加载后保存状态，确保 current_content_type 已正确设置
                self.save_current_state()

    def load_my_posts_and_restore_focus(self):
        """加载我的回复并恢复焦点"""
        print(f"[DEBUG] load_my_posts_and_restore_focus() called")
        user_info = self.auth_manager.get_user_info(self.current_forum)
        if user_info:
            uid = user_info.get('uid')
            if uid:
                self.current_uid = uid
                result = self.forum_client.get_user_posts(self.current_forum, uid)
                # 使用原始数据结构，包含threadlist和pagination
                threadlist = result.get('threadlist', [])
                # 需要转换为display_threads期望的格式，显示为回复列表
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

                # 在内容加载后保存状态，确保 current_content_type 已正确设置
                self.save_current_state()

    def search_content_and_restore_focus(self, keyword):
        """搜索内容并恢复焦点"""
        result = self.forum_client.search(self.current_forum, keyword)
        threads = result.get('threadlist', [])

        # 清理搜索结果中的HTML标签
        cleaned_threads = []
        for thread in threads:
            cleaned_thread = thread.copy()
            if 'subject' in cleaned_thread:
                cleaned_thread['subject'] = self.clean_html_tags(cleaned_thread['subject'])
            cleaned_threads.append(cleaned_thread)

        self.SetTitle(f"{self.current_forum}-<{self.get_user_nickname()}>-论坛助手")
        self.display_threads_and_restore_focus(cleaned_threads, result.get('pagination', {}), 'search_result')

    
  
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
            pass

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
                threads = result.get('threadlist', [])

                # 清理搜索结果中的HTML标签
                cleaned_threads = []
                for thread in threads:
                    cleaned_thread = thread.copy()
                    if 'subject' in cleaned_thread:
                        cleaned_thread['subject'] = self.clean_html_tags(cleaned_thread['subject'])
                    cleaned_threads.append(cleaned_thread)

                self.display_threads(cleaned_threads, result.get('pagination', {}), 'search_result')
                return True
            elif content_type == 'home_content' and 'orderby' in params:
                # 跳转到首页内容的指定页面
                result = self.forum_client.get_home_content(self.current_forum, params['orderby'], page)
                self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'home_content')
                return True

        except Exception as e:
            pass

        return False

    def restore_saved_list_state(self):
        """恢复保存的列表状态（不刷新）"""
        if not hasattr(self, 'saved_list_state') or not self.saved_list_state:
            return False

        try:
            state = self.saved_list_state

            # 恢复基本状态变量
            self.current_content_type = state.get('current_content_type', 'thread_list')
            self.current_forum = state.get('current_forum', '')
            self.current_fid = state.get('current_fid')
            self.current_keyword = state.get('current_keyword', '')
            self.current_orderby = state.get('current_orderby', 'latest')
            self.current_pagination = state.get('current_pagination', {})

            # 恢复窗口标题
            self.SetTitle(state.get('window_title', f"{self.current_forum}-<{self.get_user_nickname()}>-论坛助手"))

            # 清空当前列表
            self.list_ctrl.DeleteAllItems()
            self.list_data.clear()

            # 恢复列表数据
            saved_list_data = state.get('list_data', [])
            for item_data in saved_list_data:
                if 'type' in item_data and item_data['type'] == 'pagination':
                    # 处理分页控制
                    action = item_data.get('action', '')
                    pagination = state.get('current_pagination', {})
                    current_page = pagination.get('page', 1)
                    total_page = pagination.get('totalpage', 1)

                    if action == 'prev':
                        page = max(1, current_page - 1)
                        display_text = f"上一页({page})"
                    elif action == 'next':
                        page = min(total_page, current_page + 1)
                        display_text = f"下一页({page})"
                    elif action == 'jump':
                        display_text = f"当前第{current_page}页共{total_page}页，回车输入页码跳转"
                    elif action == 'reply':
                        display_text = f"回复帖子"
                    else:
                        display_text = f"分页控制"

                    # 添加序号（如果启用）
                    if hasattr(self, 'show_list_numbers') and self.show_list_numbers:
                        total_items = len(saved_list_data)
                        item_index = len(self.list_data)
                        display_text += f" ，{item_index+1}之{total_items}项"

                    # 清理文本并添加到列表
                    import re
                    display_text = re.sub(r';?\s*数据:\s*\d+\s*', '', display_text)
                    display_text = re.sub(r';?\s*data:\s*\d+\s*', '', display_text, flags=re.IGNORECASE)
                    display_text = re.sub(r';\s*数据:\s*\d+.*$', '', display_text)
                    display_text = re.sub(r';\s*data:\s*\d+.*$', '', display_text, flags=re.IGNORECASE)
                    display_text = re.sub(r'\s+数据:\s*\d+.*$', '', display_text)
                    display_text = re.sub(r'\s+data:\s*\d+.*$', '', display_text, flags=re.IGNORECASE)
                    display_text = re.sub(r';+\s*$', '', display_text)
                    display_text = display_text.strip()

                    self.list_ctrl.AppendItem([display_text])
                    self.list_data.append({'type': 'pagination', 'action': action})

                elif 'tid' in item_data:
                    # 处理帖子项 - 使用与display_threads相同的逻辑
                    if self.current_content_type in ['thread_list', 'search_result', 'user_threads', 'user_posts', 'home_content']:
                        # 构建显示文本 - 使用与display_threads相同的格式
                        subject = self.clean_html_tags(item_data.get('subject', ''))
                        username = item_data.get('username', '')
                        views = item_data.get('views', 0)
                        forumname = item_data.get('forumname', '')
                        dateline_fmt = item_data.get('dateline_fmt', '')
                        posts = item_data.get('posts', 0)
                        lastpost_fmt = item_data.get('lastpost_fmt', '')
                        lastusername = item_data.get('lastusername', '')

                        display_text = f"{subject} 作者:{username};浏览:{views};板块:{forumname};发表时间:{dateline_fmt};回复:{posts};回复时间:{lastpost_fmt};最后回复:{lastusername}"

                        # 添加序号（如果启用）
                        if hasattr(self, 'show_list_numbers') and self.show_list_numbers:
                            total_items = len(saved_list_data)
                            item_index = len(self.list_data)
                            display_text += f" ，{item_index+1}之{total_items}项"

                        # 清理HTML标签
                        display_text = self.clean_html_tags(display_text)

                        # 清理数据信息
                        import re
                        display_text = re.sub(r';?\s*数据:\s*\d+\s*', '', display_text)
                        display_text = re.sub(r';?\s*data:\s*\d+\s*', '', display_text, flags=re.IGNORECASE)
                        display_text = re.sub(r';\s*数据:\s*\d+.*$', '', display_text)
                        display_text = re.sub(r';\s*data:\s*\d+.*$', '', display_text, flags=re.IGNORECASE)
                        display_text = re.sub(r'\s+数据:\s*\d+.*$', '', display_text)
                        display_text = re.sub(r'\s+data:\s*\d+.*$', '', display_text, flags=re.IGNORECASE)
                        display_text = re.sub(r';+\s*$', '', display_text)
                        display_text = display_text.strip()

                        self.list_ctrl.AppendItem([display_text])
                        self.list_data.append(item_data)

            # 恢复选中状态
            selected_index = state.get('selected_index', 0)
            if selected_index < self.list_ctrl.GetItemCount():
                self.list_ctrl.SelectRow(selected_index)
                wx.CallAfter(self.reset_keyboard_cursor, selected_index)

            # 清除保存的状态，避免重复恢复
            self.saved_list_state = None

            return True

        except Exception as e:
            # 恢复失败时清除保存的状态
            self.saved_list_state = None
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
            return '用户'

    def handle_tree_selection(self, selected_item):
        """处理树视图选择并加载内容"""
        try:
            if not selected_item.IsOk():
                return

            # 如果在筛选模式下，自动退出筛选
            if hasattr(self, 'filter_mode') and self.filter_mode:
                self.filter_mode = None

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
            pass

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
            pass

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
            pass

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
            pass

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
            pass

    def on_list_focus(self, event):
        """列表获得焦点事件 - 确保有选中项以便屏幕阅读器朗读"""
        try:
            # 如果列表有内容但没有选中项，自动选择第一项
            if self.list_ctrl.GetItemCount() > 0 and self.list_ctrl.GetSelectedRow() == -1:
                self.list_ctrl.SelectRow(0)
                self.list_ctrl.SetFocus()
        except Exception as e:
            pass
        event.Skip()

    def on_list_selection(self, event):
        """列表选择事件 - DataViewListCtrl版本"""
        try:
            # DataViewListCtrl 的选择事件处理
            pass
        except Exception as e:
            pass
        event.Skip()

    def on_list_activated(self, event):
        """列表激活事件 - 处理分页控制和帖子详情加载"""
        try:
            selected_row = self.list_ctrl.GetSelectedRow()
            if selected_row != -1 and selected_row < len(self.list_data):
                self.handle_row_activation(selected_row)
        except Exception as e:
            pass
        event.Skip()

    def on_list_context_menu(self, event):
        """处理列表右键菜单/上下文菜单"""
        try:
            # 获取当前选中项
            selected_row = self.list_ctrl.GetSelectedRow()
            if selected_row == -1 or selected_row >= len(self.list_data):
                return

            item_data = self.list_data[selected_row]

            # 检查内容类型，调用相应的菜单处理方法
            if hasattr(self, 'current_content_type'):
                if self.current_content_type == 'thread_detail':
                    # 帖子详情页面的上下文菜单
                    self.on_thread_detail_context_menu(event, selected_row, item_data)
                    return
                elif self.current_content_type in ['user_threads', 'user_posts']:
                    # 用户内容页面的上下文菜单
                    self.on_user_content_context_menu(event, selected_row, item_data)
                    return

            # 默认的帖子列表上下文菜单
            self.on_thread_list_context_menu(event, selected_row, item_data)

        except Exception as e:
            pass

    def on_thread_detail_context_menu(self, event, selected_row, item_data):
        """帖子详情页面的上下文菜单"""
        try:
            # 只在帖子项上显示菜单
            if item_data.get('type') != 'post':
                return

            # 获取帖子数据 - 处理正常模式和筛选模式的不同数据结构
            if 'post_data' in item_data:
                # 正常模式
                post_data = item_data.get('post_data', {})
            else:
                # 筛选模式
                post_data = item_data.get('data', {})

            uid = post_data.get('uid') or post_data.get('authorid')  # 根据调试信息，使用uid字段
            pid = post_data.get('pid')  # 使用正确的字段名称
            username = post_data.get('username') or post_data.get('author', '用户')  # 根据调试信息，使用username字段

            if not uid:
                return

            # 判断是否可以编辑（只能编辑自己的帖子）
            can_edit = self.should_show_edit_menu(post_data)
            is_thread_author = self.is_thread_author(post_data)

            # 创建菜单
            menu = wx.Menu()

            # 基础功能
            refresh_item = menu.Append(wx.ID_ANY, "刷新(&R)\tF5")
            menu.AppendSeparator()

            # 检查是否处于筛选模式
            is_filter_mode = hasattr(self, 'filter_mode') and self.filter_mode
            filter_username = self.filter_mode.get('username') if is_filter_mode else None

            if is_filter_mode:
                # 筛选模式下的菜单
                tip_item = menu.Append(wx.ID_ANY, f"筛选模式：只看{filter_username}")
                tip_item.Enable(False)  # 禁用，仅作提示
                menu.AppendSeparator()
                reply_item = menu.Append(wx.ID_ANY, f"回复{username}(&H)\tCtrl+回车")
                profile_item = menu.Append(wx.ID_ANY, f"查看{username}的资料(&P)\tShift+回车")

                # 筛选模式下如果可以编辑仍显示编辑功能
                if can_edit:
                    if is_thread_author:
                        edit_item = menu.Append(wx.ID_ANY, f"编辑帖子(&E)\tCtrl+E")
                    else:
                        edit_item = menu.Append(wx.ID_ANY, f"编辑回复(&E)\tCtrl+E")
                    menu.AppendSeparator()
                else:
                    menu.AppendSeparator()
            else:
                # 正常模式下的完整功能
                reply_item = menu.Append(wx.ID_ANY, f"回复{username}(&H)\tCtrl+回车")
                profile_item = menu.Append(wx.ID_ANY, f"查看{username}的资料(&P)\tShift+回车")

                # 只有自己的帖子才显示编辑功能
                if can_edit:
                    menu.AppendSeparator()
                    if is_thread_author:
                        edit_item = menu.Append(wx.ID_ANY, f"编辑帖子(&E)\tCtrl+E")
                    else:
                        edit_item = menu.Append(wx.ID_ANY, f"编辑回复(&E)\tCtrl+E")

                menu.AppendSeparator()
                filter_item = menu.Append(wx.ID_ANY, f"只看{username}(&K)")

                # 用户内容的二级菜单
                user_content_menu = wx.Menu()
                threads_item = user_content_menu.Append(wx.ID_ANY, f"{username}的发布(&F)")
                posts_item = user_content_menu.Append(wx.ID_ANY, f"{username}的回复(&H)")
                menu.AppendSubMenu(user_content_menu, f"{username}的全部帖子(&T)")

            # 事件绑定
            self.Bind(wx.EVT_MENU, lambda e: self.on_refresh_thread_detail(), refresh_item)
            self.Bind(wx.EVT_MENU, lambda e: self.on_reply_to_floor(post_data), reply_item)
            self.Bind(wx.EVT_MENU, lambda e: self.on_view_user_profile(uid, username), profile_item)

            if can_edit:
                self.Bind(wx.EVT_MENU, lambda e: self.on_edit_post(post_data), edit_item)

            if not is_filter_mode:
                self.Bind(wx.EVT_MENU, lambda e: self.on_filter_posts_by_user(username, uid), filter_item)
                # 绑定二级菜单事件
                self.Bind(wx.EVT_MENU, lambda e: self.on_view_user_threads(username, uid), threads_item)
                self.Bind(wx.EVT_MENU, lambda e: self.on_view_user_posts(username, uid), posts_item)

            # 显示菜单 - 处理位置问题
            mouse_pos = wx.GetMousePosition()
            screen_pos = self.list_ctrl.ScreenToClient(mouse_pos)

            # 如果客户端坐标为负数，使用默认位置
            if screen_pos.x < 0 or screen_pos.y < 0:
                # 使用简单计算的位置
                row_height = 20  # 估计的行高
                popup_pos = wx.Point(10, selected_row * row_height + 10)
            else:
                popup_pos = screen_pos

            # 显示菜单
            self.list_ctrl.PopupMenu(menu, popup_pos)
            menu.Destroy()

        except Exception as e:
            # 静默处理异常
            pass

    def on_thread_list_context_menu(self, event, selected_row, item_data):
        """帖子列表页面的上下文菜单（保持原有功能）"""
        try:
            # 检查选中项的数据，只在有效的帖子项上显示菜单
            if item_data.get('type') == 'pagination':
                return

            # 创建菜单
            menu = wx.Menu()

            # 添加菜单项
            refresh_item = menu.Append(wx.ID_ANY, "刷新(&R)\tF5")
            menu.AppendSeparator()
            open_web_item = menu.Append(wx.ID_ANY, "网页打开(&W)\tCtrl+W")
            copy_title_item = menu.Append(wx.ID_ANY, "拷贝帖子标题(&C)\tCtrl+C")
            copy_url_item = menu.Append(wx.ID_ANY, "拷贝帖子地址(&D)\tCtrl+D")

            # 绑定事件
            self.Bind(wx.EVT_MENU, self.on_refresh, refresh_item)
            self.Bind(wx.EVT_MENU, self.on_open_in_browser, open_web_item)
            self.Bind(wx.EVT_MENU, self.on_copy_title, copy_title_item)
            self.Bind(wx.EVT_MENU, self.on_copy_url, copy_url_item)

            # 显示菜单
            self.PopupMenu(menu)
            menu.Destroy()

        except Exception as e:
            pass

    def on_user_content_context_menu(self, event, selected_row, item_data):
        """用户内容页面的上下文菜单"""
        try:
            # 暂时保持简单，可以后续扩展
            self.on_thread_list_context_menu(event, selected_row, item_data)
        except Exception as e:
            pass

    def handle_row_activation(self, selected_row):
        """处理行激活的通用逻辑"""
        try:
            # 检查是否正在处理用户资料查看
            if hasattr(self, '_handling_user_profile') and self._handling_user_profile:
                return

            # 检查是否正在处理回复
            if hasattr(self, '_handling_reply') and self._handling_reply:
                return

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
                    if self.current_content_type in ['thread_list', 'search_result', 'home_content']:
                        # 加载帖子详情
                        tid = item_data.get('tid', 0)
                        if tid and tid > 0:
                            self.load_thread_detail(tid)
                    elif self.current_content_type in ['user_threads', 'user_posts']:
                        # 从用户内容加载帖子详情，需要保存用户内容状态以便返回
                        tid = item_data.get('tid', 0)
                        if tid and tid > 0:
                            self.load_thread_detail_from_user_content(tid)
                    elif self.current_content_type == 'message_list':
                        # 加载消息详情
                        touid = item_data.get('touid', 0)
                        if touid and touid > 0:
                            self.load_message_detail(touid)
                    elif self.current_content_type == 'thread_detail':
                        # 帖子详情中的楼层编辑
                        self.show_floor_editor(selected_row)

        except Exception as e:
            pass

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

    def on_settings(self, event):
        """设置事件"""
        from settings_dialog import SettingsDialog
        dialog = SettingsDialog(self, self.config_manager)
        dialog.ShowModal()

        # 设置改变后，重新加载当前列表以应用新的设置
        self.reload_current_list()

        dialog.Destroy()

    def on_refresh(self, event):
        """刷新当前内容"""
        # 保存当前状态以便刷新后恢复焦点
        selected_row = self.list_ctrl.GetSelectedRow()
        if selected_row != -1:
            self.saved_list_index = 0  # 刷新后定位到第一个项目

        # 根据不同内容类型调用相应的刷新方法
        if hasattr(self, 'current_content_type'):
            if self.current_content_type == 'thread_list':
                # 重新加载当前板块
                if hasattr(self, 'current_fid') and self.current_fid:
                    self.load_forum_section_with_type(None, self.current_fid,
                                                      self.current_api_params.get('typeid1'),
                                                      self.current_api_params.get('typeid2'))
            elif self.current_content_type == 'thread_detail':
                # 重新加载帖子详情 - 使用save_state=False避免覆盖导航状态
                if hasattr(self, 'current_thread_info') and self.current_thread_info:
                    tid = self.current_thread_info.get('tid')
                    current_page = getattr(self, 'current_pagination', {}).get('page', 1)
                    if tid:
                        self.load_thread_detail_and_restore_page(tid, current_page, save_state=False)
            elif self.current_content_type == 'home_content':
                # 重新加载首页内容
                if hasattr(self, 'current_orderby'):
                    if self.current_orderby == 'latest':
                        self.load_latest_threads_and_restore_focus()
                    elif self.current_orderby == 'lastpost':
                        self.load_latest_replies_and_restore_focus()
            elif self.current_content_type == 'user_threads':
                # 重新加载我的发表
                self.load_my_threads_and_restore_focus()
            elif self.current_content_type == 'user_posts':
                # 重新加载我的回复
                self.load_my_posts_and_restore_focus()
            elif self.current_content_type == 'message_list':
                # 重新加载消息列表
                self.load_messages()
                # 消息列表刷新后也设置焦点到第一个项目
                if self.list_ctrl.GetItemCount() > 0:
                    self.saved_list_index = 0
                    wx.CallAfter(self.reset_keyboard_cursor, 0)
            elif self.current_content_type == 'message_detail':
                # 重新加载消息详情
                if hasattr(self, 'current_touid') and self.current_touid:
                    self.load_message_detail(self.current_touid)
            elif self.current_content_type == 'search_result':
                # 重新加载搜索结果
                if hasattr(self, 'current_keyword') and self.current_keyword:
                    self.search_content_and_restore_focus(self.current_keyword)

    def get_selected_thread_data(self):
        """获取当前选中的帖子数据"""
        try:
            selected_row = self.list_ctrl.GetSelectedRow()
            if selected_row == -1 or selected_row >= len(self.list_data):
                return None

            item_data = self.list_data[selected_row]
            if item_data.get('type') == 'pagination':
                return None

            return item_data
        except Exception:
            return None

    def build_thread_url(self, thread_data):
        """构建帖子的URL地址"""
        try:
            if not thread_data:
                return None

            # 获取帖子ID
            tid = thread_data.get('tid')
            if not tid:
                return None

            # 获取当前论坛URL
            if hasattr(self, 'current_forum_config') and self.current_forum_config:
                forum_url = self.current_forum_config.get('url', '').rstrip('/')
            else:
                # 默认使用争渡论坛的URL格式
                forum_url = 'http://www.zd.hk'

            # 构建标准格式的帖子URL
            thread_url = f"{forum_url}/thread-{tid}-1-1.html"
            return thread_url

        except Exception:
            return None

    def on_open_in_browser(self, event):
        """在浏览器中打开帖子"""
        try:
            # 获取选中的帖子数据
            thread_data = self.get_selected_thread_data()
            if not thread_data:
                return

            # 构建URL
            url = self.build_thread_url(thread_data)
            if not url:
                return

            # 在默认浏览器中打开
            webbrowser.open(url)

        except Exception:
            # 静默处理异常
            pass

    def copy_to_clipboard(self, text):
        """使用系统剪贴板API复制文本到剪贴板"""
        try:
            import subprocess
            import platform

            # 移除多余的序号信息（如果存在）
            # 例如："标题内容 ，1之24项" -> "标题内容"
            cleaned_text = text
            if '，' in text and '项' in text:
                # 移除末尾的序号信息
                cleaned_text = text.split('，')[0]

            # 根据不同操作系统使用相应的系统剪贴板命令
            if platform.system() == 'Windows':
                # Windows系统使用clip命令
                subprocess.run(['clip'], input=cleaned_text.strip().encode('gbk'), check=True, shell=True)
            elif platform.system() == 'Darwin':  # macOS
                # macOS使用pbcopy命令
                subprocess.run(['pbcopy'], input=cleaned_text.strip().encode('utf-8'), check=True)
            else:  # Linux及其他系统
                # Linux使用xclip命令（如果可用）
                try:
                    subprocess.run(['xclip', '-selection', 'clipboard'],
                                 input=cleaned_text.strip().encode('utf-8'), check=True)
                except (FileNotFoundError, subprocess.CalledProcessError):
                    # 如果xclip不可用，尝试使用xsel
                    try:
                        subprocess.run(['xsel', '--clipboard', '--input'],
                                     input=cleaned_text.strip().encode('utf-8'), check=True)
                    except (FileNotFoundError, subprocess.CalledProcessError):
                        # 如果都不可用，回退到wxPython
                        if wx.TheClipboard.Open():
                            try:
                                wx.TheClipboard.SetData(wx.TextDataObject(cleaned_text))
                                wx.TheClipboard.Close()
                            except Exception:
                                wx.TheClipboard.Close()
        except Exception:
            # 静默处理异常
            pass

    def on_copy_title(self, event):
        """拷贝帖子标题到剪贴板"""
        try:
            # 获取当前选中的行
            selected_row = self.list_ctrl.GetSelectedRow()
            if selected_row == -1:
                return

            # 直接获取列表第一列的显示文本
            # 这就是用户看到的文本内容，无需额外处理
            display_text = self.list_ctrl.GetTextValue(selected_row, 0)
            if not display_text:
                return

            # 复制到剪贴板
            self.copy_to_clipboard(display_text)

        except Exception:
            # 静默处理异常
            pass

    def on_copy_url(self, event):
        """拷贝帖子地址到剪贴板"""
        try:
            # 获取选中的帖子数据
            thread_data = self.get_selected_thread_data()
            if not thread_data:
                return

            # 构建URL
            url = self.build_thread_url(thread_data)
            if not url:
                return

            # 使用系统剪贴板API复制到剪贴板
            self.copy_to_clipboard(url)

        except Exception:
            # 静默处理异常
            pass

    def reload_current_list(self):
        """重新加载当前列表以应用设置变更"""
        try:
            # 根据当前内容类型重新加载列表
            if hasattr(self, 'current_content_type'):
                if self.current_content_type == 'thread_list':
                    # 重新加载当前板块
                    if hasattr(self, 'current_fid') and self.current_fid:
                        self.load_forum_section_with_type(None, self.current_fid,
                                                          self.current_api_params.get('typeid1'),
                                                          self.current_api_params.get('typeid2'))
                elif self.current_content_type == 'thread_detail':
                    # 重新加载帖子详情
                    if hasattr(self, 'current_thread_info') and self.current_thread_info:
                        tid = self.current_thread_info.get('tid')
                        if tid:
                            self.load_thread_detail(tid)
                elif self.current_content_type == 'home_content':
                    # 重新加载首页内容
                    if hasattr(self, 'current_orderby'):
                        if self.current_orderby == 'latest':
                            self.load_latest_threads_and_restore_focus()
                        elif self.current_orderby == 'lastpost':
                            self.load_latest_replies_and_restore_focus()
                elif self.current_content_type == 'user_threads':
                    # 重新加载我的发表
                    self.load_my_threads_and_restore_focus()
                elif self.current_content_type == 'user_posts':
                    # 重新加载我的回复
                    self.load_my_posts_and_restore_focus()
                elif self.current_content_type == 'message_list':
                    # 重新加载消息列表
                    self.load_messages()
                elif self.current_content_type == 'message_detail':
                    # 重新加载消息详情
                    if hasattr(self, 'current_touid') and self.current_touid:
                        self.load_message_detail(self.current_touid)
                elif self.current_content_type == 'search_result':
                    # 重新加载搜索结果
                    if hasattr(self, 'current_keyword') and self.current_keyword:
                        self.search_content_and_restore_focus(self.current_keyword)
        except Exception as e:
            # 重新加载失败时不显示错误，保持用户体验
            pass

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
            self.load_latest_threads_and_restore_focus()
        elif text == "最新回复":
            self.load_latest_replies_and_restore_focus()
        elif text == "我的发表":
            self.load_my_threads_and_restore_focus()
        elif text == "我的回复":
            self.load_my_posts_and_restore_focus()
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
            pass

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

    def load_my_posts(self):
        """加载我的回复"""
        user_info = self.auth_manager.get_user_info(self.current_forum)
        if user_info:
            uid = user_info.get('uid')
            if uid:
                self.current_uid = uid
                result = self.forum_client.get_user_posts(self.current_forum, uid)
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

        # 如果第一页为空但总页数大于1，自动查找有内容的第一页
        threadlist = result.get('threadlist', [])
        pagination = result.get('pagination', {})
        total_page = pagination.get('totalpage', 1)

        if not threadlist and total_page > 1:
            # 使用二分查找快速找到有内容的第一页
            first_content_page = self._find_first_content_page(api_params, total_page)

            if first_content_page > 1:
                result = self.forum_client.get_thread_list_with_type(self.current_forum, api_params, first_content_page)

                # 保存偏移信息，用于显示逻辑
                pagination['page_offset'] = first_content_page - 1
                pagination['real_total_page'] = total_page
                pagination['totalpage'] = total_page - first_content_page + 1  # 调整显示的总页数
                pagination['page'] = 1  # 强制显示为第1页

                # 使用修改后的分页信息
                self.display_threads(result.get('threadlist', []), pagination, 'thread_list', api_params)
            else:
                self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'thread_list', api_params)
        else:
            # 第一页有内容，正常显示
            self.display_threads(result.get('threadlist', []), result.get('pagination', {}), 'thread_list', api_params)

    def _find_first_content_page(self, api_params, total_page):
        """使用二分查找快速定位有内容的第一页"""
        try:
            left = 1
            right = total_page
            first_content_page = total_page + 1  # 默认为没有找到

            while left <= right:
                mid = (left + right) // 2

                try:
                    # 检查中间页是否有内容
                    result = self.forum_client.get_thread_list_with_type(self.current_forum, api_params, mid)

                    if result and isinstance(result, dict):
                        # 检查不同的可能结果结构
                        if result.get('result') == 1:
                            # 新版本API结构
                            threadlist = result.get('message', {}).get('threadlist', [])
                        elif 'threadlist' in result:
                            # 旧版本API结构
                            threadlist = result.get('threadlist', [])
                        else:
                            left = mid + 1
                            continue

                        if threadlist:  # 找到有内容的页面
                            first_content_page = mid
                            right = mid - 1  # 继续向左查找更早的有内容页面
                        else:  # 没有内容，向右查找
                            left = mid + 1
                    else:
                        left = mid + 1

                except Exception as page_check_e:
                    # 处理单个页面检查时的异常（包括编码异常）
                    left = mid + 1  # 出错时向右查找

            if first_content_page <= total_page:
                return first_content_page
            else:
                return 1

        except Exception as e:
            return 1  # 出错时返回第1页

    def search_content(self, keyword):
        """搜索内容"""
        self.current_keyword = keyword
        result = self.forum_client.search(self.current_forum, keyword)
        threads = result.get('threadlist', [])

        # 检查是否有搜索结果
        if not threads:
            wx.MessageBox(f"没有找到包含 '{keyword}' 的内容", "搜索结果", wx.OK | wx.ICON_WARNING)
            return

        # 清理搜索结果中的HTML标签
        cleaned_threads = []
        for thread in threads:
            cleaned_thread = thread.copy()
            # 清理标题中的HTML标签
            if 'subject' in cleaned_thread:
                cleaned_thread['subject'] = self.clean_html_tags(cleaned_thread['subject'])
            cleaned_threads.append(cleaned_thread)

        # 显示搜索结果
        self.display_threads(cleaned_threads, result.get('pagination', {}), 'search_result')

        # 搜索成功后自动跳到列表第一项
        if self.list_ctrl.GetItemCount() > 0:
            self.list_ctrl.SelectRow(0)
            self.list_ctrl.SetFocus()

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

        # 检查是否需要显示列表序号
        show_list_numbers = self.config_manager.get_show_list_numbers()

        for thread in threads:
            # 构建新的显示格式
            subject = self.clean_html_tags(thread.get('subject', ''))
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

            # 构建存储的数据 - 保存完整的帖子数据以便恢复时使用
            thread_data = {
                'tid': thread.get('tid', 0),
                'type': 'thread',
                'subject': subject,
                'username': username,
                'views': views,
                'forumname': forumname,
                'dateline_fmt': dateline_fmt,
                'posts': posts,
                'lastpost_fmt': lastpost_fmt,
                'lastusername': lastusername
            }

            self.list_data.append(thread_data)

        # 根据设计文档添加4个分页控制项
        # 如果没有分页信息，创建默认分页信息
        if not pagination or not isinstance(pagination, dict):
            pagination = {'page': 1, 'totalpage': 1}

        # 总是添加分页控制，即使只有一页
        self.add_pagination_controls(pagination)

        # 如果需要显示序号，使用重新构建列表的方式
        if show_list_numbers:
            total_items = len(self.list_data)  # 使用list_data的长度，因为已经包含了所有项
            # 清空列表
            self.list_ctrl.DeleteAllItems()
            # 重新构建所有项目，这次包含序号
            for i in range(total_items):
                # 获取存储的数据
                data = self.list_data[i]
                if data['type'] == 'thread':
                    # 帖子项目 - 构建包含序号的显示文本
                    try:
                        thread = self.current_threads[i] if i < len(self.current_threads) else {}
                        subject = thread.get('subject', '')
                        username = thread.get('username', '')
                        views = thread.get('views', 0)
                        forumname = thread.get('forumname', '')
                        dateline_fmt = thread.get('dateline_fmt', '')
                        posts = thread.get('posts', 0)
                        lastpost_fmt = thread.get('lastpost_fmt', '')
                        lastusername = thread.get('lastusername', '')

                        display_text = f"{subject} 作者:{username};浏览:{views};板块:{forumname};发表时间:{dateline_fmt};回复:{posts};回复时间:{lastpost_fmt};最后回复:{lastusername} ，{i+1}之{total_items}项"
                    except:
                        display_text = f"帖子数据加载失败 ，{i+1}之{total_items}项"

                    # 清理多余信息
                    import re
                    display_text = re.sub(r';?\s*数据:\s*\d+\s*', '', display_text)
                    display_text = re.sub(r';?\s*data:\s*\d+\s*', '', display_text, flags=re.IGNORECASE)
                    display_text = re.sub(r';\s*数据:\s*\d+.*$', '', display_text)
                    display_text = re.sub(r';\s*data:\s*\d+.*$', '', display_text, flags=re.IGNORECASE)
                    display_text = re.sub(r'\s+数据:\s*\d+.*$', '', display_text)
                    display_text = re.sub(r'\s+data:\s*\d+.*$', '', display_text, flags=re.IGNORECASE)
                    display_text = re.sub(r';+\s*$', '', display_text)
                    display_text = display_text.strip()

                elif data['type'] == 'post':
                    # 回复项目 - 构建包含序号的显示文本
                    try:
                        post_data = data.get('post_data', {})
                        floor = data.get('floor', i + 1)
                        username = post_data.get('username', '')
                        content = self.clean_html_tags(post_data.get('message', ''))
                        create_date = post_data.get('dateline_fmt', '')

                        if floor == 1:
                            formatted_content = f"楼主 {username} 说\n{content}\n发表时间：{create_date} ，{i+1}之{total_items}项"
                        else:
                            formatted_content = f"{floor}楼 {username} 说\n{content}\n发表时间：{create_date} ，{i+1}之{total_items}项"
                        display_text = formatted_content
                    except:
                        display_text = f"回复数据加载失败 ，{i+1}之{total_items}项"

                elif data['type'] == 'message':
                    # 消息项目 - 构建包含序号的显示文本
                    try:
                        message_data = data.get('message_data', {})
                        username = message_data.get('username', '')
                        display_text = f"{username} ，{i+1}之{total_items}项"
                    except:
                        display_text = f"消息数据加载失败 ，{i+1}之{total_items}项"

                elif data['type'] == 'conversation':
                    # 消息对话项目 - 构建包含序号的显示文本
                    try:
                        message_data = data.get('message_data', {})
                        content = message_data.get('content', '')
                        formatted_content = content

                        if len(formatted_content) > 200:
                            formatted_content = formatted_content[:200] + '...'
                        display_text = f"{formatted_content} ，{i+1}之{total_items}项"
                    except:
                        display_text = f"对话数据加载失败 ，{i+1}之{total_items}项"

                elif data['type'] == 'pagination':
                    # 分页控制项目 - 构建包含序号的显示文本
                    action = data.get('action', '')
                    page = data.get('page', 1)

                    if action == 'prev':
                        display_text = f"上一页({page}) ，{i+1}之{total_items}项"
                    elif action == 'next':
                        display_text = f"下一页({page}) ，{i+1}之{total_items}项"
                    elif action == 'jump':
                        current_page = self.current_pagination.get('page', 1)
                        total_page = self.current_pagination.get('totalpage', 1)
                        display_text = f"当前第{current_page}页共{total_page}页，回车输入页码跳转 ，{i+1}之{total_items}项"
                    elif action == 'reply':
                        display_text = f"回复帖子 ，{i+1}之{total_items}项"
                    else:
                        display_text = f"分页控制 ，{i+1}之{total_items}项"

                    # 清理分页文本
                    import re
                    display_text = re.sub(r';?\s*数据:\s*\d+\s*', '', display_text)
                    display_text = re.sub(r';?\s*data:\s*\d+\s*', '', display_text, flags=re.IGNORECASE)
                    display_text = re.sub(r';\s*数据:\s*\d+.*$', '', display_text)
                    display_text = re.sub(r';\s*data:\s*\d+.*$', '', display_text, flags=re.IGNORECASE)
                    display_text = re.sub(r'\s+数据:\s*\d+.*$', '', display_text)
                    display_text = re.sub(r'\s+data:\s*\d+.*$', '', display_text, flags=re.IGNORECASE)
                    display_text = re.sub(r';+\s*$', '', display_text)
                    display_text = display_text.strip()

                else:
                    # 其他类型的项目
                    display_text = f"项目 ，{i+1}之{total_items}项"

                # 重新添加到列表
                self.list_ctrl.AppendItem([display_text])

                # 在数据中存储序号信息
                data['list_number'] = f"{i+1}之{total_items}项"

    
    def add_pagination_controls(self, pagination):
        """根据设计文档添加4个分页控制项 - DataViewListCtrl版本"""
        current_page = pagination.get('page', 1)
        total_page = pagination.get('totalpage', 1)

        # 检查是否在筛选模式下
        is_filter_mode = hasattr(self, 'filter_mode') and self.filter_mode
        filter_username = self.filter_mode.get('username', '') if is_filter_mode else ''

        # 1. 上一页控制项
        if current_page > 1:
            if is_filter_mode:
                prev_text = f"上一页({current_page - 1})（只看{filter_username}）"
            else:
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
            if is_filter_mode:
                next_text = f"下一页({current_page + 1})（只看{filter_username}）"
            else:
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
        if is_filter_mode:
            jump_text = f"第{current_page}页/共{total_page}页 (只看{filter_username}) (回车跳转)"
        else:
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
        # 确保清除用户内容状态，避免影响普通导航
        self.user_content_state_before_thread = None
        self.load_thread_detail_and_restore_page(tid, 1)

    def load_thread_detail_from_user_content(self, tid):
        """从用户内容页面加载帖子详情，保存用户内容状态以便返回"""
        # 保存用户内容状态，用于退格键返回
        self.user_content_state_before_thread = {
            'user_content_mode': getattr(self, 'user_content_mode', None),
            'current_content_type': getattr(self, 'current_content_type', ''),
            'current_uid': getattr(self, 'current_uid', None),
            'selected_index': self.list_ctrl.GetSelectedRow() if self.list_ctrl.GetSelectedRow() != -1 else 0,
            'current_page': getattr(self, 'current_pagination', {}).get('page', 1),
            # 保存最初的帖子详情状态，避免被后续的帖子详情覆盖
            'original_thread_state': getattr(self, 'previous_state', None)
        }
        # 清除 user_content_mode，避免键盘事件处理时匹配到错误的条件
        self.user_content_mode = None

        # 加载帖子详情（不保存状态，避免覆盖用户内容状态）
        self.load_thread_detail_and_restore_page(tid, 1, save_state=False)

    def load_thread_detail_and_restore_page(self, tid, target_page=1, save_state=True):
        """加载帖子详情并恢复到指定页面"""
        try:
            # 保存当前状态，用于退格键返回（仅在首次进入时保存）
            if save_state and hasattr(self, 'current_content_type'):
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

                # 保存完整的列表状态，用于退格键退出时直接恢复（不刷新）
                if hasattr(self, 'list_ctrl') and hasattr(self, 'list_data'):
                    # 保存当前列表的所有数据
                    self.saved_list_state = {
                        'list_data': self.list_data.copy(),  # 深拷贝列表数据
                        'current_pagination': getattr(self, 'current_pagination', {}).copy(),
                        'current_content_type': getattr(self, 'current_content_type', ''),
                        'current_forum': getattr(self, 'current_forum', ''),
                        'current_fid': getattr(self, 'current_fid', None),
                        'current_keyword': getattr(self, 'current_keyword', ''),
                        'current_orderby': getattr(self, 'current_orderby', 'latest'),
                        'selected_index': selected if selected != -1 else 0,
                        'window_title': self.GetTitle()
                    }

            self.current_tid = tid

            # 总是加载指定页面，确保刷新后保持在同一页
            result = self.forum_client.get_thread_detail(self.current_forum, tid, target_page)

            posts = result.get('postlist', [])
            pagination = result.get('pagination', {})
            thread_info = result.get('thread_info', {})

            # 显示帖子详情
            self.display_posts(posts, pagination, thread_info)

        except Exception as e:
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

            # 检查是否在筛选模式下
            if hasattr(self, 'filter_mode') and self.filter_mode:
                # 筛选模式下的分页
                uid = self.filter_mode.get('uid')
                tid = self.filter_mode.get('original_tid')
                if uid and tid:
                    self.load_thread_detail_with_filter(tid, uid, page=next_page)
                    return

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
                if hasattr(self, 'filter_mode') and self.filter_mode:
                    # 在筛选模式下，使用API筛选
                    filter_uid = self.filter_mode.get('uid')
                    result = self.forum_client.get_thread_detail(self.current_forum, self.current_tid, next_page, uid=filter_uid)
                    self.display_filtered_posts(result.get('postlist', []), result.get('thread_info', {}), result.get('pagination', {}))
                else:
                    # 正常模式
                    result = self.forum_client.get_thread_detail(self.current_forum, self.current_tid, next_page)
                    self.display_posts(result.get('postlist', []), result.get('pagination', {}), result.get('thread_info', {}))

                # 设置键盘游标到第一项
                wx.CallAfter(self.reset_keyboard_cursor, 0)

        except Exception as e:
            import traceback
            error_detail = f"加载下一页失败: {str(e)}\n{traceback.format_exc()}"
            print(error_detail)  # 控制台输出详细错误
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

        # 检查是否需要显示列表序号
        show_list_numbers = self.config_manager.get_show_list_numbers()

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

            # 构建存储的数据
            post_data = {
                'type': 'post',
                'index': i,  # 保持从0开始的索引
                'floor': floor,
                'post_data': post
            }

            self.list_data.append(post_data)

        # 根据设计文档添加4个分页控制项
        # 如果没有分页信息，创建默认分页信息
        if not pagination or not isinstance(pagination, dict):
            pagination = {'page': 1, 'totalpage': 1}
        else:
            pass  # 使用传入的分页信息

        # 总是添加分页控制，即使只有一页
        self.add_pagination_controls(pagination)

        # 如果需要显示序号，使用重新构建列表的方式
        if show_list_numbers:
            total_items = len(self.list_data)  # 使用list_data的长度，因为已经包含了所有项
            # 清空列表
            self.list_ctrl.DeleteAllItems()
            # 重新构建所有项目，这次包含序号
            for i in range(total_items):
                # 获取存储的数据
                data = self.list_data[i]
                if data['type'] == 'thread':
                    # 帖子项目 - 构建包含序号的显示文本
                    try:
                        thread = self.current_threads[i] if i < len(self.current_threads) else {}
                        subject = thread.get('subject', '')
                        username = thread.get('username', '')
                        views = thread.get('views', 0)
                        forumname = thread.get('forumname', '')
                        dateline_fmt = thread.get('dateline_fmt', '')
                        posts = thread.get('posts', 0)
                        lastpost_fmt = thread.get('lastpost_fmt', '')
                        lastusername = thread.get('lastusername', '')

                        display_text = f"{subject} 作者:{username};浏览:{views};板块:{forumname};发表时间:{dateline_fmt};回复:{posts};回复时间:{lastpost_fmt};最后回复:{lastusername} ，{i+1}之{total_items}项"
                    except:
                        display_text = f"帖子数据加载失败 ，{i+1}之{total_items}项"

                    # 清理多余信息
                    import re
                    display_text = re.sub(r';?\s*数据:\s*\d+\s*', '', display_text)
                    display_text = re.sub(r';?\s*data:\s*\d+\s*', '', display_text, flags=re.IGNORECASE)
                    display_text = re.sub(r';\s*数据:\s*\d+.*$', '', display_text)
                    display_text = re.sub(r';\s*data:\s*\d+.*$', '', display_text, flags=re.IGNORECASE)
                    display_text = re.sub(r'\s+数据:\s*\d+.*$', '', display_text)
                    display_text = re.sub(r'\s+data:\s*\d+.*$', '', display_text, flags=re.IGNORECASE)
                    display_text = re.sub(r';+\s*$', '', display_text)
                    display_text = display_text.strip()

                elif data['type'] == 'post':
                    # 回复项目 - 构建包含序号的显示文本
                    try:
                        post_data = data.get('post_data', {})
                        floor = data.get('floor', i + 1)
                        username = post_data.get('username', '')
                        content = self.clean_html_tags(post_data.get('message', ''))
                        create_date = post_data.get('dateline_fmt', '')

                        if floor == 1:
                            formatted_content = f"楼主 {username} 说\n{content}\n发表时间：{create_date} ，{i+1}之{total_items}项"
                        else:
                            formatted_content = f"{floor}楼 {username} 说\n{content}\n发表时间：{create_date} ，{i+1}之{total_items}项"
                        display_text = formatted_content
                    except:
                        display_text = f"回复数据加载失败 ，{i+1}之{total_items}项"

                elif data['type'] == 'message':
                    # 消息项目 - 构建包含序号的显示文本
                    try:
                        message_data = data.get('message_data', {})
                        username = message_data.get('username', '')
                        display_text = f"{username} ，{i+1}之{total_items}项"
                    except:
                        display_text = f"消息数据加载失败 ，{i+1}之{total_items}项"

                elif data['type'] == 'conversation':
                    # 消息对话项目 - 构建包含序号的显示文本
                    try:
                        message_data = data.get('message_data', {})
                        content = message_data.get('content', '')
                        formatted_content = content

                        if len(formatted_content) > 200:
                            formatted_content = formatted_content[:200] + '...'
                        display_text = f"{formatted_content} ，{i+1}之{total_items}项"
                    except:
                        display_text = f"对话数据加载失败 ，{i+1}之{total_items}项"

                elif data['type'] == 'pagination':
                    # 分页控制项目 - 构建包含序号的显示文本
                    action = data.get('action', '')
                    page = data.get('page', 1)

                    if action == 'prev':
                        display_text = f"上一页({page}) ，{i+1}之{total_items}项"
                    elif action == 'next':
                        display_text = f"下一页({page}) ，{i+1}之{total_items}项"
                    elif action == 'jump':
                        current_page = self.current_pagination.get('page', 1)
                        total_page = self.current_pagination.get('totalpage', 1)
                        display_text = f"当前第{current_page}页共{total_page}页，回车输入页码跳转 ，{i+1}之{total_items}项"
                    elif action == 'reply':
                        display_text = f"回复帖子 ，{i+1}之{total_items}项"
                    else:
                        display_text = f"分页控制 ，{i+1}之{total_items}项"

                    # 清理分页文本
                    import re
                    display_text = re.sub(r';?\s*数据:\s*\d+\s*', '', display_text)
                    display_text = re.sub(r';?\s*data:\s*\d+\s*', '', display_text, flags=re.IGNORECASE)
                    display_text = re.sub(r';\s*数据:\s*\d+.*$', '', display_text)
                    display_text = re.sub(r';\s*data:\s*\d+.*$', '', display_text, flags=re.IGNORECASE)
                    display_text = re.sub(r'\s+数据:\s*\d+.*$', '', display_text)
                    display_text = re.sub(r'\s+data:\s*\d+.*$', '', display_text, flags=re.IGNORECASE)
                    display_text = re.sub(r';+\s*$', '', display_text)
                    display_text = display_text.strip()

                else:
                    # 其他类型的项目
                    display_text = f"项目 ，{i+1}之{total_items}项"

                # 重新添加到列表
                self.list_ctrl.AppendItem([display_text])

                # 在数据中存储序号信息
                data['list_number'] = f"{i+1}之{total_items}项"

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

            # 检查是否在筛选模式下
            if hasattr(self, 'filter_mode') and self.filter_mode:
                # 筛选模式下的分页
                uid = self.filter_mode.get('uid')
                tid = self.filter_mode.get('original_tid')
                if uid and tid:
                    self.load_thread_detail_with_filter(tid, uid, page=prev_page)
                    return

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
                if hasattr(self, 'filter_mode') and self.filter_mode:
                    # 在筛选模式下，使用API筛选
                    filter_uid = self.filter_mode.get('uid')
                    result = self.forum_client.get_thread_detail(self.current_forum, self.current_tid, prev_page, uid=filter_uid)
                    self.display_filtered_posts(result.get('postlist', []), result.get('thread_info', {}), result.get('pagination', {}))
                else:
                    # 正常模式
                    result = self.forum_client.get_thread_detail(self.current_forum, self.current_tid, prev_page)
                    self.display_posts(result.get('postlist', []), result.get('pagination', {}), result.get('thread_info', {}))

                # 设置键盘游标到第一项
                wx.CallAfter(self.reset_keyboard_cursor, 0)

        except Exception as e:
            import traceback
            error_detail = f"加载上一页失败: {str(e)}\n{traceback.format_exc()}"
            print(error_detail)  # 控制台输出详细错误
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
            ok_button = wx.Button(button_panel, id=wx.ID_OK, label="确定(&O)")
            cancel_button = wx.Button(button_panel, id=wx.ID_CANCEL, label="取消(&C)")
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

    def jump_to_page(self, target_page):
        """跳转到指定页码"""
        try:
            # 检查是否在筛选模式下
            if hasattr(self, 'filter_mode') and self.filter_mode:
                # 筛选模式下的分页
                uid = self.filter_mode.get('uid')
                tid = self.filter_mode.get('original_tid')
                if uid and tid:
                    self.load_thread_detail_with_filter(tid, uid, page=target_page)
                    return

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
                if hasattr(self, 'filter_mode') and self.filter_mode:
                    # 在筛选模式下，使用API筛选
                    filter_uid = self.filter_mode.get('uid')
                    result = self.forum_client.get_thread_detail(self.current_forum, self.current_tid, target_page, uid=filter_uid)
                    self.display_filtered_posts(result.get('postlist', []), result.get('thread_info', {}), result.get('pagination', {}))
                else:
                    # 正常模式
                    result = self.forum_client.get_thread_detail(self.current_forum, self.current_tid, target_page)
                    self.display_posts(result.get('postlist', []), result.get('pagination', {}), result.get('thread_info', {}))

            # 页面跳转成功后，将焦点移动到列表第一项
            if self.list_ctrl.GetItemCount() > 0:
                # 延迟执行以确保列表已经完全更新
                wx.CallAfter(self.move_focus_to_first_item)

        except Exception as e:
            import traceback
            error_detail = f"页面跳转失败: {str(e)}\n{traceback.format_exc()}"
            print(error_detail)  # 控制台输出详细错误
            wx.MessageBox("页面跳转失败", "错误", wx.OK | wx.ICON_ERROR)

    def move_focus_to_first_item(self):
        """将焦点移动到列表第一项"""
        try:
            if self.list_ctrl.GetItemCount() > 0:
                # 取消所有选择
                self.list_ctrl.UnselectAll()

                # 选择第一项（索引0）
                self.list_ctrl.SelectRow(0)

                # 设置焦点到列表控件
                self.list_ctrl.SetFocus()

                # 重置键盘游标位置到第一项
                self.reset_keyboard_cursor(0)

        except Exception as e:
            pass

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
            add_code_button = wx.Button(button_panel, label="添加代码(&J)")
            ok_button = wx.Button(button_panel, id=wx.ID_OK, label="发送(&S)")
            cancel_button = wx.Button(button_panel, id=wx.ID_CANCEL, label="取消(&C)")
            button_sizer.Add(add_code_button, 0, wx.ALL, 5)
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

            # 绑定添加代码按钮事件
            def on_add_code(event):
                # 打开代码生成对话框
                code_dialog = CodeGeneratorDialog(dialog)
                result = code_dialog.ShowModal()

                if result == wx.ID_OK and code_dialog.generated_code:
                    # 将生成的代码插入到内容编辑框
                    current_content = content_ctrl.GetValue()
                    cursor_pos = content_ctrl.GetInsertionPoint()

                    # 在光标位置插入代码
                    new_content = current_content[:cursor_pos] + code_dialog.generated_code + current_content[cursor_pos:]
                    content_ctrl.SetValue(new_content)

                    # 将光标移动到插入代码的后面
                    content_ctrl.SetInsertionPoint(cursor_pos + len(code_dialog.generated_code))
                    content_ctrl.SetFocus()

                code_dialog.Destroy()

            # 绑定取消按钮事件以确保对话框正确关闭
            def on_cancel(event):
                dialog.EndModal(wx.ID_CANCEL)
                event.Skip()

            def on_dialog_close(event):
                # 重置对话框打开状态
                self._reply_dialog_open = False
                event.Skip()

            add_code_button.Bind(wx.EVT_BUTTON, on_add_code)
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

    def prepare_reply_content(self, text):
        """
        准备回复内容，将每一行用<p>标签包裹

        Args:
            text: 用户输入的文本

        Returns:
            str: 处理后的内容，每一行都用<p>标签包裹
        """
        if not text:
            return ''

        # 按换行符分割文本
        lines = text.split('\n')

        # 将每一行用<p>标签包裹
        wrapped_lines = []
        for line in lines:
            wrapped_lines.append(f'<p>{line}</p>')

        # 将所有行连接起来
        return ''.join(wrapped_lines)

    def post_reply(self, content):
        """发送回复"""
        try:
            if not hasattr(self, 'current_tid') or not self.current_tid:
                return

            # 保存当前页面状态，用于回复后恢复到相同页面
            current_page = getattr(self, 'current_pagination', {}).get('page', 1)
            current_tid = self.current_tid

            # 准备回复内容，转换换行符
            prepared_content = self.prepare_reply_content(content)

            # 获取当前帖子的fid
            if hasattr(self, 'current_thread_info') and self.current_thread_info:
                fid = self.current_thread_info.get('fid')
            else:
                fid = None

            if not fid:
                wx.MessageBox("无法获取帖子信息", "错误", wx.OK | wx.ICON_ERROR)
                return

            result = self.forum_client.post_reply(self.current_forum, fid, current_tid, prepared_content)
            if result.get('success'):
                wx.MessageBox("回复发送成功", "成功", wx.OK | wx.ICON_INFORMATION)
                # 刷新当前页面，并跳转到回复前的页面（不保存状态，避免覆盖之前的列表状态）
                self.load_thread_detail_and_restore_page(current_tid, current_page, save_state=False)
            else:
                error_message = result.get('error', '回复发送失败')
                wx.MessageBox(f"回复发送失败: {error_message}", "错误", wx.OK | wx.ICON_ERROR)

        except Exception as e:
            wx.MessageBox(f"回复发送失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def display_messages(self, messages):
        """显示消息列表（只显示用户名，隐藏消息内容） - DataViewListCtrl版本"""
        self.list_ctrl.DeleteAllItems()
        # 清空数据存储
        self.list_data = []

        # 保存消息列表
        self.current_messages = messages

        # 检查是否需要显示列表序号
        show_list_numbers = self.config_manager.get_show_list_numbers()

        for i, message in enumerate(messages):
            username = message.get('username', '')
            touid = message.get('touid', '')

            # 将对方用户ID转换为整数
            try:
                uid_value = int(touid) if touid else 0
            except (ValueError, TypeError):
                uid_value = 0

            # 构建显示文本
            display_text = username

            # 使用 DataViewListCtrl 的 AppendItem 方法，只显示内容列
            # 将用户ID信息存储在 list_data 数组中
            self.list_ctrl.AppendItem([display_text])

            # 构建存储的数据
            message_data = {
                'type': 'message',
                'touid': uid_value,
                'message_data': message
            }

            self.list_data.append(message_data)

        # 如果需要显示序号，使用重新构建列表的方式
        if show_list_numbers:
            total_items = len(self.list_data)  # 使用list_data的长度，因为已经包含了所有项
            # 清空列表
            self.list_ctrl.DeleteAllItems()
            # 重新构建所有项目，这次包含序号
            for i in range(total_items):
                # 获取存储的数据
                data = self.list_data[i]
                if data['type'] == 'thread':
                    # 帖子项目 - 构建包含序号的显示文本
                    try:
                        thread = self.current_threads[i] if i < len(self.current_threads) else {}
                        subject = thread.get('subject', '')
                        username = thread.get('username', '')
                        views = thread.get('views', 0)
                        forumname = thread.get('forumname', '')
                        dateline_fmt = thread.get('dateline_fmt', '')
                        posts = thread.get('posts', 0)
                        lastpost_fmt = thread.get('lastpost_fmt', '')
                        lastusername = thread.get('lastusername', '')

                        display_text = f"{subject} 作者:{username};浏览:{views};板块:{forumname};发表时间:{dateline_fmt};回复:{posts};回复时间:{lastpost_fmt};最后回复:{lastusername} ，{i+1}之{total_items}项"
                    except:
                        display_text = f"帖子数据加载失败 ，{i+1}之{total_items}项"

                    # 清理多余信息
                    import re
                    display_text = re.sub(r';?\s*数据:\s*\d+\s*', '', display_text)
                    display_text = re.sub(r';?\s*data:\s*\d+\s*', '', display_text, flags=re.IGNORECASE)
                    display_text = re.sub(r';\s*数据:\s*\d+.*$', '', display_text)
                    display_text = re.sub(r';\s*data:\s*\d+.*$', '', display_text, flags=re.IGNORECASE)
                    display_text = re.sub(r'\s+数据:\s*\d+.*$', '', display_text)
                    display_text = re.sub(r'\s+data:\s*\d+.*$', '', display_text, flags=re.IGNORECASE)
                    display_text = re.sub(r';+\s*$', '', display_text)
                    display_text = display_text.strip()

                elif data['type'] == 'post':
                    # 回复项目 - 构建包含序号的显示文本
                    try:
                        post_data = data.get('post_data', {})
                        floor = data.get('floor', i + 1)
                        username = post_data.get('username', '')
                        content = self.clean_html_tags(post_data.get('message', ''))
                        create_date = post_data.get('dateline_fmt', '')

                        if floor == 1:
                            formatted_content = f"楼主 {username} 说\n{content}\n发表时间：{create_date} ，{i+1}之{total_items}项"
                        else:
                            formatted_content = f"{floor}楼 {username} 说\n{content}\n发表时间：{create_date} ，{i+1}之{total_items}项"
                        display_text = formatted_content
                    except:
                        display_text = f"回复数据加载失败 ，{i+1}之{total_items}项"

                elif data['type'] == 'message':
                    # 消息项目 - 构建包含序号的显示文本
                    try:
                        message_data = data.get('message_data', {})
                        username = message_data.get('username', '')
                        display_text = f"{username} ，{i+1}之{total_items}项"
                    except:
                        display_text = f"消息数据加载失败 ，{i+1}之{total_items}项"

                elif data['type'] == 'conversation':
                    # 消息对话项目 - 构建包含序号的显示文本
                    try:
                        message_data = data.get('message_data', {})
                        content = message_data.get('content', '')
                        formatted_content = content

                        if len(formatted_content) > 200:
                            formatted_content = formatted_content[:200] + '...'
                        display_text = f"{formatted_content} ，{i+1}之{total_items}项"
                    except:
                        display_text = f"对话数据加载失败 ，{i+1}之{total_items}项"

                elif data['type'] == 'pagination':
                    # 分页控制项目 - 构建包含序号的显示文本
                    action = data.get('action', '')
                    page = data.get('page', 1)

                    if action == 'prev':
                        display_text = f"上一页({page}) ，{i+1}之{total_items}项"
                    elif action == 'next':
                        display_text = f"下一页({page}) ，{i+1}之{total_items}项"
                    elif action == 'jump':
                        current_page = self.current_pagination.get('page', 1)
                        total_page = self.current_pagination.get('totalpage', 1)
                        display_text = f"当前第{current_page}页共{total_page}页，回车输入页码跳转 ，{i+1}之{total_items}项"
                    elif action == 'reply':
                        display_text = f"回复帖子 ，{i+1}之{total_items}项"
                    else:
                        display_text = f"分页控制 ，{i+1}之{total_items}项"

                    # 清理分页文本
                    import re
                    display_text = re.sub(r';?\s*数据:\s*\d+\s*', '', display_text)
                    display_text = re.sub(r';?\s*data:\s*\d+\s*', '', display_text, flags=re.IGNORECASE)
                    display_text = re.sub(r';\s*数据:\s*\d+.*$', '', display_text)
                    display_text = re.sub(r';\s*data:\s*\d+.*$', '', display_text, flags=re.IGNORECASE)
                    display_text = re.sub(r'\s+数据:\s*\d+.*$', '', display_text)
                    display_text = re.sub(r'\s+data:\s*\d+.*$', '', display_text, flags=re.IGNORECASE)
                    display_text = re.sub(r';+\s*$', '', display_text)
                    display_text = display_text.strip()

                else:
                    # 其他类型的项目
                    display_text = f"项目 ，{i+1}之{total_items}项"

                # 重新添加到列表
                self.list_ctrl.AppendItem([display_text])

                # 在数据中存储序号信息
                data['list_number'] = f"{i+1}之{total_items}项"

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

        # 检查是否需要显示列表序号
        show_list_numbers = self.config_manager.get_show_list_numbers()

        for i, message in enumerate(messages):
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

            # 构建存储的数据
            conversation_data = {
                'type': 'conversation',
                'message_data': message
            }

            self.list_data.append(conversation_data)

        # 如果需要显示序号，使用重新构建列表的方式
        if show_list_numbers:
            total_items = len(self.list_data)  # 使用list_data的长度，因为已经包含了所有项
            # 清空列表
            self.list_ctrl.DeleteAllItems()
            # 重新构建所有项目，这次包含序号
            for i in range(total_items):
                # 获取存储的数据
                data = self.list_data[i]
                if data['type'] == 'thread':
                    # 帖子项目 - 构建包含序号的显示文本
                    try:
                        thread = self.current_threads[i] if i < len(self.current_threads) else {}
                        subject = thread.get('subject', '')
                        username = thread.get('username', '')
                        views = thread.get('views', 0)
                        forumname = thread.get('forumname', '')
                        dateline_fmt = thread.get('dateline_fmt', '')
                        posts = thread.get('posts', 0)
                        lastpost_fmt = thread.get('lastpost_fmt', '')
                        lastusername = thread.get('lastusername', '')

                        display_text = f"{subject} 作者:{username};浏览:{views};板块:{forumname};发表时间:{dateline_fmt};回复:{posts};回复时间:{lastpost_fmt};最后回复:{lastusername} ，{i+1}之{total_items}项"
                    except:
                        display_text = f"帖子数据加载失败 ，{i+1}之{total_items}项"

                    # 清理多余信息
                    import re
                    display_text = re.sub(r';?\s*数据:\s*\d+\s*', '', display_text)
                    display_text = re.sub(r';?\s*data:\s*\d+\s*', '', display_text, flags=re.IGNORECASE)
                    display_text = re.sub(r';\s*数据:\s*\d+.*$', '', display_text)
                    display_text = re.sub(r';\s*data:\s*\d+.*$', '', display_text, flags=re.IGNORECASE)
                    display_text = re.sub(r'\s+数据:\s*\d+.*$', '', display_text)
                    display_text = re.sub(r'\s+data:\s*\d+.*$', '', display_text, flags=re.IGNORECASE)
                    display_text = re.sub(r';+\s*$', '', display_text)
                    display_text = display_text.strip()

                elif data['type'] == 'post':
                    # 回复项目 - 构建包含序号的显示文本
                    try:
                        post_data = data.get('post_data', {})
                        floor = data.get('floor', i + 1)
                        username = post_data.get('username', '')
                        content = self.clean_html_tags(post_data.get('message', ''))
                        create_date = post_data.get('dateline_fmt', '')

                        if floor == 1:
                            formatted_content = f"楼主 {username} 说\n{content}\n发表时间：{create_date} ，{i+1}之{total_items}项"
                        else:
                            formatted_content = f"{floor}楼 {username} 说\n{content}\n发表时间：{create_date} ，{i+1}之{total_items}项"
                        display_text = formatted_content
                    except:
                        display_text = f"回复数据加载失败 ，{i+1}之{total_items}项"

                elif data['type'] == 'message':
                    # 消息项目 - 构建包含序号的显示文本
                    try:
                        message_data = data.get('message_data', {})
                        username = message_data.get('username', '')
                        display_text = f"{username} ，{i+1}之{total_items}项"
                    except:
                        display_text = f"消息数据加载失败 ，{i+1}之{total_items}项"

                elif data['type'] == 'conversation':
                    # 消息对话项目 - 构建包含序号的显示文本
                    try:
                        message_data = data.get('message_data', {})
                        content = message_data.get('content', '')
                        formatted_content = content

                        if len(formatted_content) > 200:
                            formatted_content = formatted_content[:200] + '...'
                        display_text = f"{formatted_content} ，{i+1}之{total_items}项"
                    except:
                        display_text = f"对话数据加载失败 ，{i+1}之{total_items}项"

                elif data['type'] == 'pagination':
                    # 分页控制项目 - 构建包含序号的显示文本
                    action = data.get('action', '')
                    page = data.get('page', 1)

                    if action == 'prev':
                        display_text = f"上一页({page}) ，{i+1}之{total_items}项"
                    elif action == 'next':
                        display_text = f"下一页({page}) ，{i+1}之{total_items}项"
                    elif action == 'jump':
                        current_page = self.current_pagination.get('page', 1)
                        total_page = self.current_pagination.get('totalpage', 1)
                        display_text = f"当前第{current_page}页共{total_page}页，回车输入页码跳转 ，{i+1}之{total_items}项"
                    elif action == 'reply':
                        display_text = f"回复帖子 ，{i+1}之{total_items}项"
                    else:
                        display_text = f"分页控制 ，{i+1}之{total_items}项"

                    # 清理分页文本
                    import re
                    display_text = re.sub(r';?\s*数据:\s*\d+\s*', '', display_text)
                    display_text = re.sub(r';?\s*data:\s*\d+\s*', '', display_text, flags=re.IGNORECASE)
                    display_text = re.sub(r';\s*数据:\s*\d+.*$', '', display_text)
                    display_text = re.sub(r';\s*data:\s*\d+.*$', '', display_text, flags=re.IGNORECASE)
                    display_text = re.sub(r'\s+数据:\s*\d+.*$', '', display_text)
                    display_text = re.sub(r'\s+data:\s*\d+.*$', '', display_text, flags=re.IGNORECASE)
                    display_text = re.sub(r';+\s*$', '', display_text)
                    display_text = display_text.strip()

                else:
                    # 其他类型的项目
                    display_text = f"项目 ，{i+1}之{total_items}项"

                # 重新添加到列表
                self.list_ctrl.AppendItem([display_text])

                # 在数据中存储序号信息
                data['list_number'] = f"{i+1}之{total_items}项"

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
            wx.MessageBox("消息发送失败", "错误", wx.OK | wx.ICON_ERROR)

    def parse_floor_content_and_extract_resources(self, html_content):
        """
        解析楼层HTML内容，提取资源并生成清理后的文本
        返回: (清理后的文本, 资源列表, 资源位置映射)

        Args:
            html_content: 包含HTML标签的楼层内容

        Returns:
            tuple: (清理后的文本, 资源列表, 资源位置映射字典)
        """
        if not html_content:
            return '', [], {}

        try:
            # 资源列表和位置映射
            resources = []
            resource_map = {}

            # 统一的资源名称生成函数
            def generate_fallback_name(url, resource_type):
                """为资源生成备用名称"""
                try:
                    if not url:
                        return f'未命名{resource_type}'

                    # 从URL中提取文件名
                    if '/' in url:
                        filename = url.split('/')[-1]
                        if '?' in filename:  # 移除查询参数
                            filename = filename.split('?')[0]
                        if '#' in filename:  # 移除锚点
                            filename = filename.split('#')[0]
                        if filename:  # 如果有文件名
                            # 移除文件扩展名
                            if '.' in filename and resource_type != '链接':
                                name_without_ext = filename.split('.')[0]
                                return name_without_ext or f'未命名{resource_type}'
                            return filename
                        else:  # 如果URL以/结尾
                            path_parts = url.strip('/').split('/')
                            return path_parts[-1] if path_parts else f'未命名{resource_type}'
                    else:
                        return url or f'未命名{resource_type}'
                except Exception:
                    return f'未命名{resource_type}'

            # 处理换行相关的HTML标签
            # 将<br>、<br/>、<br />等替换为换行符
            clean_text = re.sub(r'<br\s*/?>', '\n', html_content, flags=re.IGNORECASE)

            # 只对结束标签替换为换行符，避免重复换行
            clean_text = re.sub(r'</(p|div|h[1-6]|blockquote|li|tr|td|th)>', '\n', clean_text, flags=re.IGNORECASE)

            # 移除开始标签（不添加换行符）
            clean_text = re.sub(r'<(?!/)(p|div|h[1-6]|blockquote|li|tr|td|th)[^>]*>', '', clean_text, flags=re.IGNORECASE)

            # 提取链接资源 <a href="url">text</a>
            def extract_link(match):
                try:
                    groups = match.groups()
                    url = groups[0] if groups[0] else ''
                    text = groups[1].strip() if len(groups) > 1 and groups[1] else ''

                    # 如果链接文字为空或只有空白字符，使用备用名称
                    if not text:
                        text = generate_fallback_name(url, '链接')

                    resource_name = f"{text}【链接】"
                    resource_info = {
                        'name': text,
                        'type': 'link',
                        'url': url,
                        'display_name': resource_name
                    }
                    resources.append(resource_info)
                    return resource_name
                except Exception:
                    return match.group(0) if match else ""

            # 提取音频资源 <audio controls src="url" title="title"></audio>
            def extract_audio(match):
                try:
                    groups = match.groups()

                    # 安全地获取src和title，处理不同的匹配模式
                    if len(groups) >= 2:
                        # 模式1和模式2：有两个捕获组 (src, title) 或 (title, src)
                        src = groups[0] if groups[0] else groups[1]
                        title = groups[1] if groups[1] else groups[0]
                    else:
                        # 模式3：只有一个捕获组 (src)
                        src = groups[0] if groups[0] else ''
                        title = None

                    # 如果没有title或title为空，使用备用名称
                    if not title:
                        title = generate_fallback_name(src, '音频')

                    resource_name = f"{title}【音频】"
                    resource_info = {
                        'name': title,
                        'type': 'audio',
                        'url': src,
                        'display_name': resource_name
                    }
                    resources.append(resource_info)
                    return resource_name
                except Exception:
                    return match.group(0) if match else ""

            # 提取图片资源 <img alt="alt" src="src"> 或 <img src="src" alt="alt">
            def extract_image(match):
                try:
                    groups = match.groups()

                    # 安全地获取src和alt，处理不同的匹配模式
                    if len(groups) >= 2:
                        # 模式1和模式2：有两个捕获组 (alt, src) 或 (src, alt)
                        src = groups[0] if groups[0] else groups[1]
                        alt = groups[1] if groups[1] else groups[0]
                    else:
                        # 模式3：只有一个捕获组 (src)
                        src = groups[0] if groups[0] else ''
                        alt = None

                    # 如果没有alt或alt为空，使用备用名称
                    if not alt:
                        alt = generate_fallback_name(src, '图片')

                    resource_name = f"{alt}【图片】"
                    resource_info = {
                        'name': alt,
                        'type': 'image',
                        'url': src,
                        'display_name': resource_name
                    }
                    resources.append(resource_info)
                    return resource_name
                except Exception:
                    return match.group(0) if match else ""

          # 提取链接
            # 改进的链接正则表达式，确保文字组总是存在（即使是空的）
            link_pattern = r'<a\s+[^>]*href\s*=\s*["\']([^"\']+)["\'][^>]*>([^<]*)</a>'
            clean_text = re.sub(link_pattern, extract_link, clean_text, flags=re.IGNORECASE)

            # 提取音频（处理三种常见格式）
            # 第一种格式：src在前，title在后
            pattern1 = r'<audio\s+[^>]*src\s*=\s*["\']([^"\']+)["\'][^>]*title\s*=\s*["\']([^"\']+)["\'][^>]*>.*?</audio>'
            clean_text = re.sub(pattern1, extract_audio, clean_text, flags=re.IGNORECASE | re.DOTALL)

            # 第二种格式：title在前，src在后
            pattern2 = r'<audio\s+[^>]*title\s*=\s*["\']([^"\']+)["\'][^>]*src\s*=\s*["\']([^"\']+)["\'][^>]*>.*?</audio>'
            clean_text = re.sub(pattern2, extract_audio, clean_text, flags=re.IGNORECASE | re.DOTALL)

            # 第三种格式：只有src
            pattern3 = r'<audio\s+[^>]*src\s*=\s*["\']([^"\']+)["\'][^>]*>.*?</audio>'
            clean_text = re.sub(pattern3, lambda m: extract_audio(m), clean_text, flags=re.IGNORECASE | re.DOTALL)

            # 提取图片（处理三种常见格式）
            # 第一种格式：alt在前，src在后
            img_pattern1 = r'<img\s+[^>]*alt\s*=\s*["\']([^"\']*)["\'][^>]*src\s*=\s*["\']([^"\']+)["\'][^>]*>'
            clean_text = re.sub(img_pattern1, extract_image, clean_text, flags=re.IGNORECASE)

            # 第二种格式：src在前，alt在后
            img_pattern2 = r'<img\s+[^>]*src\s*=\s*["\']([^"\']+)["\'][^>]*alt\s*=\s*["\']([^"\']*)["\'][^>]*>'
            clean_text = re.sub(img_pattern2, extract_image, clean_text, flags=re.IGNORECASE)

            # 第三种格式：只有src
            img_pattern3 = r'<img\s+[^>]*src\s*=\s*["\']([^"\']+)["\'][^>]*>'
            clean_text = re.sub(img_pattern3, lambda m: extract_image(m), clean_text, flags=re.IGNORECASE)

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
                '&lsquo;': ''',
                '&rsquo;': ''',
                '&ldquo;': '"',
                '&rdquo;': '"',
                '&euro;': '€',
                '&pound;': '£',
                '&yen;': '¥'
            }

            for entity, char in html_entities.items():
                clean_text = clean_text.replace(entity, char)

            # 建立资源位置映射
            current_pos = 0
            for i, resource in enumerate(resources):
                resource_name = resource['display_name']
                pos = clean_text.find(resource_name, current_pos)
                if pos != -1:
                    resource_map[pos] = resource
                    current_pos = pos + len(resource_name)

            # 清理多余的空行和空格
            # 将多个连续换行符合并为单个换行符
            clean_text = re.sub(r'\n+', '\n', clean_text)

            # 清理首尾空白
            clean_text = clean_text.strip()

            return clean_text, resources, resource_map

        except Exception as e:
            # 如果整个解析过程失败，返回基础的HTML清理结果
            print(f"[DEBUG] HTML解析整体失败，使用基础清理: {e}")
            clean_text = self.clean_html_tags(html_content)
            return clean_text, [], {}

    def find_resource_near_cursor(self, text, cursor_pos, resources):
        """
        基于改进的位置和关键词检测光标附近的资源

        Args:
            text: 文本框中的完整文本
            cursor_pos: 光标位置
            resources: 资源列表

        Returns:
            dict or None: 找到的资源信息，如果没找到返回None
        """
        if not text or not resources:
            return None

        # 缩小检测范围：光标位置前后各20个字符（原来是50）
        search_range = 20
        start_pos = max(0, cursor_pos - search_range)
        end_pos = min(len(text), cursor_pos + search_range)
        context_text = text[start_pos:end_pos]

        # 使用正则表达式匹配资源标记
        resource_pattern = r'([^\【\】\n\r，。！？；：""''（）《》【】]+)\【(链接|音频|图片)\】'

        # 在上下文中查找所有匹配的资源标记
        matches = list(re.finditer(resource_pattern, context_text))

        if not matches:
            return None

        # 如果只有一个匹配，直接返回
        if len(matches) == 1:
            match = matches[0]
            resource_name = match.group(1).strip()
            resource_type = match.group(2)
        else:
            # 多个匹配时，选择距离光标最近的
            closest_match = None
            min_distance = float('inf')

            for match in matches:
                # 计算匹配在原文中的位置
                match_start_in_context = match.start()
                match_start_in_text = start_pos + match_start_in_context

                # 计算距离光标的距离
                distance = abs(match_start_in_text - cursor_pos)

                if distance < min_distance:
                    min_distance = distance
                    closest_match = match

            if closest_match:
                resource_name = closest_match.group(1).strip()
                resource_type = closest_match.group(2)
            else:
                return None

        # 将中文类型转换为英文
        type_mapping = {'链接': 'link', '音频': 'audio', '图片': 'image'}
        resource_type_en = type_mapping.get(resource_type, 'unknown')

        # 在资源列表中查找匹配的资源
        for resource in resources:
            if (resource['name'] == resource_name and
                resource['type'] == resource_type_en):
                return resource

        return None

    def open_resource(self, resource):
        """
        打开资源文件

        Args:
            resource: 资源信息字典，包含类型和URL
        """
        # 添加状态标记防止重复打开
        if hasattr(self, '_opening_resource') and self._opening_resource:
            return

        try:
            self._opening_resource = True

            url = resource['url']
            resource_type = resource['type']

            if resource_type == 'link':
                # 链接使用浏览器打开
                webbrowser.open(url)
            elif resource_type == 'audio':
                # 音频使用系统默认播放器打开
                webbrowser.open(url)
            elif resource_type == 'image':
                # 图片使用系统默认查看器打开
                webbrowser.open(url)
            else:
                # 其他类型也尝试用浏览器打开
                webbrowser.open(url)

        except Exception as e:
            try:
                wx.MessageBox(f"无法打开资源 {resource['name']}：{str(e)}",
                            "错误", wx.OK | wx.ICON_ERROR)
            except:
                pass
        finally:
            # 清除状态标记
            self._opening_resource = False

    def show_floor_editor(self, floor_index):
        """显示楼层内容浏览框（增强版：支持资源显示和交互）"""
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

            # 解析HTML内容并提取资源（带异常处理）
            try:
                clean_text, resources, resource_map = self.parse_floor_content_and_extract_resources(original_content)
            except Exception as e:
                # 如果解析失败，使用基础的HTML清理
                print(f"[DEBUG] HTML解析失败，使用基础清理: {e}")
                clean_text = self.clean_html_tags(original_content)
                resources = []
                resource_map = {}

            # 设置对话框状态为打开
            self._floor_dialog_open = True

                      # 创建浏览对话框 - 增大尺寸以容纳资源列表
            dialog = wx.Dialog(self, title=f"浏览{floor}楼 - {username}", size=(700, 500))

            # 创建主sizer用于dialog
            main_sizer = wx.BoxSizer(wx.VERTICAL)

            panel = wx.Panel(dialog)
            sizer = wx.BoxSizer(wx.VERTICAL)

            # 楼层信息（只读）
            info_label = wx.StaticText(panel, label=f"{floor}楼 {username} 的内容:")
            sizer.Add(info_label, 0, wx.ALL | wx.EXPAND, 5)

            # 内容显示框（只读，不自动换行）- 使用清理后的文本
            content_ctrl = wx.TextCtrl(panel, value=clean_text, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP)
            sizer.Add(content_ctrl, 1, wx.ALL | wx.EXPAND, 5)

            # 资源列表（如果有资源）
            resource_list_ctrl = None
            if resources:
                # 资源列表标题
                resource_label = wx.StaticText(panel, label="资源:")
                sizer.Add(resource_label, 0, wx.ALL | wx.EXPAND, 5)

                # 创建资源列表
                resource_list_ctrl = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
                resource_list_ctrl.InsertColumn(0, "序号", width=50)
                resource_list_ctrl.InsertColumn(1, "资源名称", width=300)
                resource_list_ctrl.InsertColumn(2, "类型", width=80)

                # 添加资源数据
                resource_data = []
                for i, resource in enumerate(resources):
                    type_text = {'link': '链接', 'audio': '音频', 'image': '图片'}.get(resource['type'], '其他')
                    index = resource_list_ctrl.InsertItem(i, str(i+1))
                    resource_list_ctrl.SetItem(index, 1, resource['name'])
                    resource_list_ctrl.SetItem(index, 2, type_text)
                    resource_data.append(resource)

                sizer.Add(resource_list_ctrl, 0, wx.ALL | wx.EXPAND, 5)

            # 按钮面板
            button_panel = wx.Panel(panel)
            button_sizer = wx.BoxSizer(wx.HORIZONTAL)
            close_button = wx.Button(button_panel, id=wx.ID_CANCEL, label="关闭(&C)")
            button_sizer.Add(close_button, 0, wx.ALL, 5)
            button_panel.SetSizer(button_sizer)
            sizer.Add(button_panel, 0, wx.ALL | wx.ALIGN_CENTER, 5)

            panel.SetSizer(sizer)
            main_sizer.Add(panel, 1, wx.EXPAND)
            dialog.SetSizerAndFit(main_sizer)

            # 绑定键盘事件
            def on_content_key_down(event):
                keycode = event.GetKeyCode()

                if keycode == wx.WXK_ESCAPE or keycode == wx.WXK_BACK:
                    dialog.EndModal(wx.ID_CANCEL)
                    return

                if keycode == wx.WXK_RETURN:
                    # 基于关键词检测资源（方案A）
                    cursor_pos = content_ctrl.GetInsertionPoint()
                    full_text = content_ctrl.GetValue()

                    # 改进的精确位置匹配逻辑
                    # 1. 首先尝试精确位置匹配
                    if cursor_pos in resource_map:
                        resource = resource_map[cursor_pos]
                        self.open_resource(resource)
                        return

                    # 2. 如果没有精确匹配，尝试查找附近的位置
                    # 找到距离光标最近的资源位置
                    nearest_pos = None
                    min_distance = float('inf')
                    nearest_resource = None

                    for pos, resource in resource_map.items():
                        distance = abs(pos - cursor_pos)
                        if distance < min_distance:
                            min_distance = distance
                            nearest_pos = pos
                            nearest_resource = resource

                    # 如果最近的资源在合理范围内（10个字符内），使用它
                    if nearest_resource is not None and min_distance <= 10:
                        self.open_resource(nearest_resource)
                        return

                    # 3. 如果位置匹配失败，使用改进的关键词检测
                    found_resource = self.find_resource_near_cursor(full_text, cursor_pos, resources)
                    if found_resource:
                        self.open_resource(found_resource)
                        return
                    return

                if keycode == wx.WXK_TAB:
                    # Tab键切换到资源列表（如果存在）
                    if resource_list_ctrl:
                        resource_list_ctrl.SetFocus()
                    return

                event.Skip()

            def on_resource_key_down(event):
                keycode = event.GetKeyCode()

                if keycode == wx.WXK_ESCAPE or keycode == wx.WXK_BACK:
                    dialog.EndModal(wx.ID_CANCEL)
                    return

                if keycode == wx.WXK_RETURN:
                    # 激活选中的资源
                    selected_index = resource_list_ctrl.GetFirstSelected()
                    if selected_index >= 0 and selected_index < len(resource_data):
                        resource = resource_data[selected_index]
                        self.open_resource(resource)
                    return

                if keycode == wx.WXK_TAB:
                    # Tab键切换到内容框
                    content_ctrl.SetFocus()
                    return

                event.Skip()

            # 资源列表双击激活事件
            def on_resource_activated(event):
                selected_index = resource_list_ctrl.GetFirstSelected()
                if selected_index >= 0 and selected_index < len(resource_data):
                    resource = resource_data[selected_index]
                    self.open_resource(resource)

            # 对话框关闭事件处理
            def on_dialog_close(event):
                self._floor_dialog_open = False
                event.Skip()

            # 按钮事件处理
            def on_close_button(event):
                dialog.EndModal(wx.ID_CANCEL)

            # 资源列表上下文菜单处理
            def on_resource_context_menu(event):
                """处理资源列表右键菜单"""
                if not resource_list_ctrl or not resource_data:
                    event.Skip()
                    return

                # 获取点击位置的项目索引
                pos = event.GetPosition()
                item_index, flags = resource_list_ctrl.HitTest(pos)

                if item_index >= 0 and item_index < len(resource_data):
                    # 选中该项目
                    resource_list_ctrl.Select(item_index)

                    # 创建上下文菜单
                    menu = wx.Menu()

                    # 添加菜单项
                    copy_title_item = menu.Append(wx.ID_ANY, "拷贝标题(&C)\tCtrl+C")
                    copy_url_item = menu.Append(wx.ID_ANY, "拷贝地址(&D)\tCtrl+D")

                    # 绑定菜单事件
                    def on_copy_title(menu_event):
                        if item_index >= 0 and item_index < len(resource_data):
                            resource = resource_data[item_index]
                            title = resource['name']
                            self.copy_to_clipboard(title)

                    def on_copy_url(menu_event):
                        if item_index >= 0 and item_index < len(resource_data):
                            resource = resource_data[item_index]
                            url = resource['url']
                            self.copy_to_clipboard(url)

                    # 绑定事件处理器
                    dialog.Bind(wx.EVT_MENU, on_copy_title, copy_title_item)
                    dialog.Bind(wx.EVT_MENU, on_copy_url, copy_url_item)

                    # 显示菜单
                    resource_list_ctrl.PopupMenu(menu, pos)
                    menu.Destroy()
                else:
                    event.Skip()

            # 资源列表键盘快捷键处理
            def on_resource_key_down_with_shortcuts(event):
                """处理资源列表键盘事件，包括快捷键"""
                keycode = event.GetKeyCode()

                # 添加调试信息（可以移除）
                # print(f"资源列表键盘事件: {keycode}, Ctrl: {event.ControlDown()}")

                if keycode == wx.WXK_ESCAPE or keycode == wx.WXK_BACK:
                    dialog.EndModal(wx.ID_CANCEL)
                    return

                # Ctrl+C: 拷贝标题
                if event.ControlDown() and keycode == ord('C'):
                    selected_index = resource_list_ctrl.GetFirstSelected()
                    if selected_index >= 0 and selected_index < len(resource_data):
                        resource = resource_data[selected_index]
                        title = resource['name']
                        self.copy_to_clipboard(title)
                    return

                # Ctrl+D: 拷贝地址
                if event.ControlDown() and keycode == ord('D'):
                    selected_index = resource_list_ctrl.GetFirstSelected()
                    if selected_index >= 0 and selected_index < len(resource_data):
                        resource = resource_data[selected_index]
                        url = resource['url']
                        self.copy_to_clipboard(url)
                    return

                # Application Key (上下文菜单键): 触发上下文菜单
                if keycode == wx.WXK_WINDOWS_MENU:
                    # 检查是否有选中的资源
                    selected_index = resource_list_ctrl.GetFirstSelected()
                    if selected_index < 0:
                        # 如果没有选中任何项目，选中第一个
                        if resource_data:
                            selected_index = 0
                            resource_list_ctrl.Select(selected_index)

                    if selected_index >= 0 and selected_index < len(resource_data):
                        # 创建上下文菜单
                        menu = wx.Menu()

                        # 添加菜单项
                        copy_title_item = menu.Append(wx.ID_ANY, "拷贝标题(&C)\tCtrl+C")
                        copy_url_item = menu.Append(wx.ID_ANY, "拷贝地址(&D)\tCtrl+D")

                        # 绑定菜单事件
                        def on_copy_title(menu_event):
                            if selected_index >= 0 and selected_index < len(resource_data):
                                resource = resource_data[selected_index]
                                title = resource['name']
                                self.copy_to_clipboard(title)

                        def on_copy_url(menu_event):
                            if selected_index >= 0 and selected_index < len(resource_data):
                                resource = resource_data[selected_index]
                                url = resource['url']
                                self.copy_to_clipboard(url)

                        # 绑定事件处理器
                        dialog.Bind(wx.EVT_MENU, on_copy_title, copy_title_item)
                        dialog.Bind(wx.EVT_MENU, on_copy_url, copy_url_item)

                        # 获取选中项目的显示位置
                        item_rect = resource_list_ctrl.GetItemRect(selected_index)
                        menu_pos = item_rect.GetBottomLeft()
                        menu_pos.y += 5  # 稍微向下偏移

                        # 显示菜单
                        resource_list_ctrl.PopupMenu(menu, menu_pos)
                        menu.Destroy()
                    return

                if keycode == wx.WXK_RETURN:
                    # 激活选中的资源
                    selected_index = resource_list_ctrl.GetFirstSelected()
                    if selected_index >= 0 and selected_index < len(resource_data):
                        resource = resource_data[selected_index]
                        # 使用wx.CallAfter延迟执行，避免与列表激活事件冲突
                        wx.CallAfter(self.open_resource, resource)
                    return

                if keycode == wx.WXK_TAB:
                    # Tab键切换到内容框
                    content_ctrl.SetFocus()
                    return

                event.Skip()

            # 资源列表右键事件处理（备选方案）
            def on_resource_right_click(event):
                """处理资源列表右键点击事件"""
                if not resource_list_ctrl or not resource_data:
                    event.Skip()
                    return

                # 获取点击位置的项目索引
                pos = event.GetPosition()
                item_index, flags = resource_list_ctrl.HitTest(pos)

                if item_index >= 0 and item_index < len(resource_data):
                    # 选中该项目
                    resource_list_ctrl.Select(item_index)

                    # 创建上下文菜单
                    menu = wx.Menu()

                    # 添加菜单项
                    copy_title_item = menu.Append(wx.ID_ANY, "拷贝标题(&C)\tCtrl+C")
                    copy_url_item = menu.Append(wx.ID_ANY, "拷贝地址(&D)\tCtrl+D")

                    # 绑定菜单事件
                    def on_copy_title(menu_event):
                        if item_index >= 0 and item_index < len(resource_data):
                            resource = resource_data[item_index]
                            title = resource['name']
                            self.copy_to_clipboard(title)

                    def on_copy_url(menu_event):
                        if item_index >= 0 and item_index < len(resource_data):
                            resource = resource_data[item_index]
                            url = resource['url']
                            self.copy_to_clipboard(url)

                    # 绑定事件处理器
                    dialog.Bind(wx.EVT_MENU, on_copy_title, copy_title_item)
                    dialog.Bind(wx.EVT_MENU, on_copy_url, copy_url_item)

                    # 显示菜单
                    resource_list_ctrl.PopupMenu(menu, pos)
                    menu.Destroy()
                else:
                    event.Skip()

            # 绑定事件
            content_ctrl.Bind(wx.EVT_CHAR, on_content_key_down)
            if resource_list_ctrl:
                resource_list_ctrl.Bind(wx.EVT_CHAR, on_resource_key_down_with_shortcuts)
                resource_list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, on_resource_activated)
                resource_list_ctrl.Bind(wx.EVT_CONTEXT_MENU, on_resource_context_menu)
                resource_list_ctrl.Bind(wx.EVT_RIGHT_UP, on_resource_right_click)  # 添加右键事件
            close_button.Bind(wx.EVT_BUTTON, on_close_button)
            dialog.Bind(wx.EVT_CLOSE, on_dialog_close)

            # 创建加速器表来处理快捷键
            if resource_list_ctrl and resource_data:
                # 创建加速器条目
                accel_entries = [
                    wx.AcceleratorEntry(wx.ACCEL_CTRL, ord('C'), 1001),  # Ctrl+C: 拷贝标题
                    wx.AcceleratorEntry(wx.ACCEL_CTRL, ord('D'), 1002),  # Ctrl+D: 拷贝地址
                ]
                accel_table = wx.AcceleratorTable(accel_entries)
                dialog.SetAcceleratorTable(accel_table)

                # 绑定加速器事件
                def on_accelerator(event):
                    """处理加速器事件"""
                    accel_id = event.GetId()

                    if accel_id == 1001:  # Ctrl+C: 拷贝标题
                        selected_index = resource_list_ctrl.GetFirstSelected()
                        if selected_index >= 0 and selected_index < len(resource_data):
                            resource = resource_data[selected_index]
                            title = resource['name']
                            self.copy_to_clipboard(title)
                        return

                    elif accel_id == 1002:  # Ctrl+D: 拷贝地址
                        selected_index = resource_list_ctrl.GetFirstSelected()
                        if selected_index >= 0 and selected_index < len(resource_data):
                            resource = resource_data[selected_index]
                            url = resource['url']
                            self.copy_to_clipboard(url)
                        return

                    event.Skip()

                dialog.Bind(wx.EVT_MENU, on_accelerator)

            # 使用wx.CallAfter设置焦点到内容框
            wx.CallAfter(content_ctrl.SetFocus)

            try:
                # 显示对话框
                dialog.ShowModal()
            except Exception as dialog_error:
                pass
            finally:
                # 确保状态被重置
                self._floor_dialog_open = False
                dialog.Destroy()

        except Exception as e:
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
            pass

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

    # =========================================================================
    # 帖子详情右键菜单增强功能的辅助方法
    # =========================================================================

    def should_show_edit_menu(self, post_data):
        """判断是否应该显示编辑菜单"""
        try:
            # 检查是否登录
            if not self.auth_manager.is_logged_in():
                return False

            # 获取当前登录用户ID
            current_user_id = self.auth_manager.get_current_user_id()
            if not current_user_id:
                return False

            # 获取帖子作者ID - 兼容不同字段名称
            post_user_id = post_data.get('uid') or post_data.get('authorid') or post_data.get('author_id')
            if not post_user_id:
                return False

            # 判断是否是自己的帖子
            return str(current_user_id) == str(post_user_id)

        except Exception:
            return False

    def is_thread_author(self, post_data):
        """判断是否是楼主"""
        try:
            # 楼主的floor通常为1，或者检查是否是帖子的第一个回复
            floor = post_data.get('floor', 0)
            return floor == 1
        except Exception:
            return False

    def on_refresh_thread_detail(self):
        """刷新帖子详情"""
        try:
            if hasattr(self, 'current_tid') and self.current_tid:
                # 重新加载帖子详情
                if hasattr(self, 'current_thread_info') and self.current_thread_info:
                    tid = self.current_thread_info.get('tid')
                    if tid:
                        # 如果处于筛选模式，保持筛选状态
                        if hasattr(self, 'filter_mode') and self.filter_mode:
                            filter_uid = self.filter_mode.get('uid')
                            if filter_uid:
                                self.load_thread_detail_with_filter(tid, filter_uid)
                        else:
                            self.load_thread_detail(tid)

                # 恢复焦点到第一项
                wx.CallAfter(self.reset_keyboard_cursor, 0)
        except Exception as e:
            wx.MessageBox("刷新失败", "错误", wx.OK | wx.ICON_ERROR)

    def on_reply_to_floor(self, post_data):
        """回复特定楼层"""
        try:
            # 获取当前帖子的必要信息
            pid = post_data.get('pid')
            username = post_data.get('author', post_data.get('username', '用户'))
            if not hasattr(self, 'current_thread_info') or not self.current_thread_info:
                wx.MessageBox("无法获取帖子信息", "错误", wx.OK | wx.ICON_ERROR)
                return

            fid = self.current_thread_info.get('fid')
            tid = self.current_thread_info.get('tid')

            if not fid or not tid:
                wx.MessageBox("无法获取帖子信息", "错误", wx.OK | wx.ICON_ERROR)
                return

            # 设置回复目标
            self.reply_target = {
                'fid': fid,
                'tid': tid,
                'pid': pid,
                'username': username
            }

            # 显示回复对话框，预填充引用内容
            self.show_reply_dialog_with_quote(username)

        except Exception as e:
            wx.MessageBox(f"设置回复目标失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def show_reply_dialog_with_quote(self, username):
        """显示带引用的回复对话框"""
        try:
            # 防止重复打开对话框
            if hasattr(self, '_reply_dialog_open') and self._reply_dialog_open:
                return

            if not hasattr(self, 'reply_target') or not self.reply_target:
                wx.MessageBox("请先选择要回复的楼层", "提示", wx.OK | wx.ICON_INFORMATION)
                return

            # 标记对话框为打开状态
            self._reply_dialog_open = True

            # 创建回复对话框
            dialog = wx.Dialog(self, title=f"回复{username}", size=(500, 350))
            dialog.SetExtraStyle(wx.WS_EX_CONTEXTHELP)

            panel = wx.Panel(dialog)
            sizer = wx.BoxSizer(wx.VERTICAL)

            # 回复对象信息（只读）
            target_label = wx.StaticText(panel, label=f"回复对象: {username}")
            sizer.Add(target_label, 0, wx.ALL | wx.EXPAND, 5)

            # 引用内容预填充（只读）
            quote_text = f"引用 {username} 的回复："
            quote_ctrl = wx.TextCtrl(panel, value=quote_text, style=wx.TE_READONLY)
            sizer.Add(quote_ctrl, 0, wx.ALL | wx.EXPAND, 5)

            # 内容输入框
            content_label = wx.StaticText(panel, label="回复内容:")
            content_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER)
            sizer.Add(content_label, 0, wx.ALL | wx.EXPAND, 5)
            sizer.Add(content_ctrl, 1, wx.ALL | wx.EXPAND, 5)

            # 按钮面板
            button_panel = wx.Panel(panel)
            button_sizer = wx.BoxSizer(wx.HORIZONTAL)
            add_code_button = wx.Button(button_panel, label="添加代码(&J)")
            ok_button = wx.Button(button_panel, id=wx.ID_OK, label="发送(&S)")
            cancel_button = wx.Button(button_panel, id=wx.ID_CANCEL, label="取消(&C)")
            button_sizer.Add(add_code_button, 0, wx.ALL, 5)
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

            # 绑定添加代码按钮事件
            def on_add_code(event):
                # 打开代码生成对话框
                code_dialog = CodeGeneratorDialog(dialog)
                result = code_dialog.ShowModal()

                if result == wx.ID_OK and code_dialog.generated_code:
                    # 将生成的代码插入到内容编辑框
                    current_content = content_ctrl.GetValue()
                    cursor_pos = content_ctrl.GetInsertionPoint()

                    # 在光标位置插入代码
                    new_content = current_content[:cursor_pos] + code_dialog.generated_code + current_content[cursor_pos:]
                    content_ctrl.SetValue(new_content)

                    # 将光标移动到插入代码的后面
                    content_ctrl.SetInsertionPoint(cursor_pos + len(code_dialog.generated_code))
                    content_ctrl.SetFocus()

                code_dialog.Destroy()

            # 绑定取消按钮事件以确保对话框正确关闭
            def on_cancel(event):
                dialog.EndModal(wx.ID_CANCEL)
                event.Skip()

            def on_dialog_close(event):
                # 重置对话框打开状态
                self._reply_dialog_open = False
                event.Skip()

            add_code_button.Bind(wx.EVT_BUTTON, on_add_code)
            cancel_button.Bind(wx.EVT_BUTTON, on_cancel)
            dialog.Bind(wx.EVT_CLOSE, on_dialog_close)

            # 显示对话框
            result = dialog.ShowModal()
            # 重置对话框打开状态
            self._reply_dialog_open = False

            if result == wx.ID_OK:
                content = content_ctrl.GetValue().strip()
                if content:
                    self.send_floor_reply(content)
                else:
                    wx.MessageBox("回复内容不能为空", "提示", wx.OK | wx.ICON_WARNING)

            dialog.Destroy()

        except Exception as e:
            # 确保在异常情况下也重置状态
            self._reply_dialog_open = False

    def send_floor_reply(self, content):
        """发送楼层回复"""
        try:
            if not hasattr(self, 'reply_target') or not self.reply_target:
                wx.MessageBox("请先选择要回复的楼层", "提示", wx.OK | wx.ICON_INFORMATION)
                return

            reply_target = self.reply_target

            # 保存当前页面状态，用于回复后恢复到相同页面
            current_page = getattr(self, 'current_pagination', {}).get('page', 1)
            current_tid = reply_target['tid']

            # 准备回复内容
            prepared_content = self.prepare_reply_content(content)

            # 调用回复API（使用新的参数格式）
            result = self.forum_client.post_reply(
                self.current_forum,
                reply_target['fid'],
                reply_target['tid'],
                prepared_content,
                reply_target['pid']  # 关键：指定要回复的楼层
            )

            if result.get('success'):
                wx.MessageBox(f"回复{reply_target['username']}成功", "成功", wx.OK | wx.ICON_INFORMATION)
                # 刷新当前页面，并跳转到回复前的页面（不保存状态，避免覆盖之前的列表状态）
                self.load_thread_detail_and_restore_page(current_tid, current_page, save_state=False)
            else:
                error_message = result.get('error', '回复发送失败')
                wx.MessageBox(f"回复发送失败: {error_message}", "错误", wx.OK | wx.ICON_ERROR)

        except Exception as e:
            wx.MessageBox(f"回复发送失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def on_view_user_profile(self, uid, username):
        """查看用户资料"""
        try:
            if not uid:
                wx.MessageBox("无法获取用户ID", "错误", wx.OK | wx.ICON_ERROR)
                return

            # 调用API获取用户资料
            profile_data = self.forum_client.get_user_profile(self.current_forum, uid)

            # 显示用户资料对话框
            self.show_user_profile_dialog(username, profile_data)

        except Exception as e:
            wx.MessageBox(f"获取{username}的资料失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def show_user_profile_dialog(self, username, profile_data):
        """显示用户资料对话框 - 使用编辑框形式"""
        try:
            # 获取用户昵称，优先使用API返回的username，如果没有则使用传入的username
            user_nickname = profile_data.get('username', username)
            dialog = wx.Dialog(self, title=f"{user_nickname}的资料", size=(500, 600))

            # 创建主布局
            main_sizer = wx.BoxSizer(wx.VERTICAL)

            # 创建资料编辑框
            profile_text = wx.TextCtrl(
                dialog,
                style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP | wx.TE_RICH2
            )

            # 构建资料显示文本
            profile_lines = []

            # 资料字段映射 - 根据API实际返回的字段名进行调整
            field_mapping = [
                ('用户名', profile_data.get('username', '')),  # 用户昵称
                ('争渡号', str(profile_data.get('uid', ''))),  # 用户ID
                ('注册时间', profile_data.get('regdate_fmt', '')),  # 注册时间(格式化)
                ('级别', profile_data.get('groupname', '')),  # 用户级别/组名
                ('最后活跃', profile_data.get('lastactive_fmt', '')),  # 最后活跃时间
                ('在线状态', '在线' if profile_data.get('isonline', 0) else '离线'),  # 在线状态
                ('主题数', str(profile_data.get('threads', 0))),  # 发表的主题数
                ('帖子数', str(profile_data.get('posts', 0))),  # 发表的帖子数
                ('我的帖子', str(profile_data.get('myposts', 0))),  # 用户自己的帖子数
                ('精华帖数', str(profile_data.get('digests', 0))),  # 精华帖数
                ('关注数', str(profile_data.get('follows', 0))),  # 关注的人数
                ('粉丝数', str(profile_data.get('followeds', 0))),  # 粉丝数
                ('个人主页', profile_data.get('homepage', '')),  # 个人主页
                ('在线时长', str(profile_data.get('onlinetime', 0))),  # 在线时长(秒)
                ('个人签名', profile_data.get('sign', '')),  # 个人签名
                ('签到次数', str(profile_data.get('attendancenum', 0))),  # 签到次数
                ('成长值', str(profile_data.get('attendancecredits', 0))),  # 签到成长值
                ('小黑点', str(profile_data.get('black_points', 0))),  # 小黑点数
                ('头像', '有' if profile_data.get('avatar', 0) else '无'),  # 是否有头像
                ('允许改名', '是' if profile_data.get('allowrename', 0) else '否'),  # 是否允许改名
                ('在线认证', profile_data.get('online_auth_expiry_fmt', '')),  # 在线认证到期时间
                ('关注状态', '已关注' if profile_data.get('followstatus', 0) else '未关注')  # 当前关注状态
            ]

            # 添加资料项到文本
            for label, value in field_mapping:
                # 基本空值检查 - 只过滤完全空的值
                if value is None or value == '':
                    continue

                # 处理长文本
                if label == '个人签名' and len(str(value)) > 50:
                    display_value = str(value)[:47] + '...'
                elif label == '在线时长':
                    # 将秒数转换为小时
                    try:
                        hours = int(value) // 3600
                        display_value = f"{hours}小时"
                    except:
                        display_value = str(value)
                else:
                    display_value = str(value)

                # 添加到文本行
                profile_lines.append(f"{label}: {display_value}")

            # 如果没有有效数据，显示提示
            if not profile_lines:
                profile_lines.append("暂无可用资料")

            # 设置编辑框内容
            profile_text.SetValue('\n'.join(profile_lines))

            # 添加编辑框到主布局
            main_sizer.Add(profile_text, 1, wx.EXPAND | wx.ALL, 10)

            # 添加分隔线
            main_sizer.Add(wx.StaticLine(dialog), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

            # 创建按钮区域
            button_sizer = wx.BoxSizer(wx.HORIZONTAL)

            # 添加关闭按钮
            close_btn = wx.Button(dialog, label="关闭(&C)")
            close_btn.Bind(wx.EVT_BUTTON, lambda e: dialog.Close())
            button_sizer.Add(close_btn, 0, wx.ALL, 5)

            main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

            # 设置对话框的sizer
            dialog.SetSizerAndFit(main_sizer)

            # 绑定键盘事件到对话框
            def on_dialog_key_down(event):
                key_code = event.GetKeyCode()
                if key_code == wx.WXK_ESCAPE or key_code == wx.WXK_BACK:
                    dialog.Close()
                    return
                event.Skip()

            dialog.Bind(wx.EVT_KEY_DOWN, on_dialog_key_down)

            # 也绑定到编辑框作为备用
            def on_text_key_down(event):
                key_code = event.GetKeyCode()
                if key_code == wx.WXK_ESCAPE or key_code == wx.WXK_BACK:
                    dialog.Close()
                    return
                event.Skip()

            profile_text.Bind(wx.EVT_KEY_DOWN, on_text_key_down)

            # 居中显示并设置焦点
            dialog.CenterOnParent()
            profile_text.SetFocus()
            dialog.ShowModal()
            dialog.Destroy()

        except Exception as e:
            wx.MessageBox(f"显示用户资料失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def show_profile_details(self, profile_data):
        """显示详细的用户资料（包含完整内容）"""
        try:
            dialog = wx.Dialog(self, title="详细资料", size=(450, 350))
            main_sizer = wx.BoxSizer(wx.VERTICAL)

            # 创建文本控件显示完整内容
            text_ctrl = wx.TextCtrl(dialog, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)

            # 构建详细内容
            details = []

            # 基本资料
            details.append(f"用户名: {username}")

            if profile_data.get('uid'):
                details.append(f"争渡号: {profile_data.get('uid')}")

            if profile_data.get('group'):
                details.append(f"级别: {profile_data.get('group')}")

            if profile_data.get('regdate'):
                details.append(f"注册时间: {profile_data.get('regdate')}")

            if profile_data.get('lastactive'):
                details.append(f"最后活跃: {profile_data.get('lastactive')}")

            if profile_data.get('online'):
                details.append(f"在线状态: {profile_data.get('online')}")

            # 活跃度统计
            details.append("")  # 空行分隔

            if profile_data.get('threads'):
                details.append(f"主题: {profile_data.get('threads')}")

            if profile_data.get('posts'):
                details.append(f"帖子: {profile_data.get('posts')}")

            if profile_data.get('extcredits'):
                details.append(f"成长值: {profile_data.get('extcredits')}")

            if profile_data.get('blackpoints'):
                details.append(f"小黑点: {profile_data.get('blackpoints')}")

            if profile_data.get('attendcount'):
                details.append(f"签到次数: {profile_data.get('attendcount')}")

            if profile_data.get('digestposts'):
                details.append(f"精华: {profile_data.get('digestposts')}")

            # 社交信息
            details.append("")  # 空行分隔

            if profile_data.get('following'):
                details.append(f"关注: {profile_data.get('following')}")

            if profile_data.get('followers'):
                details.append(f"粉丝: {profile_data.get('followers')}")

            # 其他资料
            details.append("")  # 空行分隔

            if profile_data.get('email'):
                details.append(f"邮箱: {profile_data.get('email')}")

            if profile_data.get('gender'):
                details.append(f"性别: {self.format_gender(profile_data.get('gender'))}")

            if profile_data.get('birthday'):
                details.append(f"生日: {profile_data.get('birthday')}")

            if profile_data.get('location'):
                details.append(f"所在地: {profile_data.get('location')}")

            if profile_data.get('signature'):
                details.append(f"\n个人签名:\n{profile_data.get('signature')}")

            # 设置文本内容
            text_ctrl.SetValue('\n'.join(details) if details else "暂无详细资料")

            # 添加到布局
            main_sizer.Add(text_ctrl, 1, wx.EXPAND | wx.ALL, 10)

            # 关闭按钮
            close_btn = wx.Button(dialog, label="关闭(&C)")
            close_btn.Bind(wx.EVT_BUTTON, lambda e: dialog.Close())
            main_sizer.Add(close_btn, 0, wx.ALIGN_CENTER | wx.ALL, 10)

            dialog.SetSizerAndFit(main_sizer)
            dialog.CenterOnParent()
            dialog.ShowModal()
            dialog.Destroy()

        except Exception as e:
            wx.MessageBox(f"显示详细资料失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def format_timestamp(self, timestamp):
        """格式化时间戳"""
        try:
            if isinstance(timestamp, (int, float)):
                return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
            return str(timestamp)
        except Exception:
            return str(timestamp)

    def format_gender(self, gender):
        """格式化性别显示"""
        try:
            gender_map = {
                '1': '男',
                '0': '女',
                '2': '保密'
            }
            return gender_map.get(str(gender), '未知')
        except Exception:
            return '未知'

    def on_edit_post(self, post_data, is_thread_author):
        """编辑帖子"""
        try:
            # 获取必要信息
            pid = post_data.get('pid')
            fid = post_data.get('fid')
            tid = post_data.get('tid')

            if not all([pid, fid, tid]):
                wx.MessageBox("无法获取帖子信息", "错误", wx.OK | wx.ICON_ERROR)
                return

            # 保存编辑目标
            self.edit_target = {
                'pid': pid,
                'fid': fid,
                'tid': tid,
                'is_thread_author': is_thread_author,
                'original_data': post_data
            }

            # 显示编辑对话框
            self.show_edit_dialog(post_data, is_thread_author)

        except Exception as e:
            wx.MessageBox(f"编辑帖子失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def show_edit_dialog(self, post_data, is_thread_author):
        """显示编辑对话框"""
        try:
            dialog = wx.Dialog(self, title="编辑帖子", size=(600, 400))
            panel = wx.Panel(dialog)
            sizer = wx.BoxSizer(wx.VERTICAL)

            # 如果是楼主，显示标题编辑
            if is_thread_author:
                # 标题输入
                title_label = wx.StaticText(panel, label="标题:")
                sizer.Add(title_label, 0, wx.ALL, 5)

                title_ctrl = wx.TextCtrl(panel, value=post_data.get('subject', ''))
                sizer.Add(title_ctrl, 0, wx.EXPAND | wx.ALL, 5)
            else:
                title_ctrl = None

            # 内容编辑
            content_label = wx.StaticText(panel, label="内容:")
            sizer.Add(content_label, 0, wx.ALL, 5)

            # 获取原始内容（清理HTML标签）
            original_content = self.clean_html_tags(post_data.get('message', ''))
            content_ctrl = wx.TextCtrl(panel, value=original_content, style=wx.TE_MULTILINE)
            sizer.Add(content_ctrl, 1, wx.EXPAND | wx.ALL, 5)

            # 按钮区域
            btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

            # 确定按钮
            ok_btn = wx.Button(panel, label="确定(&O)")
            ok_btn.Bind(wx.EVT_BUTTON, lambda e: self.save_edit(dialog, title_ctrl if is_thread_author else None, content_ctrl))
            btn_sizer.Add(ok_btn, 0, wx.ALL, 5)

            # 取消按钮
            cancel_btn = wx.Button(panel, label="取消(&C)")
            cancel_btn.Bind(wx.EVT_BUTTON, lambda e: dialog.Close())
            btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)

            sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

            panel.SetSizer(sizer)
            dialog.SetSizerAndFit(sizer)

            # 居中显示
            dialog.CenterOnParent()

            # 设置焦点到内容编辑框
            if is_thread_author:
                title_ctrl.SetFocus()
            else:
                content_ctrl.SetFocus()

            dialog.ShowModal()
            dialog.Destroy()

        except Exception as e:
            wx.MessageBox(f"显示编辑对话框失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def save_edit(self, dialog, title_ctrl, content_ctrl):
        """保存编辑"""
        try:
            # 获取编辑内容
            title = title_ctrl.GetValue().strip() if title_ctrl else None
            content = content_ctrl.GetValue().strip()

            if not content:
                wx.MessageBox("内容不能为空", "提示", wx.OK | wx.ICON_WARNING)
                return

            edit_target = getattr(self, 'edit_target', {})
            if not edit_target:
                wx.MessageBox("编辑目标信息丢失", "错误", wx.OK | wx.ICON_ERROR)
                return

            # 准备编辑参数
            edit_params = {
                'fid': edit_target['fid'],
                'pid': edit_target['pid'],
                'message': content
            }

            # 如果是楼主，添加标题和分类信息
            if edit_target['is_thread_author'] and title:
                edit_params['subject'] = title
                # 从原始数据获取分类信息
                original_data = edit_target.get('original_data', {})
                edit_params['typeid1'] = original_data.get('typeid1')
                edit_params['typeid2'] = original_data.get('typeid2')
                edit_params['typeid3'] = original_data.get('typeid3')
                edit_params['typeid4'] = original_data.get('typeid4')

            # 调用编辑API
            success = self.forum_client.update_post(self.current_forum, edit_params)

            if success:
                wx.MessageBox("编辑成功", "成功", wx.OK | wx.ICON_INFORMATION)
                dialog.Close()
                # 刷新帖子详情
                self.load_thread_detail(edit_target['tid'])
            else:
                wx.MessageBox("编辑失败", "错误", wx.OK | wx.ICON_ERROR)

        except Exception as e:
            wx.MessageBox(f"保存编辑失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    
    def on_filter_posts_by_user(self, username, uid):
        """只看他功能 - 筛选特定用户的帖子"""
        if not self.current_content_type == 'thread_detail' or not self.current_tid:
            return

        # 不需要在这里重新保存列表状态，因为进入帖子详情时已经保存了

        # 保存当前状态，用于退格键返回
        self.previous_state = {
            'content_type': self.current_content_type,
            'tid': self.current_tid,
            'selected_index': getattr(self, 'saved_list_index', 0),
            'page': getattr(self, 'current_page', 1),
            'filter_mode': getattr(self, 'filter_mode', None)
        }

        # 设置筛选模式
        self.filter_mode = {
            'username': username,
            'uid': uid,
            'original_tid': self.current_tid
        }

        # 重新加载帖子详情，带筛选参数
        self.load_thread_detail_with_filter(self.current_tid, uid)

    def load_thread_detail_with_filter(self, tid, uid, page=None):
        """加载筛选后的帖子详情 - 获取整页数据再前端筛选"""
        try:
            # 获取目标页面的完整帖子详情（不带uid参数）
            if page is None:
                current_page = getattr(self, 'current_page', 1)
            else:
                current_page = page

            result = self.forum_client.get_thread_detail(self.current_forum, tid, page=current_page)

            if 'postlist' in result and 'pagination' in result:
                post_list = result.get('postlist', [])
                thread_info = result.get('thread_info', {})
                pagination = result.get('pagination', {})
                page_info = {
                    'current': pagination.get('page', 1),
                    'total': pagination.get('totalpage', 1)
                }

                # 更新当前页面信息
                self.current_page = page_info['current']
                self.total_pages = page_info['total']
                self.current_pagination = page_info

                # 前端筛选出目标用户的回复
                filter_username = self.filter_mode.get('username', '')
                filtered_posts = [post for post in post_list if post.get('username', '') == filter_username]

                # 显示筛选后的帖子
                self.display_filtered_posts(filtered_posts, post_list, thread_info, page_info)

                # 更新窗口标题显示筛选状态
                filter_username = self.filter_mode.get('username', '')
                self.SetTitle(f"{self.current_forum}-<{self.get_user_nickname()}>-论坛助手 (只看{filter_username})")

                # 自动焦点到第一个帖子
                if hasattr(self, 'list_ctrl') and self.list_ctrl.GetItemCount() > 0:
                    self.list_ctrl.SetFocus()
                    # 选择第一个项目
                    self.list_ctrl.SelectRow(0)
                    # 保存当前选中的索引
                    self.saved_list_index = 0

            else:
                self.show_error_message("获取筛选帖子失败：API返回数据格式不正确")

        except Exception as e:
            self.show_error_message(f"筛选帖子时发生错误: {str(e)}")
        finally:
            # 状态栏已移除，无需设置状态文本
            pass

    def display_filtered_posts(self, filtered_posts, all_posts, thread_info, page_info):
        """显示筛选后的帖子列表 - 保持原始楼层号和分页结构"""
        # 清空列表
        self.list_ctrl.DeleteAllItems()
        self.list_data.clear()

        # 添加筛选后的帖子项，保持原始楼层号（无论是否有内容都要显示分页）
        for post in filtered_posts:
            try:
                # 格式化帖子内容
                username = post.get('username', '')
                message = post.get('message', '')
                dateline = post.get('dateline_fmt', '')

                # 使用正确的楼层号字段名
                floor_number = post.get('floor', 1)

                # 清理HTML标签
                clean_message = self.clean_html_tags(message)

                # 构建显示文本，保持原始楼层号
                if floor_number == 1:
                    display_text = f"楼主 {username} 说\n{clean_message}\n发表时间：{dateline}"
                else:
                    display_text = f"{floor_number}楼 {username} 说\n{clean_message}\n发表时间：{dateline}"

                # 添加到列表
                index = self.list_ctrl.AppendItem([display_text])
                self.list_data.append({
                    'type': 'post',
                    'data': post,
                    'floor_index': floor_number - 1,  # 保持原始楼层索引
                    'post_data': post  # 兼容现有代码结构
                })

            except Exception as e:
                print(f"显示筛选帖子项时出错: {e}")
                continue

        # 添加分页控制
        pagination = {
            'page': page_info['current'],
            'totalpage': page_info['total']
        }
        self.add_pagination_controls(pagination)

    def exit_filter_mode(self):
        """退出筛选模式，返回原始帖子详情"""
        if not hasattr(self, 'filter_mode') or not self.filter_mode:
            return

        # 获取原始帖子信息
        original_tid = self.filter_mode.get('original_tid')

        # 清除筛选模式
        self.filter_mode = None

        # 恢复原始帖子详情显示
        self.load_thread_detail(original_tid)

        # 立即更新窗口标题，移除筛选状态
        self.SetTitle(f"{self.current_forum}-<{self.get_user_nickname()}>-论坛助手")

    def exit_filter_mode_to_list(self):
        """退出筛选模式，直接返回帖子列表"""
        if not hasattr(self, 'filter_mode') or not self.filter_mode:
            return

        # 清除筛选模式
        self.filter_mode = None

        # 恢复窗口标题
        self.SetTitle(f"{self.current_forum}-<{self.get_user_nickname()}>-论坛助手")

        
        # 直接返回到之前的列表状态
        self.go_back_to_previous_list()

    def on_view_user_threads(self, username, uid):
        """查看用户的主题帖子"""
        if not uid:
            return

        # 保存当前状态
        self.save_current_state()

        # 设置用户内容查看模式
        self.user_content_mode = {
            'username': username,
            'uid': uid,
            'content_type': 'threads'
        }

        # 加载用户的主题帖子
        self.load_user_threads_and_restore_focus(uid)

    def on_view_user_posts(self, username, uid):
        """查看用户的回复帖子"""
        if not uid:
            return

        # 保存当前状态
        self.save_current_state()

        # 设置用户内容查看模式
        self.user_content_mode = {
            'username': username,
            'uid': uid,
            'content_type': 'posts'
        }

        # 加载用户的回复帖子
        self.load_user_posts_and_restore_focus(uid)

    def save_current_state(self):
        """保存当前状态，用于返回导航"""
        self.previous_state = {
            'content_type': getattr(self, 'current_content_type', None),
            'tid': getattr(self, 'current_tid', None),
            'selected_index': getattr(self, 'saved_list_index', 0),
            'page': getattr(self, 'current_page', 1),
            'filter_mode': getattr(self, 'filter_mode', None),
            'user_content_mode': getattr(self, 'user_content_mode', None)
        }

    def load_user_threads_and_restore_focus(self, uid, page=1):
        """加载用户的主题帖子并恢复焦点"""
        try:
            # 状态栏已移除，无需设置状态文本

            # 调用API获取用户的主题帖子
            result = self.forum_client.get_user_threads(self.current_forum, uid, page=page)

            # 使用原始数据结构，包含threadlist和pagination
            threadlist = result.get('threadlist', [])
            pagination = result.get('pagination', {})

            # 更新当前状态
            self.current_content_type = 'user_threads'
            self.current_uid = uid
            self.current_page = pagination.get('page', 1)
            self.total_pages = pagination.get('totalpage', 1)

            # 显示用户的主题帖子
            # 直接传递pagination对象，因为display_threads期望的格式是{'page': x, 'totalpage': y}
            self.display_threads(threadlist, pagination, 'user_threads')

            # 更新窗口标题
            username = self.user_content_mode.get('username', str(uid))
            self.SetTitle(f"{self.current_forum}-<{self.get_user_nickname()}>-论坛助手 ({username}的主题)")

            # 设置焦点到第一个项目
            wx.CallAfter(self.reset_keyboard_cursor, 0)

        except Exception as e:
            self.show_error_message(f"加载用户主题帖子时发生错误: {str(e)}")
        finally:
            # 状态栏已移除，无需设置状态文本
            pass

    def load_user_posts_and_restore_focus(self, uid, page=1):
        """加载用户的回复帖子并恢复焦点"""
        try:
            # 状态栏已移除，无需设置状态文本

            # 调用API获取用户的回复帖子
            result = self.forum_client.get_user_posts(self.current_forum, uid, page=page)

            # 使用原始数据结构，包含threadlist和pagination
            threadlist = result.get('threadlist', [])
            pagination = result.get('pagination', {})

            # 需要转换为display_threads期望的格式，显示为回复列表
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

            # 更新当前状态
            self.current_content_type = 'user_posts'
            self.current_uid = uid
            self.current_page = pagination.get('page', 1)
            self.total_pages = pagination.get('totalpage', 1)

            # 显示用户的回复帖子
            # 直接传递pagination对象，因为display_threads期望的格式是{'page': x, 'totalpage': y}
            self.display_threads(formatted_threads, pagination, 'user_posts')

            # 更新窗口标题
            username = self.user_content_mode.get('username', str(uid))
            self.SetTitle(f"{self.current_forum}-<{self.get_user_nickname()}>-论坛助手 ({username}的回复)")

            # 设置焦点到第一个项目
            wx.CallAfter(self.reset_keyboard_cursor, 0)

        except Exception as e:
            self.show_error_message(f"加载用户回复帖子时发生错误: {str(e)}")
        finally:
            # 状态栏已移除，无需设置状态文本
            pass

    def show_info_message(self, message):
        """显示信息提示"""
        wx.MessageBox(message, "提示", wx.OK | wx.ICON_INFORMATION)

    def show_error_message(self, message):
        """显示错误提示"""
        wx.MessageBox(message, "错误", wx.OK | wx.ICON_ERROR)

    # 键盘事件处理的辅助方法
    def handle_reply_to_floor(self, selected_row):
        """处理回复此楼功能"""
        if selected_row >= len(self.list_data):
            return

        item_data = self.list_data[selected_row]
        if item_data.get('type') != 'post':
            return

        # 兼容两种数据结构：正常模式使用 'post_data'，筛选模式使用 'data'
        if 'post_data' in item_data:
            # 正常模式
            post_data = item_data.get('post_data', {})
        else:
            # 筛选模式
            post_data = item_data.get('data', {})

        if not post_data:
            return

        # 设置标记，表示正在处理回复
        self._handling_reply = True

        # 调用回复此楼方法
        self.on_reply_to_floor(post_data)

        # 延迟清除标记
        def clear_flag():
            self._handling_reply = False

        wx.CallLater(500, clear_flag)

    def handle_view_user_profile(self, selected_row):
        """处理查看用户资料功能"""
        if selected_row >= len(self.list_data):
            return

        item_data = self.list_data[selected_row]
        if item_data.get('type') != 'post':
            return

        # 兼容两种数据结构：正常模式使用 'post_data'，筛选模式使用 'data'
        if 'post_data' in item_data:
            # 正常模式
            post_data = item_data.get('post_data', {})
        else:
            # 筛选模式
            post_data = item_data.get('data', {})

        if not post_data:
            return

        # 获取用户信息
        username = post_data.get('username') or post_data.get('author', '')
        uid = post_data.get('uid') or post_data.get('authorid', '')

        if not uid:
            self.show_error_message("无法获取用户信息")
            return

        # 设置标记，表示正在处理用户资料查看
        self._handling_user_profile = True

        # 调用查看用户资料方法
        self.on_view_user_profile(uid, username)

        # 延迟清除标记
        def clear_flag():
            self._handling_user_profile = False

        wx.CallLater(500, clear_flag)

    def handle_filter_by_user(self, selected_row):
        """处理只看他功能"""
        if selected_row >= len(self.list_data):
            return

        item_data = self.list_data[selected_row]
        if item_data.get('type') != 'post':
            return

        # 兼容两种数据结构：正常模式使用 'post_data'，筛选模式使用 'data'
        if 'post_data' in item_data:
            # 正常模式
            post_data = item_data.get('post_data', {})
        else:
            # 筛选模式
            post_data = item_data.get('data', {})

        if not post_data:
            return

        # 获取用户信息
        username = post_data.get('username') or post_data.get('author', '')
        uid = post_data.get('uid') or post_data.get('authorid', '')

        if not uid:
            self.show_error_message("无法获取用户信息")
            return

        # 调用筛选方法
        self.on_filter_posts_by_user(username, uid)

    def handle_user_content_menu(self, selected_row):
        """处理用户内容二级菜单"""
        if selected_row >= len(self.list_data):
            return

        item_data = self.list_data[selected_row]
        if item_data.get('type') != 'post':
            return

        # 兼容两种数据结构：正常模式使用 'post_data'，筛选模式使用 'data'
        if 'post_data' in item_data:
            # 正常模式
            post_data = item_data.get('post_data', {})
        else:
            # 筛选模式
            post_data = item_data.get('data', {})

        if not post_data:
            return

        # 获取用户信息
        username = post_data.get('username') or post_data.get('author', '')
        uid = post_data.get('uid') or post_data.get('authorid', '')

        if not uid:
            self.show_error_message("无法获取用户信息")
            return

        # 显示用户内容二级菜单
        self.show_user_content_submenu(username, uid)

    def handle_edit_post(self, selected_row):
        """处理编辑帖子功能"""
        if selected_row >= len(self.list_data):
            return

        item_data = self.list_data[selected_row]
        if item_data.get('type') != 'post':
            return

        # 兼容两种数据结构：正常模式使用 'post_data'，筛选模式使用 'data'
        if 'post_data' in item_data:
            # 正常模式
            post_data = item_data.get('post_data', {})
        else:
            # 筛选模式
            post_data = item_data.get('data', {})

        if not post_data:
            return

        # 检查是否有编辑权限
        if not self.should_show_edit_menu(post_data):
            self.show_error_message("您没有编辑此帖子的权限")
            return

        # 调用编辑方法
        self.on_edit_post(post_data)

    def show_user_content_submenu(self, username, uid):
        """显示用户内容二级菜单"""
        # 创建菜单
        menu = wx.Menu()

        threads_item = menu.Append(wx.ID_ANY, f"{username}的发布(&F)")
        posts_item = menu.Append(wx.ID_ANY, f"{username}的回复(&H)")

        # 绑定事件
        self.Bind(wx.EVT_MENU, lambda e: self.on_view_user_threads(username, uid), threads_item)
        self.Bind(wx.EVT_MENU, lambda e: self.on_view_user_posts(username, uid), posts_item)

        # 显示菜单
        self.list_ctrl.PopupMenu(menu)
        menu.Destroy()

    def exit_user_content_mode(self):
        """退出用户内容查看模式，返回之前的帖子详情"""
        if not hasattr(self, 'user_content_mode') or not self.user_content_mode:
            return

        # 清除用户内容模式
        self.user_content_mode = None

        # 清除可能存在的用户内容状态
        self.user_content_state_before_thread = None

        # 恢复之前的帖子详情
        if hasattr(self, 'previous_state') and self.previous_state:
            state = self.previous_state
            if state.get('content_type') == 'thread_detail' and state.get('tid'):
                # 恢复到帖子详情，使用save_state=False避免覆盖导航状态
                # 恢复到原来的页码
                target_page = state.get('page', 1)
                self.load_thread_detail_and_restore_page(state['tid'], target_page, save_state=False)

                # 恢复焦点位置
                if state.get('selected_index') is not None:
                    wx.CallAfter(lambda: self.restore_list_focus(state['selected_index']))

                # 恢复窗口标题到默认格式
                self.SetTitle(f"{self.current_forum}-<{self.get_user_nickname()}>-论坛助手")
        else:
            # 如果没有之前的帖子详情状态，恢复到默认标题
            self.SetTitle(f"{self.current_forum}-<{self.get_user_nickname()}>-论坛助手")

    def restore_list_focus(self, index):
        """恢复列表焦点到指定位置"""
        if hasattr(self, 'list_ctrl') and self.list_ctrl.GetItemCount() > index:
            self.list_ctrl.SelectRow(index)
            self.list_ctrl.SetFocus()

    def return_to_user_content(self):
        """返回到用户内容页面"""
        if not hasattr(self, 'user_content_state_before_thread') or not self.user_content_state_before_thread:
            return

        state = self.user_content_state_before_thread
        user_content_mode = state.get('user_content_mode')
        content_type = state.get('current_content_type')
        uid = state.get('current_uid')

        if not user_content_mode or not uid:
            return

        # 使用保存的原始帖子详情状态，而不是当前的
        original_thread_state = state.get('original_thread_state')
        if original_thread_state:
            self.previous_state = original_thread_state
        else:
            # 如果没有保存的原始状态，使用当前状态（向后兼容）
            self.previous_state = {
                'content_type': 'thread_detail',
                'tid': getattr(self, 'current_tid', None),
                'selected_index': 0,
                'page': 1,
                'filter_mode': getattr(self, 'filter_mode', None),
                'user_content_mode': None
            }

        # 恢复用户内容模式
        self.user_content_mode = user_content_mode
        self.current_content_type = content_type
        self.current_uid = uid

        # 恢复到之前的页面和焦点
        target_page = state.get('current_page', 1)
        selected_index = state.get('selected_index', 0)

        # 根据内容类型加载相应的用户内容，使用保存的页码
        if content_type == 'user_threads':
            self.load_user_threads_and_restore_focus(uid, page=target_page)
            # 恢复窗口标题
            username = user_content_mode.get('username', str(uid))
            self.SetTitle(f"{self.current_forum}-<{self.get_user_nickname()}>-论坛助手 ({username}的主题)")
        elif content_type == 'user_posts':
            self.load_user_posts_and_restore_focus(uid, page=target_page)
            # 恢复窗口标题
            username = user_content_mode.get('username', str(uid))
            self.SetTitle(f"{self.current_forum}-<{self.get_user_nickname()}>-论坛助手 ({username}的回复)")

        # 延迟执行焦点恢复
        wx.CallAfter(lambda: self.restore_user_content_focus(selected_index))

        # 不要立即清除用户内容状态，保持用于第二次退格键
        # 在第二次退格键时（从用户内容到帖子详情）才会清除

    def restore_user_content_focus(self, index):
        """恢复用户内容页面的焦点"""
        if hasattr(self, 'list_ctrl') and self.list_ctrl.GetItemCount() > index:
            self.list_ctrl.SelectRow(index)
            self.list_ctrl.SetFocus()