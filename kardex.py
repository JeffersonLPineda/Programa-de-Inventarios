from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QHBoxLayout, QDateEdit, QFileDialog
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QDate, Qt
import sqlite3
import database as db
import os
import sys

# Exportaciones
from openpyxl import Workbook
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter, landscape



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

def resource_path(relative_path):
    """Obtiene la ruta absoluta del recurso, compatible con PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class KardexWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kardex de Ventas")
        self.setMinimumSize(1100, 650)
        self.setWindowIcon(QIcon(resource_path("mainlogo.ico")))

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()

        # Selección de rango de fechas
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Fecha inicio:"))
        self.fecha_inicio = QDateEdit()
        self.fecha_inicio.setCalendarPopup(True)
        self.fecha_inicio.setDate(QDate.currentDate().addDays(-30))
        date_layout.addWidget(self.fecha_inicio)

        date_layout.addWidget(QLabel("Fecha fin:"))
        self.fecha_fin = QDateEdit()
        self.fecha_fin.setCalendarPopup(True)
        self.fecha_fin.setDate(QDate.currentDate())
        date_layout.addWidget(self.fecha_fin)

        layout.addLayout(date_layout)

        # Botón mostrar Kardex
        btn_mostrar = QPushButton("Mostrar Kardex")
        btn_mostrar.clicked.connect(self.mostrar_kardex)
        layout.addWidget(btn_mostrar)

        # Botones exportación
        export_layout = QHBoxLayout()
        btn_excel = QPushButton("Exportar a Excel")
        btn_excel.clicked.connect(self.exportar_excel)
        export_layout.addWidget(btn_excel)

        btn_pdf = QPushButton("Exportar a PDF")
        btn_pdf.clicked.connect(self.exportar_pdf)
        export_layout.addWidget(btn_pdf)

        layout.addLayout(export_layout)

        # Tabla Kardex
        self.kardex_table = QTableWidget()
        layout.addWidget(self.kardex_table)

        central.setLayout(layout)


        
    def mostrar_kardex(self):
        conn = sqlite3.connect(db.DB_NAME)
        cursor = conn.cursor()

        fecha_inicio = self.fecha_inicio.date().toString("yyyy-MM-dd")
        fecha_fin = self.fecha_fin.date().toString("yyyy-MM-dd")

        # ================================
        # Movimientos con liberaciones
        # ================================
        cursor.execute("""
            SELECT
                l.fecha AS fecha_liberacion,
                l.id_liberacion,
                v.id_venta,
                p.nombre AS producto,
                c.id_compra AS id_compra,
                dc.cantidad AS compra_cantidad,
                dc.precio_unitario AS compra_precio,
                (dc.cantidad * dc.precio_unitario) AS compra_total,
                li.cantidad AS salida_cantidad,
                i.precio_unitario AS salida_precio,
                (li.cantidad * i.precio_unitario) AS salida_total
            FROM liberaciones l
            JOIN liberacion_inventarios li ON li.id_liberacion = l.id_liberacion
            JOIN inventarios i ON i.id = li.id_inventario
            JOIN compras c ON c.id_compra = i.id_compra
            JOIN detalle_compras dc ON dc.id_compra = c.id_compra AND dc.id_producto = i.id_producto
            JOIN productos p ON p.id_producto = i.id_producto
            LEFT JOIN detalle_ventas dv ON dv.id_venta = l.id_venta AND dv.id_producto = i.id_producto
            LEFT JOIN ventas v ON v.id_venta = l.id_venta
            WHERE l.fecha BETWEEN ? AND ?
            ORDER BY l.fecha ASC, l.id_liberacion ASC, i.id ASC
        """, (fecha_inicio, fecha_fin))
        filas = cursor.fetchall()

        # ================================
        # Todas las compras (para visualización y total)
        # ================================
        cursor.execute("""
            SELECT
                c.fecha AS fecha_compra,
                p.nombre AS producto,
                c.id_compra AS id_compra,
                dc.cantidad AS compra_cantidad,
                dc.precio_unitario AS compra_precio,
                (dc.cantidad * dc.precio_unitario) AS compra_total
            FROM compras c
            JOIN detalle_compras dc ON dc.id_compra = c.id_compra
            JOIN productos p ON p.id_producto = dc.id_producto
            WHERE c.fecha BETWEEN ? AND ?
            ORDER BY c.fecha ASC, c.id_compra ASC
        """, (fecha_inicio, fecha_fin))
        todas_compras = cursor.fetchall()

        if not filas and not todas_compras:
            QMessageBox.information(self, "Info", "No hay movimientos en el rango de fechas.")
            self.kardex_table.clear()
            self.kardex_table.setRowCount(0)
            self.kardex_table.setColumnCount(0)
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

        # Pre-asignar filas con un buffer suficiente
        total_rows = (len(filas) * 3) + len(todas_compras) + 50
        self.kardex_table.setColumnCount(len(columnas))
        self.kardex_table.setRowCount(total_rows)

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

        def merge_group(start_col, span, text):
            self.kardex_table.setSpan(0, start_col, 1, span)
            itm = self.kardex_table.item(0, start_col)
            if itm:
                itm.setText(text)
            else:
                self.kardex_table.setItem(0, start_col, QTableWidgetItem(text))

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

        # inventario_actual: map id_compra -> (cantidad_restante, precio_unitario)
        inventario_actual = {}
        # inventario_total: producto -> cantidad total final (sum compras - sum salidas)
        inventario_total = {}
        row_idx = 2

        # ================================
        # Mostrar todas las compras (estéticas, en su fecha original)
        # ================================
        for (fecha_compra, producto, id_compra, compra_cantidad, compra_precio, compra_total) in todas_compras:
            compra_cant = safe_int(compra_cantidad)
            compra_prec = safe_float(compra_precio)
            compra_tot = safe_float(compra_total)

            # Aumenta inventario_total (luego las ventas lo restarán)
            inventario_total[producto] = inventario_total.get(producto, 0) + compra_cant

            compra_row = [
                str(fecha_compra), "Compra", str(producto),
                str(compra_cant), f"{compra_prec:.2f}", f"{compra_tot:.2f}",
                "-", "-", "-",
                str(compra_cant), f"{compra_prec:.2f}", f"{compra_tot:.2f}"
            ]
            for col, val in enumerate(compra_row):
                self.kardex_table.setItem(row_idx, col, QTableWidgetItem(str(val)))
            row_idx += 1

        # ================================
        # Procesar ventas: para cada uso de inventario mostrar copia de la compra (estética) justo antes de la venta,
        # luego actualizar inventario_actual y descontar del inventario_total
        # ================================
        for (fecha_lib, id_liberacion, id_venta, producto, id_compra,
            compra_cantidad, compra_precio, compra_total,
            salida_cantidad, salida_precio, salida_total) in filas:

            compra_cant = safe_int(compra_cantidad)
            compra_prec = safe_float(compra_precio)
            compra_tot = safe_float(compra_total)

            # stock antes de la venta: si ya está registrado en inventario_actual usamos su cantidad actual,
            # si no, usamos la cantidad original de la compra (compra_cant)
            stock_before = inventario_actual.get(id_compra, (compra_cant, compra_prec))[0]
            stock_prec = inventario_actual.get(id_compra, (compra_cant, compra_prec))[1]

            # Copiar compra antes de la venta (estética) usando stock real antes de restar
            compra_row = [
                str(fecha_lib), "Compra", str(producto),
                str(stock_before), f"{stock_prec:.2f}", f"{stock_before * stock_prec:.2f}",
                "-", "-", "-",
                str(stock_before), f"{stock_prec:.2f}", f"{stock_before * stock_prec:.2f}"
            ]
            for col, val in enumerate(compra_row):
                self.kardex_table.setItem(row_idx, col, QTableWidgetItem(str(val)))
            row_idx += 1

            # Registrar stock real en inventario_actual si no estaba
            if id_compra not in inventario_actual:
                inventario_actual[id_compra] = (compra_cant, compra_prec)

            # Procesar la salida (venta)
            salida_cant = safe_int(salida_cantidad)
            salida_prec = safe_float(salida_precio)
            salida_tot = safe_float(salida_total)

            cur_cant, cur_prec = inventario_actual.get(id_compra, (0, salida_prec))
            new_cant = cur_cant - salida_cant
            if new_cant < 0:
                new_cant = 0
            inventario_actual[id_compra] = (new_cant, cur_prec)

            # Actualizar inventario_total por producto (restar salida)
            inventario_total[producto] = max(inventario_total.get(producto, 0) - salida_cant, 0)

            # Preparar fila de venta con inventario final para esa compra
            final_row = ["-", "-", "-"] if new_cant <= 0 else [
                str(new_cant), f"{cur_prec:.2f}", f"{new_cant * cur_prec:.2f}"
            ]

            venta_row = [
                str(fecha_lib), "Venta", str(producto),
                "-", "-", "-",
                str(salida_cant) if salida_cant else "-",
                f"{salida_prec:.2f}" if salida_cant else "-",
                f"{salida_tot:.2f}" if salida_cant else "-",
                final_row[0], final_row[1], final_row[2]
            ]
            for col, val in enumerate(venta_row):
                self.kardex_table.setItem(row_idx, col, QTableWidgetItem(str(val)))
            row_idx += 1

        # ================================
        # TOTAL por producto (UNA fila por PRODUCTO) — valor: suma del saldo restante de cada compra (cada compra cuenta una sola vez)
        # ================================
        productos_unicos = list(dict.fromkeys([p for (_, p, *_) in todas_compras] + [p for (_, p, *_) in [(f[3], f[3], *[]) for f in filas] if p]))  # priorizar orden de compras
        # Fallback: si no salieron productos_unicos correctamente, obtener desde inventario_total keys
        if not productos_unicos:
            productos_unicos = list(inventario_total.keys())

        for producto in productos_unicos:
            total_cantidad = 0
            total_valor = 0.0

            # Recorremos todas las compras del producto, sumando saldo restante (si fue usado) o cantidad completa (si nunca fue usada)
            for (fecha_compra, prod, id_compra, cant, prec, _) in todas_compras:
                if prod != producto:
                    continue
                if id_compra in inventario_actual:
                    cant_rest, prec_rest = inventario_actual[id_compra]
                    if cant_rest > 0:
                        total_cantidad += cant_rest
                        total_valor += cant_rest * prec_rest
                else:
                    cant_ini = safe_int(cant)
                    prec_ini = safe_float(prec)
                    total_cantidad += cant_ini
                    total_valor += cant_ini * prec_ini

            # Además puede haber compras fuera de 'todas_compras' que fueron usadas en 'filas' (raro porque todas_compras viene de rango),
            # pero para seguridad revisamos inventario_actual por compras no listadas en todas_compras:
            for id_compra, (cant_rest, prec_rest) in inventario_actual.items():
                # obtener producto de esa compra (si no está en las compras listadas)
                cursor.execute("""
                    SELECT p.nombre FROM detalle_compras dc
                    JOIN productos p ON p.id_producto = dc.id_producto
                    WHERE dc.id_compra = ? LIMIT 1
                """, (id_compra,))
                row = cursor.fetchone()
                if row and row[0] == producto:
                    # Si esta compra no estaba en todas_compras (por cualquier razón), sumamos su saldo restante
                    # pero cuidamos de no volver a sumar compras ya contadas: comprobamos existencia por id_compra en todas_compras
                    ids_listadas = {c[2] for c in todas_compras}
                    if id_compra not in ids_listadas and cant_rest > 0:
                        total_cantidad += cant_rest
                        total_valor += cant_rest * prec_rest

            if total_cantidad > 0:
                total_row = [
                    "-", "TOTAL", producto,
                    "-", "-", "-",
                    "-", "-", "-",
                    str(total_cantidad), "-", f"{total_valor:.2f}"
                ]
                for col, val in enumerate(total_row):
                    self.kardex_table.setItem(row_idx, col, QTableWidgetItem(str(val)))
                row_idx += 1

        conn.close()
        self.kardex_table.resizeColumnsToContents()
        self.kardex_table.resizeRowsToContents()
        self.kardex_table.verticalHeader().setVisible(False)


    # ================================
    # Exportar a Excel
    # ================================
    def exportar_excel(self):
        if self.kardex_table.rowCount() == 0:
            QMessageBox.warning(self, "Error", "No hay datos para exportar.")
            return

        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar Kardex en Excel", "", "Archivos Excel (*.xlsx)")
        if not ruta:
            return  # Usuario canceló

        wb = Workbook()
        ws = wb.active
        ws.title = "Kardex"

        # Guardar encabezados
        for col in range(self.kardex_table.columnCount()):
            header = self.kardex_table.item(1, col)
            if header:
                ws.cell(row=1, column=col+1, value=header.text())

        # Guardar datos
        for row in range(2, self.kardex_table.rowCount()):
            for col in range(self.kardex_table.columnCount()):
                item = self.kardex_table.item(row, col)
                if item:
                    ws.cell(row=row, column=col+1, value=item.text())

        wb.save(ruta)
        QMessageBox.information(self, "Éxito", f"Kardex exportado a:\n{ruta}")


    # ================================
    # Exportar a PDF
    # ================================
    def exportar_pdf(self):
        if self.kardex_table.rowCount() == 0:
            QMessageBox.warning(self, "Error", "No hay datos para exportar.")
            return

        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar Kardex en PDF", "", "Archivos PDF (*.pdf)")
        if not ruta:
            return  # Usuario canceló

        data = []

        # Encabezados (fila 1 de la tabla UI)
        headers = []
        for col in range(self.kardex_table.columnCount()):
            header = self.kardex_table.item(1, col)
            headers.append(header.text() if header else "")
        data.append(headers)

        # Datos (desde la fila 2 en adelante)
        for row in range(2, self.kardex_table.rowCount()):
            fila = []
            fila_vacia = True
            for col in range(self.kardex_table.columnCount()):
                item = self.kardex_table.item(row, col)
                texto = item.text() if item else ""
                if texto.strip():
                    fila_vacia = False
                fila.append(texto)
            # solo añadir filas que tengan algo (evita filas vacías del buffer)
            if not fila_vacia:
                data.append(fila)

        # Usar landscape para que la página quede horizontal
        page_size = landscape(letter)
        left_margin = right_margin = top_margin = bottom_margin = 18  # márgenes en puntos

        doc = SimpleDocTemplate(ruta, pagesize=page_size,
                                leftMargin=left_margin, rightMargin=right_margin,
                                topMargin=top_margin, bottomMargin=bottom_margin)

        elementos = []
        styles = getSampleStyleSheet()
        elementos.append(Paragraph("Reporte de Kardex", styles["Heading1"]))
        elementos.append(Spacer(1, 12))

        # calcular ancho util (ancho de página menos márgenes)
        page_width, page_height = page_size
        usable_width = page_width - left_margin - right_margin

        # distribuir columnas uniformemente (puedes ajustar si quieres pesos distintos)
        col_count = max(1, self.kardex_table.columnCount())
        col_widths = [usable_width / col_count] * col_count

        tabla = Table(data, colWidths=col_widths, repeatRows=1)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ]))

        elementos.append(tabla)
        doc.build(elementos)

        QMessageBox.information(self, "Éxito", f"Kardex exportado a:\n{ruta}")
