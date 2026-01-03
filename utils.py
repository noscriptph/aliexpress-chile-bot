import hashlib
import time
import requests
import os
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import analizador
import ia_local

load_dotenv()
APP_KEY = os.getenv("ALI_APP_KEY")
APP_SECRET = os.getenv("ALI_APP_SECRET")

def obtener_firma(params):
    """Algoritmo de firma oficial de AliExpress."""
    sorted_params = sorted(params.items())
    query_string = "".join(f"{k}{v}" for k, v in sorted_params)
    sign_str = f"{APP_SECRET}{query_string}{APP_SECRET}"
    return hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()

def extraer_nombre_e_imagen(url):
    """Extrae metadatos y maneja redirecciones de links de afiliados."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "es-CL,es;q=0.9"
        }
        
        # MANEJO DE LINKS CORTOS (s.click / a.aliexpress)
        if "aliexpress.com" in url and ("/e/" in url or "s.click" in url):
            print("   [Utils] Siguiendo redirección de link corto...")
            r_head = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
            url = r_head.url

        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        meta_titulo = soup.find("meta", property="og:title")
        titulo = meta_titulo["content"] if meta_titulo else (soup.title.string if soup.title else "Producto")
        
        meta_imagen = soup.find("meta", property="og:image")
        imagen = meta_imagen["content"] if meta_imagen else None
        
        titulo_limpio = titulo.split('|')[0].split('-')[0].strip()
        return titulo_limpio, imagen, url
    except Exception as e:
        print(f"   [Error Web] Fallo al extraer datos base: {e}")
        return "Producto", None, url

def investigar_mejor_oferta(entrada, callback_status=None):
    """
    Motor de búsqueda universal. 
    'entrada' puede ser una URL (Modo Bot) o un Texto (Modo Cazador).
    """
    es_url = "http" in entrada
    debug_info = {
        "ia_activa": False,
        "termino_usado": "",
        "total_encontrados": 0,
        "mensajes": [],
        "error": None
    }

    # --- FASE 1: OBTENCIÓN DE KEYWORDS ---
    intentos_keywords = []

    if es_url:
        # Lógica para URL (Telegram)
        nombre_sucio, foto_original, url_real = extraer_nombre_e_imagen(entrada)
        
        # 1. IA
        termino_ia = ia_local.analizar_con_ia(nombre_sucio)
        if termino_ia:
            termino_ia = re.sub(r'[^a-zA-Z0-9\s]', '', termino_ia).strip()
            if len(termino_ia) > 2:
                intentos_keywords.append({"termino": termino_ia, "fuente": "Gemma 3 (IA)"})
                debug_info["ia_activa"] = True
        
        # 2. Analizador de Reglas
        termino_reglas = analizador.limpiar_titulo(nombre_sucio)
        if termino_reglas and termino_reglas not in [i["termino"] for i in intentos_keywords]:
            intentos_keywords.append({"termino": termino_reglas, "fuente": "Analizador (Reglas)"})

        # 3. Failsafe
        if not intentos_keywords:
            recorte = " ".join(nombre_sucio.split()[:3])
            intentos_keywords.append({"termino": recorte, "fuente": "Recorte Directo"})
    else:
        # Lógica para Texto Directo (Cazador)
        intentos_keywords.append({"termino": entrada, "fuente": "Búsqueda Directa"})

    # --- FASE 2: BÚSQUEDA MULTI-NIVEL ---
    niveles = [
        ("Premium", 0.12, 2.5),
        ("Estándar Chile", 0.28, 4.2),
        ("Carga Pesada", 0.45, 180.0)
    ]

    for nombre_nivel, umbral_pct, umbral_fijo in niveles:
        msg = f"🔍 <b>Nivel {nombre_nivel}:</b> Buscando mejores precios..."
        if callback_status: callback_status(msg)
        debug_info["mensajes"].append(msg)

        for kw in intentos_keywords:
            termino = kw["termino"]
            fuente_kw = kw["fuente"]
            debug_info["termino_usado"] = termino

            endpoint = "https://gw.api.alibaba.com/openapi/param2/2/portals.open/api.product.query/" + APP_KEY
            params = {
                "app_key": APP_KEY, "format": "json",
                "method": "aliexpress.affiliate.product.query",
                "keywords": termino, "ship_to_country": "CL",
                "sort": "VOLUME_HIGH", "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "v": "2.0", "sign_method": "md5"
            }
            params["sign"] = obtener_firma(params)

            try:
                response = requests.get(endpoint, params=params, timeout=12)
                data = response.json()
                res_root = data.get("aliexpress_affiliate_product_query_response", {})
                productos = res_root.get("resp_result", {}).get("result", {}).get("products", [])
                
                debug_info["total_encontrados"] = len(productos)

                for p in productos:
                    precio = float(p.get('target_sale_price', 0))
                    envio = float(p.get('target_shipping_fee', 0))
                    
                    if precio > 0:
                        es_valido = False
                        if precio < 15:
                            if envio <= umbral_fijo: es_valido = True
                        else:
                            if envio <= (precio * umbral_pct): es_valido = True
                        
                        if es_valido:
                            msg_exito = f"✅ Éxito en {nombre_nivel} con '{termino}'"
                            debug_info["mensajes"].append(msg_exito)
                            return {
                                "link": p['promotion_link'],
                                "precio": precio,
                                "envio": envio,
                                "foto": p['product_main_image_url'],
                                "titulo": p['product_title'],
                                "fuente_exito": f"{fuente_kw} ({nombre_nivel})"
                            }, debug_info
                
            except Exception as e:
                debug_info["error"] = str(e)
                print(f"   [Error API] {e}")

    return None, debug_info