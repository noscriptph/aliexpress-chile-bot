import os
import time
import hashlib
import requests
import telebot
from dotenv import load_dotenv

# Cargar credenciales desde el archivo .env
load_dotenv()
APP_KEY = os.getenv("ALI_APP_KEY")
APP_SECRET = os.getenv("ALI_APP_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TRACKING_ID = "telegram_chile_bot"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def obtener_firma(params):
    """
    Algoritmo de firma oficial de AliExpress.
    Ordena los parámetros alfabéticamente y los cifra con el Secret.
    """
    # Ordenar parámetros alfabéticamente
    sorted_params = sorted(params.items())
    # Concatenar: Secret + LlaveValor + Secret
    query_string = "".join(f"{k}{v}" for k, v in sorted_params)
    sign_str = f"{APP_SECRET}{query_string}{APP_SECRET}"
    # Devolver MD5 en mayúsculas
    return hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()

def consultar_producto(link_original):
    """
    Usa la API 'aliexpress.affiliate.link.generate' para convertir el link.
    """
    endpoint = "https://gw.api.alibaba.com/openapi/param2/2/portals.open/api.getPromotionLinks/" + APP_KEY
    
    # Parámetros básicos requeridos por la API
    params = {
        "app_key": APP_KEY,
        "format": "json",
        "method": "aliexpress.affiliate.link.generate",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "v": "2.0",
        "sign_method": "md5",
        "promotion_link_type": "0",
        "source_values": link_original,
        "tracking_id": TRACKING_ID
    }
    
    # Añadir la firma calculada
    params["sign"] = obtener_firma(params)
    
    try:
        response = requests.get(endpoint, params=params)
        data = response.json()
        # Navegar en el JSON de respuesta de AliExpress
        res_list = data.get("aliexpress_affiliate_link_generate_response", {}).get("resp_result", {}).get("result", {}).get("promot_links", [])
        return res_list[0] if res_list else link_original
    except Exception as e:
        print(f"Error en API: {e}")
        return link_original

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🇨🇱 **Bot AliExpress Chile conectado.**\nEnvíame un link para generar tu oferta con comisión.")

@bot.message_handler(func=lambda m: "aliexpress.com" in m.text)
def handle_aliexpress_link(message):
    bot.send_chat_action(message.chat.id, 'typing')
    link_convertido = consultar_producto(message.text)
    
    texto = (
        "🔥 **OFERTA SELECCIONADA** 🔥\n\n"
        f"🔗 **Link:** {link_convertido}\n\n"
        "✅ Envío validado para Chile."
    )
    bot.reply_to(message, texto, parse_mode="Markdown")

if __name__ == "__main__":
    print("Servidor local iniciado. Esperando mensajes...")
    bot.polling()