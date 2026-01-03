import time
import schedule
import utils
import telebot
import os
import csv
from datetime import datetime
import explorador_tendencias

# --- CONFIGURACIÓN ---
GRUPO_ID = "-100XXXXXXXXXX" 
LIMITE_DIARIO = 5           
HORA_EJECUCION = "10:30"    
ARCHIVO_HISTORIAL = "historial_ofertas.csv"

bot = telebot.TeleBot(os.getenv("TELEGRAM_TOKEN"))

def inicializar_csv():
    """Crea el CSV con encabezados si no existe."""
    if not os.path.exists(ARCHIVO_HISTORIAL):
        with open(ARCHIVO_HISTORIAL, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['fecha', 'producto_buscado', 'titulo_encontrado', 'precio', 'envio', 'link'])

def producto_ya_publicado(titulo):
    """Revisa en el CSV si el producto ya fue enviado antes."""
    if not os.path.exists(ARCHIVO_HISTORIAL):
        return False
    with open(ARCHIVO_HISTORIAL, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if titulo in row: # Compara por título para evitar repetidos
                return True
    return False

def registrar_en_csv(busqueda, resultado):
    """Guarda la oferta exitosa en el historial."""
    with open(ARCHIVO_HISTORIAL, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            busqueda,
            resultado['titulo'],
            resultado['precio'],
            resultado['envio'],
            resultado['link']
        ])

def tarea_diaria():
    print(f"\n🚀 [Cazador Auto] Iniciando tarea: {datetime.now()}")
    inicializar_csv()
    
    productos_a_cazar = explorador_tendencias.obtener_keywords_tendencia()
    enviados = 0
    
    for item in productos_a_cazar:
        if enviados >= LIMITE_DIARIO:
            break
            
        # Filtro de duplicados
        if producto_ya_publicado(item):
            print(f"   [Skip] '{item}' ya se publicó recientemente.")
            continue

        print(f"🔎 Analizando tendencia: {item}")
        resultado, debug = utils.investigar_mejor_oferta(item)
        
        if resultado:
            porcentaje = round((resultado['envio'] / resultado['precio']) * 100, 1) if resultado['precio'] > 0 else 0
            
            caption = (
                f"🔥 <b>¡TENDENCIA DEL DÍA!</b> 🔥\n\n"
                f"📦 <b>{resultado['titulo'][:90]}...</b>\n\n"
                f"💰 <b>Precio:</b> ${resultado['precio']} USD\n"
                f"🚚 <b>Envío a Chile:</b> ${resultado['envio']} USD ({porcentaje}%)\n\n"
                f"🔗 <a href='{resultado['link']}'>COMPRAR AHORA EN ALI</a>"
            )
            
            try:
                bot.send_photo(GRUPO_ID, resultado['foto'], caption=caption, parse_mode="HTML")
                registrar_en_csv(item, resultado) # <--- Guardar en CSV
                enviados += 1
                print(f"   [OK] {enviados}/{LIMITE_DIARIO} enviado y registrado.")
                time.sleep(25) 
            except Exception as e:
                print(f"   [Error] {e}")
        else:
            print(f"   [Saltado] Sin oferta válida para '{item}'")

# --- CICLO DE EJECUCIÓN ---
schedule.every().day.at(HORA_EJECUCION).do(tarea_diaria)

if __name__ == "__main__":
    inicializar_csv()
    print(f"⏰ Sistema listo. Historial: {ARCHIVO_HISTORIAL}")
    while True:
        schedule.run_pending()
        time.sleep(60)