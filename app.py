import os
import mercadopago
import psycopg2
from functools import wraps
from flask import Flask, render_template, request, redirect, session, url_for

# ---------------------------------------
#   CONFIG GLOBAL
# ---------------------------------------
BACK_URL_BASE = os.getenv("BACK_URL_BASE", "http://localhost:5000")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret")

mp = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))

# ---------------------------------------
#   CONEXIÓN DB (RENDER)
# ---------------------------------------
def conectar():
    return psycopg2.connect(
        os.getenv("DATABASE_URL"),
        sslmode="require"
    )


# ---------------------------------------
#   SOLO ADMIN
# ---------------------------------------
def solo_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "usuario" not in session or not session["usuario"].get("es_admin"):
            return redirect("/productos")
        return f(*args, **kwargs)
    return wrapper

# ---------------------------------------
#   RUTAS BÁSICAS
# ---------------------------------------
@app.route("/")
def inicio():
    return redirect("/productos")

@app.route("/productos")
def productos():
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nombre, descripcion, precio, imagen
        FROM productos
        ORDER BY id
    """)
    productos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("productos.html", productos=productos, usuario=session.get("usuario"))

# ---------------------------------------
#   CARRITO
# ---------------------------------------
@app.route("/agregar_carrito", methods=["POST"])
def agregar_carrito():
    if "usuario" not in session:
        return redirect("/login")

    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO carrito (usuario_id, producto_id, cantidad)
        VALUES (%s, %s, %s)
    """, (
        session["usuario"]["id"],
        request.form["id"],
        request.form.get("cantidad", 1)
    ))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/productos")

@app.route("/carrito")
def ver_carrito():
    if "usuario" not in session:
        return redirect("/login")

    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            carrito.id,
            productos.nombre,
            productos.precio,
            carrito.cantidad,
            productos.imagen
        FROM carrito
        JOIN productos ON carrito.producto_id = productos.id
        WHERE carrito.usuario_id=%s
    """, (session["usuario"]["id"],))
    carrito = cur.fetchall()
    cur.close()
    conn.close()

    total = sum(float(p) * int(c) for _, _, p, c, _ in carrito)
    return render_template("carrito.html", carrito=carrito, total=total)

@app.route("/quitar/<int:carrito_id>", methods=["POST"])
def quitar(carrito_id):
    if "usuario" not in session:
        return redirect("/login")

    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM carrito
        WHERE id=%s AND usuario_id=%s
    """, (carrito_id, session["usuario"]["id"]))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/carrito")

# ---------------------------------------
#   LOGIN
# ---------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nombre, email, es_admin
            FROM usuarios
            WHERE email=%s AND password=%s
        """, (request.form["email"], request.form["password"]))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            session["usuario"] = {
                "id": user[0],
                "nombre": user[1],
                "email": user[2],
                "es_admin": user[3]
            }
            return redirect("/productos")

    return render_template("login.html")

# ---------------------------------------
#   MERCADO PAGO
# ---------------------------------------
@app.route("/pago", methods=["GET", "POST"])
def pago():
    if "usuario" not in session:
        return redirect("/login")

    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT productos.nombre, productos.precio, carrito.cantidad
        FROM carrito
        JOIN productos ON carrito.producto_id = productos.id
        WHERE carrito.usuario_id=%s
    """, (session["usuario"]["id"],))
    items = cur.fetchall()
    cur.close()
    conn.close()

    if not items:
        return redirect("/carrito")

    total = sum(float(p) * int(c) for _, p, c in items)

    if request.method == "POST":
        preference = mp.preference().create({
            "items": [{
                "title": nombre,
                "quantity": int(cantidad),
                "unit_price": float(precio),
                "currency_id": "MXN"
            } for nombre, precio, cantidad in items],

            "payer": {
                "email": session["usuario"]["email"]
            },

            "back_urls": {
                "success": f"{BACK_URL_BASE}/pago_exitoso",
                "failure": f"{BACK_URL_BASE}/pago_error",
                "pending": f"{BACK_URL_BASE}/pago_pendiente"
            },

            "notification_url": f"{BACK_URL_BASE}/mp/webhook",
            "external_reference": f"user_{session['usuario']['id']}"
        })

        pref_resp = preference["response"]

        if "init_point" in pref_resp:
            return redirect(pref_resp["init_point"])
        else:
            print(pref_resp)
            return "Error al generar la preferencia"

    return render_template("pago.html", total=total, usuario=session.get("usuario"))

# ---------------------------------------
#   RESULTADOS DE PAGO
# ---------------------------------------
@app.route("/pago_exitoso")
def pago_exitoso():
    return "Pago aprobado ✅"

@app.route("/pago_error")
def pago_error():
    return "Pago rechazado ❌"

@app.route("/pago_pendiente")
def pago_pendiente():
    return "Pago pendiente ⏳"

# ---------------------------------------
#   WEBHOOK MP
# ---------------------------------------
@app.route("/mp/webhook", methods=["POST"])
def mp_webhook():
    print("📩 Webhook Mercado Pago:", request.json)
    return "OK", 200

# ---------------------------------------
#   LOGOUT
# ---------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/productos")


