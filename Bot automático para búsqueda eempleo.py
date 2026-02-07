import requests
from bs4 import BeautifulSoup
import time
import schedule
import html

# --- TUS DATOS CONFIGURADOS ---
TOKEN = "8290995613:AAFfckFmKlMSUpgaFOvkxu9jzaJahf0ZX-I"
# IMPORTANTE: CHAT_ID debe ser TU ID de usuario, no el ID del bot.
# Puedes obtener tu ID enviando un mensaje a @userinfobot en Telegram.
CHAT_ID = "276483510" 
OFERTAS_VISTAS = set()

# Headers para que LinkedIn crea que somos un navegador real
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensaje,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code != 200:
            print(f"Error de Telegram (Status {response.status_code}): {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error enviando a Telegram: {e}")
        return False

def buscar_linkedin():
    print("Revisando LinkedIn...")
    url_lp = "https://www.linkedin.com/jobs/search/?currentJobId=4369673774&f_TPR=r86400&f_WT=2&geoId=105646813&keywords=Back%20Office&origin=JOB_SEARCH_PAGE_LOCATION_HISTORY&refresh=true"
    
    try:
        res = requests.get(url_lp, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            print(f"Error: LinkedIn devolvió status {res.status_code}")
            return

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
                    
                    if not titulo_elem or not empresa_elem or not link_elem:
                        continue

                    titulo = html.escape(titulo_elem.text.strip())
                    empresa = html.escape(empresa_elem.text.strip())
                    link = link_elem['href']
                    
                    mensaje = (
                        f"🚀 <b>¡NUEVA OFERTA EN LINKEDIN!</b>\n\n"
                        f"📌 <b>Puesto:</b> {titulo}\n"
                        f"🏢 <b>Empresa:</b> {empresa}\n"
                        f"🕒 <b>Filtro:</b> Últimas 24h / Remoto\n\n"
                        f"🔗 <a href='{link}'>Postularse aquí</a>"
                    )
                    
                    if enviar_telegram(mensaje):
                        OFERTAS_VISTAS.add(job_id)
                        nuevas += 1
            except Exception:
                continue
        
        if nuevas > 0:
            print(f"✅ Se enviaron {nuevas} ofertas nuevas de LinkedIn.")
        else:
            print("No se encontraron ofertas nuevas en LinkedIn.")
                
    except Exception as e:
        print(f"Error en el scraping de LinkedIn: {e}")

from curl_cffi import requests as curl_requests
import random

def buscar_indeed():
    print("Revisando Indeed...")
    url_in = "https://es.indeed.com/jobs?q=back+office&l=espa%C3%B1a&fromage=1&sc=0kf%3Aattr%28DS7X8%29%3B"
    
    try:
        # Añadimos un pequeño delay aleatorio inicial
        time.sleep(random.uniform(2, 5))
        
        # Usamos curl_requests con impersonate para imitar un navegador real a nivel de conexión
        res = curl_requests.get(
            url_in, 
            impersonate="chrome120",
            timeout=30
        )
        
        if res.status_code != 200:
            print(f"Error: Indeed devolvió status {res.status_code}")
            if res.status_code == 403:
                print("💡 Indeed sigue bloqueando. Es posible que la IP requiera un tiempo de descanso.")
            return

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
                    empresa = html.escape(empresa_elem.text.strip()) if empresa_elem else "Empresa no especificada"
                    link = "https://es.indeed.com" + link_tag['href']
                    
                    mensaje = (
                        f"🔥 <b>¡NUEVA OFERTA EN INDEED!</b>\n\n"
                        f"📌 <b>Puesto:</b> {titulo}\n"
                        f"🏢 <b>Empresa:</b> {empresa}\n"
                        f"🕒 <b>Filtro:</b> Últimas 24h / Remoto\n\n"
                        f"🔗 <a href='{link}'>Postularse aquí</a>"
                    )
                    
                    if enviar_telegram(mensaje):
                        OFERTAS_VISTAS.add(job_id)
                        nuevas += 1
            except Exception:
                continue
        
        if nuevas > 0:
            print(f"✅ Se enviaron {nuevas} ofertas nuevas de Indeed.")
        else:
            print("Indeed: No se encontraron ofertas nuevas.")
                
    except Exception as e:
        print(f"Error en el scraping de Indeed: {e}")

import re

def buscar_infojobs():
    print("Revisando InfoJobs...")
    # URL actualizada para evitar errores 500
    url_ij = "https://www.infojobs.net/ofertas-trabajo?keyword=backoffice&teleworkingIds=3&sortBy=PUBLICATION_DATE"
    
    try:
        time.sleep(random.uniform(2, 4))
        # InfoJobs a veces prefiere headers más explícitos
        headers_ij = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9",
        }
        
        res = curl_requests.get(
            url_ij, 
            headers=headers_ij,
            impersonate="chrome120",
            timeout=30
        )
        
        if res.status_code != 200:
            print(f"Error: InfoJobs devolvió status {res.status_code}")
            if res.status_code == 500:
                print("💡 El servidor de InfoJobs dio un error interno. Puede ser un problema temporal o con los filtros.")
            return

        soup = BeautifulSoup(res.text, 'html.parser')
        # Buscamos todos los links que apunten a ofertas
        links_ofertas = soup.find_all('a', href=re.compile(r'/of-i'))
        print(f"InfoJobs: Se detectaron {len(links_ofertas)} enlaces de ofertas en la página.")
        
        nuevas = 0
        encontrados_en_esta_vuelta = set()
        
        for link_tag in links_ofertas:
            try:
                link = link_tag['href']
                if not link.startswith('http'):
                    link = "https:" + link if link.startswith('//') else "https://www.infojobs.net" + link
                
                # Extraemos un ID único de la URL
                match = re.search(r'of-i([a-zA-Z0-9]+)', link)
                if not match: continue
                
                job_id = "infojobs_" + match.group(1)
                
                # Evitar procesar el mismo link varias veces (si hay varios en la misma tarjeta)
                if job_id in encontrados_en_esta_vuelta: continue
                encontrados_en_esta_vuelta.add(job_id)
                
                if job_id not in OFERTAS_VISTAS:
                    # Buscamos el contenedor para sacar más info
                    parent = link_tag.find_parent(['li', 'div'], class_=re.compile(r'ij-'))
                    
                    raw_titulo = link_tag.text.strip()
                    if not raw_titulo: # A veces el link es una imagen/logo
                        titulo_elem = parent.find(['h2', 'h1']) if parent else None
                        raw_titulo = titulo_elem.text.strip() if titulo_elem else "Puesto sin título"
                    
                    # Filtro manual de calidad para asegurar que sea backoffice o relacionado
                    if not any(k in raw_titulo.lower() for k in ["back", "office", "admin", "auxiliar", "gestión", "recep"]):
                        continue
                    
                    titulo = html.escape(raw_titulo)
                    empresa = "Empresa no especificada"
                    if parent:
                        empresa_elem = parent.find(['h3', 'span'], class_=re.compile(r'subtitle|company|name'))
                        if empresa_elem:
                            empresa = html.escape(empresa_elem.text.strip())
                    
                    mensaje = (
                        f"🔵 <b>¡NUEVA OFERTA EN INFOJOBS!</b>\n\n"
                        f"📌 <b>Puesto:</b> {titulo}\n"
                        f"🏢 <b>Empresa:</b> {empresa}\n"
                        f"🕒 <b>Filtro:</b> Últimas 24h / Remoto\n\n"
                        f"🔗 <a href='{link}'>Postularse aquí</a>"
                    )
                    
                    if enviar_telegram(mensaje):
                        OFERTAS_VISTAS.add(job_id)
                        nuevas += 1
            except Exception:
                continue
        
        if nuevas > 0:
            print(f"✅ Se enviaron {nuevas} ofertas nuevas de InfoJobs (Total detectadas: {len(links_ofertas)}).")
        else:
            print(f"InfoJobs: No se encontraron ofertas nuevas (Total detectadas: {len(links_ofertas)}).")
                
    except Exception as e:
        print(f"Error en el scraping de InfoJobs: {e}")

