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