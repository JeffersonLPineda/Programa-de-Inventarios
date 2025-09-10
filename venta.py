import sys
import os
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QSpinBox, QLineEdit, QDateEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox
)
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QIcon
import database as db  # tu archivo de conexión
from liberacion import LiberacionWindow  # Importar la ventana de liberación

def resource_path(relative_path):
    """Obtiene la ruta absoluta del recurso, compatible con PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class VentasWindow(QMainWindow):
    def __init__(self, role="Usuario"):
        super().__init__()
        self.role = role.lower()
        self.setWindowTitle("Registro de ventas")
        self.setMinimumSize(900, 600)
        self.setWindowIcon(QIcon(resource_path("mainlogo.ico")))

        central = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Registrar nueva venta:"))
        form_layout = QHBoxLayout()

        # ======================
        # BOTÓN ELIMINAR VENTA
        # ======================
        self.btn_eliminar = QPushButton("Eliminar venta")
        self.btn_eliminar.clicked.connect(self.eliminar_venta)
        form_layout.addWidget(self.btn_eliminar)

        # ======================
        # BOTÓN LIBERACIÓN (solo administradores)
        # ======================


        # Cliente
        self.cliente_combo = QComboBox()
        self.load_clientes()
        form_layout.addWidget(QLabel("Cliente:"))
        form_layout.addWidget(self.cliente_combo)

        # Producto
        self.producto_combo = QComboBox()
        self.load_productos()
        form_layout.addWidget(QLabel("Producto:"))
        form_layout.addWidget(self.producto_combo)

        # Cantidad
        self.cantidad_spin = QSpinBox()
        self.cantidad_spin.setMinimum(1)
        self.cantidad_spin.setMaximum(1000)
        form_layout.addWidget(QLabel("Cantidad:"))
        form_layout.addWidget(self.cantidad_spin)

        # Precio unitario
        self.precio_input = QLineEdit()
        form_layout.addWidget(QLabel("Precio unitario:"))
        form_layout.addWidget(self.precio_input)

        # Fecha
        self.fecha_edit = QDateEdit()
        self.fecha_edit.setDate(QDate.currentDate())
        self.fecha_edit.setCalendarPopup(True)
        form_layout.addWidget(QLabel("Fecha:"))
        form_layout.addWidget(self.fecha_edit)

        # Botón Registrar
        btn_registrar = QPushButton("Registrar Venta")
        btn_registrar.clicked.connect(self.confirm_sale)
        form_layout.addWidget(btn_registrar)

        layout.addLayout(form_layout)

        # Tabla de ventas
        self.ventas_table = QTableWidget()
        self.ventas_table.setColumnCount(6)
        self.ventas_table.setHorizontalHeaderLabels(
            ["ID", "Fecha", "Cliente", "Producto", "Cantidad", "Total"]
        )
        layout.addWidget(self.ventas_table)

        self.load_ventas()

        central.setLayout(layout)
        self.setCentralWidget(central)

    def load_clientes(self):
        conn = sqlite3.connect(db.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id_cliente, nombre FROM clientes")
        clientes = cursor.fetchall()
        self.cliente_combo.clear()
        for cid, nombre in clientes:
            self.cliente_combo.addItem(nombre, cid)
        conn.close()

    def load_productos(self):
        conn = sqlite3.connect(db.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id_producto, nombre FROM productos")
        productos = cursor.fetchall()
        self.producto_combo.clear()
        for pid, nombre in productos:
            self.producto_combo.addItem(nombre, pid)
        conn.close()

    def load_ventas(self):
        self.ventas_table.setRowCount(0)
        conn = sqlite3.connect(db.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT v.id_venta, v.fecha, c.nombre, p.nombre, d.cantidad, d.cantidad*d.precio_unitario
            FROM ventas v
            JOIN detalle_ventas d ON v.id_venta = d.id_venta
            LEFT JOIN clientes c ON v.cliente_id = c.id_cliente
            JOIN productos p ON d.id_producto = p.id_producto
            ORDER BY v.id_venta ASC
        """)
        rows = cursor.fetchall()
        self.ventas_table.setRowCount(len(rows))
        for i, (num, fecha, cliente, producto, cantidad, total) in enumerate(rows):
            self.ventas_table.setItem(i, 0, QTableWidgetItem(str(num)))
            self.ventas_table.setItem(i, 1, QTableWidgetItem(fecha))
            self.ventas_table.setItem(i, 2, QTableWidgetItem(str(cliente) if cliente else "Sin cliente"))
            self.ventas_table.setItem(i, 3, QTableWidgetItem(producto))
            self.ventas_table.setItem(i, 4, QTableWidgetItem(str(cantidad)))
            self.ventas_table.setItem(i, 5, QTableWidgetItem(f"{total:.2f}"))
        conn.close()

    def confirm_sale(self):
        cliente_id = self.cliente_combo.currentData()
        producto_id = self.producto_combo.currentData()
        cantidad = self.cantidad_spin.value()
        precio_unitario_str = self.precio_input.text()
        fecha = self.fecha_edit.date().toString("yyyy-MM-dd")

        try:
            precio_unitario = float(precio_unitario_str)
            if precio_unitario <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Error", "Precio unitario inválido")
            return

        total = cantidad * precio_unitario

        conn = sqlite3.connect(db.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ventas (fecha, cliente_id, usuario_id, total)
            VALUES (?, ?, ?, ?)
        """, (fecha, cliente_id, 1, total))  # Reemplaza 1 por self.user_id si lo tienes

        venta_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO detalle_ventas (id_venta, id_producto, cantidad, precio_unitario)
            VALUES (?, ?, ?, ?)
        """, (venta_id, producto_id, cantidad, precio_unitario))

        conn.commit()
        conn.close()

        self.load_ventas()
        QMessageBox.information(self, "Éxito", f"Venta #{venta_id} registrada correctamente.\nTotal: {total:.2f}")

    def eliminar_venta(self):
        row = self.ventas_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Seleccione una venta para eliminar.")
            return

        venta_id = self.ventas_table.item(row, 0).text()

        reply = QMessageBox.question(
            self,
            "Eliminar venta",
            "¿Está seguro que desea eliminar esta venta?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        conn = sqlite3.connect(db.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM detalle_ventas WHERE id_venta = ?", (venta_id,))
        cursor.execute("DELETE FROM ventas WHERE id_venta = ?", (venta_id,))
        conn.commit()
        conn.close()

        self.load_ventas()
        QMessageBox.information(self, "Eliminado", "Venta eliminada correctamente.")



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VentasWindow(role="Administrador")  # Cambiar role para pruebas
    window.show()
    sys.exit(app.exec())
