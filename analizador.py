import re
import unicodedata

def eliminar_acentos(texto):
    """Normaliza el texto eliminando tildes para evitar fallos de búsqueda."""
    return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

def limpiar_titulo(titulo_sucio):
    """
    Limpieza por reglas fijas. Pre-procesa el texto antes de enviarlo a la IA
    o sirve como motor principal si la IA está apagada.
    """
    if not titulo_sucio:
        return "Producto"

    # 0. Normalización básica
    texto_limpio = eliminar_acentos(titulo_sucio)

    # 1. Limpieza de ruido técnico (Regex)
    patrones_ruido = [
        r'\d+\s?[pP][cC][sS]?',          # Cantidades (2pcs, 10 PCS)
        r'\d+\s?[vV](?!\w)',             # Voltaje (220V)
        r'\d+\s?[wW](?!\w)',             # Watts (65W)
        r'\d+\s?[aA](?!\w)',             # Amperaje
        r'\d+\s?[mM][hH][zZ]',           # Frecuencia
        r'\d+\s?[mM][mM]',               # Medidas mm
        r'\d+\s?[cC][mM]',               # Medidas cm
        r'\d+\s?[gG](?!\w)',             # Peso
        r'x\d+',                         # Multiplicadores (x10)
        r'\[.*?\]',                      # Contenido en corchetes
        r'\(.*?\)',                      # Contenido en paréntesis
        r'USB\s?\d\.\d',                 # Versiones USB
        r'Type\s?-?\s?C',                # Conector
        r'GaN\s?\d*',                    # Tecnología GaN
    ]
    
    for patron in patrones_ruido:
        texto_limpio = re.sub(patron, '', texto_limpio, flags=re.IGNORECASE)

    # 2. Eliminar caracteres especiales (excepto espacios)
    texto_limpio = re.sub(r'[^\w\s]', ' ', texto_limpio)

    # 3. Diccionario de ruido de marketing (Expandido para Chile/Global)
    palabras_marketing = {
        "original", "new", "top", "best", "sale", "cheap", "hot", "quality", 
        "free", "shipping", "promo", "stock", "nuevo", "oficial", "official",
        "envio", "gratis", "oferta", "descuento", "high", "low", "price", "fast",
        "charger", "cargador", "cable", "para", "for", "with", "con", "port", "puerto",
        "smartphone", "mobile", "phone", "celular", "tempered", "glass", "case", "funda"
    }
    
    palabras = texto_limpio.split()
    
    # 4. Filtrado inteligente
    palabras_filtradas = [
        p for p in palabras 
        if p.lower() not in palabras_marketing and len(p) > 2
    ]

    # ESTRATEGIA: Tomamos Marca + Modelo/Tipo
    if len(palabras_filtradas) > 4:
        resultado = " ".join(palabras_filtradas[:3])
    else:
        resultado = " ".join(palabras_filtradas)
    
    return resultado.strip() if resultado else "AliExpress Product"