# Guía de Setup Local y Testing Pre-Producción

**Última actualización:** 2026-01-22

---

## 📋 Prerequisitos

Antes de comenzar, asegúrate de tener instalado:

```bash
# Verificar versiones mínimas
node --version    # >= 18.0.0
npm --version     # >= 9.0.0
python --version  # >= 3.11
docker --version  # >= 24.0 (opcional, para n8n local)
git --version     # >= 2.40
```

También necesitarás:
- [ ] Cuenta en Supabase (https://supabase.com)
- [ ] API Key de OpenAI (https://platform.openai.com/api-keys)
- [ ] Editor de código (VSCode recomendado)

---

## 🚀 Paso 1: Clonar el Repositorio

```bash
# Clonar
git clone https://github.com/tu-usuario/ia-powered-support.git
cd ia-powered-support

# Verificar estructura
tree -L 2 -I 'node_modules|__pycache__|.venv'
```

**Estructura esperada:**
```
ia-powered-support/
├── supabase/
│   └── setup.sql
├── python-api/
│   ├── app/
│   ├── requirements.txt
│   └── Dockerfile
├── n8n-workflow/
│   └── workflow.json
├── frontend/
│   ├── src/
│   └── package.json
└── docs/
```

---

## 🗄️ Paso 2: Configurar Supabase

### 2.1 Crear Proyecto en Supabase

1. Ve a https://app.supabase.com
2. Click en "New Project"
3. Configura:
   - **Name:** `ia-support-dev` (o el que prefieras)
   - **Database Password:** Genera uno seguro (guárdalo)
   - **Region:** Selecciona el más cercano a ti
4. Espera 2-3 minutos a que se cree el proyecto

### 2.2 Ejecutar el Schema SQL

#### **Opción A: Dashboard de Supabase** ⭐ **Recomendado - Más Fácil**

```bash
# 1. Abre el archivo SQL en tu editor
cat supabase/setup.sql

# 2. Copia TODO el contenido (Ctrl+A, Ctrl+C)

# 3. Ve al SQL Editor de tu proyecto:
# https://supabase.com/dashboard/project/TU_PROJECT_REF/sql/new

# 4. Pega el SQL completo en el editor

# 5. Click en "RUN" (botón ▶️ arriba a la derecha)

# 6. Deberías ver: "Success. No rows returned"
```

#### **Opción B: Supabase CLI** (Requiere instalación)

```bash
# 1. Instalar Supabase CLI (si no lo tienes)
npm install -g supabase

# 2. Login
supabase login

# 3. Link al proyecto
supabase link --project-ref TU_PROJECT_REF
# Te pedirá la password de la DB

# 4. Ejecutar SQL usando stdin
cat supabase/setup.sql | supabase db execute --linked

# O usando psql directamente:
# psql "postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres" -f supabase/setup.sql
```

**Nota:** La flag `--file` no existe en `supabase db push`. Usa el Dashboard o `db execute` con stdin.

### 2.3 Verificar que la tabla se creó

```sql
-- Ejecuta esto en SQL Editor para verificar
SELECT
  table_name,
  column_name,
  data_type,
  is_nullable
FROM information_schema.columns
WHERE table_name = 'tickets'
ORDER BY ordinal_position;

-- Deberías ver 13 columnas (id, created_at, description, etc.)
```

### 2.4 Obtener Credentials

Ve a **Project Settings > API** y copia:

```bash
# Guarda estos valores (los necesitarás después)
SUPABASE_URL="https://tu-proyecto.supabase.co"
SUPABASE_SERVICE_ROLE_KEY="eyJ..."  # Service role (NO la anon key)
```

⚠️ **IMPORTANTE:** Usa la **service_role** key (no la anon key) para el backend.

---

## 🐍 Paso 3: Configurar Backend (FastAPI)

### 3.1 Crear Entorno Virtual

```bash
cd python-api

# Crear virtualenv
python -m venv .venv

# Activar
# En Linux/Mac:
source .venv/bin/activate
# En Windows:
.venv\Scripts\activate

# Verificar que estás en el venv
which python  # Debería mostrar la ruta al venv
```

### 3.2 Instalar Dependencias

```bash
# Actualizar pip
pip install --upgrade pip

# Instalar requirements
pip install -r requirements.txt

# Verificar instalación
pip list | grep -E "fastapi|langchain|supabase"
```

**Dependencias principales:**
- fastapi==0.109.0
- langchain==0.1.0
- langchain-openai==0.0.2
- supabase==2.3.0
- pydantic==2.5.0
- tenacity==8.2.3

### 3.3 Configurar Variables de Entorno

**Elige una de las dos opciones de LLM:**

#### **Opción A: OpenAI (Pago - $5 gratis primeros 3 meses)** ⭐ Recomendado para demo

```bash
# Crear archivo .env en python-api/
cat > .env << 'EOF'
# Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# OpenAI (Necesitas tarjeta de crédito, pero $5 gratis inicial)
OPENAI_API_KEY=sk-proj-...

# LLM Config
LLM_PROVIDER=openai
LLM_MODEL=gpt-3.5-turbo
LLM_TEMPERATURE=0.1

# App Config
LOG_LEVEL=INFO
ENVIRONMENT=development
EOF

# ⚠️ IMPORTANTE: Reemplaza los valores con tus credentials reales
nano .env  # o usa tu editor favorito
```

**Cómo obtener OpenAI API Key:**
1. Ve a https://platform.openai.com/api-keys
2. Crea cuenta (requiere tarjeta pero $5 gratis inicial)
3. Click "Create new secret key"
4. Copia la key (comienza con `sk-proj-...`)

---

#### **Opción B: HuggingFace (100% GRATIS)** ⭐ Recomendado para costo $0

```bash
# Crear archivo .env en python-api/
cat > .env << 'EOF'
# Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# HuggingFace (100% gratis para siempre)
HUGGINGFACE_API_TOKEN=hf_...

# LLM Config
LLM_PROVIDER=huggingface
LLM_MODEL=mistralai/Mixtral-8x7B-Instruct-v0.1
LLM_TEMPERATURE=0.1

# App Config
LOG_LEVEL=INFO
ENVIRONMENT=development
EOF

# ⚠️ IMPORTANTE: Reemplaza los valores con tus credentials reales
nano .env  # o usa tu editor favorito
```

**Cómo obtener HuggingFace Token (GRATIS):**
1. Ve a https://huggingface.co/join
2. Crea cuenta (gratis, no requiere tarjeta)
3. Ve a https://huggingface.co/settings/tokens
4. Click "New token" > Name: "ia-support" > Role: "read" > Create
5. Copia el token (comienza con `hf_...`)

**Límites HuggingFace (tier gratuito):**
- ~1000 requests por día
- Suficiente para desarrollo y pruebas
- Precisión: 85-92% (vs 95-98% de OpenAI)

---

**💡 Recomendación:**
- **Para demo/presentación:** Usa OpenAI (mejor precisión, $0.10 de costo real)
- **Para desarrollo continuo:** Usa HuggingFace (gratis, menor precisión pero aceptable)

### 3.4 Probar Conexión a Supabase

```bash
# Desde python-api/
python << 'EOF'
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

print(f"URL: {url}")
print(f"Key: {key[:20]}...")

client = create_client(url, key)
response = client.table("tickets").select("count").execute()
print(f"✅ Conexión exitosa! Tickets en DB: {len(response.data)}")
EOF
```

**Salida esperada:**
```
URL: https://tu-proyecto.supabase.co
Key: eyJhbGciOiJIUzI1NiI...
✅ Conexión exitosa! Tickets en DB: 5
```

### 3.5 Iniciar el Servidor FastAPI

```bash
# Desde python-api/
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Salida esperada:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345]
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 3.6 Verificar API (nueva terminal)

```bash
# Health check
curl http://localhost:8000/health | jq

# Debería retornar:
# {
#   "status": "healthy",
#   "timestamp": "2026-01-22T...",
#   "database": "connected",
#   "llm_provider": "openai"  // o "huggingface" si elegiste esa opción
# }
```

✅ **Si ves "status": "healthy" y "database": "connected", el backend está listo!**

**Nota:** El campo `llm_provider` mostrará:
- `"openai"` si configuraste OpenAI
- `"huggingface"` si configuraste HuggingFace

---

## ⚛️ Paso 4: Configurar Frontend (React)

### 4.1 Instalar Dependencias

```bash
# Nueva terminal
cd ../frontend

# Instalar packages
npm install

# Verificar que no hay errores
npm list --depth=0
```

**Dependencias principales:**
- react@18.2.0
- @supabase/supabase-js@2.39.0
- tailwindcss@3.4.0
- vite@5.0.8
- typescript@5.3.3

### 4.2 Configurar Variables de Entorno

```bash
# Crear .env en frontend/
cat > .env << 'EOF'
# Supabase (Frontend usa anon key, NO service role)
VITE_SUPABASE_URL=https://tu-proyecto.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...  # <- Esta es la ANON key

# API Backend (local)
VITE_API_URL=http://localhost:8000
EOF

# ⚠️ IMPORTANTE: Usa ANON key para frontend (no service role)
# Encuéntrala en: Project Settings > API > anon public
nano .env
```

⚠️ **Diferencia crítica:**
- **Backend:** Usa `SUPABASE_SERVICE_ROLE_KEY` (acceso completo)
- **Frontend:** Usa `VITE_SUPABASE_ANON_KEY` (acceso limitado por RLS)

### 4.3 Iniciar Dev Server

```bash
# Desde frontend/
npm run dev
```

**Salida esperada:**
```
VITE v5.0.8  ready in 523 ms

➜  Local:   http://localhost:5173/
➜  Network: http://192.168.1.x:5173/
➜  press h to show help
```

### 4.4 Abrir en Navegador

1. Ve a http://localhost:5173
2. Deberías ver el dashboard con:
   - Header con estadísticas (Total, Procesados, Pendientes)
   - Lista de 5 tickets de prueba (del setup.sql)
   - Indicador de conexión "Live updates active" 🟢

✅ **Si ves los tickets, el frontend está listo!**

---

## 🔄 Paso 5: Configurar n8n (Opcional para Local)

### Opción A: n8n en Docker (Recomendado)

```bash
# Desde el root del proyecto
cd ..

# Crear docker-compose.yml
cat > docker-compose.n8n.yml << 'EOF'
version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    container_name: n8n-local
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=false
      - N8N_HOST=localhost
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - WEBHOOK_URL=http://localhost:5678/
    volumes:
      - ./n8n-data:/home/node/.n8n
    restart: unless-stopped
EOF

# Iniciar n8n
docker-compose -f docker-compose.n8n.yml up -d

# Ver logs
docker logs -f n8n-local
```

**Salida esperada:**
```
n8n ready on port 5678
Editor is now accessible via: http://localhost:5678/
```

### Opción B: n8n con npm

```bash
# Instalar globalmente
npm install -g n8n

# Iniciar
n8n start
```

### 5.1 Importar Workflow

1. Ve a http://localhost:5678
2. Click en "Add workflow" (o presiona Ctrl+Alt+N)
3. Click en el menú (⋮) > "Import from File"
4. Selecciona `n8n-workflow/workflow.json`
5. Click en "Import"

### 5.2 Configurar Nodos del Workflow

#### 📥 Nodo 1: "Get Unprocessed Tickets" (HTTP Request)

Este nodo obtiene los tickets sin procesar desde Supabase.

**1. Authentication:**
- Type: `Generic Credential Type`
- Generic Auth Type: `Header Auth`
- Name: `apikey`
- Value: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (tu SUPABASE_SERVICE_ROLE_KEY)

**2. HTTP Request Settings:**
- **Method**: `GET`
- **URL**: `https://tu-proyecto.supabase.co/rest/v1/tickets`

**3. Query Parameters** (Add Parameter):
- `processed`: `eq.false` (filtrar solo no procesados)
- `select`: `*` (seleccionar todos los campos)
- `order`: `created_at.asc` (ordenar por más antiguos primero)

**4. Headers** (Add Header):
- `Authorization`: `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (mismo que apikey)
- `Content-Type`: `application/json`

**URL Final completa:**
```
https://tikcyizaoggobuqafptu.supabase.co/rest/v1/tickets?processed=eq.false&select=*&order=created_at.asc
```

**Respuesta esperada:**
```json
[
  {
    "id": "uuid-del-ticket",
    "description": "Mi conexión a internet no funciona",
    "processed": false,
    "created_at": "2026-01-22T...",
    ...
  }
]
```

---

#### 🤖 Nodo 2: "Call FastAPI Classifier" (HTTP Request)

Este nodo envía cada ticket a tu API de FastAPI para clasificarlo con IA.

**1. Authentication:**
- Type: `Generic Credential Type`
- Generic Auth Type: `Header Auth`
- Name: `X-API-Key`
- Value: `oMEuUaUY35EcRdLLPDHN5Db9vqtYfZXxJ_83OLficXI` (tu API_KEY del .env)

**2. HTTP Request Settings:**
- **Method**: `POST`
- **URL**: `http://host.docker.internal:8000/api/v1/process-ticket`
  - ⚠️ Si n8n está en Docker: usa `host.docker.internal:8000`
  - ⚠️ Si n8n está local (npm): usa `localhost:8000`

**3. Headers:**
- `Content-Type`: `application/json`

**4. Body (Send Body):**
- **Body Content Type**: `JSON`
- **Specify Body**: `Using JSON`

**JSON Body:**
```json
{
  "ticket_id": "{{ $json.id }}",
  "description": "{{ $json.description }}"
}
```

**Expresiones n8n:**
- `{{ $json.id }}`: Toma el ID del ticket del nodo anterior
- `{{ $json.description }}`: Toma la descripción del nodo anterior

**Respuesta esperada:**
```json
{
  "success": true,
  "ticket_id": "uuid-del-ticket",
  "classification": {
    "category": "Técnico",
    "sentiment": "Neutral",
    "confidence_score": null
  },
  "processing_time_ms": 23833,
  "message": "Ticket processed successfully"
}
```

---

#### 📧 Nodo 3: "Send Email Notification" (Opcional)

Puedes configurar notificaciones por email para tickets procesados.

**Opción A: Gmail (para testing)**

1. Crear credencial Gmail OAuth2 en n8n
2. Configurar nodo:
   - **To**: `tu-email@gmail.com`
   - **Subject**: `🎫 Ticket Procesado: {{ $node["Call FastAPI Classifier"].json.classification.category }}`
   - **Message Type**: `HTML`
   - **Message**:
   ```html
   <h2>Ticket Procesado</h2>
   <p><strong>ID:</strong> {{ $node["Call FastAPI Classifier"].json.ticket_id }}</p>
   <p><strong>Categoría:</strong> {{ $node["Call FastAPI Classifier"].json.classification.category }}</p>
   <p><strong>Sentimiento:</strong> {{ $node["Call FastAPI Classifier"].json.classification.sentiment }}</p>
   <p><strong>Tiempo:</strong> {{ $node["Call FastAPI Classifier"].json.processing_time_ms }}ms</p>
   ```

**Opción B: SMTP**

1. Crear credencial SMTP en n8n
2. Configurar servidor:
   - **Host**: `smtp.gmail.com` (o tu proveedor)
   - **Port**: `587`
   - **User**: `tu-email@ejemplo.com`
   - **Password**: App Password de Gmail
3. Configurar mensaje igual que Opción A

---

### 5.3 Configurar Trigger del Workflow

**Schedule Trigger:**
- **Trigger Interval**: `Every 60 seconds`
- **Description**: "Check for new unprocessed tickets every minute"

Esto ejecutará el workflow automáticamente cada 60 segundos para buscar tickets nuevos.

---

### 5.4 Probar el Workflow

**Test Manual:**
1. En n8n, click en "Execute Workflow" (botón ▶️)
2. Deberías ver:
   - ✅ Nodo 1: Lista de tickets sin procesar
   - ✅ Nodo 2: Respuesta de clasificación para cada ticket
   - ✅ Nodo 3: Confirmación de email enviado (si configurado)

**Test con Trigger:**
1. Click en "Active" (toggle arriba a la derecha)
2. Inserta un ticket nuevo en Supabase:
   ```sql
   INSERT INTO tickets (description, processed)
   VALUES ('Mi internet no funciona desde esta mañana', false);
   ```
3. Espera hasta 60 segundos
4. Ve a "Executions" en n8n para ver el resultado

⚠️ **Nota:** Si usas Docker, recuerda usar `host.docker.internal` en lugar de `localhost`.

### 5.5 Activar el Workflow

1. Click en el toggle "Inactive" → "Active" (arriba a la derecha)
2. El workflow se ejecutará cada 60 segundos automáticamente
3. Verifica que no hay errores en la primera ejecución

✅ **Si no hay errores en la ejecución, n8n está listo!**

**Monitoreo:**
- Ve a "Executions" para ver el historial de ejecuciones
- Cada ejecución mostrará cuántos tickets se procesaron
- Los errores aparecerán en rojo con detalles del problema

---

## 🧪 Paso 6: Testing Pre-Producción

Antes de desplegar, debes verificar que todo funciona correctamente.

### 6.1 Tests Manuales Esenciales

#### ✅ Test 1: Health Check Backend

```bash
# Desde cualquier terminal
curl -X GET http://localhost:8000/health | jq

# Esperado:
# {
#   "status": "healthy",
#   "database": "connected",
#   "llm_provider": "openai"  // o "huggingface"
# }
```

**✅ PASS si:** `status: "healthy"` y `database: "connected"`
**❌ FAIL si:** Error de conexión o `status: "unhealthy"`

**Nota:** `llm_provider` mostrará el proveedor que configuraste en `.env`

---

#### ✅ Test 2: Insertar Ticket en Supabase

```bash
# Insertar un ticket nuevo
curl -X POST "https://tu-proyecto.supabase.co/rest/v1/tickets" \
  -H "apikey: TU_ANON_KEY" \
  -H "Authorization: Bearer TU_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Mi internet está muy lento desde esta mañana. He reiniciado el router pero sigue igual.",
    "processed": false
  }' | jq
```

**✅ PASS si:** Retorna el ticket con `id` y `created_at`
**❌ FAIL si:** Error 401/403 (revisar API key) o 400 (revisar schema)

---

#### ✅ Test 3: Procesar Ticket con FastAPI

```bash
# Obtener el ID del ticket que insertaste (desde SQL Editor o curl)
TICKET_ID="uuid-del-ticket"

# Procesar
curl -X POST http://localhost:8000/api/v1/process-ticket \
  -H "Content-Type: application/json" \
  -d "{
    \"ticket_id\": \"$TICKET_ID\",
    \"description\": \"Mi internet está muy lento desde esta mañana.\"
  }" | jq
```

**Esperado:**
```json
{
  "success": true,
  "ticket_id": "uuid-del-ticket",
  "classification": {
    "category": "Técnico",
    "sentiment": "Negativo",
    "confidence_score": 0.95
  },
  "processing_time_ms": 1234
}
```

**✅ PASS si:** `success: true` y clasificación razonable
**❌ FAIL si:** Error 500 (revisar logs de FastAPI) o timeout

---

#### ✅ Test 4: Verificar Actualización en Supabase

```bash
# Query para ver si se actualizó
curl "https://tu-proyecto.supabase.co/rest/v1/tickets?id=eq.$TICKET_ID&select=*" \
  -H "apikey: TU_ANON_KEY" \
  -H "Authorization: Bearer TU_ANON_KEY" | jq
```

**✅ PASS si:**
- `processed: true`
- `category: "Técnico"`
- `sentiment: "Negativo"`
- `processed_at` tiene timestamp
- `processing_time_ms` > 0

---

#### ✅ Test 5: Real-time Updates en Frontend

1. Abre el dashboard en http://localhost:5173
2. Abre DevTools (F12) > Console
3. Inserta un ticket nuevo desde SQL Editor:
   ```sql
   INSERT INTO tickets (description, processed, category, sentiment)
   VALUES ('Test real-time', true, 'Técnico', 'Positivo');
   ```
4. Mira el dashboard

**✅ PASS si:**
- Ves el log "New ticket inserted:" en Console
- El ticket aparece en el dashboard SIN refrescar
- La animación "slide-in" se ejecuta
- El badge "NEW" aparece por 3 segundos

**❌ FAIL si:** Necesitas refrescar para ver el ticket

---

#### ✅ Test 6: Connection Status Tracking

1. En el dashboard, verifica que el indicador muestra "Live updates active" 🟢
2. Detén Supabase (o desconecta internet por 5 segundos)
3. Verifica que cambia a "Connection error" 🔴
4. Reconecta
5. Verifica que vuelve a "Live updates active" 🟢

**✅ PASS si:** El indicador refleja el estado real
**❌ FAIL si:** Siempre muestra "connected" aunque no haya conexión

---

#### ✅ Test 7: Error Handling - Ticket Inválido

```bash
# Intentar procesar ticket con descripción demasiado corta
curl -X POST http://localhost:8000/api/v1/process-ticket \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "00000000-0000-0000-0000-000000000000",
    "description": "Corto"
  }' | jq
```

**✅ PASS si:**
- Retorna error 404 o 400 con mensaje claro
- Logs en FastAPI muestran el error estructurado
- No crashea el servidor

**❌ FAIL si:** Error 500 o servidor crashea

---

#### ✅ Test 8: Idempotency Check

```bash
# Procesar el mismo ticket DOS VECES
TICKET_ID="uuid-de-ticket-ya-procesado"

# Primera llamada
curl -X POST http://localhost:8000/api/v1/process-ticket \
  -H "Content-Type: application/json" \
  -d "{\"ticket_id\": \"$TICKET_ID\", \"description\": \"Test\"}" | jq

# Segunda llamada (debería retornar cached)
curl -X POST http://localhost:8000/api/v1/process-ticket \
  -H "Content-Type: application/json" \
  -d "{\"ticket_id\": \"$TICKET_ID\", \"description\": \"Test\"}" | jq
```

**✅ PASS si:** Segunda llamada retorna el mismo resultado sin volver a llamar al LLM
**❌ FAIL si:** Procesa de nuevo (desperdicio de API calls de OpenAI)

---

#### ✅ Test 9: LLM Robustness - Edge Cases

```bash
# Test con typos
curl -X POST http://localhost:8000/api/v1/process-ticket \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "new-uuid-1",
    "description": "Mi faktura tiene un herror en el monto cobrado"
  }' | jq

# Test con emojis
curl -X POST http://localhost:8000/api/v1/process-ticket \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "new-uuid-2",
    "description": "😡 El servicio está fatal, no funciona nada!!!"
  }' | jq

# Test con sarcasmo
curl -X POST http://localhost:8000/api/v1/process-ticket \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "new-uuid-3",
    "description": "Genial, otra vez se cayó el sistema. Esto es lo máximo 👏"
  }' | jq
```

**✅ PASS si:**
- Primer test: Clasifica como "Facturación" (detecta la intención)
- Segundo test: Sentiment "Negativo" (detecta emoji de enojo)
- Tercer test: Sentiment "Negativo" (detecta sarcasmo)

**❌ FAIL si:** Clasifica incorrectamente o falla el parsing

---

#### ✅ Test 10: Performance - Concurrencia

```bash
# Instalar herramienta de benchmarking
pip install httpx

# Crear script de test
cat > test_concurrent.py << 'EOF'
import asyncio
import httpx
import time

async def process_ticket(client, i):
    response = await client.post(
        "http://localhost:8000/api/v1/process-ticket",
        json={
            "ticket_id": f"test-{i}",
            "description": f"Test ticket número {i} para validar concurrencia"
        }
    )
    return response.status_code

async def main():
    start = time.time()
    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [process_ticket(client, i) for i in range(10)]
        results = await asyncio.gather(*tasks)
    elapsed = time.time() - start

    success = sum(1 for r in results if r == 200)
    print(f"✅ {success}/10 requests exitosos en {elapsed:.2f}s")
    print(f"Throughput: {10/elapsed:.2f} req/s")

asyncio.run(main())
EOF

# Ejecutar
python test_concurrent.py
```

**✅ PASS si:**
- 10/10 requests exitosos
- Tiempo total < 15 segundos
- Sin errores en logs de FastAPI

**❌ FAIL si:** Timeout o errores de conexión

---

### 6.2 Checklist de Funcionalidad End-to-End

Ejecuta este flujo completo:

```
1. [ ] Insertar ticket nuevo en Supabase (processed=false)
2. [ ] Ticket aparece en dashboard instantáneamente
3. [ ] n8n detecta el ticket (esperar hasta 60s)
4. [ ] n8n llama a FastAPI automáticamente
5. [ ] FastAPI procesa y actualiza Supabase
6. [ ] Dashboard se actualiza con categoría/sentiment
7. [ ] Si sentiment="Negativo", n8n simula email
8. [ ] Ver log de email en ejecución de n8n
```

**✅ PASS si:** Todo el flujo se ejecuta automáticamente
**❌ FAIL si:** Algún paso requiere intervención manual

---

### 6.3 Tests de Regresión Visual

| Componente | Qué Verificar | ✅/❌ |
|------------|---------------|-------|
| **Header** | Muestra estadísticas correctas (Total, Procesados, Pendientes) | |
| **Tickets** | Grid responsivo (1 col móvil, 3 cols desktop) | |
| **Badges** | Colores correctos (Técnico=azul, Facturación=verde, Comercial=morado) | |
| **Sentiment** | Iconos correctos (Positivo=😊, Neutral=😐, Negativo=😞) | |
| **Connection** | Indicador visible y actualizado | |
| **Empty State** | Se muestra cuando no hay tickets | |
| **Error State** | Se muestra con botón "Try again" cuando falla carga | |
| **Loading** | Spinner visible durante carga inicial | |
| **Animaciones** | Slide-in suave para nuevos tickets | |
| **Responsive** | Funciona en móvil (viewport 375px) | |

---

### 6.4 Tests de Seguridad Básicos

```bash
# Test 1: Verificar que Frontend usa ANON key (no service role)
curl "https://tu-proyecto.supabase.co/rest/v1/tickets" \
  -H "apikey: TU_SERVICE_ROLE_KEY" \
  -H "Authorization: Bearer TU_SERVICE_ROLE_KEY"

# ✅ PASS: Debería funcionar (tienes service role)

# Test 2: Intentar DELETE con ANON key (debería fallar por RLS)
curl -X DELETE "https://tu-proyecto.supabase.co/rest/v1/tickets?id=eq.uuid" \
  -H "apikey: TU_ANON_KEY" \
  -H "Authorization: Bearer TU_ANON_KEY"

# ✅ PASS: Debería retornar 403 Forbidden (RLS bloquea DELETE)
# ❌ FAIL: Si permite DELETE con anon key, RLS está mal configurado

# Test 3: Verificar que .env no está en git
git ls-files | grep ".env"

# ✅ PASS: No debería retornar nada
# ❌ FAIL: Si retorna .env, lo estás commiteando (PELIGRO)

# Test 4: Verificar CORS en backend
curl -X OPTIONS http://localhost:8000/api/v1/process-ticket \
  -H "Origin: http://malicious-site.com" \
  -v

# ✅ PASS: Debería rechazar origin no autorizado
# ❌ FAIL: Si permite any origin en producción
```

---

### 6.5 Checklist de Logs y Observabilidad

```bash
# Test 1: Verificar logs estructurados en FastAPI
# Procesar un ticket y revisar logs

# ✅ PASS si ves logs como:
# {"level": "info", "request_id": "abc123", "ticket_id": "uuid", "processing_time_ms": 1234}

# Test 2: Verificar health check incluye timestamp
curl http://localhost:8000/health | jq .timestamp

# ✅ PASS si retorna ISO 8601 timestamp

# Test 3: Verificar que errores se loggean con traceback
# Forzar un error (enviar ticket_id inválido)

# ✅ PASS si logs incluyen full stack trace
```

---

## ✅ Checklist Final Pre-Producción

Marca cada item antes de desplegar:

### Backend (FastAPI)

- [ ] Health check retorna "healthy"
- [ ] Conexión a Supabase exitosa
- [ ] API Key de LLM válida (OpenAI o HuggingFace token)
- [ ] Endpoint `/process-ticket` responde < 5s
- [ ] Retry logic funciona (probado desconectando Supabase temporalmente)
- [ ] Fallback a "Técnico + Neutral" funciona cuando LLM falla
- [ ] Logs estructurados con request IDs
- [ ] Manejo de errores no crashea el servidor
- [ ] Dockerfile builds sin errores
- [ ] Variables de entorno NO están hardcoded en código
- [ ] `.env` está en `.gitignore`

### Frontend (React)

- [ ] Build de producción exitoso (`npm run build`)
- [ ] No hay errores de TypeScript (`npm run type-check`)
- [ ] Linter pasa sin warnings (`npm run lint`)
- [ ] Conexión a Supabase exitosa
- [ ] Realtime updates funcionan
- [ ] Connection status tracking funcional
- [ ] Responsive design en móvil/tablet/desktop
- [ ] Empty state se muestra correctamente
- [ ] Error state permite retry
- [ ] Loading states visibles
- [ ] Variables de entorno usan VITE_ prefix
- [ ] `.env` está en `.gitignore`

### n8n Workflow

- [ ] Workflow importa sin errores
- [ ] Schedule trigger configurado (60s)
- [ ] URL de Supabase correcta
- [ ] URL de FastAPI correcta
- [ ] Headers con API keys correctos
- [ ] IF node detecta sentiment correctamente
- [ ] Email simulation funciona
- [ ] Manejo de errores configurado (retry 3x)

### Supabase

- [ ] Tabla `tickets` creada con schema correcto
- [ ] ENUM types creados (category_enum, sentiment_enum)
- [ ] Indexes creados (5 indexes estratégicos)
- [ ] RLS policies habilitadas
- [ ] Realtime habilitado en la tabla
- [ ] Sample data visible (5 tickets)
- [ ] Triggers funcionan (updated_at se actualiza)
- [ ] Backup configurado (Supabase lo hace automáticamente)

### Seguridad

- [ ] Service role key SOLO en backend
- [ ] Anon key SOLO en frontend
- [ ] RLS previene DELETE con anon key
- [ ] `.env` files NO están en git
- [ ] API keys NO están hardcoded
- [ ] CORS configurado correctamente
- [ ] Rate limiting considerado (o documentado para futuro)

### Observabilidad

- [ ] Health checks configurados
- [ ] Logs estructurados implementados
- [ ] Request IDs en todos los logs
- [ ] Errores incluyen traceback
- [ ] Processing time medido
- [ ] Connection status visible en UI

---

## 🚀 Siguiente Paso: Deployment

Una vez que todos los tests pasen, estás listo para desplegar:

1. **Backend a Railway.app**
   - Guía: `docs/deployment-guide.md` (crear después)
2. **Frontend a Vercel**
   - Guía: `docs/deployment-guide.md`
3. **n8n a n8n Cloud**
   - Guía: `docs/deployment-guide.md`
4. **Actualizar URLs en README.md**

---

## 🆘 Troubleshooting Común

### ❌ Error: "Connection to Supabase failed"

**Causa:** URL o API key incorrectos

**Solución:**
```bash
# Verificar credentials
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_ROLE_KEY | cut -c1-20

# Probar conexión manualmente
curl "$SUPABASE_URL/rest/v1/tickets?select=count" \
  -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY"
```

---

### ❌ Error: "OpenAI API key invalid"

**Causa:** API key expirado o sin créditos

**Solución:**
1. Ve a https://platform.openai.com/api-keys
2. Verifica que la key existe y está activa
3. Revisa tu billing: https://platform.openai.com/account/billing

---

### ❌ Error: "Real-time updates not working"

**Causa:** Realtime no habilitado en Supabase

**Solución:**
```sql
-- Verificar que Realtime está habilitado
SELECT * FROM pg_publication WHERE pubname = 'supabase_realtime';

-- Si no existe, habilitar:
ALTER PUBLICATION supabase_realtime ADD TABLE tickets;
```

---

### ❌ Error: "Tickets not appearing in dashboard"

**Causa:** Filtro `processed=true` en query

**Solución:**
```typescript
// Revisar en useTickets.ts
const { data } = await supabase
  .from('tickets')
  .select('*')
  .eq('processed', true)  // <- Asegúrate que tickets tienen processed=true
  .order('created_at', { ascending: false })
```

---

### ❌ Error: "CORS error in browser"

**Causa:** CORS no configurado en FastAPI

**Solución:**
```python
# En app/main.py, verificar:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # <- Agregar tu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### ❌ Error: "LLM timeout"

**Causa:** API del LLM lenta o sobrecargada

**Solución:**
```python
# En app/services/classifier.py, ajustar timeout:
self.llm = ChatOpenAI(
    model=self.model_name,
    temperature=self.temperature,
    timeout=15.0,  # <- Aumentar si es necesario (OpenAI/HuggingFace)
    max_retries=3,
)
```

**Nota para HuggingFace:** Si usas HuggingFace y tienes timeouts frecuentes, considera:
- Cambiar a un modelo más pequeño (ej: `google/flan-t5-large`)
- Usar HuggingFace Inference Endpoints (pago pero más rápido)
- Esperar y reintentar (la inferencia gratuita puede tener cola)

---

### ❌ Error: "Invalid HuggingFace token"

**Causa:** Token de HuggingFace inválido o sin permisos

**Solución:**
1. Ve a https://huggingface.co/settings/tokens
2. Verifica que el token existe y está activo
3. Asegúrate de tener role "read" mínimo
4. Regenera el token si es necesario

```bash
# Probar token manualmente
curl "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1" \
  -H "Authorization: Bearer hf_TU_TOKEN"

# Debería retornar información del modelo, no error 401
```

---

## 📊 Comparación: OpenAI vs HuggingFace

| Característica | OpenAI (GPT-3.5) | HuggingFace (Mixtral-8x7B) |
|----------------|------------------|----------------------------|
| **Costo** | $0.0002/ticket (~$0.18 por 1000) | **GRATIS** |
| **Precisión** | 95-98% | 85-92% |
| **Velocidad** | 1-2 segundos | 2-4 segundos |
| **Límites** | Necesita tarjeta ($5 gratis inicial) | ~1000 req/día (gratis) |
| **Setup** | Requiere API key de pago | Solo email (sin tarjeta) |
| **Ideal para** | Demo/presentación profesional | Desarrollo y pruebas |

**Ejemplos de clasificación:**

```
Input: "Mi internet está muy lento desde esta mañana"

OpenAI GPT-3.5:
  Category: Técnico ✅
  Sentiment: Negativo ✅
  Confidence: 0.95

HuggingFace Mixtral:
  Category: Técnico ✅
  Sentiment: Negativo ✅
  Confidence: 0.88
```

```
Input: "¡Genial! Otra vez falla el sistema 👏" (sarcasmo)

OpenAI GPT-3.5:
  Category: Técnico ✅
  Sentiment: Negativo ✅ (detecta sarcasmo)

HuggingFace Mixtral:
  Category: Técnico ✅
  Sentiment: Neutral ⚠️ (puede no detectar sarcasmo)
```

**Recomendación:**
- **Para esta prueba técnica:** Usa OpenAI si tienes $0.50 disponible (mejor impresión)
- **Para aprender/practicar:** Usa HuggingFace (sin costo, funciona bien)
- **Ambos están 100% implementados** en el proyecto, solo cambia el `.env`

---

## 📚 Recursos Adicionales

### Servicios Core
- **Documentación Supabase:** https://supabase.com/docs
- **Documentación FastAPI:** https://fastapi.tiangolo.com
- **Documentación LangChain:** https://python.langchain.com
- **Documentación n8n:** https://docs.n8n.io
- **Documentación React:** https://react.dev

### LLM Providers
- **OpenAI Platform:** https://platform.openai.com/docs
- **OpenAI Pricing:** https://openai.com/api/pricing/
- **HuggingFace Docs:** https://huggingface.co/docs
- **HuggingFace Inference API:** https://huggingface.co/docs/api-inference
- **HuggingFace Models:** https://huggingface.co/models

---

**¿Listo para desplegar?** Continúa con `docs/deployment-guide.md` (próximo documento).
