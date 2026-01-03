import requests
import json
import re

def analizar_con_ia(titulo_sucio):
    """
    Usa Gemma 3 27b para extraer la esencia comercial del producto.
    Optimizado para hardware con 32GB RAM DDR5 y 3070 Ti.
    """
    
    # PROMPT MEJORADO: Ahora permite modelos técnicos (importante para herramientas)
    # pero elimina basura de marketing.
    prompt = (
        f"Task: Extract the core product name and model from the title.\n"
        f"Rules: Remove marketing words (Sale, New, Hot, Top, 2026). Keep technical models (e.g., IR6500, GMK26). "
        f"Result must be in Spanish or English, max 4 words.\n"
        f"Title: {titulo_sucio}\n"
        f"Result:"
    )
    
    try:
        payload = {
            "model": "gemma3:27b",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,    # Casi determinista para evitar inventos
                "num_predict": 20,     # Un poco más de margen para modelos largos
                "num_thread": 12,      # Aprovechamos más hilos de tu CPU
                "top_k": 20,
                "top_p": 0.9
            }
        }
        
        url_ollama = "http://127.0.0.1:11434/api/generate"
        
        # TIMEOUT: 45 segundos es perfecto para que cargue desde la RAM DDR5 si es necesario
        response = requests.post(url_ollama, json=payload, timeout=45)
        
        if response.status_code == 200:
            resultado = response.json()
            nombre_ia = resultado.get("response", "").strip()
            
            # Limpieza de formato
            nombre_ia = nombre_ia.replace('"', '').replace("'", "").replace("\n", "")
            # Elimina prefijos comunes que Gemma a veces añade
            nombre_ia = re.sub(r'^(Product Name:|Result:|Name:)', '', nombre_ia, flags=re.IGNORECASE).strip()
            # Limpieza de puntuación innecesaria
            nombre_ia = re.sub(r'[.\!\?]', '', nombre_ia)
            
            if nombre_ia and len(nombre_ia) >= 3:
                print(f"   [IA] Cerebro Gemma identificó: '{nombre_ia}'")
                return nombre_ia
            
        return None

    except Exception as e:
        print(f"   [IA Debug] Error con Gemma 27b: {e}")
        return None