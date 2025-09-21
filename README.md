# ForumAssist

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-orange.svg)

一个专为视障用户设计的无障碍论坛客户端，支持100%键盘操作。

## 特性

- 🔐 **多账户管理** - 支持多个论坛账户，密码AES加密存储
- 🌐 **完整论坛功能** - 支持浏览、发帖、回复、私信等所有功能
- ♿ **无障碍设计** - 完全支持键盘操作，适合视障用户使用
- 🔍 **智能搜索** - 快速搜索论坛内容
- 💬 **消息系统** - 支持私信功能，HTML解析实现
- 🛡️ **安全认证** - 实时登录，会话信息内存存储

## 技术栈

- **语言**: Python 3.8+
- **GUI**: WxPython
- **网络**: requests
- **解析**: BeautifulSoup4
- **加密**: cryptography
- **配置**: configparser

## 安装

1. 克隆项目：
```bash
git clone https://github.com/yourusername/ForumAssist.git
cd ForumAssist
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 运行程序：
```bash
python main.py
```

## 使用说明

### 首次运行

1. 启动程序后，会自动显示账户管理界面
2. 点击"新建"添加你的论坛账户
3. 输入账户信息（论坛名称、地址、用户名、密码、昵称）
4. 添加成功后，选择账户登录即可使用

### 键盘快捷键

| 功能 | 快捷键 |
|------|--------|
| 激活菜单栏 | Alt |
| 控件间切换 | Tab |
| 确认/激活 | Enter |
| 关闭对话框 | Esc |
| 新建账户 | Ctrl+N |
| 编辑账户 | Ctrl+E |
| 删除账户 | Ctrl+D |
| 发送消息 | Ctrl+Enter |
| 刷新内容 | F5 |

### 界面布局

- **左侧**: 树形导航（最新发表、我的发表、论坛板块等）
- **右侧**: 内容列表（帖子列表、回复列表等）
- **顶部**: 搜索框

## 项目结构

```
ForumAssist/
├── main.py                 # 程序入口
├── requirements.txt        # 依赖包
├── README.md              # 项目说明
├── .gitignore             # Git忽略文件
├── src/                   # 源代码
│   ├── main_frame.py      # 主窗口框架
│   ├── auth_manager.py    # 认证管理器
│   ├── forum_client.py    # 论坛客户端
│   ├── config_manager.py  # 配置管理器
│   ├── account_manager.py # 账户管理界面
│   ├── message_manager.py # 消息管理器
│   └── utils/            # 工具模块
│       ├── crypto.py     # 加密工具
│       └── html_parser.py# HTML解析
└── config/               # 配置目录
    └── api_config.py     # API配置
```

## 支持的论坛

目前支持争渡论坛(zd.hk)，未来将支持更多论坛。

## 开发计划

- [ ] 支持更多论坛平台
- [ ] 主题切换功能
- [ ] 语音提示功能
- [ ] 打包为可执行文件
- [ ] 自动更新功能

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License

## 致谢

感谢所有为无障碍事业做出贡献的开发者和用户。

---

**注意**: 本程序专为视障用户设计，请保持无障碍特性的完整性。