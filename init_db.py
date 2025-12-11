import psycopg2
from models import get_db_connection

# CREAR TABLAS EN POSTGRES

def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()

    # Tabla usuarios
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(50),
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(200) NOT NULL
        );
    """)

    # Tabla productos
    cur.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            precio NUMERIC(10,2) NOT NULL,
            descripcion TEXT
        );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("Tablas creadas correctamente.")


if __name__ == "__main__":
    create_tables()
