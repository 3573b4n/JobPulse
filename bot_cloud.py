import requests
from bs4 import BeautifulSoup
import time
import html
import os
import re
import random
from curl_cffi import requests as curl_requests

# --- CONFIGURACIÓN ESTABLE ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DB_FILE = "ofertas_vistas.txt"

def cargar_vistas():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return set(f.read().splitlines())
        except: return set()
    return set()

def guardar_vistas(vistas):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(list(vistas)))
    except: pass

OFERTAS_VISTAS = cargar_vistas()

def enviar_telegram(mensaje):
    if not TOKEN or not CHAT_ID: return False
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        res = requests.post(url, data=payload, timeout=10)
        return res.status_code == 200
    except: return False

def peticion(url):
    # Uso de impersonate fijo para máxima estabilidad
    headers = {"Accept-Language": "es-ES,es;q=0.9"}
    return curl_requests.get(url, impersonate="chrome110", headers=headers, timeout=30)

# --- RASTREADORES ---

def buscar_linkedin(query):
    q_enc = query.replace(" ", "%20")
    url = f"https://www.linkedin.com/jobs/search/?f_TPR=r86400&f_WT=2&keywords={q_enc}&location=Spain"
    try:
        res = peticion(url)
        if res.status_code != 200: return 0
        soup = BeautifulSoup(res.text, 'html.parser')
        jobs = soup.find_all('div', class_=re.compile(r'base-card|job-search-card'))
        nuevas = 0
        for job in jobs:
            try:
                job_id = "ln_" + (job.get('data-entity-urn') or str(hash(job.text[:20])))
                if job_id not in OFERTAS_VISTAS:
                    titulo = job.find(['h3', 'h2']).text.strip()
                    link = job.find('a')['href'].split('?')[0]
                    msg = f"🚀 <b>LINKEDIN</b>\n📌 {titulo}\n🔗 <a href='{link}'>Ver Oferta</a>"
                    if enviar_telegram(msg): OFERTAS_VISTAS.add(job_id); nuevas += 1
            except: continue
        return nuevas
    except: return 0

def buscar_infojobs(query):
    q_enc = query.replace(" ", "%20")
    url = f"https://www.infojobs.net/ofertas-trabajo?keyword={q_enc}&teleworkingIds=3&sortBy=PUBLICATION_DATE"
    try:
        res = peticion(url)
        if res.status_code != 200: return 0
        soup = BeautifulSoup(res.text, 'html.parser')
        links = soup.find_all('a', href=re.compile(r'/of-i'))
        nuevas = 0
        for link in links:
            try:
                href = link['href']
                match = re.search(r'of-i([a-zA-Z0-9]+)', href)
                if match:
                    job_id = "ij_" + match.group(1)
                    if job_id not in OFERTAS_VISTAS:
                        t = link.text.strip()
                        # Filtro de calidad
                        if any(k in t.lower() for k in ["back", "office", "admin", "postventa", "director", "mando", "auxiliar", "gestión"]):
                            if enviar_telegram(f"🔵 <b>INFOJOBS</b>\n📌 {html.escape(t)}\n🔗 <a href='{href}'>Ver Oferta</a>"):
                                OFERTAS_VISTAS.add(job_id); nuevas += 1
            except: continue
        return nuevas
    except: return 0

def buscar_tecnoempleo(query):
    q_enc = query.replace(" ", "+")
    url = f"https://www.tecnoempleo.com/busqueda-empleo.php?te={q_enc}&re=1&f=24h"
    try:
        res = peticion(url)
        if res.status_code != 200: return 0
        soup = BeautifulSoup(res.text, 'html.parser')
        offers = soup.find_all('h3')
        nuevas = 0
        for offer in offers:
            try:
                link = offer.find('a')['href']
                job_id = "te_" + str(hash(link))
                if job_id not in OFERTAS_VISTAS:
                    t = offer.text.strip()
                    if enviar_telegram(f"💻 <b>TECNOEMPLEO</b>\n📌 {t}\n🔗 <a href='{link}'>Ver Oferta</a>"):
                        OFERTAS_VISTAS.add(job_id); nuevas += 1
            except: continue
        return nuevas
    except: return 0

def buscar_jobtoday(query):
    q_enc = query.replace(" ", "+")
    url = f"https://jobtoday.com/es/jobs?q={q_enc}+remoto"
    try:
        res = peticion(url)
        if res.status_code != 200: return 0
        soup = BeautifulSoup(res.text, 'html.parser')
        links = soup.find_all('a', href=re.compile(r'/job/|/trabajo/'))
        nuevas = 0
        for link in links:
            try:
                href = "https://jobtoday.com" + link['href']
                txt = link.text.lower()
                if "remoto" not in txt and "teletrabajo" not in txt: continue
                job_id = "jt_" + str(hash(href))
                if job_id not in OFERTAS_VISTAS:
                    t = link.text.strip().split("\n")[0]
                    if enviar_telegram(f"📱 <b>JOBTODAY</b>\n📌 {t}\n🔗 <a href='{href}'>Ver Oferta</a>"):
                        OFERTAS_VISTAS.add(job_id); nuevas += 1
            except: continue
        return nuevas
    except: return 0

def buscar_manfred():
    url = "https://www.getmanfred.com/ofertas-empleo?onlyActive=true&remote=100"
    try:
        res = peticion(url)
        if res.status_code != 200: return 0
        soup = BeautifulSoup(res.text, 'html.parser')
        offers = soup.find_all(['h2', 'h3'])
        nuevas = 0
        for offer in offers:
            try:
                t = offer.text.strip().lower()
                if any(k in t for k in ["back office", "admin", "postventa", "director", "mando", "gestión"]):
                    href = "https://www.getmanfred.com" + offer.find_parent('a')['href']
                    job_id = "mf_" + href.split('/')[-1]
                    if job_id not in OFERTAS_VISTAS:
                        if enviar_telegram(f"🦄 <b>MANFRED</b>\n📌 {t.upper()}\n🔗 <a href='{href}'>Ver Oferta</a>"):
                            OFERTAS_VISTAS.add(job_id); nuevas += 1
            except: continue
        return nuevas
    except: return 0

def ejecutar_todas():
    total = 0
    terminos = ["Back Office", "Postventa"]
    
    for term in terminos:
        total += buscar_linkedin(term)
        total += buscar_infojobs(term)
        total += buscar_tecnoempleo(term)
        total += buscar_jobtoday(term)
        time.sleep(2)
    
    total += buscar_manfred()

    if total > 0:
        enviar_telegram(f"✅ <b>Ciclo de Búsqueda Finalizado</b>\nHe encontrado y enviado <b>{total}</b> ofertas nuevas.")
    else:
        # Solo enviamos mensaje si quieres saber que sigue vivo, o lo comentamos para menos ruido
        print("Sin ofertas nuevas.")

if __name__ == "__main__":
    ejecutar_todas()
    guardar_vistas(OFERTAS_VISTAS)
