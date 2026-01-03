import re

def limpiar_titulo(titulo_sucio):
    """
    Limpieza por reglas fijas. Optimizado para extraer Marca + Producto
    cuando la IA no está disponible o falla.
    """
    if not titulo_sucio:
        return "Producto"

    # 1. Limpieza de ruido técnico (Regex)
    # Agregamos más patrones para limpiar especificaciones que ensucian la búsqueda
    patrones_ruido = [
        r'\d+\s?[pP][cC][sS]?',          # Cantidades
        r'\d+\s?[vV](?!\w)',             # Voltaje
        r'\d+\s?[wW](?!\w)',             # Watts
        r'\d+\s?[aA](?!\w)',             # Amperaje
        r'\d+\s?[mM][hH][zZ]',           # Frecuencia
        r'\d+\s?[mM][mM]',               # Medidas mm
        r'\d+\s?[cC][mM]',               # Medidas cm
        r'\d+\s?[gG]',                   # Peso
        r'x\d+',                         # Multiplicadores
        r'\[.*?\]',                      # Corchetes
        r'\(.*?\)',                      # Paréntesis
        r'USB\s?\d\.\d',                 # Versiones USB
        r'Type\s?-?\s?C',                # Conector (Suele sobrar en búsqueda)
        r'GaN\s?\d*',                    # Tecnología GaN (A veces ensucia)
    ]
    
    texto_limpio = titulo_sucio
    for patron in patrones_ruido:
        texto_limpio = re.sub(patron, '', texto_limpio, flags=re.IGNORECASE)

    # 2. Eliminar caracteres especiales (excepto espacios)
    texto_limpio = re.sub(r'[^\w\s]', ' ', texto_limpio)

    # 3. Diccionario de ruido de marketing (Expandido)
    palabras_marketing = {
        "original", "new", "top", "best", "sale", "cheap", "hot", "quality", 
        "free", "shipping", "promo", "stock", "nuevo", "oficial", "official",
        "envio", "gratis", "oferta", "descuento", "high", "low", "price", "fast",
        "charger", "cargador", "cable", "para", "for", "with", "con", "port", "puerto"
    }
    
    palabras = texto_limpio.split()
    
    # 4. Lógica de selección inteligente:
    # Filtramos palabras de marketing y cortas, pero mantenemos el orden original
    palabras_filtradas = [
        p for p in palabras 
        if p.lower() not in palabras_marketing and len(p) > 2
    ]

    # ESTRATEGIA: 
    # Si después de limpiar quedan muchas palabras, intentamos agarrar 
    # la Marca (suele ser la 1ra) y el modelo (suele estar cerca).
    if len(palabras_filtradas) > 4:
        # Tomamos 1ra (Marca) + 2da y 3ra (Modelo/Producto)
        resultado = " ".join(palabras_filtradas[:3])
    else:
        resultado = " ".join(palabras_filtradas)
    
    return resultado if resultado else "AliExpress Product"