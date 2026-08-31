# Copyright 2026 Zach Taffet
# Distributed under the terms of the GNU General Public License v3 (GPLv3).
# See the LICENSE file for the full text.
"""Capture still images from RTSP camera feeds for WeeWX.

This extension runs as a WeeWX report generator.  On each report cycle it
invokes ``ffmpeg`` once per configured camera, grabs a single video frame,
and writes the resulting image to one or more local destinations.

Nothing about the cameras, the ``ffmpeg`` binary, or the output locations is
hard coded -- every value comes from the ``[StdReport] / [[rtspimage]]``
section of ``weewx.conf``.  See ``README.md`` for the full option reference.

Standalone smoke test (does not touch WeeWX internals beyond config parsing)::

    PYTHONPATH=bin python bin/user/rtspimage.py --config /etc/weewx/weewx.conf
"""

import contextlib
import logging
import os
import shlex
import shutil
import subprocess
import tempfile
import time

import weewx
import weewx.reportengine
from weeutil.weeutil import to_bool

log = logging.getLogger(__name__)

VERSION = "0.1.0"

DEFAULT_FFMPEG = "ffmpeg"
DEFAULT_RTSP_TRANSPORT = "tcp"
DEFAULT_TIMEOUT = 30
DEFAULT_QUALITY = 2


def logdbg(msg, label="rtspimage"):
    log.debug("%s: %s", label, msg)


def loginf(msg, label="rtspimage"):
    log.info("%s: %s", label, msg)


def logerr(msg, label="rtspimage"):
    log.error("%s: %s", label, msg)


class RTSPImageError(Exception):
    """Raised when a single camera capture cannot be completed."""


def _int_or_none(value):
    """Return ``value`` as an int, or ``None`` when it is unset/blank."""
    if value is None or value == "":
        return None
    return int(value)


def _as_list(value):
    """Normalise a config value into a clean list of non-empty strings.

    Accepts what ConfigObj may hand us: a real list (comma-separated values
    in ``weewx.conf``), a bare string, or ``None``.  A single string is also
    split on commas so a quoted ``"a, b"`` still works.
    """
    if value is None:
        return []
    items = value if isinstance(value, (list, tuple)) else str(value).split(",")
    return [item.strip() for item in items if item and item.strip()]


def _mode_or_none(value):
    """Parse a file-mode string such as ``"0644"`` into an int.

    Modes are always interpreted as octal, with or without a leading ``0o`` /
    ``0`` prefix, so both ``644`` and ``0644`` mean ``rw-r--r--``.
    """
    if value is None or value == "":
        return None
    text = str(value).strip()
    return int(text, 8)


