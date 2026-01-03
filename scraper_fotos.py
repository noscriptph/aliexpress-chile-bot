import requests
from bs4 import BeautifulSoup
import re

def obtener_fotos_reales(url):
    """
    Entra a la página del producto y busca fotos en la sección de reseñas.
    Optimizado para extraer imágenes de alta resolución de los servidores de AliExpress.
    """
    print(f"   [Scraper] Iniciando búsqueda de fotos reales...")
    
    # Resultado por defecto
    resultado = {"principal": None, "resenas": []}
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "es-CL,es;q=0.9",
            "Referer": "https://www.aliexpress.com/"
        }
        
        # Petición con timeout generoso para evitar bloqueos
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"   [Scraper] Error: Código de respuesta {response.status_code}")
            return resultado

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Foto principal del producto (Meta Tag OG)
        meta_photo = soup.find("meta", property="og:image")
        if meta_photo and meta_photo.get("content"):
            resultado["principal"] = meta_photo["content"]
            print("   [Scraper] Foto de portada detectada.")

        # 2. Búsqueda de fotos de reseñas (Feedback de compradores)
        # Filtramos por dominios conocidos de imágenes de AliExpress (kf, ae01, etc)
        # y patrones que indican miniaturas de reseñas (_220x220).
        fotos_resenas = []
        patron_img = re.compile(r'\.jpg_220x220|feedback|ae01\.alicdn\.com/kf/')
        
        all_imgs = soup.find_all('img', src=patron_img)
        
        for img in all_imgs:
            src = img.get('src')
            if not src:
                continue

            # Normalización del protocolo
            if src.startswith('//'):
                src = "https:" + src
            elif not src.startswith('http'):
                continue # Saltar rutas relativas no válidas

            # --- LIMPIEZA DE ALTA RESOLUCIÓN ---
            # AliExpress añade sufijos de redimensionamiento (ej: .jpg_220x220.jpg).
            # Eliminamos todo lo que esté después de '.jpg' para obtener la original.
            if '.jpg' in src:
                clean_url = src.split('.jpg')[0] + ".jpg"
                
                # Evitar duplicados y no incluir la foto principal en las de reseñas
                if clean_url not in fotos_resenas and clean_url != resultado["principal"]:
                    if len(fotos_resenas) < 4:
                        fotos_resenas.append(clean_url)
                        print(f"      -> Foto de comprador #{len(fotos_resenas)} extraída.")

        resultado["resenas"] = fotos_resenas
        
        if not fotos_resenas:
            print("   [Scraper] Nota: No se hallaron fotos de compradores en el HTML base.")
        else:
            print(f"   [Scraper] Proceso finalizado. Total: {len(fotos_resenas)} fotos.")

        return resultado
        
    except Exception as e:
        print(f"   [Error Scraper] Error crítico durante el proceso: {e}")
        return resultado