import time
import schedule
import utils
import telebot
import os
import csv
import threading
from datetime import datetime
import explorador_tendencias
from dotenv import load_dotenv

# Carga de variables de entorno
load_dotenv()

# --- CONFIGURACIÓN ---
# Prioriza el .env, si no, usa el valor por defecto
GRUPO_ID = os.getenv("GRUPO_ID") or "-100XXXXXXXXXX" 
LIMITE_DIARIO = 5           
HORA_EJECUCION = "10:30"    
ARCHIVO_HISTORIAL = "historial_ofertas.csv"

# Inicialización del Bot
bot = telebot.TeleBot(os.getenv("TELEGRAM_TOKEN"))

def inicializar_csv():
    """Crea el CSV con encabezados si no existe."""
    if not os.path.exists(ARCHIVO_HISTORIAL):
        with open(ARCHIVO_HISTORIAL, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['fecha', 'producto_buscado', 'titulo_encontrado', 'precio', 'envio', 'link'])

def producto_ya_publicado(termino_busqueda):
    """Revisa en el CSV si el término ya fue procesado para evitar spam."""
    if not os.path.exists(ARCHIVO_HISTORIAL):
        return False
    with open(ARCHIVO_HISTORIAL, mode='r', encoding='utf-8') as f:
        # Leemos todo el contenido para una búsqueda rápida
        contenido = f.read()
        return termino_busqueda in contenido

def mostrar_historial():
    """Lee y muestra las últimas 10 entradas del CSV en consola."""
    print("\n--- 📄 ÚLTIMAS 10 OFERTAS EN HISTORIAL ---")
    if not os.path.exists(ARCHIVO_HISTORIAL):
        print("El historial aún no ha sido creado.")
        return
    try:
        with open(ARCHIVO_HISTORIAL, mode='r', encoding='utf-8') as f:
            reader = list(csv.reader(f))
            if len(reader) <= 1:
                print("El historial está vacío (solo encabezados).")
                return
            # Saltamos el encabezado y tomamos los últimos 10
            for row in reader[-10:]:
                print(f"📅 {row[0]} | 💰 ${row[3]} | 📦 {row[2][:40]}...")
    except Exception as e:
        print(f"❌ Error al leer historial: {e}")
    print("-------------------------------------------\n")

def borrar_historial():
    """Elimina el archivo CSV y lo reinicia."""
    if os.path.exists(ARCHIVO_HISTORIAL):
        os.remove(ARCHIVO_HISTORIAL)
        inicializar_csv()
        print("✅ Historial eliminado y reiniciado.")

def enviar_prueba_grupo():
    """Envía un mensaje simple para verificar permisos de administrador."""
    print(f"📡 Enviando señal de prueba a {GRUPO_ID}...")
    try:
        test_msg = f"🤖 <b>Sistema de Control:</b> Conexión establecida con éxito.\n⏰ Hora local: {datetime.now().strftime('%H:%M:%S')}"
        bot.send_message(GRUPO_ID, test_msg, parse_mode="HTML")
        print("✅ ¡Mensaje enviado! Revisa tu grupo de Telegram.")
    except Exception as e:
        print(f"❌ Error de conexión: {e}\nRevisa que el bot sea ADMIN del grupo y el ID sea correcto.")

def tarea_diaria():
    """Función principal de cacería (usada por el schedule y manualmente)."""
    print(f"\n🚀 [{datetime.now().strftime('%H:%M:%S')}] Iniciando cacería de tendencias...")
    inicializar_csv()
    
    productos_a_cazar = explorador_tendencias.obtener_keywords_tendencia()
    enviados = 0
    
    for item in productos_a_cazar:
        if enviados >= LIMITE_DIARIO:
            print(f"🏁 Límite diario de {LIMITE_DIARIO} alcanzado.")
            break
            
        if producto_ya_publicado(item):
            print(f"   [Skip] '{item}' ya se publicó anteriormente.")
            continue

        print(f"🔎 Analizando tendencia actual: {item}")
        # Llamamos a utils (que a su vez usa la IA para limpiar)
        resultado, debug = utils.investigar_mejor_oferta(item)
        
        if resultado:
            porcentaje_envio = round((resultado['envio'] / resultado['precio']) * 100, 1) if resultado['precio'] > 0 else 0
            
            caption = (
                f"🔥 <b>¡TENDENCIA DEL DÍA!</b> 🔥\n\n"
                f"📦 <b>{resultado['titulo'][:90]}...</b>\n\n"
                f"💰 <b>Precio:</b> ${resultado['precio']} USD\n"
                f"🚚 <b>Envío a Chile:</b> ${resultado['envio']} USD ({porcentaje_envio}%)\n\n"
                f"🔗 <a href='{resultado['link']}'>¡COMPRAR AHORA EN ALIEXPRESS!</a>"
            )
            
            try:
                bot.send_photo(GRUPO_ID, resultado['foto'], caption=caption, parse_mode="HTML")
                # Registro en CSV
                with open(ARCHIVO_HISTORIAL, mode='a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        item,
                        resultado['titulo'],
                        resultado['precio'],
                        resultado['envio'],
                        resultado['link']
                    ])
                enviados += 1
                print(f"   [OK] {enviados}/{LIMITE_DIARIO} publicado con éxito.")
                time.sleep(25) # Protección contra Flood de Telegram
            except Exception as e:
                print(f"   [Error en envío] {e}")
        else:
            print(f"   [Filtro] No se halló oferta que cumpla los requisitos para '{item}'")

def run_scheduler():
    """Bucle infinito para el hilo secundario (reloj automático)."""
    schedule.every().day.at(HORA_EJECUCION).do(tarea_diaria)
    while True:
        schedule.run_pending()
        time.sleep(60)

def menu():
    """Interfaz de usuario en consola."""
    inicializar_csv()
    
    # Iniciar el hilo del programador (Daemon para que cierre con el programa)
    hilo_auto = threading.Thread(target=run_scheduler, daemon=True)
    hilo_auto.start()

    while True:
        print(f"\n" + "="*45)
        print(f"   🛰️  SISTEMA CENTRAL - BOT CAZADOR AUTO")
        print(f"   Estado: AUTO-ACTIVO | Hora: {HORA_EJECUCION}")
        print(f"   Destino: {GRUPO_ID}")
        print("="*45)
        print("[1] Ejecutar cacería de tendencias AHORA")
        print("[2] Ver historial de publicaciones (CSV)")
        print("[3] Ver configuración y límites")
        print("[4] Vaciar historial de publicaciones")
        print("[5] Enviar mensaje de prueba al grupo")
        print("[0] Salir")
        print("="*45)
        
        opcion = input("💻 Seleccione una opción: ")

        if opcion == "1":
            tarea_diaria()
        elif opcion == "2":
            mostrar_historial()
        elif opcion == "3":
            print(f"\n⚙️  DETALLES TÉCNICOS:")
            print(f"   📍 Canal/Grupo: {GRUPO_ID}")
            print(f"   📦 Stock diario: {LIMITE_DIARIO} mensajes")
            print(f"   ⏰ Programación: {HORA_EJECUCION} cada día")
            print(f"   📂 Archivo: {ARCHIVO_HISTORIAL}\n")
        elif opcion == "4":
            confirmar = input("⚠️  ¿Borrar permanentemente el historial CSV? (s/n): ")
            if confirmar.lower() == 's':
                borrar_historial()
        elif opcion == "5":
            enviar_prueba_grupo()
        elif opcion == "0":
            print("👋 Cerrando sistema...")
            break
        else:
            print("❌ Opción inválida. Intente de nuevo.")

if __name__ == "__main__":
    menu()