# -*- coding: utf-8 -*-
"""
账户管理界面
管理论坛账户的添加、编辑和删除
"""

import wx
import requests
from config.api_config import APPKEY, SECKEY, BASE_URL

class AccountManager(wx.Dialog):
    """账户管理器"""

    def __init__(self, config_manager, parent=None):
        """
        初始化账户管理器

        Args:
            config_manager: 配置管理器实例
            parent: 父窗口
        """
        self.config_manager = config_manager
        self.accounts = self.config_manager.get_forum_list()

        super().__init__(parent, title="账户管理", size=(600, 400))

        self.create_ui()
        self.load_accounts()
        self.bind_events()

        # 设置快捷键
        self.setup_accelerators()

    def create_ui(self):
        """创建用户界面"""
        # 创建主面板
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # 创建账户列表
        self.create_account_list(panel, sizer)

        # 创建按钮区域
        self.create_button_area(panel, sizer)

        panel.SetSizer(sizer)

    def create_account_list(self, parent, sizer):
        """创建账户列表"""
        # 创建列表控件
        self.list_ctrl = wx.ListCtrl(parent, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.list_ctrl.InsertColumn(0, "论坛名称", width=150)
        self.list_ctrl.InsertColumn(1, "用户名", width=200)
        self.list_ctrl.InsertColumn(2, "昵称", width=150)

        sizer.Add(self.list_ctrl, 1, wx.ALL | wx.EXPAND, 10)

    def create_button_area(self, parent, sizer):
        """创建按钮区域"""
        button_panel = wx.Panel(parent)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 创建按钮
        self.new_button = wx.Button(button_panel, label="新建 (Ctrl+N)")
        self.edit_button = wx.Button(button_panel, label="编辑 (Ctrl+E)")
        self.delete_button = wx.Button(button_panel, label="删除 (Ctrl+D)")
        self.close_button = wx.Button(button_panel, label="关闭")

        # 添加按钮到布局
        button_sizer.Add(self.new_button, 0, wx.ALL, 5)
        button_sizer.Add(self.edit_button, 0, wx.ALL, 5)
        button_sizer.Add(self.delete_button, 0, wx.ALL, 5)
        button_sizer.AddStretchSpacer()
        button_sizer.Add(self.close_button, 0, wx.ALL, 5)

        button_panel.SetSizer(button_sizer)
        sizer.Add(button_panel, 0, wx.ALL | wx.EXPAND, 10)

    def bind_events(self):
        """绑定事件"""
        # 按钮事件
        self.new_button.Bind(wx.EVT_BUTTON, self.on_new_account)
        self.edit_button.Bind(wx.EVT_BUTTON, self.on_edit_account)
        self.delete_button.Bind(wx.EVT_BUTTON, self.on_delete_account)
        self.close_button.Bind(wx.EVT_BUTTON, self.on_close)

        # 列表事件
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_selection_changed)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_activated)

        # 对话框事件
        self.Bind(wx.EVT_CLOSE, self.on_close)

        # 键盘事件
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)

    def setup_accelerators(self):
        """设置快捷键"""
        # 创建快捷键表
        accel_entries = [
            wx.AcceleratorEntry(wx.ACCEL_CTRL, ord('N'), wx.ID_NEW),
            wx.AcceleratorEntry(wx.ACCEL_CTRL, ord('E'), wx.ID_EDIT),
            wx.AcceleratorEntry(wx.ACCEL_CTRL, ord('D'), wx.ID_DELETE)
        ]

        # 创建加速器表
        accel_table = wx.AcceleratorTable(accel_entries)
        self.SetAcceleratorTable(accel_table)

        # 绑定快捷键事件
        self.Bind(wx.EVT_MENU, self.on_new_account, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.on_edit_account, id=wx.ID_EDIT)
        self.Bind(wx.EVT_MENU, self.on_delete_account, id=wx.ID_DELETE)

    def load_accounts(self):
        """加载账户列表"""
        self.list_ctrl.DeleteAllItems()

        for i, account in enumerate(self.accounts):
            self.list_ctrl.InsertItem(i, account.get('name', ''))
            self.list_ctrl.SetItem(i, 1, account.get('username', ''))
            self.list_ctrl.SetItem(i, 2, account.get('nickname', account.get('username', '')))

    def on_new_account(self, event):
        """新建账户"""
        dialog = AccountEditDialog(self, title="新建账户")
        if dialog.ShowModal() == wx.ID_OK:
            account_data = dialog.get_account_data()
            if account_data:
                # 检查账户名称是否已存在
                if self.config_manager.forum_exists(account_data['name']):
                    wx.MessageBox("账户名称已存在", "错误", wx.OK | wx.ICON_ERROR)
                    return

                # 添加账户
                if self.config_manager.add_forum(account_data):
                    self.accounts = self.config_manager.get_forum_list()
                    self.load_accounts()
                    wx.MessageBox("账户添加成功", "成功", wx.OK | wx.ICON_INFORMATION)
                else:
                    wx.MessageBox("账户添加失败", "错误", wx.OK | wx.ICON_ERROR)

        dialog.Destroy()

    def on_edit_account(self, event):
        """编辑账户"""
        selected = self.list_ctrl.GetFirstSelected()
        if selected == -1:
            wx.MessageBox("请选择要编辑的账户", "提示", wx.OK | wx.ICON_INFORMATION)
            return

        account = self.accounts[selected]
        dialog = AccountEditDialog(self, title="编辑账户", account=account)
        if dialog.ShowModal() == wx.ID_OK:
            account_data = dialog.get_account_data()
            if account_data:
                # 更新账户
                if self.config_manager.update_forum(account['name'], account_data):
                    self.accounts = self.config_manager.get_forum_list()
                    self.load_accounts()
                    wx.MessageBox("账户更新成功", "成功", wx.OK | wx.ICON_INFORMATION)
                else:
                    wx.MessageBox("账户更新失败", "错误", wx.OK | wx.ICON_ERROR)

        dialog.Destroy()

    def on_delete_account(self, event):
        """删除账户"""
        selected = self.list_ctrl.GetFirstSelected()
        if selected == -1:
            wx.MessageBox("请选择要删除的账户", "提示", wx.OK | wx.ICON_INFORMATION)
            return

        account = self.accounts[selected]

        # 确认删除
        result = wx.MessageBox(
            f"确定要删除账户 '{account['name']}' 吗？",
            "确认删除",
            wx.YES_NO | wx.ICON_QUESTION
        )

        if result == wx.YES:
            # 删除账户
            if self.config_manager.delete_forum(account['name']):
                self.accounts = self.config_manager.get_forum_list()
                self.load_accounts()
                wx.MessageBox("账户删除成功", "成功", wx.OK | wx.ICON_INFORMATION)
            else:
                wx.MessageBox("账户删除失败", "错误", wx.OK | wx.ICON_ERROR)

    def on_selection_changed(self, event):
        """选择改变事件"""
        # 更新按钮状态
        selected = self.list_ctrl.GetFirstSelected()
        has_selection = selected != -1

        self.edit_button.Enable(has_selection)
        self.delete_button.Enable(has_selection)

    def on_item_activated(self, event):
        """项目激活事件"""
        # 双击编辑
        self.on_edit_account(event)

    def on_close(self, event):
        """关闭事件"""
        self.EndModal(wx.ID_OK)

    def on_key_down(self, event):
        """键盘事件"""
        key_code = event.GetKeyCode()

        # ESC键关闭
        if key_code == wx.WXK_ESCAPE:
            self.on_close(event)
        else:
            event.Skip()

