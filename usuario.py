import sqlite3
import os
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QLabel, QPushButton, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QComboBox, QMessageBox, QTableWidget, QTableWidgetItem,
    QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QIcon, QColor
from PyQt6.QtCore import Qt

DB_NAME = "sistema.db"

def resource_path(relative_path):
    """Obtiene la ruta absoluta del recurso, compatible con PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# -----------------------------
# Funciones DB
# -----------------------------
def obtener_roles():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM roles")
    roles = cursor.fetchall()
    conn.close()
    return roles

def obtener_usuarios():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.username, r.nombre 
        FROM usuarios u
        JOIN roles r ON u.role_id = r.id
    """)
    usuarios = cursor.fetchall()
    conn.close()
    return usuarios

def crear_usuario(username, password, role_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO usuarios (username, password, role_id) VALUES (?, ?, ?)",
                   (username, password, role_id))
    conn.commit()
    conn.close()

def modificar_usuario(user_id, username, password, role_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET username=?, password=?, role_id=? WHERE id=?",
                   (username, password, role_id, user_id))
    conn.commit()
    conn.close()

def eliminar_usuario(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

def obtener_clientes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id_cliente, nombre, contacto FROM clientes")
    clientes = cursor.fetchall()
    conn.close()
    return clientes

def crear_cliente(nombre, contacto):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO clientes (nombre, contacto) VALUES (?, ?)", (nombre, contacto))
    conn.commit()
    conn.close()

def modificar_cliente(cliente_id, nombre, contacto):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE clientes SET nombre=?, contacto=? WHERE id_cliente=?",
                   (nombre, contacto, cliente_id))
    conn.commit()
    conn.close()

