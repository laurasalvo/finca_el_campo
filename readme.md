
<h3>Crear entorno virtual</h3>

```
    >>> cd cnn_celular
    >>> python -m venv virtual
```

<h3>Activar entorno virtual</h3>

```
    >>> cd cnn_celular
    >>> virtual\Scripts\activate
```

<h3>Instalar dependencias</h3>

```
    >>> python.exe -m pip install --upgrade pip
    >>> pip install -r requirements.txt
```

<h3>Instalar WKHTMLTOX</h3>

```
    wkhtmltox-0.12.6-1.msvc2015-win64.exe
    RUTA :: C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe
```

<h3>Crear la base de datos</h3>

```
    >>> psql
    >>> CREATE USER boda WITH PASSWORD 'root';
    >>> ALTER USER boda CREATEDB;
    >>> ALTER USER boda WITH SUPERUSER;
    >>> CREATE DATABASE boda_app WITH OWNER = boda;
    >>> GRANT ALL PRIVILEGES ON DATABASE boda_app TO boda;
    >>> COMMENT ON DATABASE boda_app IS 'Base de datos de gestion de bodas';
```

<h3>Inicializar la base de datos</h3>

```
>>> cd /D ruta-proyecto
>>> python -m venv virtual
>>> cd virtual/Scripts
>>> activate
>>> cd ..
>>> cd ..
>>> python.exe -m pip install --upgrade pip
>>> pip install -r requirements.txt
>>> flask db init
>>> flask db migrate -m "Initial migration"
>>> flask db upgrade
```

<h3>Actualiza base de datos</h3>

```
>>> cd /D ruta-proyecto
>>> flask db migrate -m "Comentario del cambio"
>>> flask db upgrade
```

<h3>Reiniciar datos (opcional)</h3>

```
# Borrar la carpeta /migrations
>>> cd /D ruta-proyecto
>>> flask shell
>>> from application.models.commons import db
>>> db.drop_all()
```