from pydantic import BaseModel


class Blog(BaseModel):
    title: str
    body: str
    published: bool


class Spreadsheet(BaseModel):
    spreadsheet_id_input: str
    range_input: str

class Inventario(BaseModel):
    inventario_nombre:str
    inventario_telefono:str
    inventario_correo:str
    inventario_direccion:str
