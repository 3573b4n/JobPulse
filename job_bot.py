import requests
from bs4 import BeautifulSoup
import time
import html
import os
import re
import random
import logging
from datetime import datetime
from curl_cffi import requests as curl_requests
from typing import Tuple, Optional, Set
import json

# ========== CONFIGURACIÓN LOGGING ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ========== CONFIGURACIÓN GLOBAL ==========
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DB_FILE = "ofertas_vistas.json"
LOG_FILE = "bot.log"

# Palabras clave que SIEMPRE deben estar presentes (AND)
REQUIRED_KEYWORDS = {"back office", "backoffice", "postventa"}

# Palabras clave que DEBEN estar excluidas (NOT)
EXCLUDED_KEYWORDS = {
    "director", "manager", "gerente", "jefe", "supervisor",
    "ejecutivo", "ceo", "cto", "engineer", "developer",
    "python", "java", "javascript", "devops", "docker",
    "senior", "lead", "arquitecto", "tech lead", "fullstack",
    "freelance", "consultor", "contrato temporal", "práctica",
    "teleoperador", "soporte técnico", "it", "programador"
}

# Palabras que indican remoto
REMOTE_KEYWORDS = {"remoto", "teletrabajo", "home office", "100% remoto", "work from home"}

# ========== PERSISTENCIA DE DATOS ==========
def load_seen_offers() -> Set[str]:
    """Carga las ofertas ya vistas desde JSON"""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("seen_offers", []))
        except Exception as e:
            logger.warning(f"Error cargando base de datos: {e}. Iniciando nueva.")
    return set()

def save_seen_offers(offers: Set[str]) -> bool:
    """Guarda las ofertas vistas en JSON"""
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "seen_offers": list(offers),
                "last_updated": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error guardando base de datos: {e}")
        return False

OFERTAS_VISTAS = load_seen_offers()

# ========== FUNCIONES DE FILTRADO ==========
def matches_criteria(title: str, company: str = "", description: str = "") -> bool:
    """
    Valida que la oferta cumpla con los criterios de filtrado.
    
    Criterios:
    1. DEBE contener al menos una palabra clave requerida
    2. DEBE contener palabra remoto
    3. NO DEBE contener palabras excluidas
    """
    text = f"{title} {company} {description}".lower()
    
    # Verificar palabras requeridas (AND)
    has_required = any(kw in text for kw in REQUIRED_KEYWORDS)
    if not has_required:
        return False
    
    # Verificar palabras remotas
    has_remote = any(kw in text for kw in REMOTE_KEYWORDS)
    if not has_remote:
        return False
    
    # Verificar palabras excluidas (NOT)
    has_excluded = any(kw in text for kw in EXCLUDED_KEYWORDS)
    if has_excluded:
        return False
    
    return True

def safe_html_escape(text: str) -> str:
    """Escapa seguramente texto HTML"""
    if not text:
        return "N/A"
    return html.escape(str(text).strip()[:150])  # Limitar a 150 caracteres

# ========== TELEGRAM ==========
def send_telegram(message: str) -> bool:
    """Envía mensaje a Telegram con manejo de errores mejorado"""
    if not TOKEN or not CHAT_ID:
        logger.error("Credenciales de Telegram no configuradas")
        return False
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, data=payload, timeout=15)
        if response.status_code == 200:
            return True
        else:
            logger.error(f"Telegram error {response.status_code}: {response.text}")
            return False
    except requests.Timeout:
        logger.error("Timeout enviando a Telegram")
        return False
    except Exception as e:
        logger.error(f"Error enviando Telegram: {e}")
        return False

def format_job_message(platform: str, title: str, company: str, link: str, emoji: str) -> str:
    """Formatea un mensaje de oferta con plantilla estándar"""
    return (
        f"{emoji} <b>NUEVA OFERTA EN {platform.upper()}</b>\n\n"
        f"📌 <b>Puesto:</b> {safe_html_escape(title)}\n"
        f"🏢 <b>Empresa:</b> {safe_html_escape(company)}\n"
        f"🎯 <b>Tipo:</b> Back Office / Remoto\n"
        f"🔗 <a href='{link}'>👉 VER OFERTA</a>"
    )

