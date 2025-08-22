import sqlite3
import os

DB_NAME = "sistema.db"

def create_connection():
    conn = sqlite3.connect(DB_NAME)
    return conn

def initialize_db():
    conn = create_connection()
    cursor = conn.cursor()

    # --- Tabla de Roles ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL
        )
    """)

    # --- Tabla de Usuarios ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role_id INTEGER NOT NULL,
            FOREIGN KEY (role_id) REFERENCES roles(id)
        )
    """)

    # --- Tabla de Productos ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            proveedor_id INTEGER,
            FOREIGN KEY (proveedor_id) REFERENCES proveedores(id_proveedor)
        )
    """)

    # --- Tabla de Proveedores ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proveedores (
            id_proveedor INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            contacto TEXT,
            direccion TEXT
        )
    """)

    # --- Tabla de Clientes ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            contacto TEXT
        )
    """)

    # --- Tabla de Ventas ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id_venta INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            usuario_id INTEGER NOT NULL,
            cliente_id INTEGER,
            total REAL NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY (cliente_id) REFERENCES clientes(id_cliente)
        )
    """)

    # --- Detalle de Ventas ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detalle_ventas (
            id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
            id_venta INTEGER NOT NULL,
            id_producto INTEGER NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_unitario REAL NOT NULL,
            FOREIGN KEY (id_venta) REFERENCES ventas(id_venta),
            FOREIGN KEY (id_producto) REFERENCES productos(id_producto)
        )
    """)

    # --- Tabla de Compras ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compras (
            id_compra INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            usuario_id INTEGER NOT NULL,
            proveedor_id INTEGER,
            total REAL NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY (proveedor_id) REFERENCES proveedores(id_proveedor)
        )
    """)

    # --- Detalle de Compras ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detalle_compras (
            id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
            id_compra INTEGER NOT NULL,
            id_producto INTEGER NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_unitario REAL NOT NULL,
            FOREIGN KEY (id_compra) REFERENCES compras(id_compra),
            FOREIGN KEY (id_producto) REFERENCES productos(id_producto)
        )
    """)

    # --- NUEVA TABLA: Inventarios ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_producto INTEGER NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_unitario REAL NOT NULL,
            fecha_compra TEXT NOT NULL,
            id_compra INTEGER NOT NULL,
            FOREIGN KEY (id_producto) REFERENCES productos(id_producto),
            FOREIGN KEY (id_compra) REFERENCES compras(id_compra)
        )
    """)
    # --- NUEVA TABLA: Liberaciones ---  
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS liberaciones (
            id_liberacion INTEGER PRIMARY KEY AUTOINCREMENT,
            id_venta INTEGER NOT NULL,
            total REAL NOT NULL,
            fecha TEXT NOT NULL,
            FOREIGN KEY (id_venta) REFERENCES ventas(id_venta)
        );
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS liberacion_inventarios (
            id_relacion INTEGER PRIMARY KEY AUTOINCREMENT,
            id_liberacion INTEGER NOT NULL,
            id_inventario INTEGER NOT NULL,
            cantidad INTEGER NOT NULL,
            total REAL NOT NULL,
            FOREIGN KEY (id_liberacion) REFERENCES liberaciones(id_liberacion),
            FOREIGN KEY (id_inventario) REFERENCES inventarios(id)
        );
    """)
    

    # Insertar roles si no existen
    roles = ["Administrador", "Usuario", "Invitado"]
    for role in roles:
        cursor.execute("INSERT OR IGNORE INTO roles (nombre) VALUES (?)", (role,))

    # Crear usuario ADMIN si no existe
    cursor.execute("SELECT * FROM usuarios WHERE username = 'ADMIN'")
    admin_exists = cursor.fetchone()
    if not admin_exists:
        cursor.execute("SELECT id FROM roles WHERE nombre = 'Administrador'")
        admin_role_id = cursor.fetchone()[0]
        cursor.execute("""
            INSERT INTO usuarios (username, password, role_id)
            VALUES (?, ?, ?)
        """, ("ADMIN", "UMG2025", admin_role_id))

    conn.commit()
    conn.close()

def login(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT username, roles.nombre
        FROM usuarios
        JOIN roles ON usuarios.role_id = roles.id
        WHERE username = ? AND password = ?
    """, (username, password))
    result = cursor.fetchone()
    conn.close()
    return result

def crear_usuario(username, password, rol_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO usuarios (username, password, role_id) VALUES (?, ?, ?)",
        (username, password, rol_id)
    )
    conn.commit()
    conn.close()

def obtener_roles():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM roles")
    roles = cursor.fetchall()
    conn.close()
    return roles


if __name__ == "__main__":
    initialize_db()
    print("Base de datos inicializada correctamente.")
