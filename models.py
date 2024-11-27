from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    ciudad = db.Column(db.String(100))

    # Relación con los mantenimientos
    mantenimiento = db.relationship('Mantenimiento', backref='usuario', lazy=True)


class Maquina(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Esta es la columna ID de la tabla Maquina
    nombre = db.Column(db.String(100), nullable=False)
    ciudad = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(100), nullable=False)
    tipo_id = db.Column(db.Integer, nullable=True)  # ID opcional si lo necesitas

    # Relación con los mantenimientos
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
   
