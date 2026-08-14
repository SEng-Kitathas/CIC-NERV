from __future__ import annotations

import json
import os
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from personal_cic.core.config import RuntimeConfig
from personal_cic.runtime import default_runtime_config_path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "config" / "runtime.example.json"


class ConfigurationAuthorityTests(TestCase):
    def test_default_runtime_config_is_xdg_deployment_state(self):
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": "/tmp/cic-config-authority"}, clear=False):
            self.assertEqual(
                default_runtime_config_path(),
                Path("/tmp/cic-config-authority/personal-cic/runtime.json"),
            )

    def test_default_runtime_config_falls_back_to_user_config_home(self):
        env = dict(os.environ)
        env.pop("XDG_CONFIG_HOME", None)
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(
                default_runtime_config_path(),
                Path.home() / ".config" / "personal-cic" / "runtime.json",
            )

    def test_authored_runtime_example_is_neutral_and_loadable(self):
        payload = json.loads(EXAMPLE.read_text())
        awareness = payload["world_awareness"]
        self.assertFalse(awareness["enabled"])
        self.assertEqual(awareness["location"]["label"], "CONFIGURE_ME")
        self.assertEqual(awareness["location"]["latitude"], 0.0)
        self.assertEqual(awareness["location"]["longitude"], 0.0)
        self.assertFalse(awareness["traffic"]["enabled"])
        self.assertEqual(awareness["traffic"]["scope_counties"], ["CONFIGURE_ME"])
        self.assertEqual(payload["operator_context"]["site_anchor"], {"enabled": False})
        RuntimeConfig.load(EXAMPLE)

    def test_live_runtime_config_path_is_gitignored(self):
        self.assertIn("config/runtime.json", (ROOT / ".gitignore").read_text().splitlines())
