# ami-backend

Este documento describe, de forma general, la funcion de cada carpeta del proyecto.

## Estructura General

### app/
Carpeta principal de la aplicacion. Contiene toda la logica del backend (configuracion, modelos, rutas, servicios, etc.).

## Estructura Dentro de app/

### core/
Configuraciones centrales de la aplicacion: variables de entorno, conexion a base de datos y seguridad.

### models/
Definicion de entidades/tablas del sistema (estructura de datos persistidos).

### repositories/
Capa de acceso a datos. Se encarga de consultar y persistir informacion en la base de datos.

### routers/
Definicion de endpoints HTTP (rutas de la API) que exponen funcionalidades del sistema.

### schemas/
Esquemas de entrada/salida para validacion y serializacion de datos (contratos de la API).

### services/
Logica de negocio de la aplicacion. Orquesta validaciones, reglas y llamadas a repositorios.

### seeds/
Scripts o utilidades para poblar datos iniciales/requeridos en la base de datos.

### utils/
Funciones auxiliares reutilizables para tareas transversales (por ejemplo envio de correo).

## Archivos Relevantes en la Raiz

### .env
Variables de entorno locales usadas en ejecucion.

### ,env.example
Plantilla de variables de entorno para configurar el proyecto en otros entornos.

### requirements.txt
Listado de dependencias de Python necesarias para ejecutar el backend.


### Comando que deben ejecutar en ese orden para instalar lo necesario para el backend

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

### Para ejecutar el proyecto
uvicorn app.main:app --reload

## Reportes dinamicos con IA

El backend incluye el modulo `/api/reportes` para interpretar y ejecutar reportes dinamicos en espanol.

### Variables necesarias

En tu archivo `.env` agrega, si corresponde, la clave de OpenAI y el modelo a usar:

```env
OPENAI_API_KEY=tu_clave
OPENAI_REPORT_MODEL=gpt5.4mini
REPORTES_USAR_OPENAI=true
```

Si no hay clave, el sistema usa una interpretacion local por plantilla como respaldo.
Si quieres probar sin llamar a OpenAI, usa `REPORTES_USAR_OPENAI=false`.

### Endpoints

- `GET /api/reportes/plantillas`
- `POST /api/reportes/{empresa_id}/run`
- `POST /api/reportes/{empresa_id}/interpretar`

El endpoint principal para consumir desde el front es `POST /api/reportes/{empresa_id}/run`.
Recibe solo el `prompt` en el body y usa el `empresa_id` de la ruta para buscar los datos de esa empresa.

Ejemplo:

```json
{
	"prompt": "Resumen de ventas del ultimo mes"
}
```

### Prueba rapida

```powershell
python scripts/probar_reportes.py
```
