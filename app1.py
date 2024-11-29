from flask import Flask, render_template, send_file, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask import make_response
import io
from io import BytesIO
from sqlalchemy import distinct

app = Flask(__name__)
#app.config['SECRET_KEY'] = 'mi_secreto_super_seguro'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/controlm'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://kevinmaster:Cu1121822307.@kevinmaster.mysql.pythonanywhere-services.com/kevinmaster$controlm'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Modelos de la base de datos (asumiendo que ya se han cambiado en models.py)
class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    ciudad = db.Column(db.String(100))

    def __init__(self, username, email, password, ciudad):
        self.username = username
        self.email = email
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        self.ciudad = ciudad

class Maquina(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Esta es la columna ID de la tabla Maquina
    nombre = db.Column(db.String(100), nullable=False)
    ciudad = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(100), nullable=False)
    tipo_id = db.Column(db.Integer, nullable=True)  # ID opcional si lo necesitas

    # Relación con los mantenimiento
    mantenimiento = db.relationship('Mantenimiento', backref='maquina', lazy=True)


class Mantenimiento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))  # Relación con Usuario
    ciudad = db.Column(db.String(100), nullable=False)
    mantenimiento = db.Column(db.String(500))
    fecha = db.Column(db.DateTime, default=datetime.utcnow) 

    # Relación con Maquina, usando el id de la tabla Maquina
    maquina_id = db.Column(db.Integer, db.ForeignKey('maquina.id'))  # Relación con Maquina usando la columna `id`
    maquina_nombre = db.Column(db.String(100))  # Aquí guardamos el nombre de la máquina, como lo deseas

    # Relaciones
    usuario = db.relationship('Usuario', backref='mantenimiento')
    






