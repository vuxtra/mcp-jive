# 🚀 Release Process Documentation

This document outlines the automated release process for MCP Jive using semantic versioning and GitHub Actions.

## Overview

MCP Jive uses an automated release system based on:
- **Semantic Versioning** (SemVer 2.0.0)
- **Conventional Commits** for determining release types
- **GitHub Actions** for automation
- **Automatic changelog generation**

## Release Types

### Automatic Releases (Recommended)

Releases are automatically triggered when commits are pushed to the `main` branch, based on commit message conventions:

| Commit Type | Release Type | Version Bump | Example |
|-------------|--------------|--------------|---------|
| `fix:` | Patch | 1.0.0 → 1.0.1 | `fix: resolve memory leak in websocket` |
| `feat:` | Minor | 1.0.0 → 1.1.0 | `feat: add user authentication` |
| `BREAKING CHANGE:` or `!:` | Major | 1.0.0 → 2.0.0 | `feat!: redesign API structure` |
| Other (`docs:`, `chore:`, etc.) | None | No release | `docs: update README` |

### Manual Releases

Use the **"Manual Version Bump"** workflow for:
- Emergency releases
- Custom version numbers
- Prerelease versions
- Override automatic detection

## Conventional Commits

### Format
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Valid Types
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `ci`: CI/CD changes
- `build`: Build system changes

### Examples
```bash
# Patch release (1.0.0 → 1.0.1)
git commit -m "fix: resolve database connection timeout"

# Minor release (1.0.0 → 1.1.0)
git commit -m "feat: add real-time collaboration features"

# Major release (1.0.0 → 2.0.0)
git commit -m "feat!: redesign API with breaking changes

BREAKING CHANGE: API endpoints have been restructured"

# No release
git commit -m "docs: update API documentation"
git commit -m "chore: update dependencies"
```

## Workflows

### 1. Automatic Release (`release.yml`)

**Triggers:**
- Push to `main` branch
- Manual dispatch with release type override

**Process:**
1. Analyzes commits since last release
2. Determines release type using conventional commits
3. Calculates new version number
4. Updates `setup.py` version
5. Generates/updates `CHANGELOG.md`
6. Creates Git tag
7. Builds Python package
8. Creates GitHub release with assets
9. Runs tests and validations

### 2. Manual Version Bump (`version-bump.yml`)

**Triggers:**
- Manual workflow dispatch only

**Options:**
- `patch`, `minor`, `major`, `prerelease`
- Custom version number
- Create GitHub release (optional)

### 3. PR Validation (`pr-validation.yml`)

**Triggers:**
- Pull request to `main` or `develop`

**Validates:**
- Conventional commit format
- Code quality and tests
- Provides release preview

## Usage Examples

### Standard Development Flow

```bash
# Feature development
git checkout -b feature/user-auth
git commit -m "feat: add JWT authentication"
git commit -m "test: add authentication tests"
git commit -m "docs: update auth documentation"

# Create PR - workflow validates commits and shows release preview
gh pr create --title "Add user authentication" --body "Implements JWT-based auth"

# After PR approval and merge to main
# → Automatic minor release (e.g., 1.0.0 → 1.1.0)
```

### Hotfix Flow

```bash
# Hotfix
git checkout -b hotfix/memory-leak
git commit -m "fix: resolve memory leak in websocket connections"

# Create PR and merge
# → Automatic patch release (e.g., 1.1.0 → 1.1.1)
```

### Breaking Change Flow

```bash
# Breaking change
git checkout -b feature/api-redesign
git commit -m "feat!: redesign API structure

BREAKING CHANGE: All endpoints now use /api/v2/ prefix"

# Create PR and merge
# → Automatic major release (e.g., 1.1.1 → 2.0.0)
```

### Manual Release

1. Go to **Actions** → **Manual Version Bump**
2. Click **"Run workflow"**
3. Select version type or enter custom version
4. Choose whether to create GitHub release
5. Click **"Run workflow"**

## Release Artifacts

Each release includes:

### GitHub Release
- **Release notes** with changelog
- **Installation instructions**
- **Links to documentation**

### Python Package
- Built wheel (`.whl`) file
- Source distribution (`.tar.gz`)
- Attached to GitHub release

### Docker Image (if Dockerfile exists)
- Tagged with version number
- Tagged as `latest`

## Changelog Format

The changelog follows [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
# Changelog

## [1.2.0] - 2024-01-15

### Added
✨ feat: add real-time collaboration features
✨ feat: implement task dependencies

### Fixed
🐛 fix: resolve database connection timeout
🐛 fix: fix memory leak in websocket

### Changed
🔧 refactor: improve error handling
🔧 perf: optimize database queries
```

## Version Management

### Current Version
```bash
# Check current version
grep version setup.py

# Or using Python
python -c "import setup; print(setup.version)"
```

### Version History
```bash
# List all tags
git tag -l

# Show latest releases
gh release list
```

## Troubleshooting

### Release Failed
1. Check GitHub Actions logs
2. Verify commit message format
3. Ensure no conflicting tags exist
4. Check repository permissions

### Wrong Version Released
1. Use manual workflow to correct version
2. Or create hotfix with proper version

### Missing Changelog Entry
1. Manually edit `CHANGELOG.md`
2. Commit with `docs: update changelog`

## Best Practices

### Commit Messages
- Use clear, descriptive messages
- Follow conventional commit format
- Include scope when helpful: `feat(auth): add OAuth support`
- Reference issues: `fix: resolve database timeout (#123)`

### Release Planning
- Group related changes into single releases
- Test thoroughly before merging to main
- Use feature branches for development
- Review PRs for proper commit format

### Version Strategy
- **Patch**: Bug fixes, security updates
- **Minor**: New features, enhancements
- **Major**: Breaking changes, API redesign
- **Prerelease**: Beta versions, testing

## Monitoring

### GitHub Actions
- Monitor workflow status in **Actions** tab
- Check failure notifications
- Review release summaries

### Release Metrics
- Track release frequency
- Monitor adoption of new versions
- Collect user feedback

## Security

### Secrets Required
- `GITHUB_TOKEN`: Automatic (provided by GitHub)

### Permissions
- **Contents**: Write (for tags and releases)
- **Pull Requests**: Write (for comments)
- **Issues**: Write (for notifications)

## Support

For questions about the release process:
1. Check this documentation
2. Review GitHub Actions logs
3. Create an issue with `release` label
4. Contact the development team