def buscar_tecnoempleo():
    print("Revisando TecnoEmpleo...")
    # URL: Back Office, Teletrabajo, Últimas 24h
    url_te = "https://www.tecnoempleo.com/busqueda-empleo.php?te=back+office&re=1&f=24h"
    
    try:
        time.sleep(random.uniform(2, 4))
        res = curl_requests.get(url_te, impersonate="chrome120", timeout=30)
        
        if res.status_code != 200:
            print(f"Error: TecnoEmpleo devolvió status {res.status_code}")
            return

        soup = BeautifulSoup(res.text, 'html.parser')
        # Las ofertas están en h3 con links
        offers = soup.find_all('h3')
        
        nuevas = 0
        for offer in offers:
            try:
                link_tag = offer.find('a')
                if not link_tag: continue
                
                link = link_tag['href']
                titulo = html.escape(link_tag.text.strip())
                
                # ID único (suele terminar en rf-...)
                match = re.search(r'rf-([a-zA-Z0-9]+)', link)
                job_id = "tecno_" + match.group(1) if match else "tecno_id_" + str(hash(link))
                
                if job_id not in OFERTAS_VISTAS:
                    # Empresa: buscamos link que contenga "-trabajo" o "/re-" cerca
                    parent = offer.find_parent('div')
                    empresa = "Empresa no especificada"
                    if parent:
                        c_tag = parent.find('a', href=re.compile(r'-trabajo|/re-'))
                        if c_tag and c_tag.text.strip():
                            empresa = html.escape(c_tag.text.strip())
                    
                    mensaje = (
                        f"💻 <b>¡NUEVA OFERTA EN TECNOEMPLEO!</b>\n\n"
                        f"📌 <b>Puesto:</b> {titulo}\n"
                        f"🏢 <b>Empresa:</b> {empresa}\n"
                        f"🕒 <b>Filtro:</b> Últimas 24h / Remoto\n\n"
                        f"🔗 <a href='{link}'>Postularse aquí</a>"
                    )
                    
                    if enviar_telegram(mensaje):
                        OFERTAS_VISTAS.add(job_id)
                        nuevas += 1
            except Exception:
                continue
        
        if nuevas > 0:
            print(f"✅ Se enviaron {nuevas} ofertas nuevas de TecnoEmpleo.")
        else:
            print("TecnoEmpleo: No se encontraron ofertas nuevas.")
                
    except Exception as e:
        print(f"Error en el scraping de TecnoEmpleo: {e}")

