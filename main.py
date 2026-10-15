import sys
from PyQt6 import QtWidgets, uic, QtCore
import pyautogui
from pynput import keyboard

# мышку в угол чтобы экстренно остановить
pyautogui.FAILSAFE = True

class AutoClickerApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            uic.loadUi("clicker.ui", self)
        except Exception as e:
            app = QtWidgets.QApplication.instance()
            error_box = QtWidgets.QMessageBox()
            error_box.setIcon(QtWidgets.QMessageBox.Icon.Critical)
            error_box.setText(f"Не удалось загрузить файл clicker.ui: {e}")
            error_box.exec()
            sys.exit(1)


        self.is_clicking = False
        self.current_index = 0
        self.max_points = 3
        self.row_count = 0
        self.interval = 0.2

        self.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

        if self.intervalLineEdit:
            self.intervalLineEdit.setText(str(self.interval))
        if self.maxLenLineEdit:
            self.maxLenLineEdit.setText(str(self.max_points))

        if hasattr(self, 'radioButton1'):
            self.radioButton1.setChecked(True)

        self.click_timer = QtCore.QTimer(self)
        self.click_timer.timeout.connect(self.perform_click)

        if hasattr(self, 'start'):
            self.start.clicked.connect(self.toggle_clicking)
        if hasattr(self, 'saveCoords'):
            self.saveCoords.clicked.connect(self.save_current_position)
        if hasattr(self, 'delSelected'):
            self.delSelected.clicked.connect(self.delete_selected_row)
        if hasattr(self, 'removeAll'):
            self.removeAll.clicked.connect(self.clear_all_rows)
        if hasattr(self, 'submit'):
            self.submit.clicked.connect(self.apply_settings)

        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
        self.keyboard_listener.start()

        self.update_status("Готов к работе. Нажмите Старт или Shift+S для сохранения.")

    def update_status(self, text):
        if hasattr(self, 'status'):
            self.status.setText(f"status: {text}")

    def toggle_clicking(self):
        self.is_clicking = not self.is_clicking
        if self.is_clicking:
            self.apply_settings()

            if hasattr(self, 'radioButton2') and self.radioButton2.isChecked():
                self.row_count = self.tableWidget.rowCount()
                if self.row_count == 0:
                    self.update_status("Ошибка: нет сохраненных точек для перебора!")
                    self.is_clicking = False
                    return

            interval_ms = int(self.interval * 1000)
            self.click_timer.start(interval_ms)

            if hasattr(self, 'start'):
                self.start.setText("Стоп")
            self.update_status("Автокликер запущен...")
        else:
            self.click_timer.stop()
            if hasattr(self, 'start'):
                self.start.setText("Старт/Стоп")
            self.update_status("Автокликер остановлен.")

    def perform_click(self):
        try:
            if self.radioButton1.isChecked():
                pyautogui.click()

            elif self.radioButton2.isChecked():
                if self.current_index >= self.row_count:
                    self.current_index = 0

                x_item = self.tableWidget.item(self.current_index, 0)
                y_item = self.tableWidget.item(self.current_index, 1)
                x = int(x_item.text())
                y = int(y_item.text())
                pyautogui.click(x, y)
                self.current_index += 1
        except Exception as e:
            self.update_status(f"Ошибка клика: {str(e)}")
            self.toggle_clicking()

    def save_current_position(self):
        pos = pyautogui.position()
        current_rows = self.tableWidget.rowCount()

        if current_rows >= self.max_points:
            self.tableWidget.removeRow(0)
            current_rows = self.tableWidget.rowCount()

        self.tableWidget.insertRow(current_rows)
        self.tableWidget.setItem(current_rows, 0, QtWidgets.QTableWidgetItem(str(pos.x)))
        self.tableWidget.setItem(current_rows, 1, QtWidgets.QTableWidgetItem(str(pos.y)))
        self.row_count = current_rows

        self.update_status(f"Сохранена позиция: X={pos.x}, Y={pos.y}")

    def delete_selected_row(self):
        selected_rows = self.tableWidget.selectionModel().selectedRows()
        if not selected_rows:
            self.update_status("Выберите строку в таблице для удаления.")
            return
        for index in sorted(selected_rows, reverse=True):
            self.tableWidget.removeRow(index.row())
        self.update_status("Выбранные координаты удалены.")

    def clear_all_rows(self):
        self.tableWidget.setRowCount(0)
        self.current_index = 0
        self.update_status("Все сохраненные координаты очищены.")

    def apply_settings(self):
        try:
            if self.intervalLineEdit:
                val = float(self.intervalLineEdit.text())
                if val >= 0:
                    self.interval = val
            if self.maxLenLineEdit:
                val = int(self.maxLenLineEdit.text())
                if val > 0:
                    self.max_points = val
            self.update_status(f"Настройки применены. Интервал: {self.interval}с, Макс. точек: {self.max_points}")
        except ValueError:
            self.update_status("Ошибка: проверьте правильность введенных чисел в настройках.")

    def on_key_press(self, key):
        try:
            if key == keyboard.Key.ctrl or key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.toggle_clicking()
            if key == keyboard.Key.alt or key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                self.save_current_position()
        except Exception as e:
            self.update_status(str(e))

    def handle_global_save(self):
        QtCore.QMetaObject.invokeMethod(self, "save_current_position", QtCore.Qt.ConnectionType.QueuedConnection)

    def closeEvent(self, event):
        try:
            self.keyboard_listener.stop()
        except Exception:
            pass
        event.accept()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = AutoClickerApp()
    window.show()
    sys.exit(app.exec())