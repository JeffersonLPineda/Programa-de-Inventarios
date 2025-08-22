import sys
import os
import database as db
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QMessageBox, QStyleFactory
from PyQt6.QtGui import QIcon, QPalette, QColor
from menu import MenuPrincipal  # Hub del sistema

def resource_path(relative_path):
    """Obtiene la ruta absoluta del recurso, compatible con PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# =========================
# LOGIN
# =========================
class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setMinimumSize(400, 200)
        self.setWindowIcon(QIcon(resource_path("mainlogo.ico")))
        layout = QVBoxLayout()

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Usuario")
        layout.addWidget(self.user_input)

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Contraseña")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.pass_input)

        login_btn = QPushButton("Iniciar sesión")
        login_btn.clicked.connect(self.login)
        layout.addWidget(login_btn)

        self.setLayout(layout)

    def login(self):
        usuario = self.user_input.text()
        password = self.pass_input.text()
        user_data = db.login(usuario, password)  

        if user_data:
            username, role = user_data
            self.accept_login(username, role)
        else:
            QMessageBox.critical(self, "Error", "Credenciales inválidas.")

    def accept_login(self, usuario, role):
        self.close()
        self.menu_window = MenuPrincipal(usuario, role)
        self.menu_window.show()



# =========================
# MAIN
# =========================
if __name__ == "__main__":
    if not os.path.exists(db.DB_NAME):
        db.initialize_db()

    app = QApplication(sys.argv)

    app.setStyleSheet("""
        QWidget {
            background-color: white;
            color: black;
        }
        QLineEdit {
            background-color: white;
            color: black;
            border: 1px solid gray;
            padding: 4px;
        }
        QPushButton {
            background-color: #f0f0f0;
            color: black;
            border: 1px solid gray;
            padding: 6px;
        }
        QPushButton:hover {
            background-color: #dcdcdc;
        }
    """)


    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec())
