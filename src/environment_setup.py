import os
import sys
from pathlib import Path

class EnvironmentSetup:
    """运行时环境配置"""

    def __init__(self):
        self.app_dir = self.get_app_directory()
        self.dependencies_dir = os.path.join(self.app_dir, 'dependencies')
        self.setup_environment()

    def get_app_directory(self) -> str:
        """获取应用程序目录"""
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return str(Path(__file__).parent.parent.parent)

    def setup_environment(self):
        """设置运行环境"""
        dep_dir = self.dependencies_dir

        # 添加Python库路径
        lib_dir = os.path.join(dep_dir, 'libraries')
        if os.path.exists(lib_dir) and lib_dir not in sys.path:
            sys.path.insert(0, lib_dir)

        # 添加Python运行时路径
        python_dir = os.path.join(dep_dir, 'python')
        if os.path.exists(python_dir):
            os.environ['PATH'] = python_dir + os.pathsep + os.environ.get('PATH', '')

        # 添加VLC路径
        vlc_dir = os.path.join(dep_dir, 'vlc')
        if os.path.exists(vlc_dir):
            os.environ['PATH'] = vlc_dir + os.pathsep + os.environ.get('PATH', '')
            os.environ['VLC_PLUGIN_PATH'] = os.path.join(vlc_dir, 'plugins')

        # 设置配置路径
        config_dir = os.path.join(dep_dir, 'config')
        if os.path.exists(config_dir):
            os.environ['FORUM_CONFIG_DIR'] = config_dir

    def check_dependencies(self) -> dict:
        """检查依赖项"""
        dep_dir = self.dependencies_dir
        status = {
            'dependencies_folder': os.path.exists(dep_dir)
        }

        if not status['dependencies_folder']:
            return status

        # 检查各组件
        components = {
            'python_runtime': ['python', ['python311.dll', 'python311.zip']],
            'python_libs': ['libraries', ['wx', 'requests', 'vlc', 'src']],
            'vlc': ['vlc', ['vlc.exe', 'libvlc.dll', 'libvlccore.dll']],
            'config': ['config', []]
        }

        for comp_name, (subdir, required_files) in components.items():
            comp_dir = os.path.join(dep_dir, subdir)
            if os.path.exists(comp_dir):
                if required_files:
                    status[comp_name] = all(
                        os.path.exists(os.path.join(comp_dir, f)) for f in required_files
                    )
                else:
                    status[comp_name] = True
            else:
                status[comp_name] = False

        return status

    def show_dependency_error(self):
        """显示依赖缺失错误"""
        status = self.check_dependencies()
        missing_items = [k for k, v in status.items() if not v]

        message = "以下组件缺失或损坏：\n\n"

        item_names = {
            'dependencies_folder': '• dependencies 文件夹\n',
            'python_runtime': '• Python运行时文件\n',
            'python_libs': '• Python库文件\n',
            'vlc': '• VLC播放组件\n',
            'config': '• 配置文件\n'
        }

        for item in missing_items:
            message += item_names.get(item, f"• {item}\n")

        message += "\n请重新安装应用程序。"

        try:
            import wx
            dlg = wx.MessageDialog(
                None, message, "组件缺失",
                wx.OK | wx.ICON_ERROR
            )
            dlg.ShowModal()
            dlg.Destroy()
        except:
            print(message)
            input("按Enter键退出...")