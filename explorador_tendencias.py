import requests
from bs4 import BeautifulSoup
import re

def obtener_keywords_tendencia():
    """
    Scrapea tendencias y aplica un filtro de calidad para keywords de búsqueda.
    """
    print("   [Explorador] Buscando tendencias actuales en AliExpress...")
    tendencias = []
    
    url = "https://es.aliexpress.com/w/wholesale-top-selling-products.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "es-CL,es;q=0.9"
    }

    # Lista de respaldo inteligente con productos de alta demanda en Chile (2025-2026)
    lista_respaldo = [
        "Consola R36S Retro", "SSD NVMe 1TB Kingston", "Teclado Mecánico RGB", 
        "Proyector Magcubic Hy300", "Power Bank Baseus 65W", "Smartwatch Amoled",
        "Audífonos Lenovo LP40", "Mouse Gaming Inalámbrico", "Cargador GaN 65W"
    ]

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return lista_respaldo

        soup = BeautifulSoup(response.text, 'html.parser')
        titulos = soup.find_all('h3')
        
        for t in titulos:
            texto = t.get_text().strip()
            # Limpieza: Eliminamos símbolos raros y números de series largos
            limpio = re.sub(r'[^\w\s]', '', texto)
            palabras = limpio.split()[:4] # Tomamos las primeras 4 palabras
            keyword = " ".join(palabras)
            
            # Filtro: Evitar palabras basura del sitio
            palabras_basura = ['envío', 'gratis', 'aliexpress', 'oficial', 'tienda', 'nuevo']
            if any(basura in keyword.lower() for basura in palabras_basura):
                continue

            if len(keyword) > 10 and keyword not in tendencias:
                tendencias.append(keyword)
        
        return tendencias[:15] if tendencias else lista_respaldo
        
    except Exception as e:
        print(f"   [Explorador] Error de conexión: {e}. Usando lista de respaldo.")
        return lista_respaldo