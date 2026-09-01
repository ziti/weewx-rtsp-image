# Security Policy

## Supported versions

This project is maintained on a best-effort basis. Security fixes are made
against the **latest release** only. Please upgrade before reporting.

| Version | Supported |
|---------|-----------|
| latest release | :white_check_mark: |
| anything older | :x: |

## Reporting a vulnerability

Please **do not open a public issue** for security problems.

Report privately through
[GitHub private vulnerability reporting](https://github.com/ziti/weewx-rtsp-image/security/advisories/new)
— on the repository, open the **Security** tab and choose
**Report a vulnerability**. This keeps the report and the discussion private
until a fix ships.

Please include:

- a description of the issue and its impact,
- steps to reproduce or a proof of concept,
- affected version(s),
- any suggested fix.

You can expect an acknowledgement within about a week. Once a fix is ready a
new release will be published and the advisory disclosed, with credit to the
reporter unless you prefer otherwise.

## Scope notes

- This extension shells out to `ffmpeg` using an argument list (never a
  shell), with values taken from `weewx.conf`. Anyone who can edit
  `weewx.conf` can already run commands as the WeeWX user, so config-driven
  command construction is by design, not a vulnerability.
- RTSP URLs and credentials live in `weewx.conf`. Keep that file readable
  only by the WeeWX user, and redact URLs before sharing logs or configs.
