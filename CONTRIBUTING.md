# Contributing to UnsplashPaper

Thanks for your interest in contributing. This document outlines the process for submitting changes.

## Getting started

1. Fork the repository
2. Create a feature branch from `main`: `git checkout -b feat/your-feature`
3. Install dependencies: `pip install -r requirements.txt`
4. Make your changes
5. Test on your platform
6. Commit using [Conventional Commits](https://www.conventionalcommits.org/) format
7. Push and open a pull request

## Commit messages

This project follows [Conventional Commits](https://www.conventionalcommits.org/). Every commit message must follow this format:

```
type(scope): short description

Optional longer description.
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
- `feat: add wallpaper history navigation`
- `fix(linux): handle missing gsettings on KDE`
- `docs: update API key guide`

## Pull requests

- Keep PRs focused on a single change
- Update documentation if your change affects user-facing behavior
- Ensure the app runs without errors on at least one platform
- Fill in the PR template when opening your pull request

## Code style

- Python 3.10+
- No strict linter enforced, but keep it clean and readable
- No comments unless explaining a non-obvious "why"
- Prefer simple, direct code over abstractions

## Reporting bugs

Use the [bug report template](https://github.com/Teyk0o/unsplashpaper/issues/new?template=bug_report.md) and include:
- Your OS and version
- Steps to reproduce
- Expected vs actual behavior

## Feature requests

Use the [feature request template](https://github.com/Teyk0o/unsplashpaper/issues/new?template=feature_request.md). Describe the problem you want to solve, not just the solution you have in mind.
