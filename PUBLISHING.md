# Publishing To PyPI

This package is set up for GitHub Actions Trusted Publishing.

## Preconditions

- The package name in `pyproject.toml` must be the exact name you want on PyPI.
- The repository must have a GitHub Actions workflow at `.github/workflows/release.yml`.
- `codex` authentication is not managed here; users authenticate with Codex CLI separately.

## One-Time Setup

### 1. Create PyPI and TestPyPI accounts

- PyPI: `https://pypi.org/account/register/`
- TestPyPI: `https://test.pypi.org/account/register/`

### 2. Configure Trusted Publishers

For a brand-new project, use a pending publisher on both PyPI and TestPyPI.

Configure GitHub Actions as the publisher with:

- Owner: your GitHub org or username
- Repository: this repository name
- Workflow: `.github/workflows/release.yml`
- Environment: `pypi` for PyPI
- Environment: `testpypi` for TestPyPI
- Project name: `project-agent-framework`

For an existing project, add the publisher from the project's Publishing settings instead of creating a pending publisher.

### 3. Create GitHub environments

In GitHub repository settings, create:

- `pypi`
- `testpypi`

Optional but recommended:

- require manual approval for the `pypi` environment
- restrict which branches or tags can deploy

## Local Validation

Run before tagging a release:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
python -m pytest -q
python -m build
python -m twine check dist/*
```

## TestPyPI Release

To test the publishing pipeline without creating a real PyPI release:

1. Push your branch to GitHub.
2. Run the `Release` workflow manually.
3. Choose `testpypi` as the `repository` input.

If the publish succeeds, verify the package on TestPyPI and install it from there if needed.

## PyPI Release

To publish a real release:

1. Bump the version in `pyproject.toml`.
2. Commit the version change.
3. Create a Git tag matching the release, for example:

```bash
git tag v0.1.0
git push origin v0.1.0
```

4. Create a GitHub Release from that tag, or publish one if your workflow is tag-driven from releases.
5. GitHub Actions will build the distributions and publish to PyPI using Trusted Publishing.

## Common Failure Modes

- Package name mismatch:
  `pyproject.toml` name must match the pending publisher project name exactly.
- Publisher mismatch:
  GitHub owner, repository, workflow path, and environment must match PyPI exactly.
- Missing `id-token: write`:
  Trusted Publishing will fail if the publish job does not have OIDC permission.
- README rendering or metadata issues:
  run `python -m twine check dist/*` locally before releasing.

## Notes

- The release workflow publishes attestations automatically through `pypa/gh-action-pypi-publish` when using Trusted Publishing.
- The package metadata now declares `GPL-3.0-or-later` and includes a root `LICENSE` file, which is the expected PyPI-friendly setup for an open-source release.
