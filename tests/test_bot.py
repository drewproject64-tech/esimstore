import unittest
from unittest.mock import Mock
import bot

class BotTests(unittest.TestCase):
    def test_menu_and_command_routes(self):
        self.assertEqual(len(bot.KEYBOARD["keyboard"]), 3)
        for label, expected in bot.CONTENT.items():
            self.assertEqual(bot.reply_for(label), expected)
        for command, expected in bot.COMMANDS.items():
            self.assertEqual(bot.reply_for("/" + command + "@ExampleBot"), expected)
        self.assertEqual(bot.reply_for("/start campaign"), bot.WELCOME)
        self.assertIn("Choose", bot.reply_for(None))
        self.assertIn("Privacy", bot.reply_for("/privacy"))

    def test_profile_is_applied_at_startup(self):
        api = Mock()
        bot.configure(api)
        api.call.assert_any_call("setMyName", name="eSIM Store")
        api.call.assert_any_call("setMyShortDescription", short_description=bot.ABOUT)
        api.call.assert_any_call("setMyDescription", description=bot.DESCRIPTION)
        self.assertLessEqual(len(bot.ABOUT), 120)
        self.assertLessEqual(len(bot.DESCRIPTION), 512)
        for text in [bot.ABOUT, bot.DESCRIPTION, bot.WELCOME, *bot.CONTENT.values()]:
            self.assertNotIn("https://", text)
            self.assertNotIn("http://", text)

if __name__ == "__main__":
    unittest.main()