def buscar_jobtoday():
    print("Revisando JobToday...")
    # URL: Back Office
    url_jt = "https://jobtoday.com/es/jobs?q=back+office"
    
    try:
        time.sleep(random.uniform(2, 4))
        res = curl_requests.get(url_jt, impersonate="chrome120", timeout=30)
        
        if res.status_code != 200:
            print(f"Error: JobToday devolvió status {res.status_code}")
            return

        soup = BeautifulSoup(res.text, 'html.parser')
        # Buscamos links de trabajo
        links = soup.find_all('a', href=re.compile(r'/job/|/trabajo/'))
        
        nuevas = 0
        vistos_en_ciclo = set()
        
        for link_tag in links:
            try:
                href = link_tag['href']
                if not href.startswith('http'):
                    href = "https://jobtoday.com" + href
                
                # ID único de JobToday (código al final)
                match = re.search(r'/([A-Z0-9]+)$', href)
                job_id = "jt_" + match.group(1) if match else "jt_id_" + str(hash(href))
                
                if job_id in vistos_en_ciclo: continue
                vistos_en_ciclo.add(job_id)
                
                if job_id not in OFERTAS_VISTAS:
                    # Título: El texto suele ser largo, limpiamos
                    raw_text = link_tag.text.strip()
                    # El título suele ser hasta el primer salto de línea o "hace X..."
                    titulo = html.escape(re.split(r'\d+\s+(minutos|horas|días|minute|hour|day)', raw_text)[0].strip())
                    
                    # Filtro manual de remoto si no viene en la URL
                    if "remoto" not in raw_text.lower() and "teletrabajo" not in raw_text.lower():
                        # A veces el remoto está en el título o descripción, si no, saltamos
                        # Para ser conservadores, si el usuario pidió remoto, filtramos aquí
                        continue

                    # Empresa
                    parent = link_tag.find_parent(['div', 'article'])
                    empresa = "Empresa no especificada"
                    if parent:
                        spans = parent.find_all('span')
                        for s in spans:
                            text = s.text.strip()
                            if text and text != raw_text and len(text) < 50:
                                empresa = html.escape(text)
                                break
                    
                    mensaje = (
                        f"📱 <b>¡NUEVA OFERTA EN JOBTODAY!</b>\n\n"
                        f"📌 <b>Puesto:</b> {titulo}\n"
                        f"🏢 <b>Empresa:</b> {empresa}\n"
                        f"🕒 <b>Filtro:</b> Remoto\n\n"
                        f"🔗 <a href='{href}'>Postularse aquí</a>"
                    )
                    
                    if enviar_telegram(mensaje):
                        OFERTAS_VISTAS.add(job_id)
                        nuevas += 1
            except Exception:
                continue
        
        if nuevas > 0:
            print(f"✅ Se enviaron {nuevas} ofertas nuevas de JobToday.")
        else:
            print("JobToday: No se encontraron ofertas nuevas.")
                
    except Exception as e:
        print(f"Error en el scraping de JobToday: {e}")

