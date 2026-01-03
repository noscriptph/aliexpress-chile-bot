import time
import utils
import os
import requests
import schedule
from dotenv import load_dotenv

# Cargar configuración desde .env
load_dotenv()

def descargar_imagen(url, nombre_archivo):
    """Descarga la imagen del producto para tenerla lista para publicar."""
    try:
        if not url: return False
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            with open(nombre_archivo, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"   [Error Imagen] No se pudo descargar: {e}")
    return False

def ejecutar_caceria():
    archivo_objetivos = "objetivos.txt"
    carpeta_resultados = "resultados_caceria"
    
    if not os.path.exists(carpeta_resultados):
        os.makedirs(carpeta_resultados)

    if not os.path.exists(archivo_objetivos):
        print(f"❌ Error: No existe {archivo_objetivos}")
        return

    with open(archivo_objetivos, "r", encoding="utf-8") as f:
        busquedas = [line.strip() for line in f if line.strip()]

    if not busquedas:
        print("⚠️ El archivo objetivos.txt está vacío. Esperando próxima ejecución...")
        return

    print(f"\n🎯 [{time.strftime('%H:%M:%S')}] Iniciando cacería de {len(busquedas)} productos...")
    print(f"📂 Guardando en: /{carpeta_resultados}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    for item in busquedas:
        print(f"\n🔍 Analizando objetivo: {item}...")
        
        def log_status(texto):
            print(f"   {texto.replace('<b>', '').replace('</b>', '')}")

        # La función investigar_mejor_oferta de utils ya usa las API KEYS del .env
        resultado, debug = utils.investigar_mejor_oferta(item, callback_status=log_status)

        if resultado:
            # Generación de ID único basado en tiempo
            id_unico = str(int(time.time()))[-6:]
            nombre_limpio = "".join([c for c in item if c.isalnum() or c==' ']).strip()
            nombre_carpeta = f"{id_unico}_{nombre_limpio.replace(' ', '_')}"
            
            ruta_producto = os.path.join(carpeta_resultados, nombre_carpeta)
            if not os.path.exists(ruta_producto):
                os.makedirs(ruta_producto)

            # 1. Descargar Imagen
            nombre_img = os.path.join(ruta_producto, "foto_producto.jpg")
            descargar_imagen(resultado['foto'], nombre_img)

            # 2. Crear Ficha de Texto Ordenada
            ficha_path = os.path.join(ruta_producto, "ficha_oferta.txt")
            with open(ficha_path, "w", encoding="utf-8") as f:
                f.write("🔥 REPORTE DE OFERTA ENCONTRADA 🔥\n")
                f.write("="*40 + "\n\n")
                f.write(f"🆔 ID REPORTE: {id_unico}\n")
                f.write(f"🏷️ BÚSQUEDA:  {item}\n")
                f.write(f"📦 PRODUCTO:  {resultado['titulo']}\n\n")
                f.write(f"💰 PRECIO:    ${resultado['precio']} USD\n")
                f.write(f"🚚 ENVÍO:    ${resultado['envio']} USD\n")
                f.write(f"🎯 MÉTODO:    {resultado['fuente_exito']}\n\n")
                f.write(f"🔗 LINK:      {resultado['link']}\n\n")
                f.write("="*40 + "\n")
                f.write(f"Generado el: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

            print(f"✅ Carpeta creada: /{nombre_carpeta}")
        else:
            print(f"❌ No se encontró oferta válida para '{item}'")
        
        time.sleep(5) # Delay entre productos para la API

    print(f"\n✅ Cacería finalizada. Próxima revisión en 12 horas.")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

# --- PROGRAMACIÓN DE LA TAREA ---

def tarea_programada():
    ejecutar_caceria()

# Configuración: Revisar la lista cada 12 horas
schedule.every(12).hours.do(tarea_programada)

if __name__ == "__main__":
    print("🛰️  Cazador Manual Automatizado Activado")
    print("📝 Leyendo objetivos de: objetivos.txt")
    
    # Ejecutar inmediatamente la primera vez
    tarea_programada()
    
    while True:
        schedule.run_pending()
        time.sleep(60)