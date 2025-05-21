# -*- coding: UTF-8 -*-
#!/usr/bin/env python 

import os
from flask import Flask
from boda.models.commons import db
from boda.config import DbManager

def create_app():
    '''
    Crea la aplicacion
    '''

    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(DbManager)

    # -- Extensión de archivos permitidos
    app.config['UPLOAD_EXTENSIONS'] = ['.png', '.jpg', '.jpeg', '.gif', '.diff']

    # -- Máximo 100 MB
    app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 100

    # -- Carpeta para subida de archivos
    app.config['UPLOAD_PATH'] = 'boda/static/uploads'
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    if not os.path.exists(app.config['UPLOAD_PATH']):
        os.makedirs(app.config['UPLOAD_PATH'])

    secret = os.urandom(32)
    app.config['SECRET_KEY'] = secret
    app.secret_key = secret

    return app, db