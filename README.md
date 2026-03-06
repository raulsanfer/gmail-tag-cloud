# InboxSweep

InboxSweep es una aplicación web en FastAPI para analizar remitentes de Gmail y limpiar correos en lote.
Muestra una nube de remitentes por frecuencia, permite filtrar por periodos (1-6 meses) y encola la eliminación/movido a papelera en segundo plano.

## Funcionalidades

- Nube de remitentes con contador de correos.
- Filtro por periodo:
  - Último mes
  - Últimos 2 meses
  - ...hasta 6 meses
- Selección múltiple de remitentes con checkbox.
- Eliminación en cola (`BackgroundTasks`) con progreso y resumen final.
- Refresco automático al terminar el job.

## Requisitos

- Python 3.10+
- Cuenta de Gmail
- Proyecto en Google Cloud con Gmail API habilitada

Dependencias Python usadas:

- `fastapi`
- `uvicorn`
- `google-api-python-client`
- `google-auth-oauthlib`
- `google-auth-httplib2`

## Instalación

En la raíz del proyecto:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn google-api-python-client google-auth-oauthlib google-auth-httplib2
```

Si usas `fish`:

```fish
source .venv/bin/activate.fish
```

## Crear `credentials.json` (Google OAuth)

1. Entra en Google Cloud Console: https://console.cloud.google.com/
2. Crea un proyecto nuevo (o usa uno existente).
3. Activa **Gmail API** en `APIs y servicios > Biblioteca`.
4. Configura la pantalla OAuth en `APIs y servicios > Pantalla de consentimiento OAuth`.
5. Crea credenciales en `APIs y servicios > Credenciales > Crear credenciales > ID de cliente OAuth`.
6. Tipo de aplicación: **Desktop app**.
7. Descarga el JSON y guárdalo como `credentials.json` en la raíz del proyecto.

Ruta esperada:

```text
./credentials.json
```

## Generar `token.json`

`token.json` se genera automáticamente en el primer uso:

1. Arranca la app.
2. Abre la URL local.
3. Acepta el flujo OAuth en el navegador.

Al finalizar, se creará:

```text
./token.json
```

## Ejecución

```bash
uvicorn main:app --reload --port 8001
```

Luego abre:

```text
http://127.0.0.1:8001
```

## Uso básico

1. Selecciona el periodo en el combo.
2. Pulsa `Buscar`.
3. Marca uno o varios remitentes.
4. Pulsa `Eliminar seleccionados (encolar)`.
5. Revisa progreso y resumen.
6. Al terminar, la vista se refresca automáticamente.

## Notas importantes

- La app usa scope `gmail.modify`.
- Según permisos de la cuenta, algunos correos pueden moverse a papelera en lugar de borrarse permanentemente.
- No subas `credentials.json` ni `token.json` al repositorio.

Sugerido en `.gitignore`:

```gitignore
credentials.json
token.json
__pycache__/
```
