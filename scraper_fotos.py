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
        # Headers optimizados para evitar bloqueos por bot-detection
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept-Language": "es-CL,es;q=0.9",
            "Referer": "https://www.aliexpress.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        }
        
        # Petición con timeout generoso
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"   [Scraper] Error: Código de respuesta {response.status_code}")
            return resultado

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Foto principal del producto (Meta Tag OG)
        meta_photo = soup.find("meta", property="og:image")
        if meta_photo and meta_photo.get("content"):
            foto_base = meta_photo["content"]
            # Limpiar posibles miniaturas para que la principal sea HQ
            if ".jpg_" in foto_base:
                foto_base = foto_base.split(".jpg_")[0] + ".jpg"
            resultado["principal"] = foto_base
            print("   [Scraper] Foto de portada detectada (HQ).")

        # 2. Búsqueda de fotos de reseñas (Feedback de compradores)
        # Buscamos patrones de imágenes alojadas en servidores de feedback/kf
        fotos_resenas = []
        
        # Este patrón busca específicamente imágenes de reseñas o almacenadas en el Content Delivery Network (CDN)
        patron_img = re.compile(r'ae01\.alicdn\.com/kf/|feedback')
        
        all_imgs = soup.find_all('img', src=patron_img)
        
        for img in all_imgs:
            src = img.get('src') or img.get('data-src') # Algunos elementos usan lazy loading
            if not src:
                continue

            # Normalización del protocolo
            if src.startswith('//'):
                src = "https:" + src
            elif not src.startswith('http'):
                continue 

            # --- LIMPIEZA DE ALTA RESOLUCIÓN ---
            # AliExpress redimensiona con sufijos como .jpg_220x220.jpg o .jpg_Q90.jpg
            # Queremos la imagen original sin compresión agresiva.
            if '.jpg' in src:
                # Cortamos en la primera aparición de .jpg para limpiar el sufijo
                clean_url = src.split('.jpg')[0] + ".json" # Truco: .json a veces devuelve metadata, mejor forzar .jpg puro
                clean_url = src.split('.jpg')[0] + ".jpg"
                
                # FILTROS DE CALIDAD:
                # 1. Evitar duplicados
                # 2. Evitar la foto principal
                # 3. Evitar iconos pequeños (como banderas o avatars que pesen poco en la URL)
                if clean_url not in fotos_resenas and clean_url != resultado["principal"]:
                    if "HTB1" not in clean_url and "avatar" not in clean_url: # HTB1 suele ser basura de UI antigua
                        if len(fotos_resenas) < 4:
                            fotos_resenas.append(clean_url)
                            print(f"      -> Foto de comprador #{len(fotos_resenas)} extraída.")

        resultado["resenas"] = fotos_resenas
        
        if not fotos_resenas:
            print("   [Scraper] Nota: No se hallaron fotos de compradores en el HTML estático.")
        else:
            print(f"   [Scraper] Proceso finalizado. Total: {len(fotos_resenas)} fotos.")

        return resultado
        
    except Exception as e:
        print(f"   [Error Scraper] Error crítico: {e}")
        return resultado