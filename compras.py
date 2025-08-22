import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QComboBox, QMessageBox, QTableWidget, QTableWidgetItem, QSpinBox, QDateEdit, QLineEdit
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QDate
import sqlite3
import database as db

def resource_path(relative_path):
    """Obtiene la ruta absoluta del recurso, compatible con PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ======================
# VENTANA PRINCIPAL DE COMPRAS
# ======================
class ComprasWindow(QMainWindow):
    def __init__(self, role="Usuario"):
        super().__init__()
        self.role = role
        self.setWindowTitle("Registro y Historial de Compras")
        self.setMinimumSize(900, 600)
        self.setWindowIcon(QIcon(resource_path("mainlogo.ico")))

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()

        # ======================
        # FILTRO DE HISTORIAL
        # ======================
        filtro_layout = QHBoxLayout()
        self.mes_edit = QDateEdit()
        self.mes_edit.setDisplayFormat("MM/yyyy")
        self.mes_edit.setDate(QDate.currentDate())
        self.mes_edit.setCalendarPopup(True)
        filtro_layout.addWidget(QLabel("Seleccionar mes:"))
        filtro_layout.addWidget(self.mes_edit)
        btn_filtrar = QPushButton("Filtrar historial")
        btn_filtrar.clicked.connect(self.load_compras)
        filtro_layout.addWidget(btn_filtrar)
        layout.addLayout(filtro_layout)

        # Tabla de compras
        self.compras_table = QTableWidget()
        self.compras_table.setColumnCount(6)
        self.compras_table.setHorizontalHeaderLabels(
            ["Número", "Fecha", "Producto", "Cantidad", "Precio unitario", "Total"]
        )
        layout.addWidget(self.compras_table)

        # ======================
        # REGISTRO DE NUEVA COMPRA
        # ======================
        layout.addWidget(QLabel("Registrar nueva compra:"))
        form_layout = QHBoxLayout()
        self.product_combo = QComboBox()
        self.load_product_combo()
        form_layout.addWidget(QLabel("Producto:"))
        form_layout.addWidget(self.product_combo)

        self.cantidad_spin = QSpinBox()
        self.cantidad_spin.setMinimum(1)
        self.cantidad_spin.setMaximum(1000)
        form_layout.addWidget(QLabel("Cantidad:"))
        form_layout.addWidget(self.cantidad_spin)

        self.precio_input = QLineEdit()
        self.precio_input.setPlaceholderText("Precio unitario (opcional)")
        form_layout.addWidget(QLabel("Precio unitario:"))
        form_layout.addWidget(self.precio_input)

        self.fecha_edit = QDateEdit()
        self.fecha_edit.setDate(QDate.currentDate())
        self.fecha_edit.setCalendarPopup(True)
        form_layout.addWidget(QLabel("Fecha:"))
        form_layout.addWidget(self.fecha_edit)

        btn_registrar = QPushButton("Registrar Compra")
        btn_registrar.clicked.connect(self.confirm_purchase)
        form_layout.addWidget(btn_registrar)

        layout.addLayout(form_layout)

        # ======================
        # BOTÓN AGREGAR PRODUCTOS (solo admin)
        # ======================
        if self.role.lower() == "administrador":
            btn_productos = QPushButton("Agregar Productos")
            btn_productos.clicked.connect(self.abrir_productos)
            layout.addWidget(btn_productos)

        central.setLayout(layout)
        self.load_compras()  # Cargar compras del mes actual al inicio

    def load_product_combo(self):
        self.product_combo.clear()
        conn = sqlite3.connect(db.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id_producto, nombre FROM productos")
        rows = cursor.fetchall()
        for pid, nombre in rows:
            self.product_combo.addItem(nombre, pid)
        conn.close()

    def load_compras(self):
        self.compras_table.setRowCount(0)
        fecha = self.mes_edit.date()
        mes = fecha.month()
        anio = fecha.year()

        conn = sqlite3.connect(db.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id_compra, c.fecha, p.nombre, d.cantidad, d.precio_unitario, d.cantidad*d.precio_unitario as total
            FROM compras c
            JOIN detalle_compras d ON c.id_compra = d.id_compra
            JOIN productos p ON d.id_producto = p.id_producto
            WHERE strftime('%m', c.fecha) = ? AND strftime('%Y', c.fecha) = ?
            ORDER BY c.fecha ASC
        """, (f"{mes:02d}", str(anio)))
        rows = cursor.fetchall()
        self.compras_table.setRowCount(len(rows))
        for i, (num, fecha, producto, cantidad, precio_unitario, total) in enumerate(rows):
            self.compras_table.setItem(i, 0, QTableWidgetItem(str(num)))
            self.compras_table.setItem(i, 1, QTableWidgetItem(fecha))
            self.compras_table.setItem(i, 2, QTableWidgetItem(producto))
            self.compras_table.setItem(i, 3, QTableWidgetItem(str(cantidad)))
            self.compras_table.setItem(i, 4, QTableWidgetItem(f"{precio_unitario:.2f}"))
            self.compras_table.setItem(i, 5, QTableWidgetItem(f"{total:.2f}"))
        conn.close()

    def confirm_purchase(self):
        producto_id = self.product_combo.currentData()

        # --- VALIDACIÓN: debe haber al menos un producto ---
        if producto_id is None:
            QMessageBox.warning(self, "Error", "No hay productos disponibles para registrar la compra.")
            return

        fecha = self.fecha_edit.date().toString("yyyy-MM-dd")
        cantidad = self.cantidad_spin.value()

        conn = sqlite3.connect(db.DB_NAME)
        cursor = conn.cursor()

        # Número de compra automático
        cursor.execute("SELECT MAX(id_compra) FROM compras")
        last = cursor.fetchone()[0]
        next_id = 1 if last is None else last + 1

        # Precio ingresado por el usuario (opcional)
        precio_texto = self.precio_input.text().strip()
        if precio_texto == "":
            # Usar precio del producto si no se ingresa nada
            cursor.execute("SELECT precio FROM productos WHERE id_producto=?", (producto_id,))
            precio_unitario = cursor.fetchone()[0]
        else:
            try:
                precio_unitario = float(precio_texto)
            except ValueError:
                QMessageBox.warning(self, "Error", "Precio inválido.")
                conn.close()
                return

        total = precio_unitario * cantidad

        # Insertar compra
        cursor.execute(
            "INSERT INTO compras (id_compra, fecha, usuario_id, proveedor_id, total) VALUES (?, ?, ?, ?, ?)",
            (next_id, fecha, 1, None, total)
        )
        cursor.execute(
            "INSERT INTO detalle_compras (id_compra, id_producto, cantidad, precio_unitario) VALUES (?, ?, ?, ?)",
            (next_id, producto_id, cantidad, precio_unitario)
        )

        # Insertar en inventarios
        cursor.execute(
            "INSERT INTO inventarios (id_producto, cantidad, precio_unitario, fecha_compra, id_compra) VALUES (?, ?, ?, ?, ?)",
            (producto_id, cantidad, precio_unitario, fecha, next_id)
        )

        # Actualizar stock del producto
        cursor.execute("UPDATE productos SET stock = stock + ? WHERE id_producto=?", (cantidad, producto_id))

        conn.commit()
        conn.close()
        self.load_product_combo()
        self.load_compras()
        QMessageBox.information(self, "Éxito", f"Compra #{next_id} registrada.\nTotal: {total:.2f}")


    # ======================
    # ABRIR VENTANA DE PRODUCTOS (solo admin)
    # ======================
    def abrir_productos(self):
        self.productos_window = ProductosWindow()
        self.productos_window.show()


