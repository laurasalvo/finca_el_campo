from enum import Enum
from .commons import db, UserMixin
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, date


# Definir el Enum para los roles
class RoleEnum(Enum):
    cliente = 'cliente'
    administrador = 'administrador'


class User(db.Model, UserMixin):
    '''
    Datos de usuarios
    Hereda de UserMixin para compatibilidad con Flask-Login
    '''
    
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, comment="Identificador único de la oferta")
    username = db.Column(db.String(80), nullable=True, comment="Nombre de usuario")
    lastname = db.Column(db.String(80), nullable=True, comment="Apellido del usuario")
    usermail = db.Column(db.String(120), unique=True, nullable=False, comment="Correo electrónico del usuario")
    phone_number = db.Column(db.String(24), nullable=True, comment="Teléfono")
    password_hash = db.Column(db.String(128), nullable=False, comment="Contraseña del usuario")
    role = db.Column(db.Enum(RoleEnum), nullable=False, default=RoleEnum.cliente, comment="Rol del usuario (cliente o administrador)")
    birthday = db.Column(db.Date, nullable=False, comment="Fecha de nacimiento")
    dni = db.Column(db.String(20), nullable=True, default="-", comment="DNI")
    address = db.Column(db.String(255), nullable=True, default="-", comment="Direccion")

    def __repr__(self):
        return f'<User {self.usermail}, Role: {self.role}>'

    def calcular_edad(self):
        '''
        Calcula la edad del paciente
        '''
        
        today = date.today()
        return today.year - self.birthday.year
    
class CarouselImage(db.Model):
    '''
    Imágenes del carrusel
    '''
    __tablename__ = 'carousel_images'

    id = db.Column(db.Integer, primary_key=True, comment="ID único de la imagen")
    image_path = db.Column(db.String(255), nullable=False, comment="Ruta relativa de la imagen (ej: static/images/carrusel/ejemplo.jpg)")
    description = db.Column(db.String(255), nullable=True, comment="Descripción de la imagen")
    is_active = db.Column(db.Boolean, default=True, nullable=True, comment="Indica si la imagen está activa para mostrarla")

    def __repr__(self):
        return f'<CarouselImage id={self.id} path={self.image_path}>'
    
class Consulta(db.Model):
    '''
    Registro de consultas realizadas por clientes
    '''
    __tablename__ = 'consultas'

    id = db.Column(db.Integer, primary_key=True, comment="ID único de la consulta")
    nombre_cliente = db.Column(db.String(100), nullable=False, comment="Nombre del cliente que realiza la consulta")
    email = db.Column(db.String(120), nullable=False, comment="Correo electrónico del cliente")
    telefono = db.Column(db.String(24), nullable=True, comment="Teléfono de contacto")
    direccion = db.Column(db.String(255), nullable=True, comment="Dirección del cliente")
    ciudad = db.Column(db.String(100), nullable=True, comment="Ciudad del cliente")
    fecha_creacion = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False, comment="Fecha y hora en que se registró la consulta")

    def __repr__(self):
        return f'<Consulta {self.nombre_cliente} - {self.email}>'