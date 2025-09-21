# -*- coding: utf-8 -*-
"""
论坛助手主程序
"""

import wx
import os
import sys
from src.main_frame import MainFrame
from src.config_manager import ConfigManager

def main():
    """主程序入口"""
    # 初始化应用程序
    app = wx.App()

    # 创建配置管理器
    config_manager = ConfigManager()

    # 创建主窗口
    main_frame = MainFrame(config_manager)
    main_frame.Show()

    # 运行应用程序
    app.MainLoop()

if __name__ == "__main__":
    main()