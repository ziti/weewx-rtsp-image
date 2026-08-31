# Using this template

This repository is a starting point for a well-run open-source project. The
community-health files (license, code of conduct, contributing guide, issue
and PR templates) are **language-agnostic**. The CI and release automation
under `.github/workflows/` are a **C# / .NET 10 overlay** — swap them for your
stack if the project isn't .NET.

## 1. Create your repo

Click **Use this template** on GitHub, or:

```bash
gh repo create <owner>/<project> --public --template <owner>/oss-template
```

## 2. Replace the placeholders

Search the whole tree for `{{ ... }}` and fill each in:

| Placeholder            | Meaning                                   | Example                          |
|------------------------|-------------------------------------------|----------------------------------|
| `{{PROJECT_NAME}}`     | Human-readable name                       | `Acme Widget CLI`                |
| `{{PROJECT_SLUG}}`     | Repo name / package id                    | `acme-widget-cli`                |
| `{{PROJECT_DESCRIPTION}}` | One-line description                    | `A CLI for managing widgets.`    |
| `{{OWNER}}`            | GitHub user or org                        | `ziti`                           |
| `{{COPYRIGHT_HOLDER}}` | Name on the copyright line               | `Zach Taffet`                    |
| `{{CONTACT_EMAIL}}`    | Security / conduct contact               | `you@example.com`                |
| `{{YEAR}}`             | Copyright year                            | `2026`                           |

```bash
# quick pass (GNU sed)
grep -rl '{{' . | xargs sed -i \
  -e 's/{{PROJECT_NAME}}/Acme Widget CLI/g' \
  -e 's/{{PROJECT_SLUG}}/acme-widget-cli/g' \
  -e 's#{{PROJECT_DESCRIPTION}}#A CLI for managing widgets.#g' \
  -e 's/{{OWNER}}/ziti/g' \
  -e 's/{{COPYRIGHT_HOLDER}}/Zach Taffet/g' \
  -e 's/{{CONTACT_EMAIL}}/you@example.com/g' \
  -e 's/{{YEAR}}/2026/g'
```

## 3. Pick a licence

The default is **MIT** (`LICENSE`). If you need something else, replace the
file contents and update the licence line/badge in `README.md`.

## 4. Choose your stack

**Staying on .NET?** Add your solution/projects. The workflows auto-detect a
`*.sln`/`*.csproj` and only then run `dotnet` — so CI is green immediately and
starts doing real work once you commit a project. Set `nullable` and
`TreatWarningsAsErrors` in `Directory.Build.props`, and keep `dotnet format`
clean.

**Not .NET?** Delete the overlay and drop in your own:

```bash
rm .github/workflows/ci.yml .github/workflows/release.yml
# remove the "nuget" block from .github/dependabot.yml
# delete the ".NET / C# overlay" section from CONTRIBUTING.md
# adjust .gitignore and .editorconfig
```

See the sibling `weewx-rtsp-image` repo for a Python overlay (ruff + pytest).

## 5. Turn on the guardrails

- Settings → General → check **Automatically delete head branches**.
- Settings → Branches → protect `main`: require the CI check to pass and the
  branch to be up to date before merging. Add "require a pull request" if more
  than one person will push.
- Settings → Code security → enable Dependabot alerts and
  **private vulnerability reporting** (referenced by `SECURITY.md`).
- Enable **Discussions** if you keep the link in the issue chooser.

## 6. First release

Update `CHANGELOG.md`, commit as `chore(release): 0.1.0`, then:

```bash
git tag v0.1.0 && git push --tags
```

The release workflow builds, tests, packs, and creates the GitHub Release with
notes taken from the changelog. (NuGet publishing is intentionally left out —
see the commented block in `release.yml`.)
