from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from database import Base

# 

class Inventario(Base):
    __tablename__ = "inventario"
    inventario_id = Column(Integer, primary_key=True, index=False)
    inventario_nombre = Column(String)
    inventario_telefono = Column(String)
    inventario_correo = Column(String)
    inventario_direccion = Column(String)
