import re

def limpiar_titulo(titulo_sucio):
    """
    Limpia el título mediante reglas fijas (Regex) para encontrar la esencia.
    Funciona como respaldo (failsafe) cuando la IA no responde.
    """
    if not titulo_sucio:
        return "Producto"

    # 1. Limpieza de variaciones técnicas y medidas
    # Agregamos patrones para modelos de chips y conectores comunes
    patrones_ruido = [
        r'\d+\s?[pP][cC][sS]?',         # Cantidades (1pcs, 10 PCS)
        r'\d+\s?[vV](?!\w)',            # Voltaje (12V, 5v)
        r'\d+\s?[wW](?!\w)',            # Watts (20W)
        r'\d+\s?[aA](?!\w)',            # Amperaje (2A)
        r'\d+\s?[mM][hH][zZ]',          # Frecuencia
        r'\d+\s?[mM][mM]',              # Medidas mm
        r'\d+\s?[cC][mM]',              # Medidas cm
        r'\d+\s?[gG]',                  # Peso (gramos)
        r'x\d+',                         # Multiplicadores (x10)
        r'\[.*?\]',                     # Texto entre corchetes (ej: [Global Version])
        r'\(.*?\)',                     # Texto entre paréntesis
        r'USB\s?\d\.\d',                # Versiones USB
    ]
    
    texto_limpio = titulo_sucio
    for patron in patrones_ruido:
        texto_limpio = re.sub(patron, '', texto_limpio, flags=re.IGNORECASE)

    # 2. Eliminar caracteres especiales y dejar solo letras/números
    texto_limpio = re.sub(r'[^\w\s]', ' ', texto_limpio)

    # 3. Eliminar "ruido" de marketing (español e inglés)
    palabras_marketing = {
        "original", "new", "top", "best", "sale", "cheap", "hot", "quality", 
        "free", "shipping", "promo", "stock", "nuevo", "oficial", "official",
        "envio", "gratis", "oferta", "descuento", "high", "low", "price", "fast"
    }
    
    palabras = texto_limpio.split()
    
    # Filtramos: palabras que no sean marketing y que tengan más de 2 letras
    palabras_finales = [
        p for p in palabras 
        if p.lower() not in palabras_marketing and len(p) > 2
    ]

    # 4. Retornar la esencia (3 palabras suelen ser suficientes para la API)
    # Ejemplo: "For Xiaomi Redmi Note 13 Pro Global Version" -> "Xiaomi Redmi Note"
    resultado = " ".join(palabras_finales[:3])
    
    return resultado if resultado else "AliExpress Product"