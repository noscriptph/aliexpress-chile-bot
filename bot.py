import os
import telebot
from dotenv import load_dotenv
import utils          # Lógica de API, IA y búsqueda
import scraper_fotos  # Lógica de fotos reales de clientes
import time

# Carga de configuración
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "<b>🇨🇱 Investigador de Ofertas Pro</b>\n\n"
        "¡Hola! Envíame un link de AliExpress y haré lo siguiente:\n"
        "1. Usaré <b>Gemma 3 (IA)</b> para entender qué es.\n"
        "2. Buscaré la mejor oferta con <b>envío bajo a Chile</b>.\n"
        "3. Te mostraré <b>fotos reales</b> de otros compradores."
    )
    bot.reply_to(message, welcome_text, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text and "aliexpress.com" in m.text)
def handle_link(message):
    # --- LOG DE CONSOLA ---
    nombre_usuario = message.from_user.first_name
    tag_usuario = f"@{message.from_user.username}" if message.from_user.username else "Sin nick"
    print(f"\n[NUEVO MENSAJE] {nombre_usuario} ({tag_usuario}) envió un link.")
    
    # 1. Mensaje inicial de espera
    status_msg = bot.reply_to(message, "⏳ <b>Iniciando Cerebro (Gemma 3)...</b>", parse_mode="HTML")
    
    def update_status(text):
        """Función callback para actualizar el estado en Telegram en tiempo real."""
        try:
            bot.edit_message_text(text, message.chat.id, status_msg.message_id, parse_mode="HTML")
        except Exception:
            pass # Evita errores si el mensaje es idéntico

    bot.send_chat_action(message.chat.id, 'typing')
    url_usuario = message.text
    
    # 2. Investigar mejor oferta (Pasamos la función update_status como callback)
    print(" -> Paso 1: Consultando Cerebro (IA) y API AliExpress...")
    inicio_busqueda = time.time()
    
    # Llamada a la función con el sistema de niveles informativos
    resultado, debug = utils.investigar_mejor_oferta(url_usuario, callback_status=update_status)
    
    tiempo_total = round(time.time() - inicio_busqueda, 1)
    
    # --- LOG DE CONSOLA: Resultado ---
    origen_log = resultado.get("fuente_exito", "Ninguna") if resultado else "Fallo total"
    print(f"    [INFO] Término: '{debug['termino_usado']}' | Fuente: {origen_log}")
    print(f"    [INFO] Candidatos encontrados: {debug['total_encontrados']}")
    
    # --- ACTUALIZAR REPORTE TÉCNICO FINAL ---
    estado_ia = "✅ Gemma 3 Activa" if debug["ia_activa"] else "⚠️ IA Offline (Respaldo activo)"
    reporte_niveles = "\n".join(debug.get("mensajes", []))
    
    info_debug = (
        f"🔍 <b>REPORTE DE BÚSQUEDA</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🤖 <b>IA:</b> {estado_ia}\n"
        f"🏷️ <b>Buscado como:</b> <code>{debug['termino_usado']}</code>\n"
        f"📦 <b>Total analizados:</b> {debug['total_encontrados']}\n"
        f"⏱️ <b>Tiempo total:</b> {tiempo_total}s\n\n"
        f"📊 <b>Progreso de niveles:</b>\n{reporte_niveles}"
    )
    
    if debug["error"]:
        info_debug += f"\n❌ <b>Error:</b> <code>{debug['error']}</code>"
    
    # Editamos el mensaje final de reporte
    update_status(info_debug)

    if resultado:
        print(" -> Paso 2: Buscando fotos reales de clientes...")
        bot.send_chat_action(message.chat.id, 'upload_photo')
        
        # 3. Scraping de fotos reales
        datos_visuales = scraper_fotos.obtener_fotos_reales(url_usuario)
        
        # Construcción del mensaje de oferta
        porcentaje_envio = round((resultado['envio'] / resultado['precio']) * 100, 1) if resultado['precio'] > 0 else 0
        
        # Alerta si es carga pesada (Nivel 3)
        alerta_envio = "⚠️ <b>Envío elevado detectado (Carga Pesada/Volumen)</b>\n" if porcentaje_envio > 30 else ""

        caption = (
            f"<b>🔥 MEJOR OPCIÓN ENCONTRADA 🔥</b>\n\n"
            f"📦 <b>Producto:</b> {resultado['titulo'][:80]}...\n"
            f"💰 <b>Precio:</b> ${resultado['precio']} USD\n"
            f"🚚 <b>Envío:</b> ${resultado['envio']} USD ({porcentaje_envio}% del valor)\n"
            f"🎯 <b>Método:</b> {resultado.get('fuente_exito', 'API')}\n\n"
            f"{alerta_envio}"
            f"🔗 <b>Link:</b> <a href='{resultado['link']}'>Ver en AliExpress</a>"
        )
        
        # Enviar foto principal
        try:
            bot.send_photo(message.chat.id, resultado['foto'], caption=caption, parse_mode="HTML")
            print(" -> [OK] Oferta enviada.")
        except Exception as e:
            bot.send_message(message.chat.id, caption, parse_mode="HTML")

        # 4. Álbum de fotos de clientes
        if datos_visuales and datos_visuales.get('resenas'):
            media_group = []
            for url_foto in datos_visuales['resenas'][:4]:
                media_group.append(telebot.types.InputMediaPhoto(url_foto))
            
            if media_group:
                try:
                    bot.send_message(message.chat.id, "📸 <b>Fotos reales capturadas:</b>", parse_mode="HTML")
                    bot.send_media_group(message.chat.id, media_group)
                except Exception:
                    pass
    else:
        # Mensaje de error detallado
        if debug['total_encontrados'] > 0:
            bot.send_message(message.chat.id, "❌ <b>Sin éxito:</b> Los productos encontrados superan incluso el umbral de carga pesada (45% del valor).")
        else:
            bot.send_message(message.chat.id, "❌ <b>Sin éxito:</b> No se encontraron productos similares en la base de datos de AliExpress.")

if __name__ == "__main__":
    print("---------------------------------------")
    print("   SISTEMA DE OFERTAS CHILE ACTIVO")
    print("   IA: Gemma 3 (Ollama) | API: Ali")
    print("---------------------------------------")
    bot.polling(none_stop=True)