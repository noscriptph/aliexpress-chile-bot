import time
import utils
import os

def ejecutar_caceria():
    archivo_objetivos = "objetivos.txt"
    archivo_resultados = "ofertas_encontradas.txt"

    if not os.path.exists(archivo_objetivos):
        print(f"❌ Error: No existe el archivo {archivo_objetivos}")
        return

    with open(archivo_objetivos, "r", encoding="utf-8") as f:
        busquedas = [line.strip() for line in f if line.strip()]

    print(f"🎯 Iniciando cacería de {len(busquedas)} productos...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    for item in busquedas:
        print(f"🔍 Buscando: {item}...")
        
        # Simulamos un callback simple para consola
        def log_status(texto):
            print(f"   {texto}")

        # Reutilizamos la lógica potente de utils.py
        # Nota: Como no tenemos URL, pasamos el término directamente
        # He ajustado esta llamada para que utils sepa manejarla
        resultado, debug = utils.investigar_mejor_oferta_por_texto(item, callback_status=log_status)

        if resultado:
            print(f"✅ ¡OFERTA ENCONTRADA!: {resultado['titulo'][:50]}...")
            print(f"   💰 Precio: ${resultado['precio']} | Envío: ${resultado['envio']}")
            print(f"   🔗 Link: {resultado['link']}")
            
            # Guardamos en un archivo de resultados
            with open(archivo_resultados, "a", encoding="utf-8") as res_f:
                res_f.write(f"Producto buscado: {item}\n")
                res_f.write(f"Encontrado: {resultado['titulo']}\n")
                res_f.write(f"Precio: ${resultado['precio']} | Envío: ${resultado['envio']}\n")
                res_f.write(f"Link: {resultado['link']}\n")
                res_f.write("-" * 30 + "\n")
        else:
            print(f"❌ No se encontró nada aceptable para '{item}'")
        
        print("--- Esperando 5 segundos para evitar bloqueo de API ---")
        time.sleep(5)

if __name__ == "__main__":
    ejecutar_caceria()