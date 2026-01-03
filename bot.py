import os
import telebot
from dotenv import load_dotenv
import utils          # Lógica de API y búsqueda
import scraper_fotos  # Lógica de fotos reales de clientes

load_dotenv()
bot = telebot.TeleBot(os.getenv("TELEGRAM_TOKEN"))

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "<b>🇨🇱 Investigador de Ofertas Chile</b>\nEnvíame un link y buscaré la mejor opción con envío barato y fotos reales.", parse_mode="HTML")

@bot.message_handler(func=lambda m: "aliexpress.com" in m.text)
def handle_link(message):
    bot.send_chat_action(message.chat.id, 'typing')
    url_usuario = message.text
    
    # 1. Investigar la mejor oferta mediante API (en utils.py)
    resultado = utils.investigar_mejor_oferta(url_usuario)
    
    if resultado:
        # 2. Buscar fotos reales de clientes (en scraper_fotos.py)
        # Usamos el link que el bot encontró para que las fotos coincidan con la oferta
        datos_visuales = scraper_fotos.obtener_fotos_reales(resultado['link'])
        
        caption = (
            f"<b>🔥 MEJOR OPCIÓN ENCONTRADA 🔥</b>\n\n"
            f"📦 <b>Producto:</b> {resultado['titulo'][:50]}...\n"
            f"💰 <b>Precio:</b> ${resultado['precio']}\n"
            f"🚚 <b>Envío:</b> Validado &lt; 10%\n\n"
            f"🔗 <b>Link:</b> <a href='{resultado['link']}'>Ver en AliExpress</a>"
        )
        
        # Enviamos la oferta principal
        bot.send_photo(message.chat.id, resultado['foto'], caption=caption, parse_mode="HTML")

        # 3. Si hay fotos de reseñas, las enviamos en un grupo (álbum)
        if datos_visuales['resenas']:
            bot.send_chat_action(message.chat.id, 'upload_photo')
            media_group = []
            for i, url_foto in enumerate(datos_visuales['resenas']):
                # Limitamos a 4 fotos para no saturar
                if i < 4:
                    media_group.append(telebot.types.InputMediaPhoto(url_foto))
            
            if media_group:
                bot.send_message(message.chat.id, "📸 <b>Fotos reales de compradores:</b>", parse_mode="HTML")
                bot.send_media_group(message.chat.id, media_group)
    else:
        bot.reply_to(message, "No encontré una mejor oferta con envío &lt; 10% para Chile, pero puedes intentar con otro producto.")

if __name__ == "__main__":
    print("---------------------------------------")
    print("Bot con Búsqueda e Imágenes iniciado...")
    print("---------------------------------------")
    bot.polling(none_stop=True)