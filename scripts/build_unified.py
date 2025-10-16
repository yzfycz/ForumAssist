import os
import sys
import shutil
import subprocess
from pathlib import Path

def create_unified_structure(dist_dir: Path):
    """创建统一依赖结构"""
    print("正在创建目录结构...")

    dependencies_dir = dist_dir / 'dependencies'
    subdirs = ['python', 'libraries', 'vlc', 'config', 'assets']

    for subdir in subdirs:
        (dependencies_dir / subdir).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ dependencies/{subdir}")

def copy_components_to_unified(dist_dir: Path):
    """复制所有组件到统一目录"""
    project_root = Path(__file__).parent.parent
    dependencies_dir = dist_dir / 'dependencies'

    print("正在复制组件...")

    # Python运行时
    print("  复制Python运行时...")
    python_dir = dependencies_dir / 'python'

    # 检查是否在虚拟环境中
    if hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix:
        # 在虚拟环境中，使用基础Python
        system_python = Path(sys.base_prefix)
    else:
        # 在系统Python中
        system_python = Path(sys.executable).parent

    print(f"    使用Python路径: {system_python}")

    required_files = [
        'python311.dll', 'python311.zip', 'vcruntime140.dll',
        'vcruntime140_1.dll', 'msvcp140.dll', 'api-ms-win-crt-*.dll'
    ]

    copied_files = 0
    for pattern in required_files:
        for file_path in system_python.glob(pattern):
            if file_path.is_file():
                shutil.copy2(file_path, python_dir)
                copied_files += 1
                print(f"    ✓ {file_path.name}")

    print(f"    复制了 {copied_files} 个Python运行时文件")

    # Python库
    print("  复制Python库...")
    lib_dir = dependencies_dir / 'libraries'

    required_packages = [
        'wx', 'requests', 'urllib3', 'certifi', 'charset_normalizer', 'idna', 'vlc'
    ]

    # 获取site-packages路径
    if hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix:
        site_packages = Path(sys.base_prefix) / 'Lib' / 'site-packages'
    else:
        site_packages = Path(sys.prefix) / 'Lib' / 'site-packages'

    print(f"    使用库路径: {site_packages}")

    copied_packages = 0
    for package in required_packages:
        src = site_packages / package
        dst = lib_dir / package
        if src.exists():
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
                copied_packages += 1
                print(f"    ✓ {package}/")
            else:
                shutil.copy2(src, dst)
                copied_packages += 1
                print(f"    ✓ {package}")
        else:
            print(f"    ⚠ {package} 不存在")

    # 项目源码
    print("  复制项目源码...")
    project_src = project_root / 'src'
    dst_src = lib_dir / 'src'
    if project_src.exists():
        shutil.copytree(project_src, dst_src, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git'))
        print(f"    ✓ src/")
    else:
        print(f"    ⚠ src/ 目录不存在")

    # VLC组件
    print("  复制VLC组件...")
    vlc_source = project_root / 'vlc'
    vlc_dest = dependencies_dir / 'vlc'
    if vlc_source.exists():
        file_count = 0
        for item in vlc_source.rglob('*'):
            if item.is_file():
                rel_path = item.relative_to(vlc_source)
                dst_file = vlc_dest / rel_path
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dst_file)
                file_count += 1
        print(f"    ✓ vlc/ ({file_count} 个文件)")
    else:
        print(f"    ⚠ vlc/ 目录不存在，请先运行: python scripts/download_vlc.py")

    # 配置和资源
    print("  复制配置和资源...")

    config_source = project_root / 'config'
    config_dest = dependencies_dir / 'config'
    if config_source.exists():
        shutil.copytree(config_source, config_dest, dirs_exist_ok=True)
        print(f"    ✓ config/")
    else:
        print(f"    ⚠ config/ 目录不存在")

    assets_source = project_root / 'assets'
    assets_dest = dependencies_dir / 'assets'
    if assets_source.exists():
        shutil.copytree(assets_source, assets_dest, dirs_exist_ok=True)
        print(f"    ✓ assets/")
    else:
        # 创建空的assets目录
        assets_dest.mkdir(exist_ok=True)
        print(f"    ✓ assets/ (创建空目录)")

def create_readme(dist_dir: Path):
    """创建说明文件"""
    readme_content = """ForumAssist - 论坛助手

目录说明：
- ForumAssist.exe    : 主程序
- dependencies/      : 所有依赖文件
  - python/         : Python运行时环境
  - libraries/      : Python库文件
  - vlc/           : VLC播放器组件
  - config/        : 配置文件
  - assets/        : 资源文件

使用方法：
1. 双击 ForumAssist.exe 启动程序
2. 或使用 "启动ForumAssist.bat"

音频播放功能：
- 自动检测帖子中的音频文件
- 支持MP3、WAV、M4A等格式
- 完整的播放控制快捷键
- 实时播放状态显示

快捷键说明：
- 播放/暂停：空格键 / Ctrl+Home
- 停止：Ctrl+End
- 上一首：Ctrl+PageUp
- 下一首：Ctrl+PageDown
- 快退：Ctrl+Left
- 快进：Ctrl+Right
- 音量增加：Ctrl+Up
- 音量减少：Ctrl+Down

注意事项：
- 请勿删除dependencies文件夹及其内容
- 程序需要Windows 7或更高版本
- 首次运行可能需要防火墙授权
- 如果音频播放功能不可用，请检查VLC组件是否完整

版本：1.0
更新日期：2025年
技术支持：基于wxPython和VLC开发
"""

    readme_path = dist_dir / 'README.txt'
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("  ✓ README.txt")

