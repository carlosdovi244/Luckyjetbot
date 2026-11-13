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

# Compteur pour suivre les multiplicateurs bleus consécutifs
consecutive_blues = 0

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
    """Se connecte au flux et surveille l'apparition de 2 bleus consécutifs."""
    global consecutive_blues
    url = "https://1win.win/luckyjet"  # Remplace par l'URL du websocket cible si nécessaire
    
    while True:
        try:
            logging.info("Connexion au flux en cours...")
            async with aiohttp.ClientSession() as session:
                # Simulation de l'écoute du flux ou connexion WebSocket
                # Ici on simule la réception d'un multiplicateur pour l'exemple de test
                await asyncio.sleep(5)
                
                # --- LOGIQUE DE TEST : 2 BLEUS CONSÉCUTIFS ---
                # Un multiplicateur bleu est compris entre 1.0 et 1.99
                # Pour le test, on va simuler un multiplicateur bleu reçu :
                multiplier = 1.25  # (Exemple de test)
                
                if 1.0 <= multiplier < 2.0:
                    consecutive_blues += 1
                    logging.info(f"Multiplicateur bleu détecté : {multiplier} (Total consécutif : {consecutive_blues})")
                    
                    if consecutive_blues >= 2:
                        await send_telegram_alert("🚨 **TEST RÉUSSI** : 2 multiplicateurs bleus consécutifs détectés !")
                        consecutive_blues = 0  # Réinitialisation après l'alerte
                else:
                    consecutive_blues = 0  # Réinitialisation si ce n'est pas un bleu
                    
        except Exception as e:
                    logging.error(f"Erreur dans la boucle de surveillance: {e}")
                    await asyncio.sleep(10)

# Serveur web minimal pour maintenir le service Render éveillé (évite le mode veille)
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
    logging.info(f"Serveur web de maintien en ligne actif sur le port {port}")

async def main():
    # Lance le serveur web et le moniteur en même temps
    await asyncio.gather(
        start_web_server(),
        monitor_lucky_jet()
    )

if __name__ == "__main__":
    asyncio.run(main())
