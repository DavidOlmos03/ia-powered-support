# React Frontend Deployment - Vercel

**Última actualización:** 2026-01-23

Esta guía te llevará paso a paso para desplegar tu frontend de React en Vercel.

---

## 📋 Pre-requisitos

Antes de comenzar, asegúrate de tener:

- ✅ Cuenta en Vercel (https://vercel.com)
- ✅ Frontend funcionando localmente (`npm run dev`)
- ✅ Backend desplegado en Railway (URL disponible)
- ✅ Cuenta en Supabase con la base de datos configurada
- ✅ Git instalado y repositorio inicializado
- ✅ Node.js 18+ instalado

---

## 🚀 Paso 1: Preparar el Proyecto

### 1.1 Verificar Variables de Entorno

Crea o verifica `frontend/.env.example` para documentar las variables necesarias:

```bash
# frontend/.env.example
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_API_URL=https://your-backend.up.railway.app
```

### 1.2 Verificar package.json

Asegúrate que tus scripts de build estén correctos:

```json
{
  "name": "frontend",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "@supabase/supabase-js": "^2.39.0"
  }
}
```

### 1.3 Verificar vite.config.ts

Tu configuración de Vite debe estar optimizada para producción:

```typescript
// frontend/vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'esbuild',
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'supabase-vendor': ['@supabase/supabase-js'],
        },
      },
    },
  },
})
```

### 1.4 Crear vercel.json (Opcional)

Crea `frontend/vercel.json` para configuración avanzada:

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "vite",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ],
  "headers": [
    {
      "source": "/assets/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    }
  ]
}
```

---

## 🔐 Paso 2: Preparar Variables de Entorno

### 2.1 Crear lista de variables

En un archivo temporal (NO lo comitees), prepara tus variables:

```bash
# Variables para Vercel
VITE_SUPABASE_URL=https://tikcyizaoggobuqafptu.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
VITE_API_URL=https://your-backend.up.railway.app
```

**⚠️ IMPORTANTE:**
- Usa el `SUPABASE_ANON_KEY` (NO el service role key)
- La URL del backend debe ser tu Railway deployment
- Todas las variables deben empezar con `VITE_` para ser expuestas al cliente

### 2.2 Obtener URL del Backend

Tu backend en Railway debe estar desplegado primero. La URL será algo como:
```
https://ia-powered-support-production.up.railway.app
```

---

## 🚂 Paso 3: Desplegar en Vercel

### 3.1 Crear Proyecto en Vercel (UI)

1. Ve a https://vercel.com/new
2. Click en **"Import Git Repository"**
3. Autoriza Vercel para acceder a GitHub
4. Selecciona tu repositorio `ia-powered-support`
5. Configure los siguientes ajustes:

**Project Settings:**
- **Framework Preset**: Vite
- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Install Command**: `npm install`

**O si prefieres Vercel CLI:**

```bash
# Instalar Vercel CLI
npm install -g vercel

# Login
vercel login

# Desplegar desde el directorio frontend
cd frontend
vercel

# Seguir el wizard:
# - Set up and deploy "~/projects/ia-powered-support/frontend"? [Y/n] y
# - Which scope? → Tu cuenta
# - Link to existing project? [y/N] n
# - What's your project's name? → ia-powered-support-frontend
# - In which directory is your code located? → ./
# - Want to modify settings? [y/N] n
```

### 3.2 Configurar Variables de Entorno

En Vercel UI:
1. Ve a tu proyecto → **Settings** → **Environment Variables**
2. Agrega las siguientes variables para **Production**, **Preview**, y **Development**:

```
VITE_SUPABASE_URL = https://tikcyizaoggobuqafptu.supabase.co
VITE_SUPABASE_ANON_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
VITE_API_URL = https://your-backend.up.railway.app
```

**Environment Options:**
- ✅ **Production**: Variables para producción (rama `main`)
- ✅ **Preview**: Variables para preview deployments (PRs)
- ✅ **Development**: Variables para `vercel dev` local

**O con Vercel CLI:**

```bash
# Agregar variables de entorno
vercel env add VITE_SUPABASE_URL production
# Pegar el valor cuando te lo pida

