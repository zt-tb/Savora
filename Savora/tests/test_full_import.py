import importlib
import unittest

from tests import _stubs  # noqa: F401

MODULES = [
    "app.config", "app.db", "app.models", "app.emoji_ids", "app.buttons", "app.texts",
    "app.users", "app.downloader", "app.session_vault", "app.login_flow", "app.telethon_runtime",
    "app.handlers.common", "app.handlers.start", "app.handlers.admin_panel",
    "app.handlers.session_login", "app.handlers.download", "app.handlers.router", "main",
    "app.ui", "app.settings_store", "app.links", "app.mediaprep", "app.sender",
    "app.progress", "app.download_queue", "app.monitor", "app.handlers.payments",
    "app.antispam", "app.plans", "app.welcome_media",
]


class TestFullImport(unittest.TestCase):
    def test_every_module_imports_cleanly(self):
        for name in MODULES:
            with self.subTest(module=name):
                importlib.import_module(name)

    def test_build_application_wires_without_crashing(self):
        main = importlib.import_module("main")
        app = main.build_application()
        self.assertEqual(len(app.handlers), 10)
        self.assertEqual(app.groups[0], -1)
        self.assertEqual(len(app.error_handlers), 1)
        self.assertIsNotNone(app.defaults)
        self.assertIsNotNone(app.rate_limiter)
        self.assertEqual([j[3] for j in app.job_queue.jobs], [])


if __name__ == "__main__":
    unittest.main()
