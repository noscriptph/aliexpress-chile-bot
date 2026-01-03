import hashlib
import time
import requests
import os
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import analizador  # Tu analizador universal
import ia_local   # El archivo que conecta con Ollama

load_dotenv()
APP_KEY = os.getenv("ALI_APP_KEY")
APP_SECRET = os.getenv("ALI_APP_SECRET")
TRACKING_ID = "telegram_chile_bot"

def obtener_firma(params):
    """Algoritmo de firma oficial de AliExpress."""
    sorted_params = sorted(params.items())
    query_string = "".join(f"{k}{v}" for k, v in sorted_params)
    sign_str = f"{APP_SECRET}{query_string}{APP_SECRET}"
    return hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()

def extraer_nombre_e_imagen(url):
    """Extrae datos básicos del HTML de AliExpress."""
    try:
        print("   [Utils] Extrayendo metadatos del link original...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "es-CL,es;q=0.9"
        }
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        meta_titulo = soup.find("meta", property="og:title")
        if meta_titulo:
            titulo = meta_titulo["content"]
        else:
            titulo = soup.title.string if soup.title else "Producto AliExpress"
        
        meta_imagen = soup.find("meta", property="og:image")
        imagen = meta_imagen["content"] if meta_imagen else None
        
        # Limpieza básica para evitar ruidos en el análisis
        titulo_limpio = titulo.split('|')[0].split('-')[0].strip()
        return titulo_limpio, imagen
    except Exception as e:
        print(f"   [Error Web] Fallo al extraer datos base: {e}")
        return "Producto", None

def investigar_mejor_oferta(url_original):
    """
    Coordina la limpieza (IA/Manual) y realiza búsquedas en cascada.
    """
    nombre_sucio, foto_original = extraer_nombre_e_imagen(url_original)
    
    debug_info = {
        "ia_activa": False,
        "termino_usado": "",
        "total_encontrados": 0,
        "error": None
    }

    # --- FASE 1: GENERAR TÉRMINOS DE BÚSQUEDA ---
    print(f"   [Proceso] Analizando: '{nombre_sucio[:50]}...'")
    
    intentos_busqueda = []
    
    # 1. Intentar con IA (Gemma 3 27b)
    termino_ia = ia_local.analizar_con_ia(nombre_sucio)
    if termino_ia:
        # Normalizar: Solo letras, números y espacios
        termino_ia = re.sub(r'[^a-zA-Z0-9\s]', '', termino_ia).strip()
        if len(termino_ia) > 3:
            intentos_busqueda.append({"termino": termino_ia, "fuente": "Gemma 3 (IA)"})
            debug_info["ia_activa"] = True
    
    # 2. Respaldo con Analizador de Reglas
    termino_manual = analizador.limpiar_titulo(nombre_sucio)
    termino_manual = re.sub(r'[^a-zA-Z0-9\s]', '', termino_manual).strip()
    
    # Solo añadir si es útil y diferente al de la IA
    if termino_manual and termino_manual not in [i["termino"] for i in intentos_busqueda]:
        intentos_busqueda.append({"termino": termino_manual, "fuente": "Analizador (Reglas)"})

    # 3. Caso especial: Si no hay nada, usar el inicio del título sucio (último recurso)
    if not intentos_busqueda:
        recorte = " ".join(nombre_sucio.split()[:3])
        intentos_busqueda.append({"termino": recorte, "fuente": "Recorte Directo"})

    # --- FASE 2: EJECUCIÓN EN CASCADA ---
    for idx, intento in enumerate(intentos_busqueda):
        termino = intento["termino"]
        fuente = intento["fuente"]
        
        print(f"   [API] Intento {idx+1}: Buscando '{termino}' ({fuente})...")
        debug_info["termino_usado"] = termino # Actualizar para el reporte de Telegram

        endpoint = "https://gw.api.alibaba.com/openapi/param2/2/portals.open/api.product.query/" + APP_KEY
        params = {
            "app_key": APP_KEY,
            "format": "json",
            "method": "aliexpress.affiliate.product.query",
            "keywords": termino,
            "ship_to_country": "CL",
            "sort": "VOLUME_HIGH",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "v": "2.0",
            "sign_method": "md5"
        }
        params["sign"] = obtener_firma(params)

        try:
            response = requests.get(endpoint, params=params, timeout=12)
            data = response.json()
            
            # Navegación segura del JSON
            query_res = data.get("aliexpress_affiliate_product_query_response", {})
            resp_result = query_res.get("resp_result", {})
            result_obj = resp_result.get("result", {})
            productos = result_obj.get("products", [])
            
            debug_info["total_encontrados"] = len(productos)

            # --- FASE 3: FILTRADO ---
            for p in productos:
                precio = float(p.get('target_sale_price', 0))
                envio = float(p.get('target_shipping_fee', 0))
                
                if precio > 0:
                    # Umbral flexible: 15% para productos caros, 10% para baratos
                    umbral = 0.15 if precio > 15 else 0.10
                    
                    if envio <= (precio * umbral):
                        print(f"      [Check] Encontrado: ${precio} USD (Envío: ${envio}) - CUMPLE con {fuente}")
                        return {
                            "link": p['promotion_link'],
                            "precio": precio,
                            "envio": envio,
                            "foto": p['product_main_image_url'],
                            "titulo": p['product_title'],
                            "fuente_exito": fuente
                        }, debug_info
            
            print(f"   [API] Intento {idx+1} ({fuente}) sin ofertas válidas.")
            
        except Exception as e:
            print(f"   [API Error] Fallo en intento {idx+1}: {e}")
            debug_info["error"] = str(e)

    # Si ningún intento devolvió producto
    return None, debug_info