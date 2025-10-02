# -*- coding: utf-8 -*-
"""
设置对话框
提供软件设置选项界面
"""

import wx

class SettingsDialog(wx.Dialog):
    """设置对话框"""

    def __init__(self, parent, config_manager):
        """
        初始化设置对话框

        Args:
            parent: 父窗口
            config_manager: 配置管理器实例
        """
        super().__init__(parent, title="设置", size=(500, 400))

        self.config_manager = config_manager

        # 创建UI
        self.create_ui()

        # 居中显示
        self.Center()

    def create_ui(self):
        """创建用户界面"""
        # 创建主sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 创建选项卡
        notebook = wx.Notebook(self)

        # 软件设置选项卡
        software_panel = self.create_software_settings_panel(notebook)
        notebook.AddPage(software_panel, "软件设置")

        main_sizer.Add(notebook, 1, wx.EXPAND | wx.ALL, 10)

        # 创建按钮区域
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 确定按钮
        ok_button = wx.Button(self, wx.ID_OK, "确定")
        ok_button.Bind(wx.EVT_BUTTON, self.on_ok)

        # 取消按钮
        cancel_button = wx.Button(self, wx.ID_CANCEL, "取消")
        cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)

        button_sizer.AddStretchSpacer(1)
        button_sizer.Add(ok_button, 0, wx.ALL, 5)
        button_sizer.Add(cancel_button, 0, wx.ALL, 5)

        main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizerAndFit(main_sizer)

    def create_software_settings_panel(self, parent):
        """创建软件设置选项卡面板"""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # 显示列表序号复选框
        self.show_list_numbers_checkbox = wx.CheckBox(
            panel,
            label="显示列表序号",
            style=wx.ALIGN_LEFT
        )

        # 设置当前状态
        current_state = self.config_manager.get_show_list_numbers()
        self.show_list_numbers_checkbox.SetValue(current_state)

        # 添加说明文字
        info_text = wx.StaticText(
            panel,
            label="启用后将在列表中创建包含序号的隐藏列，格式为'1之24项'等",
            style=wx.ST_ELLIPSIZE_END
        )
        info_text.Wrap(450)

        sizer.Add(self.show_list_numbers_checkbox, 0, wx.ALL, 10)
        sizer.Add(info_text, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        sizer.AddStretchSpacer(1)

        panel.SetSizer(sizer)
        return panel

    def on_ok(self, event):
        """确定按钮事件"""
        # 保存设置
        show_list_numbers = self.show_list_numbers_checkbox.GetValue()
        self.config_manager.set_show_list_numbers(show_list_numbers)

        # 关闭对话框
        self.EndModal(wx.ID_OK)

    def on_cancel(self, event):
        """取消按钮事件"""
        self.EndModal(wx.ID_CANCEL)