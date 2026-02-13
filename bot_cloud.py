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
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        res = requests.post(url, data=payload, timeout=10)
        return res.status_code == 200
    except: return False

def peticion_pro(url, imp="chrome110"):
    # curl_cffi maneja automáticamente los headers para que coincidan con la huella TLS
    return curl_requests.get(url, impersonate=imp, timeout=30)

# --- RASTREADORES ---

def buscar_linkedin(query):
    q_enc = query.replace(" ", "%20")
    url = f"https://www.linkedin.com/jobs/search/?f_TPR=r86400&f_WT=2&keywords={q_enc}&location=Spain"
    try:
        res = peticion_pro(url)
        if res.status_code != 200: return 0, f"LinkedIn: {res.status_code}"
        soup = BeautifulSoup(res.text, 'html.parser')
        jobs = soup.find_all('div', class_=re.compile(r'base-card|job-search-card'))
        nuevas = 0
        for job in jobs:
            try:
                job_id = "ln_" + (job.get('data-entity-urn') or str(hash(job.text[:20])))
                if job_id not in OFERTAS_VISTAS:
                    t_el = job.find(['h3', 'h2'])
                    if not t_el: continue
                    t = t_el.text.strip()
                    l = job.find('a')['href'].split('?')[0]
                    if enviar_telegram(f"🚀 <b>LINKEDIN</b>\n📌 {t}\n🔗 <a href='{l}'>Ver</a>"):
                        OFERTAS_VISTAS.add(job_id); nuevas += 1
            except: continue
        return nuevas, None
    except Exception as e: return 0, f"LinkedIn: {str(e)}"

def buscar_infojobs(query):
    q_enc = query.replace(" ", "%20")
    url = f"https://www.infojobs.net/ofertas-trabajo?keyword={q_enc}&teleworkingIds=3&sortBy=PUBLICATION_DATE"
    try:
        res = peticion_pro(url)
        if res.status_code != 200: return 0, f"InfoJobs: {res.status_code}"
        soup = BeautifulSoup(res.text, 'html.parser')
        links = soup.find_all('a', href=re.compile(r'/of-i'))
        nuevas = 0
        for link in links:
            try:
                href = link['href']
                match = re.search(r'of-i([a-zA-Z0-9]+)', href)
                if not match: continue
                job_id = "ij_" + match.group(1)
                if job_id not in OFERTAS_VISTAS:
                    titulo = link.text.strip()
                    if not any(k in titulo.lower() for k in ["back", "office", "admin", "postventa", "director", "mando"]): continue
                    if enviar_telegram(f"🔵 <b>INFOJOBS</b>\n📌 {html.escape(titulo)}\n🔗 <a href='{href}'>Ver</a>"):
                        OFERTAS_VISTAS.add(job_id); nuevas += 1
            except: continue
        return nuevas, None
    except Exception as e: return 0, f"InfoJobs: {str(e)}"

def buscar_indeed(query):
    q_enc = query.replace(" ", "+")
    url = f"https://es.indeed.com/jobs?q={q_enc}&l=España&fromage=1"
    try:
        time.sleep(random.uniform(2, 4))
        res = peticion_pro(url, imp="safari_15_3") # Safari suele tener menos problemas en Indeed
        if res.status_code != 200: return 0, f"Indeed: {res.status_code}"
        soup = BeautifulSoup(res.text, 'html.parser')
        jobs = soup.find_all('div', class_=re.compile(r'job_seen_beacon'))
        nuevas = 0
        for job in jobs:
            try:
                link_tag = job.find('a', href=re.compile(r'/rc/|/pagead/'))
                if not link_tag: continue
                jk = re.search(r'jk=([a-zA-Z0-9]+)', link_tag['href']).group(1)
                job_id = "in_" + jk
                if job_id not in OFERTAS_VISTAS:
                    titulo = job.find('h2').text.strip()
                    link = f"https://es.indeed.com/viewjob?jk={jk}"
                    if enviar_telegram(f"🔥 <b>INDEED</b>\n📌 {titulo}\n🔗 <a href='{link}'>Ver</a>"):
                        OFERTAS_VISTAS.add(job_id); nuevas += 1
            except: continue
        return nuevas, None
    except Exception as e: return 0, f"Indeed: {str(e)}"

def buscar_tecnoempleo(query):
    q_enc = query.replace(" ", "+")
    url = f"https://www.tecnoempleo.com/busqueda-empleo.php?te={q_enc}&re=1&f=24h"
    try:
        res = peticion_pro(url)
        if res.status_code != 200: return 0, f"TecnoEmpleo: {res.status_code}"
        soup = BeautifulSoup(res.text, 'html.parser')
        offers = soup.find_all('h3')
        nuevas = 0
        for offer in offers:
            try:
                link = offer.find('a')['href']
                job_id = "te_" + str(hash(link))
                if job_id not in OFERTAS_VISTAS:
                    t = offer.text.strip()
                    if enviar_telegram(f"💻 <b>TECNOEMPLEO</b>\n📌 {t}\n🔗 <a href='{link}'>Ver</a>"):
                        OFERTAS_VISTAS.add(job_id); nuevas += 1
            except: continue
        return nuevas, None
    except Exception as e: return 0, f"TecnoEmpleo: {str(e)}"