vercel env add VITE_SUPABASE_ANON_KEY production
vercel env add VITE_API_URL production

# También agregar para preview y development
vercel env add VITE_SUPABASE_URL preview
vercel env add VITE_SUPABASE_ANON_KEY preview
vercel env add VITE_API_URL preview
```

### 3.3 Configurar Dominio

Vercel asigna automáticamente un dominio:
- **Production**: `your-project.vercel.app`
- **Preview**: `your-project-git-branch.vercel.app`

**Para Custom Domain:**
1. Ve a **Settings** → **Domains**
2. Click en **"Add Domain"**
3. Ingresa tu dominio (ej. `support.tuempresa.com`)
4. Sigue las instrucciones para configurar DNS

---

## ✅ Paso 4: Verificar Deployment

### 4.1 Ver Logs de Build

En Vercel UI:
- Ve a **Deployments** → Click en el último deployment
- Revisa **"Build Logs"** para ver el proceso de compilación

O con CLI:
```bash
vercel logs <deployment-url>
```

### 4.2 Verificar Build Exitoso

El build debe completarse sin errores. Busca:
```bash
✓ built in XXXms
✓ Build Completed in <path> [XX s]
```

### 4.3 Probar la Aplicación

Visita tu URL de Vercel:
```
https://your-project.vercel.app
```

**Checklist de verificación:**
- ✅ La página carga sin errores 404
- ✅ Los estilos de Tailwind se aplican correctamente
- ✅ La conexión a Supabase funciona (tickets se muestran)
- ✅ Las actualizaciones en tiempo real funcionan
- ✅ No hay errores en la consola del navegador

### 4.4 Verificar Conexión con Backend

Abre DevTools (F12) → Console y verifica:

```javascript
// Debe mostrar tu URL de Railway
console.log(import.meta.env.VITE_API_URL)
// https://your-backend.up.railway.app
```

### 4.5 Verificar Variables de Entorno

En tu deployment de Vercel, abre la consola del navegador:

```javascript
// Verificar que las variables están disponibles
console.log({
  supabaseUrl: import.meta.env.VITE_SUPABASE_URL,
  apiUrl: import.meta.env.VITE_API_URL,
  hasAnonKey: !!import.meta.env.VITE_SUPABASE_ANON_KEY
})
```

**Resultado esperado:**
```javascript
{
  supabaseUrl: "https://tikcyizaoggobuqafptu.supabase.co",
  apiUrl: "https://your-backend.up.railway.app",
  hasAnonKey: true
}
```

---

## 🔧 Paso 5: Configuración Avanzada (Opcional)

### 5.1 Configurar CORS en Backend

Tu backend de Railway necesita permitir el dominio de Vercel. En tu `.env` de Railway:

```bash
# Agregar el dominio de Vercel a CORS_ORIGINS
CORS_ORIGINS=["https://your-project.vercel.app", "http://localhost:3000"]
```

O en `python-api/app/config.py`:

```python
cors_origins: list[str] = Field(
    default=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://your-project.vercel.app"
    ],
    description="Allowed CORS origins",
)
```

### 5.2 Configurar Preview Deployments

Para cada PR, Vercel crea un preview deployment automático:

**Settings** → **Git**:
- ✅ **Ignored Build Step**: (Déjalo vacío para build siempre)
- ✅ **Production Branch**: `main`
- ✅ **Preview Branches**: `All branches`

### 5.3 Configurar Build Cache

Vercel cachea automáticamente node_modules, pero puedes optimizar:

```json
// vercel.json
{
  "github": {
    "silent": true
  },
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm ci"
}
```

**Usar `npm ci` en vez de `npm install`**:
- Más rápido (usa package-lock.json)
- Más confiable (instala exactas versiones)

### 5.4 Configurar Performance Hints

En `vite.config.ts`:

```typescript
export default defineConfig({
  build: {
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'router': ['react-router-dom'],
          'supabase': ['@supabase/supabase-js'],
        },
      },
    },
  },
})
```

### 5.5 Configurar Security Headers

En `vercel.json`:

```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        },
        {
          "key": "Referrer-Policy",
          "value": "strict-origin-when-cross-origin"
        }
      ]
    }
  ]
}
```

---

## 🐛 Troubleshooting

### Error: "Failed to load module"

**Causa:** Rutas de importación incorrectas o aliases no resueltos

**Solución:**
```bash
# Verificar que tsconfig.json tiene los paths correctos
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}

