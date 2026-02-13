import requests
from bs4 import BeautifulSoup
import time
import html
import os
import re
import random
from curl_cffi import requests as curl_requests

# --- CONFIGURACIÓN ---
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
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "HTML", "disable_web_page_preview": False}
    try:
        res = requests.post(url, data=payload, timeout=10)
        return res.status_code == 200
    except: return False

def peticion(url):
    return curl_requests.get(url, impersonate="chrome110", timeout=30)

def es_oferta_valida(titulo, ubicacion_raw):
    titulo = titulo.lower()
    ubicacion = (ubicacion_raw or "").lower()
    keywords = ["back", "office", "postventa", "post-venta", "admin", "gestión", "mando", "director", "auxiliar"]
    if not any(k in titulo for k in keywords): return False
    es_remoto = any(x in ubicacion or x in titulo for x in ["remoto", "teletrabajo", "100%", "home office", "distancia"])
    es_murcia = "murcia" in ubicacion or "murcia" in titulo
    return es_remoto or es_murcia

# --- RASTREADORES ---

def buscar_linkedin(query):
    q_enc = query.replace(" ", "%20")
    url = f"https://www.linkedin.com/jobs/search/?f_TPR=r86400&keywords={q_enc}&location=Spain"
    try:
        res = peticion(url)
        if res.status_code != 200: return 0
        soup = BeautifulSoup(res.text, 'html.parser')
        jobs = soup.find_all('div', class_=re.compile(r'base-card|job-search-card'))
        nuevas = 0
        for job in jobs:
            try:
                titulo = job.find(['h3', 'h2']).text.strip()
                ubi = job.find('span', class_='job-search-card__location').text.strip()
                if es_oferta_valida(titulo, ubi):
                    job_id = "ln_" + (job.get('data-entity-urn') or str(hash(titulo)))
                    if job_id not in OFERTAS_VISTAS:
                        link = job.find('a')['href'].split('?')[0]
                        if enviar_telegram(f"🚀 <b>LINKEDIN</b>\n📌 {titulo}\n📍 {ubi}\n🔗 <a href='{link}'>Postularse</a>"):
                            OFERTAS_VISTAS.add(job_id); nuevas += 1
            except: continue
        return nuevas
    except: return 0

def buscar_infojobs(query):
    q_enc = query.replace(" ", "%20")
    url = f"https://www.infojobs.net/ofertas-trabajo?keyword={q_enc}&sortBy=PUBLICATION_DATE"
    try:
        res = peticion(url)
        if res.status_code != 200: return 0
        soup = BeautifulSoup(res.text, 'html.parser')
        links = soup.find_all('a', href=re.compile(r'/of-i'))
        nuevas = 0
        for link_tag in links:
            try:
                href = link_tag['href']
                if not href.startswith('http'): href = "https://www.infojobs.net" + href
                titulo = link_tag.text.strip()
                if es_oferta_valida(titulo, "Remoto Murcia"):
                    job_id = "ij_" + (re.search(r'of-i([a-zA-Z0-9]+)', href).group(1) if 'of-i' in href else str(hash(href)))
                    if job_id not in OFERTAS_VISTAS:
                        if enviar_telegram(f"🔵 <b>INFOJOBS</b>\n📌 {html.escape(titulo)}\n🔗 <a href='{href}'>Postularse</a>"):
                            OFERTAS_VISTAS.add(job_id); nuevas += 1
            except: continue
        return nuevas
    except: return 0

def buscar_tecnoempleo(query):
    q_enc = query.replace(" ", "+")
    url = f"https://www.tecnoempleo.com/busqueda-empleo.php?te={q_enc}&f=24h"
    try:
        res = peticion(url)
        if res.status_code != 200: return 0
        soup = BeautifulSoup(res.text, 'html.parser')
        offers = soup.find_all('div', class_='p-2') 
        nuevas = 0
        for off in offers:
            try:
                title_tag = off.find('h3')
                if not title_tag: continue
                titulo = title_tag.text.strip()
                link = title_tag.find('a')['href']
                if not link.startswith('http'): link = "https://www.tecnoempleo.com/" + link
                ubi = off.get_text().strip()
                if es_oferta_valida(titulo, ubi):
                    job_id = "te_" + str(hash(link))
                    if job_id not in OFERTAS_VISTAS:
                        if enviar_telegram(f"💻 <b>TECNOEMPLEO</b>\n📌 {titulo}\n🔗 <a href='{link}'>Postularse</a>"):
                            OFERTAS_VISTAS.add(job_id); nuevas += 1
            except: continue
        return nuevas
    except: return 0

def buscar_jobtoday(query):
    q_enc = query.replace(" ", "+")
    url = f"https://jobtoday.com/es/jobs?q={q_enc}+murcia"
    try:
        res = peticion(url)
        if res.status_code != 200: return 0
        soup = BeautifulSoup(res.text, 'html.parser')
        links = soup.find_all('a', href=re.compile(r'/job/|/trabajo/'))
        nuevas = 0
        for link in links:
            try:
                href = link['href']
                if not href.startswith('http'): href = "https://jobtoday.com" + href
                titulo = link.text.strip().split("\n")[0]
                if es_oferta_valida(titulo, "Remoto Murcia"):
                    job_id = "jt_" + str(hash(href))
                    if job_id not in OFERTAS_VISTAS:
                        if enviar_telegram(f"📱 <b>JOBTODAY</b>\n📌 {titulo}\n🔗 <a href='{href}'>Postularse</a>"):
                            OFERTAS_VISTAS.add(job_id); nuevas += 1
            except: continue
        return nuevas
    except: return 0

def buscar_manfred():
    url = "https://www.getmanfred.com/ofertas-empleo?onlyActive=true"
    try:
        res = peticion(url)
        if res.status_code != 200: return 0
        soup = BeautifulSoup(res.text, 'html.parser')
        offers = soup.find_all(['h2', 'h3'])
        nuevas = 0
        for offer in offers:
            try:
                titulo = offer.text.strip()
                if es_oferta_valida(titulo, "Remoto"):
                    link_tag = offer.find_parent('a') or offer.find('a')
                    href = link_tag['href']
                    if not href.startswith('http'): href = "https://www.getmanfred.com" + href
                    job_id = "mf_" + href.split('/')[-1]
                    if job_id not in OFERTAS_VISTAS:
                        if enviar_telegram(f"🦄 <b>MANFRED</b>\n📌 {titulo}\n🔗 <a href='{href}'>Postularse</a>"):
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
        enviar_telegram(f"✅ <b>Búsqueda finalizada</b>\nSe han enviado <b>{total}</b> ofertas nuevas.")

if __name__ == "__main__":
    ejecutar_todas()
    guardar_vistas(OFERTAS_VISTAS)

