from flask import Flask, request, jsonify, send_from_directory, json, url_for, redirect, flash, render_template, render_template_string
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import flask_bcrypt
from flask_migrate import Migrate
from flask_cors import CORS
from flask_restful import Api
from flask_login import login_user
from werkzeug.utils import secure_filename
import os
from boda import create_app
from boda.models import User, CarouselImage, Consulta, Lugar, Habitacion, Reserva, ReservaEvento
from dotenv import load_dotenv
from enum import Enum
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import logging
from PIL import Image
import time
import cv2
load_dotenv()

# -- Configuración del logger
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]"
)
_logger = logging.getLogger(__name__)

# -- Read .env file
try:
    PORT = int(os.getenv('flask_port'))
except:
    raise ValueError("PORT variable is not defined")

# -- Crear la aplicación Flask
app, db = create_app()

login_manager = LoginManager(app)
 # -- Redirigir a la vista /login si no está autenticado
login_manager.login_view = "login"

#Manejar contraseñas de forma segura
bcrypt = flask_bcrypt.Bcrypt(app)
CORS(app)
api = Api(app)

# -- Inicializa la base de datos
db.init_app(app)
migrate = Migrate(app, db)

# -- Extensiones permitidas
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'dcm', 'tiff'}

class RoleEnum(Enum):
    cliente = 'cliente'
    administrador = 'administrador'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/<filename>')
def download(filename):
    """
    Sirve el archivo desde la ruta especificada en app.config['UPLOAD_PATH']
    """
    # Obtener la ruta completa donde están los archivos subidos
    uploads_dir = app.config['UPLOAD_PATH']

    # Retornar el archivo para su descarga
    try:
        return send_from_directory(directory=uploads_dir, path=filename, as_attachment=True)
    except FileNotFoundError:
        return f"El archivo '{filename}' no se encontró en la carpeta '{uploads_dir}'", 404
    
def convert_to_pdf(data:str, report_name:str) -> None:
    '''
    Convierte un archivo a PDF
    RUTA BASE > C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe
    https://pypi.org/project/pdfkit/
    '''
    import pdfkit

    path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    options = {
        'quiet': '',
    }
    pdfkit.from_string( input=data, output_path=os.path.join(app.config['UPLOAD_PATH'], report_name), configuration=config, options=options)
    print('PDF creado...')


@app.route('/static/<path:filename>')
def static_file(filename):
    return send_from_directory(app.static_folder, filename)


@app.route('/update_user/<int:uid>', methods=['POST', 'GET'])
@login_required
def update_user(uid:int):
    '''
    Actualiza datos de usuario
    '''

    # -- Obtener el usuario que tiene el id indicado
    user = User.query.get(uid)

    if not user:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('get_pacient_page', uid=user.id))

    if request.method == 'GET':
        return redirect(url_for('get_pacient_page', uid=user.id))

    # -- Intentar obtener los datos desde JSON o Form
    data = request.get_json() if request.is_json else request.form
    nombre = data.get('nombre', user.username)
    lastname = data.get('lastname', user.lastname)
    dni = data.get('dni', user.dni)
    address = data.get('address', user.address)
    phone_number = data.get('phone_number', user.phone_number)

    try:
        user.username = nombre
        user.lastname = lastname
        user.dni = dni
        user.address = address
        user.phone_number = phone_number

        db.session.commit()
        flash('Datos actualizados correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar los datos: {str(e)}', 'error')

    return redirect(url_for('get_pacient_page', uid=user.id))
    
