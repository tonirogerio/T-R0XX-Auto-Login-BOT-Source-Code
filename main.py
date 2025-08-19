import sys
import os
import cv2
import json
import time
import win32gui
import win32ui
import win32con
import ctypes
import numpy as np
import psutil
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QLabel, QLineEdit, QFormLayout, QMessageBox,
                             QDialog, QTableWidget, QTableWidgetItem, QHBoxLayout,
                             QHeaderView, QSpinBox, QSpacerItem, QSizePolicy, QComboBox)
from PyQt6.QtCore import Qt
import mouse
import keyboard
from pointers import Pointers
from img_finder import ImageFinder


# Resource path for files.
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class AccountDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Accounts")
        self.setMinimumSize(600, 500)
        self.setStyleSheet("font-size: 14px; font-family: Consolas")

        self.button_style = """
                        QPushButton {
                            /* Background color of the button */
                            /*background-color: #4CAF50; /* Green */
                            /*color: Black; /* Text color */
                            /*max-width: 120px; /* Button width */
                            /*max-height: 20px; /* Button height */
                            border: 2px solid #696969; /* Border color */
                            border-radius: 4px; /* Rounded corners */
                            padding: 2px 2px; /* Padding for better spacing */
                            font-size: 12px; /* Font size */
                            font-weight: bold; /* Font weight */
                            text-align: center; /* Align text in the center */
                            text-decoration: none; /* Remove underline */
                        }

                        QPushButton:hover {
                            /* Style when the mouse hovers over the button */
                            background-color: #415fa1; /* Slightly darker green */
                            border-color: #696969; /* Match border color with background */
                        }

                        QPushButton:pressed {
                            /* Style when the button is pressed */
                            background-color: #F4A460; /* Even darker green */
                            border-color: #696969; /* Match border color */
                            color: #d4d4d4; /* Change text color */
                        }"""

        self.server_list = ["Light in the Darkness", "All Stars", "Tiger Fish", "Giant Sky Medal", "Wild Wave(EE)",
                            "Blue Ice", "White Horse [NEW]"]
        self.pos = ["Left", "Center", "Right"]

        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Tabela de contas
        self.table = QTableWidget(0, 6)  # 0 linhas, 6 colunas (Select, ID, Login, Senha, Posição, Server)
        self.table.setHorizontalHeaderLabels(["Select", "ID", "Login", "Password", "Position", "Server"])

        # Define o modo de redimensionamento para cada coluna
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Checkbox
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # ID
        for i in range(2, 6):  # Demais colunas
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        # Define larguras fixas para checkbox e ID
        self.table.setColumnWidth(0, 60)  # Checkbox
        self.table.setColumnWidth(1, 40)  # ID

        layout.addWidget(self.table)

        # Form para adicionar nova conta
        form_layout = QFormLayout()

        self.login_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.position_select = QComboBox()
        self.position_select.addItems(self.pos)
        self.server_select = QComboBox()
        self.server_select.addItems(self.server_list)

        form_layout.addRow("Login:", self.login_input)
        form_layout.addRow("Password:", self.password_input)
        form_layout.addRow("Position:", self.position_select)
        form_layout.addRow("Server:", self.server_select)

        layout.addLayout(form_layout)

        # Botões
        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add Account")
        self.add_button.setStyleSheet(self.button_style)
        self.add_button.clicked.connect(self.add_account)

        self.remove_button = QPushButton("Remove Account")
        self.remove_button.setStyleSheet(self.button_style)
        self.remove_button.clicked.connect(self.remove_account)

        self.save_button = QPushButton("Save")
        self.save_button.setStyleSheet(self.button_style)
        self.save_button.clicked.connect(self.accept)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)

        # Load accounts existentes
        self.accounts = []
        self.load_accounts()
        self.update_table()

    def load_accounts(self):
        try:
            with open('accounts.json', 'r') as f:
                data = json.load(f)
                self.accounts = data.get("accounts", [])
                # Adiciona o campo selected se não existir
                for account in self.accounts:
                    if "selected" not in account:
                        account["selected"] = False
        except Exception as e:
            print(f"Erro ao carregar contas: {str(e)}")

    def save_accounts(self):
        try:
            with open('accounts.json', 'w') as f:
                json.dump({"accounts": self.accounts}, f, indent=4)
            return True
        except Exception as e:
            print(f"Erro ao salvar contas: {str(e)}")
            return False

    def update_table(self):
        # Disconnect the signal temporarily to avoid triggers during update
        try:
            self.table.cellChanged.disconnect()
        except:
            pass

        self.table.setRowCount(0)
        for i, account in enumerate(self.accounts):
            self.table.insertRow(i)

            # Adiciona checkbox
            checkbox = QTableWidgetItem()
            checkbox.setText("Log?")

            checkbox.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            checkbox.setCheckState(Qt.CheckState.Checked if account.get("selected", False) else Qt.CheckState.Unchecked)
            self.table.setItem(i, 0, checkbox)

            self.table.setItem(i, 1, QTableWidgetItem(str(i + 1)))
            self.table.setItem(i, 2, QTableWidgetItem(account["login"]))
            self.table.setItem(i, 3, QTableWidgetItem("*" * len(account["password"])))
            self.table.setItem(i, 4, QTableWidgetItem(str(account["position"])))
            self.table.setItem(i, 5, QTableWidgetItem(str(account["server"])))

        # Reconnect the signal after update
        self.table.cellChanged.connect(self.on_cell_changed)

    def on_cell_changed(self, row, column):
        """Update data when cell is edited"""
        if 0 <= row < len(self.accounts):
            try:
                item = self.table.item(row, column)
                if item is None:
                    return

                if column == 0:  # Checkbox
                    self.accounts[row]["selected"] = item.checkState() == Qt.CheckState.Checked
                    if self.save_accounts():
                        print(f"Account {row + 1} selection state updated successfully")
                    return

                new_value = item.text().strip()

                if column == 2:  # Login
                    self.accounts[row]["login"] = new_value
                elif column == 4:  # Posição
                    # Validar se a posição é válida
                    if new_value in self.pos:
                        self.accounts[row]["position"] = new_value
                    else:
                        # Restaurar valor anterior se inválido
                        item.setText(self.accounts[row]["position"])
                        QMessageBox.warning(self, "Invalid Value",
                                            f"Position must be one of the options: {', '.join(self.pos)}")
                        return
                elif column == 5:  # Server
                    # Validar se o servidor é válido
                    if new_value in self.server_list:
                        self.accounts[row]["server"] = new_value
                    else:
                        # Restaurar valor anterior se inválido
                        item.setText(self.accounts[row]["server"])
                        QMessageBox.warning(self, "Invalid Value",
                                            f"Server must be one of the options: {', '.join(self.server_list)}")
                        return

                # Save only if the change was valid
                if self.save_accounts():
                    print(f"Account {row + 1} updated and saved successfully")
                else:
                    QMessageBox.warning(self, "Error", "Error saving changes!")

            except Exception as e:
                print(f"Error editing cell: {e}")
                QMessageBox.warning(self, "Error", f"Error processing change: {str(e)}")

    def add_account(self):
        login = self.login_input.text().strip()
        password = self.password_input.text().strip()
        position = self.position_select.currentText()
        server = self.server_select.currentText()

        if not login or not password:
            QMessageBox.warning(self, "Warning", "Login and password are required!")
            return

        self.accounts.append({
            "login": login,
            "password": password,
            "position": position,
            "server": server,
            "selected": False
        })

        # Clear fields
        self.login_input.clear()
        self.password_input.clear()
        self.position_select.currentText()
        self.server_select.currentText()

        # Update table
        self.update_table()

        # Auto-save
        self.save_accounts()

    def remove_account(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Select an account to remove!")
            return

        row = selected_rows[0].row()
        if 0 <= row < len(self.accounts):
            self.accounts.pop(row)
            self.update_table()

            # Auto-save
            self.save_accounts()


class AutoLoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Start pos for mouse event, move window.
        self._start_pos = None

        self.setWindowTitle("T-R0XX Talisman Auto Login 1024*768")
        self.setWindowIcon(QIcon(resource_path("bot.ico")))
        self.setFixedSize(400, 130)

        self.button_style = """
                        QPushButton {
                            /* Background color of the button */
                            /*background-color: #4CAF50; /* Green */
                            /*color: Black; /* Text color */
                            /*max-width: 120px; /* Button width */
                            /*max-height: 20px; /* Button height */
                            border: 2px solid #696969; /* Border color */
                            border-radius: 4px; /* Rounded corners */
                            padding: 2px 2px; /* Padding for better spacing */
                            font-size: 12px; /* Font size */
                            font-weight: bold; /* Font weight */
                            text-align: center; /* Align text in the center */
                            text-decoration: none; /* Remove underline */
                        }

                        QPushButton:hover {
                            /* Style when the mouse hovers over the button */
                            background-color: #415fa1; /* Slightly darker green */
                            border-color: #696969; /* Match border color with background */
                        }

                        QPushButton:pressed {
                            /* Style when the button is pressed */
                            background-color: #F4A460; /* Even darker green */
                            border-color: #696969; /* Match border color */
                            color: #d4d4d4; /* Change text color */
                        }"""

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Form layout for settings
        form_layout = QFormLayout()

        # Client.bat field, load saved path
        with open("client_folder.txt", "r") as f:
            path = f.read()
            # print(path)

            self.client_path = QLineEdit(path)
            self.client_path.setStyleSheet("font-weight: bold; font-size: 12px; font-family: Consolas")
            self.client_path.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Button to select folder
        self.browse_button = QPushButton("Select Folder")
        self.browse_button.setFixedSize(110, 24)
        self.browse_button.setStyleSheet(self.button_style)
        self.browse_button.clicked.connect(self.browse_client_path)

        # Horizontal layout for field and button
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.client_path)

        folder_layout = QHBoxLayout()
        folder_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        folder_layout.addWidget(self.browse_button)
        folder_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        buttons_layout = QHBoxLayout()

        # Button to manage accounts
        self.accounts_button = QPushButton("Manage Accounts")
        self.accounts_button.setFixedSize(110, 30)
        self.accounts_button.setStyleSheet(self.button_style)
        self.accounts_button.clicked.connect(self.open_accounts_dialog)

        # Start Button
        self.start_button = QPushButton("Start")
        self.start_button.setFixedSize(110, 30)
        self.start_button.setStyleSheet(self.button_style)
        self.start_button.clicked.connect(self.start_auto_login)

        buttons_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        buttons_layout.addWidget(self.accounts_button)
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        client_folder_title = QLabel("Client.bat Path:")
        client_folder_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        client_folder_title.setStyleSheet("color: #FF4500; font-weight: bold; font-size: 20px; font-family: Consolas")

        # Add to form layout
        form_layout.addWidget(client_folder_title)
        form_layout.addRow(path_layout)
        form_layout.addRow(folder_layout)
        # form_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        form_layout.addRow(buttons_layout)

        # Add form layout to main layout
        layout.addLayout(form_layout)

        # List to store initial PIDs
        self.initial_pids = self.get_client_pids()

        # Load accounts
        self.accounts = []
        self.load_accounts()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._start_pos:
            self.move(event.globalPosition().toPoint() - self._start_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_pos = None
            event.accept()

    def get_client_pids(self):
        client_pids = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'].lower() == 'client.exe':
                    client_pids.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return client_pids

    def save_pids_to_json(self, pids):
        data = {"client_pids": pids}
        json_path = os.path.join(os.path.dirname(__file__), "client_pids.json")
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=4)
        return json_path

    def load_accounts(self):
        try:
            with open('accounts.json', 'r') as f:
                data = json.load(f)
                self.accounts = data.get("accounts", [])
        except Exception as e:
            print(f"Erro ao carregar contas: {str(e)}")
            self.accounts = []

    def open_accounts_dialog(self):
        dialog = AccountDialog(self)
        if dialog.exec():
            # Saves accounts and updates the local list
            if dialog.save_accounts():
                self.accounts = dialog.accounts
                QMessageBox.information(self, "Success", "Accounts saved successfully!")
            else:
                QMessageBox.warning(self, "Error", "Error saving accounts!")
        else:
            # Mesmo se cancelar, recarrega as contas para garantir sincronização
            self.load_accounts()

    def browse_client_path(self):
        from PyQt6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "Select Game Folder")
        if folder:
            client_path = os.path.normpath(os.path.join(folder, "Client.bat"))
            self.client_path.setText(client_path)
            with open("client_folder.txt", 'w') as f:
                f.write(client_path)

    def on_clients_started(self, new_pids):
        self.client_pids.extend(new_pids)
        self.save_client_pids()
        self.log_message(f"New PIDs: {new_pids}")

        failed_accounts = []
        for account in self.accounts:
            if account['login_status'] == 'failed':
                failed_accounts.append(account)

        if failed_accounts:
            self.log_message("Accounts that failed to log in:")
            for account in failed_accounts:
                self.log_message(f"- {account['login']}")
            self.log_message("No new login attempt will be made for failed accounts.")
        else:
            self.log_message("All accounts logged in successfully.")

    def check_failed_logins(self, pids):
        print("Checking accounts that may have failed to log in...")
        # Here you can implement additional logic to check
        # which accounts did not log in and try again

    class LoginThread(QThread):
        def __init__(self, pid, account, parent=None):
            super().__init__(parent)
            self.pid = pid
            self.account = account
            self.hwnd = None
            self.coords = {
                "account": (625, 395),
                "password": (613, 425),
                "passError": (515, 333),
                "ok_button": (518, 495),
                "server_1": (339,365),
                "server_2": (344,345),
                "server_3": (354,323),
                "server_4": (360,302),
                "server_5": (342,283),
                "server_6": (342,264),
                "server_7": (339,245),
                "ok_server": (557, 531),
                "pos_1": (144, 453),
                "pos_2": (465, 466),
                "pos_3": (827, 471),
                "entergame": (515, 735)
            }

        def find_window_alternative(self):
            """Alternative method to find the window when EnumWindows fails"""
            try:
                import win32gui
                import win32process

                # Tenta FindWindowEx percorrendo todas as janelas top-level
                try:
                    hwnd = win32gui.GetTopWindow(0)
                    while hwnd:
                        try:
                            _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
                            if window_pid == self.pid and win32gui.IsWindowVisible(hwnd):
                                self.hwnd = hwnd
                                return
                        except Exception:
                            pass
                        hwnd = win32gui.GetWindow(hwnd, win32con.GW_HWNDNEXT)
                except Exception:
                    pass

            except Exception as e:
                print(f"Erro no método alternativo para PID {self.pid}: {str(e)}")

        def run(self):
            try:
                # Verifica se o processo ainda existe
                if not psutil.pid_exists(self.pid):
                    print(f"Processo {self.pid} não existe mais")
                    return

                # Aguarda um pouco antes de tentar encontrar a janela
                time.sleep(2)

                # Obtém o handle da janela pelo PID com tratamento de erro robusto
                import win32gui
                import win32process

                def enum_windows_callback(hwnd, extra):
                    try:
                        if win32gui.IsWindowVisible(hwnd):
                            _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                            if found_pid == self.pid:
                                self.hwnd = hwnd
                                return False
                    except Exception:
                        pass  # Ignora erros individuais de janelas
                    return True

                # Tenta enumerar as janelas com tratamento de erro
                try:
                    win32gui.EnumWindows(enum_windows_callback, None)
                except Exception as e:
                    print(f"Erro ao enumerar janelas para PID {self.pid}: {str(e)}")
                    # Tenta uma abordagem alternativa usando FindWindow
                    self.find_window_alternative()

                if self.hwnd:
                    success = self.perform_account_login()
                    if success:
                        print(f"Login realizado com sucesso para {self.account['login']}")
                    else:
                        print(f"Falha ao fazer login para {self.account['login']}")
                else:
                    print(f"Não foi possível encontrar a janela para o PID: {self.pid}")

            except Exception as e:
                print(f"Erro ao realizar login para o PID {self.pid}: {str(e)}")

        def find_window_alternative(self):
            """Alternative method to find the window when EnumWindows fails"""
            try:
                import win32gui
                import win32process

                # Lista de possíveis títulos de janela do client
                possible_titles = ["", "Client", "client", "Game", "ver.6139", "Talisman Online"]

                for title in possible_titles:
                    try:
                        hwnd = win32gui.FindWindow(None, title)
                        if hwnd:
                            _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
                            if window_pid == self.pid:
                                self.hwnd = hwnd
                                return
                    except Exception:
                        continue

                # Se não encontrou por título, tenta FindWindowEx
                try:
                    hwnd = win32gui.GetTopWindow(0)
                    while hwnd:
                        try:
                            _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
                            if window_pid == self.pid and win32gui.IsWindowVisible(hwnd):
                                self.hwnd = hwnd
                                return
                        except Exception:
                            pass
                        hwnd = win32gui.GetWindow(hwnd, win32con.GW_HWNDNEXT)
                except Exception:
                    pass

            except Exception as e:
                print(f"Erro no método alternativo para PID {self.pid}: {str(e)}")

        def perform_account_login(self):
            try:
                # Verifica se a janela ainda existe
                if not win32gui.IsWindow(self.hwnd):
                    print(f"Janela não existe mais para {self.account['login']}")
                    return False

                # Clica na posição da conta
                mouse.left(self.hwnd, self.coords['account'][0], self.coords['account'][1])
                time.sleep(1)

                # Apaga qualquer texto existente
                for _ in range(50):
                    keyboard.send(self.hwnd, "BACKSPACE")
                time.sleep(0.5)

                # Escreve o login
                keyboard.write(self.hwnd, self.account["login"])
                time.sleep(1)

                # Campo password
                mouse.left(self.hwnd, self.coords['password'][0], self.coords['password'][1])
                time.sleep(0.5)
                keyboard.write(self.hwnd, self.account["password"])
                time.sleep(1)

                # Confirma login
                mouse.left(self.hwnd, self.coords['ok_button'][0], self.coords['ok_button'][1])
                time.sleep(2)  # Aumentado o tempo de espera

                # Verifica erro de login
                while True:
                    pointers = Pointers(self.pid)
                    login = pointers.check_login()

                    if login == 1:
                        print(f"Erro de login detectado para {self.account['login']}")
                        mouse.left(self.hwnd, self.coords['passError'][0], self.coords['passError'][1])
                        time.sleep(1)
                        return self.perform_account_login()
                    elif login == 0:
                        break

                    time.sleep(1)

                # Seleciona servidor
                server = self.account["server"]
                server_coords = {
                    "Light in the Darkness": 'server_1',
                    "All Stars": 'server_2',
                    "Tiger Fish": 'server_3',
                    "Giant Sky Medal": 'server_4',
                    "Wild Wave(EE)": 'server_5',
                    "Blue Ice": 'server_6',
                    "White Horse [NEW]": 'server_7'
                }

                if server in server_coords:
                    mouse.left(self.hwnd, self.coords[server_coords[server]][0], self.coords[server_coords[server]][1])
                    time.sleep(0.5)

                mouse.left(self.hwnd, self.coords['ok_server'][0], self.coords['ok_server'][1])
                time.sleep(5)

                # Checa disconnect depois de entrar no servidor
                while True:
                    pointers = Pointers(self.pid)
                    login = pointers.check_login()

                    if login == 1:
                        print(f"Disconnect depois de selecionar o server {self.account['login']}")
                        mouse.left(self.hwnd, self.coords['passError'][0], self.coords['passError'][1])
                        time.sleep(1)
                        return self.perform_account_login()
                    elif login == 0:
                        break

                    time.sleep(1)

                # Queue check - aguarda indefinidamente até sair da fila
                finder = ImageFinder(self.hwnd)
                found = finder.find_image()
                time.sleep(1)

                if found:
                    print(f"Char {self.account['login']} está na fila. Aguardando...")
                    while found:
                        time.sleep(30)
                        found = finder.find_image()
                        time.sleep(1)
                    print(f"Char {self.account['login']} saiu da fila.")
                else:
                    print(f"Char {self.account['login']} sem fila.")

                # Seleciona posição do personagem
                position_coords = {
                    "Left": 'pos_1',
                    "Center": 'pos_2',
                    "Right": 'pos_3'
                }

                # Se não tem fila, seleciona a posição e entra no jogo
                if self.account["position"] in position_coords:
                    mouse.left(self.hwnd, self.coords[position_coords[self.account["position"]]][0],
                               self.coords[position_coords[self.account["position"]]][1])
                time.sleep(1)

                # Checa disconnect antes de entrar no jogo
                while True:
                    pointers = Pointers(self.pid)
                    login = pointers.check_login()

                    if login == 1:
                        print(f"Erro de login antes do Enter Game {self.account['login']}")
                        mouse.left(self.hwnd, self.coords['passError'][0], self.coords['passError'][1])
                        time.sleep(1)
                        return self.perform_account_login()
                    elif login == 0:
                        break

                    time.sleep(1)

                mouse.left(self.hwnd, self.coords['entergame'][0], self.coords['entergame'][1])
                time.sleep(3)

                # Character name
                pointers = Pointers(self.pid)
                char_name = pointers.get_char_name()
                win32gui.SetWindowText(self.hwnd, char_name)
                time.sleep(1)

                return True

            except Exception as e:
                print(f"Erro no login de {self.account['login']}: {str(e)}")
                return False

    def perform_login(self, pids):
        if len(pids) == 0 or len(self.accounts) == 0:
            return

        # Filtra apenas as contas selecionadas
        selected_accounts = [account for account in self.accounts if account.get('selected', False)]

        if not selected_accounts:
            QMessageBox.warning(self, "Aviso",
                                "Nenhuma conta selecionada para login. Por favor, selecione pelo menos uma conta.")
            return

        # Garante que temos PIDs suficientes para as contas selecionadas
        max_logins = min(len(pids), len(selected_accounts))

        print(f"Iniciando login para {max_logins} contas selecionadas em sequência:")
        for i in range(max_logins):
            print(f"  PID {pids[i]} -> Conta: {selected_accounts[i]['login']}")

        # Cria uma thread de login para cada par de PID e conta em ordem
        login_threads = []
        for i in range(max_logins):
            pid = pids[i]
            account = selected_accounts[i]
            thread = self.LoginThread(pid, account, self)
            login_threads.append(thread)
            thread.start()
            time.sleep(1)  # Pequena pausa entre inicializações das threads

        # Não bloqueia a thread principal
        # As threads de login continuarão executando em segundo plano

    def start_auto_login(self):
        client_path = self.client_path.text()

        # Verifica se o arquivo existe
        if not os.path.exists(client_path):
            QMessageBox.critical(self, "Erro", f"Arquivo não encontrado: {client_path}")
            return

        # IMPORTANTE: Recarrega as contas antes de iniciar
        print("Recarregando contas do arquivo...")
        self.load_accounts()

        # Limpa os PIDs salvos anteriormente para evitar problemas com janelas fechadas
        self.save_pids_to_json([])

        if len(self.accounts) == 0:
            QMessageBox.warning(self, "Aviso",
                                "Não há contas cadastradas. Por favor, cadastre pelo menos uma conta antes de iniciar.")
            return

        # Verifica se há contas selecionadas
        selected_accounts = [account for account in self.accounts if account.get('selected', False)]
        if not selected_accounts:
            QMessageBox.warning(self, "Aviso",
                                "Nenhuma conta selecionada para login. Por favor, selecione pelo menos uma conta.")
            return

        # print(f"Contas carregadas: {len(self.accounts)}")
        # for i, acc in enumerate(self.accounts):
        # print(f"  {i+1}: {acc['login']} - {acc['position']} - {acc['server']}")

        try:
            # Obtém o diretório do client.bat
            client_dir = os.path.dirname(client_path)
            # Muda para o diretório do client.bat
            os.chdir(client_dir)

            # Inicia um cliente para cada conta selecionada
            num_selected_accounts = len(selected_accounts)
            print(f"Iniciando {num_selected_accounts} clientes para as contas selecionadas")

            # Cria e inicia o thread do cliente
            self.client_thread = ClientThread(client_path, num_selected_accounts, self.initial_pids)
            self.client_thread.finished.connect(lambda pids: self.on_clients_started(pids))
            self.client_thread.start()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao executar os clientes: {str(e)}")

    def on_clients_started(self, new_pids):
        try:
            # Salva os PIDs no arquivo JSON
            json_path = self.save_pids_to_json(new_pids)
            # Realiza o login automático para cada cliente
            self.perform_login(new_pids)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao processar os clientes: {str(e)}")


