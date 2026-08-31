# weewx-rtsp-image

[![CI](https://github.com/ziti/weewx-rtsp-image/actions/workflows/ci.yml/badge.svg)](https://github.com/ziti/weewx-rtsp-image/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/ziti/weewx-rtsp-image?sort=semver)](https://github.com/ziti/weewx-rtsp-image/releases)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

A [WeeWX](https://weewx.com/) extension that grabs a still frame from one or
more RTSP camera feeds and saves it to one or more local destinations.

It replaces the common "cron job that runs `ffmpeg` once a minute and drops a
JPEG into the skin folder" pattern with a configured, logged report generator
that runs as part of the normal WeeWX report cycle.

- **Multiple cameras** — each with its own URL, capture options, and
  destination list.
- **Nothing hard coded** — every value comes from `weewx.conf`.
- **Atomic writes** — frames are written to a temporary file and then moved
  into place, so a web server never serves a half-written image.
- **Fails soft** — a camera that is offline logs an error and is skipped; the
  rest of the report still runs.

---

## Requirements

| Requirement | Notes |
|-------------|-------|
| WeeWX       | 5.4 or newer (uses `weectl extension` and the modern report engine). |
| Python      | 3.9 or newer (matches WeeWX 5). |
| `ffmpeg`    | Must be installed and on `PATH` (or give an absolute path in the config). Install with `apt install ffmpeg`, `dnf install ffmpeg`, `brew install ffmpeg`, etc. |

The extension itself has **no Python dependencies** beyond the standard
library and WeeWX.

---

## Installation

1. Download the latest release archive:

   ```bash
   wget https://github.com/ziti/weewx-rtsp-image/releases/latest/download/weewx-rtsp-image.zip
   ```

   (Or grab a specific `weewx-rtsp-image-<version>.zip` from the
   [releases page](https://github.com/ziti/weewx-rtsp-image/releases).)

2. Install it:

   ```bash
   weectl extension install weewx-rtsp-image.zip
   ```

3. Edit `weewx.conf` to point at your camera(s) — see
   [Configuration](#configuration) below.

4. Restart WeeWX:

   ```bash
   sudo systemctl restart weewx
   ```

The installer adds a starter `[StdReport] / [[rtspimage]]` section with one
example camera. It will **not** capture anything useful until you replace the
example URL and destination with real values.

---

## Configuration

All configuration lives in `weewx.conf` under `[StdReport]`:

```ini
[StdReport]

    # ... your existing reports (SeasonsReport, Belchertown, etc.) ...

    [[rtspimage]]
        skin = rtspimage
        enable = true

        # ---- defaults inherited by every camera below ----
        ffmpeg_path = ffmpeg
        rtsp_transport = tcp
        timeout = 30
        quality = 2
        # file_mode = 0644

        # How often to capture: standard WeeWX report timing. Omit for
        # "every archive interval". Example: once a minute:
        # report_timing = "* * * * *"

        [[[cameras]]]

            [[[[cam01]]]]
                url = rtsp://user:password@192.168.8.124:8554/ch1
                destinations = /var/www/html/belchertown/cam01.jpg

            [[[[driveway]]]]
                url = rtsp://user:password@192.168.8.130:554/stream1
                destinations = /var/www/html/belchertown/driveway.jpg, /srv/timelapse/driveway/latest.jpg
                quality = 3
                timeout = 15
```

### Options

Options set directly under `[[rtspimage]]` are **defaults**; any camera can
override them in its own `[[[[section]]]]`.

| Option | Default | Scope | Description |
|--------|---------|-------|-------------|
| `enable` | `true` | report | Set to `false` to disable all captures without removing the config. |
| `log_success` | `true` | report | Log a one-line summary after each run. |
| `ffmpeg_path` | `ffmpeg` | default + camera | Name or absolute path of the `ffmpeg` executable. |
| `rtsp_transport` | `tcp` | default + camera | Value for ffmpeg's `-rtsp_transport` (`tcp` or `udp`). Set empty to omit the flag. |
| `timeout` | `30` | default + camera | Hard limit in seconds for each `ffmpeg` run. The process is killed if it exceeds this. |
| `quality` | `2` | default + camera | Value for ffmpeg's `-q:v` (1 = best, 31 = worst). Set empty to omit. |
| `file_mode` | *(unset)* | default + camera | Octal mode applied to each written file, e.g. `0644`. Unset leaves the OS default. |
| `ffmpeg_input_args` | *(unset)* | default + camera | Extra ffmpeg arguments inserted **before** `-i` (shell-quoted). |
| `ffmpeg_output_args` | *(unset)* | default + camera | Extra ffmpeg arguments inserted **before** the output path (shell-quoted), e.g. `-vf scale=1280:-1`. |
| `url` | *(required)* | camera | Full RTSP URL, including credentials if the camera needs them. |
| `destinations` | *(required)* | camera | One or more absolute paths, comma-separated. Parent directories are created if missing. |
| `enable` | `true` | camera | Set to `false` to skip just this camera. |

### The generated ffmpeg command

With the defaults above, each capture runs the equivalent of:

```bash
ffmpeg -nostdin -loglevel error -rtsp_transport tcp \
    -i "<url>" -frames:v 1 -q:v 2 -y "<temp file>"
```

which mirrors the classic one-shot grab. Use `ffmpeg_input_args` /
`ffmpeg_output_args` for anything else (scaling, drawtext timestamp overlays,
`-ss` seek, alternate codecs, and so on).

### Capture frequency

The extension runs whenever WeeWX runs its reports — by default once per
archive interval (commonly five minutes). To capture more or less often, set
[`report_timing`](https://weewx.com/docs/latest/reference/report-options/report_timing/)
in the `[[rtspimage]]` section, e.g. `report_timing = "* * * * *"` for every
minute.

### File ownership

When WeeWX runs the report it does so as the WeeWX user, so captured files are
owned by that user — no `chown` step is needed. Use `file_mode` if your web
server needs specific permissions.

### A note on credentials

The RTSP URL (including any username/password) is stored in `weewx.conf`.
Make sure that file is readable only by the WeeWX user
(`chmod 640 /etc/weewx/weewx.conf`). Never paste a real URL into a bug report.

---

## Testing your configuration

Run the report on demand and watch the log:

```bash
weectl report run rtspimage
sudo journalctl -u weewx -n 50 --no-pager
```

For a lower-level check that bypasses WeeWX entirely:

```bash
PYTHONPATH=/usr/share/weewx python /usr/share/weewx/user/rtspimage.py \
    --config /etc/weewx/weewx.conf --debug
```

If that fails, run your raw `ffmpeg` command by hand to isolate the camera
from the extension.

---

## Upgrading

Install the new archive over the old one:

```bash
weectl extension install weewx-rtsp-image-<new-version>.zip
sudo systemctl restart weewx
```

`weectl` replaces the extension's files. Your `[StdReport] / [[rtspimage]]`
settings in `weewx.conf` are left untouched. Check
[`CHANGELOG.md`](CHANGELOG.md) for any new or renamed options.

---

## Uninstalling

```bash
weectl extension uninstall rtspimage
sudo systemctl restart weewx
```

This removes the extension's files and the `[[rtspimage]]` report section.
Any JPEGs already written to your destinations are left in place.

---

## Troubleshooting

| Symptom | Things to check |
|---------|-----------------|
| `ffmpeg executable 'ffmpeg' not found` | `ffmpeg` is not installed or not on the WeeWX user's `PATH`. Set `ffmpeg_path` to an absolute path. |
| `ffmpeg timed out after N seconds` | Camera unreachable or slow to hand over a keyframe. Raise `timeout`, try `rtsp_transport = udp`, or check the network/credentials. |
| `ffmpeg exited 1: ...` | Read the message after the colon — usually a bad URL, wrong credentials, or an unsupported stream. Reproduce with a manual `ffmpeg` command. |
| `ffmpeg produced an empty file` | The stream connected but no frame decoded. Try adding `-ss 1` via `ffmpeg_input_args`, or a longer `timeout`. |
| Nothing happens on schedule | Confirm the report is listed by `weectl report run rtspimage`, and check `report_timing`. |
| Permission denied writing the file | The WeeWX user cannot write the destination directory. Fix directory ownership, or point `destinations` somewhere writable. |

Enable WeeWX debug logging (`debug = 1` in `weewx.conf`) for the full ffmpeg
command and per-camera detail.

---

## Contributing

Bug reports and pull requests are welcome. Please read
[CONTRIBUTING.md](CONTRIBUTING.md) first — it covers the coding standard,
commit-message convention, and what a good PR looks like. All participation is
governed by the [Code of Conduct](CODE_OF_CONDUCT.md).

Security issues: see [SECURITY.md](SECURITY.md).

---

## License

Distributed under the terms of the **GNU General Public License v3.0**. See
[LICENSE](LICENSE).