# ======================
# VENTANA AGREGAR PRODUCTOS
# ======================
class ProductosWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Agregar Productos")
        self.setMinimumSize(400, 300)
        self.setWindowIcon(QIcon("mainlogo.ico"))

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()

        self.nombre_input = QLineEdit()
        self.nombre_input.setPlaceholderText("Nombre del producto")
        layout.addWidget(self.nombre_input)

        self.proveedor_combo = QComboBox()
        self.load_proveedores()
        layout.addWidget(QLabel("Proveedor:"))
        layout.addWidget(self.proveedor_combo)

        self.precio_input = QLineEdit()
        self.precio_input.setPlaceholderText("Precio unitario")
        layout.addWidget(self.precio_input)

        btn_guardar = QPushButton("Agregar Producto")
        btn_guardar.clicked.connect(self.add_product)
        layout.addWidget(btn_guardar)

        central.setLayout(layout)

    def load_proveedores(self):
        self.proveedor_combo.clear()
        conn = sqlite3.connect(db.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id_proveedor, nombre FROM proveedores")
        rows = cursor.fetchall()
        for pid, nombre in rows:
            self.proveedor_combo.addItem(nombre, pid)
        conn.close()

    def add_product(self):
        nombre = self.nombre_input.text()
        proveedor_id = self.proveedor_combo.currentData()
        try:
            precio = float(self.precio_input.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Precio inválido")
            return

        conn = sqlite3.connect(db.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO productos (nombre, proveedor_id, precio, stock) VALUES (?, ?, ?, ?)",
                       (nombre, proveedor_id, precio, 0))
        conn.commit()
        conn.close()

        self.nombre_input.clear()
        self.precio_input.clear()
        QMessageBox.information(self, "Éxito", f"Producto '{nombre}' agregado con éxito.")
