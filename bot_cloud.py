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

def buscar_linkedin():
    print("Revisando LinkedIn...")
    url_lp = "https://www.linkedin.com/jobs/search/?currentJobId=4369673774&f_TPR=r86400&f_WT=2&geoId=105646813&keywords=Back%20Office&origin=JOB_SEARCH_PAGE_LOCATION_HISTORY&refresh=true"
    try:
        res = requests.get(url_lp, headers=HEADERS, timeout=15)
        if res.status_code != 200: return
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

def buscar_indeed():
    print("Revisando Indeed...")
    url_in = "https://es.indeed.com/jobs?q=back+office&l=espa%C3%B1a&fromage=1&sc=0kf%3Aattr%28DS7X8%29%3B"
    try:
        time.sleep(random.uniform(2, 5))
        res = curl_requests.get(url_in, impersonate="chrome120", timeout=30)
        if res.status_code != 200: return
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

def buscar_infojobs():
    print("Revisando InfoJobs...")
    # InfoJobs: backoffice remoto ordenado por fecha últimas 24h (history=1)
    url_ij = "https://www.infojobs.net/ofertas-trabajo?keyword=backoffice&teleworkingIds=3&sortBy=PUBLICATION_DATE&history=1"
    try:
        time.sleep(random.uniform(2, 4))
        res = curl_requests.get(url_ij, impersonate="chrome120", timeout=30)
        if res.status_code != 200: return
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
                    
                    # Filtro manual de calidad para asegurar que sea backoffice o relacionado
                    if not any(k in raw_titulo.lower() for k in ["back", "office", "admin", "auxiliar", "gestión", "recep"]):
                        continue
                        
                    titulo = html.escape(raw_titulo)
                    mensaje = (f"🔵 <b>¡NUEVA OFERTA EN INFOJOBS!</b>\n\n📌 <b>Puesto:</b> {titulo}\n🕒 <b>Filtro:</b> 24h / Remoto\n\n🔗 <a href='{link}'>Postularse</a>")
                    if enviar_telegram(mensaje): OFERTAS_VISTAS.add(job_id); nuevas += 1
            except Exception: continue
        return nuevas
    except Exception as e: 
        print(f"Error InfoJobs: {e}")
        return 0

def buscar_tecnoempleo():
    print("Revisando TecnoEmpleo...")
    url_te = "https://www.tecnoempleo.com/busqueda-empleo.php?te=back+office&re=1&f=24h"
    try:
        time.sleep(random.uniform(2, 4))
        res = curl_requests.get(url_te, impersonate="chrome120", timeout=30)
        if res.status_code != 200: return
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

def buscar_jobtoday():
    print("Revisando JobToday...")
    url_jt = "https://jobtoday.com/es/jobs?q=back+office+remoto"
    try:
        time.sleep(random.uniform(2, 4))
        res = curl_requests.get(url_jt, impersonate="chrome120", timeout=30)
        if res.status_code != 200: return
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

def buscar_glassdoor():
    print("Revisando Glassdoor...")
    url_gd = "https://www.glassdoor.es/Job/espana-back-office-jobs-SRCH_IL.0,6_IN219_KO7,18.htm?fromAge=1"
    try:
        time.sleep(random.uniform(3, 5))
        res = curl_requests.get(url_gd, impersonate="chrome120", timeout=30)
        if res.status_code != 200: return
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
        if res.status_code != 200: return
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
                if "back office" not in titulo.lower() and "admin" not in titulo.lower(): continue
                job_id = "mf_" + href.split('/')[-1]
                if job_id not in OFERTAS_VISTAS:
                    mensaje = (f"🦄 <b>¡NUEVA OFERTA EN MANFRED!</b>\n\n📌 <b>Puesto:</b> {titulo}\n🏢 <b>Empresa:</b> Manfred\n🕒 <b>Filtro:</b> 100% Remoto\n\n🔗 <a href='{href}'>Postularse</a>")
                    if enviar_telegram(mensaje): OFERTAS_VISTAS.add(job_id); nuevas += 1
            except Exception: continue
        return nuevas
    except Exception as e: 
        print(f"Error Manfred: {e}")
        return 0

def buscar_jooble():
    print("Revisando Jooble...")
    url_jb = "https://es.jooble.org/trabajo-back-office-remoto/España?date=1"
    try:
        time.sleep(random.uniform(4, 6))
        res = curl_requests.get(url_jb, impersonate="chrome120", timeout=30)
        if res.status_code != 200: return
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
    total += buscar_linkedin()
    total += buscar_infojobs()
    total += buscar_tecnoempleo()
    total += buscar_indeed()
    total += buscar_jobtoday()
    total += buscar_glassdoor()
    total += buscar_manfred()
    total += buscar_jooble()
    
    if total == 0:
        enviar_telegram("🔎 <b>Búsqueda finalizada</b>\n\n0 ofertas encontradas en las últimas 24h.")
    else:
        enviar_telegram(f"✅ <b>Búsqueda completada</b>\n\nSe han encontrado <b>{total}</b> ofertas nuevas.")

if __name__ == "__main__":
    print("🤖 Iniciando rastreo...")
    ejecutar_todas()
    guardar_vistas(OFERTAS_VISTAS)
    print("✅ Proceso completado.")
