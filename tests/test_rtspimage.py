"""Unit tests for bin/user/rtspimage.py."""

import logging
import os
import subprocess

import pytest

from user.rtspimage import (
    VERSION,
    RTSPCapture,
    RTSPImageError,
    RTSPImageGenerator,
    _int_or_none,
    _mode_or_none,
)


# ---------------------------------------------------------------------------
# fakes
# ---------------------------------------------------------------------------
class FakeCompleted:
    def __init__(self, returncode=0, stderr=b""):
        self.returncode = returncode
        self.stderr = stderr
        self.stdout = b""


def fake_run_factory(returncode=0, stderr=b"", payload=b"\xff\xd8\xff\xe0jpegdata",
                     raises=None, record=None):
    """Build a stand-in for ``subprocess.run``.

    Writes ``payload`` to the ffmpeg output path (the argument after ``-y``)
    unless ``payload`` is falsy, then returns a :class:`FakeCompleted`.
    """

    def _run(cmd, **kwargs):
        if record is not None:
            record.append((cmd, kwargs))
        if raises is not None:
            raise raises
        out_path = cmd[-1]
        if payload:
            with open(out_path, "wb") as fh:
                fh.write(payload)
        else:
            open(out_path, "wb").close()
        return FakeCompleted(returncode=returncode, stderr=stderr)

    return _run


def make_capture(tmp_path, **overrides):
    kwargs = dict(
        name="cam01",
        url="rtsp://user:pass@camera.example:8554/ch1",
        destinations=[str(tmp_path / "out" / "cam01.jpg")],
    )
    kwargs.update(overrides)
    return RTSPCapture(**kwargs)


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------
def test_version_is_nonempty_string():
    assert isinstance(VERSION, str) and VERSION


@pytest.mark.parametrize("value, expected", [
    (None, None), ("", None), ("0", 0), ("5", 5), (3, 3),
])
def test_int_or_none(value, expected):
    assert _int_or_none(value) == expected


@pytest.mark.parametrize("value, expected", [
    (None, None), ("", None), ("644", 0o644), ("0644", 0o644),
    ("0o600", 0o600), ("755", 0o755),
])
def test_mode_or_none(value, expected):
    assert _mode_or_none(value) == expected


# ---------------------------------------------------------------------------
# build_command
# ---------------------------------------------------------------------------
def test_build_command_matches_reference_invocation(tmp_path):
    cap = make_capture(tmp_path)
    cmd = cap.build_command("/tmp/frame.jpg")
    assert cmd[0] == "ffmpeg"
    assert "-rtsp_transport" in cmd and cmd[cmd.index("-rtsp_transport") + 1] == "tcp"
    assert cmd[cmd.index("-i") + 1] == cap.url
    assert "-frames:v" in cmd and cmd[cmd.index("-frames:v") + 1] == "1"
    assert cmd[cmd.index("-q:v") + 1] == "2"
    assert cmd[-2:] == ["-y", "/tmp/frame.jpg"]


def test_build_command_omits_transport_and_quality_when_unset(tmp_path):
    cap = make_capture(tmp_path, rtsp_transport="", quality=None)
    cmd = cap.build_command("/tmp/f.jpg")
    assert "-rtsp_transport" not in cmd
    assert "-q:v" not in cmd


def test_build_command_places_extra_args_around_input(tmp_path):
    cap = make_capture(
        tmp_path,
        extra_input_args=["-timeout", "5000000"],
        extra_output_args=["-vf", "scale=640:-1"],
    )
    cmd = cap.build_command("/tmp/f.jpg")
    assert cmd.index("-timeout") < cmd.index("-i")
    assert cmd.index("-vf") > cmd.index("-i")
    assert cmd.index("-vf") < cmd.index("-y")


# ---------------------------------------------------------------------------
# capture(): success paths
# ---------------------------------------------------------------------------
def test_capture_writes_all_destinations(tmp_path, monkeypatch):
    dests = [str(tmp_path / "a" / "cam.jpg"), str(tmp_path / "b" / "cam.jpg")]
    cap = make_capture(tmp_path, destinations=dests)
    monkeypatch.setattr(subprocess, "run", fake_run_factory(payload=b"JPEGDATA"))

    written = cap.capture()

    assert written == dests
    for d in dests:
        assert os.path.isfile(d)
        with open(d, "rb") as fh:
            assert fh.read() == b"JPEGDATA"


