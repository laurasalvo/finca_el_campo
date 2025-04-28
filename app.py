from flask import Flask, request, jsonify, send_from_directory, json, url_for, redirect, flash, render_template, render_template_string
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import flask_bcrypt
from flask_migrate import Migrate
from flask_cors import CORS
from flask_restful import Api
from flask_login import login_user
from werkzeug.utils import secure_filename
import os
from application import create_app
from application.models import User, Citologia, ImagenCitologia
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
    RUTA BASE > C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe
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
    
@app.route('/client_page', methods=['POST', 'GET'])
def get_client_page():
    '''
    Control de vista administrativa
    '''
    pass

@app.route('/admin_page', methods=['POST', 'GET'])
def get_admin_page():
    '''
    Control de vista administrativa
    '''
    pass
    
@app.route('/register', methods=['POST', 'GET'])
def new_account():
    '''
    Registro de usuario
    '''
    pass

@app.route('/login', methods=['GET', 'POST'])
def login():
    '''
    Autenticación de usuario.
    - GET   : Indica que el método correcto es POST.
    - POST  : Procesa la autenticación.
    '''

    # -- Verificar si el usuario ya está autenticado
    if current_user.is_authenticated:
        if current_user.role.value == RoleEnum.cliente.value:
            return redirect(url_for('get_client_page'))
        elif current_user.role.value == RoleEnum.administrador.value:
            return redirect(url_for('get_admin_page'))
        else:
            logout_user()
            return redirect(url_for('login'))
        
    if request.method == 'GET':
        return render_template('login.html'), 200

    # -- Capturar los datos del formulario
    usermail = request.form.get('usermail')
    password = request.form.get('password')

    # -- Buscar al usuario en la base de datos
    user = User.query.filter_by(usermail=usermail).first()

    if user and bcrypt.check_password_hash(user.password_hash, password):
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