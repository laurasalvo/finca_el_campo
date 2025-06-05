from enum import Enum
from .commons import db, UserMixin
from sqlalchemy.orm import relationship, validates
from datetime import datetime, timezone, date


# Definir el Enum para los roles
class RoleEnum(Enum):
    cliente = 'cliente'
    administrador = 'administrador'


class TipoEventoEnum(Enum):
    boda = 'Boda'
    bautizo = 'Bautizo'
    cumpleaños = 'Cumpleaños'
    aniversario = 'Aniversario'
    corporativo = 'Evento Corporativo'
    otros = 'Otros'

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
    username = db.Column(db.String(100), nullable=False, comment="Nombre del cliente que realiza la consulta")
    usermail = db.Column(db.String(120), nullable=False, comment="Correo electrónico del cliente")
    telefono = db.Column(db.String(24), nullable=True, comment="Teléfono de contacto")
    direccion = db.Column(db.String(255), nullable=True, comment="Dirección del cliente")
    ciudad = db.Column(db.String(100), nullable=True, comment="Ciudad del cliente")
    fecha_creacion = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False, comment="Fecha y hora en que se registró la consulta")
    message = db.Column(db.Text, nullable=True, comment="Mensaje enviado por el cliente")
    respondida = db.Column(db.Boolean, default=False, comment="Indica si la consulta ha sido respondida")
    admin_response = db.Column(db.Text, default="-", comment="Respuesta del administrador")

    def __repr__(self):
        return f'<Consulta {self.username} - {self.usermail}>'
    

class Lugar(db.Model):
    '''
    Modelo para almacenar información de lugares
    '''
    __tablename__ = 'lugares'

    id = db.Column(db.Integer, primary_key=True, comment="ID único del lugar")
    titulo = db.Column(db.String(150), nullable=False, comment="Título o nombre del lugar")
    descripcion = db.Column(db.Text, nullable=True, comment="Descripción del lugar")
    imagen = db.Column(db.String(255), nullable=False, comment="Ruta relativa de la imagen del lugar (ej: static/images/lugares/nombre.jpg)")

    def __repr__(self):
        return f'<Lugar {self.titulo}>'
    

class Habitacion(db.Model):
    '''
    Modelo para almacenar información de habitaciones
    '''
    __tablename__ = 'habitaciones'

    id = db.Column(db.Integer, primary_key=True, comment="ID único de la habitación")
    titulo = db.Column(db.String(150), nullable=False, comment="Nombre o tipo de la habitación")
    descripcion = db.Column(db.Text, nullable=True, comment="Descripción de la habitación")
    imagen = db.Column(db.String(255), nullable=False, comment="Ruta de imagen de la habitación (ej: static/images/habitaciones/ejemplo.jpg)")
    precio = db.Column(db.Float, nullable=False, comment="Precio por noche")
    disponible = db.Column(db.Boolean, default=True, nullable=False, comment="Indica si la habitación está disponible")

    # Relación con reservas (si decides crear ese modelo)
    reservas = db.relationship('Reserva', backref='habitacion', lazy=True)

    def __repr__(self):
        return f'<Habitacion {self.titulo} - ${self.precio:.2f}>'
    

class Reserva(db.Model):
    '''
    Reservas de habitaciones
    '''
    __tablename__ = 'reservas'

    id = db.Column(db.Integer, primary_key=True, comment="ID único de la reserva")
    habitacion_id = db.Column(db.Integer, db.ForeignKey('habitaciones.id'), nullable=False, comment="ID de la habitación reservada")
    username = db.Column(db.String(100), nullable=False, comment="Nombre del cliente")
    usermail = db.Column(db.String(120), nullable=False, comment="Correo electrónico del cliente")
    fecha_entrada = db.Column(db.Date, nullable=True, comment="Fecha de entrada")
    fecha_salida = db.Column(db.Date, nullable=True, comment="Fecha de salida")
    fecha_reserva = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False, comment="Fecha en que se realizó la reserva")
    completado = db.Column(db.Boolean, default=False, comment="Indica si fue completada la reserva")

    def __repr__(self):
        return f'<Reserva {self.username} - {self.fecha_entrada} a {self.fecha_salida}>'
    
    @validates('fecha_entrada', 'fecha_salida')
    def validar_fechas(self, key, value):
        if key == 'fecha_salida' and self.fecha_entrada and value <= self.fecha_entrada:
            raise ValueError("La fecha de salida debe ser posterior a la de entrada")
        return value

class ReservaEvento(db.Model):
    '''
    Reservas de eventos
    '''
    __tablename__ = 'reservas_eventos'

    id = db.Column(db.Integer, primary_key=True, comment="ID único de la reserva de evento")
    username = db.Column(db.String(100), nullable=False, comment="Nombre del cliente que realiza la reserva")
    usermail = db.Column(db.String(120), nullable=False, comment="Correo electrónico del cliente")
    telefono = db.Column(db.String(24), nullable=True, comment="Teléfono de contacto")
    tipo_evento = db.Column(db.Enum(TipoEventoEnum), default=TipoEventoEnum.boda, nullable=False, comment="Tipo de evento")
    fecha_evento = db.Column(db.Date, nullable=False, comment="Fecha del evento")
    numero_invitados = db.Column(db.Integer, nullable=False, comment="Número estimado de invitados")
    lugar_evento = db.Column(db.String(150), nullable=True, comment="Lugar o área reservada")
    mensaje = db.Column(db.Text, nullable=True, comment="Mensaje adicional o requerimientos especiales")
    fecha_reserva = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False, comment="Fecha y hora en que se registró la reserva")
    completado = db.Column(db.Boolean, default=False, comment="Indica si fue completado el evento")

    def __repr__(self):
        return f'<ReservaEvento {self.username} - {self.tipo_evento.name} - {self.fecha_evento}>'