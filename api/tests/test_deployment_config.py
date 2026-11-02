import importlib
import tomllib
import unittest
from pathlib import Path

import api.app as api_app

ROOT = Path(__file__).resolve().parents[2]


class DeploymentConfigTest(unittest.TestCase):
    def test_fastapi_entrypoint_resolves_to_the_app(self):
        with (ROOT / "pyproject.toml").open("rb") as file:
            entrypoint = tomllib.load(file)["tool"]["fastapi"]["entrypoint"]

        module_name, _, attribute = entrypoint.partition(":")
        module = importlib.import_module(module_name)
        self.assertIs(getattr(module, attribute or "app"), api_app.app)

    def test_cloud_bundle_keeps_runtime_files(self):
        ignored = (ROOT / ".fastapicloudignore").read_text().splitlines()
        self.assertTrue((api_app.FRONTEND_DIRECTORY / "index.html").is_file())
        for path in ("frontend/", "checkbox_detection/", "api/"):
            self.assertNotIn(path, ignored)
        self.assertIn("checkbox_detection/data/", ignored)
        self.assertIn("**/tests/", ignored)
