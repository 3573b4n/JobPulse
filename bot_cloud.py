import requests
from bs4 import BeautifulSoup
import time
import html
import os
import re
import random
import json
from curl_cffi import requests as curl_requests

# --- CONFIGURACIÓN PARA GITHUB ACTIONS (MODO NUBE) ---
# En GitHub se configuran como Secrets: TELEGRAM_TOKEN y TELEGRAM_CHAT_ID
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- PERSISTENCIA DE DATOS ---
DB_FILE = "ofertas_vistas.txt"

def cargar_vistas():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return set(f.read().splitlines())
    return set()

def guardar_vistas(vistas):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(list(vistas)))

OFERTAS_VISTAS = cargar_vistas()

# --- HEADERS GLOBALES ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

def enviar_telegram(mensaje):
    if not TOKEN or not CHAT_ID:
        print("⚠️ Error: TOKEN o CHAT_ID no configurados en las variables de entorno.")
        return False
        
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensaje,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, data=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error enviando a Telegram: {e}")
        return False

# --- FUNCIONES DE BÚSQUEDA ---

def buscar_linkedin(query):
    print(f"Revisando LinkedIn para: {query}...")
    q_enc = query.replace(" ", "%20")
    url_lp = f"https://www.linkedin.com/jobs/search/?f_TPR=r86400&f_WT=2&keywords={q_enc}&location=Spain"
    try:
        res = curl_requests.get(url_lp, impersonate="chrome120", timeout=30)
        if res.status_code != 200: return 0
        soup = BeautifulSoup(res.text, 'html.parser')
        jobs = soup.find_all('div', class_='base-card')
        nuevas = 0
        for job in jobs:
            try:
                job_id = "linkedin_" + job.get('data-entity-urn', 'id_desconocido')
                if job_id not in OFERTAS_VISTAS:
                    titulo_elem = job.find('h3', class_='base-search-card__title')
                    empresa_elem = job.find('h4', class_='base-search-card__subtitle')
                    link_elem = job.find('a', class_='base-card__full-link')
                    if not titulo_elem or not empresa_elem or not link_elem: continue
                    titulo = html.escape(titulo_elem.text.strip())
                    empresa = html.escape(empresa_elem.text.strip())
                    link = link_elem['href']
                    mensaje = (f"🚀 <b>¡NUEVA OFERTA EN LINKEDIN!</b>\n\n"
                               f"📌 <b>Puesto:</b> {titulo}\n"
                               f"🏢 <b>Empresa:</b> {empresa}\n"
                               f"🕒 <b>Filtro:</b> 24h / Remoto\n\n"
                               f"🔗 <a href='{link}'>Postularse</a>")
                    if enviar_telegram(mensaje): OFERTAS_VISTAS.add(job_id); nuevas += 1
            except Exception: continue
        return nuevas
    except Exception as e: 
        print(f"Error LinkedIn: {e}")
        return 0

def buscar_indeed(query):
    print(f"Revisando Indeed para: {query}...")
    q_enc = query.replace(" ", "+")
    url_in = f"https://es.indeed.com/jobs?q={q_enc}&l=espa%C3%B1a&fromage=1&sc=0kf%3Aattr%28DS7X8%29%3B"
    try:
        time.sleep(random.uniform(2, 5))
        res = curl_requests.get(url_in, impersonate="chrome120", timeout=30)
        if res.status_code != 200: return 0
        soup = BeautifulSoup(res.text, 'html.parser')
        jobs = soup.find_all('div', class_='job_seen_beacon')
        nuevas = 0
        for job in jobs:
            try:
                link_tag = job.find('a', class_='jcs-JobTitle')
                if not link_tag: continue
                job_id = "indeed_" + link_tag.get('data-jk', 'id_desconocido')
                if job_id not in OFERTAS_VISTAS:
                    titulo_elem = job.find('h2', class_='jobTitle')
                    empresa_elem = job.find('span', {'data-testid': 'company-name'}) or job.find('span', class_='companyName')
                    if not titulo_elem: continue
                    titulo = html.escape(titulo_elem.text.strip())
                    empresa = html.escape(empresa_elem.text.strip()) if empresa_elem else "Empresa?"
                    link = "https://es.indeed.com" + link_tag['href']
                    mensaje = (f"🔥 <b>¡NUEVA OFERTA EN INDEED!</b>\n\n📌 <b>Puesto:</b> {titulo}\n🏢 <b>Empresa:</b> {empresa}\n🕒 <b>Filtro:</b> 24h / Remoto\n\n🔗 <a href='{link}'>Postularse</a>")
                    if enviar_telegram(mensaje): OFERTAS_VISTAS.add(job_id); nuevas += 1
            except Exception: continue
        return nuevas
    except Exception as e: 
        print(f"Error Indeed: {e}")
        return 0

