# FastAPI Backend Deployment - Railway.app

**Última actualización:** 2026-01-23

Esta guía te llevará paso a paso para desplegar tu API de FastAPI en Railway.app.

---

## 📋 Pre-requisitos

Antes de comenzar, asegúrate de tener:

- ✅ Cuenta en Railway.app (https://railway.app)
- ✅ Backend funcionando localmente (`uvicorn app.main:app`)
- ✅ Cuenta en Supabase con la base de datos configurada
- ✅ API Key de Ollama/OpenAI/HuggingFace configurada
- ✅ Git instalado y repositorio inicializado

---

## 🚀 Paso 1: Preparar el Proyecto

### 1.1 Verificar Dockerfile

Railway usa Docker para desplegar. Verifica que tienes un `Dockerfile` en `python-api/`:

```dockerfile
# python-api/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Exponer puerto
EXPOSE 8000

# Comando de inicio
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 1.2 Verificar .dockerignore

Crea `python-api/.dockerignore` para excluir archivos innecesarios:

```
.env
.env.example
.venv
__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.so
.pytest_cache
.coverage
htmlcov/
*.log
.git
.gitignore
README.md
tests/
```

### 1.3 Crear railway.json (Opcional)

Crea `python-api/railway.json` para configuración específica de Railway:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 30,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

---

## 🔐 Paso 2: Preparar Variables de Entorno

### 2.1 Crear lista de variables

En un archivo temporal (NO lo comitees), prepara tus variables:

```bash
# Variables para Railway
API_KEY=<genera-una-nueva-key-segura>
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
OPENAI_API_KEY=sk-proj-...  # O las que uses
LLM_PROVIDER=ollama  # o openai, huggingface
LLM_MODEL=qwen2.5:3b-instruct
LLM_TEMPERATURE=0.1
LOG_LEVEL=INFO
ENVIRONMENT=production
```

**⚠️ IMPORTANTE:**
- Genera una nueva `API_KEY` para producción (no uses la de desarrollo)
- Usa el `SUPABASE_SERVICE_ROLE_KEY` (NO la anon key)

```bash
# Generar nueva API_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🚂 Paso 3: Desplegar en Railway

### 3.1 Crear Proyecto en Railway

1. Ve a https://railway.app/new
2. Click en **"Deploy from GitHub repo"**
3. Autoriza Railway para acceder a GitHub
4. Selecciona tu repositorio `ia-powered-support`

**O si prefieres Railway CLI:**

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Inicializar proyecto
cd python-api
railway init
```

### 3.2 Configurar Servicio

1. Railway detectará automáticamente el Dockerfile
2. En **Settings**:
   - **Root Directory**: Cambia a `python-api`
   - **Watch Paths**: `python-api/**`
   - **Build Command**: (Déjalo vacío, usa Dockerfile)
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 3.3 Configurar Variables de Entorno

En Railway UI:
1. Ve a tu servicio → **Variables**
2. Click en **"+ New Variable"**
3. Agrega una por una:

```
API_KEY = <tu-api-key-generada>
SUPABASE_URL = https://tu-proyecto.supabase.co
SUPABASE_SERVICE_ROLE_KEY = eyJ...
OPENAI_API_KEY = sk-proj-...  (si usas OpenAI)
LLM_PROVIDER = ollama
LLM_MODEL = qwen2.5:3b-instruct
LLM_TEMPERATURE = 0.1
LOG_LEVEL = INFO
ENVIRONMENT = production
```

**O con Railway CLI:**

```bash
railway variables set API_KEY="<tu-key>"
railway variables set SUPABASE_URL="https://..."
railway variables set SUPABASE_SERVICE_ROLE_KEY="eyJ..."
railway variables set LLM_PROVIDER="ollama"
railway variables set LLM_MODEL="qwen2.5:3b-instruct"
railway variables set LLM_TEMPERATURE="0.1"
railway variables set LOG_LEVEL="INFO"
railway variables set ENVIRONMENT="production"
```

### 3.4 Configurar Dominio

1. Ve a **Settings** → **Networking**
2. Click en **"Generate Domain"**
3. Railway te dará una URL como: `your-app.up.railway.app`
4. (Opcional) Agrega un dominio custom

---

## ✅ Paso 4: Verificar Deployment

### 4.1 Ver Logs

En Railway UI:
- Ve a **Deployments** → Click en el último deployment
- Ve la pestaña **"Build Logs"** y **"Deploy Logs"**

O con CLI:
```bash
railway logs
```

### 4.2 Health Check

Una vez desplegado, verifica:

```bash
# Health check
curl https://your-app.up.railway.app/health

# Debería retornar:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "timestamp": "2026-01-23T...",
#   "services": {
#     "database": "up",
#     "llm": "configured"
#   }
# }
```

### 4.3 Probar API Docs

Visita en tu navegador:
- **Swagger UI**: `https://your-app.up.railway.app/docs`
- **ReDoc**: `https://your-app.up.railway.app/redoc`

### 4.4 Probar Endpoint de Clasificación

```bash
# Crear ticket de prueba en Supabase
TICKET_ID="<uuid-de-ticket-real>"

# Probar clasificación
curl -X POST https://your-app.up.railway.app/api/v1/process-ticket \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <tu-api-key>" \
  -d "{
    \"ticket_id\": \"$TICKET_ID\",
    \"description\": \"Mi conexión a internet no funciona desde esta mañana\"
  }"
```

---

## 🔧 Paso 5: Configuración Avanzada (Opcional)

### 5.1 Configurar Health Checks

En Railway → **Settings** → **Health Checks**:

- **Path**: `/health`
- **Port**: `8000`
- **Interval**: `30` segundos
- **Timeout**: `10` segundos
- **Retries**: `3`

### 5.2 Configurar Autoscaling (Pro Plan)

En **Settings** → **Autoscaling**:
- **Min Replicas**: `1`
- **Max Replicas**: `3`
- **CPU Threshold**: `80%`
- **Memory Threshold**: `85%`

### 5.3 Configurar Monitoreo

Railway incluye métricas básicas:
- CPU Usage
- Memory Usage
- Network Traffic
- Request Count

Para monitoreo avanzado, considera integrar:
- Sentry (errores)
- Datadog (APM)
- LogTail (logs centralizados)

---

## 🐛 Troubleshooting

### Error: "Connection to Supabase failed"

**Causa:** Variables de entorno incorrectas

**Solución:**
```bash
# Verificar variables
railway variables

# Re-verificar SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY
# Asegúrate de usar SERVICE_ROLE_KEY, no ANON_KEY
```

---

### Error: "Health check failing"

**Causa:** App no responde en el puerto correcto

**Solución:**
```python
# En app/main.py, asegúrate de usar PORT de environment
import os
port = int(os.getenv("PORT", 8000))

# Railway asigna PORT automáticamente
# Usa --port $PORT en el start command
```

---

### Error: "Out of memory (OOM)"

**Causa:** Railway free tier tiene límite de 512MB RAM

**Solución:**
1. Optimizar imports (lazy loading)
2. Reducir workers de uvicorn
3. Upgrade a Railway Pro ($5/mo = 8GB RAM)

```bash
# Start command optimizado para free tier
uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
```

---

### Error: "LLM timeout"

**Causa:** Ollama no disponible en Railway (necesita GPU)

**Solución:**
Cambiar a OpenAI o HuggingFace en producción:

```bash
railway variables set LLM_PROVIDER="openai"
railway variables set LLM_MODEL="gpt-3.5-turbo"
railway variables set OPENAI_API_KEY="sk-..."
```

**Nota:** Ollama requiere deployment en infraestructura con GPU (GCP, AWS, etc.)

---

### Error: "Build failed"

**Causa:** Dependencias faltantes o Dockerfile incorrecto

**Solución:**
```bash
# Probar build localmente
cd python-api
docker build -t test-api .
docker run -p 8000:8000 test-api

# Si funciona localmente, el problema es configuración en Railway
```

---

## 📊 Monitoreo Post-Deployment

### Métricas a Vigilar

1. **Response Time**: Debe ser < 5s en p95
2. **Error Rate**: Debe ser < 1%
3. **CPU Usage**: Debe estar < 80%
4. **Memory Usage**: Debe estar < 400MB (free tier)

### Logs Estructurados

Los logs aparecerán en Railway Logs con formato JSON:

```json
{
  "timestamp": "2026-01-23T10:30:15.123Z",
  "level": "INFO",
  "message": "Ticket classified successfully",
  "request_id": "req_abc123",
  "ticket_id": "uuid...",
  "category": "Técnico",
  "processing_time_ms": 4234
}
```

---

## 🔄 Actualizaciones y CI/CD

### Deployment Automático

Railway se actualiza automáticamente con cada push a tu rama principal:

```bash
git add .
git commit -m "Update: improve classification prompt"
git push origin main

# Railway detecta el push y despliega automáticamente
```

### Deployment Manual

Si prefieres control manual:

1. Railway → **Settings** → **Automatic Deployments**: OFF
2. Despliega manualmente:
   ```bash
   railway up
   ```

### Rollback

Si algo sale mal:

1. Railway → **Deployments**
2. Click en deployment anterior que funcionaba
3. Click en **"Rollback to this deployment"**

---

## 💰 Costos Estimados

### Railway Free Tier
- ✅ 500 horas de ejecución/mes
- ✅ 512 MB RAM
- ✅ 1 GB disco
- ✅ 100 GB transferencia
- ⚠️ Sin custom domains
- ⚠️ App duerme después de 15 min inactividad

**Suficiente para:** Desarrollo, demos, MVP con < 100 tickets/día

### Railway Pro ($5/mes)
- ✅ Ejecución ilimitada
- ✅ 8 GB RAM
- ✅ 100 GB disco
- ✅ 100 GB transferencia
- ✅ Custom domains
- ✅ Sin sleep mode

**Suficiente para:** Producción con 1,000+ tickets/día

---

## ✅ Checklist Final

Marca cada item antes de considerar el deployment completo:

- [ ] Build exitoso en Railway
- [ ] Health check retorna "healthy"
- [ ] Swagger UI accesible en /docs
- [ ] Endpoint /process-ticket funciona
- [ ] Variables de entorno configuradas
- [ ] Logs aparecen correctamente
- [ ] Dominio generado y accesible
- [ ] Conexión a Supabase verificada
- [ ] LLM respondiendo correctamente
- [ ] URL guardada para configurar en frontend
- [ ] URL guardada para configurar en n8n
- [ ] Documentación actualizada con URL de producción

---

## 📚 Recursos Adicionales

- **Railway Docs**: https://docs.railway.app
- **Railway CLI**: https://docs.railway.app/develop/cli
- **Railway Status**: https://railway.app/status
- **Railway Discord**: https://discord.gg/railway
- **FastAPI Deployment**: https://fastapi.tiangolo.com/deployment/

---

## 🎉 ¡Listo!

Tu backend está desplegado en Railway. Guarda la URL y continúa con el deployment del frontend en Vercel.

**URL de tu API:** `https://your-app.up.railway.app`

**Próximo paso:** [Frontend Deployment en Vercel](./vercel-frontend.md)

---

*Última actualización: 2026-01-23*
