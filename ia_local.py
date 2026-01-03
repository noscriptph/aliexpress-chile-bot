import requests
import json
import re

def analizar_con_ia(titulo_sucio):
    """
    Usa Gemma 3 27b. Dado que el modelo corre parcialmente en RAM DDR5,
    hemos ampliado el tiempo de espera para evitar errores de conexión.
    """
    # Prompt optimizado para máxima brevedad
    prompt = (
        f"You are an e-commerce specialist. Extract ONLY the generic product name. "
        f"Strict rules: No brands, no numbers, no technical specs. Max 3 words.\n"
        f"Title: {titulo_sucio}\n"
        f"Product Name:"
    )
    
    try:
        payload = {
            "model": "gemma3:27b",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 15,
                "num_thread": 8  # Aprovecha tus núcleos de CPU para ayudar a la RAM DDR5
            }
        }
        
        # URL exacta de Ollama (127.0.0.1 es más estable que localhost en Windows)
        url_ollama = "http://127.0.0.1:11434/api/generate"
        
        # TIMEOUT: Subimos a 45 segundos. 
        # Al usar 32GB de RAM DDR5 en lugar de solo VRAM, el primer token puede tardar.
        response = requests.post(url_ollama, json=payload, timeout=45)
        
        if response.status_code == 200:
            resultado = response.json()
            nombre_ia = resultado.get("response", "").strip()
            
            # Limpieza profunda de caracteres que puedan romper la API de AliExpress
            nombre_ia = nombre_ia.replace('"', '').replace("'", "").replace("\n", "")
            nombre_ia = re.sub(r'[.\!\?]', '', nombre_ia)
            
            # Validación de seguridad: si la IA devuelve basura o nada, activar respaldo
            if nombre_ia and len(nombre_ia) >= 3:
                return nombre_ia
            
        return None

    except Exception as e:
        # Imprime el error para que podamos verlo en la ventana negra del bot
        print(f"   [IA Debug] Error con Gemma 27b: {e}")
        return None