def buscar_infojobs(query):
    print(f"Revisando InfoJobs para: {query}...")
    q_enc = query.replace(" ", "%20")
    # InfoJobs: remoto ordenado por fecha últimas 24h (history=1)
    url_ij = f"https://www.infojobs.net/ofertas-trabajo?keyword={q_enc}&teleworkingIds=3&sortBy=PUBLICATION_DATE&history=1"
    try:
        time.sleep(random.uniform(2, 4))
        res = curl_requests.get(url_ij, impersonate="chrome120", timeout=30)
        if res.status_code != 200: return 0
        soup = BeautifulSoup(res.text, 'html.parser')
        links_ofertas = soup.find_all('a', href=re.compile(r'/of-i'))
        nuevas = 0
        for link_tag in links_ofertas:
            try:
                link = link_tag['href']
                if not link.startswith('http'): link = "https://www.infojobs.net" + link
                match = re.search(r'of-i([a-zA-Z0-9]+)', link)
                if not match: continue
                job_id = "infojobs_" + match.group(1)
                if job_id not in OFERTAS_VISTAS:
                    raw_titulo = link_tag.text.strip()
                    if not raw_titulo:
                        raw_titulo = "Puesto InfoJobs"
                    
                    # Filtro manual de calidad
                    validos = ["back", "office", "admin", "auxiliar", "gestión", "recep", "postventa", "director", "mando"]
                    if not any(k in raw_titulo.lower() for k in validos):
                        continue
                        
                    titulo = html.escape(raw_titulo)
                    mensaje = (f"🔵 <b>¡NUEVA OFERTA EN INFOJOBS!</b>\n\n📌 <b>Puesto:</b> {titulo}\n🕒 <b>Filtro:</b> 24h / Remoto\n\n🔗 <a href='{link}'>Postularse</a>")
                    if enviar_telegram(mensaje): OFERTAS_VISTAS.add(job_id); nuevas += 1
            except Exception: continue
        return nuevas
    except Exception as e: 
        print(f"Error InfoJobs: {e}")
        return 0

def buscar_tecnoempleo(query):
    print(f"Revisando TecnoEmpleo para: {query}...")
    q_enc = query.replace(" ", "+")
    url_te = f"https://www.tecnoempleo.com/busqueda-empleo.php?te={q_enc}&re=1&f=24h"
    try:
        time.sleep(random.uniform(2, 4))
        res = curl_requests.get(url_te, impersonate="chrome120", timeout=30)
        if res.status_code != 200: return 0
        soup = BeautifulSoup(res.text, 'html.parser')
        offers = soup.find_all('h3')
        nuevas = 0
        for offer in offers:
            try:
                link_tag = offer.find('a')
                if not link_tag: continue
                link = link_tag['href']
                job_id = "tecno_" + (re.search(r'rf-([a-zA-Z0-9]+)', link).group(1) if re.search(r'rf-([a-zA-Z0-9]+)', link) else str(hash(link)))
                if job_id not in OFERTAS_VISTAS:
                    titulo = html.escape(link_tag.text.strip())
                    mensaje = (f"💻 <b>¡NUEVA OFERTA EN TECNOEMPLEO!</b>\n\n📌 <b>Puesto:</b> {titulo}\n🕒 <b>Filtro:</b> 24h / Remoto\n\n🔗 <a href='{link}'>Postularse</a>")
                    if enviar_telegram(mensaje): OFERTAS_VISTAS.add(job_id); nuevas += 1
            except Exception: continue
        return nuevas
    except Exception as e: 
        print(f"Error TecnoEmpleo: {e}")
        return 0

