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
    APP_MODEL_NAME = os.getenv('model_name')
    APP_PREDICTOR_NAME = os.getenv('predictor_name')
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
    paciente = 'paciente'
    doctor = 'doctor'

@app.route('/segregar_celulas', methods=['POST'])
def segregar_celulas():
    def generar_nombre_carpeta(base_path):
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        folder_name = f"celulas_{timestamp}"
        folder_path = os.path.join(base_path, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        return folder_path

    if 'cell-image' not in request.files:
        flash('No se seleccionó ninguna imagen', 'error')
        return redirect(url_for('get_pacient_page'))

    ancho = int(float(request.form.get('ancho')))
    alto = int(float(request.form.get('alto')))
    file = request.files['cell-image']
    if file.filename == '':
        flash('No se seleccionó ninguna imagen', 'error')
        return redirect(url_for('get_pacient_page'))

    # Procesar la imagen subida
    try:
        pacient_id = request.form.get('pacient_id')
        upload_dir = 'C:\\Users\\migue\\Desktop\\celulas_segregadas\\uploads'
        os.makedirs(upload_dir, exist_ok=True)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(upload_dir, file.filename)
            file.save(filepath)

            print(f'Ruta de imagen para segregar celulas: {filepath}')
            image = cv2.imread(filepath)

            # Detectar celulas
            alpha=1.2
            beta=20
            kernel_size_blur=(3,3)
            kernel_size_morph=(3,3)
            distance_threshold=0.1
            cell_bbox_size = (ancho, alto)
            iou_threshold = 0.3
            selected_boxes = CellDetector.detect_cells(image, alpha, beta, kernel_size_blur,
                                          kernel_size_morph, distance_threshold,
                                          cell_bbox_size, iou_threshold)

            # Segregar cuadros delimitadores en carpeta
            cell_output_size = (224, 224)
            extracted_regions = CellDetector.extract_regions_interest(image, selected_boxes, cell_output_size)

            # Guardar imágenes en carpeta generada
            folder_name = generar_nombre_carpeta('C:\\Users\\migue\\Desktop\\celulas_segregadas')
            print(f'Ruta de carpeta para segregar celulas: {folder_name}')

            for num_cell, img_region in enumerate(extracted_regions):
                cv2.imwrite(os.path.join(folder_name, f'celula_{num_cell}.jpeg'), img_region)

            #detected_filepath = os.path.join(folder_name, f'celulas_detectadas.jpeg')
            #CellDetector.save_detected_cells(image, selected_boxes, detected_filepath)

        flash('Imagen segregada exitosamente!', 'success')
    except Exception as e:
        flash(f'Error al segregar la imagen: {str(e)}', 'error')
    
    return redirect(url_for('get_pacient_page', uid=pacient_id))

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

@app.route('/generate_report/<int:cid>', methods=['POST'])
@login_required
def generate_report(cid: int):
    '''
    Borra una citología con seguridad
    '''

    # -- Devuelve 404 si no existe
    cito = Citologia.query.get_or_404(cid)

    paciente = User.query.get(cito.user_id)
    doctor = User.query.get(cito.doctor_id)
    imagenes = ImagenCitologia.query.filter_by(citologia_id=cid).all()

    # -- Crear el HTML para el reporte

    html_content = ""
    with open('report_layout.html', 'r') as file:
        html_content = file.read()

    rep = render_template_string(html_content, nombre_doctor=f'{doctor.username} {doctor.lastname}', nombre_paciente=f'{paciente.username} {paciente.lastname}', fecha_actual=time.ctime(), comentario=cito.observacion, images=imagenes)
    
    filename = f'reporte_{cid}.pdf'
    try:
        convert_to_pdf(data=rep, report_name=filename)
    except Exception as e:
        #print(e)
        None

    return redirect(url_for('static', filename=f'uploads/{filename}'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/update_cid/<int:cid>/<int:uid>', methods=['POST'])
@login_required
def update_citologia(cid: int, uid:int):
    try:
        # -- Obtener el comentario del formulario
        comment = request.form.get('comment')

        # -- Validar si el comentario está vacío
        if not comment:
            flash('El comentario no puede estar vacío.', 'error')
            return redirect(url_for('show_citology_images', cid=cid, uid=uid))

        # --  Buscar la citología por ID
        citologia = Citologia.query.get(cid)

        # -- Verificar si la citología existe
        if not citologia:
            flash('Citología no encontrada', 'error')
            return redirect(url_for('get_pacient_list'))

        # -- Actualizar el campo observación en la citología
        citologia.observacion = comment

        # -- Guardar los cambios en la base de datos
        db.session.commit()

        # -- Dejar mensaje
        flash('Observación actualizada con éxito', 'success')

        # -- Redirigir a la pagina actual
        return redirect(url_for('show_citology_images', cid=cid, uid=uid))
    except Exception as e:
        flash(f'Error al actualizar la citología: {str(e)}', 'error')
        return redirect(url_for('get_pacient_list'))

@app.route('/show_image/<int:cid>/<int:uid>', methods=['GET'])
@login_required
def show_citology_images(cid: int, uid: int):
    '''
    Muestra las imágenes de la citología
    cid (int) -> Id de la citología
    uid (int) -> Id del usuario 
    '''
    try:
        # -- Obtener la citología por ID
        citologia = Citologia.query.filter_by(id=cid).first()

        # -- Obtener el paciente asociado
        pacient_user = User.query.get(uid) if uid else None

        if pacient_user is None:
            flash('No se ha encontrado el paciente indicado', 'error')
            return redirect(url_for('get_pacient_list'))
        
        # -- Si no se encuentra la citología, retornar error
        if not citologia:
            flash('Citología no encontrada', 'error')
            return redirect(url_for('get_pacient_list'))

        # -- Obtener todas las imágenes asociadas a la citología
        imagenes = ImagenCitologia.query.filter_by(citologia_id=cid).all()

        if not imagenes:
            flash('No se han encontrado imágenes para esta citología', 'error')
            return redirect(url_for('get_pacient_list'))
        
        # -- Pasar las imágenes completas al template
        return render_template('image_carousel.html', 
                               images=imagenes, 
                               user_role=current_user.role.value, 
                               pacient_user=pacient_user,
                               edad_paciente=pacient_user.calcular_edad(),
                               observacion=citologia.observacion,
                               cid=cid,
                               uid=uid)

    except Exception as e:
        flash(f'Error al mostrar las imágenes: {str(e)}', 'error')
        return redirect(url_for('get_pacient_page'))


@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    '''
    Captura y almacena los datos de la citología con múltiples imágenes
    '''

    def diagnosticar(modelo:object, predictor:dict, file_path:str):
        '''
        Categorizar la imagen con el modelo
        '''
        
        print('Categorizando ' + fr'{file_path}' + '...')
        # -- Realizar la predicción
        try:
            cat_id, max_val = CNNModel.categorizador_local(model=modelo, path=fr'{file_path}')
            return {'prediccion': predictor[cat_id].lower(), 'probabilidad':max_val, 'status':True, 'message':'OK'}
        except Exception as e:
            return {'prediccion': 'Ocurrió un error al procesar la imagen', 'probabilidad':0, 'status': False, 'message':str(e)}

    try:
        fecha = request.form.get('citologia-date')
        codigo = request.form.get('citologia-code')
        files = request.files.getlist('citologia-images')
        laboratorio = request.form.get('citologia-lab')
        pacient_id = request.form.get('pacient_id')

        if not fecha or not codigo or not files:
            flash('Todos los campos son obligatorios', 'error')
            return render_template('404.html', message="Todos los campos son obligatorios", user_role=current_user.role.value)

        # -- Crear el nombre de la carpeta donde se alojaran las imagenes del usuario
        code_name = codigo.replace('@', '_').replace('.', '_').upper() + '_' + str(fecha).replace('-', '_')
        pacient_folder = os.path.join(app.config['UPLOAD_PATH'], code_name)
        
        # -- Crear la carpeta si no existe
        os.makedirs(pacient_folder, exist_ok=True)

        # -- Crear el objeto Citologia sin imágenes aún
        new_citologia = Citologia(
            user_id=int(pacient_id),
            doctor_id=current_user.id,
            folder=pacient_folder,
            fecha=fecha,
            diagnostico='N/A',
            laboratorio=laboratorio
        )

        db.session.add(new_citologia)
        # -- Confirmar la citología antes de asociar imágenes
        db.session.commit()

        print('Cargando modelo y predictor...')
        # -- Cargar el modelo y el predictor

        predictor = CNNModel.get_predictor(path=APP_PREDICTOR_NAME)
        modelo = CNNModel.load_model(path=APP_MODEL_NAME)

        print(f'Ruta de modelo: {APP_MODEL_NAME}')
        print(f'Predictor: {predictor}')
        print(f'Modelo: {modelo}')

        # -- Guardar imágenes como registros en ImagenCitologia
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(pacient_folder, filename)
                real_path = f'uploads/{code_name}/{filename}'

                # -- Verificar si la imagen es TIFF y convertirla a PNG
                if filename.lower().endswith('.tiff'):
                    with Image.open(file) as img:
                        png_filename = filename.replace('.tiff', '.jpeg')
                        png_filepath = os.path.join(pacient_folder, png_filename)
                        real_path = f'uploads/{code_name}/{png_filename}'
                        img.save(png_filepath, 'JPEG')  # Guardar como PNG
                        filepath = png_filepath
                else:
                    file.save(filepath)

                # -- Categorizar la imagen usando el modelo
                result = diagnosticar(modelo=modelo, predictor=predictor, file_path=filepath)
                print(result)
                if result.get('status') == False:
                    return render_template('notification.html', message=f'Error al procesar la imagen: {result.get("message")}')

                # -- Guardar la imagen en la base de datos
                _image = ImagenCitologia(
                    citologia_id=new_citologia.id,
                    image_path=real_path,
                    image_name=real_path.split('/')[-1],
                    categoria=result.get('prediccion') if result.get('status') else None,
                    probabilidad=round( float(result.get('probabilidad')), 6)
                )

                db.session.add(_image)

        # -- Confirmar todas las imágenes en la BD
        db.session.commit()

        flash('Citología guardada con éxito', 'success')
        return redirect(url_for('get_pacient_page', uid=pacient_id))

    except Exception as e:
        db.session.rollback()  # Revertir cambios en caso de error
        flash(f'Error al subir la citología: {str(e)}', 'error')
        return render_template('notification.html', message=f'Error al subir la citología: {str(e)}')

@app.route('/static/<path:filename>')
def static_file(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/pacient_list', methods=['GET'])
@login_required             # -- Restringe el acceso a usuarios autenticados
def get_pacient_list():
    '''
    Obtiene la lista de pacientes
    '''
    # -- Obtener los usuarios que tienen rol 'paciente', ordenados por lastname
    pacientes = User.query.filter_by(role='paciente').order_by(User.dni).all()

    return render_template('pacient_list.html', user=current_user, pacientes=pacientes)

@app.route('/delete_cito/<int:cid>', methods=['POST'])
@login_required
def delete_citologia(cid: int):
    '''
    Borra una citología con seguridad
    '''

    # -- Devuelve 404 si no existe
    cito = Citologia.query.get_or_404(cid)

    try:
        db.session.delete(cito)
        db.session.commit()
        flash('Citología eliminada correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la citología: {str(e)}', 'error')

    return redirect(request.referrer or url_for('dashboard'))


@app.route('/pacient_page/<int:uid>', methods=['GET'])
@app.route('/pacient_page', methods=['GET'])
# -- Restringe el acceso a usuarios autenticados
@login_required
def get_pacient_page(uid=None) -> str:
    '''
    Retorna la pagina del paciente junto a sus citologías
    uid (int) -> Id del usuario
    '''

    # -- Si se pasa un 'uid', buscamos el usuario en la base de datos
    pacient_user = User.query.get(uid) if uid else current_user

    # -- Si no existe el usuario redirigimos con un mensaje de error
    if not pacient_user:
        flash('Usuario no encontrado', 'error')
        return render_template('notification.html', message='Usuario no encontrado')
    
    if current_user.role.value != pacient_user.role.value:
        # -- Mostrar las citologías del paciente asociadas al doctor actual
        citologias = Citologia.query.filter_by(user_id=pacient_user.id, doctor_id=current_user.id).order_by(Citologia.id.desc()).all()
    elif current_user.role.value == pacient_user.role.value:
        # -- Mostrar todas las citologías del paciente
        # -- Si el usuario es paciente, mostrar solo sus citologías
        citologias = Citologia.query.filter_by(user_id=pacient_user.id).order_by(Citologia.id.desc()).all()
    else:
        citologias = Citologia.query.order_by(Citologia.id.desc()).all()

    return render_template('pacient_page.html', doctor=current_user, user=pacient_user, user_role=current_user.role.value, citologias=citologias)

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
    
@app.route('/admin_page', methods=['POST', 'GET'])
def admin_page():
    '''
    Creacion de usuarios por medio de vista administrador
    '''
    if request.method == 'GET':
        return render_template('admin_page.html'), 200

    try:
        # -- Intentar obtener los datos desde JSON o Form
        data = request.get_json() if request.is_json else request.form
        usermail = data.get('usermail', None)
        password = data.get('password', None)
        username = data.get('username', None) 
        lastname = data.get('lastname', None)
        role     = data.get('role', None)
        dni      = data.get('dni', None)
        address  = data.get('address', '-')
        phone_number = data.get('phone_number', '-')
        birthday = data.get('birthday', None)

        if None in (usermail,password,username, lastname, role):
            return render_template('register_failed.html', message='Registro fallido, intente de nuevo mas tarde ó contacte a un administrador'), 400

        # Convertir la fecha de nacimiento a un objeto datetime.date
        try:
            birthday = datetime.strptime(birthday, '%Y-%m-%d').date()
        except ValueError:
            return render_template('register_failed.html', message='Fecha de nacimiento no válida'), 400
        
        # -- Verificar si el usuario ya existe
        existing_user = User.query.filter_by(usermail=usermail).first()
        if existing_user:
            return render_template('register_failed.html', message='Registro fallido, intente de nuevo mas tarde ó contacte a un administrador'), 400

        # -- Hashear la contraseña
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # -- Guardar usuario en la base de datos
        new_user = User(usermail=usermail,
                        password_hash=hashed_password,
                        username=username,
                        lastname=lastname,
                        role=role,
                        dni=dni,
                        address=address,
                        phone_number=phone_number,
                        birthday=birthday
                        )
        db.session.add(new_user)
        db.session.commit()

        return render_template('user_registered.html', message='Usuario registrado satisfactoriamente'), 200

    except IntegrityError:
        db.session.rollback()
        return render_template('register_failed.html', message='Registro fallido, intente de nuevo mas tarde ó contacte a un administrador'), 400
    except Exception as e:
        return render_template('register_failed.html', message='Registro fallido, intente de nuevo mas tarde ó contacte a un administrador'), 400
    
@app.route('/register', methods=['POST', 'GET'])
def new_account():
    '''
    Registro de usuario
    '''
    if request.method == 'GET':
        return render_template('register.html'), 200

    try:
        # -- Intentar obtener los datos desde JSON o Form
        data = request.get_json() if request.is_json else request.form
        usermail = data.get('usermail', None)
        password = data.get('password', None)
        username = data.get('username', None) 
        lastname = data.get('lastname', None)
        role     = data.get('role', None)
        dni      = data.get('dni', None)
        address  = data.get('address', '-')
        phone_number = data.get('phone_number', '-')
        birthday = data.get('birthday', None)

        if None in (usermail,password,username, lastname, role):
            return render_template('register_failed.html', message='Registro fallido, intente de nuevo mas tarde ó contacte a un administrador'), 400

        # Convertir la fecha de nacimiento a un objeto datetime.date
        try:
            birthday = datetime.strptime(birthday, '%Y-%m-%d').date()
        except ValueError:
            return render_template('register_failed.html', message='Fecha de nacimiento no válida'), 400
        
        # -- Verificar si el usuario ya existe
        existing_user = User.query.filter_by(usermail=usermail).first()
        if existing_user:
            return render_template('register_failed.html', message='Registro fallido, intente de nuevo mas tarde ó contacte a un administrador'), 400

        # -- Hashear la contraseña
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # -- Guardar usuario en la base de datos
        new_user = User(usermail=usermail,
                        password_hash=hashed_password,
                        username=username,
                        lastname=lastname,
                        role=role,
                        dni=dni,
                        address=address,
                        phone_number=phone_number,
                        birthday=birthday
                        )
        db.session.add(new_user)
        db.session.commit()

        return render_template('user_registered.html', message='Usuario registrado satisfactoriamente'), 200

    except IntegrityError:
        db.session.rollback()
        return render_template('register_failed.html', message='Registro fallido, intente de nuevo mas tarde ó contacte a un administrador'), 400
    except Exception as e:
        return render_template('register_failed.html', message='Registro fallido, intente de nuevo mas tarde ó contacte a un administrador'), 400

@app.route('/login', methods=['GET', 'POST'])
def login():
    '''
    Autenticación de usuario.
    - GET   : Indica que el método correcto es POST.
    - POST  : Procesa la autenticación.
    '''

    # -- Verificar si el usuario ya está autenticado
    if current_user.is_authenticated:
        if current_user.role.value == RoleEnum.paciente.value:
            return redirect(url_for('get_pacient_page'))
        elif current_user.role.value == RoleEnum.doctor.value:
            return redirect(url_for('get_pacient_list'))
        elif current_user.role.value == RoleEnum.admin.value:
            return redirect(url_for('admin_page'))
        
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

        if user.role.value == RoleEnum.paciente.value:
            return redirect(next_page or url_for('get_pacient_page'))
        elif user.role.value == RoleEnum.doctor.value:
            return redirect(next_page or url_for('get_pacient_list'))
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