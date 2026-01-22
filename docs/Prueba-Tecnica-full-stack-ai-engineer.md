# Contexto del Desafiío

En VIVETORI buscamos ingenieros que dominen tanto el desarrollo
tradicional como las nuevas fronteras de la Inteligencia Artificial. Tu
objetivo es construir un **\"AI-Powered Support Co-Pilot\"**: un sistema
capaz de recibir tickets de soporte, procesarlos mediante agentes de IA
para categorizarlos y analizar su sentimiento, y visualizarlos en tiempo
real en un dashboard.

# Requerimientos Técnicos

## Base de Datos (Supabase)

1.  Configura una tabla tickets en Supabase con los siguientes campos:

    - id (UUID, Primary Key)

    - created_at (Timestamp)

    - description (Text - El contenido del ticket)

    - category (Text/Enum - Ej: Técnico, Facturación, Comercial)

    - sentiment (Text - Ej: Positivo, Neutral, Negativo)

    - processed (Boolean - Default: false)

2.  **Entregable:** Un archivo setup.sql con el esquema de la tabla y
    cualquier política RLS

necesaria.

## Microservicio de IA (Python + FastAPI)

1.  Crea una API en Python utilizando **FastAPI** y **LangChain**.

2.  Implementa un endpoint POST /process-ticket que:

    - Reciba el texto de un ticket.

    - Utilice un modelo de lenguaje (LLM via LangChain/Hugging Face)
      para extraer la

> categoría y el sentimiento en formato JSON estructurado.

- Actualice la fila correspondiente en Supabase marcándola como
  processed: true.

3.  **Despliegue:** Debes desplegar este servicio en una plataforma
    gratuita como

### Render.com, Vercel o Railway.app.

4.  **Entregable:** La URL pública de la API y el código fuente.

## Automatización Low-Code (n8n)

1.  Crea un flujo en **n8n** que:

    - Se active mediante un **Webhook** o un trigger de \"Nueva Fila\"
      en Supabase.

    - Consuma tu Microservicio de Python para procesar el ticket.

    - Si el sentimiento detectado es \"Negativo\", el flujo debe
      disparar una notificación

> simulada (envío de un email).

- (Plus) puedes agregar elementos adicionales a tu flujo que agreguen
  valor al proyecto.

2.  **Entregable:** El archivo .json del flujo exportado.

## Dashboard Frontend (React + TypeScript)

1.  Desarrolla una interfaz simple con **React 18**, **TypeScript** y
    **Vite**.

2.  Requerimientos visuales:

    - Usar **Tailwind CSS** para el diseño.

    - Mostrar la lista de tickets consumiendo directamente de Supabase.

    - Implementar **Realtime** (usando los canales de Supabase) para que
      los tickets

> aparezcan y se actualicen sin refrescar la página.

3.  **Entregable:** La URL de la web desplegada (Vercel/Netlify).

# Formato de Entrega

Debes enviar un repositorio de GitHub organizado de la siguiente manera:

- /supabase: Archivo setup.sql.

- /python-api: Código de la API de FastAPI, requirements.txt y
  Dockerfile (si aplica).

- /n8n-workflow: Archivo .json del flujo.

- /frontend: Código fuente del dashboard.

### En el README del repositorio debe incluirse obligatoriamente:

1.  **URL del Dashboard** activo.

2.  **URL de la API de Python** activa.

3.  Breve explicación de la estrategia de **Prompt Engineering**
    utilizada para la clasificación.

# Criterios de Evaluación

- **Funcionalidad End-to-End:** ¿El sistema realmente procesa un ticket
  desde que entra hasta que se visualiza?

- **Calidad del Microservicio:** Manejo de errores en Python, uso de
  tipos y eficiencia del prompt.

- **Dominio de Ecosistema:** Integración correcta entre Supabase, n8n y
  el frontend.

- **DevOps Básico:** Capacidad de desplegar servicios funcionales en la
  nube.