def buscar_jobtoday(query):
    q_enc = query.replace(" ", "+")
    url = f"https://jobtoday.com/es/jobs?q={q_enc}+remoto"
    try:
        res = peticion_pro(url)
        if res.status_code != 200: return 0, f"JobToday: {res.status_code}"
        soup = BeautifulSoup(res.text, 'html.parser')
        links = soup.find_all('a', href=re.compile(r'/job/|/trabajo/'))
        nuevas = 0
        for link in links:
            try:
                href = "https://jobtoday.com" + link['href']
                if "remoto" not in link.text.lower() and "teletrabajo" not in link.text.lower(): continue
                job_id = "jt_" + str(hash(href))
                if job_id not in OFERTAS_VISTAS:
                    t = link.text.strip().split("\n")[0]
                    if enviar_telegram(f"📱 <b>JOBTODAY</b>\n📌 {t}\n🔗 <a href='{href}'>Ver</a>"):
                        OFERTAS_VISTAS.add(job_id); nuevas += 1
            except: continue
        return nuevas, None
    except Exception as e: return 0, f"JobToday: {str(e)}"

def buscar_glassdoor(query):
    q_enc = query.replace(" ", "-")
    url = f"https://www.glassdoor.es/Job/espana-{q_enc}-jobs-SRCH_IL.0,6_IN219.htm?fromAge=1"
    try:
        time.sleep(random.uniform(3, 5))
        res = peticion_pro(url, imp="chrome110") 
        if res.status_code != 200: return 0, f"Glassdoor: {res.status_code}"
        soup = BeautifulSoup(res.text, 'html.parser')
        links = soup.find_all('a', attrs={'data-test': 'job-link'})
        nuevas = 0
        for link in links:
            try:
                href = "https://www.glassdoor.es" + link['href']
                job_id = "gd_" + str(hash(href))
                if job_id not in OFERTAS_VISTAS:
                    t = link.text.strip()
                    if enviar_telegram(f"📊 <b>GLASSDOOR</b>\n📌 {t}\n🔗 <a href='{href}'>Ver</a>"):
                        OFERTAS_VISTAS.add(job_id); nuevas += 1
            except: continue
        return nuevas, None
    except Exception as e: return 0, f"Glassdoor: {str(e)}"

def buscar_manfred():
    url = "https://www.getmanfred.com/ofertas-empleo?onlyActive=true&remote=100"
    try:
        res = peticion_pro(url)
        if res.status_code != 200: return 0, f"Manfred: {res.status_code}"
        soup = BeautifulSoup(res.text, 'html.parser')
        offers = soup.find_all(['h2', 'h3'])
        nuevas = 0
        for offer in offers:
            try:
                t = offer.text.strip()
                if not any(k in t.lower() for k in ["back office", "admin", "postventa", "director", "mando"]): continue
                href = "https://www.getmanfred.com" + offer.find_parent('a')['href']
                job_id = "mf_" + href.split('/')[-1]
                if job_id not in OFERTAS_VISTAS:
                    if enviar_telegram(f"🦄 <b>MANFRED</b>\n📌 {t}\n🔗 <a href='{href}'>Ver</a>"):
                        OFERTAS_VISTAS.add(job_id); nuevas += 1
            except: continue
        return nuevas, None
    except Exception as e: return 0, f"Manfred: {str(e)}"

def buscar_jooble(query):
    q_enc = query.replace(" ", "%20")
    url = f"https://es.jooble.org/trabajo?q={q_enc}&l=España"
    try:
        time.sleep(random.uniform(2, 4))
        res = peticion_pro(url, imp="chrome116")
        if res.status_code != 200: return 0, f"Jooble: {res.status_code}"
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = soup.find_all('article')
        nuevas = 0
        for art in articles:
            try:
                link = art.find('a')
                if not link or '/desc/' not in link['href']: continue
                href = link['href']
                job_id = "jb_" + str(hash(href))
                if job_id not in OFERTAS_VISTAS:
                    t = link.text.strip()
                    if enviar_telegram(f"🔍 <b>JOOBLE</b>\n📌 {t}\n🔗 <a href='{href}'>Ver</a>"):
                        OFERTAS_VISTAS.add(job_id); nuevas += 1
            except: continue
        return nuevas, None
    except Exception as e: return 0, f"Jooble: {str(e)}"

def ejecutar_todas():
    total = 0
    errores = []
    terminos = ["Back Office", "Postventa"]
    rastreadores = [
        ("LinkedIn", buscar_linkedin), ("InfoJobs", buscar_infojobs), 
        ("TecnoEmpleo", buscar_tecnoempleo), ("JobToday", buscar_jobtoday),
        ("Indeed", buscar_indeed), ("Glassdoor", buscar_glassdoor), ("Jooble", buscar_jooble)
    ]
    for term in terminos:
        for nombre, func in rastreadores:
            try:
                n, err = func(term)
                total += n
                if err: errores.append(err)
                time.sleep(3)
            except Exception as e:
                errores.append(f"{nombre}: {str(e)}")
    
    try:
        n, err = buscar_manfred()
        total += n
        if err: errores.append(err)
    except Exception as e:
        errores.append(f"Manfred: {str(e)}")

    if total > 0:
        enviar_telegram(f"✅ <b>Ciclo Finalizado</b>\nSe han enviado <b>{total}</b> ofertas nuevas.")
    else:
        enviar_telegram("🔎 <b>Ciclo Finalizado</b>\nSin ofertas nuevas en este turno.")
        
    if errores:
        resumen = "\n".join([f"• {e}" for e in list(set(errores))])
        enviar_telegram(f"⚠️ <b>ESTADO DE PLATAFORMAS</b>\n{resumen}")

if __name__ == "__main__":
    ejecutar_todas()
    guardar_vistas(OFERTAS_VISTAS)
