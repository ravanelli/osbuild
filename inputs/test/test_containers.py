#!/usr/bin/python3

import os
import pathlib
import random
import socket
import string
import subprocess
import tempfile

import pytest

from osbuild.testutil import has_executable, make_container

INPUTS_NAME = "org.osbuild.containers-storage"


class FakeStoreClient:
    def __init__(self, fake_sources_base):
        self.fake_sources_base = fake_sources_base
        self.fake_sources_base.mkdir()

    def source(self, name: str) -> str:
        fake_source_path = self.fake_sources_base / f"path-for-{name}"
        fake_source_path.mkdir(parents=True)
        return fake_source_path


def rmdir_only(path):
    """
    Remove all empty directories from the given target, errors for
    non-empty dirs
    """
    for root, dirs, _ in os.walk(path):
        for d in dirs:
            os.rmdir(pathlib.Path(root) / d)
    os.rmdir(path)


@pytest.mark.skipif(not has_executable("podman"), reason="no podman executable")
@pytest.mark.skipif(os.getuid() != 0, reason="root only")
def test_containers_local_inputs_integration(tmp_path, inputs_module):
    base_tag = "container-" + "".join(random.choices(string.digits, k=12))
    with make_container(tmp_path, base_tag, {"file1": "file1 content"}):
        image_id = subprocess.check_output(
            ["podman", "inspect", "-f", "{{ .Id }}", base_tag],
            universal_newlines=True).strip()
        inputs = {
            "type": INPUTS_NAME,
            "origin": "org.osbuild.source",
            "references": {
                f"sha256:{image_id}": {
                    "name": "localhost/some-name:latest",
                }
            }
        }
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        cnt_inputs = inputs_module.ContainersInput.from_args(["--service-fd", str(sock.fileno())])
        store = FakeStoreClient(tmp_path / "fake-sources")
        # not using "tmp_path" here as it will "rm -rf" on cleanup and
        # that is dangerous as during the tests we bind mount the
        # system container storage read-write
        target = pathlib.Path(tempfile.TemporaryDirectory("cnt-target").name)
        options = None
        try:
            reply = cnt_inputs.map(store, inputs["origin"], inputs["references"], target, options)
            assert reply["path"] == target
            assert len(reply["data"]["archives"]) == 1
            assert (target / "storage").exists()
        finally:
            cnt_inputs.unmap()
            rmdir_only(target)
