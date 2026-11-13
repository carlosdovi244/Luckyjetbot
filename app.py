import os
import asyncio
import aiohttp
import logging
from aiohttp import web

# Configuration des logs
logging.basicConfig(level=logging.INFO)

# Identifiants Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN", "9109662984:AAE3N4vqzQTfl8ihHtpQIEZ-WHmzm3lMHmw")
CHAT_ID = os.getenv("CHAT_ID", "5348890650")

# États du bot pour la logique des séries
consecutive_blues = 0
waiting_for_violet_series = True
alert_sent = False

async def send_telegram_alert(message):
    """Envoie une notification sur Telegram."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    logging.info("Alerte Telegram envoyée avec succès !")
                else:
                    logging.error(f"Erreur Telegram: {await response.text()}")
    except Exception as e:
        logging.error(f"Erreur connexion Telegram: {e}")

def classify_multiplier(val):
    """Classe le multiplicateur : bleu (<2.0), violet (2.0 à 9.99), orange (>=10.0)."""
    if val < 2.0:
        return "blue"
    elif val < 10.0:
        return "purple"
    else:
        return "orange"

async def monitor_lucky_jet():
    """Surveille les multiplicateurs selon la logique des séries de violets et de bleus."""
    global consecutive_blues, waiting_for_violet_series, alert_sent
    
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                await asyncio.sleep(5) # Intervalle de vérification
                
                # --- Simulation ou récupération du dernier multiplicateur du jeu ---
                current_multiplier = 1.35  
                color = classify_multiplier(current_multiplier)
                
                logging.info(f"Résultat reçu : {current_multiplier}x ({color})")

                if color == "purple" or color == "orange":
                    # Cassure par un violet ou orange
                    logging.info(f"Cassure par un {color} ({current_multiplier}x).")
                    waiting_for_violet_series = False
                    consecutive_blues = 0
                    alert_sent = False

                elif color == "blue":
                    consecutive_blues += 1
                    logging.info(f"Multiplicateur bleu détecté. Série en cours : {consecutive_blues}")
                    
                    # Condition : 2 bleus consécutifs
                    if consecutive_blues >= 2 and not alert_sent:
                        await send_telegram_alert(f"🚨 **ALERTE LUCKY JET**\n2 multiplicateurs bleus consécutifs détectés !\nDernier résultat : {current_multiplier}x")
                        alert_sent = True

        except Exception as e:
            logging.error(f"Erreur dans la boucle de surveillance : {e}")
            await asyncio.sleep(10)

# Serveur web minimal pour maintenir Render éveillé
async def handle(request):
    return web.Response(text="Lucky Jet Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Serveur web actif sur le port {port}")

async def main():
    await asyncio.gather(
        start_web_server(),
        monitor_lucky_jet()
    )

if __name__ == "__main__":
    asyncio.run(main())
