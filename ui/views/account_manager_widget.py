# 文件名: ui/views/account_manager_widget.py (V3.1 - 优化编辑功能)

import sys
import csv
import random
import string
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QDialog, QLineEdit, QFormLayout, QDialogButtonBox, QMessageBox,
    QHeaderView, QSpinBox, QComboBox, QLabel, QFileDialog, QToolButton, QCheckBox
)
from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import QAction

from core.db_manager import DBManager
from core.auth_manager import AuthManager

# ... (所有常量和对话框类都保持不变, 此处省略) ...
CREDENTIAL_REGEX = QRegularExpression(r"^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{}|;':\",./<>?]+$")
ERROR_STYLE_SHEET = "border: 1px solid red;"
ERROR_TEXT_COLOR = "color: red;"
ALLOWED_PUNCTUATION_REGEX = r"!@#$%^&*()_+\-="
ALLOWED_PUNCTUATION_DISPLAY = "!@#$%^()_+-="
INVALID_TOOLTIP_TEXT = f"只能包含字母、数字以及标点: {ALLOWED_PUNCTUATION_DISPLAY}"


class SingleCreationResultDialog(QDialog):
    def __init__(self, account_data, parent=None):
        super().__init__(parent)
        self.account_data = account_data;
        self.setWindowTitle("创建成功")
        layout = QVBoxLayout(self);
        self.full_info_text = self._build_full_info_text()
        self.info_label = QLabel();
        self.info_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.show_pass_checkbox = QCheckBox("显示明文密码")
        if not self.account_data.get("password"): self.show_pass_checkbox.setEnabled(False)
        self.show_pass_checkbox.toggled.connect(self.toggle_password_visibility)
        button_layout = QHBoxLayout();
        self.copy_btn = QPushButton("复制信息");
        self.ok_btn = QPushButton("确定")
        button_layout.addStretch();
        button_layout.addWidget(self.copy_btn);
        button_layout.addWidget(self.ok_btn)
        layout.addWidget(self.info_label);
        layout.addWidget(self.show_pass_checkbox, 0, Qt.AlignmentFlag.AlignRight);
        layout.addLayout(button_layout)
        self.copy_btn.clicked.connect(self.copy_to_clipboard);
        self.ok_btn.clicked.connect(self.accept)
        self.toggle_password_visibility(False)

    def _build_full_info_text(self):
        text = f"成功创建新条目！\n--------------------\n"
        if self.account_data.get('display_name'): text += f"选手昵称: {self.account_data['display_name']}\n"
        if self.account_data.get('ingame_id'): text += f"游戏ID: {self.account_data['ingame_id']}\n"
        if self.account_data.get('username'): text += f"登录账号: {self.account_data['username']}\n"
        if self.account_data.get('password'): text += f"登录密码: {self.account_data['password']}\n"
        return text

    def toggle_password_visibility(self, checked):
        display_text = self.full_info_text
        if not checked and self.account_data.get("password"): display_text = display_text.replace(
            self.account_data["password"], "********")
        self.info_label.setText(display_text)

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard();
        clipboard.setText(self.full_info_text)
        QMessageBox.information(self, "已复制", "账号信息已复制到剪贴板。")


