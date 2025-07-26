# 文件名: ui/views/map_manager/widget.py

import sys, os, shutil, csv, json, ctypes
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

try:
    from PIL import Image, ImageDraw, ImageFont
    import io
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from core.db_manager import DBManager
from core.language_service_placeholder import i18n
# 从同级目录导入拆分后的组件
from .thread import MapImportThread
from .dialogs import AdvancedFilterDialog
from .delegates import ThumbnailDelegate
from .map_card import MapCardWidget
# 新增: 从上级目录导入工具
from utils.path_finder import find_kartrider_path, find_unpacker_path


class MapManagerWidget(QWidget):
    status_updated = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DBManager()
        self.map_data = {}
        self.advanced_filters = {}
        self.current_map_pool = "默认地图池"
        self.current_selections = set()
        self._setup_ui()
        self._connect_signals()
        self.load_and_display_data()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self);
        splitter = QSplitter(Qt.Orientation.Horizontal)
        left_panel = QWidget();
        left_layout = QVBoxLayout(left_panel)
        self.theme_tree = QTreeView();
        self.theme_tree.setHeaderHidden(True)
        self.theme_model = QStandardItemModel();
        self.theme_tree.setModel(self.theme_model)
        self.theme_tree.setIconSize(QSize(48, 48));
        font = QFont();
        font.setPointSize(12);
        self.theme_tree.setFont(font)
        left_layout.addWidget(QLabel("地图主题"));
        left_layout.addWidget(self.theme_tree)

        right_panel = QWidget();
        right_layout = QVBoxLayout(right_panel)
        top_bar_layout = QHBoxLayout()
        self.scan_button = QPushButton("扫描游戏");
        self.adv_filter_button = QPushButton("高级筛选");
        self.clear_button = QPushButton("清除地图库")
        self.view_switch_button = QPushButton("切换为表格视图")
        self.search_edit = QLineEdit();
        self.search_edit.setPlaceholderText("搜索地图名称或ID...")
        top_bar_layout.addWidget(self.scan_button);
        top_bar_layout.addWidget(self.adv_filter_button);
        top_bar_layout.addWidget(self.clear_button)
        top_bar_layout.addStretch();
        top_bar_layout.addWidget(QLabel("搜索:"));
        top_bar_layout.addWidget(self.search_edit);
        top_bar_layout.addWidget(self.view_switch_button)

        mid_bar_layout = QHBoxLayout()
        self.map_pool_combo = QComboBox();
        self.new_pool_btn = QPushButton("新建");
        self.del_pool_btn = QPushButton("删除")
        self.export_button = QPushButton("导出当前地图池...")
        mid_bar_layout.addWidget(QLabel("当前地图池:"));
        mid_bar_layout.addWidget(self.map_pool_combo, 1);
        mid_bar_layout.addWidget(self.new_pool_btn);
        mid_bar_layout.addWidget(self.del_pool_btn);
        mid_bar_layout.addStretch()
        mid_bar_layout.addWidget(self.export_button)

        bottom_bar_layout = QHBoxLayout()
        self.speed_checkbox = QCheckBox("竞速");
        self.item_checkbox = QCheckBox("道具");
        self.other_checkbox = QCheckBox("其他")
        self.speed_checkbox.setChecked(True);
        self.item_checkbox.setChecked(True);
        self.other_checkbox.setChecked(True)
        self.select_all_btn = QPushButton("全选");
        self.deselect_all_btn = QPushButton("全不选");
        self.invert_select_btn = QPushButton("反选")
        bottom_bar_layout.addWidget(self.speed_checkbox);
        bottom_bar_layout.addWidget(self.item_checkbox);
        bottom_bar_layout.addWidget(self.other_checkbox)
        bottom_bar_layout.addStretch()
        bottom_bar_layout.addWidget(self.select_all_btn);
        bottom_bar_layout.addWidget(self.deselect_all_btn);
        bottom_bar_layout.addWidget(self.invert_select_btn)

        self.card_view = QListWidget()
        self.card_view.setViewMode(QListWidget.ViewMode.IconMode);
        self.card_view.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.card_view.setMovement(QListWidget.Movement.Static);
        self.card_view.setIconSize(QSize(222, 180))
        self.card_view.setSpacing(10);
        self.card_view.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

        self.table_view = QTableWidget()
        self.table_view.setColumnCount(11)
        self.table_view.setHorizontalHeaderLabels(
            ["", "缩略图", "ID", "显示名称", "简中名", "繁中名", "韩文名", "难度", "标签", "类型"])
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows);
        self.table_view.verticalHeader().setDefaultSectionSize(76);
        self.table_view.setColumnWidth(1, 130)
        self.table_view.setItemDelegateForColumn(1, ThumbnailDelegate(self))
        self.table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table_view.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self.view_stack = QStackedWidget();
        self.view_stack.addWidget(self.card_view);
        self.view_stack.addWidget(self.table_view)

        right_layout.addLayout(top_bar_layout);
        right_layout.addLayout(mid_bar_layout);
        right_layout.addLayout(bottom_bar_layout)
        right_layout.addWidget(self.view_stack)
        splitter.addWidget(left_panel);
        splitter.addWidget(right_panel);
        splitter.setStretchFactor(1, 4)
        main_layout.addWidget(splitter)

    def _connect_signals(self):
        self.view_switch_button.clicked.connect(self.switch_view)
        self.scan_button.clicked.connect(self.start_map_import)
        self.adv_filter_button.clicked.connect(self.open_advanced_filter)
        self.clear_button.clicked.connect(self.clear_map_library)
        self.export_button.clicked.connect(self.export_selected_maps)
        self.search_edit.textChanged.connect(self.filter_table)
        self.theme_tree.selectionModel().currentChanged.connect(self.filter_table)
        self.speed_checkbox.stateChanged.connect(self.filter_table)
        self.item_checkbox.stateChanged.connect(self.filter_table)
        self.other_checkbox.stateChanged.connect(self.filter_table)
        self.map_pool_combo.currentTextChanged.connect(self.load_map_pool)
        self.new_pool_btn.clicked.connect(self.new_map_pool)
        self.del_pool_btn.clicked.connect(self.delete_map_pool)
        self.select_all_btn.clicked.connect(self.select_all_visible)
        self.deselect_all_btn.clicked.connect(self.deselect_all_visible)
        self.invert_select_btn.clicked.connect(self.invert_selection_visible)

    def load_and_display_data(self):
        self.map_data = self.db.get_all_maps_structured_by_theme()
        self.theme_model.clear()

        selected_item = QStandardItem("★ 已选地图")
        selected_item.setData("selected", Qt.ItemDataRole.UserRole)
        self.theme_model.appendRow(selected_item)

        all_item = QStandardItem("所有主题")
        all_item.setData("all", Qt.ItemDataRole.UserRole)
        self.theme_model.appendRow(all_item)

        for theme_code in sorted(self.map_data.keys()):
            icon_path = f"data/theme_icons/{theme_code}.png"
            theme_display_name = i18n.get_theme_name(theme_code, fallback=theme_code.capitalize())
            theme_item = QStandardItem(theme_display_name)
            if os.path.exists(icon_path):
                theme_item.setIcon(QIcon(icon_path))
            theme_item.setData(theme_code, Qt.ItemDataRole.UserRole)
            self.theme_model.appendRow(theme_item)

        self.load_map_pool_list()
        self.theme_tree.setCurrentIndex(self.theme_model.index(1, 0))

    def filter_table(self):
        is_card_view = self.view_stack.currentIndex() == 0
        view = self.card_view if is_card_view else self.table_view
        view.blockSignals(True)
        if is_card_view: self.card_view.clear()
        else: self.table_view.setRowCount(0); self.table_view.setHorizontalHeaderLabels(["", "缩略图", "ID", "显示名称", "简中名", "繁中名", "韩文名", "难度", "标签", "类型"])
        maps_to_display = self._get_filtered_map_list()
        for map_item, is_reverse in maps_to_display:
            if is_card_view: self._add_map_to_card_view(map_item, is_reverse)
            else: self._add_map_to_table_view(map_item, is_reverse)
        view.blockSignals(False)

    def _get_filtered_map_list(self):
        selected_index = self.theme_tree.currentIndex()
        selected_theme = selected_index.data(Qt.ItemDataRole.UserRole) if selected_index.isValid() else "all"
        search_text = self.search_edit.text().lower()  # 新增: 获取搜索文本

        maps_to_process = []
        if selected_theme == "selected":
            all_maps_flat = [m for theme_maps in self.map_data.values() for m in theme_maps]
            for map_item in all_maps_flat:
                map_id = map_item['id']
                if map_id in self.current_selections:
                    maps_to_process.append((map_item, False))
                if map_item.get('has_reverse_mode') and f"{map_id}_rvs" in self.current_selections:
                    maps_to_process.append((map_item, True))
        else:
            source_list = []
            if selected_theme == "all":
                for theme_maps in self.map_data.values(): source_list.extend(theme_maps)
            else:
                source_list = self.map_data.get(selected_theme, [])

            for map_item in source_list:
                maps_to_process.append((map_item, False))
                if map_item.get('has_reverse_mode'):
                    maps_to_process.append((map_item, True))

        final_list = []
        show_types = {'竞速': self.speed_checkbox.isChecked(), '道具': self.item_checkbox.isChecked(),
                      '其他': self.other_checkbox.isChecked()}

        for map_item, is_reverse in maps_to_process:
            # 新增: 搜索逻辑
            if search_text:
                if not (search_text in map_item['id'].lower() or
                        search_text in (map_item.get('name_cn') or '').lower() or
                        search_text in (map_item.get('name_tw') or '').lower() or
                        search_text in (map_item.get('name_kr') or '').lower() or
                        search_text in i18n.get_map_name_with_fallback(map_item).lower()):
                    continue

            if not show_types.get(map_item['game_type'], show_types['其他']):
                continue

            should_display = True
            if self.advanced_filters:
                if self.advanced_filters.get('no_cn_name') and not map_item['name_cn']:
                    pass
                elif self.advanced_filters.get('no_cn_name'):
                    should_display = False
                if self.advanced_filters.get('no_tw_name') and not map_item['name_tw']:
                    pass
                elif self.advanced_filters.get('no_tw_name'):
                    should_display = False
                if self.advanced_filters.get('no_kr_name') and not map_item['name_kr']:
                    pass
                elif self.advanced_filters.get('no_kr_name'):
                    should_display = False
                if self.advanced_filters.get('no_difficulty') and map_item['difficulty'] is None:
                    pass
                elif self.advanced_filters.get('no_difficulty'):
                    should_display = False

            if should_display:
                final_list.append((map_item, is_reverse))

        return final_list

    def _add_map_to_card_view(self, map_item, is_reverse):
        map_display_id = map_item['id'] + ("_rvs" if is_reverse else "")
        card = MapCardWidget(map_item, is_reverse)
        card.selection_changed.connect(self.on_map_selection_changed)
        if map_display_id in self.current_selections:
            card.set_checked(True)
        list_item = QListWidgetItem(self.card_view)
        list_item.setSizeHint(card.sizeHint())
        self.card_view.addItem(list_item)
        self.card_view.setItemWidget(list_item, card)

    def _add_map_to_table_view(self, map_item, is_reverse):
        row = self.table_view.rowCount()
        self.table_view.insertRow(row)
        map_display_id = map_item['id'] + ("_rvs" if is_reverse else "")

        # 复选框
        chk_item_widget = QWidget()
        chk_layout = QHBoxLayout(chk_item_widget)
        chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chk_layout.setContentsMargins(0, 0, 0, 0)
        checkbox = QCheckBox()
        checkbox.setChecked(map_display_id in self.current_selections)
        checkbox.toggled.connect(lambda checked, mid=map_display_id: self.on_map_selection_changed(mid, checked))
        chk_layout.addWidget(checkbox)
        self.table_view.setCellWidget(row, 0, chk_item_widget)

        # 缩略图
        thumb_item = QTableWidgetItem()
        thumb_item.setData(Qt.ItemDataRole.UserRole, f"data/thumbnails/{map_item['id']}.png")
        thumb_item.setData(Qt.ItemDataRole.UserRole + 1, is_reverse)
        thumb_item.setFlags(thumb_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table_view.setItem(row, 1, thumb_item)

        # 显示名称
        display_name = i18n.get_map_name_with_fallback(map_item)
        if is_reverse:
            prefix = i18n.tr("map_prefixes.reverse")
            display_name = f"{prefix} {display_name}"

        self.table_view.setItem(row, 2, QTableWidgetItem(map_item['id']))
        self.table_view.setItem(row, 3, QTableWidgetItem(display_name))

        # 独立语言列
        cn_name = map_item.get('name_cn') or ''
        tw_name = map_item.get('name_tw') or ''
        kr_name = map_item.get('name_kr') or ''
        if is_reverse:
            cn_name = f"{i18n.tr('map_prefixes.reverse_cn')} {cn_name}" if cn_name else ""
            tw_name = f"{i18n.tr('map_prefixes.reverse_tw')} {tw_name}" if tw_name else ""
            kr_name = f"{i18n.tr('map_prefixes.reverse_kr')} {kr_name}" if kr_name else ""
        self.table_view.setItem(row, 4, QTableWidgetItem(cn_name))
        self.table_view.setItem(row, 5, QTableWidgetItem(tw_name))
        self.table_view.setItem(row, 6, QTableWidgetItem(kr_name))

        self.table_view.setItem(row, 7, QTableWidgetItem(str(map_item['difficulty'] or '')))
        tags = map_item.get('tags', [])
        self.table_view.setItem(row, 8, QTableWidgetItem(", ".join(tags)))

        # --- 核心修改: 使用i18n翻译类型码 ---
        type_display = i18n.get_map_type_name(map_item.get('game_type'))
        self.table_view.setItem(row, 9, QTableWidgetItem(type_display))

    def on_map_selection_changed(self, map_display_id, checked):
        if checked:
            self.current_selections.add(map_display_id)
        else:
            self.current_selections.discard(map_display_id)
        self.db.save_map_pool(self.current_map_pool, list(self.current_selections))
        if self.theme_tree.currentIndex().data(Qt.ItemDataRole.UserRole) == "selected":
            self.filter_table()

    def load_map_pool_list(self):
        self.map_pool_combo.blockSignals(True)
        self.map_pool_combo.clear()
        pools = self.db.get_all_map_pools()
        if not pools:
            self.db.save_map_pool("默认地图池", [])
            pools = self.db.get_all_map_pools()
        for pool in pools:
            self.map_pool_combo.addItem(pool['name'])
        self.map_pool_combo.blockSignals(False)

    def load_map_pool(self, pool_name):
        if not pool_name: return
        self.current_map_pool = pool_name
        pool_data = self.db.get_map_pool_by_name(pool_name)
        self.current_selections = set(pool_data['selected_maps']) if pool_data else set()
        self.filter_table()

    def new_map_pool(self):
        name, ok = QInputDialog.getText(self, "新建地图池", "请输入新地图池的名称:")
        if ok and name:
            self.db.save_map_pool(name, [])
            self.load_map_pool_list()
            self.map_pool_combo.setCurrentText(name)

    def delete_map_pool(self):
        pool_name = self.current_map_pool
        if pool_name == "默认地图池":
            QMessageBox.warning(self, "提示", "不能删除默认地图池。")
            return
        reply = QMessageBox.question(self, "确认删除", f"您确定要删除地图池 '{pool_name}' 吗？")
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_map_pool(pool_name)
            self.load_map_pool_list()

    def switch_view(self):
        # --- 核心修改: 修正按钮文本逻辑 ---
        is_card_view = self.view_stack.currentIndex() == 0
        if is_card_view:
            self.view_stack.setCurrentIndex(1)
            self.view_switch_button.setText("切换为卡片视图")
        else:
            self.view_stack.setCurrentIndex(0)
            self.view_switch_button.setText("切换为表格视图")
        self.filter_table()

    def select_all_visible(self):
        visible_maps_ids = {item[0]['id'] + ("_rvs" if item[1] else "") for item in self._get_filtered_map_list()}
        self.current_selections.update(visible_maps_ids)
        self.db.save_map_pool(self.current_map_pool, list(self.current_selections))
        self.filter_table()
    def deselect_all_visible(self):
        visible_maps_ids = {item[0]['id'] + ("_rvs" if item[1] else "") for item in self._get_filtered_map_list()}
        self.current_selections.difference_update(visible_maps_ids)
        self.db.save_map_pool(self.current_map_pool, list(self.current_selections))
        self.filter_table()
    def invert_selection_visible(self):
        visible_maps_ids = {item[0]['id'] + ("_rvs" if item[1] else "") for item in self._get_filtered_map_list()}
        self.current_selections.symmetric_difference_update(visible_maps_ids)
        self.db.save_map_pool(self.current_map_pool, list(self.current_selections))
        self.filter_table()

    def export_selected_maps(self):
        # --- 核心修改: 实现导出逻辑 ---
        if not self.current_selections:
            QMessageBox.warning(self, "提示", "当前地图池为空，没有可导出的地图。")
            return

        path, _ = QFileDialog.getSaveFileName(self, "导出地图池为图片", "", "PNG 图片 (*.png)")
        if not path: return

        try:
            all_maps_flat = {m['id']: m for theme_maps in self.map_data.values() for m in theme_maps}
            cards_to_render = []
            for map_display_id in sorted(list(self.current_selections)):
                is_reverse = map_display_id.endswith("_rvs")
                map_id = map_display_id.replace("_rvs", "")
                if map_id in all_maps_flat:
                    cards_to_render.append(MapCardWidget(all_maps_flat[map_id], is_reverse))

            if not cards_to_render:
                QMessageBox.warning(self, "错误", "未能生成任何地图卡片。");
                return

            cols = 5;
            rows = (len(cards_to_render) + cols - 1) // cols
            card_w, card_h = 222, 180;
            padding = 15;
            img_w = cols * card_w + (cols + 1) * padding
            img_h = rows * card_h + (rows + 1) * padding + 50  # 增加标题高度

            image = Image.new('RGB', (img_w, img_h), '#f0f0f0')
            draw = ImageDraw.Draw(image)
            # 尝试加载一个好看的字体
            try:
                font = ImageFont.truetype("msyh.ttc", 32)
            except IOError:
                font = ImageFont.load_default()

            draw.text((padding, padding), f"赛事地图池: {self.current_map_pool}", font=font, fill="black")

            for i, card_widget in enumerate(cards_to_render):
                row, col = divmod(i, cols)
                x = padding + col * (card_w + padding)
                y = 50 + padding + row * (card_h + padding)

                # 使用grab()获取控件截图，然后转换为Pillow Image
                pixmap = card_widget.grab()
                buffer = QBuffer()
                buffer.open(QBuffer.OpenModeFlag.ReadWrite)
                pixmap.save(buffer, "PNG")
                pil_img = Image.open(io.BytesIO(buffer.data()))

                image.paste(pil_img, (x, y))

            image.save(path, 'PNG')
            QMessageBox.information(self, "成功", f"地图池公告图已成功导出到:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"生成图片时发生错误: {e}")

    def start_map_import(self):
        # --- 核心修改: 实现智能路径查找 ---
        game_path = find_kartrider_path()
        if not game_path:
            self.status_updated.emit("未能自动找到游戏目录，请手动选择 (如 PopKart)", "INFO")
            game_path = QFileDialog.getExistingDirectory(self, "请选择跑跑卡丁车游戏主目录(如 PopKart)")
        if not game_path: return

        unpacker_path = find_unpacker_path()
        if not unpacker_path:
            self.status_updated.emit("未能自动找到解包工具，请手动选择 RhoUnpacker.exe", "INFO")
            unpacker_path = QFileDialog.getOpenFileName(self, "请选择RhoUnpacker.exe", "", "Executable (*.exe)")[0]
        if not unpacker_path: return

        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        if not is_admin:
            reply = QMessageBox.question(self, "权限提示",
                                         "此功能可能需要管理员权限才能访问游戏目录。\n是否尝试以管理员身份重启本程序？",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.Yes)
            if reply == QMessageBox.StandardButton.Yes:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
                QApplication.instance().quit()
                return

        self.scan_button.setEnabled(False)
        self.import_thread = MapImportThread(game_path, unpacker_path)
        self.import_thread.progress_updated.connect(self.status_updated.emit)
        self.import_thread.import_finished.connect(self.on_import_finished)
        self.import_thread.start()

    def start_map_import(self):
        # --- 更新: 实现智能路径查找和管理员权限处理 ---
        # 1. 检查管理员权限 (仅Windows)
        is_admin = False
        try:
            # os.name 在windows系统上返回 'nt'
            if os.name == 'nt':
                is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            # 在非Windows系统或发生错误时，跳过权限检查
            pass

        if os.name == 'nt' and not is_admin:
            reply = QMessageBox.question(self, "权限提示",
                                         "扫描游戏目录功能可能需要管理员权限。\n是否尝试以管理员身份重启本程序？",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.Yes)
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
                    QApplication.instance().quit()
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"提权失败: {e}")
                return

        # 2. 智能查找路径
        game_path = find_kartrider_path()
        if not game_path:
            game_path = QFileDialog.getExistingDirectory(self, "未能自动找到游戏目录，请手动选择 (如 PopKart/M01、TCGameApps/kart)")
        if not game_path: return

        unpacker_path = find_unpacker_path()
        if not unpacker_path:
            unpacker_path = QFileDialog.getOpenFileName(self, "未能自动找到解包工具，请手动选择 RhoUnpacker.exe", "",
                                                        "Executable (*.exe)")[0]
        if not unpacker_path: return

        # 3. 启动后台线程
        self.scan_button.setEnabled(False)
        self.import_thread = MapImportThread(game_path, unpacker_path)
        self.import_thread.progress_updated.connect(self.status_updated.emit)
        self.import_thread.import_finished.connect(self.on_import_finished)
        self.import_thread.start()

    def clear_map_library(self):
        reply = QMessageBox.question(self, "确认操作", "您确定要永久删除所有已导入的地图数据吗？\n此操作不可撤销。",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.db.clear_maps_table()
            if os.path.exists("data/thumbnails"): shutil.rmtree("data/thumbnails")
            if os.path.exists("data/theme_icons"): shutil.rmtree("data/theme_icons")
            QMessageBox.information(self, "完成", "地图库已成功清空。")
            self.load_and_display_data()

    def open_advanced_filter(self):
        dialog = AdvancedFilterDialog(self)
        if dialog.exec():
            self.advanced_filters = dialog.get_selected_filters()
            self.filter_table()

    def on_import_finished(self, result_data):
        count = result_data['count']
        themes_data = result_data.get('themes_data', {})

        if count >= 0:
            QMessageBox.information(self, "完成", f"地图库更新完成，共处理 {count} 个地图ID。")
            new_themes = i18n.find_untranslated_themes(themes_data.keys())
            if new_themes:
                new_themes_str = ", ".join(new_themes)
                reply = QMessageBox.question(self, "发现新主题",
                                             f"发现了 {len(new_themes)} 个新的地图主题:\n{new_themes_str}\n\n"
                                             "是否要将它们的默认中文名添加到您的翻译文件中？",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                             QMessageBox.StandardButton.Yes)
                if reply == QMessageBox.StandardButton.Yes:
                    i18n.update_theme_translations(themes_data)
                    self.status_updated.emit("新的主题翻译已保存。", "INFO")

        self.scan_button.setEnabled(True)
        self.load_and_display_data()