class AccountEditDialog(wx.Dialog):
    """账户编辑对话框"""

    def __init__(self, parent, title, account=None):
        """
        初始化账户编辑对话框

        Args:
            parent: 父窗口
            title: 对话框标题
            account: 要编辑的账户数据，如果为None则新建
        """
        self.account = account
        self.is_edit = account is not None

        super().__init__(parent, title=title, size=(400, 300))

        self.create_ui()
        self.bind_events()

        if self.is_edit:
            self.load_account_data()

    def create_ui(self):
        """创建用户界面"""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # 创建输入字段
        self.create_input_fields(panel, sizer)

        # 创建按钮
        self.create_buttons(panel, sizer)

        panel.SetSizer(sizer)

    def create_input_fields(self, parent, sizer):
        """创建输入字段"""
        # 论坛名称（组合框）
        name_label = wx.StaticText(parent, label="论坛名称:")
        forum_choices = ["争渡论坛", "自定义"]
        self.name_combo = wx.ComboBox(parent, choices=forum_choices, style=wx.CB_READONLY)
        if self.is_edit:
            self.name_combo.Disable()  # 编辑模式下禁止修改名称

        # 用户名
        username_label = wx.StaticText(parent, label="争渡好或邮箱:")
        self.username_ctrl = wx.TextCtrl(parent)

        # 密码
        password_label = wx.StaticText(parent, label="密码:")
        self.password_ctrl = wx.TextCtrl(parent, style=wx.TE_PASSWORD)

        # 添加到布局
        grid_sizer = wx.FlexGridSizer(3, 2, 10, 10)
        grid_sizer.AddGrowableCol(1, 1)

        grid_sizer.Add(name_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.name_combo, 0, wx.EXPAND)

        grid_sizer.Add(username_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.username_ctrl, 0, wx.EXPAND)

        grid_sizer.Add(password_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.password_ctrl, 0, wx.EXPAND)

        sizer.Add(grid_sizer, 1, wx.ALL | wx.EXPAND, 20)

    def create_buttons(self, parent, sizer):
        """创建按钮"""
        button_panel = wx.Panel(parent)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 创建按钮
        ok_button = wx.Button(button_panel, id=wx.ID_OK, label="确定")
        cancel_button = wx.Button(button_panel, id=wx.ID_CANCEL, label="取消")

        # 添加按钮到布局
        button_sizer.Add(ok_button, 0, wx.ALL, 5)
        button_sizer.Add(cancel_button, 0, wx.ALL, 5)

        button_panel.SetSizer(button_sizer)
        sizer.Add(button_panel, 0, wx.ALL | wx.ALIGN_CENTER, 10)

    def bind_events(self):
        """绑定事件"""
        self.Bind(wx.EVT_BUTTON, self.on_ok, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, id=wx.ID_CANCEL)

        # 文本框回车事件
        self.username_ctrl.Bind(wx.EVT_TEXT_ENTER, self.on_ok)
        self.password_ctrl.Bind(wx.EVT_TEXT_ENTER, self.on_ok)

    def load_account_data(self):
        """加载账户数据"""
        if self.account:
            forum_name = self.account.get('name', '')
            self.name_combo.SetValue(forum_name)
            self.username_ctrl.SetValue(self.account.get('username', ''))
            self.password_ctrl.SetValue(self.account.get('password', ''))

    def get_account_data(self):
        """获取账户数据并验证登录"""
        forum_name = self.name_combo.GetValue().strip()
        username = self.username_ctrl.GetValue().strip()
        password = self.password_ctrl.GetValue().strip()

        # 验证必填字段
        if not forum_name:
            wx.MessageBox("请选择论坛名称", "错误", wx.OK | wx.ICON_ERROR)
            self.name_combo.SetFocus()
            return None

        if not username:
            wx.MessageBox("请输入争渡好或邮箱", "错误", wx.OK | wx.ICON_ERROR)
            self.username_ctrl.SetFocus()
            return None

        if not password:
            wx.MessageBox("请输入密码", "错误", wx.OK | wx.ICON_ERROR)
            self.password_ctrl.SetFocus()
            return None

        # 测试登录API
        if not self.test_login(forum_name, username, password):
            return None

        # 根据论坛名称确定URL
        if forum_name == "争渡论坛":
            url = BASE_URL
        else:
            url = "http://www.zd.hk/"  # 默认URL

        return {
            'name': forum_name,
            'url': url,
            'username': username,
            'password': password,
            'nickname': username  # 使用用户名作为昵称
        }

    def test_login(self, forum_name, username, password):
        """测试登录API"""
        try:
            # 创建临时会话进行登录测试
            session = requests.Session()

            # 确定登录URL
            if forum_name == "争渡论坛":
                login_url = f"{BASE_URL.rstrip('/')}/user-login.htm"
            else:
                login_url = "http://www.zd.hk/user-login.htm"

            # 准备登录数据
            login_data = {
                "email": username,
                "password": password,
                "appkey": APPKEY,
                "seckey": SECKEY,
                "format": "json"
            }

            # 显示等待提示
            wx.BeginBusyCursor()
            try:
                response = session.post(login_url, data=login_data, timeout=10)

                if response.status_code == 200:
                    result = response.json()
                    if result.get('status') == 1:
                        # 登录成功，获取用户信息
                        uid = result.get('uid')
                        if uid:
                            # 获取用户详细信息
                            user_info_url = f"{BASE_URL.rstrip('/')}/user-index.htm"
                            user_params = {
                                "uid": uid,
                                "format": "json"
                            }

                            user_response = session.get(user_info_url, params=user_params, timeout=10)
                            if user_response.status_code == 200:
                                user_result = user_response.json()
                                if user_result.get('status') == 1:
                                    user_data = user_result.get('data', {})
                                    # 缓存用户信息以备后用
                                    self.user_info = {
                                        'uid': uid,
                                        'username': user_data.get('username', username),
                                        'nickname': user_data.get('nickname', username)
                                    }
                                    return True
                    else:
                        error_msg = result.get('message', '登录失败')
                        wx.MessageBox(f"登录失败: {error_msg}", "错误", wx.OK | wx.ICON_ERROR)
                        return False
                else:
                    wx.MessageBox(f"网络错误: HTTP {response.status_code}", "错误", wx.OK | wx.ICON_ERROR)
                    return False
            finally:
                wx.EndBusyCursor()

        except Exception as e:
            wx.EndBusyCursor()
            wx.MessageBox(f"连接失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            return False

    def on_ok(self, event):
        """确定按钮"""
        if self.get_account_data():
            self.EndModal(wx.ID_OK)

    def on_cancel(self, event):
        """取消按钮"""
        self.EndModal(wx.ID_CANCEL)