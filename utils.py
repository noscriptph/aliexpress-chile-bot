import hashlib
import time
import requests
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
APP_KEY = os.getenv("ALI_APP_KEY")
APP_SECRET = os.getenv("ALI_APP_SECRET")
TRACKING_ID = "telegram_chile_bot"

def obtener_firma(params):
    sorted_params = sorted(params.items())
    query_string = "".join(f"{k}{v}" for k, v in sorted_params)
    sign_str = f"{APP_SECRET}{query_string}{APP_SECRET}"
    return hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()

def extraer_nombre_e_imagen(url):
    """Entra al link para sacar el nombre del producto y su foto."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        titulo = soup.find("meta", property="og:title")["content"]
        imagen = soup.find("meta", property="og:image")["content"]
        return titulo.split('|')[0].strip(), imagen
    except:
        return "Producto AliExpress", None

def investigar_mejor_oferta(url_original):
    """Busca una mejor opción con link de afiliado y envío < 10%."""
    nombre, foto_original = extraer_nombre_e_imagen(url_original)
    
    endpoint = "https://gw.api.alibaba.com/openapi/param2/2/portals.open/api.product.query/" + APP_KEY
    params = {
        "app_key": APP_KEY,
        "format": "json",
        "method": "aliexpress.affiliate.product.query",
        "keywords": nombre,
        "ship_to_country": "CL",
        "sort": "VOLUME_HIGH",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "v": "2.0",
        "sign_method": "md5"
    }
    params["sign"] = obtener_firma(params)

    try:
        response = requests.get(endpoint, params=params)
        data = response.json()
        productos = data.get("aliexpress_affiliate_product_query_response", {}).get("resp_result", {}).get("result", {}).get("products", [])
        
        for p in productos:
            precio = float(p['target_sale_price'])
            envio = float(p.get('target_shipping_fee', 0))
            if envio <= (precio * 0.10): # REGLA DEL 10%
                return {
                    "link": p['promotion_link'],
                    "precio": precio,
                    "foto": p['product_main_image_url'],
                    "titulo": p['product_title']
                }
    except:
        pass
    return None