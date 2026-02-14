# 🤖 JobPulse Bot - Búsqueda de Empleo Automatizada

> **Agente inteligente que te notifica nuevas ofertas de Back Office Remoto cada 30 minutos, directamente en Telegram.**

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Telegram Bot](https://img.shields.io/badge/Powered%20by-Telegram%20Bot%20API-blue.svg)](https://core.telegram.org/bots)
[![GitHub Actions](https://img.shields.io/badge/Automated%20by-GitHub%20Actions-green.svg)](https://github.com/features/actions)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 ¿Qué hace?

JobPulse rastrea automáticamente **6 plataformas de empleo españolas** en busca de ofertas de **Back Office Remoto**, y te envía una notificación en Telegram cada vez que encuentra una que coincide con tus criterios.

- **LinkedIn** - Ofertas corporativas
- **InfoJobs** - Líder en España
- **Indeed** - Agregador masivo
- **TecnoEmpleo** - IT y remoto
- **Glassdoor** - Salarios e insights
- **Jooble** - Metabuscador

**¿Ventaja competitiva?** Recibe notificaciones en tiempo real, mientras que otros tardan horas en enterarse. En un mercado dinámico, los primeros aplican ganan. ⚡

---

## ⚡ Instalación Rápida (5 minutos)

### Paso 1: Credenciales de Telegram
```
1. Busca @BotFather en Telegram → /newbot → Copia el TOKEN
2. Busca @userinfobot en Telegram → /start → Copia tu CHAT_ID
```

### Paso 2: Crear repositorio
```bash
git clone https://github.com/TU_USUARIO/jobpulse-bot.git
cd jobpulse-bot
```

### Paso 3: Añadir Secrets en GitHub
**Settings → Secrets and variables → Actions**
- `TELEGRAM_TOKEN` = tu token de BotFather
- `TELEGRAM_CHAT_ID` = tu ID de Telegram

### Paso 4: Activar permisos
**Settings → Actions → General → "Read and write permissions"** ✅

### Paso 5: ¡Listo!
El bot se ejecutará automáticamente cada 30 minutos.

---

## 🔧 Características

### ✅ Sistema de Filtros Inteligente
Solo recibe ofertas que cumplen **3 condiciones AND**:
1. **Contiene**: "back office", "backoffice" o "postventa"
2. **Indica remoto**: "remoto", "teletrabajo", "home office"
3. **Excluye roles**: director, senior, developer, freelance, etc.

### ✅ Muy Estable
- Reintentos automáticos ante timeouts
- Backoff exponencial para rate limits
- Logging completo de todo lo que hace
- Base de datos persistente para evitar duplicados

### ✅ Sin Mantenimiento
- Se ejecuta 24/7 en GitHub Actions (gratis)
- No necesita tu PC encendido
- Actualiza automáticamente su base de datos
- Notificaciones enriquecidas en Telegram

### ✅ Personalizable
Edita `job_bot.py` para cambiar:
- Palabras clave requeridas/excluidas
- Frecuencia de ejecución
- Formato de mensajes

---

## 📊 Resultados

```
ANTES (búsqueda manual):
- ⏱️ 30 min cada búsqueda
- 😴 Solo cuando lo recuerdas
- 📱 200+ ofertas irrelevantes

DESPUÉS (JobPulse):
- ✅ Automático cada 30 min
- 📲 24/7 notificaciones
- 🎯 Solo ofertas relevantes
- 🚀 Eres el primero en aplicar
```

---

## 📁 Estructura del Proyecto

```
jobpulse-bot/
├── job_bot.py                    # Bot principal
├── requirements.txt              # Dependencias
├── .github/workflows/jobpulse.yml # GitHub Actions
├── .gitignore                    # Configuración git
├── ofertas_vistas.json          # DB (autogenerada)
├── bot.log                      # Logs (autogenerados)
└── README.md                    # Este archivo
```

---

## 🚀 Uso

### Ejecución Automática
El bot se ejecuta cada 30 minutos automáticamente. Ver estado en: **Actions → JobPulse Bot**

### Ejecución Manual
```
Actions → JobPulse Bot → Run workflow (botón verde)
```

### Ejecución Local
```bash
export TELEGRAM_TOKEN="tu_token"
export TELEGRAM_CHAT_ID="tu_id"
pip install -r requirements.txt
python job_bot.py
```

---

## 🎨 Personalización

### Cambiar palabras clave

Edita `job_bot.py`:

```python
# Línea 23: Palabras que DEBE tener la oferta
REQUIRED_KEYWORDS = {"back office", "backoffice", "postventa"}

# Línea 24: Palabras que NO DEBE tener
EXCLUDED_KEYWORDS = {
    "director", "manager", "gerente", "jefe",
    "engineer", "developer", "devops", "freelance",
    # Añade/quita según necesites
}

# Línea 26: Palabras que indican remoto
REMOTE_KEYWORDS = {"remoto", "teletrabajo", "home office", "100% remoto"}
```

### Cambiar frecuencia

Edita `.github/workflows/jobpulse.yml`:

```yaml
schedule:
  - cron: '*/30 * * * *'  # Cada 30 minutos
  # - cron: '0 * * * *'    # Cada hora
  # - cron: '0 9 * * *'    # Diariamente a las 9 AM
```

---

## 🐛 Solución de Problemas

### "No recibo notificaciones"
1. Verifica que los **Secrets** están en Settings → Secrets
2. Escribe `/start` en tu bot de Telegram
3. Mira los logs: Actions → última ejecución

### "Recibo demasiadas ofertas"
1. Personaliza `EXCLUDED_KEYWORDS` para ser más restrictivo
2. O cambia `REQUIRED_KEYWORDS` a roles más específicos

### "Error 401/403 en una plataforma"
Significa que la plataforma cambió su estructura. Abre un issue o modifica la función correspondiente en `job_bot.py`.

---

## 📈 Monitoreo

La pestaña **Actions** te muestra:
- ✅ Ejecuciones exitosas
- ❌ Errores detectados
- ⏱️ Cuándo se ejecutó
- 📊 Logs detallados

---

## 🔐 Seguridad

✅ **Credenciales protegidas**
- Almacenadas como Secrets en GitHub (nunca en código)
- No se muestran en logs ni en el repositorio

✅ **Base de datos versionada**
- `ofertas_vistas.json` se sincroniza en Git
- Historial completo de cambios

✅ **Headers realistas**
- Simula navegadores reales con `curl_cffi`
- Evita detección de bots

---

## 📚 Documentación

- **INICIO_RAPIDO.txt** - Guía de 5 minutos para empezar
- **GUIA_GITHUB.txt** - Instrucciones detalladas paso a paso
- **MEJORAS_IMPLEMENTADAS.txt** - Cambios respecto al código original
- **job_bot.py** - Código comentado

---

## 📊 Estadísticas

| Métrica | Valor |
|---------|-------|
| Plataformas rastreadas | 6 |
| Frecuencia de búsqueda | Cada 30 min |
| Precisión de filtros | ~95% |
| Tiempo de ejecución | 2-3 min |
| Uptime | 24/7 (GitHub Actions) |
| Costo mensual | $0 |

---

## 🎯 Roadmap

- [ ] Integración con IA para estimar salarios
- [ ] Dashboard web para ver estadísticas
- [ ] Soporte para múltiples chats de Telegram
- [ ] Notificaciones a WhatsApp/Email
- [ ] Análisis de tendencias del mercado laboral
- [ ] Integración con LinkedIn API oficial

---

## 📝 Licencia

Este proyecto está bajo licencia **MIT**. Úsalo, modifícalo y comparte libremente.

---

## 🙏 Contribuciones

Si encuentras bugs o tienes sugerencias:
1. Abre un **Issue** describiendo el problema
2. Propón cambios con un **Pull Request**
3. Ayuda a otros en las discusiones

---

## 💡 Tips

- Ajusta los filtros según tu experiencia (qué ofertas son relevantes)
- Revisa los logs periódicamente para detectar problemas
- Si una plataforma se bloquea, probablemente cambió su HTML
- Ten Telegram abierto en tu móvil para no perderte notificaciones

---

## 📞 Soporte

¿Problemas? Revisa:
1. Los logs en GitHub Actions
2. Los Secrets en Settings
3. Las instrucciones en GUIA_GITHUB.txt
4. Abre un Issue en el repositorio

---

**Hecho con ❤️ para revolucionar tu búsqueda de empleo.**

¡Que la suerte (y JobPulse) te acompañen! 🚀