class AccountDialog(QDialog):
    def __init__(self, account_data=None, parent=None):
        super().__init__(parent)
        self.account_data = account_data;
        self.setWindowTitle("编辑选手/账号" if account_data else "添加新选手/账号")
        layout = QFormLayout(self);
        layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.username_edit = QLineEdit(account_data['username'] if account_data and account_data['username'] else "")
        self.ingame_id_edit = QLineEdit(account_data['ingame_id'] if account_data and account_data['ingame_id'] else "")
        self.display_name_edit = QLineEdit(
            account_data['display_name'] if account_data and account_data['display_name'] else "")
        self.password_edit = QLineEdit();
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setInputMethodHints(
            Qt.InputMethodHint.ImhNoPredictiveText | Qt.InputMethodHint.ImhSensitiveData)
        self.toggle_password_btn = QToolButton(text="显示");
        self.toggle_password_btn.setCheckable(True)
        self.toggle_password_btn.toggled.connect(self.on_toggle_password_visibility)
        self.random_pass_btn = QPushButton("随机生成");
        self.random_pass_btn.clicked.connect(self.generate_random_password)
        password_layout = QHBoxLayout();
        password_layout.setContentsMargins(0, 0, 0, 0)
        password_layout.addWidget(self.password_edit, 1);
        password_layout.addWidget(self.toggle_password_btn);
        password_layout.addWidget(self.random_pass_btn)
        password_label_text = "新密码 (留空则不修改):" if account_data else "密码 (可留空):"
        password_label = QLabel(password_label_text)
        self.username_error_label = QLabel(INVALID_TOOLTIP_TEXT);
        self.username_error_label.setStyleSheet(ERROR_TEXT_COLOR);
        self.username_error_label.hide()
        self.password_error_label = QLabel(INVALID_TOOLTIP_TEXT);
        self.password_error_label.setStyleSheet(ERROR_TEXT_COLOR);
        self.password_error_label.hide()
        username_widget = QWidget();
        username_layout = QVBoxLayout(username_widget);
        username_layout.setContentsMargins(0, 0, 0, 0)
        username_layout.addWidget(self.username_edit);
        username_layout.addWidget(self.username_error_label)
        password_widget = QWidget();
        password_v_layout = QVBoxLayout(password_widget);
        password_v_layout.setContentsMargins(0, 0, 0, 0)
        password_v_layout.addLayout(password_layout);
        password_v_layout.addWidget(self.password_error_label)
        layout.addRow("游戏ID:", self.ingame_id_edit);
        layout.addRow("选手昵称:", self.display_name_edit)
        layout.addRow("登录账号 (可留空):", username_widget);
        layout.addRow(password_label, password_widget)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept);
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        self.username_edit.textChanged.connect(self._validate_inputs);
        self.password_edit.textChanged.connect(self._validate_inputs)
        self._validate_inputs()

    def _validate_inputs(self):
        username = self.username_edit.text();
        password = self.password_edit.text()
        is_username_valid = not (username and not CREDENTIAL_REGEX.match(username).hasMatch())
        is_password_valid = not (password and not CREDENTIAL_REGEX.match(password).hasMatch())
        self.username_edit.setStyleSheet(ERROR_STYLE_SHEET if not is_username_valid else "");
        self.username_error_label.setVisible(not is_username_valid)
        self.password_edit.setStyleSheet(ERROR_STYLE_SHEET if not is_password_valid else "");
        self.password_error_label.setVisible(not is_password_valid)
        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok);
        ok_button.setEnabled(is_username_valid and is_password_valid)

    def on_toggle_password_visibility(self, checked):
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)
        self.toggle_password_btn.setText("隐藏" if checked else "显示")

    def generate_random_password(self):
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8));
        self.password_edit.setText(password)

    def get_data(self):
        return {"id": self.account_data['id'] if self.account_data else None,
                "username": self.username_edit.text().strip(), "ingame_id": self.ingame_id_edit.text().strip(),
                "display_name": self.display_name_edit.text().strip(), "password": self.password_edit.text()}