# ========== SCRAPING CON REINTENTOS ==========
def get_page(url: str, impersonate: str = "chrome120", retries: int = 3) -> Optional[str]:
    """Obtiene página con reintentos y manejo de errores"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "es-ES,es;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    
    for attempt in range(retries):
        try:
            time.sleep(random.uniform(2, 4))  # Pausa entre peticiones
            response = curl_requests.get(
                url,
                impersonate=impersonate,
                headers=headers,
                timeout=20
            )
            
            if response.status_code == 200:
                return response.text
            elif response.status_code in [429, 503]:
                wait_time = min(60, 5 * (attempt + 1))
                logger.warning(f"Rate limited. Esperando {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.warning(f"Status {response.status_code} en intento {attempt + 1}/{retries}")
                
        except Exception as e:
            logger.warning(f"Intento {attempt + 1} fallido: {e}")
            if attempt < retries - 1:
                time.sleep(5)
    
    return None

# ========== SCRAPING DE PLATAFORMAS ==========

def search_linkedin(query: str = "Back Office") -> Tuple[int, Optional[str]]:
    """Busca en LinkedIn"""
    logger.info("📱 Buscando en LinkedIn...")
    query_encoded = query.replace(" ", "%20")
    url = f"https://www.linkedin.com/jobs/search/?f_TPR=r86400&f_WT=2&keywords={query_encoded}&location=Spain"
    
    try:
        page_html = get_page(url, impersonate="chrome120")
        if not page_html:
            return 0, "LinkedIn: No se pudo obtener la página"
        
        soup = BeautifulSoup(page_html, 'html.parser')
        jobs = soup.find_all('div', class_=re.compile(r'base-card|job-card'))
        
        nuevas = 0
        for job in jobs:
            try:
                job_id = "ln_" + (job.get('data-entity-urn') or str(hash(job.text[:30])))
                
                if job_id in OFERTAS_VISTAS:
                    continue
                
                # Extraer información
                title_elem = job.find(['h3', 'h2', 'span'], class_=re.compile(r'title|name'))
                company_elem = job.find(['h4', 'span'], class_=re.compile(r'company|subtitle'))
                link_elem = job.find('a', href=re.compile(r'linkedin.com/jobs/view'))
                
                if not title_elem or not link_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                company = company_elem.get_text(strip=True) if company_elem else "Sin empresa"
                link = link_elem['href'].split('?')[0]
                
                # Aplicar filtros
                if not matches_criteria(title, company):
                    continue
                
                # Enviar y registrar
                msg = format_job_message("LinkedIn", title, company, link, "🚀")
                if send_telegram(msg):
                    OFERTAS_VISTAS.add(job_id)
                    nuevas += 1
                    logger.info(f"✅ LinkedIn: {title[:50]}...")
                    
            except Exception as e:
                logger.debug(f"Error procesando job LinkedIn: {e}")
                continue
        
        logger.info(f"LinkedIn: {nuevas} nuevas encontradas")
        return nuevas, None
        
    except Exception as e:
        logger.error(f"LinkedIn error crítico: {e}")
        return 0, f"LinkedIn: {str(e)}"

def search_infojobs(query: str = "Back Office") -> Tuple[int, Optional[str]]:
    """Busca en InfoJobs"""
    logger.info("💼 Buscando en InfoJobs...")
    query_encoded = query.replace(" ", "%20")
    url = f"https://www.infojobs.net/ofertas-trabajo?keyword={query_encoded}&teleworkingIds=3&sortBy=PUBLICATION_DATE"
    
    try:
        page_html = get_page(url)
        if not page_html:
            return 0, "InfoJobs: No se pudo obtener la página"
        
        soup = BeautifulSoup(page_html, 'html.parser')
        offers = soup.find_all('a', href=re.compile(r'/of-i'))
        
        nuevas = 0
        for offer in offers:
            try:
                href = offer.get('href', '')
                match = re.search(r'/of-i([a-zA-Z0-9]+)', href)
                if not match:
                    continue
                
                job_id = f"ij_{match.group(1)}"
                
                if job_id in OFERTAS_VISTAS:
                    continue
                
                title = offer.get_text(strip=True)
                
                # Filtros específicos InfoJobs
                if not matches_criteria(title):
                    continue
                
                full_link = f"https://www.infojobs.net{href}" if not href.startswith('http') else href
                
                msg = format_job_message("InfoJobs", title, "InfoJobs", full_link, "💼")
                if send_telegram(msg):
                    OFERTAS_VISTAS.add(job_id)
                    nuevas += 1
                    logger.info(f"✅ InfoJobs: {title[:50]}...")
                    
            except Exception as e:
                logger.debug(f"Error procesando offer InfoJobs: {e}")
                continue
        
        logger.info(f"InfoJobs: {nuevas} nuevas encontradas")
        return nuevas, None
        
    except Exception as e:
        logger.error(f"InfoJobs error crítico: {e}")
        return 0, f"InfoJobs: {str(e)}"

def search_indeed(query: str = "Back Office Remoto") -> Tuple[int, Optional[str]]:
    """Busca en Indeed"""
    logger.info("🔥 Buscando en Indeed...")
    query_encoded = query.replace(" ", "+")
    url = f"https://es.indeed.com/jobs?q={query_encoded}&l=España&fromage=1&sc=0kf%3Atemp_type%3A7;"
    
    try:
        page_html = get_page(url, impersonate="chrome110")
        if not page_html:
            return 0, "Indeed: No se pudo obtener la página"
        
        soup = BeautifulSoup(page_html, 'html.parser')
        jobs = soup.find_all('div', class_=re.compile(r'job_seen_beacon|jobsearch-SerpJob'))
        
        nuevas = 0
        for job in jobs:
            try:
                link_tag = job.find('a', class_=re.compile(r'jcs-JobTitle|base-card__full-link'))
                if not link_tag:
                    continue
                
                jk = link_tag.get('data-jk') or re.search(r'jk=([a-zA-Z0-9]+)', link_tag.get('href', '')).group(1)
                job_id = f"in_{jk}"
                
                if job_id in OFERTAS_VISTAS:
                    continue
                
                title_elem = job.find(['h2', 'span'], class_=re.compile(r'jobTitle|title'))
                company_elem = job.find(['span', 'div'], class_=re.compile(r'company|companyName'))
                
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                company = company_elem.get_text(strip=True) if company_elem else "Sin empresa"
                link = f"https://es.indeed.com/viewjob?jk={jk}"
                
                if not matches_criteria(title, company):
                    continue
                
                msg = format_job_message("Indeed", title, company, link, "🔥")
                if send_telegram(msg):
                    OFERTAS_VISTAS.add(job_id)
                    nuevas += 1
                    logger.info(f"✅ Indeed: {title[:50]}...")
                    
            except Exception as e:
                logger.debug(f"Error procesando job Indeed: {e}")
                continue
        
        logger.info(f"Indeed: {nuevas} nuevas encontradas")
        return nuevas, None
        
    except Exception as e:
        logger.error(f"Indeed error crítico: {e}")
        return 0, f"Indeed: {str(e)}"

def search_tecnoempleo(query: str = "Back Office") -> Tuple[int, Optional[str]]:
    """Busca en TecnoEmpleo"""
    logger.info("💻 Buscando en TecnoEmpleo...")
    query_encoded = query.replace(" ", "+")
    url = f"https://www.tecnoempleo.com/busqueda-empleo.php?te={query_encoded}&re=1&f=24h"
    
    try:
        page_html = get_page(url)
        if not page_html:
            return 0, "TecnoEmpleo: No se pudo obtener la página"
        
        soup = BeautifulSoup(page_html, 'html.parser')
        offers = soup.find_all(['h3', 'h2'])
        
        nuevas = 0
        for offer in offers:
            try:
                link_tag = offer.find('a')
                if not link_tag:
                    continue
                
                href = link_tag.get('href', '')
                job_id = f"te_{hash(href)}"
                
                if job_id in OFERTAS_VISTAS:
                    continue
                
                title = offer.get_text(strip=True)
                
                if not matches_criteria(title):
                    continue
                
                full_link = href if href.startswith('http') else f"https://www.tecnoempleo.com{href}"
                
                msg = format_job_message("TecnoEmpleo", title, "TecnoEmpleo", full_link, "💻")
                if send_telegram(msg):
                    OFERTAS_VISTAS.add(job_id)
                    nuevas += 1
                    logger.info(f"✅ TecnoEmpleo: {title[:50]}...")
                    
            except Exception as e:
                logger.debug(f"Error procesando offer TecnoEmpleo: {e}")
                continue
        
        logger.info(f"TecnoEmpleo: {nuevas} nuevas encontradas")
        return nuevas, None
        
    except Exception as e:
        logger.error(f"TecnoEmpleo error crítico: {e}")
        return 0, f"TecnoEmpleo: {str(e)}"

def search_glassdoor() -> Tuple[int, Optional[str]]:
    """Busca en Glassdoor"""
    logger.info("💎 Buscando en Glassdoor...")
    url = "https://www.glassdoor.es/Job/espana-back-office-jobs-SRCH_IL.0,6_IN219.htm?fromAge=1"
    
    try:
        page_html = get_page(url, impersonate="safari_ios_16_0")
        if not page_html:
            return 0, "Glassdoor: No se pudo obtener la página"
        
        soup = BeautifulSoup(page_html, 'html.parser')
        links = soup.find_all('a', attrs={'data-test': 'job-link'})
        
        nuevas = 0
        for link in links:
            try:
                href = link.get('href', '')
                if not href:
                    continue
                
                job_id = f"gd_{hash(href)}"
                
                if job_id in OFERTAS_VISTAS:
                    continue
                
                title = link.get_text(strip=True)
                
                if not matches_criteria(title):
                    continue
                
                full_link = href if href.startswith('http') else f"https://www.glassdoor.es{href}"
                
                msg = format_job_message("Glassdoor", title, "Glassdoor", full_link, "💎")
                if send_telegram(msg):
                    OFERTAS_VISTAS.add(job_id)
                    nuevas += 1
                    logger.info(f"✅ Glassdoor: {title[:50]}...")
                    
            except Exception as e:
                logger.debug(f"Error procesando job Glassdoor: {e}")
                continue
        
        logger.info(f"Glassdoor: {nuevas} nuevas encontradas")
        return nuevas, None
        
    except Exception as e:
        logger.error(f"Glassdoor error crítico: {e}")
        return 0, f"Glassdoor: {str(e)}"

def search_jooble(query: str = "Back Office") -> Tuple[int, Optional[str]]:
    """Busca en Jooble"""
    logger.info("🔍 Buscando en Jooble...")
    query_encoded = query.replace(" ", "%20")
    url = f"https://es.jooble.org/trabajo?q={query_encoded}&l=España"
    
    try:
        page_html = get_page(url)
        if not page_html:
            return 0, "Jooble: No se pudo obtener la página"
        
        soup = BeautifulSoup(page_html, 'html.parser')
        articles = soup.find_all('article')
        
        nuevas = 0
        for article in articles:
            try:
                link_tag = article.find('a')
                if not link_tag:
                    continue
                
                href = link_tag.get('href', '')
                job_id = f"jb_{hash(href)}"
                
                if job_id in OFERTAS_VISTAS:
                    continue
                
                title = link_tag.get_text(strip=True)
                
                if not matches_criteria(title):
                    continue
                
                full_link = href if href.startswith('http') else f"https://es.jooble.org{href}"
                
                msg = format_job_message("Jooble", title, "Jooble", full_link, "🔍")
                if send_telegram(msg):
                    OFERTAS_VISTAS.add(job_id)
                    nuevas += 1
                    logger.info(f"✅ Jooble: {title[:50]}...")
                    
            except Exception as e:
                logger.debug(f"Error procesando job Jooble: {e}")
                continue
        
        logger.info(f"Jooble: {nuevas} nuevas encontradas")
        return nuevas, None
        
    except Exception as e:
        logger.error(f"Jooble error crítico: {e}")
        return 0, f"Jooble: {str(e)}"

# ========== ORQUESTACIÓN ==========
def run_all_searches() -> None:
    """Ejecuta todos los buscadores"""
    logger.info("=" * 50)
    logger.info("INICIANDO CICLO DE BÚSQUEDA")
    logger.info(f"Ofertas en caché: {len(OFERTAS_VISTAS)}")
    logger.info("=" * 50)
    
    searches = [
        ("LinkedIn", lambda: search_linkedin("Back Office")),
        ("InfoJobs", lambda: search_infojobs("Back Office")),
        ("Indeed", lambda: search_indeed("Back Office Remoto")),
        ("TecnoEmpleo", lambda: search_tecnoempleo("Back Office")),
        ("Glassdoor", lambda: search_glassdoor()),
        ("Jooble", lambda: search_jooble("Back Office"))
    ]
    
    total_nuevas = 0
    errores = []
    
    for nombre, search_func in searches:
        try:
            nuevas, error = search_func()
            total_nuevas += nuevas
            if error:
                errores.append(error)
        except Exception as e:
            logger.error(f"Error en {nombre}: {e}")
            errores.append(f"{nombre}: {str(e)}")
        
        time.sleep(random.uniform(5, 10))  # Pausa entre plataformas
    
    # Resumen final
    summary = (
        f"✅ <b>CICLO COMPLETADO</b>\n\n"
        f"📊 <b>Resumen:</b>\n"
        f"🎯 Ofertas nuevas: <b>{total_nuevas}</b>\n"
        f"💾 Total en caché: <b>{len(OFERTAS_VISTAS)}</b>\n"
        f"⏰ {datetime.now().strftime('%H:%M:%S')}"
    )
    send_telegram(summary)
    
    if errores:
        error_msg = "⚠️ <b>ERRORES DETECTADOS</b>\n" + "\n".join([f"• {e}" for e in errores[:5]])
        send_telegram(error_msg)
    
    logger.info(f"Ciclo completado: {total_nuevas} nuevas, {len(errores)} errores")
    save_seen_offers(OFERTAS_VISTAS)

if __name__ == "__main__":
    logger.info("🤖 JobPulse Bot iniciado")
    try:
        run_all_searches()
    except KeyboardInterrupt:
        logger.info("Bot detenido manualmente")
    except Exception as e:
        logger.critical(f"Error crítico: {e}")
        send_telegram(f"❌ <b>ERROR CRÍTICO</b>\n{str(e)}")
    finally:
        save_seen_offers(OFERTAS_VISTAS)
        logger.info("🤖 JobPulse Bot finalizado")
