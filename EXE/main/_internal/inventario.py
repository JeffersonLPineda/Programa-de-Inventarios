import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QComboBox, QDateEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QMessageBox
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

class InventarioWindow(QMainWindow):
    def __init__(self, role="Usuario"):
        super().__init__()
        self.role = role.lower()
        self.setWindowTitle("Inventario")
        self.setMinimumSize(900, 600)
        self.setWindowIcon(QIcon(resource_path("mainlogo.ico")))

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()

        # ======================
        # FILTROS
        # ======================
        filtro_layout = QHBoxLayout()

        # Filtrar por producto
        self.product_combo = QComboBox()
        self.product_combo.addItem("Todos", None)
        self.load_productos()
        filtro_layout.addWidget(QLabel("Producto:"))
        filtro_layout.addWidget(self.product_combo)

        # Filtrar por período (fecha desde / hasta)
        self.fecha_desde = QDateEdit()
        self.fecha_desde.setCalendarPopup(True)
        self.fecha_desde.setDate(QDate.currentDate().addMonths(-1))
        filtro_layout.addWidget(QLabel("Desde:"))
        filtro_layout.addWidget(self.fecha_desde)

        self.fecha_hasta = QDateEdit()
        self.fecha_hasta.setCalendarPopup(True)
        self.fecha_hasta.setDate(QDate.currentDate())
        filtro_layout.addWidget(QLabel("Hasta:"))
        filtro_layout.addWidget(self.fecha_hasta)

        btn_filtrar = QPushButton("Filtrar Inventario")
        btn_filtrar.clicked.connect(self.load_inventario)
        filtro_layout.addWidget(btn_filtrar)

        layout.addLayout(filtro_layout)

        # ======================
        # TABLA DE INVENTARIO
        # ======================
        self.inventario_table = QTableWidget()
        self.inventario_table.setColumnCount(6 if self.role == "administrador" else 5)
        headers = ["ID Inventario", "Producto", "Cantidad", "Precio Unitario", "Fecha Compra"]
        if self.role == "administrador":
            headers.append("Eliminar")
        self.inventario_table.setHorizontalHeaderLabels(headers)
        layout.addWidget(self.inventario_table)

        central.setLayout(layout)
        self.load_inventario()

    def load_productos(self):
        conn = sqlite3.connect(db.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id_producto, nombre FROM productos")
        rows = cursor.fetchall()
        for pid, nombre in rows:
            self.product_combo.addItem(nombre, pid)
        conn.close()

    def load_inventario(self):
        self.inventario_table.setRowCount(0)

        producto_id = self.product_combo.currentData()
        desde = self.fecha_desde.date().toString("yyyy-MM-dd")
        hasta = self.fecha_hasta.date().toString("yyyy-MM-dd")

        conn = sqlite3.connect(db.DB_NAME)
        cursor = conn.cursor()

        sql = """
                SELECT DISTINCT i.id, p.nombre, i.cantidad, i.precio_unitario, c.fecha, c.id_compra
                FROM inventarios i
                JOIN productos p ON i.id_producto = p.id_producto
                JOIN compras c ON i.id_compra = c.id_compra
                WHERE c.fecha BETWEEN ? AND ?
        """
        params = [desde, hasta]

        if producto_id is not None:
            sql += " AND i.id_producto = ?"
            params.append(producto_id)

        sql += " ORDER BY c.fecha ASC"

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        self.inventario_table.setRowCount(len(rows))

        for i, (inv_id, producto, cantidad, precio_unitario, fecha, compra_id) in enumerate(rows):
            self.inventario_table.setItem(i, 0, QTableWidgetItem(str(inv_id)))
            self.inventario_table.setItem(i, 1, QTableWidgetItem(producto))
            self.inventario_table.setItem(i, 2, QTableWidgetItem(str(cantidad)))
            self.inventario_table.setItem(i, 3, QTableWidgetItem(f"{precio_unitario:.2f}"))
            self.inventario_table.setItem(i, 4, QTableWidgetItem(fecha))

            if self.role == "administrador":
                btn_delete = QPushButton("Eliminar")
                btn_delete.clicked.connect(lambda checked, cid=compra_id: self.eliminar_compra(cid))
                self.inventario_table.setCellWidget(i, 5, btn_delete)

        conn.close()

    def eliminar_compra(self, compra_id):
        reply = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Desea eliminar la compra #{compra_id} y su inventario asociado?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            conn = sqlite3.connect(db.DB_NAME)
            cursor = conn.cursor()
            # Eliminar detalle de compras
            cursor.execute("DELETE FROM detalle_compras WHERE id_compra = ?", (compra_id,))
            # Eliminar compra
            cursor.execute("DELETE FROM compras WHERE id_compra = ?", (compra_id,))
            # Eliminar inventario asociado
            cursor.execute("DELETE FROM inventarios WHERE id_compra = ?", (compra_id,))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Éxito", f"Compra #{compra_id} y su inventario eliminado.")
            self.load_inventario()
