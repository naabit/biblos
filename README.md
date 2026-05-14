# Biblos

Aplicación web en **Django** para **importar, revisar y exportar** artículos bibliográficos desde/ hacia Excel.

## Funcionalidades

- Importa un `.xlsx` y crea artículos a partir de columnas típicas de WoS/Scopus:
  - `TI` (título), `AU` (autores), `PY` (año), `AB` (resumen), `KW_Merged` (palabras clave), `DI` (DOI), `SO` (fuente).
- Lista de artículos con búsqueda y filtros (estado, año, DOI).
- Cambia el estado del artículo: `Pendiente`, `Incluido`, `Excluido`, `Revisar después`.
- Exporta a Excel el resultado filtrado.
- Elimina artículos individuales, todos los artículos, o una carga de Excel completa (con sus artículos).

## Requisitos

- Python 3.11+
- Dependencias principales:
  - Django
  - pandas + openpyxl (para importar/exportar Excel)

## Configuración (variables de entorno)

Este proyecto lee variables desde `.env` (ver `.env.example`):

- `DEBUG`: `True`/`False`
- `SECRET_KEY`: clave larga y aleatoria (obligatoria cuando `DEBUG=False`)
- `ALLOWED_HOSTS`: lista separada por comas, por ejemplo `biblos-adql.onrender.com`
- `CSRF_TRUSTED_ORIGINS`: lista separada por comas con esquema, por ejemplo `https://biblos-adql.onrender.com`

Cuando `DEBUG=False`, el proyecto habilita automáticamente:

- `SECURE_SSL_REDIRECT=True` (redirige todo a HTTPS)
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`
- HSTS (configurable con `SECURE_HSTS_SECONDS`)

## Instalación (Windows / PowerShell)

1) Crear y activar un entorno virtual:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2) Instalar dependencias:

```powershell
python -m pip install --upgrade pip
python -m pip install "Django==5.2.14" pandas openpyxl
```

3) Migraciones:

```powershell
python manage.py migrate
```

4) (Opcional) Crear usuario admin:

```powershell
python manage.py createsuperuser
```

## Ejecutar

```powershell
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

- App: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`

## Uso rápido

- Importar Excel: entra a la vista de carga (ruta `/upload/`).
- Revisar/filtrar: usa el buscador y los filtros en la lista principal.
- Exportar Excel filtrado: ruta `/export/`.

## Estructura del proyecto

- `config/`: settings/urls/wsgi/asgi del proyecto Django.
- `articles/`: app principal (modelos, vistas, urls, templates).
- `static/`: archivos estáticos (imágenes, etc.).
- `db.sqlite3`: base de datos SQLite (desarrollo).

## Árbol de directorios

```text
biblos/
├── articles/
│   ├── migrations/
│   │   ├── 0001_initial.py
│   │   └── 0002_excelupload_article_excel_upload.py
│   ├── templates/
│   │   └── articles/
│   │       ├── article_list.html
│   │       ├── base.html
│   │       └── upload_excel.html
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── config/
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── static/
│   └── img/
│       ├── favicon.png
│       └── logo.png
├── staticfiles/            # generado por collectstatic (si aplica)
├── .env
├── .gitignore
├── db.sqlite3
├── manage.py
├── README.md
├── requirements.txt
└── runtime.txt
```

## Notas

- La importación/exportación requiere `pandas` y `openpyxl`. Si faltan, la app muestra un mensaje de error al intentar importar/exportar.

---

![firma](static/img/firma.png)
