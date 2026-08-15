# GitHub Actions Workflows

This project includes three automated workflows for CI/CD, testing, and documentation.

## Workflows

### 1. `test.yml` — Tests & Quality (Primary CI)
**Triggers:** Push to `main`/`develop` or PR

**Jobs:**
- **Test & Lint** (runs on ubuntu-latest + macos-latest with Python 3.12)
  - Install UV + dependencies
  - Run pytest with coverage reporting
  - Upload coverage to Codecov
  - Run Black formatting checks
  - Run flake8 linting

- **Security Checks**
  - Scan for secrets with TruffleHog
  - Non-blocking (continue on error)

**Key Outputs:**
- ✅ All tests passing
- ✅ Code coverage >80%
- ✅ Black formatting compliant
- ✅ Flake8 style compliant
- 🔍 No secrets committed

### 2. `docs.yml` — Documentation
**Triggers:** Push to `main` or PR

**Jobs:**
- **Build Documentation**
  - Install UV + dependencies
  - Generate API documentation stubs
  - Create docs artifact for preview

- **Preview Documentation** (on PR)
  - Comment on PR with docs preview link
  - 5-day artifact retention

**Key Outputs:**
- 📚 Documentation preview available
- ✅ PR comments with preview links

### 3. `docs-publish.yml` — Docs & Pages (GitHub Pages)
**Triggers:** Push to `main` or PR

**Jobs:**
- **Build Documentation**
  - Reuses workflow from docs.yml
  - Generates docs from README and copilot-instructions

- **Publish to GitHub Pages** (main only)
  - Deploys documentation to GitHub Pages
  - Updates page_url on successful deploy
  - Requires: `pages: write` + `id-token: write`

**Key Outputs:**
- 📖 Automatic documentation deployment
- 🔗 GitHub Pages URL available

## Configuration

### Required Repository Settings

1. **GitHub Pages** (under Settings > Pages)
   - Source: Deploy from a branch
   - Branch: `gh-pages` (auto-created by deploy action)
   - Path: `/ (root)`

2. **Branch Protection** (recommended)
   - Require status checks to pass:
     - `Tests & Quality / Test & Lint (ubuntu-latest)`
     - `Tests & Quality / Test & Lint (macos-latest)`
     - `Tests & Quality / Security Checks`

3. **Codecov Integration** (optional)
   - Install Codecov app: https://github.com/apps/codecov
   - Automatic coverage tracking on PRs

## Local Testing

Test workflows locally with [act](https://github.com/nektos/act):

```bash
# Install act
brew install act

# Test the main CI workflow
act --job test

# Test docs workflow
act --job build-docs

# Test specific event
act -e pull_request
```

## Adapted From

Original workflows from another repository that used `great-docs`. Adapted for:
- **UV package manager** (instead of Poetry)
- **Python 3.12** (instead of 3.14)
- **pytest** (instead of great-docs)
- **Codecov** integration for coverage tracking
- **TruffleHog** for secret scanning

## Future Enhancements

- [ ] Add Matrix strategy for Python 3.11, 3.12, 3.13
- [ ] Add benchmarking workflow for performance tracking
- [ ] Add dependency vulnerability scanning (Dependabot)
- [ ] Add type checking (mypy) workflow
- [ ] Generate & publish API documentation with Sphinx/MkDocs

## Troubleshooting

### Workflow not triggering?
- Check branch name matches trigger conditions (main/develop)
- Verify `.github/workflows/` files are on the branch

### Coverage not uploading?
- Codecov may not be configured; check `fail_ci_if_error: false`
- Coverage report is still generated locally

### GitHub Pages not deploying?
- Enable Pages in repository settings
- Verify workflow has `pages: write` + `id-token: write` permissions
- Check Actions tab for deployment status
