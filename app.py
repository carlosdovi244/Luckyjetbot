import os
import asyncio
import aiohttp
import json
import logging
from aiohttp import web

# Configuration des logs
logging.basicConfig(level=logging.INFO)

# Récupération des identifiants Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN", "9109662984:AAE3N4vqzQTfl8ihHtpQIEZ-WHmzm3lMHmw")
CHAT_ID = os.getenv("CHAT_ID", "5348890650")

# Variables d'état
consecutive_blues = 0
alert_already_sent = False  # Verrou pour stopper les alertes en boucle

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
                    logging.error(f"Erreur d'envoi Telegram: {await response.text()}")
    except Exception as e:
        logging.error(f"Erreur connexion Telegram: {e}")

async def monitor_lucky_jet():
    """Surveille les multiplicateurs et s'arrête après une alerte jusqu'à un reset."""
    global consecutive_blues, alert_already_sent
    
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                await asyncio.sleep(5)
                
                # Simulation d'un multiplicateur (À adapter selon ton flux réel)
                multiplier = 1.25  
                is_purple_or_orange = False # Remplace par ta condition de violet/orange
                
                # Si une alerte a déjà été envoyée, on attend qu'un "violet" réinitialise le système
                if alert_already_sent:
                    if is_purple_or_orange:
                        logging.info("Nouveau violet détecté : réinitialisation du système d'alerte.")
                        consecutive_blues = 0
                        alert_already_sent = False  # On déverrouille pour de futures alertes
                    continue  # On ignore tant qu'on n'a pas eu le signal de reset

                # --- LOGIQUE DE TEST : 2 BLEUS CONSÉCUTIFS ---
                if 1.0 <= multiplier < 2.0:
                    consecutive_blues += 1
                    logging.info(f"Multiplicateur bleu détecté : {multiplier} (Total : {consecutive_blues})")
                    
                    if consecutive_blues >= 2 and not alert_already_sent:
                        await send_telegram_alert("🚨 **ALERTE STOP** : 2 multiplicateurs bleus consécutifs détectés ! En attente d'un nouveau violet...")
                        alert_already_sent = True  # Verrouille pour stopper les envois en double
                else:
                    consecutive_blues = 0  
                    
        except Exception as e:
                    logging.error(f"Erreur dans la boucle de surveillance: {e}")
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
