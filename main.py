from builtins import list
from typing import Optional
import os, json
import uvicorn as uvicorn
from fastapi import FastAPI, Depends, status, Response
from google.oauth2 import service_account
from google.cloud import storage
from googleapiclient.discovery import build
import pymysql
from pymysql.err import OperationalError
from pymysql.constants import CLIENT
from sqlalchemy.orm import Session

import models
import schemas
from schemas import Blog, Spreadsheet
from database import engine, SessionLocal

# models.Base.metadata.create_all(engine)

CONFIG_BUCKET = None
SQL_CONFIG = None
mysql_conn = None

app = FastAPI(title='Apis Demo', description='apis de prueba de uso de spreadsheets con FastApi')


@app.get('/blog')
def limiting(limit=10, published: bool = True, sort: Optional[str] = None):
    if published:
        return {'data': f'{limit} published  from the database'}
    else:
        return {'data': f'{limit} blogs from the db'}


@app.get('/blog/{id}')
def index(id: int):
    return {'data': id}


@app.get('/blog/{id}/comments')
def comments(id, limit=10):
    return {'data': {'1', '2'}}


@app.post('/blog')
def create_blog(blog: Blog):
    return {'data': f"Blog is created with {blog.title} as title"}


@app.get("/")
def root():
    return {'hola mundo': 1}


# =============================================================

# --------------------------------------------------------------------
# obtiene objeto bucket de configuración
# --------------------------------------------------------------------
def getObjBucket():
    # google-cloud-resource-manager
    if os.environ.get('LOCAL'):
        credential = getLocalCredentials()
        STORAGE_CLIENT = storage.Client(credentials=credential)
    else:
        STORAGE_CLIENT = storage.Client()

    return STORAGE_CLIENT.get_bucket('arete-almacenes-config')


# --------------------------------------------------------------------
# obtiene google account service para permisos del proyecto local
# --------------------------------------------------------------------
def getLocalCredentials():
    # Obtiene los permisos de un archivo en la computadora
    path_file = '{path}/{file}'.format(path=os.environ.get('CREDENTIALS'), file=os.environ.get('CREDENTIAL_FILE'))
    print('LOCAL path_file', path_file)
    credential = service_account.Credentials.from_service_account_file(path_file)
    print('LOCAL project_id', credential.project_id)
    return credential


def getLocalCredentialsByName(CREDENTIAL_FILE):
    # Obtiene los permisos de un archivo en la computadora
    path_file = '{path}/{file}'.format(path=os.environ.get('CREDENTIALS'), file=CREDENTIAL_FILE)
    print('LOCAL path_file', path_file)
    credential = service_account.Credentials.from_service_account_file(path_file)
    print('LOCAL project_id', credential.project_id)
    return credential


def getLocalFileByName(FileName):
    path_file = '{path}/{file}'.format(path=os.environ.get('CREDENTIALS'), file=FileName)
    return open(path_file).read()


# --------------------------------------------------------------------
# obtiene credenciales de un json guardado el storage
# este service account es el que tiene permiso de lectura/escritura a los Sheets
# spreadsheet-writer@arete-almacenes.iam.gserviceaccount.com
# --------------------------------------------------------------------
def getCredentialsSheets():
    # blob: apuntador al archivo de configuración SQL
    config_file_name = 'credentials.json'
    contents = CONFIG_BUCKET.get_blob('credentials.json').download_as_string()
    parsed_json_creds = json.loads(contents)
    # print('--------------------------- credentials ------------------------------------------- INI')
    # print(parsed_json_creds)
    # print('--------------------------- credentials ------------------------------------------- END')
    # build credentials with the service account dict
    scopes = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
    credentials = service_account.Credentials.from_service_account_info(parsed_json_creds, scopes=scopes, )
    print('CONNECT', credentials.project_id)
    return credentials


# --------------------------------------------------------------------
# obtiene datos de conexion a bd
# de un archivo guardado en storage
# --------------------------------------------------------------------
def getConfigBD():
    # blob: apuntador al archivo de configuración SQL
    config_file_name = 'config-sql.txt'
    if os.environ.get('LOCAL'):
        contents = getLocalFileByName(config_file_name).splitlines()
    else:
        contents = CONFIG_BUCKET.get_blob(config_file_name).download_as_string().splitlines()
    SQL_CONFIG = format_connection(contents)
    return SQL_CONFIG


def getConfigBDDos():
    config_file_name = 'config-sql.txt'
    if os.environ.get('LOCAL'):
        contents = getLocalFileByName(config_file_name).splitlines()
    else:
        contents = CONFIG_BUCKET.get_blob(config_file_name).download_as_string().splitlines()
    SQL_CONFIG = format_connection_dos(contents)
    return SQL_CONFIG


def format_connection_dos(contents):
    if not os.environ.get('LOCAL'):
        SQL_CONFIG = {
            'user': contents[7].decode("utf-8"),
            'password': contents[19].decode("utf-8"),
            'db': contents[4].decode("utf-8"),
            'charset': 'utf8',
            'port': 3306,
            'host': contents[16].decode("utf-8"),
            'cursorclass': pymysql.cursors.DictCursor,
            'autocommit': True,
            'client_flag': CLIENT.FOUND_ROWS
        }
    else:

        SQL_CONFIG = {
            'user': contents[7],
            'password': contents[19],
            'db': contents[4],
            'charset': 'utf8',
            'port': 3306,
            'host': contents[16],
            'cursorclass': pymysql.cursors.DictCursor,
            'autocommit': True,
            'client_flag': CLIENT.FOUND_ROWS
        }
    return SQL_CONFIG