def test_capture_applies_file_mode(tmp_path, monkeypatch):
    dest = str(tmp_path / "cam.jpg")
    cap = make_capture(tmp_path, destinations=[dest], file_mode=0o640)
    monkeypatch.setattr(subprocess, "run", fake_run_factory())

    cap.capture()

    mode = os.stat(dest).st_mode & 0o777
    if os.name == "posix":
        assert mode == 0o640


def test_capture_removes_temp_file(tmp_path, monkeypatch):
    cap = make_capture(tmp_path)
    seen = []
    real_factory = fake_run_factory(record=seen)
    monkeypatch.setattr(subprocess, "run", real_factory)

    cap.capture()

    tmp_out = seen[0][0][-1]
    assert not os.path.exists(tmp_out)


def test_capture_passes_timeout_and_devnull_stdin(tmp_path, monkeypatch):
    cap = make_capture(tmp_path, timeout=17)
    seen = []
    monkeypatch.setattr(subprocess, "run", fake_run_factory(record=seen))

    cap.capture()

    _cmd, kwargs = seen[0]
    assert kwargs["timeout"] == 17
    assert kwargs["stdin"] == subprocess.DEVNULL


# ---------------------------------------------------------------------------
# capture(): failure paths
# ---------------------------------------------------------------------------
def test_capture_missing_ffmpeg_raises(tmp_path, monkeypatch):
    cap = make_capture(tmp_path, ffmpeg_path="/no/such/ffmpeg")
    monkeypatch.setattr(
        subprocess, "run", fake_run_factory(raises=FileNotFoundError())
    )
    with pytest.raises(RTSPImageError, match="not found"):
        cap.capture()


def test_capture_timeout_raises(tmp_path, monkeypatch):
    cap = make_capture(tmp_path, timeout=3)
    monkeypatch.setattr(
        subprocess, "run",
        fake_run_factory(raises=subprocess.TimeoutExpired(cmd="ffmpeg", timeout=3)),
    )
    with pytest.raises(RTSPImageError, match="timed out after 3"):
        cap.capture()


def test_capture_nonzero_exit_includes_stderr(tmp_path, monkeypatch):
    cap = make_capture(tmp_path)
    monkeypatch.setattr(
        subprocess, "run",
        fake_run_factory(returncode=1, stderr=b"Connection refused", payload=b""),
    )
    with pytest.raises(RTSPImageError, match="Connection refused"):
        cap.capture()


def test_capture_empty_output_raises(tmp_path, monkeypatch):
    cap = make_capture(tmp_path)
    monkeypatch.setattr(subprocess, "run", fake_run_factory(payload=b""))
    with pytest.raises(RTSPImageError, match="empty file"):
        cap.capture()


def test_capture_failure_still_cleans_temp_file(tmp_path, monkeypatch):
    cap = make_capture(tmp_path)
    seen = []
    monkeypatch.setattr(
        subprocess, "run",
        fake_run_factory(returncode=1, stderr=b"boom", payload=b"", record=seen),
    )
    with pytest.raises(RTSPImageError):
        cap.capture()
    assert not os.path.exists(seen[0][0][-1])


# ---------------------------------------------------------------------------
# _publish
# ---------------------------------------------------------------------------
def test_publish_creates_parent_dirs(tmp_path):
    src = tmp_path / "src.jpg"
    src.write_bytes(b"x")
    dest = tmp_path / "deep" / "nested" / "out.jpg"
    make_capture(tmp_path)._publish(str(src), str(dest))
    assert dest.read_bytes() == b"x"


def test_publish_leaves_no_staging_file_on_success(tmp_path):
    src = tmp_path / "src.jpg"
    src.write_bytes(b"x")
    dest = tmp_path / "out.jpg"
    make_capture(tmp_path)._publish(str(src), str(dest))
    assert not (tmp_path / "out.jpg.rtspimage.tmp").exists()


