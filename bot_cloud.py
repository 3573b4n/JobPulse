import requests
from bs4 import BeautifulSoup
import time
import html
import os
import re
import random
import json
from curl_cffi import requests as curl_requests

# --- CONFIGURACIÓN PARA GITHUB ACTIONS ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
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

def enviar_telegram(mensaje):
    if not TOKEN or not CHAT_ID: return False
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "HTML"}
    try:
        response = requests.post(url, data=payload, timeout=10)
        return response.status_code == 200
    except: return False

# --- FUNCIÓN DE PETICIÓN SEGURA (BYPASS 403) ---
def peticion_segura(url, impersonate="chrome120"):
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9",
        "Referer": "https://www.google.com/",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Upgrade-Insecure-Requests": "1"
    }
    return curl_requests.get(url, impersonate=impersonate, headers=headers, timeout=30)

# --- FUNCIONES DE BÚSQUEDA ---

def buscar_linkedin(query):
    print(f"Buscando LinkedIn: {query}...")
    q_enc = query.replace(" ", "%20")
    url = f"https://www.linkedin.com/jobs/search/?f_TPR=r86400&f_WT=2&keywords={q_enc}&location=Spain"
    try:
        res = peticion_segura(url)
        if res.status_code != 200: return 0, f"LinkedIn: {res.status_code}"
        soup = BeautifulSoup(res.text, 'html.parser')
        jobs = soup.find_all('div', class_=re.compile(r'base-card|job-search-card'))
        nuevas = 0
        for job in jobs:
            try:
                job_id = "ln_" + (job.get('data-entity-urn') or job.get('data-id') or str(hash(job.text[:30])))
                if job_id not in OFERTAS_VISTAS:
                    titulo_elem = job.find(['h3', 'h2'])
                    empresa_elem = job.find(['h4', 'span'], class_=re.compile(r'subtitle|company'))
                    link_elem = job.find('a')
                    if not titulo_elem or not link_elem: continue
                    link = link_elem['href'].split('?')[0]
                    mensaje = f"🚀 <b>NUEVA EN LINKEDIN</b>\n\n📌 {html.escape(titulo_elem.text.strip())}\n🏢 {html.escape(empresa_elem.text.strip()) if empresa_elem else '?'}\n\n🔗 <a href='{link}'>Ver oferta</a>"
                    if enviar_telegram(mensaje): OFERTAS_VISTAS.add(job_id); nuevas += 1
            except: continue
        return nuevas, None
    except Exception as e: return 0, f"LinkedIn: {str(e)}"

def buscar_indeed(query):
    print(f"Buscando Indeed: {query}...")
    q_enc = query.replace(" ", "+")
    # Usamos URL de móvil que suele ser más permisiva con el 403
    url = f"https://es.indeed.com/m/jobs?q={q_enc}&l=España&fromage=1"
    try:
        time.sleep(random.uniform(2, 4))
        res = peticion_segura(url, impersonate="chrome110")
        if res.status_code != 200: return 0, f"Indeed: {res.status_code}"
        soup = BeautifulSoup(res.text, 'html.parser')
        jobs = soup.find_all(['div', 'a'], class_=re.compile(r'job_seen_beacon|result'))
        nuevas = 0
        for job in jobs:
            try:
                link_tag = job.find('a') if job.name == 'div' else job
                if not link_tag or 'jk=' not in link_tag.get('href', ''): continue
                jk = re.search(r'jk=([a-zA-Z0-9]+)', link_tag['href']).group(1)
                job_id = "in_" + jk
                if job_id not in OFERTAS_VISTAS:
                    titulo = html.escape(job.text.strip()[:100])
                    link = f"https://es.indeed.com/viewjob?jk={jk}"
                    mensaje = f"🔥 <b>NUEVA EN INDEED</b>\n\n📌 {titulo}\n\n🔗 <a href='{link}'>Ver oferta</a>"
                    if enviar_telegram(mensaje): OFERTAS_VISTAS.add(job_id); nuevas += 1
            except: continue
        return nuevas, None
    except Exception as e: return 0, f"Indeed: {str(e)}"

def buscar_infojobs(query):
    print(f"Buscando InfoJobs: {query}...")
    q_enc = query.replace(" ", "%20")
    url = f"https://www.infojobs.net/ofertas-trabajo?keyword={q_enc}&teleworkingIds=3&sortBy=PUBLICATION_DATE"
    try:
        res = peticion_segura(url)
        if res.status_code != 200: return 0, f"InfoJobs: {res.status_code}"
        soup = BeautifulSoup(res.text, 'html.parser')
        links = soup.find_all('a', href=re.compile(r'/of-i'))
        nuevas = 0
        for link_tag in links:
            try:
                href = link_tag['href']
                job_id = "ij_" + re.search(r'of-i([a-zA-Z0-9]+)', href).group(1)
                if job_id not in OFERTAS_VISTAS:
                    titulo = link_tag.text.strip()
                    if not any(k in titulo.lower() for k in ["back", "office", "admin", "postventa", "director", "mando"]): continue
                    mensaje = f"🔵 <b>NUEVA EN INFOJOBS</b>\n\n📌 {html.escape(titulo)}\n\n🔗 <a href='{href}'>Ver oferta</a>"
                    if enviar_telegram(mensaje): OFERTAS_VISTAS.add(job_id); nuevas += 1
            except: continue
        return nuevas, None
    except Exception as e: return 0, f"InfoJobs: {str(e)}"

