import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton,
    QMessageBox, QInputDialog, QTableWidget, QTableWidgetItem
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QDate, Qt
import sqlite3
import database as db

def resource_path(relative_path):
    """Obtiene la ruta absoluta del recurso, compatible con PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class KardexVistaPreviaWindow(QMainWindow):
    def __init__(self, venta_id, metodo="UEPS"):
        super().__init__()
        self.venta_id = venta_id
        self.metodo = metodo
        self.setWindowTitle(f"Vista Previa Liberación - Venta #{venta_id} ({metodo})")
        self.setMinimumSize(1100, 650)
        self.setWindowIcon(QIcon(resource_path("mainlogo.ico")))

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Vista previa de liberación para Venta #{venta_id} usando método {metodo}"))

        # Tabla Kardex
        self.kardex_table = QTableWidget()
        layout.addWidget(self.kardex_table)
        central.setLayout(layout)

        self.mostrar_kardex_preview()

    def mostrar_kardex_preview(self):
        conn = sqlite3.connect(db.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id_producto, cantidad FROM detalle_ventas WHERE id_venta = ?", (self.venta_id,))
        venta_detalle = cursor.fetchall()
        if not venta_detalle:
            QMessageBox.information(self, "Info", f"La venta #{self.venta_id} no tiene detalle.")
            conn.close()
            return

        columnas = [
            "Fecha", "Tipo", "Producto",
            "Cantidad", "Precio Unitario", "Valor Total",
            "Cantidad", "Precio Unitario", "Valor Total",
            "Cantidad", "Precio Unitario", "Valor Total"
        ]
        grupos = [
            "", "", "",
            "Entradas", "Entradas", "Entradas",
            "Salidas", "Salidas", "Salidas",
            "Inventario Final", "Inventario Final", "Inventario Final"
        ]

        total_rows = len(venta_detalle) * 2
        self.kardex_table.setColumnCount(len(columnas))
        self.kardex_table.setRowCount(total_rows + 10)

        # Encabezados
        for col, texto in enumerate(grupos):
            item = QTableWidgetItem(texto)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.kardex_table.setItem(0, col, item)
        for col, texto in enumerate(columnas):
            item = QTableWidgetItem(texto)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.kardex_table.setItem(1, col, item)

        self.kardex_table.setSpan(0, 0, 2, 1)
        self.kardex_table.setSpan(0, 1, 2, 1)
        self.kardex_table.setSpan(0, 2, 2, 1)
        for start_col, span, text in [(3, 3, "Entradas"), (6, 3, "Salidas"), (9, 3, "Inventario Final")]:
            self.kardex_table.setSpan(0, start_col, 1, span)
            self.kardex_table.setItem(0, start_col, QTableWidgetItem(text))

        def safe_int(v):
            try:
                return int(v)
            except:
                return 0

        def safe_float(v):
            try:
                return float(v)
            except:
                return 0.0

        inventario_actual = {}
        inventario_total = {}
        row_idx = 2

        for producto_id, cantidad_requerida in venta_detalle:
            cantidad_restante = cantidad_requerida
            orden = "DESC" if self.metodo == "UEPS" else "ASC"
            cursor.execute(f"""
                SELECT id, cantidad, precio_unitario, fecha_compra
                FROM inventarios
                WHERE id_producto = ? AND cantidad > 0
                ORDER BY fecha_compra {orden}
            """, (producto_id,))
            inventarios = cursor.fetchall()
            if not inventarios:
                QMessageBox.warning(self, "Error", f"No hay inventario para el producto {producto_id}.")
                continue

            inv_id, inv_cant, inv_precio, fecha_compra = inventarios[0]
            inventario_actual[inv_id] = (inv_cant, inv_precio)
            inventario_total[producto_id] = inventario_total.get(producto_id, 0) + inv_cant

            # Entrada
            compra_row = [
                str(fecha_compra), "Compra", str(producto_id),
                str(inv_cant), f"{inv_precio:.2f}", f"{inv_cant * inv_precio:.2f}",
                "-", "-", "-",
                str(inv_cant), f"{inv_precio:.2f}", f"{inv_cant * inv_precio:.2f}"
            ]
            for col, val in enumerate(compra_row):
                self.kardex_table.setItem(row_idx, col, QTableWidgetItem(str(val)))
            row_idx += 1

            # Salida
            salida_cant = cantidad_requerida
            salida_prec = inv_precio
            inventario_actual[inv_id] = (inv_cant - salida_cant, inv_precio)
            inventario_total[producto_id] = max(inventario_total[producto_id] - salida_cant, 0)
            final_cant = inventario_total[producto_id]
            venta_row = [
                "-", "Venta", str(producto_id),
                "-", "-", "-",
                str(salida_cant), f"{salida_prec:.2f}", f"{salida_cant * salida_prec:.2f}",
                str(final_cant), f"{salida_prec:.2f}", f"{final_cant * salida_prec:.2f}"
            ]
            for col, val in enumerate(venta_row):
                self.kardex_table.setItem(row_idx, col, QTableWidgetItem(str(val)))
            row_idx += 1

        conn.close()
        self.kardex_table.resizeColumnsToContents()
        self.kardex_table.resizeRowsToContents()
        self.kardex_table.verticalHeader().setVisible(False)


class LiberacionWindow(QMainWindow):
    def __init__(self, role="Usuario"):
        super().__init__()
        self.role = role
        self.setWindowTitle("Liberación de Ventas")
        self.setMinimumSize(600, 400)
        self.setWindowIcon(QIcon("mainlogo.ico"))

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()

        self.venta_combo = QComboBox()
        self.load_ventas()
        layout.addWidget(QLabel("Seleccione una venta:"))
        layout.addWidget(self.venta_combo)

        self.btn_liberar_ueps = QPushButton("Liberar Venta (UEPS)")
        self.btn_liberar_ueps.clicked.connect(lambda: self.liberar_venta(metodo="UEPS"))
        layout.addWidget(self.btn_liberar_ueps)

        self.btn_liberar_peps = QPushButton("Liberar Venta (PEPS)")
        self.btn_liberar_peps.clicked.connect(lambda: self.liberar_venta(metodo="PEPS"))
        layout.addWidget(self.btn_liberar_peps)

        self.btn_vista_previa = QPushButton("Vista Previa")
        self.btn_vista_previa.clicked.connect(self.vista_previa_avanzada)
        layout.addWidget(self.btn_vista_previa)

        self.btn_eliminar = QPushButton("Eliminar Liberación")
        self.btn_eliminar.clicked.connect(self.eliminar_liberacion)
        layout.addWidget(self.btn_eliminar)

        central.setLayout(layout)

    def _table_has_column(self, table_name: str, column_name: str) -> bool:
        conn = sqlite3.connect(db.DB_NAME)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        cols = [r[1] for r in cursor.fetchall()]
        conn.close()
        return column_name in cols

    def load_ventas(self):
        self.venta_combo.clear()
        conn = sqlite3.connect(db.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT v.id_venta, IFNULL(SUM(d.cantidad), 0)
            FROM ventas v
            LEFT JOIN detalle_ventas d ON v.id_venta = d.id_venta
            GROUP BY v.id_venta
            ORDER BY v.id_venta ASC
        """)
        rows = cursor.fetchall()
        for vid, total_cant in rows:
            self.venta_combo.addItem(f"Venta #{vid} - Cant total: {total_cant}", vid)
        conn.close()

    def vista_previa_avanzada(self):
        venta_id = self.venta_combo.currentData()
        if venta_id is None:
            QMessageBox.warning(self, "Error", "Seleccione una venta válida.")
            return

        # Pedir método UEPS o PEPS
        metodo, ok = QInputDialog.getItem(
            self, "Método de inventario", "Seleccione método de inventario:", ["UEPS", "PEPS"], 0, False
        )
        if not ok or not metodo:
            return

        from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel
        self.preview_win = QMainWindow()
        self.preview_win.setWindowTitle(f"Vista Previa de Venta #{venta_id} ({metodo})")
        self.preview_win.setMinimumSize(1100, 650)
        central = QWidget()
        layout = QVBoxLayout()
        self.preview_win.setCentralWidget(central)

        self.preview_table = QTableWidget()
        layout.addWidget(QLabel(f"Vista previa de la liberación de la venta #{venta_id}"))
        layout.addWidget(self.preview_table)
        central.setLayout(layout)

        conn = sqlite3.connect(db.DB_NAME)
        cursor = conn.cursor()

        try:
            # Obtener detalle de la venta
            cursor.execute("SELECT id_producto, cantidad FROM detalle_ventas WHERE id_venta = ?", (venta_id,))
            venta_detalle = cursor.fetchall()
            if not venta_detalle:
                QMessageBox.information(self, "Info", f"La venta #{venta_id} no tiene detalle.")
                return

            columnas = [
                "Fecha", "Tipo", "Producto",
                "Cantidad", "Precio Unitario", "Valor Total",
                "Cantidad", "Precio Unitario", "Valor Total",
                "Cantidad", "Precio Unitario", "Valor Total"
            ]
            grupos = [
                "", "", "",
                "Entradas", "Entradas", "Entradas",
                "Salidas", "Salidas", "Salidas",
                "Inventario Final", "Inventario Final", "Inventario Final"
            ]

            total_rows = len(venta_detalle) * 5  # aproximación
            self.preview_table.setColumnCount(len(columnas))
            self.preview_table.setRowCount(total_rows + 20)

            # Encabezados
            for col, texto in enumerate(grupos):
                item = QTableWidgetItem(texto)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.preview_table.setItem(0, col, item)
            for col, texto in enumerate(columnas):
                item = QTableWidgetItem(texto)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.preview_table.setItem(1, col, item)
            self.preview_table.setSpan(0, 0, 2, 1)
            self.preview_table.setSpan(0, 1, 2, 1)
            self.preview_table.setSpan(0, 2, 2, 1)

            def merge_group(start_col, span, text):
                self.preview_table.setSpan(0, start_col, 1, span)
                itm = self.preview_table.item(0, start_col)
                if itm:
                    itm.setText(text)
                else:
                    self.preview_table.setItem(0, start_col, QTableWidgetItem(text))

            merge_group(3, 3, "Entradas")
            merge_group(6, 3, "Salidas")
            merge_group(9, 3, "Inventario Final")

            def safe_int(v):
                try:
                    return int(v)
                except:
                    return 0

            def safe_float(v):
                try:
                    return float(v)
                except:
                    return 0.0

            row_idx = 2
            inventario_total = {}  # por producto

            for producto_id, cantidad_venta in venta_detalle:
                # Obtener inventarios disponibles por compra
                orden = "DESC" if metodo == "UEPS" else "ASC"
                cursor.execute(f"""
                    SELECT i.id, i.cantidad, i.precio_unitario, c.fecha
                    FROM inventarios i
                    JOIN compras c ON c.id_compra = i.id_compra
                    WHERE i.id_producto = ? AND i.cantidad > 0
                    ORDER BY c.fecha {orden}
                """, (producto_id,))
                inventarios = cursor.fetchall()

                cantidad_restante = cantidad_venta

                for inv_id, inv_cant, precio_unitario, fecha_compra in inventarios:
                    if cantidad_restante <= 0:
                        break
                    tomar = min(inv_cant, cantidad_restante)

                    # Entradas: cantidad original en inventario (puede haber sido parcialmente usado antes)
                    entrada_row = [
                        str(fecha_compra), "Compra", str(producto_id),
                        str(inv_cant), f"{precio_unitario:.2f}", f"{inv_cant * precio_unitario:.2f}",
                        "-", "-", "-",
                        "-", "-", "-"
                    ]
                    for col, val in enumerate(entrada_row):
                        self.preview_table.setItem(row_idx, col, QTableWidgetItem(str(val)))

                    # Salidas: cantidad tomada para venta
                    salida_row = [
                        "-", "Venta", str(producto_id),
                        "-", "-", "-",
                        str(tomar), f"{precio_unitario:.2f}", f"{tomar * precio_unitario:.2f}",
                        "-", "-", "-"
                    ]
                    for col, val in enumerate(salida_row):
                        self.preview_table.setItem(row_idx + 1, col, QTableWidgetItem(str(val)))

                    # Inventario final: inventario restante de esa compra
                    final_cant = inv_cant - tomar
                    inventario_total[producto_id] = inventario_total.get(producto_id, 0) + final_cant
                    final_row = [
                        "-", "Inventario Final", str(producto_id),
                        "-", "-", "-",
                        "-", "-", "-",
                        str(final_cant), f"{precio_unitario:.2f}", f"{final_cant * precio_unitario:.2f}"
                    ]
                    for col, val in enumerate(final_row):
                        self.preview_table.setItem(row_idx + 2, col, QTableWidgetItem(str(val)))

                    cantidad_restante -= tomar
                    row_idx += 3

            # Totales finales por producto
            for producto, cantidad in inventario_total.items():
                cursor.execute("""
                    SELECT precio_unitario
                    FROM detalle_compras dc
                    JOIN productos p ON p.id_producto = dc.id_producto
                    WHERE p.id_producto = ?
                    ORDER BY dc.id_compra DESC
                    LIMIT 1
                """, (producto,))
                row = cursor.fetchone()
                precio = safe_float(row[0]) if row else 0.0
                total_valor = cantidad * precio
                total_row = [
                    "-", "TOTAL", str(producto),
                    "-", "-", "-",
                    "-", "-", "-",
                    str(cantidad), f"{precio:.2f}", f"{total_valor:.2f}"
                ]
                for col, val in enumerate(total_row):
                    self.preview_table.setItem(row_idx, col, QTableWidgetItem(str(val)))
                row_idx += 1

            self.preview_table.resizeColumnsToContents()
            self.preview_table.resizeRowsToContents()
            self.preview_table.verticalHeader().setVisible(False)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error en la vista previa: {e}")
        finally:
            conn.close()

        self.preview_win.show()



    def liberar_venta(self, metodo="UEPS"):
        venta_id = self.venta_combo.currentData()
        if venta_id is None:
            QMessageBox.warning(self, "Error", "Seleccione una venta válida.")
            return

        # === Elegir la fecha de liberación ===
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QCalendarWidget, QDialogButtonBox
        fecha_dialog = QDialog(self)
        fecha_dialog.setWindowTitle("Seleccione la fecha de liberación")
        layout = QVBoxLayout()

        calendar = QCalendarWidget()
        calendar.setSelectedDate(QDate.currentDate())
        layout.addWidget(calendar)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(btns)
        fecha_dialog.setLayout(layout)

        fecha_str = None

        def aceptar():
            nonlocal fecha_str
            fecha = calendar.selectedDate()
            fecha_str = fecha.toString("yyyy-MM-dd")
            fecha_dialog.accept()

        btns.accepted.connect(aceptar)
        btns.rejected.connect(fecha_dialog.reject)

        if fecha_dialog.exec() != QDialog.DialogCode.Accepted or not fecha_str:
            return  # Cancelado por el usuario
        # ======================================

        conn = sqlite3.connect(db.DB_NAME)
        cursor = conn.cursor()
        try:
            # Evitar liberar dos veces la misma venta
            cursor.execute("SELECT id_liberacion FROM liberaciones WHERE id_venta = ?", (venta_id,))
            if cursor.fetchone():
                QMessageBox.warning(self, "Error", f"La venta #{venta_id} ya fue liberada anteriormente.")
                return

            # Obtener detalle de la venta
            cursor.execute("SELECT id_producto, cantidad FROM detalle_ventas WHERE id_venta = ?", (venta_id,))
            venta_detalle = cursor.fetchall()
            if not venta_detalle:
                QMessageBox.information(self, "Info", f"La venta #{venta_id} no tiene detalle.")
                return

            cantidad_total_venta = sum(row[1] for row in venta_detalle)

            # Insertar cabecera en liberaciones con la fecha elegida
            if self._table_has_column("liberaciones", "cantidad"):
                cursor.execute("""
                    INSERT INTO liberaciones (id_venta, total, cantidad, fecha)
                    VALUES (?, ?, ?, ?)
                """, (venta_id, 0.0, cantidad_total_venta, fecha_str))
            else:
                cursor.execute("""
                    INSERT INTO liberaciones (id_venta, total, fecha)
                    VALUES (?, ?, ?)
                """, (venta_id, 0.0, fecha_str))
            id_liberacion = cursor.lastrowid

            total_general = 0.0

            for producto_id, cantidad_requerida in venta_detalle:
                cantidad_restante = cantidad_requerida

                # Seleccionar inventarios disponibles según método y fecha de liberación
                orden = "DESC" if metodo == "UEPS" else "ASC"
                cursor.execute(f"""
                    SELECT id, cantidad, precio_unitario
                    FROM inventarios
                    WHERE id_producto = ?
                      AND cantidad > 0
                      AND fecha_compra <= ?
                    ORDER BY fecha_compra {orden}
                """, (producto_id, fecha_str))
                inventarios = cursor.fetchall()

                total_disponible = sum(inv[1] for inv in inventarios)
                if total_disponible < cantidad_requerida:
                    conn.rollback()
                    cursor.execute("DELETE FROM liberaciones WHERE id_liberacion = ?", (id_liberacion,))
                    conn.commit()
                    QMessageBox.warning(
                        self, "Error",
                        f"No hay suficiente inventario (hasta la fecha {fecha_str}) para el producto {producto_id} en la venta #{venta_id}."
                    )
                    return

                for inv_id, inv_cant, precio_unitario in inventarios:
                    if cantidad_restante <= 0:
                        break
                    tomar = min(inv_cant, cantidad_restante)
                    subtotal = tomar * (precio_unitario if precio_unitario else 0.0)

                    cursor.execute("""
                        INSERT INTO liberacion_inventarios (id_liberacion, id_inventario, cantidad, total)
                        VALUES (?, ?, ?, ?)
                    """, (id_liberacion, inv_id, tomar, subtotal))

                    cursor.execute("UPDATE inventarios SET cantidad = cantidad - ? WHERE id = ?", (tomar, inv_id))

                    cantidad_restante -= tomar
                    total_general += subtotal

            cursor.execute("UPDATE liberaciones SET total = ? WHERE id_liberacion = ?", (total_general, id_liberacion))
            conn.commit()
            QMessageBox.information(
                self, "Éxito",
                f"Venta #{venta_id} liberada correctamente (Liberación #{id_liberacion}) con método {metodo} en fecha {fecha_str}."
            )

        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Error", f"Ocurrió un error al liberar la venta:\n{e}")
        finally:
            conn.close()
            self.load_ventas()



    def eliminar_liberacion(self):
        conn = sqlite3.connect(db.DB_NAME)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT l.id_liberacion, v.id_venta, l.fecha
                FROM liberaciones l
                LEFT JOIN ventas v ON l.id_venta = v.id_venta
                ORDER BY l.id_liberacion ASC
            """)
            liberaciones = cursor.fetchall()

            if not liberaciones:
                QMessageBox.information(self, "Eliminar liberación", "No hay liberaciones registradas.")
                return

            liberacion_textos = [f"ID: {lib_id} | Venta: {venta_id} | Fecha: {fecha}"
                                 for lib_id, venta_id, fecha in liberaciones]

            item, ok = QInputDialog.getItem(
                self,
                "Eliminar liberación",
                "Seleccione la liberación a eliminar:",
                liberacion_textos,
                0,
                False
            )
            if not ok or not item:
                return

            id_liberacion = int(item.split("|")[0].replace("ID:", "").strip())

            cursor.execute("""
                SELECT id_inventario, cantidad
                FROM liberacion_inventarios
                WHERE id_liberacion = ?
            """, (id_liberacion,))
            detalles = cursor.fetchall()

            for id_inv, cantidad in detalles:
                cursor.execute("UPDATE inventarios SET cantidad = cantidad + ? WHERE id = ?", (cantidad, id_inv))

            cursor.execute("DELETE FROM liberacion_inventarios WHERE id_liberacion = ?", (id_liberacion,))
            cursor.execute("DELETE FROM liberaciones WHERE id_liberacion = ?", (id_liberacion,))

            conn.commit()
            QMessageBox.information(self, "Eliminar liberación", "Liberación eliminada y cantidades devueltas al inventario correctamente.")
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Error", f"Ocurrió un error al eliminar la liberación:\n{e}")
        finally:
            conn.close()
            self.load_ventas()