# Verificar vite.config.ts
resolve: {
  alias: {
    '@': path.resolve(__dirname, './src'),
  },
}
```

---

### Error: "Environment variables are undefined"

**Causa:** Variables no empiezan con `VITE_` o no están configuradas en Vercel

**Solución:**
```bash
# Verificar nombres de variables (deben empezar con VITE_)
# En Vercel → Settings → Environment Variables

# Re-desplegar después de agregar variables
vercel --prod
```

**⚠️ IMPORTANTE:** Cambios en variables de entorno requieren re-deployment

---

### Error: "404 on page refresh"

**Causa:** SPA routing no configurado en Vercel

**Solución:**
```json
// vercel.json
{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

Commit y push el cambio, Vercel re-desplegará automáticamente.

---

### Error: "CORS policy blocked"

**Causa:** Backend no permite el dominio de Vercel

**Solución:**
```bash
# En Railway backend, agregar el dominio de Vercel a CORS_ORIGINS
railway variables set CORS_ORIGINS='["https://your-project.vercel.app"]'

# O actualizar app/config.py y hacer push
```

---

### Error: "Build fails with TypeScript errors"

**Causa:** Errores de TypeScript que no aparecen en desarrollo

**Solución:**
```bash
# Probar build localmente primero
cd frontend
npm run build

# Si hay errores, corregirlos antes de desplegar
# O temporalmente, en vite.config.ts:
export default defineConfig({
  build: {
    rollupOptions: {
      onwarn(warning, warn) {
        // Ignorar warnings específicos
        if (warning.code === 'UNUSED_EXTERNAL_IMPORT') return
        warn(warning)
      }
    }
  }
})
```

---

### Error: "Supabase realtime not working"

**Causa:** WebSocket connection bloqueada o mal configurada

**Solución:**
```typescript
// Verificar configuración de Supabase client
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY,
  {
    realtime: {
      params: {
        eventsPerSecond: 10
      }
    }
  }
)
```

**Verificar en Supabase Dashboard:**
- Database → Replication → Supabase Realtime debe estar habilitado
- Table settings → Enable Realtime para la tabla `tickets`

---

### Error: "Build exceeds size limit"

**Causa:** Bundle demasiado grande

**Solución:**
```bash
# Analizar tamaño del bundle
npm install -D vite-bundle-visualizer

# En vite.config.ts
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig({
  plugins: [
    react(),
    visualizer({ open: true })
  ]
})

# Optimizar imports
// ❌ Mal: importar toda la librería
import _ from 'lodash'

// ✅ Bien: importar solo lo necesario
import debounce from 'lodash/debounce'
```

---

## 📊 Monitoreo Post-Deployment

### Métricas de Vercel Analytics

Vercel incluye Analytics automáticamente:
- **Core Web Vitals**: LCP, FID, CLS
- **Deployment Frequency**: Frecuencia de deploys
- **Build Time**: Tiempo de compilación

**Para activar:**
1. Ve a tu proyecto → **Analytics**
2. Enable **Vercel Analytics** (gratis)

### Lighthouse Score

Vercel ejecuta Lighthouse automáticamente:
- **Performance**: Debe ser > 90
- **Accessibility**: Debe ser > 90
- **Best Practices**: Debe ser > 90
- **SEO**: Debe ser > 90

### Real User Monitoring

Agregar Vercel Speed Insights:

```bash
npm install @vercel/speed-insights
```

```typescript
// src/main.tsx
import { SpeedInsights } from '@vercel/speed-insights/react'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
    <SpeedInsights />
  </React.StrictMode>
)
```

---

## 🔄 Actualizaciones y CI/CD

### Deployment Automático

Vercel se actualiza automáticamente con cada push:

```bash
git add .
git commit -m "feat: add real-time notifications"
git push origin main

# Vercel detecta el push y despliega automáticamente
```

**Vercel comentará en tu commit/PR con:**
- ✅ Preview URL
- ⚡ Build status
- 📊 Performance metrics

### Deployment Manual

Si prefieres control manual:

```bash
# Deploy a producción
vercel --prod

# Deploy preview
vercel
```

### Rollback

Si algo sale mal:

1. Vercel → **Deployments**
2. Click en deployment anterior que funcionaba
3. Click en **"⋯"** → **"Promote to Production"**

O con CLI:
```bash
# Listar deployments
vercel ls

# Promover deployment anterior
vercel promote <deployment-url>
```

### Branch Previews

Cada rama automáticamente obtiene su preview:
- `main` → `your-project.vercel.app` (production)
- `develop` → `your-project-git-develop.vercel.app` (preview)
- `feature-x` → `your-project-git-feature-x.vercel.app` (preview)

---

## 💰 Costos Estimados

### Vercel Hobby (Free)
- ✅ Deployments ilimitados
- ✅ Preview deployments
- ✅ 100 GB bandwidth/mes
- ✅ Custom domains
- ✅ Automatic HTTPS
- ⚠️ Sin team collaboration
- ⚠️ Sin password protection

**Suficiente para:** Proyectos personales, MVPs, demos

### Vercel Pro ($20/mes)
- ✅ Todo lo de Hobby +
- ✅ 1 TB bandwidth/mes
- ✅ Team collaboration
- ✅ Password protection
- ✅ Analytics avanzado
- ✅ Prioridad en builds

**Suficiente para:** Producción con múltiples usuarios, equipos

---

## ✅ Checklist Final

Marca cada item antes de considerar el deployment completo:

- [ ] Build exitoso en Vercel
- [ ] Frontend accesible en URL de Vercel
- [ ] Variables de entorno configuradas
- [ ] Conexión a Supabase funcionando
- [ ] Real-time updates funcionando
- [ ] Tickets se muestran correctamente
- [ ] Conexión a backend de Railway funcionando
- [ ] No hay errores en consola del navegador
- [ ] CORS configurado en backend
- [ ] Lighthouse score > 90
- [ ] Custom domain configurado (opcional)
- [ ] Vercel Analytics habilitado
- [ ] Team members agregados (opcional)
- [ ] URL documentada para compartir

---

## 🔗 Integración Frontend ↔ Backend

### Actualizar CORS en Backend (Railway)

En tu backend de Railway, asegúrate de agregar el dominio de Vercel:

```bash
# Railway → Variables
CORS_ORIGINS=["https://your-project.vercel.app", "http://localhost:3000", "http://localhost:5173"]
```

### Verificar Integración Completa

```bash
# 1. Backend (Railway) responde
curl https://your-backend.up.railway.app/health

# 2. Frontend (Vercel) carga
curl -I https://your-project.vercel.app

# 3. Frontend puede llamar al Backend (desde DevTools)
fetch('https://your-backend.up.railway.app/health')
  .then(r => r.json())
  .then(console.log)
```

---

## 📚 Recursos Adicionales

- **Vercel Docs**: https://vercel.com/docs
- **Vercel CLI**: https://vercel.com/docs/cli
- **Vite Deployment**: https://vitejs.dev/guide/static-deploy.html#vercel
- **React Deployment**: https://react.dev/learn/start-a-new-react-project#deploying-to-production
- **Vercel Status**: https://www.vercel-status.com/
- **Vercel Discord**: https://vercel.com/discord

---

## 🎉 ¡Listo!

Tu frontend está desplegado en Vercel y conectado a tu backend en Railway.

**URL de tu Frontend:** `https://your-project.vercel.app`

**Stack completo desplegado:**
- ✅ Backend FastAPI en Railway
- ✅ Frontend React en Vercel
- ✅ Database en Supabase
- ✅ LLM local con Ollama (o cloud con OpenAI)
- ✅ Workflow automation con n8n

---

*Última actualización: 2026-01-23*
