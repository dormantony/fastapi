from typing import Optional
import os, json
import uvicorn as uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from google.oauth2 import service_account
from google.cloud import storage
from googleapiclient.discovery import build
import pymysql
from pymysql.err import OperationalError
from pymysql.constants import CLIENT


class Blog(BaseModel):
    title: str
    body: str
    published: bool


class Almacen(BaseModel):
    spreadsheet_id_input: str
    range_input: str
    spreadsheet_id_ouput: str
    range_ouput: str


app = FastAPI()


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


#--------------------------------------------------------------------
# obtiene credenciales de un json guardado el storage
# este service account es el que tiene permiso de lectura/escritura a los Sheets
# spreadsheet-writer@arete-almacenes.iam.gserviceaccount.com
#--------------------------------------------------------------------
def getCredentialsSheets():
    # blob: apuntador al archivo de configuración SQL
    config_file_name = 'credentials.json'
    contents = CONFIG_BUCKET.get_blob('credentials.json').download_as_string()
    parsed_json_creds = json.loads(contents)
    # print('--------------------------- credentials ------------------------------------------- INI')
    # print(parsed_json_creds)
    # print('--------------------------- credentials ------------------------------------------- END')
    # build credentials with the service account dict
    scopes = ['https://www.googleapis.com/auth/drive','https://www.googleapis.com/auth/spreadsheets']
    credentials = service_account.Credentials.from_service_account_info(parsed_json_creds, scopes=scopes,)
    print('CONNECT', credentials.project_id)
    return credentials

#--------------------------------------------------------------------
# obtiene datos de conexion a bd
# de un archivo guardado en storage
#--------------------------------------------------------------------
def getConfigBD():
    # blob: apuntador al archivo de configuración SQL
    config_file_name = 'config-sql.txt'
    contents = CONFIG_BUCKET.get_blob(config_file_name).download_as_string().splitlines()
    # Initialize mysql config
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
    return SQL_CONFIG


#---------------------------------------------------------------------
# conexion al bucket de configuración
#---------------------------------------------------------------------
print('creating instance of buckets')
CONFIG_BUCKET = getObjBucket()
print('creating instance of bd')
# SQL_CONFIG = getConfigBD()
print('loading ok')
#==============================================================

@app.post('/crear_almacen')
def crear_almacen(almacen: Almacen):
    spreadsheet_id_input = almacen.spreadsheet_id_input
    spreadsheet_id_ouput=almacen.spreadsheet_id_ouput
    range_input = almacen.range_input
    range_ouput=almacen.range_ouput

    credentials = getCredentialsSheets()
    service = build('sheets', 'v4', credentials=credentials)
    response = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id_input, range=range_input).execute()
    response['range'] = range_ouput
    request2 = service.spreadsheets().values().update(spreadsheetId=spreadsheet_id_ouput, range=range_ouput, body=response, valueInputOption='RAW')
    response2 = request2.execute()

    return {'data': 'almacen creado'}




if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
