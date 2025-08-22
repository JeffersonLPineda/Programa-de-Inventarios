import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QGridLayout, QLabel,
    QVBoxLayout, QHBoxLayout, QMessageBox, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QIcon, QFont, QColor
from PyQt6.QtCore import Qt, QSize
from compras import ComprasWindow
from inventario import InventarioWindow
from venta import VentasWindow
from kardex import KardexWindow
from usuario import MainMenu as UsuarioMenu

def resource_path(relative_path):
    """Obtiene la ruta absoluta del recurso, compatible con PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class ShadowButton(QPushButton):
    """Botón con sombra y contorno negro al pasar el mouse."""
    def __init__(self, icon_path, callback=None, size=150):
        super().__init__()
        self.setFixedSize(size, size)
        self.setIconSize(QSize(90, 90))
        self.setIcon(QIcon(icon_path))
        self.default_style = """
            QPushButton {
                background-color: white;
                border-radius: 15px;
            }
            QPushButton:pressed {
                background-color: #cce0ff;
            }
        """
        self.hover_style = """
            QPushButton {
                background-color: white;
                border-radius: 15px;
                border: 2px solid black;
            }
            QPushButton:pressed {
                background-color: #cce0ff;
            }
        """
        self.setStyleSheet(self.default_style)

        # Sombra
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

        if callback:
            self.clicked.connect(callback)

    def enterEvent(self, event):
        self.setStyleSheet(self.hover_style)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self.default_style)
        super().leaveEvent(event)


class MenuPrincipal(QMainWindow):
    def __init__(self, username, role, login_window=None):
        super().__init__()
        self.username = username
        self.role = role
        self.login_window = login_window  # Para cerrar sesión

        self.setWindowTitle(f"Menú principal - Usuario: {username} ({role})")
        self.setMinimumSize(800, 600)
        self.setWindowIcon(QIcon(resource_path("mainlogo.ico")))

        central = QWidget()
        self.setCentralWidget(central)
        central.setStyleSheet("background-color: white;")

        main_layout = QVBoxLayout()
        main_layout.setSpacing(30)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Encabezado ---
        header_widget = QWidget()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 10, 10, 10)

        header_label = QLabel("Sistema Contable")
        header_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header_label.setStyleSheet("color: #1670B6;")
        header_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Botón “Más opciones”
        self.mas_opciones_btn = QPushButton("...")
        self.mas_opciones_btn.setFixedSize(40, 40)
        self.mas_opciones_btn.setStyleSheet("""
            QPushButton {
                background-color: #1670B6;
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0d4e8b;
            }
        """)
        self.mas_opciones_btn.clicked.connect(self.mostrar_mas_opciones)

        header_layout.addWidget(header_label, alignment=Qt.AlignmentFlag.AlignLeft)
        header_layout.addWidget(self.mas_opciones_btn, alignment=Qt.AlignmentFlag.AlignRight)
        header_widget.setLayout(header_layout)
        main_layout.addWidget(header_widget)

        # --- Panel de grid 2x2 ---
        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setSpacing(50)

        botones_info = [
            ("Compras", "compras.png", self.abrir_compras),
            ("Inventario", "inventario.png", self.abrir_inventario),
            ("Ventas", "ventas.png", self.abrir_ventas),
            ("Kardex", "kardex.png", self.abrir_kardex),
        ]

        for index, (texto, icono, callback) in enumerate(botones_info):
            row = index // 2
            col = index % 2

            container = QWidget()
            v_layout = QVBoxLayout()
            v_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            v_layout.setSpacing(10)

            btn = ShadowButton(resource_path(icono), callback)
            label = QLabel(texto)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-size: 14px; color: black;")

            v_layout.addWidget(btn)
            v_layout.addWidget(label)
            container.setLayout(v_layout)

            grid_layout.addWidget(container, row, col, alignment=Qt.AlignmentFlag.AlignCenter)

        grid_widget.setLayout(grid_layout)
        main_layout.addWidget(grid_widget)

        # --- Etiqueta de versión ---
        version_label = QLabel("Version 0.0.1")
        version_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        version_label.setStyleSheet("color: rgba(0,0,0,0.2); font-size: 12px;")
        main_layout.addWidget(version_label)

        central.setLayout(main_layout)

    # --- Métodos de apertura ---
    def abrir_compras(self):
        self.compras_window = ComprasWindow(role=self.role)
        self.compras_window.show()

    def abrir_inventario(self):
        self.inventario_window = InventarioWindow(role=self.role)
        self.inventario_window.show()

    def abrir_ventas(self):
        self.ventas_window = VentasWindow(role=self.role)
        self.ventas_window.show()

    def abrir_kardex(self):
        self.kardex_window = KardexWindow()
        self.kardex_window.show()

    # --- Más opciones / Usuarios ---
    def mostrar_mas_opciones(self):
        if hasattr(self, "mas_opciones_panel") and self.mas_opciones_panel.isVisible():
            self.mas_opciones_panel.hide()
            return

        self.mas_opciones_panel = QWidget(self.centralWidget())
        self.mas_opciones_panel.setStyleSheet(
            "background-color: white; border: 1px solid #ccc; border-radius: 10px;"
        )
        self.mas_opciones_panel.setFixedSize(200, 150)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # Usuario actual
        label_user = QLabel(f"Usuario actual: {self.username}")
        label_user.setStyleSheet("font-size: 14px; color: black;")
        layout.addWidget(label_user)

        # Botón usuarios
        btn_usuarios = QPushButton("Usuarios")
        btn_usuarios.setStyleSheet("""
            QPushButton {
                background-color: #1670B6;
                color: white;
                border-radius: 10px;
                padding: 5px 10px;
            }
            QPushButton:pressed {
                background-color: #0d4e8b;
            }
        """)
        btn_usuarios.clicked.connect(self.abrir_usuarios)
        layout.addWidget(btn_usuarios)

        # Botón cerrar sesión
        btn_logout = QPushButton("Cerrar Sesión")
        btn_logout.setStyleSheet("""
            QPushButton {
                background-color: #1670B6;
                color: white;
                border-radius: 10px;
                padding: 5px 10px;
            }
            QPushButton:pressed {
                background-color: #0d4e8b;
            }
        """)
        btn_logout.clicked.connect(self.cerrar_sesion)
        layout.addWidget(btn_logout)

        self.mas_opciones_panel.setLayout(layout)

        # Posicionar panel relativo al botón "..."
        btn_pos = self.mas_opciones_btn.pos()  # posición relativa al parent
        x = btn_pos.x() + self.mas_opciones_btn.width() - self.mas_opciones_panel.width()
        y = btn_pos.y() + self.mas_opciones_btn.height()
        self.mas_opciones_panel.move(x, y)
        self.mas_opciones_panel.show()
        self.mas_opciones_panel.raise_()

    def abrir_usuarios(self):
        if self.role != "Administrador":
            QMessageBox.warning(self, "Acceso denegado",
                                "No tienes los permisos suficientes para acceder a esta función.")
            return
        self.usuario_window = UsuarioMenu()
        self.usuario_window.show()

    def cerrar_sesion(self):
            from main import LoginWindow
            self.close()
            self.login_window = LoginWindow()
            self.login_window.show()