import os
import tempfile
import unittest

from dbpad import gameconfig

SAMPLE = "\r\n".join([
    "[Engine.PlayerInput]",
    'Bindings=(Name="LeftMouseButton",Command="Fire")',
    'Bindings=(Name="XboxTypeS_RightTrigger",Command="Fire")',
    "[ShooterGame.SGPlayerInputPawn]",
    'Bindings=(Name="XboxTypeS_LeftTrigger",Command="ToggleTargetingMode",Control=False)',
    'Bindings=(Name="R",Command="ReloadCmd")',
    "[GFxUI.KeyMap]",
    "XboxTypeS_LeftTrigger=GAMEPAD_L2",
    "",
])


class GameConfigTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "ShooterInput.ini")
        with open(self.path, "w", encoding="utf-8", newline="") as f:
            f.write(SAMPLE)

    def read(self):
        with open(self.path, encoding="utf-8", newline="") as f:
            return f.read()

    def test_off_comments_only_the_controller_bindings_and_keeps_a_backup(self):
        self.assertEqual(gameconfig.status(self.path), "on")
        self.assertEqual(gameconfig.disable(self.path), 2)
        text = self.read()
        self.assertIn(';dbpad-off Bindings=(Name="XboxTypeS_RightTrigger"', text)
        self.assertIn(';dbpad-off Bindings=(Name="XboxTypeS_LeftTrigger"', text)
        self.assertIn('\r\nBindings=(Name="LeftMouseButton",Command="Fire")\r\n', text)
        self.assertIn("\r\nXboxTypeS_LeftTrigger=GAMEPAD_L2\r\n", text)     # button-prompt names left alone
        self.assertEqual(gameconfig.status(self.path), "off")
        with open(self.path + gameconfig.BACKUP_SUFFIX, encoding="utf-8", newline="") as f:
            self.assertEqual(f.read(), SAMPLE)

    def test_on_puts_the_file_back_exactly(self):
        gameconfig.disable(self.path)
        self.assertEqual(gameconfig.enable(self.path), 2)
        self.assertEqual(self.read(), SAMPLE)
        self.assertEqual(gameconfig.status(self.path), "on")

    def test_switching_twice_changes_nothing_more(self):
        gameconfig.disable(self.path)
        self.assertEqual(gameconfig.disable(self.path), 0)

    def test_a_missing_file(self):
        self.assertEqual(gameconfig.status(os.path.join(self.dir, "nope.ini")), "missing")


if __name__ == "__main__":
    unittest.main()
