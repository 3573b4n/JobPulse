# 🤖 JobPulse — Búsqueda de Empleo Automatizada

**[🇪🇸 Español](#-español) · [🇬🇧 English](#-english)**

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![Telegram Bot](https://img.shields.io/badge/Telegram-Bot_API-26A5E4?style=flat&logo=telegram&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Cron_30min-2088FF?style=flat&logo=githubactions&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 🇪🇸 Español

Agente inteligente que rastrea **plataformas de empleo españolas cada 30 minutos** y te
notifica por Telegram cuando aparece una oferta que cumple tus criterios. Corre 24/7 en
GitHub Actions (nivel gratuito): no necesita tu PC encendido.

### 🎯 ¿Qué hace?

- **Rastreo automático** de ofertas cada 30 minutos (cron configurable).
- **Notificaciones enriquecidas en Telegram** con título, ubicación y enlace directo.
- **Deduplicación persistente**: guarda los IDs de ofertas ya vistas y nunca repite.
- **Primero en aplicar**: en un mercado dinámico, recibir la oferta en minutos marca la diferencia.

### 🧩 Dos módulos de scraping

| Módulo | Plataformas | Workflow |
|---|---|---|
| `job_bot.py` | LinkedIn · InfoJobs · Indeed · TecnoEmpleo · Glassdoor · Jooble | `.github/workflows/jobpulse.yml` |
| `bot_cloud.py` | LinkedIn · InfoJobs · TecnoEmpleo · JobToday · Manfred | `.github/workflows/main.yml` |

### ✅ Sistema de filtros inteligente

Solo recibe ofertas que cumplen **3 condiciones AND**:

1. **Contiene**: "back office", "backoffice" o "postventa"
2. **Indica remoto**: "remoto", "teletrabajo", "home office"
3. **Excluye roles**: director, senior, developer, freelance, etc.

### 🛡️ Estable y seguro

- Reintentos automáticos ante timeouts y backoff exponencial para rate limits.
- Logging completo de cada ejecución.
- Credenciales **solo por variables de entorno / GitHub Secrets** — ningún secreto en el código.

### ⚡ Instalación (5 minutos)

1. **Credenciales de Telegram**: `@BotFather` → `/newbot` → copia el `TOKEN`. `@userinfobot` → `/start` → copia tu `CHAT_ID`.
2. **Clona el repo**: `git clone https://github.com/3573b4n/JobPulse.git`
3. **Añade los Secrets**: Settings → Secrets and variables → Actions → `TELEGRAM_TOKEN` y `TELEGRAM_CHAT_ID`.
4. **Permisos**: Settings → Actions → General → "Read and write permissions" ✅
5. **Listo**: el bot se ejecuta solo cada 30 minutos (o manualmente con `workflow_dispatch`).

### 🗂 Estructura del proyecto

```
JobPulse/
├── job_bot.py                       # Scraper principal — 6 plataformas
├── bot_cloud.py                     # Scraper alternativo — 5 plataformas
├── validate.py                      # Validación de config y conexión a Telegram
├── requirements.txt                 # requests · beautifulsoup4 · curl_cffi · lxml
├── ofertas_vistas.txt               # IDs ya vistos (dedup, autogenerado)
├── .github/workflows/jobpulse.yml   # Cron 30 min → job_bot.py
└── .github/workflows/main.yml       # Cron 30 min → bot_cloud.py
```

### 🔧 Personalización

Edita `job_bot.py` o `bot_cloud.py` para cambiar palabras clave requeridas/excluidas,
la frecuencia del cron (`.github/workflows/*.yml`) o el formato de los mensajes.

---

## 🇬🇧 English

Smart agent that scans **Spanish job boards every 30 minutes** and sends you a Telegram
notification whenever a posting matches your criteria. Runs 24/7 on GitHub Actions
(free tier) — your PC stays off.

### 🎯 What it does

- **Automatic scraping** every 30 minutes (configurable cron).
- **Rich Telegram notifications** with title, location and direct link.
- **Persistent deduplication**: stores seen offer IDs, never repeats.
- **First to apply**: getting the alert in minutes makes the difference in a fast market.

### 🧩 Two scraping modules

| Module | Platforms | Workflow |
|---|---|---|
| `job_bot.py` | LinkedIn · InfoJobs · Indeed · TecnoEmpleo · Glassdoor · Jooble | `.github/workflows/jobpulse.yml` |
| `bot_cloud.py` | LinkedIn · InfoJobs · TecnoEmpleo · JobToday · Manfred | `.github/workflows/main.yml` |

### ✅ Smart filtering

You only get offers matching **3 AND conditions**: keywords ("back office", "backoffice",
"postventa") + remote signal ("remoto", "teletrabajo", "home office") minus excluded roles
(director, senior, developer, freelance…).

### 🛡️ Stable and secure

- Automatic retries on timeouts, exponential backoff for rate limits.
- Full logging on every run.
- Credentials **only via environment variables / GitHub Secrets** — no secrets in code.

### ⚡ Setup (5 minutes)

1. **Telegram credentials**: `@BotFather` → `/newbot` → copy the `TOKEN`. `@userinfobot` → `/start` → copy your `CHAT_ID`.
2. **Clone the repo**: `git clone https://github.com/3573b4n/JobPulse.git`
3. **Add Secrets**: Settings → Secrets and variables → Actions → `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID`.
4. **Permissions**: Settings → Actions → General → "Read and write permissions" ✅
5. **Done**: the bot runs itself every 30 minutes (or manually via `workflow_dispatch`).

### 🔧 Customization

Edit `job_bot.py` or `bot_cloud.py` to change keywords, the cron schedule
(`.github/workflows/*.yml`) or the message format.
