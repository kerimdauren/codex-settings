import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "doctor", Path(__file__).resolve().parent / "doctor.py"
)
doctor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(doctor)


class SetupReadinessTest(unittest.TestCase):
    def test_setup_does_not_require_removed_code_review_graph(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            codex_home = root / "codex"
            codex_home.mkdir()
            ai_root = root / "ai"
            shared = 'model = "gpt-6.1-sol"\nmodel_provider = "openai"\n'
            (codex_home / "shared.config.toml").write_text(shared)
            (codex_home / "config.toml").write_text(
                shared
                + f'\n[projects.{json.dumps(str(ai_root))}]\ntrust_level = "trusted"\n'
            )
            with (
                patch.dict(
                    os.environ,
                    {"CODEX_HOME": str(codex_home), "CODEX_AI_ROOT": str(ai_root)},
                ),
                patch.object(doctor, "command_path", return_value="/installed/tool"),
                patch.object(doctor, "command_succeeds", return_value=True),
            ):
                report = doctor.inspect_environment()

        self.assertTrue(report["ready"], report["planned_actions"])


if __name__ == "__main__":
    unittest.main()
