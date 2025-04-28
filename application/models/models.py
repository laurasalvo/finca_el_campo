from enum import Enum
from .commons import db, UserMixin
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, date


# Definir el Enum para los roles
class RoleEnum(Enum):
    paciente = 'paciente'
    doctor = 'doctor'
    admin = 'admin'

class CategoriaEnum(Enum):
    ascus = 'ascus'
    altogrado = 'altogrado'
    bajogrado = 'bajogrado'
    benigna = 'benigna'


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
    role = db.Column(db.Enum(RoleEnum), nullable=False, default=RoleEnum.paciente, comment="Rol del usuario (paciente o doctor)")
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

class Citologia(db.Model):
    '''
    Imagenes de las células
    '''
    __tablename__ = 'citologias'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment="Relacion con User")
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment="Relacion con User")
    folder = db.Column(db.String(255), nullable=True, comment="Folder")
    fecha = db.Column(db.Date, nullable=False)
    diagnostico = db.Column(db.String(255), nullable=True)
    laboratorio = db.Column(db.String(255), default="-", nullable=True)
    observacion = db.Column(db.Text, nullable=True, default="-", comment="Observaciones adicionales")
    
    # -- Relaciones
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('citologias_paciente', lazy=True))
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref=db.backref('citologias_doctor', lazy=True))

    def __repr__(self):
        return f'<Citologia {self.id}, User: {self.user.username}, Fecha: {self.fecha}>'


class ImagenCitologia(db.Model):
    '''
    Tabla de imágenes asociadas a una citología, con diagnóstico incluido
    '''
    __tablename__ = 'imagenes_citologia'

    id = db.Column(db.Integer, primary_key=True)
    citologia_id = db.Column(db.Integer, db.ForeignKey('citologias.id', ondelete='CASCADE'), nullable=False, index=True)
    image_path = db.Column(db.String(255), nullable=False, comment="Ruta de la imagen")
    image_name = db.Column(db.String(255), nullable=True, default="-", comment="Nombre de la imagen")

    # -- Campos de diagnóstico
    categoria = db.Column(db.Enum(CategoriaEnum), nullable=True, comment="Categoría del diagnóstico")
    fecha_revision = db.Column(db.Date, nullable=True, default=lambda: datetime.now(timezone.utc), comment="Fecha de revisión")
    probabilidad = db.Column(db.Float, nullable=True, default=0.0, comment="Probabilidad del diagnóstico")

    # -- Relación con citología
    citologia = db.relationship('Citologia', backref=db.backref('imagenes', lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f'<Imagen {self.id}, Citologia: {self.citologia_id}, Ruta: {self.image_path}, Categoria: {self.categoria}, Probabilidad: {self.probabilidad}>'