class RTSPCapture:
    """Grab a single frame from one RTSP feed and publish it.

    Args:
        name: Camera name, used only for logging.
        url: Full RTSP URL, including any embedded credentials.
        destinations: Iterable of absolute file paths to write the frame to.
        ffmpeg_path: Path to (or name of) the ffmpeg executable.
        rtsp_transport: Value for ffmpeg's ``-rtsp_transport`` flag, or a
            falsy value to omit the flag entirely.
        timeout: Hard wall-clock limit, in seconds, for the ffmpeg process.
        quality: Value for ffmpeg's ``-q:v`` flag (lower is better quality),
            or ``None`` to omit it.
        extra_input_args: Extra ffmpeg arguments placed before ``-i``.
        extra_output_args: Extra ffmpeg arguments placed before the output path.
        file_mode: Optional integer mode (e.g. ``0o644``) applied to each
            published file.
    """

    def __init__(self, name, url, destinations, ffmpeg_path=DEFAULT_FFMPEG,
                 rtsp_transport=DEFAULT_RTSP_TRANSPORT, timeout=DEFAULT_TIMEOUT,
                 quality=DEFAULT_QUALITY, extra_input_args=None,
                 extra_output_args=None, file_mode=None):
        self.name = name
        self.url = url
        self.destinations = [os.path.expanduser(d) for d in destinations]
        self.ffmpeg_path = ffmpeg_path
        self.rtsp_transport = rtsp_transport
        self.timeout = timeout
        self.quality = quality
        self.extra_input_args = list(extra_input_args or [])
        self.extra_output_args = list(extra_output_args or [])
        self.file_mode = file_mode

    def build_command(self, output_path):
        """Return the ffmpeg argument list for capturing to ``output_path``."""
        cmd = [self.ffmpeg_path, "-nostdin", "-loglevel", "error"]
        if self.rtsp_transport:
            cmd += ["-rtsp_transport", self.rtsp_transport]
        cmd += self.extra_input_args
        cmd += ["-i", self.url, "-frames:v", "1"]
        if self.quality is not None:
            cmd += ["-q:v", str(self.quality)]
        cmd += self.extra_output_args
        cmd += ["-y", output_path]
        return cmd

    def capture(self):
        """Grab one frame and write it to every destination.

        Returns the list of destination paths that were written.  Raises
        :class:`RTSPImageError` if ffmpeg is missing, times out, exits
        non-zero, or produces an empty file.
        """
        fd, tmp_path = tempfile.mkstemp(prefix="rtspimage-", suffix=".jpg")
        os.close(fd)
        try:
            cmd = self.build_command(tmp_path)
            logdbg("camera %s: running %s" % (self.name, " ".join(cmd)))
            try:
                proc = subprocess.run(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    timeout=self.timeout,
                )
            except FileNotFoundError as e:
                raise RTSPImageError(
                    "camera %s: ffmpeg executable %r not found"
                    % (self.name, self.ffmpeg_path)
                ) from e
            except subprocess.TimeoutExpired as e:
                raise RTSPImageError(
                    "camera %s: ffmpeg timed out after %s seconds"
                    % (self.name, self.timeout)
                ) from e

            if proc.returncode != 0:
                detail = proc.stderr.decode("utf-8", "replace").strip()
                raise RTSPImageError(
                    "camera %s: ffmpeg exited %s%s"
                    % (self.name, proc.returncode, ": %s" % detail if detail else "")
                )
            if os.path.getsize(tmp_path) == 0:
                raise RTSPImageError(
                    "camera %s: ffmpeg produced an empty file" % self.name
                )

            written = []
            for dest in self.destinations:
                self._publish(tmp_path, dest)
                written.append(dest)
            return written
        finally:
            with contextlib.suppress(OSError):
                os.remove(tmp_path)

    def _publish(self, tmp_path, dest):
        """Copy ``tmp_path`` to ``dest`` atomically, creating parent dirs."""
        dest_dir = os.path.dirname(dest)
        if dest_dir and not os.path.isdir(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)
        staging = "%s.rtspimage.tmp" % dest
        shutil.copyfile(tmp_path, staging)
        try:
            if self.file_mode is not None:
                os.chmod(staging, self.file_mode)
            os.replace(staging, dest)
        except OSError:
            with contextlib.suppress(OSError):
                os.remove(staging)
            raise


