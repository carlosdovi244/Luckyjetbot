import os
import asyncio
import aiohttp
import json
import logging
import websockets
from aiohttp import web

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ========== IDENTIFIANTS (à mettre dans Render) ==========
BOT_TOKEN = os.getenv("9109662984:AAE3N4vqzQTfl8ihHtpQIEZ-WHmzm3lMHmw")
CHAT_ID = os.getenv("9109662984")

# Vérification au démarrage
if not BOT_TOKEN or not CHAT_ID:
    logging.error("ERREUR : BOT_TOKEN ou CHAT_ID manquant dans les variables d'environnement !")
    raise SystemExit("Configure BOT_TOKEN et CHAT_ID dans Render")

# URL du WebSocket
WS_URL = "wss://ws.smartikowheel.com/websocket/services?master&domain=1wyvev.life&version=1.3.595"

# États
consecutive_blues = 0
alert_sent = False

async def send_telegram_alert(message: str):
    """Envoie une notification Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=10) as response:
                if response.status == 200:
                    logging.info("✅ Alerte Telegram envoyée avec succès")
                else:
                    logging.error(f"❌ Erreur Telegram : {await response.text()}")
    except Exception as e:
        logging.error(f"❌ Impossible d'envoyer l'alerte Telegram : {e}")


def extract_multiplier(data):
    """Essaie d'extraire le multiplicateur de façon plus robuste"""
    if not isinstance(data, dict):
        return None

    # Clés possibles les plus courantes
    possible_keys = ["multiplier", "result", "coef", "value", "p", "x", "crash", "rate"]
    
    for key in possible_keys:
        if key in data:
            try:
                return float(data[key])
            except (ValueError, TypeError):
                continue

    # Recherche récursive dans les valeurs
    for value in data.values():
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            cleaned = value.replace("x", "").replace(",", ".").strip()
            try:
                return float(cleaned)
            except ValueError:
                continue
        if isinstance(value, dict):
            found = extract_multiplier(value)
            if found is not None:
                return found

    return None


async def monitor_lucky_jet():
    """Surveille le jeu en continu"""
    global consecutive_blues, alert_sent

    while True:
        try:
            logging.info("🔌 Tentative de connexion au WebSocket...")
            async with websockets.connect(WS_URL, ping_interval=20, ping_timeout=20) as websocket:
                logging.info("✅ Connecté au WebSocket")

                async for message in websocket:
                    try:
                        # On ignore les messages non-JSON (ping/pong)
                        if not message.startswith("{") and not message.startswith("["):
                            continue

                        data = json.loads(message)
                        multiplier = extract_multiplier(data)

                        if multiplier is None:
                            continue

                        # ===== RÈGLE DES 2 BLEUS =====
                        if 1.00 <= multiplier <= 1.99:
                            if not alert_sent:
                                consecutive_blues += 1
                                logging.info(f"🔵 Bleu détecté : {multiplier}x | Compteur = {consecutive_blues}")

                                if consecutive_blues >= 2:
                                    await send_telegram_alert(
                                        f"🚨 *ALERTE LUCKY JET*\n\n"
                                        f"2 multiplicateurs **bleus** consécutifs détectés !\n"
                                        f"Dernier : *{multiplier}x*"
                                    )
                                    alert_sent = True
                                    consecutive_blues = 0  # On remet à zéro après l'alerte
                        else:
                            # Tout ce qui n'est pas bleu casse la série
                            if consecutive_blues > 0 or alert_sent:
                                logging.info(f"⚪ Cassure par {multiplier}x → Remise à zéro")
                            consecutive_blues = 0
                            alert_sent = False

                    except json.JSONDecodeError:
                        pass
                    except Exception as e:
                        logging.error(f"Erreur traitement message : {e}")

        except Exception as e:
            logging.error(f"❌ Connexion perdue : {e}")
            logging.info("Nouvelle tentative dans 5 secondes...")
            await asyncio.sleep(5)


# ===== Serveur web pour garder Render actif =====
async def handle(request):
    return web.Response(text="Lucky Jet Bot is running ✅")


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"🌐 Serveur web actif sur le port {port}")


async def main():
    await asyncio.gather(
        start_web_server(),
        monitor_lucky_jet()
    )


if __name__ == "__main__":
    asyncio.run(main())
