# eSIM Store

Educational Telegram bot with exactly three persistent menu buttons:
- eSIM Basics
- Compatibility Guide
- Setup & Help

All guides are delivered inside Telegram. No sales, payment flows, referral links, external websites, device scanning or plan listings.

## Run
Use Python 3.12 or newer. No third-party dependencies are required.
Set BOT_TOKEN securely in your hosting environment, then run:

```sh
python bot.py
```

Run one instance only, as this bot uses long polling. For a background worker, use `python bot.py` as the start command. This is not an HTTP web service and does not bind a port. Never commit your token.

## Profile
NAME, ABOUT and DESCRIPTION are defined in bot.py. Startup applies them with Telegram's setMyName, setMyShortDescription and setMyDescription methods, along with the command menu. Add a suitable profile picture through BotFather before promoting the bot.

Commands: /start, /basics, /compatibility, /setup, /help, /menu, /privacy.
Only private-chat messages are answered. No user database or persistent chat logs are created. The privacy command explains message processing.

The bot cannot detect device support or activate an eSIM. Guidance explains the limits of compatibility checks and provider-specific instructions.

Telegram Ads approval is determined by Telegram. Ads should describe the educational functions accurately; the name "Store" does not mean purchases are available.

## Verification
`python -m unittest discover -s tests -v`
