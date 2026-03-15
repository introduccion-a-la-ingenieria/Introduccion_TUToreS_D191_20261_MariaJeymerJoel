import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Date, Time, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

# Base declarative class
Base = declarative_base()

# Models
class Rol(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)
    
class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    auth_id = Column(UUID(as_uuid=True), unique=True, nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    nombre_completo = Column(String(255), nullable=False)
    rol_id = Column(Integer, ForeignKey('roles.id'), nullable=True)
    activo = Column(Boolean, default=True)
    rol = relationship("Rol")

class Tutoria(Base):
    __tablename__ = 'tutorias'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    titulo = Column(String(255), nullable=False)
    descripcion = Column(Text)
    docente_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    fecha = Column(Date, nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    cupo_maximo = Column(Integer, nullable=False)
    estado = Column(String(50), default='Programada')
    docente = relationship("Usuario")

class Inscripcion(Base):
    __tablename__ = 'inscripciones'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tutoria_id = Column(UUID(as_uuid=True), ForeignKey('tutorias.id', ondelete='CASCADE'), nullable=False)
    estudiante_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    estado = Column(String(50), default='Confirmada')
    tutoria = relationship("Tutoria", backref="inscripciones")
    estudiante = relationship("Usuario")

class Material(Base):
    __tablename__ = 'materiales'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tutoria_id = Column(UUID(as_uuid=True), ForeignKey('tutorias.id', ondelete='CASCADE'), nullable=False)
    nombre_archivo = Column(String(255), nullable=False)
    url_archivo = Column(Text, nullable=False)
    subido_por = Column(UUID(as_uuid=True), ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True)
    tutoria = relationship("Tutoria", backref="materiales")

# Connection setup
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["database"]["url"]
        engine = create_engine(url, pool_size=10, max_overflow=20)
        return engine
    except Exception as e:
        st.error(f"Error conectando a la base de datos: {e}")
        return None

engine = init_connection()

def get_session():
    if engine:
        Session = sessionmaker(bind=engine)
        return Session()
    return None
