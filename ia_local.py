import requests
import json
import re

def analizar_con_ia(titulo_sucio):
    """
    Usa Ollama y Gemma 3 para extraer la esencia del producto.
    Si Ollama no responde, devuelve None para activar el respaldo local.
    """
    # Prompt ultra-optimizado: Instrucciones claras en inglés suelen funcionar 
    # mejor con modelos pequeños como 4b para tareas de extracción.
    prompt = (
        f"You are an e-commerce expert. Extract ONLY the main product name from the title. "
        f"Remove quantities, voltages, and marketing words. Maximum 3 words. "
        f"Do not explain, do not use punctuation.\n\n"
        f"Title: \"{titulo_sucio}\"\n"
        f"Product Name:"
    )
    
    try:
        # Configuración para gemma3:4b
        payload = {
            "model": "gemma3:4b", 
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Máxima precisión, mínima creatividad
                "num_predict": 12,    # Suficiente para 3-4 palabras
                "top_p": 0.9
            }
        }
        
        # Timeout de 7 segundos: si la IA no responde rápido, pasamos al analizador.py
        response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=7)
        
        if response.status_code == 200:
            resultado = response.json()
            nombre_ia = resultado.get("response", "").strip()
            
            # --- LIMPIEZA DE SEGURIDAD ---
            # Removemos comillas, puntos finales y saltos de línea indeseados
            nombre_ia = nombre_ia.replace('"', '').replace("'", "").replace("\n", "")
            nombre_ia = re.sub(r'[.\!\?]', '', nombre_ia) # Quita signos de puntuación
            
            # Si la IA devuelve algo vacío o muy corto, devolvemos None para usar respaldo
            if not nombre_ia or len(nombre_ia) < 2:
                return None
                
            return nombre_ia
        
        return None

    except Exception as e:
        # Reporte silencioso en consola para el usuario
        print(f"   [IA Status] Offline o no disponible. Usando respaldo de reglas...")
        return None