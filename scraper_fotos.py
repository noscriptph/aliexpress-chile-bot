import requests
from bs4 import BeautifulSoup
import re

def obtener_fotos_reales(url):
    """
    Entra a la página del producto y busca fotos en la sección de reseñas.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept-Language": "es-CL,es;q=0.9"
        }
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Intentar sacar la foto principal (OG Tag)
        meta_photo = soup.find("meta", property="og:image")
        main_photo = meta_photo["content"] if meta_photo else None

        # 2. Lógica para buscar fotos de reseñas (Scraping de imágenes de usuarios)
        # Nota: AliExpress carga esto dinámicamente, pero solemos encontrar 
        # las URLs en el script de la página.
        fotos_resenas = []
        all_imgs = soup.find_all('img', src=re.compile(r'\.jpg_220x220|feedback'))
        
        for img in all_imgs:
            src = img.get('src')
            if src and len(fotos_resenas) < 4: # Solo queremos las primeras 4
                # Limpiar la URL para obtener la imagen en alta resolución
                clean_url = "https:" + src.split('.jpg_')[0] + ".jpg"
                if clean_url not in fotos_resenas:
                    fotos_resenas.append(clean_url)

        return {
            "principal": main_photo,
            "resenas": fotos_resenas
        }
    except Exception as e:
        print(f"Error en scraper_fotos: {e}")
        return {"principal": None, "resenas": []}