def buscar_jobtoday(query):
    print(f"Revisando JobToday para: {query}...")
    q_enc = query.replace(" ", "+")
    url_jt = f"https://jobtoday.com/es/jobs?q={q_enc}+remoto"
    try:
        time.sleep(random.uniform(2, 4))
        res = curl_requests.get(url_jt, impersonate="chrome120", timeout=30)
        if res.status_code != 200: return 0
        soup = BeautifulSoup(res.text, 'html.parser')
        links = soup.find_all('a', href=re.compile(r'/job/|/trabajo/'))
        nuevas = 0
        for link_tag in links:
            try:
                href = "https://jobtoday.com" + link_tag['href'] if not link_tag['href'].startswith('http') else link_tag['href']
                raw_text = link_tag.text.strip()
                if "remoto" not in raw_text.lower() and "teletrabajo" not in raw_text.lower(): continue
                job_id = "jt_" + (re.search(r'/([A-Z0-9]+)$', href).group(1) if re.search(r'/([A-Z0-9]+)$', href) else str(hash(href)))
                if job_id not in OFERTAS_VISTAS:
                    titulo = html.escape(re.split(r'\d+\s+(minutos|horas|días)', raw_text)[0].strip())
                    mensaje = (f"📱 <b>¡NUEVA OFERTA EN JOBTODAY!</b>\n\n📌 <b>Puesto:</b> {titulo}\n🕒 <b>Filtro:</b> Remoto\n\n🔗 <a href='{href}'>Postularse</a>")
                    if enviar_telegram(mensaje): OFERTAS_VISTAS.add(job_id); nuevas += 1
            except Exception: continue
        return nuevas
    except Exception as e: 
        print(f"Error JobToday: {e}")
        return 0

def buscar_glassdoor(query):
    print(f"Revisando Glassdoor para: {query}...")
    q_enc = query.replace(" ", "-")
    url_gd = f"https://www.glassdoor.es/Job/espana-{q_enc}-jobs-SRCH_IL.0,6_IN219.htm?fromAge=1"
    try:
        time.sleep(random.uniform(3, 5))
        res = curl_requests.get(url_gd, impersonate="chrome120", timeout=30)
        if res.status_code != 200: return 0
        soup = BeautifulSoup(res.text, 'html.parser')
        job_links = soup.find_all('a', attrs={'data-test': 'job-link'})
        nuevas = 0
        for link_tag in job_links:
            try:
                href = "https://www.glassdoor.es" + link_tag['href'] if not link_tag['href'].startswith('http') else link_tag['href']
                job_id = "gd_" + (re.search(r'jl=(\d+)', href).group(1) if re.search(r'jl=(\d+)', href) else str(hash(href)))
                if job_id not in OFERTAS_VISTAS:
                    titulo = html.escape(link_tag.get('aria-label') or link_tag.text.strip())
                    mensaje = (f"📊 <b>¡NUEVA OFERTA EN GLASSDOOR!</b>\n\n📌 <b>Puesto:</b> {titulo}\n🕒 <b>Filtro:</b> Reciente / Remoto\n\n🔗 <a href='{href}'>Postularse</a>")
                    if enviar_telegram(mensaje): OFERTAS_VISTAS.add(job_id); nuevas += 1
            except Exception: continue
        return nuevas
    except Exception as e: 
        print(f"Error Glassdoor: {e}")
        return 0

