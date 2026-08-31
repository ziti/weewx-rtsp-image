# Contributing to weewx-rtsp-image

Thanks for taking the time to contribute! This is a small project, so the
process is light — but a few things keep it maintainable.

By participating you agree to abide by the [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Before you open an issue

Please do the basic troubleshooting first:

1. Confirm you are on **WeeWX 5.4+** and the latest release of this extension.
2. Reproduce your raw capture with a plain `ffmpeg` command to rule out the
   camera, network, or credentials.
3. Run `weectl report run rtspimage` and read the WeeWX log with
   `debug = 1` set in `weewx.conf`.
4. Search [existing issues](https://github.com/ziti/weewx-rtsp-image/issues).

When you do open a bug report, the issue form will ask for your WeeWX version,
extension version, OS, `ffmpeg -version`, your `[[rtspimage]]` config **with
credentials redacted**, and the relevant log lines. Please fill it in — issues
without this information usually can't be acted on.

---

## Development setup

```bash
git clone https://github.com/ziti/weewx-rtsp-image.git
cd weewx-rtsp-image
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
```

Run the checks that CI runs:

```bash
ruff check .                       # lint
python -m compileall -q bin install.py
pytest -q                          # unit tests
```

The unit tests stub out `ffmpeg` and (when WeeWX is not installed) WeeWX
itself, so they run anywhere. CI additionally imports the module against a
real WeeWX install.

---

## Coding standard

Python code follows **[PEP 8](https://peps.python.org/pep-0008/)**, enforced by
[`ruff`](https://docs.astral.sh/ruff/) using the configuration in
`pyproject.toml` (line length 100; `E`, `F`, `W`, `I`, `B`, `UP`, `SIM`
rule sets). `ruff check .` must pass with no warnings.

Additionally:

- **Configuration over constants.** Anything a user might reasonably want to
  change belongs in `weewx.conf`, read via `skin_dict`, with a sensible
  default. Don't hard-code paths, hosts, timeouts, or ffmpeg flags.
- **Fail soft, log clearly.** One misbehaving camera must never abort the
  report. Raise `RTSPImageError` with an actionable message; the generator
  logs it and moves on.
- **Keep runtime dependencies at zero.** Standard library plus WeeWX only. If
  you think you need a third-party package, open an issue to discuss first.
- Keep functions small and prefer pure helpers that are easy to test.
- Add or update docstrings for anything non-obvious.

### Secure coding

- Never log full RTSP URLs at `INFO` or above (they contain credentials); the
  full command is only emitted at `DEBUG`.
- Build the `ffmpeg` argument list as a list passed to `subprocess.run` —
  never `shell=True`, never string interpolation into a shell command.
- Validate and normalise anything that becomes a filesystem path; write to a
  temp file and `os.replace` into place.
- Don't commit real hostnames, credentials, or capture output.

---

## Tests

Every behavioural change needs unit tests:

- New config options: cover the default, an override, and a bad value.
- New failure modes: assert the `RTSPImageError` message and that other
  cameras still run.
- Bug fixes: add a test that fails before your fix and passes after.

---

## Commit messages

This project uses **[Conventional Commits](https://www.conventionalcommits.org/)**.
Describe the *change in behaviour*, not the files touched.

```
feat: add per-camera drawtext timestamp overlay option
fix: kill ffmpeg process group so udp readers don't linger
docs: document report_timing for sub-interval capture
test: cover empty-output handling
ci: run the test matrix on Python 3.13
refactor: extract command building into build_command()
chore: bump ruff to 0.7
```

- Good: `fix: create destination directory when it is missing`
- Avoid: `update rtspimage.py` / `fixes` / `misc changes`

Breaking changes get a `!` and a `BREAKING CHANGE:` footer.

---

## Pull requests

Open PRs against `main`. The PR description (there is a template) should cover:

1. **Why** the change is needed — the problem, not just the diff.
2. **Linked issue** — write `Closes #123` so the issue closes on merge.
3. **Config changes** — list any new/renamed/removed options, their defaults,
   and confirm `README.md` and `CHANGELOG.md` are updated.
4. **Tests** — what you added and that `ruff` + `pytest` pass locally.
5. **Compatibility** — note anything that affects existing `weewx.conf`
   setups or requires a WeeWX version bump.

Keep PRs focused on one thing. Unrelated cleanups belong in their own PR.

### Releases (maintainers)

1. Update `VERSION` in `bin/user/rtspimage.py`, `version=` in `install.py`,
   and add a dated section to `CHANGELOG.md`.
2. Commit (`chore(release): 0.2.0`), then tag `v0.2.0` and push the tag.
3. The release workflow checks the three versions agree, builds
   `weewx-rtsp-image-0.2.0.zip`, and creates the GitHub Release with notes
   taken from the changelog.