@app.route('/reservas', methods=['GET', 'POST'])
def reserva():
    '''
    Pagina de autenticacion
    '''

    # -- Verificar si el usuario ya está autenticado
    if current_user.is_authenticated:
        if current_user.role.value == RoleEnum.cliente.value:
            return redirect(url_for('get_client_page'))
        elif current_user.role.value == RoleEnum.administrador.value:
            return redirect(url_for('get_client_page'))
        else:
            logout_user()

            # -- Selecccionar las imagenes del carrusel que estan activas para uso
            carousel_images = CarouselImage.query.filter_by(is_active=True).all()

            return render_template('login.html', carousel_images=carousel_images), 200
        
    if request.method == 'GET':
        return render_template('reservas.html'), 200
    else:
        # -- Capturar los datos del formulario
        usermail = request.form.get('usermail')
        password = request.form.get('userpass')

        # -- Buscar al usuario en la base de datos
        user = User.query.filter_by(usermail=usermail).first()

        if user and check_password_hash(user.password_hash, password):
            # -- Iniciar sesión con Flask-Login
            login_user(user)

            flash('Inicio de sesión exitoso', 'success')

            print(user.role.value, RoleEnum.administrador.value, user.role.value == RoleEnum.administrador.value)
            if user.role.value == RoleEnum.cliente.value:
                return redirect(url_for('get_client_page'))
            elif user.role.value == RoleEnum.administrador.value:
                return redirect(url_for('get_admin_page'))
            else:
                logout_user()
                return redirect(url_for('login'))
        else:
            flash('Correo electrónico o contraseña incorrectos', 'error')
            return render_template('reservas.html'), 200
        
