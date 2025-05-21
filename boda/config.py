# -*- coding: UTF-8 -*-
#!/usr/bin/env python 

import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
load_dotenv()

# -- Read .env file
DRIVER =  os.getenv('db_engine')
HOST = os.getenv('db_host')
DATABASE = os.getenv('db_name')
USER = os.getenv('db_user')
PASSWORD = os.getenv('db_password')
PORT = os.getenv('db_port')

if not all([DRIVER, HOST, DATABASE, USER, PASSWORD, PORT]):
    raise ValueError("Environment variables required to configure the database are missing.")

PORT = int(PORT)

class DbManager:
    '''
    Datos de conexion para la base de datos
    '''
    
    SQLALCHEMY_DATABASE_URI = f'postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def test_connection():
        '''
        Prueba de conexion con la base de datos
        '''

        engine = create_engine(DbManager.SQLALCHEMY_DATABASE_URI)
        try:
            connection = engine.connect()
            print("✅ Successful connection to the database.")
        except Exception as e:
            print(f"⛔ Error connecting to database: {e}")
        finally:
            connection.close()

if __name__ == "__main__":
    test = DbManager.test_connection()