def buscar_glassdoor():
    print("Revisando Glassdoor...")
    # URL: Back Office, España, Últimas 24h (fromAge=1)
    url_gd = "https://www.glassdoor.es/Job/espana-back-office-jobs-SRCH_IL.0,6_IN219_KO7,18.htm?fromAge=1"
    
    try:
        time.sleep(random.uniform(3, 5))
        res = curl_requests.get(url_gd, impersonate="chrome120", timeout=30)
        
        if res.status_code != 200:
            print(f"Error: Glassdoor devolvió status {res.status_code}")
            return

        soup = BeautifulSoup(res.text, 'html.parser')
        # Glassdoor usa data-test para sus elementos principales
        job_links = soup.find_all('a', attrs={'data-test': 'job-link'})
        
        nuevas = 0
        for link_tag in job_links:
            try:
                href = link_tag['href']
                if not href.startswith('http'):
                    href = "https://www.glassdoor.es" + href
                
                # ID único de Glassdoor (suele estar en el enlace)
                match = re.search(r'jl=(\d+)', href)
                job_id = "gd_" + match.group(1) if match else "gd_id_" + str(hash(href))
                
                if job_id not in OFERTAS_VISTAS:
                    titulo = html.escape(link_tag.get('aria-label') or link_tag.text.strip())
                    if not titulo: continue
                    
                    # Empresa
                    parent = link_tag.find_parent(['li', 'div'])
                    empresa = "Empresa no especificada"
                    if parent:
                        comp_elem = parent.find(attrs={'data-test': 'employer-shortname'})
                        if comp_elem:
                            empresa = html.escape(comp_elem.text.strip())
                    
                    mensaje = (
                        f"📊 <b>¡NUEVA OFERTA EN GLASSDOOR!</b>\n\n"
                        f"📌 <b>Puesto:</b> {titulo}\n"
                        f"🏢 <b>Empresa:</b> {empresa}\n"
                        f"🕒 <b>Filtro:</b> Reciente\n\n"
                        f"🔗 <a href='{href}'>Postularse aquí</a>"
                    )
                    
                    if enviar_telegram(mensaje):
                        OFERTAS_VISTAS.add(job_id)
                        nuevas += 1
            except Exception:
                continue
        
        print(f"Glassdoor: {nuevas} ofertas nuevas enviadas.")
    except Exception as e:
        print(f"Error en Glassdoor: {e}")

def buscar_manfred():
    print("Revisando Manfred...")
    # Manfred es muy pro-remoto, buscamos directamente sus ofertas activas
    url_mf = "https://www.getmanfred.com/ofertas-empleo?onlyActive=true&remote=100"
    
    try:
        time.sleep(random.uniform(2, 4))
        res = curl_requests.get(url_mf, impersonate="chrome120", timeout=30)
        
        if res.status_code != 200:
            print(f"Error: Manfred devolvió status {res.status_code}")
            return

        soup = BeautifulSoup(res.text, 'html.parser')
        # Buscamos artículos o headers que contengan links de ofertas
        offers = soup.find_all(['h2', 'h3'])
        
        nuevas = 0
        for offer in offers:
            try:
                link_tag = offer.find('a') or offer.find_parent('a')
                if not link_tag: continue
                
                href = link_tag['href']
                if '/ofertas/' not in href: continue
                if not href.startswith('http'):
                    href = "https://www.getmanfred.com" + href
                
                titulo = html.escape(offer.text.strip())
                if "back office" not in titulo.lower() and "admin" not in titulo.lower():
                    # Manfred es muy tech, si no es explícito, saltamos para evitar ruido
                    continue

                job_id = "mf_" + href.split('/')[-1]
                
                if job_id not in OFERTAS_VISTAS:
                    mensaje = (
                        f"🦄 <b>¡NUEVA OFERTA EN MANFRED!</b>\n\n"
                        f"📌 <b>Puesto:</b> {titulo}\n"
                        f"🏢 <b>Empresa:</b> Manfred Platform\n"
                        f"🕒 <b>Filtro:</b> 100% Remoto\n\n"
                        f"🔗 <a href='{href}'>Postularse aquí</a>"
                    )
                    
                    if enviar_telegram(mensaje):
                        OFERTAS_VISTAS.add(job_id)
                        nuevas += 1
            except Exception:
                continue
        print(f"Manfred: {nuevas} ofertas nuevas enviadas.")
    except Exception as e:
        print(f"Error en Manfred: {e}")

