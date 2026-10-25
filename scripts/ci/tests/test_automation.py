import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), SCRIPTS / (name + ".py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


automation = module("automation")
overlay = module("apply-overlay")
secrets = module("prepare-build-secrets")


def release(tag, date="2026-10-24T12:03:22Z", **kwargs):
    return dict(tag_name=tag, published_at=date, draft=False, prerelease=False, assets=[], **kwargs)


class ReleasePlanningTest(unittest.TestCase):
    baseline = dict(tag="3.1.1", published_at="2026-10-24T12:03:22Z")

    def test_initial_bootstrap_excludes_old_releases(self):
        old = release("2.1.12", "2026-05-01T00:00:00Z")
        selected = automation.select_releases([old, release("3.1.1")], [], self.baseline)
        self.assertEqual([r[0]["tag_name"] for r in selected], ["3.1.1"])

    def test_multiple_releases_are_processed_oldest_first(self):
        newest = release("3.1.3", "2026-10-26T00:00:00Z")
        middle = release("3.1.2", "2026-10-25T00:00:00Z")
        self.assertEqual([r[0]["tag_name"] for r in automation.select_releases(
            [newest, release("3.1.1"), middle], [], self.baseline)], ["3.1.1", "3.1.2", "3.1.3"])

    def test_drafts_and_prereleases_are_not_upstream_targets(self):
        draft = release("3.1.2")
        draft["draft"] = True
        preview = release("3.2.0-beta")
        preview["prerelease"] = True
        self.assertEqual(automation.select_releases([draft, preview], [], self.baseline), [])

    def test_existing_incomplete_release_is_reconciled(self):
        local = release("3.1.1")
        selected = automation.select_releases([release("3.1.1")], [local], self.baseline)
        self.assertIs(selected[0][1], local)
        self.assertIsNone(automation.release_manifest(None, local, "a" * 40))

    def run_plan(self, state):
        import base64
        api, upstream = unittest.mock.Mock(), unittest.mock.Mock()
        api.sha.return_value = "b" * 40
        upstream.sha.return_value = "a" * 40
        api.request.return_value = dict(content=base64.b64encode(json.dumps(state).encode()).decode())
        api.pages.return_value = []
        upstream.pages.return_value = []
        outputs = {}
        with patch.object(automation, "GitHub", side_effect=[api, upstream]), \
                patch.object(automation, "overlay_hash", return_value="overlay"), \
                patch.object(automation, "output", side_effect=lambda k, v: outputs.update({k: v})):
            automation.plan(None)
        return outputs

    def test_unchanged_snapshot_skips_build(self):
        state = dict(upstream_sha="a" * 40, overlay_sha256="overlay",
                     checked_at=automation.dt.datetime.now(automation.dt.timezone.utc).isoformat())
        self.assertEqual(self.run_plan(state)["sync"], "false")

    def test_pure_upstream_commit_triggers_build_without_overlay_edits(self):
        state = dict(upstream_sha="c" * 40, overlay_sha256="overlay",
                     checked_at=automation.dt.datetime.now(automation.dt.timezone.utc).isoformat())
        self.assertEqual(self.run_plan(state)["sync"], "true")

    def test_45_day_maintenance_prevents_inactivity(self):
        old = automation.dt.datetime.now(automation.dt.timezone.utc) - automation.dt.timedelta(days=45)
        state = dict(upstream_sha="a" * 40, overlay_sha256="overlay", checked_at=old.isoformat())
        self.assertEqual(self.run_plan(state)["sync"], "true")


class ManifestTest(unittest.TestCase):
    def setUp(self):
        self.manifest = dict(tag="3.1.1", upstream_sha="a" * 40, apk="test.apk", apk_size=10,
                             apk_sha256="b" * 64, certificate_sha256="c" * 64)
        self.release = release("3.1.1")
        self.release["assets"] = [dict(name="build-info.json"), dict(name="SHA256SUMS"),
                                   dict(name="test.apk", size=10, digest="sha256:" + "b" * 64)]

    def data(self, api, asset):
        if asset["name"] == "build-info.json":
            return json.dumps(self.manifest).encode()
        return ("b" * 64 + "  test.apk\n").encode()

    def test_complete_release_is_verified(self):
        with patch.object(automation, "asset_bytes", side_effect=self.data):
            self.assertEqual(automation.release_manifest(None, self.release, "a" * 40), self.manifest)

    def test_upload_interruption_does_not_mark_complete(self):
        self.release["assets"] = self.release["assets"][1:]
        self.assertIsNone(automation.release_manifest(None, self.release, "a" * 40))

    def test_wrong_source_never_skips_a_release(self):
        with patch.object(automation, "asset_bytes", side_effect=self.data):
            with self.assertRaisesRegex(RuntimeError, "provenance"):
                automation.release_manifest(None, self.release, "d" * 40)

    def test_corrupt_digest_is_rejected(self):
        self.release["assets"][-1]["digest"] = "sha256:" + "d" * 64
        with patch.object(automation, "asset_bytes", side_effect=self.data):
            with self.assertRaisesRegex(RuntimeError, "digest"):
                automation.release_manifest(None, self.release, "a" * 40)

    def test_missing_apk_is_not_complete(self):
        self.release["assets"].pop()
        with patch.object(automation, "asset_bytes", side_effect=self.data):
            self.assertIsNone(automation.release_manifest(None, self.release, "a" * 40))


class GitSafetyTest(unittest.TestCase):
    def test_master_race_prevents_push(self):
        args = type("Args", (), dict(target="/tmp/candidate", base_sha="a" * 40))()
        with patch.object(automation, "git", side_effect=["b" * 40, "", "c" * 40 + "\trefs/heads/master"]) as git:
            with self.assertRaisesRegex(RuntimeError, "master changed"):
                automation.advance(args)
        self.assertFalse(any(call.args[0] == "push" for call in git.call_args_list))

    def test_update_is_normal_fast_forward_push(self):
        args = type("Args", (), dict(target="/tmp/candidate", base_sha="a" * 40))()
        with patch.object(automation, "git", side_effect=["b" * 40, "", "a" * 40 + "\trefs/heads/master", ""]) as git:
            automation.advance(args)
        self.assertEqual(git.call_args.args, ("push", "origin", "b" * 40 + ":refs/heads/master"))


class OverlayTest(unittest.TestCase):
    def test_replacements_are_idempotent_and_fail_on_upstream_change(self):
        with tempfile.TemporaryDirectory() as temporary:
            file = Path(temporary) / "source"
            file.write_text("old")
            overlay.replace_once(file, "old", "new")
            overlay.replace_once(file, "old", "new")
            self.assertEqual(file.read_text(), "new")
            file.write_text("different")
            with self.assertRaisesRegex(RuntimeError, "Upstream structure changed"):
                overlay.replace_once(file, "old", "new")

    def test_preserves_controller_when_upstream_deletes_workflow(self):
        with tempfile.TemporaryDirectory() as temporary:
            src, dst = Path(temporary) / "control", Path(temporary) / "upstream"
            (src / ".github/workflows").mkdir(parents=True)
            (src / ".github/workflows/release.yml").write_text("fork workflow")
            (dst / ".github/workflows").mkdir(parents=True)
            (dst / ".github/workflows/daily-build.yml").write_text("upstream workflow")
            automation.copy_owned(src, dst)
            self.assertEqual((dst / ".github/workflows/release.yml").read_text(), "fork workflow")
            self.assertFalse((dst / ".github/workflows/daily-build.yml").exists())

    def test_overlay_hash_is_stable_and_tracks_adapter_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "fork").mkdir()
            (root / "fork/config.json").write_text("first")
            first = automation.overlay_hash(root)
            self.assertEqual(first, automation.overlay_hash(root))
            (root / "fork/config.json").write_text("second")
            self.assertNotEqual(first, automation.overlay_hash(root))


class DeviceGateTest(unittest.TestCase):
    def test_unapproved_device_keeps_verified_release_draft(self):
        cfg = automation.config()
        cfg["device_validation"]["approved"] = False
        api = unittest.mock.Mock()
        api.release.return_value = dict(draft=True)
        args = type("Args", (), dict(tag="3.1.1", upstream_sha="a" * 40))()
        with patch.object(automation, "config", return_value=cfg), patch.object(automation, "GitHub", return_value=api), \
                patch.object(automation, "release_manifest", return_value=dict(apk_sha256="b" * 64)), \
                patch.object(automation, "output"), contextlib.redirect_stdout(io.StringIO()):
            automation.publish(args)
        api.request.assert_not_called()

    def test_missing_approval_checksum_blocks_publication(self):
        cfg = automation.config()
        cfg["device_validation"] = dict(approved=True, baseline_apk_sha256="")
        api = unittest.mock.Mock()
        api.release.return_value = dict(draft=True)
        args = type("Args", (), dict(tag="3.1.1", upstream_sha="a" * 40))()
        with patch.object(automation, "config", return_value=cfg), patch.object(automation, "GitHub", return_value=api), \
                patch.object(automation, "release_manifest", return_value=dict(apk_sha256="b" * 64)):
            with self.assertRaisesRegex(RuntimeError, "SHA-256"):
                automation.publish(args)
        api.request.assert_not_called()


class SecretTest(unittest.TestCase):
    def test_missing_secret_fails_without_writing_files(self):
        with tempfile.TemporaryDirectory() as temporary, patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "Missing required secrets"):
                secrets.prepare(Path(temporary))
            self.assertEqual(list(Path(temporary).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
