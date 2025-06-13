from enum import Enum
from .commons import db, UserMixin
from sqlalchemy.orm import relationship, validates
from datetime import datetime, timezone, date

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
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=True)
    lastname = db.Column(db.String(80), nullable=True)
    usermail = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(24), nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.Enum(RoleEnum), nullable=False, default=RoleEnum.cliente)
    birthday = db.Column(db.Date, nullable=False)
    dni = db.Column(db.String(20), nullable=True, default="-")
    address = db.Column(db.String(255), nullable=True, default="-")

    # Relación con reservas y reservas de eventos
    reservas = db.relationship('Reserva', back_populates='user', cascade="all, delete-orphan")
    reservas_eventos = db.relationship('ReservaEvento', back_populates='user', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<User {self.usermail}, Role: {self.role}>'

    def calcular_edad(self):
        today = date.today()
        return today.year - self.birthday.year

class CarouselImage(db.Model):
    __tablename__ = 'carousel_images'
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=True)

    def __repr__(self):
        return f'<CarouselImage id={self.id} path={self.image_path}>'

class Consulta(db.Model):
    __tablename__ = 'consultas'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    usermail = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(24), nullable=True)
    direccion = db.Column(db.String(255), nullable=True)
    ciudad = db.Column(db.String(100), nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    message = db.Column(db.Text, nullable=True)
    respondida = db.Column(db.Boolean, default=False)
    admin_response = db.Column(db.Text, default="-")
    tipo_reserva = db.Column(db.String(255), default="-")
    fecha_reserva = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Consulta {self.username} - {self.usermail}>'

class Lugar(db.Model):
    __tablename__ = 'lugares'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    imagen = db.Column(db.String(255), nullable=False)

    # Relación con reserva de eventos
    reservas_eventos = db.relationship('ReservaEvento', back_populates='lugar', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Lugar {self.titulo}>'

class Habitacion(db.Model):
    __tablename__ = 'habitaciones'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    imagen = db.Column(db.String(255), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    disponible = db.Column(db.Boolean, default=True, nullable=False)

    # Relación con reservas
    reservas = db.relationship('Reserva', back_populates='habitacion', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Habitacion {self.titulo} - ${self.precio:.2f}>'

class Reserva(db.Model):
    __tablename__ = 'reservas'
    id = db.Column(db.Integer, primary_key=True)
    # Clave foránea a User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment="ID del usuario")
    # Clave foránea a Habitacion
    habitacion_id = db.Column(db.Integer, db.ForeignKey('habitaciones.id'), nullable=False, comment="ID de la habitación reservada")
    username = db.Column(db.String(100), nullable=False)
    usermail = db.Column(db.String(120), nullable=False)
    fecha_entrada = db.Column(db.Date, nullable=True)
    fecha_salida = db.Column(db.Date, nullable=True)
    fecha_reserva = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    completado = db.Column(db.Boolean, default=False)

    # Relaciones
    user = db.relationship('User', back_populates='reservas')
    habitacion = db.relationship('Habitacion', back_populates='reservas')

    def __repr__(self):
        return f'<Reserva {self.username} - {self.fecha_entrada} a {self.fecha_salida}>'

    @validates('fecha_entrada', 'fecha_salida')
    def validar_fechas(self, key, value):
        if key == 'fecha_salida' and self.fecha_entrada and value <= self.fecha_entrada:
            raise ValueError("La fecha de salida debe ser posterior a la de entrada")
        return value

class ReservaEvento(db.Model):
    __tablename__ = 'reservas_eventos'
    id = db.Column(db.Integer, primary_key=True)
    # Clave foránea a User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment="ID del usuario que realiza la reserva")
    username = db.Column(db.String(100), nullable=False)
    usermail = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(24), nullable=True)
    tipo_evento = db.Column(db.Enum(TipoEventoEnum), default=TipoEventoEnum.boda, nullable=False)
    fecha_evento = db.Column(db.Date, nullable=False)
    numero_invitados = db.Column(db.Integer, nullable=False)
    # Clave foránea a Lugar
    lugar_id = db.Column(db.Integer, db.ForeignKey('lugares.id'), nullable=False, comment="ID del lugar reservado")
    lugar_evento = db.Column(db.String(150), nullable=True)
    mensaje = db.Column(db.Text, nullable=True)
    fecha_reserva = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    completado = db.Column(db.Boolean, default=False)

    # Relaciones
    user = db.relationship('User', back_populates='reservas_eventos')
    lugar = db.relationship('Lugar', back_populates='reservas_eventos')

    def __repr__(self):
        return f'<ReservaEvento {self.username} - {self.tipo_evento.name} - {self.fecha_evento}>'