class ClientThread(QThread):
    finished = pyqtSignal(list)

    def __init__(self, client_path, num_accounts, initial_pids):
        super().__init__()
        self.client_path = client_path
        self.num_accounts = num_accounts
        self.initial_pids = initial_pids

    def run(self):
        try:
            print(f"Iniciando {self.num_accounts} clientes...")
            new_pids = []

            for i in range(self.num_accounts):
                print(f"Iniciando cliente {i + 1}/{self.num_accounts}")

                # Captura PIDs antes de iniciar o cliente
                pids_before = self.get_current_client_pids()

                # Inicia o cliente
                os.startfile(self.client_path)

                # Aguarda o processo aparecer
                timeout = 0
                new_pid = None
                while timeout < 30:  # 30 segundos de timeout
                    time.sleep(1)
                    timeout += 1
                    pids_after = self.get_current_client_pids()

                    # Encontra o novo PID
                    diff_pids = [pid for pid in pids_after if pid not in pids_before and pid not in self.initial_pids]
                    if diff_pids:
                        new_pid = diff_pids[0]  # Pega o primeiro (mais recente)
                        break

                if new_pid:
                    new_pids.append(new_pid)
                    print(f"Cliente {i + 1} iniciado com PID: {new_pid}")
                else:
                    print(f"Erro: Não foi possível detectar o PID do cliente {i + 1}")

                time.sleep(3)  # Pausa entre inicializações

            print(f"PIDs em sequência: {new_pids}")

            # Emite o sinal com os novos PIDs em ordem
            self.finished.emit(new_pids)
        except Exception as e:
            print(f"Erro no thread: {str(e)}")

    def get_current_client_pids(self):
        """Obtém lista atual de PIDs do client.exe"""
        current_pids = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'client.exe' in proc.info['name'].lower():
                    current_pids.append(proc.info['pid'])
            except:
                pass
        return current_pids


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = AutoLoginWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
