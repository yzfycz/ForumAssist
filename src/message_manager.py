# -*- coding: utf-8 -*-
"""
消息管理器
处理消息相关的功能
"""

import wx
from forum_client import ForumClient
from auth_manager import AuthenticationManager

class MessageManager:
    """消息管理器"""

    def __init__(self, forum_client, auth_manager):
        """
        初始化消息管理器

        Args:
            forum_client: 论坛客户端实例
            auth_manager: 认证管理器实例
        """
        self.forum_client = forum_client
        self.auth_manager = auth_manager

    def get_message_list(self, forum_name):
        """
        获取消息列表

        Args:
            forum_name: 论坛名称

        Returns:
            list: 消息列表
        """
        return self.forum_client.get_message_list(forum_name)

    def get_message_detail(self, forum_name, touid):
        """
        获取消息详情

        Args:
            forum_name: 论坛名称
            touid: 对方用户ID

        Returns:
            list: 消息详情列表
        """
        return self.forum_client.get_message_detail(forum_name, touid)

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
        return self.forum_client.send_message(forum_name, touid, subject, message)

class MessageDialog(wx.Dialog):
    """消息对话框"""

    def __init__(self, parent, forum_name, touid, username, message_manager):
        """
        初始化消息对话框

        Args:
            parent: 父窗口
            forum_name: 论坛名称
            touid: 对方用户ID
            username: 对方用户名
            message_manager: 消息管理器实例
        """
        self.forum_name = forum_name
        self.touid = touid
        self.username = username
        self.message_manager = message_manager

        super().__init__(parent, title=f"与【{username}】的对话", size=(600, 500))

        self.create_ui()
        self.load_messages()
        self.bind_events()

    def create_ui(self):
        """创建用户界面"""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # 创建消息显示区域
        self.create_message_area(panel, sizer)

        # 创建分隔线
        line = wx.StaticLine(panel)
        sizer.Add(line, 0, wx.ALL | wx.EXPAND, 5)

        # 创建回复区域
        self.create_reply_area(panel, sizer)

        # 创建按钮区域
        self.create_button_area(panel, sizer)

        panel.SetSizer(sizer)

    def create_message_area(self, parent, sizer):
        """创建消息显示区域"""
        # 创建标题
        title_label = wx.StaticText(parent, label=f"与【{self.username}】的对话")
        title_font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title_label.SetFont(title_font)
        sizer.Add(title_label, 0, wx.ALL | wx.ALIGN_CENTER, 10)

        # 创建分隔线
        line = wx.StaticLine(parent)
        sizer.Add(line, 0, wx.ALL | wx.EXPAND, 5)

        # 创建消息显示控件
        self.message_text = wx.TextCtrl(
            parent,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH | wx.TE_AUTO_URL
        )
        self.message_text.SetMinSize((550, 300))

        sizer.Add(self.message_text, 1, wx.ALL | wx.EXPAND, 10)

    def create_reply_area(self, parent, sizer):
        """创建回复区域"""
        # 创建回复标签
        reply_label = wx.StaticText(parent, label="回复内容:")
        sizer.Add(reply_label, 0, wx.ALL | wx.ALIGN_LEFT, 5)

        # 创建回复输入框
        self.reply_text = wx.TextCtrl(
            parent,
            style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER
        )
        self.reply_text.SetMinSize((550, 100))

        sizer.Add(self.reply_text, 0, wx.ALL | wx.EXPAND, 5)

    def create_button_area(self, parent, sizer):
        """创建按钮区域"""
        button_panel = wx.Panel(parent)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 创建按钮
        self.send_button = wx.Button(button_panel, label="发送(&S) (Ctrl+Enter)")
        self.refresh_button = wx.Button(button_panel, label="刷新(&R) (F5)")
        self.close_button = wx.Button(button_panel, label="关闭(&C)")

        # 添加按钮
        button_sizer.Add(self.send_button, 0, wx.ALL, 5)
        button_sizer.Add(self.refresh_button, 0, wx.ALL, 5)
        button_sizer.AddStretchSpacer()
        button_sizer.Add(self.close_button, 0, wx.ALL, 5)

        button_panel.SetSizer(button_sizer)
        sizer.Add(button_panel, 0, wx.ALL | wx.EXPAND, 5)

    def bind_events(self):
        """绑定事件"""
        # 按钮事件
        self.send_button.Bind(wx.EVT_BUTTON, self.on_send)
        self.refresh_button.Bind(wx.EVT_BUTTON, self.on_refresh)
        self.close_button.Bind(wx.EVT_BUTTON, self.on_close)

        # 对话框事件
        self.Bind(wx.EVT_CLOSE, self.on_close)

        # 键盘事件
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.reply_text.Bind(wx.EVT_KEY_DOWN, self.on_reply_key_down)

        # 设置快捷键
        self.setup_accelerators()

    def setup_accelerators(self):
        """设置快捷键"""
        # 创建快捷键表
        accel_entries = [
            wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_F5, wx.ID_REFRESH),
            wx.AcceleratorEntry(wx.ACCEL_CTRL, wx.WXK_RETURN, wx.ID_FORWARD)
        ]

        # 创建加速器表
        accel_table = wx.AcceleratorTable(accel_entries)
        self.SetAcceleratorTable(accel_table)

        # 绑定快捷键事件
        self.Bind(wx.EVT_MENU, self.on_refresh, id=wx.ID_REFRESH)
        self.Bind(wx.EVT_MENU, self.on_send, id=wx.ID_FORWARD)

    def load_messages(self):
        """加载消息"""
        messages = self.message_manager.get_message_detail(self.forum_name, self.touid)

        if not messages:
            self.message_text.SetValue("暂无消息")
            return

        # 显示消息
        message_text = ""
        for msg in messages:
            message_text += f"{msg['username']} ({msg['datetime']}):\n"
            message_text += f"{msg['content']}\n"
            message_text += "=" * 40 + "\n"

        self.message_text.SetValue(message_text)

        # 滚动到底部
        self.message_text.SetInsertionPoint(len(self.message_text.GetValue()))

    def on_send(self, event):
        """发送消息"""
        reply_content = self.reply_text.GetValue().strip()
        if not reply_content:
            wx.MessageBox("请输入回复内容", "提示", wx.OK | wx.ICON_INFORMATION)
            return

        # 发送消息
        subject = f"回复: {self.username}"
        success = self.message_manager.send_message(
            self.forum_name, self.touid, subject, reply_content
        )

        if success:
            wx.MessageBox("消息发送成功", "成功", wx.OK | wx.ICON_INFORMATION)
            self.reply_text.Clear()
            self.load_messages()  # 刷新消息列表
        else:
            wx.MessageBox("消息发送失败", "错误", wx.OK | wx.ICON_ERROR)

    def on_refresh(self, event):
        """刷新消息"""
        self.load_messages()

    def on_close(self, event):
        """关闭对话框"""
        self.EndModal(wx.ID_OK)

    def on_key_down(self, event):
        """键盘事件"""
        key_code = event.GetKeyCode()

        # ESC键关闭
        if key_code == wx.WXK_ESCAPE:
            self.on_close(event)
        else:
            event.Skip()

    def on_reply_key_down(self, event):
        """回复框键盘事件"""
        key_code = event.GetKeyCode()

        # Ctrl+Enter发送
        if event.ControlDown() and key_code == wx.WXK_RETURN:
            self.on_send(event)
        else:
            event.Skip()

