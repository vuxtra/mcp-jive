# 🚀 MCP Jive Release Management

This document provides a quick reference for the automated release system implemented for MCP Jive.

## 🎯 Quick Start

### Automatic Releases (Recommended)
Simply push commits to `main` branch with conventional commit messages:

```bash
# Patch release (1.0.0 → 1.0.1)
git commit -m "fix: resolve database connection timeout"

# Minor release (1.0.0 → 1.1.0)
git commit -m "feat: add real-time collaboration"

# Major release (1.0.0 → 2.0.0)
git commit -m "feat!: redesign API structure

BREAKING CHANGE: All endpoints now use /api/v2/ prefix"
```

### Manual Releases
1. Go to **GitHub Actions** → **Manual Version Bump**
2. Select version type: `patch`, `minor`, `major`, or `prerelease`
3. Optionally enter custom version number
4. Click **Run workflow**

## 📋 Release Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `release.yml` | Push to `main` | Automatic semantic releases |
| `version-bump.yml` | Manual dispatch | Manual version control |
| `pr-validation.yml` | Pull requests | Validate commits & preview releases |

## 🔄 Release Process

1. **Commit Analysis** - Scans commits for conventional format
2. **Version Calculation** - Determines next version using SemVer
3. **Changelog Generation** - Updates CHANGELOG.md automatically
4. **Package Building** - Creates Python wheel and source dist
5. **GitHub Release** - Creates release with notes and assets
6. **Tagging** - Creates Git tags for version tracking

## 📊 Current Status

- **Current Version**: `1.0.0` (from setup.py)
- **Commit Format**: ✅ 10/10 recent commits follow conventional format
- **Next Release**: `1.1.0` (minor - new features detected)
- **Workflows**: ✅ 4 GitHub Actions workflows configured

## 🧪 Testing

Test the release system locally:
```bash
./scripts/test-release.sh
```

## 📚 Documentation

- **[Complete Guide](docs/RELEASE_PROCESS.md)** - Detailed release process documentation
- **[Conventional Commits](https://www.conventionalcommits.org/)** - Commit message format
- **[Semantic Versioning](https://semver.org/)** - Version numbering standard

## 🎉 Features

✅ **Semantic Versioning** - Automatic version bumping based on changes
✅ **Conventional Commits** - Standardized commit message format
✅ **Automatic Changelog** - Generated from commit messages
✅ **GitHub Releases** - Complete release notes and assets
✅ **PR Validation** - Validates commits and shows release preview
✅ **Manual Override** - Manual version bumping when needed
✅ **Asset Management** - Python packages and Docker images
✅ **Rollback Safety** - Git tags and release history

## 🚀 Ready for Production!

The release system is fully configured and ready to use. The next push to `main` with a `feat:` or `fix:` commit will trigger an automatic release.