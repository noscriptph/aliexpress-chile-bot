import os
import telebot
from dotenv import load_dotenv
import utils          # Lógica de API, IA y búsqueda
import scraper_fotos  # Lógica de fotos reales de clientes

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

@bot.message_handler(func=lambda m: "aliexpress.com" in m.text)
def handle_link(message):
    # --- LOG DE CONSOLA ---
    nombre_usuario = message.from_user.first_name
    tag_usuario = f"@{message.from_user.username}" if message.from_user.username else "Sin nick"
    print(f"\n[NUEVO MENSAJE] {nombre_usuario} ({tag_usuario}) envió un link.")
    
    bot.send_chat_action(message.chat.id, 'typing')
    url_usuario = message.text
    
    # 1. Investigar mejor oferta
    print(" -> Paso 1: Consultando Cerebro (IA) y API AliExpress...")
    resultado, debug = utils.investigar_mejor_oferta(url_usuario)
    
    # --- LOG DE CONSOLA: Resultado ---
    origen_log = "Gemma 3 (IA)" if debug["ia_activa"] else "Analizador (Código)"
    print(f"    [INFO] Término: '{debug['termino_usado']}' | Fuente: {origen_log}")
    print(f"    [INFO] Candidatos encontrados: {debug['total_encontrados']}")
    
    # --- REPORTE TÉCNICO EN TELEGRAM ---
    estado_ia = "✅ Gemma 3 Activa" if debug["ia_activa"] else "⚠️ IA Offline (Respaldo activo)"
    info_debug = (
        f"🔍 <b>REPORTE DE BÚSQUEDA</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🤖 <b>Estado IA:</b> {estado_ia}\n"
        f"🏷️ <b>Buscado como:</b> <code>{debug['termino_usado']}</code>\n"
        f"📦 <b>Encontrados:</b> {debug['total_encontrados']} productos\n"
    )
    
    if debug["error"]:
        print(f"    [ERROR] Detalle técnico: {debug['error']}")
        info_debug += f"❌ <b>Error API:</b> <code>{debug['error']}</code>"
    
    bot.send_message(message.chat.id, info_debug, parse_mode="HTML")

    if resultado:
        print(" -> Paso 2: Buscando fotos reales de clientes...")
        # 2. Scraping de fotos reales
        datos_visuales = scraper_fotos.obtener_fotos_reales(url_usuario)
        
        # Construcción del mensaje de oferta
        caption = (
            f"<b>🔥 MEJOR OPCIÓN ENCONTRADA 🔥</b>\n\n"
            f"📦 <b>Producto:</b> {resultado['titulo'][:70]}...\n"
            f"💰 <b>Precio:</b> ${resultado['precio']} USD\n"
            f"🚚 <b>Envío:</b> ${resultado['envio']} USD (Validado < 10%)\n\n"
            f"🔗 <b>Link:</b> <a href='{resultado['link']}'>Ver en AliExpress</a>"
        )
        
        # Enviar foto principal
        try:
            bot.send_photo(message.chat.id, resultado['foto'], caption=caption, parse_mode="HTML")
            print(" -> [OK] Oferta enviada a Telegram.")
        except Exception as e:
            print(f"    [Error] No se pudo enviar la foto principal: {e}")
            bot.send_message(message.chat.id, caption, parse_mode="HTML")

        # 3. Álbum de fotos de clientes
        if datos_visuales['resenas']:
            print(f" -> Paso 3: Preparando álbum de {len(datos_visuales['resenas'])} fotos...")
            bot.send_chat_action(message.chat.id, 'upload_photo')
            
            media_group = []
            for url_foto in datos_visuales['resenas'][:4]: # Máximo 4 para no saturar
                media_group.append(telebot.types.InputMediaPhoto(url_foto))
            
            if media_group:
                try:
                    bot.send_message(message.chat.id, "📸 <b>Fotos reales de compradores:</b>", parse_mode="HTML")
                    bot.send_media_group(message.chat.id, media_group)
                    print(" -> [OK] Álbum de fotos enviado.")
                except Exception as e:
                    print(f"    [Error] Fallo al enviar álbum: {e}")
    else:
        print(" -> [!] Proceso finalizado sin oferta válida.")
        if debug['total_encontrados'] > 0:
            bot.reply_to(message, "❌ No encontré el producto con envío barato (< 10%).")
        else:
            bot.reply_to(message, "❌ No hay resultados similares para este producto.")

if __name__ == "__main__":
    print("---------------------------------------")
    print("   SISTEMA DE OFERTAS CHILE ACTIVO")
    print("   IA: Gemma 3 (Ollama) | API: Ali")
    print("---------------------------------------")
    bot.polling(none_stop=True)