# Deployment Perfum Lab API

Ruta soportada para produccion:

```text
PerfumLab.exe -> HTTPS -> FastAPI -> PostgreSQL
```

Fragella se consume solo desde FastAPI. El desktop nunca recibe
`DATABASE_URL`, `SECRET_KEY`, password PostgreSQL ni `FRAGELLA_API_KEY`.

## 1. Servidor

Configura variables de entorno en el servidor o en el gestor seguro del
proveedor:

```text
APP_ENV=production
DATABASE_URL=postgresql+psycopg://...
SECRET_KEY=...
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=https://app.<dominio>
CORS_ALLOW_CREDENTIALS=true
ENABLE_DOCS=false
LOG_LEVEL=INFO
PERFUME_PROVIDER=fragella
FRAGELLA_API_KEY=...
FRAGELLA_BASE_URL=https://api.fragella.com/api/v1
FRAGELLA_TIMEOUT_SECONDS=10
```

No guardes valores reales en Git ni en el EXE.

## 2. Migracion

Antes de levantar la version nueva:

```powershell
uv run alembic upgrade head
```

Las migraciones no se ejecutan desde requests ni desde el desktop.

## 3. Arranque

Servicio directo:

```powershell
uv run uvicorn app.main_api:app --host 0.0.0.0 --port 8000
```

Container:

```powershell
docker build -t perfumlab-api .
docker run --env-file .env -p 8000:8000 perfumlab-api
```

No uses `--reload` en produccion.

## 4. HTTPS

Coloca FastAPI detras de Caddy, Nginx o la capa TLS del proveedor cloud.

Firewall recomendado:

```text
Internet -> 443 -> reverse proxy/API
PostgreSQL 5432 -> privado/restringido al backend
```

Si se usan forwarded headers, limita `FORWARDED_ALLOW_IPS` al proxy real.

## 5. Health

Verifica externamente por HTTPS:

```text
GET /api/v1/health
GET /api/v1/health/db
```

Ambos deben responder 200. `/api/v1/health/db` no expone credenciales.

## 6. Backup

Antes de desplegar:

```powershell
uv run python scripts/backup_postgres.py
```

El script usa `pg_dump`, toma credenciales desde `DATABASE_URL` y no las imprime.

## 7. Restore

Restore manual para backup custom:

```powershell
pg_restore --clean --if-exists --dbname "<DATABASE_URL_DESTINO>" backups\archivo.dump
```

Restore para SQL plano:

```powershell
psql "<DATABASE_URL_DESTINO>" -f backups\archivo.sql
```

No hay restore automatico en la aplicacion.

## 8. Rollback

Procedimiento recomendado:

1. Crear backup.
2. Desplegar backend.
3. Ejecutar migraciones.
4. Probar health, auth y flujos criticos.
5. Si falla el servicio, restaurar la version anterior del backend.
6. Si hubo una migracion incompatible, decidir restore desde backup en ventana
   controlada. No ejecutar downgrades destructivos automaticamente.

## 9. Desktop

Build de produccion:

```powershell
uv run python scripts/build_desktop.py --mode production --api-url https://api.<dominio>
```

El resultado `dist/PerfumLab/PerfumLab.exe` se entrega junto con
`perfumlab_desktop.json`. Ese JSON contiene solo la URL publica de API y
parametros no sensibles.