def buscar_jooble():
    print("Revisando Jooble...")
    # Jooble es un agregador, buscamos por términos específicos
    url_jb = "https://es.jooble.org/trabajo-back-office-remoto/España"
    
    try:
        time.sleep(random.uniform(4, 6))
        # Jooble a veces detecta curl_cffi, probamos con cloudscraper si falla
        res = curl_requests.get(url_jb, impersonate="chrome120", timeout=30)
        
        if res.status_code != 200:
            print(f"Jooble Status {res.status_code}, intentando alternativa...")
            return

        soup = BeautifulSoup(res.text, 'html.parser')
        # Jooble usa artículos para las ofertas
        items = soup.find_all('article')
        
        nuevas = 0
        for item in items:
            try:
                link_tag = item.find('a', href=re.compile(r'/desc/|/external/'))
                if not link_tag: continue
                
                href = link_tag['href']
                if not href.startswith('http'):
                    href = "https://es.jooble.org" + href
                
                job_id = "jb_" + (re.search(r'-(\d+)$', href).group(1) if re.search(r'-(\d+)$', href) else str(hash(href)))
                
                if job_id not in OFERTAS_VISTAS:
                    titulo = html.escape(link_tag.text.strip())
                    # Empresa suele estar en un div/span secundario
                    empresa = "Empresa no especificada"
                    comp_elem = item.find(class_=re.compile(r'company|employer', re.I))
                    if comp_elem: empresa = html.escape(comp_elem.text.strip())
                    
                    mensaje = (
                        f"🔍 <b>¡NUEVA OFERTA EN JOOBLE!</b>\n\n"
                        f"📌 <b>Puesto:</b> {titulo}\n"
                        f"🏢 <b>Empresa:</b> {empresa}\n"
                        f"🕒 <b>Filtro:</b> Remoto (Agregador)\n\n"
                        f"🔗 <a href='{href}'>Postularse aquí</a>"
                    )
                    
                    if enviar_telegram(mensaje):
                        OFERTAS_VISTAS.add(job_id)
                        nuevas += 1
            except Exception:
                continue
        print(f"Jooble: {nuevas} ofertas nuevas enviadas.")
    except Exception as e:
        print(f"Error en Jooble: {e}")

def ejecutar_todas():
    # Ordenamos por fiabilidad/calidad
    plataformas = [
        ("LinkedIn", buscar_linkedin),
        ("InfoJobs", buscar_infojobs),
        ("TecnoEmpleo", buscar_tecnoempleo),
        ("Indeed", buscar_indeed),
        ("JobToday", buscar_jobtoday),
        ("Glassdoor", buscar_glassdoor),
        ("Manfred", buscar_manfred),
        ("Jooble", buscar_jooble)
    ]
    
    for nombre, func in plataformas:
        try:
            func()
            time.sleep(random.uniform(5, 10)) # Pausas naturales
        except Exception as e:
            print(f"Error ejecutando {nombre}: {e}")

# --- PROGRAMACIÓN ---
schedule.every(10).minutes.do(ejecutar_todas)

if __name__ == "__main__":
    print("🤖 Agente iniciado. Presiona Ctrl+C para detener.")
    # startup_msg = "✅ <b>Agente de Empleo activado</b>\nBuscando en LinkedIn, Indeed e InfoJobs cada 10 minutos..."
    # if not enviar_telegram(startup_msg):
    #     print("⚠️ ALERTA: No se pudo enviar el mensaje inicial a Telegram. Revisa el CHAT_ID.")
    
    ejecutar_todas()
    
    while True:
        schedule.run_pending()
        time.sleep(1)