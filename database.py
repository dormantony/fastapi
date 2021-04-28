from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = \
    'mysql+pymysql://{user}:{passw}@{host}/{db}'. \
        format(user='arete-almacen', passw='*DhONCqxRn', host='35.238.144.25', db='armsv45')
engine = create_engine(SQLALCHEMY_DATABASE_URL)
     #, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