def buscar_manfred():
    print("Revisando Manfred...")
    url_mf = "https://www.getmanfred.com/ofertas-empleo?onlyActive=true&remote=100"
    try:
        time.sleep(random.uniform(2, 4))
        res = curl_requests.get(url_mf, impersonate="chrome120", timeout=30)
        if res.status_code != 200: return 0
        soup = BeautifulSoup(res.text, 'html.parser')
        offers = soup.find_all(['h2', 'h3'])
        nuevas = 0
        for offer in offers:
            try:
                link_tag = offer.find('a') or offer.find_parent('a')
                if not link_tag: continue
                href = "https://www.getmanfred.com" + link_tag['href'] if not link_tag['href'].startswith('http') else link_tag['href']
                if '/ofertas/' not in href: continue
                titulo = html.escape(offer.text.strip())
                validos = ["back office", "admin", "postventa", "director", "mando"]
                if not any(k in titulo.lower() for k in validos): continue
                job_id = "mf_" + href.split('/')[-1]
                if job_id not in OFERTAS_VISTAS:
                    mensaje = (f"🦄 <b>¡NUEVA OFERTA EN MANFRED!</b>\n\n📌 <b>Puesto:</b> {titulo}\n🏢 <b>Empresa:</b> Manfred\n🕒 <b>Filtro:</b> 100% Remoto\n\n🔗 <a href='{href}'>Postularse</a>")
                    if enviar_telegram(mensaje): OFERTAS_VISTAS.add(job_id); nuevas += 1
            except Exception: continue
        return nuevas
    except Exception as e: 
        print(f"Error Manfred: {e}")
        return 0

def buscar_jooble(query):
    print(f"Revisando Jooble para: {query}...")
    q_enc = query.replace(" ", "-")
    url_jb = f"https://es.jooble.org/trabajo-{q_enc}-remoto/España?date=1"
    try:
        time.sleep(random.uniform(4, 6))
        res = curl_requests.get(url_jb, impersonate="chrome120", timeout=30)
        if res.status_code != 200: return 0
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.find_all('article')
        nuevas = 0
        for item in items:
            try:
                link_tag = item.find('a', href=re.compile(r'/desc/|/external/'))
                if not link_tag: continue
                href = "https://es.jooble.org" + link_tag['href'] if not link_tag['href'].startswith('http') else link_tag['href']
                job_id = "jb_" + (re.search(r'-(\d+)$', href).group(1) if re.search(r'-(\d+)$', href) else str(hash(href)))
                if job_id not in OFERTAS_VISTAS:
                    titulo = html.escape(link_tag.text.strip())
                    mensaje = (f"🔍 <b>¡NUEVA OFERTA EN JOOBLE!</b>\n\n📌 <b>Puesto:</b> {titulo}\n🕒 <b>Filtro:</b> Remoto\n\n🔗 <a href='{href}'>Postularse</a>")
                    if enviar_telegram(mensaje): OFERTAS_VISTAS.add(job_id); nuevas += 1
            except Exception: continue
        return nuevas
    except Exception as e: 
        print(f"Error Jooble: {e}")
        return 0

def ejecutar_todas():
    total = 0
    terminos = ["Back Office", "Postventa"]
    
    for term in terminos:
        total += buscar_linkedin(term)
        total += buscar_infojobs(term)
        total += buscar_tecnoempleo(term)
        total += buscar_indeed(term)
        total += buscar_jobtoday(term)
        total += buscar_glassdoor(term)
        total += buscar_jooble(term)
    
    # Manfred no usa buscador por ahora, se llama una vez
    total += buscar_manfred()
    
    if total == 0:
        enviar_telegram("🔎 <b>Búsqueda finalizada</b>\n\n0 ofertas nuevas encontradas en las últimas 24h.")
    else:
        enviar_telegram(f"✅ <b>Búsqueda completada</b>\n\nSe han encontrado <b>{total}</b> ofertas nuevas entre todas las categorías.")

if __name__ == "__main__":
    print("🤖 Iniciando rastreo...")
    ejecutar_todas()
    guardar_vistas(OFERTAS_VISTAS)
    print("✅ Proceso completado.")