# Rutas y lógica de la aplicación

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@app.before_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Usuario.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Nombre de usuario o contraseña incorrectos.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        ciudad = request.form['ciudad']

        existing_user = Usuario.query.filter_by(username=username).first()
        existing_email = Usuario.query.filter_by(email=email).first()

        if existing_user:
            flash('El nombre de usuario ya está en uso. Elige otro.', 'danger')
            return redirect(url_for('register'))

        if existing_email:
            flash('El correo electrónico ya está registrado. Usa otro correo.', 'danger')
            return redirect(url_for('register'))

        new_user = Usuario(username=username, email=email, password=password, ciudad=ciudad)
        db.session.add(new_user)
        db.session.commit()

        flash('Registro exitoso! Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.username)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect(url_for('login'))

@app.route('/ciudad', methods=['GET', 'POST'])
@login_required
def ciudad():
    if request.method == 'POST':
        # Obtener datos del formulario
        nueva_ciudad = request.form.get('ciudad')
        nuevas_maquinas = request.form.getlist('maquinas[]')
        tipo_existente = request.form.get('tipo')  # Tipo seleccionado
        nuevo_tipo = request.form.get('nuevo_tipo')  # Nuevo tipo si lo creamos

        # Validar que los campos obligatorios no estén vacíos
        if not nueva_ciudad or not nuevas_maquinas:
            flash('La ciudad y las máquinas no pueden estar vacías.', 'danger')
            return redirect(url_for('ciudad'))

        # Determinar el tipo y tipo_id
        tipo_final = None
        tipo_id = None

        # Lógica para manejar el tipo de máquina
        if nuevo_tipo:
            # Si hay un nuevo tipo, lo usamos directamente
            tipo_final = nuevo_tipo
            tipo_id = None  # O asigna el tipo_id que desees si lo necesitas
        elif tipo_existente:
            # Si se selecciona un tipo existente, usamos el valor seleccionado
            tipo_final = tipo_existente
            tipo_id = 1  # O asignar el ID correspondiente si es necesario
        else:
            flash('Debe seleccionar un tipo existente o agregar uno nuevo.', 'danger')
            return redirect(url_for('ciudad'))

        # Crear las máquinas asociadas a la ciudad y el tipo
        for maquina in nuevas_maquinas:
            if maquina.strip():  # Evitar agregar máquinas con nombres vacíos
                nueva_maquina_obj = Maquina(
                    ciudad=nueva_ciudad, 
                    nombre=maquina.strip(),
                    tipo=tipo_final,  # Guardar el nombre del tipo en la columna 'tipo'
                    tipo_id=tipo_id   # Guardar el tipo_id si lo usas
                )
                db.session.add(nueva_maquina_obj)

        db.session.commit()
        flash('Ciudad, máquinas y tipo de máquina agregados con éxito.', 'success')
        return redirect(url_for('ciudad'))

    # Enviar los tipos de máquina existentes al template
    return render_template('ciudad.html')




@app.route('/mantenimiento', methods=['GET', 'POST'])
@login_required
def mantenimiento():
    if request.method == 'POST':
        ciudad = request.form['ciudad']
        maquina_nombre = request.form['maquina_nombre']
        mantenimiento_desc = request.form['mantenimiento']

        # Obtener la máquina correspondiente por nombre (asumiendo que el nombre es único)
        maquina = Maquina.query.filter_by(nombre=maquina_nombre, ciudad=ciudad).first()

        if maquina:
            # Crear un nuevo registro de mantenimiento usando el nombre de la máquina
            nuevo_mantenimiento = Mantenimiento(
                usuario_id=current_user.id,  # ID del usuario actual
                maquina_id=maquina.id,  # El id de la máquina relacionada
                maquina_nombre=maquina_nombre,  # Si deseas guardar también el nombre
                ciudad=ciudad,
                mantenimiento=mantenimiento_desc,
                fecha=datetime.now()  # Fecha actual
            )

            db.session.add(nuevo_mantenimiento)
            db.session.commit()

            flash('Mantenimiento registrado con éxito', 'success')
        else:
            flash('La máquina no existe en la ciudad seleccionada.', 'danger')

        return redirect(url_for('mantenimiento'))

    ciudades = db.session.query(Maquina.ciudad).distinct().all()
    ciudades = [ciudad[0] for ciudad in ciudades]
    return render_template('mantenimiento.html', ciudades=ciudades)



@app.route('/get_maquinas/<ciudad>', methods=['GET'])
@login_required
def get_maquinas(ciudad):
    maquinas = Maquina.query.filter_by(ciudad=ciudad).all()  # Filtra por nombre de ciudad
    maquinas_data = [{"id": maquina.id, "nombre": maquina.nombre} for maquina in maquinas]
    return jsonify(maquinas=maquinas_data)


@app.route('/ver_maquinas', methods=['GET'])
@login_required
def ver_maquinas():
    ciudad = request.args.get('ciudad')  # Obtener el parámetro 'ciudad' desde la URL (GET)
    if ciudad:
        maquinas = Maquina.query.filter_by(ciudad=ciudad).all()  # Filtrar por nombre de ciudad
    else:
        maquinas = Maquina.query.all()  # Si no hay filtro, mostrar todas las máquinas

    # Obtener todas las ciudades disponibles para el filtro
    ciudades = db.session.query(Maquina.ciudad).distinct().all()


    return render_template('ver_maquinas.html', maquinas=maquinas, ciudades=ciudades)


def obtener_reporte(fecha_inicio=None, fecha_fin=None, ciudad=None):
    query = Mantenimiento.query

    # Filtramos por las fechas de inicio y fin, si están disponibles
    if fecha_inicio:
        # Aseguramos que solo se comparen las fechas sin la hora
        query = query.filter(Mantenimiento.fecha >= fecha_inicio)
    if fecha_fin:
        query = query.filter(Mantenimiento.fecha <= fecha_fin)

    # Filtramos por la ciudad, si está disponible
    if ciudad:
        # Filtramos por la ciudad de la máquina (usamos la relación con Maquina)
        query = query.join(Maquina).filter(Maquina.ciudad == ciudad)  

    # Devolvemos todos los resultados filtrados
    return query.all()



@app.route('/reportes', methods=['GET', 'POST'])
def reportes():
    # Obtener todas las ciudades únicas de la base de datos
    ciudades = db.session.query(distinct(Maquina.ciudad)).all()
    ciudades = [ciudad[0] for ciudad in ciudades]  # Convertir a lista de strings

    if request.method == 'POST':
        # Obtener las fechas y la ciudad del formulario
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')
        ciudad_seleccionada = request.form.get('ciudad')

        # Validar formato de fechas
        try:
            if fecha_inicio:
                # Convertir las fechas de texto a tipo fecha (sin hora)
                fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            if fecha_fin:
                fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        except ValueError:
            flash("Por favor, ingresa fechas válidas.", "danger")
            return redirect(url_for('reportes'))

        # Redirigir a la ruta `ver_reporte` con los parámetros
        return redirect(
            url_for('ver_reporte', fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, ciudad=ciudad_seleccionada)
        )

    # Renderizar el formulario inicial si no hay POST
    return render_template('reportes.html', ciudades=ciudades)



@app.route('/ver_reporte', methods=['GET'])
def ver_reporte():
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    ciudad = request.args.get('ciudad')

    # Crear la consulta inicial
     # Crear la consulta inicial
    query = Mantenimiento.query.options(
        db.joinedload(Mantenimiento.maquina),  # Relación con Maquina
        db.joinedload(Mantenimiento.usuario)  # Relación con Usuario
    )
    # Filtrar por fecha de inicio
    if fecha_inicio:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        query = query.filter(Mantenimiento.fecha >= fecha_inicio)

    # Filtrar por fecha de fin
    if fecha_fin:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
        query = query.filter(Mantenimiento.fecha <= fecha_fin)

    # Filtrar por ciudad seleccionada
    if ciudad:
        query = query.join(Maquina).filter(Maquina.ciudad == ciudad)

    # Obtener los resultados
    
    report = query.all()

    # Verifica si hay reportes para mostrar
    if not report:
        flash('No se encontraron registros para los parámetros seleccionados.', 'info')

    # Renderizar el reporte en el template
    return render_template('ver_reporte.html', report=report, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, ciudad=ciudad)


# Ruta para descargar el PDF
@app.route('/descargar_pdf', methods=['GET'])
def descargar_pdf():
    # Obtener los parámetros de filtrado desde la URL
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    ciudad = request.args.get('ciudad')

    # Convertir las fechas de texto a tipo fecha, si están disponibles
    if fecha_inicio:
    # Limpiar cualquier hora extra y convertir solo la fecha
        fecha_inicio = fecha_inicio.split(' ')[0]  # Esto elimina cualquier "00:00:00" si existe
    fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()

    if fecha_fin:
    # Limpiar cualquier hora extra y convertir solo la fecha
        fecha_fin = fecha_fin.split(' ')[0]
    fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()

    # Obtener el reporte filtrado
    report = obtener_reporte(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, ciudad=ciudad)

    # Crear el archivo PDF usando ReportLab
    pdf_output = BytesIO()
    c = canvas.Canvas(pdf_output, pagesize=letter)

    # Configurar la fuente y el título
    c.setFont("Helvetica-Bold", 14)
    c.drawString(200, 750, "Reporte de Mantenimiento")

    # Agregar subtítulo con los filtros seleccionados
    c.setFont("Helvetica", 12)
    c.drawString(100, 730, f"Ciudad: {ciudad if ciudad else 'Todas las ciudades'}")
    c.drawString(100, 710, f"Rango de fechas: {fecha_inicio if fecha_inicio else 'Sin inicio'} - {fecha_fin if fecha_fin else 'Sin fin'}")

    # Añadir los datos al PDF
    y_position = 690
    for item in report:
        maquina_nombre = item.maquina.nombre  # Relación con el modelo Maquina
        mantenimiento = item.mantenimiento  # Ajusta según tu modelo
        fecha = item.fecha.strftime('%Y-%m-%d') if item.fecha else 'Fecha no disponible'
        usuario_nombre = item.usuario.username  # Obtener el nombre del usuario

        # Escribir la línea en el PDF
        c.drawString(100, y_position, f"Usuario: {usuario_nombre} | Máquina: {maquina_nombre} | Mantenimiento: {mantenimiento} | Fecha: {fecha}")
        y_position -= 20

        # Si llegamos al final de la página, agregar una nueva página
        if y_position < 100:
            c.showPage()
            c.setFont("Helvetica", 12)
            y_position = 750

    # Finalizar el PDF
    c.showPage()
    c.save()

    pdf_output.seek(0)

    # Crear la respuesta para enviar el PDF al usuario
    response = make_response(pdf_output.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=Reporte_Mantenimiento.pdf'
    return response


if __name__ == '__main__':
    app.run(debug=True)