class MessageListDialog(wx.Dialog):
    """消息列表对话框"""

    def __init__(self, parent, forum_name, message_manager):
        """
        初始化消息列表对话框

        Args:
            parent: 父窗口
            forum_name: 论坛名称
            message_manager: 消息管理器实例
        """
        self.forum_name = forum_name
        self.message_manager = message_manager

        super().__init__(parent, title="消息列表", size=(500, 400))

        self.create_ui()
        self.load_message_list()
        self.bind_events()

    def create_ui(self):
        """创建用户界面"""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # 创建消息列表
        self.create_message_list(panel, sizer)

        # 创建按钮
        self.create_buttons(panel, sizer)

        panel.SetSizer(sizer)

    def create_message_list(self, parent, sizer):
        """创建消息列表"""
        # 创建列表控件
        self.list_ctrl = wx.ListCtrl(parent, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.list_ctrl.InsertColumn(0, "用户名", width=200)
        self.list_ctrl.InsertColumn(1, "状态", width=100)
        self.list_ctrl.InsertColumn(2, "用户ID", width=100)

        sizer.Add(self.list_ctrl, 1, wx.ALL | wx.EXPAND, 10)

    def create_buttons(self, parent, sizer):
        """创建按钮"""
        button_panel = wx.Panel(parent)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 创建按钮
        self.view_button = wx.Button(button_panel, label="查看对话(&V)")
        self.refresh_button = wx.Button(button_panel, label="刷新(&R) (F5)")
        self.close_button = wx.Button(button_panel, label="关闭(&C)")

        # 添加按钮
        button_sizer.Add(self.view_button, 0, wx.ALL, 5)
        button_sizer.Add(self.refresh_button, 0, wx.ALL, 5)
        button_sizer.AddStretchSpacer()
        button_sizer.Add(self.close_button, 0, wx.ALL, 5)

        button_panel.SetSizer(button_sizer)
        sizer.Add(button_panel, 0, wx.ALL | wx.EXPAND, 5)

    def bind_events(self):
        """绑定事件"""
        # 按钮事件
        self.view_button.Bind(wx.EVT_BUTTON, self.on_view_message)
        self.refresh_button.Bind(wx.EVT_BUTTON, self.on_refresh)
        self.close_button.Bind(wx.EVT_BUTTON, self.on_close)

        # 列表事件
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_selection_changed)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_activated)

        # 对话框事件
        self.Bind(wx.EVT_CLOSE, self.on_close)

        # 设置快捷键
        self.setup_accelerators()

    def setup_accelerators(self):
        """设置快捷键"""
        # 创建快捷键表
        accel_entries = [
            wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_F5, wx.ID_REFRESH)
        ]

        # 创建加速器表
        accel_table = wx.AcceleratorTable(accel_entries)
        self.SetAcceleratorTable(accel_table)

        # 绑定快捷键事件
        self.Bind(wx.EVT_MENU, self.on_refresh, id=wx.ID_REFRESH)

    def load_message_list(self):
        """加载消息列表"""
        self.list_ctrl.DeleteAllItems()

        messages = self.message_manager.get_message_list(self.forum_name)

        for i, msg in enumerate(messages):
            self.list_ctrl.InsertItem(i, msg.get('username', ''))
            self.list_ctrl.SetItem(i, 1, msg.get('status', ''))
            self.list_ctrl.SetItem(i, 2, msg.get('touid', ''))

    def on_view_message(self, event):
        """查看消息"""
        selected = self.list_ctrl.GetFirstSelected()
        if selected == -1:
            wx.MessageBox("请选择要查看的消息", "提示", wx.OK | wx.ICON_INFORMATION)
            return

        username = self.list_ctrl.GetItemText(selected, 0)
        touid = self.list_ctrl.GetItemText(selected, 2)

        # 打开消息对话框
        dialog = MessageDialog(self, self.forum_name, touid, username, self.message_manager)
        dialog.ShowModal()
        dialog.Destroy()

    def on_selection_changed(self, event):
        """选择改变事件"""
        # 更新按钮状态
        selected = self.list_ctrl.GetFirstSelected()
        has_selection = selected != -1

        self.view_button.Enable(has_selection)

    def on_item_activated(self, event):
        """项目激活事件"""
        # 双击查看
        self.on_view_message(event)

    def on_refresh(self, event):
        """刷新"""
        self.load_message_list()

    def on_close(self, event):
        """关闭"""
        self.EndModal(wx.ID_OK)