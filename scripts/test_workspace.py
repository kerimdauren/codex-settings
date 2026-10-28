import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import workspace


class WorkspaceTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "workspace"
        self.root.mkdir()

    def git(self, *arguments):
        return subprocess.run(["git", "-C", str(self.root), *arguments], check=True,
                              capture_output=True, text=True).stdout

    def test_traversal_and_credential_urls_are_rejected(self):
        for relative in ("../outside", "/absolute", "demo/../../outside", "C:/Users", "demo/*"):
            with self.subTest(relative=relative), self.assertRaises(ValueError):
                workspace.location(self.root, relative)
        for url in ("https://token@example.com/repo", "ssh://user:password@example.com/repo", "--upload-pack=anything"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                workspace.validate_git_url(url)

    def test_secret_files_are_private_ignored_and_local_changes_are_preserved(self):
        self.git("init")
        target = self.root / ".env"
        workspace.write_env(target, "TEST_ONLY=value\n")
        self.assertEqual(target.read_text(), "TEST_ONLY=value\n")
        self.assertEqual(self.git("check-ignore", ".env").strip(), ".env")
        if os.name != "nt":
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
        with self.assertRaisesRegex(RuntimeError, "Kept differing"):
            workspace.write_env(target, "TEST_ONLY=changed\n")
        self.assertEqual(target.read_text(), "TEST_ONLY=value\n")
        workspace.write_env(target, "TEST_ONLY=changed\n", refresh=True)
        self.assertEqual(target.read_text(), "TEST_ONLY=changed\n")

    def test_tracked_env_is_never_overwritten(self):
        self.git("init")
        target = self.root / ".env"
        target.write_text("EXISTING=test-only\n")
        self.git("add", ".env")
        with self.assertRaisesRegex(RuntimeError, "tracked by Git"):
            workspace.write_env(target, "NEW=test-only\n", refresh=True)
        self.assertEqual(target.read_text(), "EXISTING=test-only\n")

    def test_dirty_repo_does_not_pull_or_change_branch(self):
        self.git("init")
        self.git("remote", "add", "origin", "git@example.com:owner/repo.git")
        (self.root / "local.txt").write_text("local work")
        workspace.sync_repo(self.root, "https://example.com/owner/repo.git")
        self.assertEqual((self.root / "local.txt").read_text(), "local work")

    def test_root_code_restores_without_git_overwriting_drive_material(self):
        self.git("init")
        (self.root / "context").mkdir()
        (self.root / "context/spec.md").write_text("old Git snapshot")
        (self.root / "app.py").write_text("first code")
        self.git("add", ".")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "fixture")
        restored = self.root.parent / "new-device"
        restored.mkdir()  # bootstrap.py creates the workspace before clone.
        with patch.object(workspace, "validate_git_url"):
            workspace.sync_repo(restored, str(self.root), materials=["context"])
            self.assertFalse((restored / "context/spec.md").exists())
            self.assertEqual((restored / "app.py").read_text(), "first code")
            (restored / "context").mkdir()
            (restored / "context/spec.md").write_text("current Drive document")
            (self.root / "app.py").write_text("updated code")
            self.git("add", "app.py")
            self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "updated fixture")
            workspace.sync_repo(restored, str(self.root), materials=["context"])
        self.assertEqual((restored / "app.py").read_text(), "updated code")
        self.assertEqual((restored / "context/spec.md").read_text(), "current Drive document")

    def test_secret_provider_errors_do_not_reveal_output(self):
        failure = subprocess.CompletedProcess(["bw", "get"], 1, "TEST_SECRET", "TEST_SECRET")
        with patch.object(workspace.subprocess, "run", return_value=failure):
            with self.assertRaises(RuntimeError) as caught:
                workspace.run(["bw", "get", "item", "test-item"])
        self.assertNotIn("TEST_SECRET", str(caught.exception))

    def test_global_customization_survives_and_conflicts_are_not_overwritten(self):
        source = self.root / "source"
        installed = self.root / "installed"
        source.mkdir()
        (source / "AGENTS.md").write_text("common\n")
        workspace.copy_asset(source, Path("AGENTS.md"), installed)
        (installed / "AGENTS.md").write_text("local customization\n")
        workspace.copy_asset(source, Path("AGENTS.md"), installed)
        self.assertEqual((installed / "AGENTS.md").read_text(), "local customization\n")
        (source / "AGENTS.md").write_text("conflicting source change\n")
        with self.assertRaisesRegex(RuntimeError, "conflicting global"):
            workspace.copy_asset(source, Path("AGENTS.md"), installed)
        self.assertEqual((installed / "AGENTS.md").read_text(), "local customization\n")

    def test_router_preserves_existing_repo_instructions(self):
        self.git("init")
        project = self.root / "demo"
        checkout = project / "code/app"
        checkout.mkdir(parents=True)
        subprocess.run(["git", "init", str(checkout)], check=True, capture_output=True)
        (project / "AGENTS.md").write_text("Shared guidance")
        repo = {"path": "demo/code/app", "project": "demo"}
        workspace.attach_project(self.root, repo)
        self.assertIn("../../AGENTS.md", (checkout / "AGENTS.md").read_text())
        (checkout / "AGENTS.md").write_text("Existing repo guidance")
        workspace.attach_project(self.root, repo)
        self.assertEqual((checkout / "AGENTS.md").read_text(), "Existing repo guidance")

    def test_env_is_restored_from_only_selected_note(self):
        config = {"envs": [{"path": "demo/.env", "item": "selected-note"}]}
        real_run = workspace.run
        def fake_run(command, **kwargs):
            if command[0] != "bw":
                return real_run(command, **kwargs)
            self.assertEqual(command, ["bw", "list", "items", "--search", "selected-note", "--nointeraction"])
            self.assertEqual(kwargs["env"]["BW_SESSION"], "TEST_SESSION")
            return subprocess.CompletedProcess(command, 0, json.dumps([{"type": 2, "name": "selected-note", "notes": "TEST_ONLY=restored\n"}]), "")
        with patch.object(workspace, "vault_session", return_value=contextlib.nullcontext({"BW_SESSION": "TEST_SESSION"})), patch.object(workspace, "run", side_effect=fake_run), contextlib.redirect_stdout(io.StringIO()) as output:
            workspace.sync_envs(self.root, config)
        self.assertEqual((self.root / "demo/.env").read_text(), "TEST_ONLY=restored\n")
        self.assertNotIn("TEST_ONLY", output.getvalue())
        self.assertNotIn("TEST_SESSION", output.getvalue())


@unittest.skipUnless(shutil.which("rclone"), "rclone is required for local integration tests")
class DriveSyncTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        base = Path(self.temporary.name)
        self.local, self.remote, self.state = base / "local", base / "remote", base / "state"
        self.local.mkdir()
        self.remote.mkdir()
        (self.local / "context").mkdir()
        self.config = {"drive": {"remote": str(self.remote)}, "materials": ["context", "AGENTS.md"]}

    def test_two_way_sync_excludes_secrets_code_and_git(self):
        (self.local / "context/spec.md").write_text("original")
        (self.local / "context/.env").write_text("TEST_SECRET=value")
        (self.local / "context/credentials.json").write_text("TEST_SECRET=value")
        (self.local / "context/.codex-env-test").mkdir()
        (self.local / "context/.codex-env-test/env").write_text("TEST_SECRET=value")
        (self.local / "code.py").write_text("code")
        (self.local / "AGENTS.md").write_text("instructions")
        workspace.sync_materials(self.local, self.config, self.state, initial=True)
        self.assertEqual((self.remote / "context/spec.md").read_text(), "original")
        self.assertFalse((self.remote / "context/.env").exists())
        self.assertFalse((self.remote / "context/credentials.json").exists())
        self.assertFalse((self.remote / "context/.codex-env-test").exists())
        self.assertFalse((self.remote / "code.py").exists())
        (self.remote / "context/spec.md").write_text("changed remotely")
        (self.local / "context/new.md").write_text("new locally")
        workspace.sync_materials(self.local, self.config, self.state)
        self.assertEqual((self.local / "context/spec.md").read_text(), "changed remotely")
        self.assertEqual((self.remote / "context/new.md").read_text(), "new locally")
        backups = list((self.state / "drive-backups").rglob("spec.md"))
        self.assertTrue(any(path.read_text() == "original" for path in backups))

    def test_initial_conflict_changes_neither_side(self):
        (self.local / "context/spec.md").write_text("local content")
        (self.remote / "context").mkdir()
        (self.remote / "context/spec.md").write_text("remote content")
        with self.assertRaisesRegex(RuntimeError, "differing files"):
            workspace.sync_materials(self.local, self.config, self.state, initial=True)
        self.assertEqual((self.local / "context/spec.md").read_text(), "local content")
        self.assertEqual((self.remote / "context/spec.md").read_text(), "remote content")

    def test_concurrent_edits_preserve_both_versions(self):
        (self.local / "AGENTS.md").write_text("original")
        (self.local / "context/stable.md").write_text("unchanged")
        workspace.sync_materials(self.local, self.config, self.state, initial=True)
        (self.local / "AGENTS.md").write_text("local version")
        (self.remote / "AGENTS.md").write_text("remote version")
        with self.assertRaisesRegex(RuntimeError, "conflicts preserved"):
            workspace.sync_materials(self.local, self.config, self.state)
        versions = {p.read_text() for p in self.local.glob("AGENTS.md.conflict*")}
        self.assertEqual(versions, {"local version", "remote version"})


if __name__ == "__main__":
    unittest.main()
