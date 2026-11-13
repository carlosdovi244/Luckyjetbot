import os
import asyncio
import aiohttp
import json
import logging
import websockets
from aiohttp import web

# Configuration des logs
logging.basicConfig(level=logging.INFO)

# Identifiants Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN", "9109662984:AAE3N4vqzQTfl8ihHtpQIEZ-WHmzm3lMHmw")
CHAT_ID = os.getenv("CHAT_ID", "5348890650")

# URL du WebSocket du jeu
WS_URL = "wss://ws.smartikowheel.com/websocket/services?master&domain=1wyvev.life&version=1.3.595"

# États du bot
consecutive_blues = 0
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

async def monitor_lucky_jet():
    """Se connecte au WebSocket et écoute les résultats."""
    global consecutive_blues, alert_sent
    
    while True:
        try:
            logging.info("Tentative de connexion au WebSocket...")
            async with websockets.connect(WS_URL) as websocket:
                logging.info("Connecté au WebSocket avec succès !")
                
                async for message in websocket:
                    try:
                        # Affichage brut pour analyser le format dans les logs Render
                        logging.info(f"Message brut reçu : {message}")
                        
                        # Parsing du message JSON
                        data = json.loads(message)
                        
                        # Recherche d'une valeur numérique représentant le multiplicateur dans le message
                        # (On parcourt les clés courantes ou les structures possibles)
                        val = None
                        if isinstance(data, dict):
                            # Cherche des clés communes ou extrait la première valeur numérique trouvée
                            for key in ["multiplier", "result", "val", "coef", "p"]:
                                if key in data:
                                    val = data[key]
                                    break
                            if val is None and len(data) > 0:
                                # Essaye de récupérer la première valeur si c'est un dictionnaire de données de jeu
                                for v in data.values():
                                    if isinstance(v, (int, float)):
                                        val = v
                                        break
                                    elif isinstance(v, str) and v.replace('.', '', 1).isdigit():
                                        val = float(v)
                                        break

                        if val is not None:
                            multiplier = float(val)
                            
                            # Application de ta règle : Bleu entre 1.00 et 1.99
                            if 1.00 <= multiplier <= 1.99:
                                if not alert_sent:
                                    consecutive_blues += 1
                                    logging.info(f"-> Bleu détecté : {multiplier}x | Compteur consécutif : {consecutive_blues}")
                                    
                                    if consecutive_blues >= 2:
                                        await send_telegram_alert(f"🚨 **ALERTE LUCKY JET**\n2 multiplicateurs bleus consécutifs détectés (entre 1.00 et 1.99) !\nDernier : {multiplier}x")
                                        alert_sent = True
                            elif multiplier >= 2.00:
                                # Cassure par un violet ou orange
                                logging.info(f"-> Cassure détectée par {multiplier}x. Remise à zéro du compteur.")
                                consecutive_blues = 0
                                alert_sent = False

                    except json.JSONDecodeError:
                        # Ce n'est pas du JSON (ex: messages de ping du serveur), on ignore
                        pass
                    except Exception as inner_e:
                        logging.error(f"Erreur de traitement d'un message: {inner_e}")

        except Exception as e:
                    logging.error(f"Erreur de connexion WebSocket: {e}. Nouvelle tentative dans 5 secondes...")
                    await asyncio.sleep(5)

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