def buscar_glassdoor(query):
    print(f"Buscando Glassdoor: {query}...")
    q_enc = query.replace(" ", "-")
    url = f"https://www.glassdoor.es/Job/espana-{q_enc}-jobs-SRCH_IL.0,6_IN219.htm?fromAge=1"
    try:
        time.sleep(random.uniform(3, 5))
        res = peticion_segura(url, impersonate="chrome110")
        if res.status_code != 200: return 0, f"Glassdoor: {res.status_code}"
        soup = BeautifulSoup(res.text, 'html.parser')
        job_links = soup.find_all('a', attrs={'data-test': 'job-link'})
        nuevas = 0
        for link in job_links:
            try:
                href = link['href']
                job_id = "gd_" + (re.search(r'jl=(\d+)', href).group(1) if 'jl=' in href else str(hash(href)))
                if job_id not in OFERTAS_VISTAS:
                    titulo = html.escape(link.text.strip())
                    mensaje = f"📊 <b>NUEVA EN GLASSDOOR</b>\n\n📌 {titulo}\n\n🔗 <a href='https://www.glassdoor.es{href}'>Ver oferta</a>"
                    if enviar_telegram(mensaje): OFERTAS_VISTAS.add(job_id); nuevas += 1
            except: continue
        return nuevas, None
    except Exception as e: return 0, f"Glassdoor: {str(e)}"

def buscar_manfred():
    url = "https://www.getmanfred.com/ofertas-empleo?onlyActive=true&remote=100"
    try:
        res = peticion_segura(url)
        if res.status_code != 200: return 0, f"Manfred: {res.status_code}"
        soup = BeautifulSoup(res.text, 'html.parser')
        offers = soup.find_all(['h2', 'h3'])
        nuevas = 0
        for offer in offers:
            try:
                titulo = offer.text.strip()
                if not any(k in titulo.lower() for k in ["back office", "admin", "postventa", "director", "mando"]): continue
                link_tag = offer.find('a') or offer.find_parent('a')
                href = "https://www.getmanfred.com" + link_tag['href']
                job_id = "mf_" + href.split('/')[-1]
                if job_id not in OFERTAS_VISTAS:
                    mensaje = f"🦄 <b>NUEVA EN MANFRED</b>\n\n📌 {html.escape(titulo)}\n\n🔗 <a href='{href}'>Ver oferta</a>"
                    if enviar_telegram(mensaje): OFERTAS_VISTAS.add(job_id); nuevas += 1
            except: continue
        return nuevas, None
    except Exception as e: return 0, f"Manfred: {str(e)}"

def buscar_jooble(query):
    print(f"Buscando Jooble: {query}...")
    q_enc = query.replace(" ", "%20")
    # URL internacional para evitar bloqueos regionales
    url = f"https://es.jooble.org/trabajo?q={q_enc}&l=España"
    try:
        time.sleep(random.uniform(4, 6))
        res = peticion_segura(url, impersonate="chrome110")
        if res.status_code != 200: return 0, f"Jooble: {res.status_code}"
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.find_all('article')
        nuevas = 0
        for item in items:
            try:
                link_tag = item.find('a')
                if not link_tag or '/desc/' not in link_tag.get('href', ''): continue
                href = link_tag['href']
                job_id = "jb_" + str(hash(href))
                if job_id not in OFERTAS_VISTAS:
                    titulo = html.escape(link_tag.text.strip())
                    mensaje = f"🔍 <b>NUEVA EN JOOBLE</b>\n\n📌 {titulo}\n\n🔗 <a href='{href}'>Ver oferta</a>"
                    if enviar_telegram(mensaje): OFERTAS_VISTAS.add(job_id); nuevas += 1
            except: continue
        return nuevas, None
    except Exception as e: return 0, f"Jooble: {str(e)}"

def ejecutar_todas():
    total = 0
    errores = []
    terminos = ["Back Office", "Postventa"]
    rastreadores = [
        ("LinkedIn", buscar_linkedin), ("InfoJobs", buscar_infojobs), 
        ("Indeed", buscar_indeed), ("Glassdoor", buscar_glassdoor), ("Jooble", buscar_jooble)
    ]
    for term in terminos:
        for nombre, func in rastreadores:
            n, err = func(term)
            total += n
            if err: errores.append(err)
            time.sleep(2)
    
    n, err = buscar_manfred()
    total += n
    if err: errores.append(err)

    if total > 0:
        enviar_telegram(f"✅ <b>Búsqueda completada</b>\nSe han enviado <b>{total}</b> ofertas nuevas.")
    else:
        enviar_telegram("🔎 <b>Búsqueda finalizada</b>\nSin ofertas nuevas en las últimas 24h.")
        
    if errores:
        resumen = "\n".join([f"• {e}" for e in list(set(errores))])
        enviar_telegram(f"⚠️ <b>AVISO DE SISTEMA</b>\nFallos en:\n{resumen}")

if __name__ == "__main__":
    ejecutar_todas()
    guardar_vistas(OFERTAS_VISTAS)
