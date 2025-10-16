import os
import threading
import time
from typing import List, Dict, Optional
from pathlib import Path
from environment_setup import EnvironmentSetup

class AudioPlayer:
    def __init__(self):
        self.env_setup = EnvironmentSetup()
        self.instance = None
        self.player = None
        self.playlist: List[Dict] = []
        self.current_index = 0
        self.is_playing = False
        self.is_paused = False
        self.current_volume = 100
        self.total_time = 0
        self.current_time = 0
        self.update_timer = None

        self.setup_vlc()

    def setup_vlc(self):
        """设置VLC"""
        if not self.check_vlc_available():
            print("[WARN] VLC not available, audio playback features will be disabled")
            return

        # 设置VLC环境变量（开发环境）
        import sys
        if not getattr(sys, 'frozen', False):
            # 开发环境
            project_root = Path(__file__).parent.parent
            vlc_dir = project_root / 'vlc'
            if vlc_dir.exists():
                os.environ['PATH'] = str(vlc_dir) + os.pathsep + os.environ.get('PATH', '')
                os.environ['VLC_PLUGIN_PATH'] = str(vlc_dir / 'plugins')
                print(f"设置VLC环境: {vlc_dir}")

        try:
            # 在Windows上尝试初始化COM以避免错误
            import platform
            if platform.system() == 'Windows':
                try:
                    import pythoncom
                    pythoncom.CoInitialize()
                    print("[OK] COM initialized successfully")
                except ImportError:
                    print("[WARN] pythoncom not available, COM initialization skipped")
                except Exception as com_e:
                    print(f"[WARN] COM initialization failed: {com_e}")

            import vlc
            # 添加VLC启动参数以解决COM初始化问题和提高音频解析能力
            args = [
                '--quiet',  # 安静模式
                '--no-video-title-show',  # 不显示视频标题
                '--no-sub-autodetect-file',  # 不自动检测字幕文件
                '--no-snapshot-preview',  # 不显示快照预览
                '--no-stats',  # 不收集统计信息（减少资源占用）
                '--no-audio-time-stretch',  # 禁用音频时间拉伸
                '--network-caching=3000',  # 网络缓存3秒，提高流媒体稳定性
                '--http-reconnect',  # 启用HTTP重连
            ]

            # 尝试使用DirectSound音频输出以避免COM问题
            try:
                args.extend(['--aout=directx'])
            except:
                # 如果DirectSound不可用，尝试其他音频输出
                try:
                    args.extend(['--aout=waveout'])
                except:
                    pass  # 使用默认音频输出

            try:
                self.instance = vlc.Instance(args)
                if self.instance is None:
                    print("[FAIL] Failed to create VLC instance")
                    return

                self.player = self.instance.media_player_new()
                if self.player is None:
                    print("[FAIL] Failed to create VLC media player")
                    return

                print("[OK] Audio player initialization complete")
            except Exception as e:
                print(f"[FAIL] Audio player initialization failed: {e}")
                import traceback
                traceback.print_exc()
                # 重置状态，确保后续检查能正确工作
                self.instance = None
                self.player = None
        except Exception as e:
            print(f"[FAIL] VLC setup failed: {e}")
            import traceback
            traceback.print_exc()
            # 重置状态，确保后续检查能正确工作
            self.instance = None
            self.player = None

    def check_vlc_available(self) -> bool:
        """检查VLC是否可用"""
        # 在开发环境中，VLC在项目根目录的vlc文件夹中
        # 在打包环境中，VLC在dependencies/vlc文件夹中

        # 先检查开发环境
        import sys
        if not getattr(sys, 'frozen', False):
            # 开发环境
            project_root = Path(__file__).parent.parent
            vlc_dir = project_root / 'vlc'

            if vlc_dir.exists():
                # For optimized components, we only need core libraries, not vlc.exe
                core_files = ['libvlc.dll', 'libvlccore.dll']
                if all((vlc_dir / f).exists() for f in core_files):
                    # 检查插件目录（VLC插件在子目录中）
                    plugins_dir = vlc_dir / 'plugins'
                    if plugins_dir.exists():
                        # 查找所有子目录中的DLL文件
                        plugin_dlls = list(plugins_dir.rglob('*.dll'))
                        if len(plugin_dlls) > 10:
                            return True

        # 检查打包环境
        status = self.env_setup.check_dependencies()
        return status.get('vlc', False)

    def is_available(self) -> bool:
        """检查播放器是否可用"""
        return self.instance is not None and self.player is not None

    def play_url(self, url: str) -> bool:
        """直接播放URL音频"""
        if not self.is_available():
            return False

        try:
            media = self.instance.media_new(url)
            self.player.set_media(media)

            # 获取媒体信息 - 使用更深度的解析
            media.parse()  # 基础解析

            # 尝试更深度的解析以获取更多信息
            try:
                # 等待解析完成
                import time
                time.sleep(0.1)

                # 尝试获取解析后的时长
                duration = media.get_duration()
                if duration > 0:
                    self.total_time = duration // 1000
                else:
                    # 如果基础解析失败，尝试异步解析
                    media.parse_with_options(1, 0)  # 1 = parse local, 0 = parse network
                    time.sleep(0.2)  # 等待异步解析
                    duration = media.get_duration()
                    self.total_time = duration // 1000 if duration > 0 else 0

            except Exception as parse_e:
                print(f"媒体解析警告: {parse_e}")
                self.total_time = 0

            # 获取音频格式信息
            import vlc  # 确保vlc模块已导入
            title = ""
            try:
                title = media.get_meta(vlc.Meta.Title)
            except:
                title = ""

            # 从URL推断音频格式
            def infer_format_from_url(url):
                """从URL推断音频格式"""
                url_lower = url.lower()
                if url_lower.endswith('.mp3') or 'mp3' in url_lower:
                    return 'MP3'
                elif url_lower.endswith('.wav') or 'wav' in url_lower:
                    return 'WAV'
                elif url_lower.endswith('.flac') or 'flac' in url_lower:
                    return 'FLAC'
                elif url_lower.endswith('.aac') or 'aac' in url_lower:
                    return 'AAC'
                elif url_lower.endswith('.ogg') or 'ogg' in url_lower:
                    return 'OGG'
                elif url_lower.endswith('.m4a') or 'm4a' in url_lower:
                    return 'M4A'
                elif url_lower.endswith('.opus') or 'opus' in url_lower:
                    return 'OPUS'
                else:
                    return '未知格式'

            track_info = {
                'url': url,
                'title': title or f"音频{self.current_index + 1}",
                'format': '音频流',
                'bitrate': '--'
            }

            # 简化的音频信息获取
            print(f"加载音频流: {url}")

            # 更新播放列表中的当前项目信息
            if 0 <= self.current_index < len(self.playlist):
                # 合并现有信息和新获取的信息，但优先保留论坛检测到的标题
                existing_info = self.playlist[self.current_index].copy()

                # 如果现有信息中有论坛检测到的标题，优先保留它
                forum_title = existing_info.get('title', '')
                if forum_title and not forum_title.startswith(f"音频"):
                    # 论坛检测到的有效标题，保留它
                    track_info['title'] = forum_title

                # 更新其他信息（格式、位速等），但保留标题
                existing_info.update({k: v for k, v in track_info.items() if k != 'title'})
                self.playlist[self.current_index] = existing_info
            else:
                # 如果当前索引无效，添加到播放列表
                self.playlist.append(track_info)
                self.current_index = len(self.playlist) - 1

            self.player.play()
            self.is_playing = True
            self.is_paused = False

            # 重置音频信息更新标志
            self._updated_audio_info = False

            # 启动更新定时器
            self.start_update_timer()
            return True
        except Exception as e:
            print(f"播放失败: {e}")

            # 如果是COM相关错误，尝试重新初始化播放器
            if "COM" in str(e) or "vlc" in str(e).lower():
                print("尝试重新初始化音频播放器...")
                try:
                    # 停止当前播放
                    if self.player:
                        self.player.stop()

                    # 重新创建播放器实例
                    if self.instance:
                        self.player = self.instance.media_player_new()
                        print("音频播放器重新初始化成功")
                except Exception as reinit_e:
                    print(f"重新初始化失败: {reinit_e}")

            return False

    def toggle_play_pause(self):
        """播放/暂停切换"""
        if self.is_paused:
            self.player.play()
            self.is_paused = False
        elif self.is_playing:
            self.player.pause()
            self.is_paused = True
        else:
            # 开始播放当前曲目
            self.play_current_track()

    def stop(self):
        """停止播放"""
        if self.player:
            self.player.stop()
        self.is_playing = False
        self.is_paused = False
        self.current_index = 0
        self.current_time = 0
        self.stop_update_timer()

    def next_track(self) -> bool:
        """播放下一首"""
        if self.current_index < len(self.playlist) - 1:
            self.current_index += 1
            return self.play_current_track()
        return False

    def previous_track(self) -> bool:
        """播放上一首"""
        if self.current_index > 0:
            self.current_index -= 1
            return self.play_current_track()
        return False

    def play_current_track(self) -> bool:
        """播放当前曲目"""
        if 0 <= self.current_index < len(self.playlist):
            return self.play_url(self.playlist[self.current_index]['url'])
        return False

    def set_volume(self, volume: int):
        """设置音量 0-100"""
        self.current_volume = max(0, min(100, volume))
        if self.player:
            self.player.audio_set_volume(self.current_volume)

    def get_audio_devices(self) -> List[Dict]:
        """获取音频设备列表"""
        devices = []
        try:
            # 获取音频输出模块
            devices.append({
                'id': 'default',
                'name': '系统默认设备',
                'is_current': True
            })
        except Exception as e:
            print(f"获取音频设备失败: {e}")

        return devices

    def set_audio_device(self, device_id: str) -> bool:
        """设置音频输出设备"""
        return True  # 简化实现

    def rewind(self, seconds: int = 10):
        """快退指定秒数"""
        if self.player:
            current_time = self.player.get_time()
            new_time = max(0, current_time - seconds * 1000)
            self.player.set_time(new_time)

    def forward(self, seconds: int = 10):
        """快进指定秒数"""
        if self.player:
            current_time = self.player.get_time()
            total_time = self.player.get_length()
            new_time = min(total_time, current_time + seconds * 1000)
            self.player.set_time(new_time)

    def start_update_timer(self):
        """启动状态更新定时器"""
        self.stop_update_timer()
        self.update_timer = threading.Timer(1.0, self.update_position)
        self.update_timer.daemon = True
        self.update_timer.start()

    def stop_update_timer(self):
        """停止状态更新定时器"""
        if self.update_timer:
            self.update_timer.cancel()
            self.update_timer = None

    def update_position(self):
        """更新播放位置信息"""
        if self.is_playing and not self.is_paused and self.player:
            try:
                self.current_time = self.player.get_time() // 1000

                # 在播放开始后尝试更新音频信息（第一次更新时）
                if self.current_time <= 1 and hasattr(self, '_updated_audio_info') and not self._updated_audio_info:
                    self.update_audio_info_from_playing()
                    self._updated_audio_info = True

                # 递归启动下一次更新
                self.update_timer = threading.Timer(1.0, self.update_position)
                self.update_timer.daemon = True
                self.update_timer.start()
            except:
                pass

    def update_audio_info_from_playing(self):
        """在播放过程中更新基本信息（时长等）"""
        try:
            if self.player and self.player.get_media():
                media = self.player.get_media()

                print("播放开始后更新基本信息...")

                # 等待一下让VLC完全加载媒体
                import time
                time.sleep(0.5)

                # 尝试更新总时长信息
                try:
                    current_duration = media.get_duration()
                    if current_duration > 0 and self.total_time <= 0:
                        self.total_time = current_duration // 1000
                        print(f"播放中更新总时长: {self.total_time}秒")
                except Exception as dur_e:
                    print(f"更新时长失败: {dur_e}")

        except Exception as e:
            print(f"更新音频信息时出错: {e}")

    def get_current_track_info(self) -> Dict:
        """获取当前曲目信息"""
        if 0 <= self.current_index < len(self.playlist):
            return self.playlist[self.current_index]
        return {}


    def get_progress_percentage(self) -> float:
        """获取播放进度百分比"""
        if self.total_time > 0:
            return (self.current_time / self.total_time) * 100
        return 0.0