class BulkCreationResultDialog(QDialog):
    def __init__(self, new_accounts_data, parent=None):
        super().__init__(parent)
        self.new_accounts_data = new_accounts_data;
        self.setWindowTitle("批量创建成功");
        self.setMinimumSize(500, 300)
        layout = QVBoxLayout(self)
        info_label = QLabel("<b>请立即复制或导出以下新账号信息。关闭此窗口后，密码将无法再次查看。</b>");
        info_label.setWordWrap(True)
        self.table = QTableWidget();
        self.table.setColumnCount(2);
        self.table.setHorizontalHeaderLabels(["登录账号", "密码"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.show_pass_checkbox = QCheckBox("显示明文密码");
        self.show_pass_checkbox.toggled.connect(self.toggle_password_visibility_in_table)
        self.populate_table()
        button_layout = QHBoxLayout();
        self.copy_btn = QPushButton("复制为文本");
        self.export_csv_btn = QPushButton("导出为CSV");
        self.close_btn = QPushButton("关闭")
        button_layout.addStretch();
        button_layout.addWidget(self.copy_btn);
        button_layout.addWidget(self.export_csv_btn);
        button_layout.addWidget(self.close_btn)
        layout.addWidget(info_label);
        layout.addWidget(self.table);
        layout.addWidget(self.show_pass_checkbox, 0, Qt.AlignmentFlag.AlignRight);
        layout.addLayout(button_layout)
        self.copy_btn.clicked.connect(self.copy_to_clipboard);
        self.export_csv_btn.clicked.connect(self.export_to_csv);
        self.close_btn.clicked.connect(self.accept)

    def populate_table(self, show_plaintext=False):
        self.table.setRowCount(len(self.new_accounts_data))
        for row, account in enumerate(self.new_accounts_data):
            self.table.setItem(row, 0, QTableWidgetItem(account['username']))
            self.table.setItem(row, 1, QTableWidgetItem(account['password'] if show_plaintext else '********'))

    def toggle_password_visibility_in_table(self, checked):
        self.populate_table(show_plaintext=checked)

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard();
        text = "登录账号,密码\n"
        for account in self.new_accounts_data: text += f"{account['username']},{account['password']}\n"
        clipboard.setText(text);
        QMessageBox.information(self, "成功", "账号信息已复制到剪贴板。")

    def export_to_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出为CSV", "", "CSV Files (*.csv)")
        if path:
            try:
                with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f);
                    writer.writerow(['Username', 'Password'])
                    for acc in self.new_accounts_data: writer.writerow([acc['username'], acc['password']])
                QMessageBox.information(self, "成功", f"新账号列表已成功导出到 {path}")
            except Exception as e:
                QMessageBox.warning(self, "导出失败", str(e))


class BulkCreateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("批量创建账号")
        layout = QFormLayout(self)
        layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.count_spinbox = QSpinBox();
        self.count_spinbox.setRange(1, 100);
        self.count_spinbox.setValue(8)
        self.prefix_edit = QLineEdit("Player");
        self.password_combo = QComboBox();
        self.password_combo.addItems(["统一密码", "随机密码"])
        self.password_edit = QLineEdit();
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setInputMethodHints(
            Qt.InputMethodHint.ImhNoPredictiveText | Qt.InputMethodHint.ImhSensitiveData)
        self.toggle_password_btn = QToolButton(text="显示");
        self.toggle_password_btn.setCheckable(True)
        self.toggle_password_btn.toggled.connect(self.on_toggle_password_visibility)
        password_layout = QHBoxLayout();
        password_layout.setContentsMargins(0, 0, 0, 0)
        password_layout.addWidget(self.password_edit);
        password_layout.addWidget(self.toggle_password_btn)
        self.prefix_error_label = QLabel(INVALID_TOOLTIP_TEXT);
        self.prefix_error_label.setStyleSheet(ERROR_TEXT_COLOR);
        self.prefix_error_label.hide()
        self.password_error_label = QLabel(INVALID_TOOLTIP_TEXT);
        self.password_error_label.setStyleSheet(ERROR_TEXT_COLOR);
        self.password_error_label.hide()
        prefix_widget = QWidget();
        prefix_layout = QVBoxLayout(prefix_widget);
        prefix_layout.setContentsMargins(0, 0, 0, 0);
        prefix_layout.addWidget(self.prefix_edit);
        prefix_layout.addWidget(self.prefix_error_label)
        password_widget = QWidget();
        password_v_layout = QVBoxLayout(password_widget);
        password_v_layout.setContentsMargins(0, 0, 0, 0);
        password_v_layout.addLayout(password_layout);
        password_v_layout.addWidget(self.password_error_label)
        layout.addRow("创建数量:", self.count_spinbox);
        layout.addRow("账号前缀:", prefix_widget)
        layout.addRow("密码模式:", self.password_combo);
        layout.addRow("统一密码 (若选择):", password_widget)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept);
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        self.prefix_edit.textChanged.connect(self._validate_inputs);
        self.password_edit.textChanged.connect(self._validate_inputs)
        self.password_combo.currentTextChanged.connect(self._validate_inputs);
        self._validate_inputs()

    def on_toggle_password_visibility(self, checked):
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)
        self.toggle_password_btn.setText("隐藏" if checked else "显示")

    def _validate_inputs(self):
        prefix = self.prefix_edit.text();
        password = self.password_edit.text()
        password_mode_is_uniform = self.password_combo.currentText() == "统一密码"
        is_prefix_valid = not (prefix and not CREDENTIAL_REGEX.match(prefix).hasMatch())
        is_password_valid = True
        if password_mode_is_uniform and password:
            if not CREDENTIAL_REGEX.match(password).hasMatch(): is_password_valid = False
        self.prefix_error_label.setVisible(not is_prefix_valid);
        self.prefix_edit.setStyleSheet(ERROR_STYLE_SHEET if not is_prefix_valid else "")
        self.password_error_label.setVisible(not is_password_valid);
        self.password_edit.setStyleSheet(ERROR_STYLE_SHEET if not is_password_valid else "")
        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setEnabled(is_prefix_valid and is_password_valid)

    def get_settings(self):
        return {"count": self.count_spinbox.value(), "prefix": self.prefix_edit.text(),
                "password_mode": self.password_combo.currentText(), "password": self.password_edit.text()}


class AccountManagerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DBManager()
        self.auth = AuthManager()
        self._setup_ui()
        self._connect_signals()
        self.refresh_table()

    def _setup_ui(self):
        # ... (此方法代码不变) ...
        main_layout = QVBoxLayout(self);
        self.table = QTableWidget()
        self.table.setColumnCount(4);
        self.table.setHorizontalHeaderLabels(["ID", "登录账号", "游戏ID", "选手昵称"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        button_layout = QHBoxLayout();
        self.add_btn = QPushButton("添加选手...");
        self.edit_btn = QPushButton("编辑选中...")
        self.delete_btn = QPushButton("删除选中");
        self.bulk_create_btn = QPushButton("批量创建账号...")
        self.export_btn = QPushButton("导出为CSV...")
        button_layout.addWidget(self.add_btn);
        button_layout.addWidget(self.edit_btn);
        button_layout.addWidget(self.delete_btn)
        button_layout.addStretch();
        button_layout.addWidget(self.bulk_create_btn);
        button_layout.addWidget(self.export_btn)
        main_layout.addWidget(self.table);
        main_layout.addLayout(button_layout)

    def _connect_signals(self):
        # ... (此方法代码不变) ...
        self.add_btn.clicked.connect(self.add_account);
        self.edit_btn.clicked.connect(self.edit_account)
        self.delete_btn.clicked.connect(self.delete_account);
        self.bulk_create_btn.clicked.connect(self.bulk_create_accounts)
        self.export_btn.clicked.connect(self.export_to_csv)

    def refresh_table(self):
        # ... (此方法代码不变) ...
        self.table.setRowCount(0);
        accounts = self.db.get_all_accounts()
        for row, account in enumerate(accounts):
            self.table.insertRow(row);
            self.table.setItem(row, 0, QTableWidgetItem(str(account['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(account['username'] or ''));
            self.table.setItem(row, 2, QTableWidgetItem(account['ingame_id'] or ''))
            self.table.setItem(row, 3, QTableWidgetItem(account['display_name'] or ''))
        self.table.resizeColumnsToContents()

    def add_account(self):
        # ... (此方法代码不变) ...
        dialog = AccountDialog(parent=self)
        if dialog.exec():
            data = dialog.get_data()
            if not data['ingame_id'] and not data['display_name'] and not data['username']:
                QMessageBox.warning(self, "创建失败", "“登录账号”、“游戏ID”和“选手昵称”至少需要填写一项。");
                return
            if data['username'] and not data['password']:
                QMessageBox.warning(self, "创建失败", "如果填写了“登录账号”，则“密码”不能为空（可随机生成）。");
                return
            if data['username'] and data['password']:
                user_id = self.auth.create_account(data['username'], data['password'], data['ingame_id'],
                                                   data['display_name'])
            else:
                user_id = self.db.create_account(None, None, None, data['ingame_id'], data['display_name'])
            if user_id:
                result_dialog = SingleCreationResultDialog(data, self);
                result_dialog.exec()
                self.refresh_table()
            else:
                QMessageBox.warning(self, "创建失败", "创建失败，登录账号可能已存在。")

    # --- 核心修改部分 ---
    def edit_account(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先选择一个要编辑的选手。")
            return

        row = selected_rows[0].row()
        # 使用ID作为唯一标识符进行查找，确保能选中任何条目
        account_id = int(self.table.item(row, 0).text())
        account_data = self.db.get_account_by_id(account_id)

        if not account_data:
            QMessageBox.critical(self, "严重错误", "无法在数据库中找到选中的选手信息。")
            return

        dialog = AccountDialog(account_data, parent=self)
        if dialog.exec():
            data = dialog.get_data()

            # 校验规则与添加时保持一致
            if not data['ingame_id'] and not data['display_name'] and not data['username']:
                QMessageBox.warning(self, "更新失败", "“登录账号”、“游戏ID”和“选手昵称”不能同时为空。");
                return
            if data['username'] and not data['password'] and not account_data['username']:  # 仅在从无到有设置用户名时强制要求密码
                QMessageBox.warning(self, "更新失败", "首次设置“登录账号”时，“密码”不能为空。");
                return

            # 更新非密码信息
            update_success = self.db.update_account(data['id'], data['username'], data['ingame_id'],
                                                    data['display_name'])
            if not update_success:
                QMessageBox.warning(self, "错误", "更新失败，登录账号可能与其他账号冲突。")
                return

            # 如果输入了新密码，则更新密码
            if data['password']:
                self.auth.update_password(data['id'], data['password'])

            QMessageBox.information(self, "成功", "选手信息已更新。")
            self.refresh_table()

    def delete_account(self):
        # ... (此方法代码不变) ...
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows: QMessageBox.warning(self, "提示", "请先选择一个要删除的账号。"); return
        row = selected_rows[0].row()
        account_id = int(self.table.item(row, 0).text())
        username = self.table.item(row, 1).text() or self.table.item(row, 3).text()
        reply = QMessageBox.question(self, "确认删除", f"您确定要永久删除选手 '{username}' 吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_account(account_id):
                QMessageBox.information(self, "成功", "选手已删除。");
                self.refresh_table()
            else:
                QMessageBox.warning(self, "错误", "删除失败。")

    def bulk_create_accounts(self):
        # ... (此方法代码不变) ...
        dialog = BulkCreateDialog(parent=self)
        if dialog.exec():
            settings = dialog.get_settings()
            created_count = 0;
            failed_count = 0
            new_accounts_info = []
            for i in range(settings['count']):
                username = f"{settings['prefix']}{i + 1}"
                password = settings['password'] if settings['password_mode'] == "统一密码" else ''.join(
                    random.choices(string.ascii_letters + string.digits, k=8))
                if not password: QMessageBox.warning(self, "错误", "使用统一密码模式时，密码不能为空。"); return
                if self.auth.create_account(username, password):
                    created_count += 1
                    new_accounts_info.append({"username": username, "password": password})
                else:
                    failed_count += 1
            self.refresh_table()
            if new_accounts_info:
                result_dialog = BulkCreationResultDialog(new_accounts_info, self);
                result_dialog.exec()
            summary_message = f"批量创建完成。\n成功: {created_count} 个\n失败(可能因用户名重复): {failed_count} 个"
            QMessageBox.information(self, "完成", summary_message)

    def export_to_csv(self):
        # ... (此方法代码不变) ...
        accounts = self.db.get_all_accounts()
        if not accounts: QMessageBox.information(self, "提示", "当前没有账号可以导出。"); return
        path, _ = QFileDialog.getSaveFileName(self, "导出为CSV", "", "CSV Files (*.csv)")
        if path:
            try:
                with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f);
                    writer.writerow(['ID', 'Username', 'InGameID', 'DisplayName'])
                    for acc in accounts: writer.writerow(
                        [acc['id'], acc['username'], acc['ingame_id'], acc['display_name']])
                QMessageBox.information(self, "成功", f"账号列表已成功导出到 {path}")
            except Exception as e:
                QMessageBox.warning(self, "导出失败", str(e))


if __name__ == '__main__':
    # ... (测试脚本切换为使用正式数据库) ...
    app = QApplication(sys.argv)
    DBManager('data/competition.db')
    AuthManager()
    window = QWidget()
    window.setWindowTitle("账号管理模块 - 独立测试")
    window.setLayout(QVBoxLayout())
    account_widget = AccountManagerWidget()
    window.layout().addWidget(account_widget)
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())