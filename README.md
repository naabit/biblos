# Biblos

**Biblos** es una aplicación web desarrollada en Django para importar, revisar, clasificar y exportar artículos bibliográficos desde archivos Excel.

El proyecto está pensado como una herramienta de apoyo para procesos de revisión bibliográfica, exploración de bases de datos académicas y organización inicial de literatura científica.

---

## Características principales

* Importación de archivos `.xlsx` con registros bibliográficos.
* Gestión de cada carga como un lote independiente mediante el modelo `ExcelUpload`.
* Asociación de artículos a una carga específica.
* Visualización de artículos en una tabla con búsqueda, filtros y ordenamiento.
* Filtros por estado de revisión, año y presencia de DOI.
* Búsqueda por texto en campos bibliográficos relevantes.
* Cambio de estado de cada artículo:

  * `Pendiente`
  * `Incluido`
  * `Excluido`
  * `Revisar después`
* Exportación a Excel del conjunto de artículos actualmente filtrado.
* Eliminación de artículos individuales.
* Eliminación de una carga completa.
* Eliminación de todos los artículos asociados a la sesión activa.

---

## Propósito del proyecto

Biblos nace como un proyecto de portafolio orientado a trabajar con datos bibliográficos reales provenientes de archivos Excel.

Su objetivo es practicar y demostrar habilidades en:

* desarrollo backend con Django;
* modelado de datos;
* manejo de archivos Excel;
* limpieza e importación de datos con `pandas`;
* construcción de filtros, búsquedas y vistas dinámicas;
* exportación de datos;
* organización de una aplicación web mantenible.

---

## Cómo funciona la sesión

La aplicación no utiliza cuentas de usuario para la revisión principal.
En su lugar, los artículos visibles se filtran por la sesión activa del navegador mediante `request.session.session_key`.

Esto implica que:

* cada navegador ve solo sus propias cargas;
* dos navegadores distintos pueden trabajar con datos separados;
* si se borra la sesión del navegador, la separación entre cargas puede perderse;
* los datos siguen existiendo en la base de datos hasta que se eliminan desde la app o directamente desde la base.

Este comportamiento permite simular una experiencia de trabajo individual sin implementar todavía un sistema completo de autenticación.

---

## Stack tecnológico

* Python 3.11+
* Django 5.2
* pandas
* openpyxl
* python-dotenv
* WhiteNoise
* SQLite en desarrollo

---

## Instalación local

Clonar el repositorio:

```bash
git clone https://github.com/naabit/biblos.git
cd biblos
```

Crear y activar un entorno virtual:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Instalar dependencias:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Aplicar migraciones:

```powershell
python manage.py migrate
```

Opcionalmente, crear un superusuario para acceder al panel de administración:

```powershell
python manage.py createsuperuser
```

---

## Variables de entorno

El proyecto carga variables desde un archivo `.env` usando `python-dotenv`.

Variables utilizadas actualmente:

```env
SECRET_KEY=tu-clave-secreta
DEBUG=True
```

Ejemplo de archivo `.env`:

```env
SECRET_KEY=django-insecure-cambia-esta-clave-en-desarrollo
DEBUG=True
```

> Nota: en desarrollo, el proyecto puede ejecutarse con `DEBUG=True`. Para producción, se debe usar una clave secreta segura y configurar correctamente `ALLOWED_HOSTS`.

---

## Ejecutar el proyecto

Con el entorno virtual activado:

```powershell
python manage.py runserver
```

Luego abrir en el navegador:

```text
http://127.0.0.1:8000/
```

---

## Rutas principales

| Ruta       | Descripción                        |
| ---------- | ---------------------------------- |
| `/`        | Listado y revisión de artículos    |
| `/upload/` | Carga de archivos Excel            |
| `/export/` | Exportación del resultado filtrado |
| `/admin/`  | Panel de administración de Django  |

---

## Formato esperado del Excel

La importación espera archivos `.xlsx` con columnas bibliográficas como:

| Columna     | Contenido          |
| ----------- | ------------------ |
| `TI`        | Título             |
| `AU`        | Autores            |
| `PY`        | Año de publicación |
| `AB`        | Resumen            |
| `KW_Merged` | Palabras clave     |
| `DI`        | DOI                |
| `SO`        | Fuente o revista   |

Si alguna columna falta, la aplicación intenta completar el campo con cadena vacía o `None`, según corresponda.

---

## Estructura principal del proyecto

```text
biblos/
|-- articles/
|   |-- models.py
|   |-- views.py
|   |-- forms.py
|   |-- utils.py
|   `-- templates/articles/
|-- config/
|   |-- settings.py
|   `-- urls.py
|-- static/
|   |-- articles/css/
|   |-- articles/js/
|   `-- img/
|-- manage.py
|-- requirements.txt
|-- build.sh
`-- README.md
```

---

## Despliegue

El proyecto incluye un archivo `build.sh` pensado para plataformas como Render.

```bash
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
```

Los archivos estáticos se sirven con WhiteNoise y se recopilan en la carpeta `staticfiles/`.

---

## Estado actual

Biblos se encuentra en desarrollo activo como proyecto de portafolio.

Actualmente permite importar, filtrar, revisar, clasificar y exportar artículos bibliográficos desde archivos Excel. La separación entre revisiones se maneja mediante sesiones del navegador, sin autenticación de usuarios.

---

## Limitaciones actuales

* Solo acepta archivos `.xlsx`.
* Usa SQLite como base de datos por defecto en desarrollo.
* No incluye autenticación de usuarios para separar revisiones entre personas.
* La separación de datos depende de la sesión activa del navegador.
* La estructura de columnas esperada está pensada para archivos bibliográficos ya normalizados.
* La configuración de idioma y zona horaria puede requerir ajustes para producción.

---

## Próximas mejoras posibles

* Agregar autenticación de usuarios.
* Permitir múltiples proyectos o revisiones por usuario.
* Mejorar la validación del archivo importado.
* Mostrar un resumen estadístico por lote.
* Agregar paginación avanzada.
* Permitir edición directa de campos bibliográficos.
* Incorporar pruebas automatizadas.
* Preparar configuración para PostgreSQL en producción.

---

## Autora

Desarrollado por **Natalia García Cofré** como parte de su portafolio de desarrollo web, backend y herramientas digitales para organización de información.
