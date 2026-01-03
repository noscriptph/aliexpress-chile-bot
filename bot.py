import os
import telebot
from dotenv import load_dotenv
import utils          # Lógica de API, IA y búsqueda
import scraper_fotos  # Lógica de fotos reales de clientes

load_dotenv()
bot = telebot.TeleBot(os.getenv("TELEGRAM_TOKEN"))

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "<b>🇨🇱 Investigador de Ofertas Pro</b>\n\nEnvíame un link y usaré <b>Gemma 3</b> para encontrar la mejor opción con envío bajo a Chile.", parse_mode="HTML")

@bot.message_handler(func=lambda m: "aliexpress.com" in m.text)
def handle_link(message):
    bot.send_chat_action(message.chat.id, 'typing')
    url_usuario = message.text
    
    # 1. Investigar mejor oferta y obtener reporte de depuración
    # Ahora utils.investigar_mejor_oferta devuelve dos cosas: (resultado, debug)
    resultado, debug = utils.investigar_mejor_oferta(url_usuario)
    
    # --- MENSAJE DE DEPURACIÓN (Independiente) ---
    estado_ia = "✅ Gemma 3 Activa" if debug["ia_activa"] else "⚠️ IA Local Offline (Usando Analizador)"
    info_debug = (
        f"🔍 <b>REPORTE DE BÚSQUEDA</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🤖 <b>Estado IA:</b> {estado_ia}\n"
        f"🏷️ <b>Buscado como:</b> <code>{debug['termino_usado']}</code>\n"
        f"📦 <b>Encontrados:</b> {debug['total_encontrados']} productos\n"
    )
    
    if debug["error"]:
        info_debug += f"❌ <b>Error:</b> <code>{debug['error']}</code>"
    
    bot.send_message(message.chat.id, info_debug, parse_mode="HTML")
    # ---------------------------------------------

    if resultado:
        # 2. Buscar fotos reales de clientes (Scraping)
        # Intentamos sacar fotos del link original que tiene las reseñas
        datos_visuales = scraper_fotos.obtener_fotos_reales(url_usuario)
        
        caption = (
            f"<b>🔥 MEJOR OPCIÓN ENCONTRADA 🔥</b>\n\n"
            f"📦 <b>Producto:</b> {resultado['titulo'][:60]}...\n"
            f"💰 <b>Precio:</b> ${resultado['precio']}\n"
            f"🚚 <b>Envío:</b> Validado &lt; 10%\n\n"
            f"🔗 <b>Link:</b> <a href='{resultado['link']}'>Ver en AliExpress</a>"
        )
        
        # Enviamos la foto principal (de la API) con el link de afiliado
        bot.send_photo(message.chat.id, resultado['foto'], caption=caption, parse_mode="HTML")

        # 3. Álbum de fotos de clientes (si existen)
        if datos_visuales['resenas']:
            bot.send_chat_action(message.chat.id, 'upload_photo')
            media_group = []
            for i, url_foto in enumerate(datos_visuales['resenas']):
                if i < 4: # Límite de 4 fotos para no saturar
                    media_group.append(telebot.types.InputMediaPhoto(url_foto))
            
            if media_group:
                bot.send_message(message.chat.id, "📸 <b>Fotos reales de compradores:</b>", parse_mode="HTML")
                bot.send_media_group(message.chat.id, media_group)
    else:
        # Si no hubo resultado pero sí debug, informamos por qué
        if debug['total_encontrados'] > 0:
            bot.reply_to(message, "❌ Se encontraron productos pero ninguno cumplía la regla de envío &lt; 10%.")
        else:
            bot.reply_to(message, "❌ No se encontraron productos similares con el término generado.")

if __name__ == "__main__":
    print("---------------------------------------")
    print("Bot con Inteligencia Local Iniciado")
    print("Ollama: Gemma 3 | API: AliExpress")
    print("---------------------------------------")
    bot.polling(none_stop=True)