from pathlib import Path
import subprocess
import tempfile
import unittest


class SkillSyncTest(unittest.TestCase):
    def test_repeated_sync_updates_user_skills_and_preserves_system_and_local_skills(
        self,
    ):
        script = Path(__file__).with_name("sync-github-settings.sh").read_text()
        apply_function = script.split("apply_codex_settings() {", 1)[1].split(
            "\nsync_codex_settings() {", 1
        )[0]
        command = (
            'settings_checkout="$1"\ncodex_home="$2"\n'
            + "apply_codex_settings() {"
            + apply_function
            + "\napply_codex_settings\n"
        )
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            target = Path(temporary) / "target"
            fixtures = {
                source / "AGENTS.md": "shared instructions",
                source / "SETUP.md": "setup",
                source / "hooks.json": "{}",
                source / "shared.config.toml": "",
                source / "rules/default.rules": "rules",
                source / "scripts/bootstrap-unix.sh": "#!/bin/sh\nexit 0\n",
                source / "scripts/doctor.py": "",
                source / "scripts/sync-github-settings.sh": "sync script",
                source / "skills/shared/SKILL.md": "updated user skill",
                source / "skills/.system/builtin/SKILL.md": "stale system skill",
                source / "skills/.system/source-only/SKILL.md": "obsolete skill",
                target / "skills/shared/SKILL.md": "old user skill",
                target / "skills/.system/builtin/SKILL.md": "current system skill",
                target / "skills/local/SKILL.md": "unrelated local skill",
            }
            for path, content in fixtures.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            (source / "scripts/bootstrap-unix.sh").chmod(0o755)
            for _ in range(2):
                subprocess.run(
                    ["bash", "-euc", command, "test-sync", str(source), str(target)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(
                    (target / "skills/shared/SKILL.md").read_text(),
                    "updated user skill",
                )
                self.assertEqual(
                    (target / "skills/.system/builtin/SKILL.md").read_text(),
                    "current system skill",
                )
                self.assertFalse((target / "skills/.system/source-only").exists())
                self.assertEqual(
                    (target / "skills/local/SKILL.md").read_text(),
                    "unrelated local skill",
                )


if __name__ == "__main__":
    unittest.main()