class RTSPImageGenerator(weewx.reportengine.ReportGenerator):
    """WeeWX report generator that captures a frame from each camera."""

    def run(self):
        if not to_bool(self.skin_dict.get("enable", True)):
            logdbg("generator is disabled via 'enable = false'")
            return

        log_success = to_bool(self.skin_dict.get("log_success", True))
        cameras = self._build_cameras(self.skin_dict)
        if not cameras:
            loginf("no cameras configured; nothing to do")
            return

        t1 = time.time()
        n_ok = 0
        n_files = 0
        for cam in cameras:
            try:
                written = cam.capture()
            except RTSPImageError as e:
                logerr(str(e))
                continue
            except Exception as e:  # never let one camera abort the report
                logerr("camera %s: unexpected error: %s" % (cam.name, e))
                continue
            n_ok += 1
            n_files += len(written)
            logdbg("camera %s wrote %s" % (cam.name, ", ".join(written)))

        if log_success:
            loginf(
                "captured %d of %d cameras (%d files) in %.2f seconds"
                % (n_ok, len(cameras), n_files, time.time() - t1)
            )

    @classmethod
    def _build_cameras(cls, skin_dict):
        """Turn the merged skin/report config into ``RTSPCapture`` objects."""
        cameras_cfg = skin_dict.get("cameras", {})
        if not hasattr(cameras_cfg, "items"):
            logerr("'cameras' section is missing or malformed")
            return []

        defaults = {
            "ffmpeg_path": skin_dict.get("ffmpeg_path", DEFAULT_FFMPEG),
            "rtsp_transport": skin_dict.get("rtsp_transport", DEFAULT_RTSP_TRANSPORT),
            "timeout": int(skin_dict.get("timeout", DEFAULT_TIMEOUT)),
            "quality": _int_or_none(skin_dict.get("quality", DEFAULT_QUALITY)),
            "file_mode": _mode_or_none(skin_dict.get("file_mode")),
            "ffmpeg_input_args": skin_dict.get("ffmpeg_input_args", ""),
            "ffmpeg_output_args": skin_dict.get("ffmpeg_output_args", ""),
        }

        cameras = []
        for name, cfg in cameras_cfg.items():
            if not hasattr(cfg, "get"):
                logerr("camera %s: expected a config section, got a scalar" % name)
                continue
            if not to_bool(cfg.get("enable", True)):
                logdbg("camera %s is disabled; skipping" % name)
                continue

            url = cfg.get("url")
            destinations = _as_list(
                cfg.get("destinations", cfg.get("destination"))
            )
            if not url or not destinations:
                logerr(
                    "camera %s: both 'url' and 'destinations' are required" % name
                )
                continue

            cameras.append(RTSPCapture(
                name=name,
                url=url,
                destinations=destinations,
                ffmpeg_path=cfg.get("ffmpeg_path", defaults["ffmpeg_path"]),
                rtsp_transport=cfg.get(
                    "rtsp_transport", defaults["rtsp_transport"]
                ),
                timeout=int(cfg.get("timeout", defaults["timeout"])),
                quality=_int_or_none(cfg.get("quality", defaults["quality"])),
                extra_input_args=shlex.split(
                    cfg.get("ffmpeg_input_args", defaults["ffmpeg_input_args"])
                ),
                extra_output_args=shlex.split(
                    cfg.get("ffmpeg_output_args", defaults["ffmpeg_output_args"])
                ),
                file_mode=(
                    _mode_or_none(cfg.get("file_mode"))
                    if "file_mode" in cfg
                    else defaults["file_mode"]
                ),
            ))
        return cameras


# ---------------------------------------------------------------------------
# Standalone entry point: PYTHONPATH=bin python bin/user/rtspimage.py --config ...
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    import configobj

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", dest="config_path", metavar="CONFIG_FILE",
                        default="/etc/weewx/weewx.conf",
                        help="path to weewx.conf")
    parser.add_argument("--report", default="rtspimage",
                        help="name of the StdReport entry to use")
    parser.add_argument("--debug", action="store_true", help="verbose logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    config = configobj.ConfigObj(args.config_path, file_error=True, encoding="utf-8")
    skin_dict = dict(config.get("StdReport", {}).get(args.report, {}))
    if "cameras" not in skin_dict:
        raise SystemExit(
            "no [StdReport] [[%s]] [[[cameras]]] section found in %s"
            % (args.report, args.config_path)
        )

    gen = RTSPImageGenerator(
        {"WEEWX_ROOT": config.get("WEEWX_ROOT", os.getcwd())},
        skin_dict, gen_ts=None, first_run=True, stn_info=None,
    )
    gen.run()
