# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-08-31

### Added
- Initial release.
- `RTSPImageGenerator` WeeWX report generator that captures a single frame
  from one or more RTSP feeds by invoking `ffmpeg`, and writes each frame to
  one or more local destinations.
- Per-camera configuration under `[StdReport] / [[rtspimage]] / [[[cameras]]]`
  with inheritable defaults for `ffmpeg_path`, `rtsp_transport`, `timeout`,
  `quality`, `file_mode`, and extra ffmpeg input/output arguments.
- Atomic publish (write-to-temp then `os.replace`) with automatic creation of
  destination directories and optional file-mode enforcement.
- Unit test suite, `ruff` linting, GitHub Actions CI, and a tag-driven
  release workflow that publishes an installable extension archive.

[Unreleased]: https://github.com/ziti/weewx-rtsp-image/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/ziti/weewx-rtsp-image/releases/tag/v0.1.0