# ---------------------------------------------------------------------------
# _build_cameras
# ---------------------------------------------------------------------------
def test_build_cameras_applies_defaults_and_overrides():
    skin = {
        "ffmpeg_path": "/usr/bin/ffmpeg",
        "rtsp_transport": "udp",
        "timeout": "45",
        "quality": "4",
        "cameras": {
            "front": {"url": "rtsp://h/1", "destinations": "/srv/front.jpg"},
            "back": {
                "url": "rtsp://h/2",
                "destinations": "/srv/back.jpg, /var/www/back.jpg",
                "timeout": "10",
                "quality": "",
                "rtsp_transport": "tcp",
            },
        },
    }
    cams = {c.name: c for c in RTSPImageGenerator._build_cameras(skin)}

    front = cams["front"]
    assert front.ffmpeg_path == "/usr/bin/ffmpeg"
    assert front.rtsp_transport == "udp"
    assert front.timeout == 45
    assert front.quality == 4
    assert front.destinations == ["/srv/front.jpg"]

    back = cams["back"]
    assert back.timeout == 10
    assert back.quality is None          # blank override wins over default
    assert back.rtsp_transport == "tcp"
    assert back.destinations == ["/srv/back.jpg", "/var/www/back.jpg"]


def test_build_cameras_skips_disabled_and_incomplete(caplog):
    skin = {
        "cameras": {
            "ok": {"url": "rtsp://h/1", "destinations": "/srv/a.jpg"},
            "off": {"url": "rtsp://h/2", "destinations": "/srv/b.jpg",
                    "enable": "false"},
            "no_url": {"destinations": "/srv/c.jpg"},
            "no_dest": {"url": "rtsp://h/4"},
        },
    }
    with caplog.at_level(logging.ERROR):
        cams = RTSPImageGenerator._build_cameras(skin)
    assert [c.name for c in cams] == ["ok"]
    assert "no_url" in caplog.text and "no_dest" in caplog.text


def test_build_cameras_missing_section_is_empty():
    assert RTSPImageGenerator._build_cameras({}) == []
    assert RTSPImageGenerator._build_cameras({"cameras": {}}) == []


def test_build_cameras_scalar_section_is_malformed(caplog):
    with caplog.at_level(logging.ERROR):
        assert RTSPImageGenerator._build_cameras({"cameras": "oops"}) == []
    assert "missing or malformed" in caplog.text


# ---------------------------------------------------------------------------
# run()
# ---------------------------------------------------------------------------
def _generator(skin):
    return RTSPImageGenerator({"WEEWX_ROOT": "/tmp"}, skin, None, None, None)


def test_run_disabled_does_nothing(caplog):
    gen = _generator({"enable": "false", "cameras": {
        "a": {"url": "rtsp://h/1", "destinations": "/srv/a.jpg"}}})
    with caplog.at_level(logging.DEBUG):
        assert gen.run() is None
    assert "disabled" in caplog.text


def test_run_no_cameras_logs_and_returns(caplog):
    gen = _generator({"cameras": {}})
    with caplog.at_level(logging.INFO):
        assert gen.run() is None
    assert "nothing to do" in caplog.text


def test_run_captures_every_camera(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(subprocess, "run", fake_run_factory())
    skin = {"cameras": {
        "a": {"url": "rtsp://h/1", "destinations": str(tmp_path / "a.jpg")},
        "b": {"url": "rtsp://h/2", "destinations": str(tmp_path / "b.jpg")},
    }}
    with caplog.at_level(logging.INFO):
        _generator(skin).run()
    assert (tmp_path / "a.jpg").exists() and (tmp_path / "b.jpg").exists()
    assert "captured 2 of 2 cameras (2 files)" in caplog.text


def test_run_one_camera_failure_does_not_abort(tmp_path, monkeypatch, caplog):
    def flaky_run(cmd, **kwargs):
        if "rtsp://h/1" in cmd:
            raise subprocess.TimeoutExpired(cmd="ffmpeg", timeout=1)
        with open(cmd[-1], "wb") as fh:
            fh.write(b"JPEG")
        return FakeCompleted()

    monkeypatch.setattr(subprocess, "run", flaky_run)
    skin = {"cameras": {
        "bad": {"url": "rtsp://h/1", "destinations": str(tmp_path / "bad.jpg")},
        "good": {"url": "rtsp://h/2", "destinations": str(tmp_path / "good.jpg")},
    }}
    with caplog.at_level(logging.INFO):
        _generator(skin).run()
    assert not (tmp_path / "bad.jpg").exists()
    assert (tmp_path / "good.jpg").exists()
    assert "captured 1 of 2 cameras (1 files)" in caplog.text


def test_run_can_silence_success_log(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(subprocess, "run", fake_run_factory())
    skin = {"log_success": "false", "cameras": {
        "a": {"url": "rtsp://h/1", "destinations": str(tmp_path / "a.jpg")}}}
    with caplog.at_level(logging.INFO):
        _generator(skin).run()
    assert "captured" not in caplog.text
