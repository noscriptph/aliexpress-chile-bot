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
        
        # Intentamos obtener el título del OpenGraph o del Title tag
        meta_titulo = soup.find("meta", property="og:title")
        if meta_titulo:
            titulo = meta_titulo["content"]
        else:
            titulo = soup.title.string if soup.title else "Producto AliExpress"
        
        meta_imagen = soup.find("meta", property="og:image")
        imagen = meta_imagen["content"] if meta_imagen else None
        
        # Limpiamos el título de separadores comunes
        titulo_limpio = titulo.split('|')[0].split('-')[0].strip()
        
        return titulo_limpio, imagen
    except Exception as e:
        print(f"   [Error Web] Fallo al extraer datos base: {e}")
        return "Producto", None

def investigar_mejor_oferta(url_original):
    """
    Coordina la limpieza (IA/Manual) y la búsqueda en la API.
    Retorna: (datos_producto, info_debug)
    """
    nombre_sucio, foto_original = extraer_nombre_e_imagen(url_original)
    
    debug_info = {
        "ia_activa": False,
        "termino_usado": "",
        "total_encontrados": 0,
        "error": None
    }
    
    # 1. Intentar limpiar con IA Local (Gemma 3)
    print(f"   [Proceso] Analizando: '{nombre_sucio[:50]}...'")
    termino = ia_local.analizar_con_ia(nombre_sucio)
    
    if termino:
        print(f"   [IA] Gemma 3 identificó: '{termino}'")
        debug_info["ia_activa"] = True
    else:
        print("   [IA] Offline o Error. Activando Analizador de reglas...")
        termino = analizador.limpiar_titulo(nombre_sucio)
    
    # Limpieza final del término para la API (quitar puntuación residual)
    termino = re.sub(r'[^\w\s]', '', termino).strip()
    debug_info["termino_usado"] = termino

    # 2. Configuración de API AliExpress
    print(f"   [API] Buscando mejores precios para '{termino}' en Chile...")
    endpoint = "https://gw.api.alibaba.com/openapi/param2/2/portals.open/api.product.query/" + APP_KEY
    
    params = {
        "app_key": APP_KEY,
        "format": "json",
        "method": "aliexpress.affiliate.product.query",
        "keywords": termino,
        "ship_to_country": "CL",
        "sort": "VOLUME_HIGH",  # Priorizamos los más vendidos (más confiables)
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "v": "2.0",
        "sign_method": "md5"
    }
    params["sign"] = obtener_firma(params)

    try:
        response = requests.get(endpoint, params=params, timeout=12)
        data = response.json()
        
        # Navegación en el JSON de respuesta
        res_root = data.get("aliexpress_affiliate_product_query_response", {})
        resp_result = res_root.get("resp_result", {})
        result = resp_result.get("result", {})
        productos = result.get("products", [])
        
        debug_info["total_encontrados"] = len(productos)

        # 3. Filtrado por la "Regla del 10%"
        for p in productos:
            precio = float(p.get('target_sale_price', 0))
            envio = float(p.get('target_shipping_fee', 0))
            
            # Solo consideramos productos con precio válido
            if precio > 0:
                # El envío debe ser menor o igual al 10% del precio del producto
                if envio <= (precio * 0.10):
                    print(f"      [Check] Encontrado: ${precio} USD | Envío: ${envio} (CUMPLE)")
                    return {
                        "link": p['promotion_link'],
                        "precio": precio,
                        "envio": envio,
                        "foto": p['product_main_image_url'],
                        "titulo": p['product_title']
                    }, debug_info
        
        print("   [API] Sin resultados que cumplan el criterio de envío bajo.")
        return None, debug_info

    except Exception as e:
        print(f"   [API Error] {e}")
        debug_info["error"] = str(e)
        return None, debug_info