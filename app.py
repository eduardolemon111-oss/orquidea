from flask import Flask, render_template, request, redirect, session, url_for
import psycopg2

app = Flask(__name__)
app.secret_key = "superclave_personalizada_987"


def conectar():
    return psycopg2.connect(
        dbname="flask_shop",
        user="tienda_user",
        password="12345",
        host="localhost"
    )


@app.route("/")
def inicio():
    return redirect("/productos")


@app.route("/productos")
def productos():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT id, nombre, descripcion, precio, imagen FROM productos ORDER BY id")
    productos = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("productos.html", productos=productos)


@app.route("/agregar_carrito", methods=["POST"])
def agregar_carrito():
    if "usuario" not in session:
        return redirect("/login?next=productos")

    usuario_id = session["usuario"]["id"]
    producto_id = int(request.form["id"])
    cantidad = int(request.form.get("cantidad", 1))

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT id FROM carrito
        WHERE usuario_id = %s AND producto_id = %s
    """, (usuario_id, producto_id))

    row = cur.fetchone()

    if row:
        cur.execute("""
            UPDATE carrito
            SET cantidad = cantidad + %s
            WHERE usuario_id = %s AND producto_id = %s
        """, (cantidad, usuario_id, producto_id))
    else:
        cur.execute("""
            INSERT INTO carrito (usuario_id, producto_id, cantidad)
            VALUES (%s, %s, %s)
        """, (usuario_id, producto_id, cantidad))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/productos")


@app.route("/carrito")
def carrito():
    if "usuario" not in session:
        return redirect("/login")

    usuario_id = session["usuario"]["id"]

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT carrito.id,
               productos.id,
               productos.nombre,
               productos.descripcion,
               productos.precio,
               productos.imagen,
               carrito.cantidad
        FROM carrito
        JOIN productos ON carrito.producto_id = productos.id
        WHERE carrito.usuario_id = %s
        ORDER BY carrito.id
    """, (usuario_id,))

    carrito = cur.fetchall()

    cur.close()
    conn.close()

    total = sum(item[4] * item[6] for item in carrito)

    return render_template("carrito.html", carrito=carrito, total=total)


@app.route("/quitar/<int:id>", methods=["POST"])
def quitar(id):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("DELETE FROM carrito WHERE id = %s", (id,))
    conn.commit()

    cur.close()
    conn.close()

    return redirect("/carrito")


@app.route("/finalizar")
def finalizar():
    if "usuario" not in session:
        return redirect("/login?next=pago")

    return redirect("/pago")


@app.route("/login", methods=["GET", "POST"])
def login():
    next_page = request.args.get("next", "productos")

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = conectar()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, nombre, email, password
            FROM usuarios
            WHERE email = %s AND password = %s
        """, (email, password))

        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            session["usuario"] = {
                "id": user[0],
                "nombre": user[1],
                "email": user[2]
            }
            return redirect("/" + next_page)

        return "Usuario o contraseña incorrectos"

    return render_template("login.html", next=next_page)


@app.route("/register", methods=["GET", "POST"])
def register():
    next_page = request.args.get("next", "productos")

    if request.method == "POST":
        nombre = request.form.get("nombre")
        email = request.form.get("email")
        password = request.form.get("password")

        conn = conectar()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO usuarios (nombre, email, password)
            VALUES (%s, %s, %s)
        """, (nombre, email, password))

        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for("login", next=next_page))

    return render_template("register.html", next=next_page)


@app.route("/pago", methods=["GET", "POST"])
def pago():
    if "usuario" not in session:
        return redirect("/login?next=pago")

    usuario = session["usuario"]
    usuario_id = usuario["id"]

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT carrito.id,
               productos.id,
               productos.nombre,
               productos.precio,
               productos.imagen,
               carrito.cantidad
        FROM carrito
        JOIN productos ON carrito.producto_id = productos.id
        WHERE carrito.usuario_id = %s
        ORDER BY carrito.id
    """, (usuario_id,))

    items = cur.fetchall()

    cur.close()
    conn.close()

    total = sum(item[3] * item[5] for item in items)

    if request.method == "POST":
        return redirect("/pago_exitoso")

    return render_template("pago.html", usuario=usuario, productos=items, total=total)


@app.route("/pago_exitoso")
def pago_exitoso():
    if "usuario" not in session:
        return redirect("/login")

    usuario_id = session["usuario"]["id"]

    conn = conectar()
    cur = conn.cursor()

    cur.execute("DELETE FROM carrito WHERE usuario_id = %s", (usuario_id,))
    conn.commit()

    cur.close()
    conn.close()

    return render_template("exito.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/productos")


if __name__ == "__main__":
    app.run(debug=True)
