# Biblos

**Biblos** es una aplicación web desarrollada con Django para importar, revisar, clasificar y exportar artículos bibliográficos desde archivos Excel.

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
* Eliminación de una carga completa junto con sus artículos asociados.
* Eliminación de todos los artículos vinculados a la sesión activa.

---

## Propósito del proyecto

Biblos nace como un proyecto de portafolio orientado al trabajo con datos bibliográficos provenientes de archivos Excel.

Su objetivo es practicar y demostrar habilidades en:

* Desarrollo backend con Django.
* Modelado de datos relacionales.
* Manejo e importación de archivos Excel.
* Limpieza y normalización básica de datos con `pandas`.
* Construcción de filtros, búsquedas y vistas dinámicas.
* Exportación de datos.
* Testing de flujos críticos de una aplicación web.
* Organización de una aplicación mantenible y preparada para crecer.

---

## Cómo funciona la sesión

La aplicación no utiliza cuentas de usuario para la revisión principal. En su lugar, los artículos visibles se filtran mediante la sesión activa del navegador, usando `request.session.session_key`.

Esto implica que:

* Cada navegador ve solo sus propias cargas y artículos.
* Dos navegadores distintos pueden trabajar con datos separados.
* Las operaciones de actualización y eliminación se restringen a los registros asociados con la sesión activa.
* Si se borra la sesión del navegador, esa separación puede perderse.
* Los datos permanecen en la base de datos hasta que se eliminan desde la aplicación o directamente desde la base de datos.

Este comportamiento permite ofrecer una experiencia de trabajo individual sin implementar todavía un sistema completo de autenticación.

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

Clona el repositorio:

```bash
git clone https://github.com/naabit/biblos.git
cd biblos
```

Crea y activa un entorno virtual:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Instala las dependencias:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Aplica las migraciones:

```powershell
python manage.py migrate
```

Opcionalmente, crea un superusuario para acceder al panel de administración:

```powershell
python manage.py createsuperuser
```

---

## Variables de entorno

El proyecto carga variables desde un archivo `.env` mediante `python-dotenv`.

Variables utilizadas actualmente:

```env
SECRET_KEY=tu-clave-secreta
DEBUG=True
```

Ejemplo de archivo `.env` para desarrollo:

```env
SECRET_KEY=django-insecure-cambia-esta-clave-en-desarrollo
DEBUG=True
```

> En producción, utiliza una clave secreta segura, configura `DEBUG=False` y define correctamente `ALLOWED_HOSTS`.

---

## Ejecutar el proyecto

Con el entorno virtual activado:

```powershell
python manage.py runserver
```

Luego abre en el navegador:

```text
http://127.0.0.1:8000/
```

---

## Rutas principales

| Ruta       | Descripción                               |
| ---------- | ----------------------------------------- |
| `/`        | Listado, búsqueda y revisión de artículos |
| `/upload/` | Carga de archivos Excel                   |
| `/export/` | Exportación del resultado filtrado        |
| `/admin/`  | Panel de administración de Django         |

---

## Formato esperado del Excel

La importación espera archivos `.xlsx` con columnas bibliográficas como las siguientes:

| Columna     | Contenido          |
| ----------- | ------------------ |
| `TI`        | Título             |
| `AU`        | Autores            |
| `PY`        | Año de publicación |
| `AB`        | Resumen            |
| `KW_Merged` | Palabras clave     |
| `DI`        | DOI                |
| `SO`        | Fuente o revista   |

Cuando faltan valores en columnas esperadas, la aplicación intenta completar los campos con una cadena vacía o `None`, según corresponda.

Por ejemplo:

* Un año vacío se guarda como `None`.
* Un DOI vacío o identificado como valor nulo se normaliza como una cadena vacía.

---

## Testing

Biblos incluye una suite inicial de pruebas automatizadas con el framework de testing integrado de Django.

Actualmente, la suite cubre flujos relevantes de la aplicación:

* Renderizado del formulario de carga.
* Importación de archivos Excel.
* Creación de lotes mediante `ExcelUpload`.
* Creación de artículos asociados a una carga.
* Normalización básica de valores vacíos durante la importación.
* Aislamiento de artículos por sesión del navegador.
* Búsqueda, filtros y ordenamiento del listado.
* Actualización de estado mediante solicitudes AJAX.
* Borrado individual y borrado masivo restringidos a la sesión activa.
* Exportación a Excel respetando los filtros seleccionados.
* Exportación de etiquetas visibles de estado, como `Incluido` o `Pendiente`.

Para ejecutar las pruebas:

```powershell
python manage.py test
```

Resultado actual de la suite:

```text
Found 9 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.........
----------------------------------------------------------------------
Ran 9 tests in 0.278s

OK
Destroying test database for alias 'default'...
```

Durante la ejecución, Django crea una base de datos temporal para aislar las pruebas y la elimina al finalizar, sin modificar los datos locales de desarrollo.

---

## Estructura principal del proyecto

```text
biblos/
|-- articles/
|   |-- forms.py
|   |-- models.py
|   |-- tests.py
|   |-- urls.py
|   |-- utils.py
|   |-- views.py
|   `-- templates/
|       `-- articles/
|-- config/
|   |-- settings.py
|   `-- urls.py
|-- static/
|   |-- articles/
|   |   |-- css/
|   |   `-- js/
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

Los archivos estáticos se sirven mediante WhiteNoise y se recopilan en la carpeta `staticfiles/`.

---

## Estado actual

Biblos se encuentra en desarrollo activo como proyecto de portafolio.

Actualmente permite importar, filtrar, buscar, revisar, clasificar, eliminar y exportar artículos bibliográficos desde archivos Excel. También cuenta con una suite inicial de pruebas automatizadas para validar los principales flujos de importación, sesión, filtrado, actualización, eliminación y exportación.

---

## Limitaciones actuales

* Solo acepta archivos `.xlsx`.
* Usa SQLite como base de datos por defecto en desarrollo.
* No incluye autenticación de usuarios.
* La separación de datos depende de la sesión activa del navegador.
* La estructura esperada está pensada para archivos bibliográficos previamente normalizados.
* La validación de años y otros valores importados puede mejorarse para archivos con datos inconsistentes.
* La configuración de idioma y zona horaria puede requerir ajustes para producción.

---

## Próximas mejoras posibles

* Agregar autenticación de usuarios.
* Permitir múltiples proyectos o revisiones por usuario.
* Mejorar la validación de archivos y columnas durante la importación.
* Manejar de forma más robusta años inválidos o valores bibliográficos inconsistentes.
* Ampliar la cobertura de pruebas para escenarios de error, importaciones fallidas y validaciones de seguridad adicionales.
* Mostrar un resumen estadístico por lote.
* Agregar paginación avanzada.
* Permitir edición directa de campos bibliográficos.
* Preparar una configuración con PostgreSQL para producción.
* Explorar compatibilidad con formatos provenientes de distintas bases académicas, como Scopus y Web of Science.

---

## Autora

Desarrollado por **Natalia García Cofré** como parte de su portafolio de desarrollo web, backend, testing y herramientas digitales para la organización de información.
