from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DecimalField, TextAreaField
from wtforms.validators import DataRequired, Email, Length

# ------------------------------
# FORMULARIO DE REGISTRO
# ------------------------------

class RegisterForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Contraseña", validators=[DataRequired(), Length(min=4)])
    submit = SubmitField("Registrarse")

# ------------------------------
# FORMULARIO DE LOGIN
# ------------------------------

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Contraseña", validators=[DataRequired()])
    submit = SubmitField("Iniciar Sesión")

# ------------------------------
# FORMULARIO DE PRODUCTOS
# ------------------------------

class ProductForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired()])
    precio = DecimalField("Precio", validators=[DataRequired()])
    descripcion = TextAreaField("Descripción")
    submit = SubmitField("Guardar Producto")
