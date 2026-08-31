# Contributing to {{PROJECT_NAME}}

Thanks for taking the time to contribute! By participating you agree to abide
by the [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Before you open an issue

1. Make sure you're on the latest release.
2. Do the basic troubleshooting for your problem and capture the output.
3. Search [existing issues](https://github.com/{{OWNER}}/{{PROJECT_SLUG}}/issues).

The bug report form asks for versions, environment, exact steps to reproduce,
and logs. Please fill it in — issues without this usually can't be acted on.
Redact secrets, tokens, and private hostnames from anything you paste.

---

## Development setup

```bash
git clone https://github.com/{{OWNER}}/{{PROJECT_SLUG}}.git
cd {{PROJECT_SLUG}}
# install the toolchain for this project's stack
```

Run the same checks CI runs before pushing (lint, build, tests).

---

## Coding standards

- **Configuration over constants.** Anything a user might reasonably want to
  change belongs in configuration with a sensible default — not hard-coded.
- **Small, focused changes.** One concern per pull request. Unrelated cleanups
  go in their own PR.
- **Readable code.** Match the style of the surrounding code. Keep functions
  small and prefer pure, testable helpers.
- **Document non-obvious behaviour** in code comments and user-facing docs.

### Secure coding

- Never commit secrets, credentials, tokens, or private hostnames. Use
  environment variables or a secrets manager.
- Treat all external input as untrusted: validate and normalise it.
- Build subprocess calls as argument lists, never by string-concatenating into
  a shell.
- Keep dependencies minimal and pinned; review what new ones pull in.
- Report vulnerabilities privately per [SECURITY.md](SECURITY.md).

### Tests

Every behavioural change needs tests:

- New options/features: cover the default, a non-default value, and an invalid
  value.
- Bug fixes: add a test that fails before the fix and passes after.

<!-- ═══════════════════════════════════════════════════════════════════════
     .NET / C# overlay — delete this section for non-.NET projects
     ═══════════════════════════════════════════════════════════════════════ -->

### C# / .NET specifics

- Target **.NET 10**. Use the current C# language version.
- Follow the [.NET runtime coding style][dotnet-style] and Microsoft's
  [Framework Design Guidelines][fdg]. Formatting is enforced by
  **`dotnet format`** against `.editorconfig`; CI fails on any diff.
- Enable `<Nullable>enable</Nullable>` and
  `<TreatWarningsAsErrors>true</TreatWarningsAsErrors>` (put them in
  `Directory.Build.props`). Keep the built-in analyzers clean; suppress a rule
  only with an inline justification.
- Tests use **xUnit** (`dotnet test`). Name tests `Method_State_Expectation`.
- Prefer `async`/`await` end to end; never `.Result` / `.Wait()`. Pass
  `CancellationToken` through public async APIs.
- Public API changes go in `CHANGELOG.md` and, if the project ships a library,
  follow [SemVer](https://semver.org/).

[dotnet-style]: https://github.com/dotnet/runtime/blob/main/docs/coding-guidelines/coding-style.md
[fdg]: https://learn.microsoft.com/dotnet/standard/design-guidelines/

<!-- ═══════════════════════════════════════════════════════════════════════
     end .NET / C# overlay
     ═══════════════════════════════════════════════════════════════════════ -->

---

## Commit messages

This project uses **[Conventional Commits](https://www.conventionalcommits.org/)**.
Describe the *change in behaviour*, not the files touched.

```
feat: add --output-format flag
fix: handle empty response from the widgets API
docs: document the retry configuration
test: cover the malformed-config path
ci: run the test matrix on the latest runtime
refactor: extract retry logic into its own type
chore: bump analyzers to the latest version
```

- Good: `fix: create the cache directory when it is missing`
- Avoid: `update code` / `fixes` / `misc changes`

Breaking changes get a `!` (e.g. `feat!:`) and a `BREAKING CHANGE:` footer.

---

## Pull requests

Open PRs against `main`. There is a template; it asks you to cover:

1. **Why** the change is needed — the problem, not just the diff.
2. **Linked issue** — write `Closes #123` so it closes on merge.
3. **Config changes** — new/renamed/removed options, their defaults, and the
   docs updated to match.
4. **Tests** — what you added, and confirmation that lint, build, and tests
   pass locally.
5. **Compatibility** — anything that affects existing users or needs a
   runtime/version bump.

### Releases (maintainers)

1. Bump the version and add a dated section to `CHANGELOG.md`.
2. Commit as `chore(release): X.Y.Z`.
3. Tag `vX.Y.Z` and push the tag — the release workflow does the rest.