def create_launcher(dist_dir: Path):
    """创建启动脚本"""
    launcher_content = """@echo off
chcp 65001 >nul
title ForumAssist - 论坛助手
cd /d "%~dp0"

echo ForumAssist - 论坛助手
echo ==================
echo.

if not exist "dependencies" (
    echo.
    echo 错误：找不到dependencies文件夹！
    echo 请确保所有文件完整。
    echo.
    pause
    exit /b 1
)

if not exist "ForumAssist.exe" (
    echo.
    echo 错误：找不到主程序ForumAssist.exe！
    echo 请确保所有文件完整。
    echo.
    pause
    exit /b 1
)

echo 正在启动ForumAssist...
echo.
ForumAssist.exe

if errorlevel 1 (
    echo.
    echo 程序异常退出，请检查dependencies文件夹是否完整。
    echo 常见问题：
    echo 1. 确保VLC组件完整（dependencies/vlc/目录）
    echo 2. 检查Python运行时文件（dependencies/python/目录）
    echo 3. 查看README.txt了解更多信息
    echo.
    pause
)
"""

    launcher_path = dist_dir / '启动ForumAssist.bat'
    with open(launcher_path, 'w', encoding='gbk') as f:
        f.write(launcher_content)
    print("  ✓ 启动ForumAssist.bat")

def build_minimal_exe():
    """构建最小化exe"""
    print("正在构建主程序exe...")

    # 检查PyInstaller是否安装
    try:
        subprocess.run(['pyinstaller', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ PyInstaller未安装，请运行: pip install pyinstaller")
        return False

    cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        "--distpath=dist/temp",
        "scripts/build_minimal.spec"
    ]

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent,
                              capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            print("✓ exe构建成功")
            return True
        else:
            print(f"❌ exe构建失败: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ exe构建超时")
        return False
    except Exception as e:
        print(f"❌ exe构建异常: {e}")
        return False

def check_dependencies():
    """检查构建依赖"""
    print("检查构建依赖...")

    # 检查PyInstaller
    try:
        result = subprocess.run(['pyinstaller', '--version'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"  ✓ PyInstaller: {result.stdout.strip()}")
        else:
            print("  ❌ PyInstaller未正确安装")
            return False
    except:
        print("  ❌ PyInstaller未安装，请运行: pip install pyinstaller")
        return False

    # 检查项目文件
    project_root = Path(__file__).parent.parent
    required_files = ['main.py', 'src/environment_setup.py', 'src/audio_player.py', 'src/main_frame.py']

    for file in required_files:
        file_path = project_root / file
        if file_path.exists():
            print(f"  ✓ {file}")
        else:
            print(f"  ❌ {file} 不存在")
            return False

    # 检查VLC组件
    vlc_dir = project_root / 'vlc'
    if vlc_dir.exists() and (vlc_dir / 'vlc.exe').exists():
        print("  ✓ VLC组件")
    else:
        print("  ⚠ VLC组件不存在，建议先运行: python scripts/download_vlc.py")

    return True

def build_unified_package():
    """构建统一打包"""
    project_root = Path(__file__).parent.parent
    dist_dir = project_root / "dist" / "ForumAssist"

    print("ForumAssist 统一依赖打包")
    print("=" * 50)

    # 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖检查失败，请解决上述问题后重试")
        return False

    # 清理并创建目录
    if dist_dir.exists():
        print("正在清理旧的构建文件...")
        shutil.rmtree(dist_dir)

    create_unified_structure(dist_dir)

    # 构建exe
    if not build_minimal_exe():
        return False

    # 复制exe
    temp_exe = project_root / "dist" / "temp" / "ForumAssist.exe"
    final_exe = dist_dir / "ForumAssist.exe"

    if temp_exe.exists():
        shutil.copy2(temp_exe, final_exe)
        exe_size = final_exe.stat().st_size / (1024*1024)
        print(f"✓ 主程序exe ({exe_size:.1f} MB)")

        # 清理临时文件
        temp_dist = project_root / "dist" / "temp"
        if temp_dist.exists():
            shutil.rmtree(temp_dist)
    else:
        print("❌ 主程序exe文件不存在")
        return False

    # 复制依赖
    copy_components_to_unified(dist_dir)

    # 创建辅助文件
    print("\n创建辅助文件...")
    create_readme(dist_dir)
    create_launcher(dist_dir)

    # 统计信息
    print("\n统计构建信息...")
    dependencies_size = sum(
        f.stat().st_size
        for f in (dist_dir / 'dependencies').rglob('*')
        if f.is_file()
    ) / (1024*1024)

    total_size = sum(
        f.stat().st_size
        for f in dist_dir.rglob('*')
        if f.is_file()
    ) / (1024*1024)

    print(f"\n✓ 打包完成!")
    print(f"主程序: {exe_size:.1f} MB")
    print(f"依赖文件: {dependencies_size:.1f} MB")
    print(f"总大小: {total_size:.1f} MB")
    print(f"输出目录: {dist_dir}")

    return True

def main():
    try:
        if build_unified_package():
            print("\n🎉 构建成功!")
            print("可以分发整个ForumAssist文件夹")
            print("\n使用说明:")
            print("1. 将整个ForumAssist文件夹复制到目标机器")
            print("2. 双击ForumAssist.exe或启动ForumAssist.bat启动程序")
            print("3. 首次运行可能需要防火墙授权")
        else:
            print("\n💥 构建失败!")
            print("请检查错误信息并重试")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n用户中断构建过程")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 构建过程中发生异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()