def format_connection(contents):
    if not os.environ.get('LOCAL'):
        SQL_CONNECTION_NAME = contents[1].decode("utf-8")
        SQL_CONFIG = {
            'user': contents[7].decode("utf-8"),
            'password': contents[19].decode("utf-8"),
            'db': contents[4].decode("utf-8"),
            'charset': 'utf8',
            'port': 3306,
            'host': contents[16].decode("utf-8"),
            'cursorclass': pymysql.cursors.DictCursor,
            'autocommit': True,
            'client_flag': CLIENT.FOUND_ROWS
        }
    else:
        SQL_CONNECTION_NAME = contents[1]
        SQL_CONFIG = {
            'user': contents[7],
            'password': contents[19],
            'db': contents[4],
            'charset': 'utf8',
            'port': 3306,
            'host': contents[16],
            'cursorclass': pymysql.cursors.DictCursor,
            'autocommit': True,
            'client_flag': CLIENT.FOUND_ROWS
        }
    return SQL_CONFIG


# @app.on_event("startup")
# async def startup():
print('creating instance of buckets')
if os.environ.get('LOCAL'):
    CONFIG_BUCKET = None
else:
    CONFIG_BUCKET = getObjBucket()
SQL_CONFIG = getConfigBD()


def __get_cursor():
    """
    Helper function to get a cursor
      PyMySQL does NOT automatically reconnect,
      so we must reconnect explicitly using ping()
    """
    try:
        return mysql_conn.cursor()
    except OperationalError:
        mysql_conn.ping(reconnect=True)
        return mysql_conn.cursor()


# ==============================================================


@app.post('/escritura_almacen')
def crear_almacen(almacen: Spreadsheet):
    spreadsheet_id_input = almacen.spreadsheet_id_input
    range_input = almacen.range_input
    if os.environ.get('LOCAL'):
        credentials = getLocalCredentialsByName('arete-almacenes-spreadsheets.json')
    else:
        credentials = getCredentialsSheets()
    service = build('sheets', 'v4', credentials=credentials)
    response = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id_input, range=range_input).execute()
    print(response['values'])

    try:
        mysql_conn = pymysql.connect(**SQL_CONFIG)
    except OperationalError:
        print('error de conexion')

    with mysql_conn.cursor() as cursor:
        resp = cursor.execute('select * from inventario')

        sql = "INSERT INTO inventario(inventario_nombre,inventario_telefono,inventario_correo,inventario_direccion) VALUES "
        val = []
        for row in response['values']:
            val.append(f"(\'{row[0]}\', \'{row[1]}\', \'{row[2]}\', \'{row[3]}\')")

        insert = sql + ','.join(val)
        cursor.execute(insert)
    return {'data': 'almacen creado'}


@app.post('/lectura_almacen')
def lectura_almacen():
    try:
        mysql_conn = pymysql.connect(**SQL_CONFIG)
    except OperationalError:
        print('error de conexion')

    with mysql_conn.cursor() as cursor:
        cursor.execute('select * from inventario')
        rows = []
        for row in cursor.fetchall():
            rows.append(row)
    return {'data': rows}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post('/inventarios_crear', status_code=status.HTTP_201_CREATED)
def write_inventario(request: schemas.Inventario, db: Session = Depends(get_db)):
    try:

        new_inventario = models.Inventario(inventario_nombre=request.inventario_nombre,
                                           inventario_telefono=request.inventario_telefono,
                                           inventario_correo=request.inventario_correo,
                                           inventario_direccion=request.inventario_direccion)
        db.add(new_inventario)
        db.commit()
        db.refresh(new_inventario)
    except Exception as e:
        print(e)

    return new_inventario


@app.post('/inventarios_crear_ss', status_code=status.HTTP_201_CREATED)
def write_inventario_ss(request: schemas.Spreadsheet, db: Session = Depends(get_db)):
    try:
        spreadsheet_id_input = request.spreadsheet_id_input
        range_input = request.range_input
        if os.environ.get('LOCAL'):
            credentials = getLocalCredentialsByName('arete-almacenes-spreadsheets.json')
        else:
            credentials = getCredentialsSheets()
        service = build('sheets', 'v4', credentials=credentials)
        response = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id_input, range=range_input).execute()
        print(response['values'])
        for row in response['values']:
            new_inventario = models.Inventario(inventario_nombre=row[0], inventario_telefono=row[1],
                                               inventario_correo=row[2], inventario_direccion=row[3])

            _query = db.query(models.Inventario).filter(models.Inventario.inventario_nombre == row[0],
                                                        models.Inventario.inventario_telefono == row[1],
                                                        models.Inventario.inventario_correo == row[2],
                                                        models.Inventario.inventario_direccion == row[3], ).first()
            if not _query:
                db.add(new_inventario)

        db.commit()
    except Exception as e:
        print(e)

    return {'data': 'almacen creado'}


@app.get('/inventarios_leer', status_code=status.HTTP_200_OK)
def read_inventario(db: Session = Depends(get_db)):
    lisInventario = db.query(models.Inventario).all()
    return lisInventario


@app.get('/inventarios_leer/{id}', status_code=status.HTTP_200_OK)
def read_by_id(id, response: Response, db: Session = Depends(get_db)):
    inventario = db.query(models.Inventario).filter(models.Inventario.inventario_id == id).first()
    if not inventario:
        response.status_code = status.HTTP_404_NOT_FOUND
    return inventario


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