@app.route('/register', methods=['GET', 'POST'])
def new_account():
    '''
    Registro de usuario
    '''
    if request.method == 'GET':
        return render_template('register.html'), 200

    # Capturar los datos del formulario
    username = request.form.get('username')
    lastname = request.form.get('lastname')
    usermail = request.form.get('usermail')
    phonenumber = request.form.get('phonenumber')
    password = request.form.get('userpass')
    password2 = request.form.get('userpass_2')
    birthday_str = request.form.get('birthday')  # Debe ser tipo "YYYY-MM-DD"
    dni = request.form.get('dni', '-')
    address = request.form.get('address', '-')

    # Validaciones básicas
    if not all([username, lastname, usermail, password, password2, birthday_str]):
        flash('Todos los campos obligatorios deben completarse.', 'danger')
        return redirect(url_for('new_account'))

    if password != password2:
        flash('Las contraseñas no coinciden.', 'danger')
        return redirect(url_for('new_account'))

    # Validar formato de fecha
    try:
        birthday = datetime.strptime(birthday_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Formato de fecha de nacimiento inválido. Use YYYY-MM-DD.', 'danger')
        return redirect(url_for('new_account'))

    # Validar que el correo no esté registrado
    existing_user = User.query.filter_by(usermail=usermail).first()
    if existing_user:
        flash('Este correo ya está registrado.', 'danger')
        return redirect(url_for('new_account'))

    # Crear nuevo usuario
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    new_user = User(
        username=username,
        lastname=lastname,
        usermail=usermail,
        phone_number=phonenumber,
        password_hash=hashed_password,
        birthday=birthday,
        dni=dni,
        address=address,
        role=RoleEnum.cliente.value
    )

    # Guardar en base de datos
    db.session.add(new_user)
    db.session.commit()

    flash('Registro exitoso. ¡Bienvenido!', 'success')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    '''
    Autenticación de usuario.
    - GET   : Indica que el método correcto es POST.
    - POST  : Procesa la autenticación.
    '''

    # -- Selecccionar las imagenes del carrusel que estan activas para uso
    carousel_images = CarouselImage.query.filter_by(is_active=True).all()
   
    if request.method == 'GET':
        return render_template('login.html', carousel_images=carousel_images, user=current_user), 200
    else:
        # -- Capturar los datos del formulario
        usermail = request.form.get('usermail')
        password = request.form.get('userpass')

        # -- Buscar al usuario en la base de datos
        user = User.query.filter_by(usermail=usermail).first()

        if user and check_password_hash(user.password_hash, password):
            # -- Iniciar sesión con Flask-Login
            login_user(user)

            flash('Inicio de sesión exitoso', 'success')
            
            # -- Redirigir al usuario a la página que intentaba acceder
            next_page = request.args.get('next')

            if user.role.value == RoleEnum.cliente.value:
                return redirect(next_page or url_for('get_client_page'))
            elif user.role.value == RoleEnum.administrador.value:
                return redirect(next_page or url_for('get_admin_page'))
            else:
                logout_user()
                return redirect(url_for('login'))
        else:
            flash('Correo electrónico o contraseña incorrectos', 'error')
            return redirect(url_for('login'))
    
@app.route('/get_admin_page', methods=['GET', 'POST'])
@login_required
def get_admin_page():
    '''
    Redireccionar a controles administrativos
    '''
    # -- Selecccionar las imagenes del carrusel que estan activas para uso
    carousel_images = CarouselImage.query.filter_by(is_active=True).all()

    # -- Verificar si el usuario ya está autenticado
    if current_user.is_authenticated:
        if current_user.role.value == RoleEnum.administrador.value:
            
            # -- Consultas no respondidas, ordenadas por más recientes primero
            consultas = Consulta.query.filter_by(respondida=False).order_by(Consulta.fecha_creacion.asc()).all()
            reservas = Reserva.query.filter_by(completado=False).all()
            eventos = ReservaEvento.query.filter_by(completado=False).all()

            return render_template('admin_page.html', carousel_images=carousel_images, user=current_user, reservas=reservas, consultas=consultas, eventos=eventos), 200
        else:
            logout_user()
            return render_template('login.html', carousel_images=carousel_images, user=current_user), 200
    else:
        logout_user()
        return render_template('login.html', carousel_images=carousel_images, user=current_user), 200

@app.route('/get_client_page', methods=['GET', 'POST'])
@login_required
def get_client_page():
    '''
    Mostrar pagina del cliente
    '''
    # -- Selecccionar las imagenes del carrusel que estan activas para uso
    carousel_images = CarouselImage.query.filter_by(is_active=True).all()

    # -- Verificar si el usuario ya está autenticado
    if current_user.is_authenticated:
        if current_user.role.value == RoleEnum.cliente.value:
            return render_template('client_page.html', carousel_images=carousel_images, user=current_user, reservas=[]), 200
        else:
            logout_user()
            return render_template('login.html', carousel_images=carousel_images, user=current_user), 200
    else:
        logout_user()
        return render_template('login.html', carousel_images=carousel_images, user=current_user), 200

@app.route('/fincas')
def fincas():
    # -- Selecccionar las imagenes del carrusel que estan activas para uso
    carousel_images = CarouselImage.query.filter_by(is_active=True).all()

    return render_template('fincas.html', user=current_user, carousel_images=carousel_images)

@app.route('/aloja')
def alojamientos():
    # -- Selecccionar las imagenes del carrusel que estan activas para uso
    carousel_images = CarouselImage.query.filter_by(is_active=True).all()

    return render_template('alojamientos.html', user=current_user, carousel_images=carousel_images)

@app.route('/events')
def eventos():
    # -- Selecccionar las imagenes del carrusel que estan activas para uso
    carousel_images = CarouselImage.query.filter_by(is_active=True).all()

    return render_template('events.html', user=current_user, carousel_images=carousel_images)

@app.route('/about_us')
def sobre_nos():
    return render_template('about_us.html')

@app.route('/contact_us', methods=['GET', 'POST'])
def contactanos():
    if request.method == 'POST':
        # Capturar datos del formulario
        username = request.form.get('username', '').strip()
        lastname = request.form.get('lastname', '').strip()
        full_name = f"{username} {lastname}".strip()

        usermail = request.form.get('usermail', '').strip()
        phone = request.form.get('phone_number', '').strip()
        message = request.form.get('message', '').strip()
        ciudad = request.form.get('direccion', '').strip()
        direccion = request.form.get('direccion', '').strip()

        # Validación simple
        if not full_name or not usermail:
            flash("Nombre y correo son obligatorios", "error")
            return redirect('/contact_us')

        # Crear registro en la base de datos
        consulta = Consulta(
            username=full_name,
            usermail=usermail,
            telefono=phone,
            direccion=direccion,
            ciudad=ciudad,
            message=message,
        )

        db.session.add(consulta)
        db.session.commit()

        flash("Tu consulta fue enviada con éxito, le respondéremos en la menor brevedad posible", "success")
        return redirect('/contact_us')

    return render_template('contact_us.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada', 'info')
    return redirect(url_for('login'))

@app.route('/', methods=['GET'])
def main():
    '''
    Pagina principal
    '''
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=PORT)