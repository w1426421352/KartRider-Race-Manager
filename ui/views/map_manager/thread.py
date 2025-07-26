# 文件名: ui/views/map_manager/thread.py

import os
import shutil
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

from core.map_manager import MapManager


class MapImportThread(QThread):
    """在后台线程中执行耗时的地图导入、缓存和清理任务"""
    progress_updated = pyqtSignal(str, str)
    import_finished = pyqtSignal(dict)  # 信号返回一个包含结果的字典

    def __init__(self, game_path, unpacker_path):
        super().__init__()
        self.game_path = game_path
        self.unpacker_path = unpacker_path
        # 在线程中创建自己的MapManager实例以确保线程安全
        self.map_manager = MapManager()

    def run(self):
        temp_path = "data/temp_unpack"
        try:
            self.progress_updated.emit("开始自动化地图导入流程...", "INFO")

            # 1. 准备路径和目录
            if os.path.exists(temp_path):
                shutil.rmtree(temp_path)
            os.makedirs(temp_path)

            # 2. 调用解包
            files_to_unpack = {
                "track_common.rho": os.path.join(self.game_path, "Data", "track_common.rho"),
                "trackThumb.rho": os.path.join(self.game_path, "Data", "trackThumb.rho"),
                "dialog2_selectTrackEx.rho": os.path.join(self.game_path, "Data", "dialog2_selectTrackEx.rho")
            }
            for name, path in files_to_unpack.items():
                if not os.path.exists(path):
                    self.progress_updated.emit(f"核心文件未找到: {name}，跳过。", "WARNING")
                    continue
                self.progress_updated.emit(f"正在解包 {name}...", "INFO")
                subprocess.run([self.unpacker_path, path, temp_path], check=True, capture_output=True)

            self.progress_updated.emit("核心资源文件解包完成。", "INFO")

            # 3. 聚合数据并存入DB
            result_data = self.map_manager.process_unpacked_data(
                temp_path=temp_path,
                progress_callback=lambda msg, level: self.progress_updated.emit(msg, level)
            )

            # 4. 缓存图片
            if result_data['count'] >= 0:
                self.progress_updated.emit("正在缓存图片资源...", "INFO")

                # 缓存地图缩略图
                thumb_source_dir = os.path.join(temp_path, "trackThumb.rho")
                thumb_cache_dir = "data/thumbnails"
                os.makedirs(thumb_cache_dir, exist_ok=True)
                if os.path.exists(thumb_source_dir):
                    for map_id_folder in os.listdir(thumb_source_dir):
                        # 假设文件夹名就是地图ID
                        thumb_path = os.path.join(thumb_source_dir, map_id_folder, "xt_trackThumb.png")
                        if os.path.exists(thumb_path):
                            shutil.copy2(thumb_path, os.path.join(thumb_cache_dir, f"{map_id_folder}.png"))

                # 缓存主题图标
                theme_icon_source_dir = os.path.join(temp_path, "dialog2_selectTrackEx.rho")
                theme_icon_cache_dir = "data/theme_icons"
                os.makedirs(theme_icon_cache_dir, exist_ok=True)
                if os.path.exists(theme_icon_source_dir):
                    for icon_file in os.listdir(theme_icon_source_dir):
                        if icon_file.endswith("_1.png"):
                            theme_name = icon_file[:-6]
                            shutil.copy2(os.path.join(theme_icon_source_dir, icon_file),
                                         os.path.join(theme_icon_cache_dir, f"{theme_name}.png"))
                self.progress_updated.emit("图片资源缓存完成。", "INFO")

            self.import_finished.emit(result_data)

        except Exception as e:
            import traceback
            error_details = f"{str(e)}\n\n{traceback.format_exc()}"
            self.progress_updated.emit(f"导入过程中发生严重错误: {error_details}", "ERROR")
            self.import_finished.emit({'count': -1, 'themes_data': {}})
        finally:
            # 5. 最后清理临时文件
            if os.path.exists(temp_path):
                shutil.rmtree(temp_path)
                self.progress_updated.emit(f"已清理临时目录", "INFO")