"""Educational Telegram bot. Uses only Python's standard library."""
import json
import logging
import os
import signal
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

NAME = "eSIM Store"
ABOUT = "Educational eSIM guide: learn the basics, check compatibility and explore setup tips. No sales or external links."
DESCRIPTION = (
    "eSIM Store is an educational assistant, not a shop. Learn how eSIMs work, "
    "how to check device compatibility, and how installation and activation work. "
    "Use the three menu buttons for guides inside Telegram. "
    "No eSIM sales, payments, external links or automatic device checks."
)
BASICS = """eSIM Basics

An eSIM is a digital SIM profile used on a compatible device instead of inserting a physical SIM card. A mobile provider supplies the profile.

Installation adds the profile to your device; activation and plan validity depend on the provider. Some plans are data-only and do not include a phone number, calls or SMS.

Before choosing a plan, check country coverage, data allowance, validity, hotspot rules and when validity begins. This bot provides education only and does not sell or activate eSIMs."""
COMPATIBILITY = """Compatibility Guide

1. Find your exact device model and the region where it was sold. Support can vary between regional versions of the same model.
2. On iPhone, look under Settings > Cellular or Mobile Data for Add eSIM. On Android, look under Settings > Connections or Network & Internet > SIM manager or SIMs for an add-eSIM option. Labels vary.
3. An EID in device information can indicate eSIM hardware, but does not guarantee support for every provider.
4. Check whether your device is carrier unlocked and whether the intended provider supports the exact model.

This is a self-check guide. The bot cannot scan your phone or confirm compatibility. Never send an activation QR code, password or identity document here."""
SETUP = """Setup & Help

General installation:
1. Confirm compatibility and read your provider's activation and validity instructions.
2. Use a reliable internet connection. In your device's SIM settings, choose Add eSIM.
3. Scan the provider's QR code or enter its activation details in the device settings. Keep these details private.
4. Label the new line and select the intended line for mobile data.
5. Enable data roaming on that line only if the provider requires it. Check your primary line's roaming and automatic data-switching settings to avoid unexpected charges.

If data does not work, check that the line is enabled, selected for data, within coverage and has an active allowance. Use the provider's exact APN settings if required. Try airplane mode or restart the device.

Do not delete a profile while troubleshooting: reinstalling may require a replacement from the provider. This bot cannot issue profiles, access accounts or activate service."""
CONTENT = {"eSIM Basics": BASICS, "Compatibility Guide": COMPATIBILITY, "Setup & Help": SETUP}
COMMANDS = {"basics": BASICS, "compatibility": COMPATIBILITY, "setup": SETUP}
KEYBOARD = {
    "keyboard": [[{"text": label}] for label in CONTENT],
    "resize_keyboard": True,
    "is_persistent": True,
}
WELCOME = (
    "Welcome to eSIM Store.\n\n"
    "Your educational eSIM assistant. Learn the basics, check compatibility "
    "and read setup guidance using the three buttons below.\n\n"
    "This bot does not sell eSIMs, take payments or open external websites."
)

class TelegramError(Exception):
    def __init__(self, code, retry_after=5):
        self.code = code
        self.retry_after = retry_after
        super().__init__(f"Telegram API error {code}")

class TelegramAPI:
    def __init__(self, token):
        self.base = "https://api.telegram.org/bot" + token + "/"

    def call(self, method, **payload):
        request = Request(
            self.base + method,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urlopen(request, timeout=45) as response:
                result = json.load(response)
        except HTTPError as error:
            try:
                result = json.loads(error.read())
            except (ValueError, UnicodeDecodeError):
                raise TelegramError(error.code) from None
        if not result.get("ok"):
            raise TelegramError(
                result.get("error_code", 500),
                result.get("parameters", {}).get("retry_after", 5),
            )
        return result["result"]

def reply_for(text):
    text = (text or "").strip()
    command = text.split(maxsplit=1)[0].split("@")[0].lower() if text else ""
    if command in ("/start", "/help", "/menu"):
        return WELCOME
    if command == "/privacy":
        return (
            "Privacy\n\nThis bot reads messages to answer your requests. "
            "It does not persist messages, user IDs or profiles to a database or files. "
            "Updates are processed in memory and replies are sent through Telegram. "
            "Operational logs do not include message text or chat IDs. "
            "Telegram processes messages under its own policies. "
            "Do not send personal documents or eSIM activation details."
        )
    if command.lstrip("/") in COMMANDS and command.startswith("/"):
        return COMMANDS[command[1:]]
    return CONTENT.get(text, "Choose eSIM Basics, Compatibility Guide or Setup & Help below. Use /help to see the menu.")

def configure(api):
    api.call("setMyName", name=NAME)
    api.call("setMyShortDescription", short_description=ABOUT)
    api.call("setMyDescription", description=DESCRIPTION)
    api.call("setMyCommands", commands=[
        {"command": "start", "description": "Open the educational menu"},
        {"command": "basics", "description": "Learn about eSIMs"},
        {"command": "compatibility", "description": "Read the device self-check guide"},
        {"command": "setup", "description": "Read setup and troubleshooting tips"},
        {"command": "help", "description": "Show the menu"},
        {"command": "privacy", "description": "Read privacy information"},
    ])
    api.call("deleteWebhook", drop_pending_updates=False)

def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    token = os.environ.get("BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("Set BOT_TOKEN in the hosting environment before starting.")
    api = TelegramAPI(token)
    running = True

    def stop(signum, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    while running:
        try:
            configure(api)
            break
        except TelegramError as error:
            if error.code in (401, 404, 409):
                raise SystemExit("Check BOT_TOKEN and ensure only one bot instance is running.") from None
            logging.warning("Profile setup failed (%s); retrying.", error.code)
            time.sleep(min(max(error.retry_after, 1), 60))
        except (URLError, TimeoutError, OSError, ValueError):
            logging.warning("Network failure during setup; retrying.")
            time.sleep(5)

    offset = None
    while running:
        try:
            updates = api.call("getUpdates", offset=offset, timeout=30, allowed_updates=["message"])
            for update in updates:
                if not running:
                    break
                message = update.get("message", {})
                chat = message.get("chat", {})
                if chat.get("type") == "private":
                    try:
                        api.call("sendMessage", chat_id=chat["id"],
                                 text=reply_for(message.get("text")),
                                 reply_markup=KEYBOARD)
                    except TelegramError as error:
                        if error.code not in (400, 403):
                            raise
                        logging.info("Skipped unavailable private chat.")
                offset = update["update_id"] + 1
        except TelegramError as error:
            if error.code in (401, 404, 409):
                raise SystemExit("Check BOT_TOKEN and ensure only one polling instance is running.") from None
            logging.warning("Telegram request failed (%s); retrying.", error.code)
            time.sleep(min(max(error.retry_after, 1), 60))
        except (URLError, TimeoutError, OSError, ValueError):
            logging.warning("Network request failed; retrying.")
            time.sleep(5)

if __name__ == "__main__":
    main()
