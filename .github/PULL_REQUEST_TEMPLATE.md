<!--
Conventional Commit title, e.g.:
  feat: add per-camera timestamp overlay option
  fix: create destination directory when missing
Describe the change in behaviour, not the files touched.
-->

## Why

<!-- The problem this solves. What was wrong or missing? -->

## What changed

<!-- A short summary of the approach. -->

## Related issues

<!-- "Closes #123" so the issue closes on merge. Use "Refs #123" if it only relates. -->
Closes #

## Configuration changes

<!-- Delete if none. Otherwise list each option: name, section, default, and
     confirm README.md + CHANGELOG.md are updated. -->
- [ ] No config changes
- [ ] New/changed options documented in `README.md`
- [ ] `CHANGELOG.md` updated under `[Unreleased]`

## Checklist

- [ ] Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/)
- [ ] `ruff check .` passes
- [ ] `pytest -q` passes; new behaviour has unit tests (default, override, bad value)
- [ ] No hard-coded paths/hosts/timeouts/flags — new knobs read from config with defaults
- [ ] No secrets, real hostnames, or capture output committed; `ffmpeg` still invoked as an argument list (no `shell=True`)
- [ ] Backwards compatible with existing `weewx.conf` setups (or the break is called out below)

## Compatibility notes

<!-- Anything users must change when upgrading, or a required WeeWX version bump. -->
