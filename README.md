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

## Uso rápido

- Importar Excel: entra a la vista de carga (ruta `/upload/`).
- Revisar/filtrar: usa el buscador y los filtros en la lista principal.
- Exportar Excel filtrado: ruta `/export/`.

## Estructura del proyecto

- `config/`: settings/urls/wsgi/asgi del proyecto Django.
- `articles/`: app principal (modelos, vistas, urls, templates).
- `static/`: archivos estáticos (imágenes, etc.).
- `db.sqlite3`: base de datos SQLite (desarrollo).

## Notas

- La importación/exportación requiere `pandas` y `openpyxl`. Si faltan, la app muestra un mensaje de error al intentar importar/exportar.
