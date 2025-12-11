import psycopg2

def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="flask_shop",
        user="tienda_user",
        password="12345"   # o la contraseña que pusiste
    )