def eliminar_cliente(cliente_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clientes WHERE id_cliente=?", (cliente_id,))
    conn.commit()
    conn.close()

def obtener_proveedores():
    """Devuelve tuplas (id_proveedor, nombre, contacto, direccion)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Asegurarse de traer la dirección también
    cursor.execute("SELECT id_proveedor, nombre, contacto, direccion FROM proveedores")
    proveedores = cursor.fetchall()
    conn.close()

    # Por seguridad, normalizamos cada fila a 4 elementos (rellenando con cadena vacía si falta)
    normalized = []
    for row in proveedores:
        if len(row) >= 4:
            normalized.append((row[0], row[1], row[2], row[3]))
        else:
            # Rellenar con valores vacíos si la fila es corta (evita ValueError)
            vals = list(row) + [""] * (4 - len(row))
            normalized.append(tuple(vals[:4]))
    return normalized

def crear_proveedor(nombre, contacto, direccion):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO proveedores (nombre, contacto, direccion) VALUES (?, ?, ?)",
                   (nombre, contacto, direccion))
    conn.commit()
    conn.close()

def modificar_proveedor(proveedor_id, nombre, contacto, direccion):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE proveedores SET nombre=?, contacto=?, direccion=? WHERE id_proveedor=?",
                   (nombre, contacto, direccion, proveedor_id))
    conn.commit()
    conn.close()

def eliminar_proveedor(proveedor_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM proveedores WHERE id_proveedor=?", (proveedor_id,))
    conn.commit()
    conn.close()

# -----------------------------
# Botón con sombra y estilo
# -----------------------------
class ShadowButton(QPushButton):
    def __init__(self, text, callback=None, size=(180, 50)):
        super().__init__(text)
        self.setFixedSize(*size)
        self.setStyleSheet("""
            QPushButton {
                background-color: #1670B6;
                color: white;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:pressed {
                background-color: #0d4e8b;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)
        if callback:
            self.clicked.connect(callback)

# -----------------------------
# Ventana principal administración
# -----------------------------
class MainMenu(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(800, 600)
        self.setWindowTitle("Panel de Administración")
        self.setWindowIcon(QIcon(resource_path("mainlogo.ico")))

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(30)

        header = QLabel("Panel de Administración")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #1670B6;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Botones
        self.btn_usuarios = ShadowButton("Usuarios", self.open_users)
        self.btn_clientes = ShadowButton("Clientes", lambda: self.open_entity("Clientes"))
        self.btn_proveedores = ShadowButton("Proveedores", lambda: self.open_entity("Proveedores"))

        layout.addWidget(self.btn_usuarios, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.btn_clientes, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.btn_proveedores, alignment=Qt.AlignmentFlag.AlignHCenter)

        central.setLayout(layout)

    def open_users(self):
        self.user_window = EntityWindow("Usuarios")
        self.user_window.show()

    def open_entity(self, tipo):
        self.entity_window = EntityWindow(tipo)
        self.entity_window.show()

# -----------------------------
# Ventana genérica Usuarios/Clientes/Proveedores
# -----------------------------
class EntityWindow(QWidget):
    def __init__(self, tipo):
        super().__init__()
        self.tipo = tipo
        self.setMinimumSize(600, 400)
        self.setWindowTitle(f"{tipo} - Administración")

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(15)

        header = QLabel(f"Administrar {tipo}")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #1670B6;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Tabla
        self.table = QTableWidget()
        if tipo == "Usuarios":
            self.table.setColumnCount(3)
            self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Rol"])
        elif tipo == "Clientes":
            self.table.setColumnCount(3)
            self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Contacto"])
        else:  # Proveedores
            self.table.setColumnCount(4)
            self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Contacto", "Dirección"])
        layout.addWidget(self.table)
        self.load_items()

        # Inputs
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Nombre")
        layout.addWidget(self.input_name)

        if tipo == "Usuarios":
            # 🔑 Campo de contraseña
            self.input_password = QLineEdit()
            self.input_password.setPlaceholderText("Contraseña")
            self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addWidget(self.input_password)

            self.role_combo = QComboBox()
            for r_id, nombre in obtener_roles():
                self.role_combo.addItem(nombre, r_id)
            layout.addWidget(self.role_combo)

        if tipo == "Clientes":
            self.input_contacto = QLineEdit()
            self.input_contacto.setPlaceholderText("Contacto")
            layout.addWidget(self.input_contacto)

        if tipo == "Proveedores":
            self.input_contacto = QLineEdit()
            self.input_contacto.setPlaceholderText("Contacto")
            self.input_direccion = QLineEdit()
            self.input_direccion.setPlaceholderText("Dirección")
            layout.addWidget(self.input_contacto)
            layout.addWidget(self.input_direccion)

        # Botones
        btn_layout = QHBoxLayout()
        btn_crear = ShadowButton("Crear", self.create_item)
        btn_modificar = ShadowButton("Modificar", self.modify_item)
        btn_eliminar = ShadowButton("Eliminar", self.delete_item)
        btn_layout.addWidget(btn_crear)
        btn_layout.addWidget(btn_modificar)
        btn_layout.addWidget(btn_eliminar)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def create_item(self):
        name = self.input_name.text()
        if not name:
            QMessageBox.warning(self, "Error", "Ingrese un nombre")
            return
        if self.tipo == "Usuarios":
            password = self.input_password.text()
            if not password:
                QMessageBox.warning(self, "Error", "Ingrese una contraseña")
                return
            role_id = self.role_combo.currentData()
            crear_usuario(name, password, role_id)
        elif self.tipo == "Clientes":
            contacto = self.input_contacto.text()
            crear_cliente(name, contacto)
        else:  # Proveedores
            contacto = self.input_contacto.text()
            direccion = self.input_direccion.text()
            crear_proveedor(name, contacto, direccion)
        QMessageBox.information(self, "Éxito", f"{self.tipo[:-1]} creado correctamente")
        self.load_items()

    def modify_item(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Seleccione un elemento para modificar")
            return
        item_id = int(self.table.item(row, 0).text())
        name = self.input_name.text()
        if not name:
            QMessageBox.warning(self, "Error", "Ingrese un nombre")
            return
        if self.tipo == "Usuarios":
            password = self.input_password.text()
            if not password:
                QMessageBox.warning(self, "Error", "Ingrese una contraseña")
                return
            role_id = self.role_combo.currentData()
            modificar_usuario(item_id, name, password, role_id)
        elif self.tipo == "Clientes":
            contacto = self.input_contacto.text()
            modificar_cliente(item_id, name, contacto)
        else:  # Proveedores
            contacto = self.input_contacto.text()
            direccion = self.input_direccion.text()
            modificar_proveedor(item_id, name, contacto, direccion)
        QMessageBox.information(self, "Éxito", f"{self.tipo[:-1]} modificado correctamente")
        self.load_items()

    def load_items(self):
        """Carga los registros en la tabla según el tipo de entidad"""
        self.table.setRowCount(0)  # limpiar tabla

        if self.tipo == "Usuarios":
            usuarios = obtener_usuarios()  # debería devolver lista de tuplas (id, nombre, rol)
            for row_idx, (u_id, nombre, rol) in enumerate(usuarios):
                self.table.insertRow(row_idx)
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(u_id)))
                self.table.setItem(row_idx, 1, QTableWidgetItem(nombre))
                self.table.setItem(row_idx, 2, QTableWidgetItem(rol))

        elif self.tipo == "Clientes":
            clientes = obtener_clientes()  # lista de tuplas (id, nombre, contacto)
            for row_idx, (c_id, nombre, contacto) in enumerate(clientes):
                self.table.insertRow(row_idx)
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(c_id)))
                self.table.setItem(row_idx, 1, QTableWidgetItem(nombre))
                self.table.setItem(row_idx, 2, QTableWidgetItem(contacto))

        elif self.tipo == "Proveedores":
                proveedores = obtener_proveedores()  # ahora devuelve (id, nombre, contacto, direccion)
                self.table.setRowCount(len(proveedores))
                for row_idx, prov in enumerate(proveedores):
                    # prov puede ser (p_id, nombre, contacto, direccion)
                    # por seguridad desempaquetamos con padding si hiciera falta
                    if len(prov) == 4:
                        p_id, nombre, contacto, direccion = prov
                    else:
                        # seguridad extra (no debería ocurrir porque normalizamos en obtener_proveedores)
                        p = list(prov) + [""] * (4 - len(prov))
                        p_id, nombre, contacto, direccion = p

                    self.table.setItem(row_idx, 0, QTableWidgetItem(str(p_id)))
                    self.table.setItem(row_idx, 1, QTableWidgetItem(nombre))
                    self.table.setItem(row_idx, 2, QTableWidgetItem(contacto))
                    self.table.setItem(row_idx, 3, QTableWidgetItem(direccion))
                
    def delete_item(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Seleccione un elemento para eliminar")
            return
        item_id = int(self.table.item(row, 0).text())
        if self.tipo == "Usuarios":
            eliminar_usuario(item_id)
        elif self.tipo == "Clientes":
            eliminar_cliente(item_id)
        else:
            eliminar_proveedor(item_id)
        QMessageBox.information(self, "Éxito", f"{self.tipo[:-1]} eliminado correctamente")
        self.load_items()

# -----------------------------
# Ejecutar
# -----------------------------
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication
