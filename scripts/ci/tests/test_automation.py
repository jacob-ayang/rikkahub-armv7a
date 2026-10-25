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
apk_checks = module("verify-apk")


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
        import hashlib
        info_hash = hashlib.sha256(json.dumps(self.manifest).encode()).hexdigest()
        return ("b" * 64 + "  test.apk\n" + info_hash + "  build-info.json\n").encode()

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

    def test_ambiguous_apks_are_not_a_complete_release(self):
        self.release["assets"].append(dict(name="old.apk", size=20))
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
    def test_rootfs_version_follows_upstream_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            file = Path(temporary) / "page.kt"
            for version in ("24.04.3", "24.04.5"):
                url = f"https://cdimage.ubuntu.com/ubuntu-base/releases/24.04/release/ubuntu-base-{version}-base-arm64.tar.gz"
                file.write_text(f'val url = "{url}"')
                overlay.adapt_rootfs_url(file)
                overlay.adapt_rootfs_url(file)
                self.assertIn(version + "-base-armhf.tar.gz", file.read_text())

    def test_changed_rootfs_source_requires_review(self):
        with tempfile.TemporaryDirectory() as temporary:
            file = Path(temporary) / "page.kt"
            file.write_text('val url = "https://example.org/unknown-rootfs.tar.gz"')
            with self.assertRaisesRegex(RuntimeError, "rootfs URL structure changed"):
                overlay.adapt_rootfs_url(file)

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

    def test_inserting_after_an_existing_anchor_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            file = Path(temporary) / "fixture"
            file.write_text("anchor")
            overlay.replace_once(file, "anchor", "anchor\naddition")
            overlay.replace_once(file, "anchor", "anchor\naddition")
            self.assertEqual(file.read_text(), "anchor\naddition")

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
            (root / "fork/config.json").write_text('{"schema": 1}')
            first = automation.overlay_hash(root)
            self.assertEqual(first, automation.overlay_hash(root))
            (root / "fork/config.json").write_text('{"schema": 2}')
            self.assertNotEqual(first, automation.overlay_hash(root))

    def test_approving_tested_apk_does_not_change_build_fingerprint(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "fork").mkdir()
            path = root / "fork/config.json"
            path.write_text('{"schema":1,"device_validation":{"approved":false}}')
            first = automation.overlay_hash(root)
            path.write_text('{"schema":1,"device_validation":{"approved":true,"baseline_apk_sha256":"abc"}}')
            self.assertEqual(first, automation.overlay_hash(root))

    def test_changed_adapter_rebuilds_draft_but_not_published_release(self):
        args = type("Args", (), dict(tag="3.1.1", upstream_sha="a" * 40))()
        api = unittest.mock.Mock()
        with patch.object(automation, "GitHub", return_value=api), \
                patch.object(automation, "release_manifest", return_value=dict(build_overlay_sha256="old")), \
                patch.object(automation, "build_hash", return_value="new"), \
                patch.object(automation, "output") as output:
            api.release.return_value = dict(draft=True)
            automation.status(args)
            output.assert_called_with("ready", "false")
            api.release.return_value = dict(draft=False)
            automation.status(args)
            output.assert_called_with("ready", "true")

    def test_controller_changes_do_not_rebuild_tested_apk(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".github/workflows").mkdir(parents=True)
            workflow = root / ".github/workflows/release.yml"
            workflow.write_text("bootstrap")
            before = automation.build_hash(root)
            workflow.write_text("production")
            self.assertEqual(before, automation.build_hash(root))
            (root / "fork").mkdir()
            (root / "fork/armv7.gradle").write_text("changed native configuration")
            self.assertNotEqual(before, automation.build_hash(root))


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

    def test_replaced_baseline_apk_cannot_be_published_as_device_approved(self):
        cfg = automation.config()
        cfg["device_validation"] = dict(approved=True, baseline_apk_sha256="b" * 64)
        api = unittest.mock.Mock()
        api.release.return_value = dict(draft=True)
        args = type("Args", (), dict(tag="3.1.1", upstream_sha="a" * 40))()
        with patch.object(automation, "config", return_value=cfg), patch.object(automation, "GitHub", return_value=api), \
                patch.object(automation, "release_manifest", side_effect=[dict(apk_sha256="b" * 64), dict(apk_sha256="c" * 64)]):
            with self.assertRaisesRegex(RuntimeError, "tested baseline APK"):
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
    def test_local_sdk_paths_are_not_carried_into_ci(self):
        import base64
        services = dict(client=[dict(client_info=dict(android_client_info=dict(package_name="me.rerere.rikkahub")))])
        signing = "storeFile=/old/key\nsdk.dir=/old/sdk\nndk.dir=/old/ndk\nstorePassword=p\nkeyAlias=k\nkeyPassword=p\n"
        env = {"KEY_BASE64": base64.b64encode(b"key").decode(),
               "SIGNING_CONFIG_B64": base64.b64encode(signing.encode()).decode(),
               "GOOGLE_SERVICES_JSON_B64": base64.b64encode(json.dumps(services).encode()).decode()}
        with tempfile.TemporaryDirectory() as temporary, patch.dict("os.environ", env):
            root = Path(temporary)
            (root / "app").mkdir()
            secrets.prepare(root)
            properties = (root / "local.properties").read_text()
            self.assertNotIn("/old/", properties)
            self.assertIn("storeFile=rikkahub.keystore", properties)
            self.assertEqual((root / "rikkahub.keystore").read_bytes(), b"key")

    def test_missing_secret_fails_without_writing_files(self):
        with tempfile.TemporaryDirectory() as temporary, patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "Missing required secrets"):
                secrets.prepare(Path(temporary))
            self.assertEqual(list(Path(temporary).iterdir()), [])


class CertificateTest(unittest.TestCase):
    def test_old_and_new_apksigner_formats(self):
        for output in (
            "Number of signers: 1\nSigner #1 certificate SHA-256 digest: " + "a" * 64,
            "Number of signers: 1\nV2 Signer: certificate SHA-256 digest: " + "a" * 64 +
            "\nV3.1 Signer: certificate SHA-256 digest: " + "a" * 64,
        ):
            with patch.object(apk_checks, "run", return_value=output):
                self.assertEqual(apk_checks.certificate("apksigner", "app.apk"), "a" * 64)

    def test_multiple_signers_are_rejected(self):
        output = "Number of signers: 2\nSigner #1 certificate SHA-256 digest: " + "a" * 64
        with patch.object(apk_checks, "run", return_value=output):
            with self.assertRaisesRegex(RuntimeError, "exactly one"):
                apk_checks.certificate("apksigner", "app.apk")


class UploadRetryTest(unittest.TestCase):
    def test_rebuilt_draft_removes_obsolete_apk_before_uploading_completion_marker(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = dict(tag="3.1.1", upstream_sha="a" * 40, source_sha="b" * 40, apk="new.apk")
            for name, data in (("build-info.json", json.dumps(manifest)), ("SHA256SUMS", "checksums"), ("new.apk", "apk")):
                (root / name).write_text(data)
            draft = dict(id=1, draft=True, upload_url="https://uploads.github.com/test{?name}",
                         assets=[dict(id=7, name="old.apk")])
            args = type("Args", (), dict(directory=temporary, tag="3.1.1", upstream_sha="a" * 40))()
            api = unittest.mock.Mock()
            api.release.return_value = draft
            api.request.return_value = None
            with patch.object(automation, "GitHub", return_value=api), \
                    patch.object(automation, "release_manifest", return_value=manifest):
                automation.upload(args)
            calls = api.request.call_args_list
            delete_index = next(i for i, call in enumerate(calls) if call.args == ("releases/assets/7", "DELETE"))
            uploads = [(i, call.args[0]) for i, call in enumerate(calls) if call.args[1:2] == ("POST",)]
            self.assertLess(delete_index, uploads[0][0])
            self.assertTrue(uploads[-1][1].endswith("name=build-info.json"))

    def test_upload_failure_leaves_no_completion_marker_and_retry_preserves_apk(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = dict(tag="3.1.1", upstream_sha="a" * 40, source_sha="b" * 40, apk="test.apk")
            (root / "build-info.json").write_text(json.dumps(manifest))
            (root / "SHA256SUMS").write_text("checksums")
            (root / "test.apk").write_bytes(b"apk")
            draft = dict(id=1, draft=True, upload_url="https://uploads.github.com/test{?name}",
                         assets=[dict(id=2, name="test.apk")])
            args = type("Args", (), dict(directory=temporary, tag="3.1.1", upstream_sha="a" * 40))()
            api = unittest.mock.Mock()
            api.release.return_value = draft
            uploads = []

            def request(path, method="GET", data=None, **kwargs):
                if method == "POST":
                    uploads.append(path)
                    if "SHA256SUMS" in path:
                        raise RuntimeError("network interrupted")
                return None

            api.request.side_effect = request
            with patch.object(automation, "GitHub", return_value=api), \
                    patch.object(automation, "asset_bytes", return_value=b"apk"):
                with self.assertRaisesRegex(RuntimeError, "network interrupted"):
                    automation.upload(args)
            self.assertEqual(len(uploads), 1)
            self.assertNotIn("build-info.json", uploads[0])
            self.assertNotIn("test.apk", uploads[0])
            self.assertFalse(any(call.args[1:2] == ("DELETE",) for call in api.request.call_args_list))

    def test_published_apk_is_never_replaced_on_retry(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = dict(tag="3.1.1", upstream_sha="a" * 40, source_sha="b" * 40, apk="test.apk")
            (root / "build-info.json").write_text(json.dumps(manifest))
            (root / "test.apk").write_bytes(b"new apk")
            api = unittest.mock.Mock()
            api.release.return_value = dict(draft=False, assets=[dict(id=2, name="test.apk")])
            args = type("Args", (), dict(directory=temporary, tag="3.1.1", upstream_sha="a" * 40))()
            with patch.object(automation, "GitHub", return_value=api), \
                    patch.object(automation, "release_manifest", return_value=None), \
                    patch.object(automation, "asset_bytes", return_value=b"old apk"):
                with self.assertRaisesRegex(RuntimeError, "Refusing to replace published asset"):
                    automation.upload(args)
            api.request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
