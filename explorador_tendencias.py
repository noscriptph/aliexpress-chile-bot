import requests
from bs4 import BeautifulSoup
import re

def obtener_keywords_tendencia():
    """
    Scrapea la sección de más vendidos o busca términos populares.
    """
    print("   [Explorador] Buscando tendencias actuales en AliExpress...")
    tendencias = []
    
    # URL de productos en oferta relámpago o más vendidos
    url = "https://es.aliexpress.com/w/wholesale-top-selling-products.html"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscamos títulos de productos en la página de resultados
        # AliExpress usa diferentes clases, pero los h3 suelen contener los nombres
        titulos = soup.find_all('h3')
        
        for t in titulos:
            texto = t.get_text().strip()
            # Limpiamos el texto para que sean keywords útiles (3-4 palabras)
            limpio = " ".join(texto.split()[:4])
            if len(limpio) > 10 and limpio not in tendencias:
                tendencias.append(limpio)
        
        # Si el scraping falla por bloqueos, devolvemos una lista de respaldo sólida
        if not tendencias:
            return ["Consola R36S", "SSD NVMe 1TB", "Teclado Mecánico RGB", "Proyector Magcubic Hy300", "Power Bank Baseus"]
            
        return tendencias[:15] # Retornamos las primeras 15 tendencias halladas
    except:
        return ["Consola R36S", "SSD NVMe 1TB", "Teclado Mecánico RGB", "Proyector Magcubic Hy300", "Power Bank Baseus"]