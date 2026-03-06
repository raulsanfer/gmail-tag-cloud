# agents.md

Guía para agentes que trabajen en este repositorio.

## Objetivo
Aplicación FastAPI para analizar correos de Gmail por remitente y permitir borrado masivo por `sender` usando la API de Gmail.

## Estructura
- `main.py`: rutas HTTP y render del HTML.
- `gmail_service.py`: acceso a Gmail API, conteo y borrado.
- `auth.py`: OAuth (`credentials.json` -> `token.json`).
- `templates/index.html`: UI principal.
- `templates/static/styles.css`: estilos.

## Entorno esperado
- Python 3.10+.
- Dependencias principales:
  - `fastapi`
  - `uvicorn`
  - `google-api-python-client`
  - `google-auth-oauthlib`
  - `google-auth-httplib2`

## Configuración OAuth
1. Colocar `credentials.json` en la raíz del proyecto.
2. Primer arranque: se abre flujo OAuth local.
3. Se genera `token.json` automáticamente.

Notas:
- No subir `credentials.json` ni `token.json` al repositorio.
- El scope actual es `https://www.googleapis.com/auth/gmail.modify`.

## Ejecutar en local
```bash
uvicorn main:app --reload
```

## Comportamiento actual
- `GET /`: obtiene mensajes (`in:anywhere`), normaliza remitentes y muestra conteos.
- `POST /delete/{sender}`: borra mensajes de ese remitente usando `batchDelete`.

## Reglas para cambios
- Mantener compatibilidad con el flujo OAuth de `auth.py`.
- En lógica de borrado, priorizar seguridad y validaciones antes de enviar `batchDelete`.
- Si se toca performance, evitar múltiples llamadas innecesarias a Gmail API.
- Evitar dependencias nuevas si no son estrictamente necesarias.

## Checklist mínimo antes de terminar una tarea
1. Verificar que la app arranca con `uvicorn main:app --reload`.
2. Revisar que `GET /` renderiza sin errores.
3. Si hubo cambios en borrado, comprobar que `delete_by_sender` devuelve número de mensajes eliminados.
4. Confirmar que no se añadieron secretos al repo.

## Convención de respuestas de agente
- Explicar primero qué se cambió.
- Incluir rutas de archivos tocados.
- Indicar qué validaciones se ejecutaron y cuáles no.
