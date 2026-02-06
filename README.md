# 🤖 Bot de Búsqueda de Empleo 24/7 (Back Office & Remoto)

Este proyecto es un agente inteligente desarrollado en Python diseñado para rastrear automáticamente las principales plataformas de empleo en España, buscando puestos de **Back Office** con modalidad **Remoto/Teletrabajo**. El bot envía notificaciones instantáneas a través de un canal de **Telegram** cada vez que encuentra una nueva oferta.

## 🚀 Características Principales

* **Multiplataforma**: Rastrea simultáneamente 8 portales líderes.
* **Automatización Total**: Configurado para funcionar 24/7 mediante **GitHub Actions** sin necesidad de tener el ordenador encendido.
* **Inteligencia Anti-Duplicados**: Utiliza un sistema de persistencia para no repetir ofertas que ya han sido enviadas.
* **Simulación de Navegador Humano**: Implementa `curl_cffi` y cabeceras personalizadas para evitar bloqueos por parte de los portales de empleo.

## 📊 Plataformas Soportadas

| Plataforma | Especialidad |
| :--- | :--- |
| **LinkedIn** | Ofertas corporativas y perfiles profesionales. |
| **InfoJobs** | Principal portal de empleo en España. |
| **Indeed** | Agregador global de ofertas. |
| **TecnoEmpleo** | Ofertas especializadas en tecnología y remoto. |
| **Glassdoor** | Salarios y valoraciones de empresas. |
| **Manfred** | Ofertas tecnológicas transparentes y remotas. |
| **JobToday** | Mercado laboral dinámico y rápido. |
| **Jooble** | Metuscador para no perder ninguna oportunidad. |

## 🏗️ Arquitectura del Proyecto

El bot tiene dos modos de operación:

1. **Modo Nube (`bot_cloud.py`)**: Diseñado para ejecutarse en GitHub Actions. Se despierta, busca, notifica y se apaga. Utiliza el archivo `ofertas_vistas.txt` para recordar los IDs.
2. **Modo Local (`Bot automático para búsqueda eempleo.py`)**: Script con bucle infinito para ejecución continua en un servidor propio o portátil.

## 🛠️ Instalación y Configuración (Modo Nube)

### 1. Variables de Entorno (Secrets)

Para que el bot funcione en GitHub, debes añadir estos **Secrets** en tu repositorio (`Settings` > `Secrets and variables` > `Actions`):

* `TELEGRAM_TOKEN`: El token proporcionado por [@BotFather](https://t.me/BotFather).
* `TELEGRAM_CHAT_ID`: Tu ID de chat (puedes obtenerlo de [@userinfobot](https://t.me/userinfobot)).

### 2. Permisos de Escritura

Para que el bot pueda guardar las ofertas vistas, activa los permisos en:
`Settings` > `Actions` > `General` > `Workflow permissions` > Seleccionar **"Read and write permissions"**.

### 3. Ejecución

El bot está configurado en `.github/workflows/main.yml` para ejecutarse cada 30 minutos de forma automática. También puedes lanzarlo manualmente desde la pestaña **Actions**.

## 📦 Requisitos Técnicos

Las librerías necesarias están detalladas en `requirements.txt`:

* `requests`
* `beautifulsoup4`
* `curl_cffi`
* `cloudscraper` (opcional según plataforma)

---
*Desarrollado con ❤️ para optimizar la búsqueda de empleo por EDL.*
