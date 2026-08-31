<!--
Conventional Commit title, e.g.:
  feat: add --output-format flag
  fix: handle empty API response
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

- [ ] No config changes
- [ ] New/changed options documented in `README.md`
- [ ] `CHANGELOG.md` updated under `[Unreleased]`

## Checklist

- [ ] Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/)
- [ ] Lint/format passes
- [ ] Build passes
- [ ] Tests pass; new behaviour has tests (default, non-default, invalid input)
- [ ] No hard-coded values that belong in configuration
- [ ] No secrets, tokens, or private hostnames committed; external input validated; no shell string-building
- [ ] Backwards compatible for existing users (or the break is called out below)

## Compatibility notes

<!-- Anything users must change when upgrading, or a required runtime/version bump. -->
