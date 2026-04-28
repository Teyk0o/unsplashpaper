# UnsplashPaper

A lightweight, cross-platform desktop app that automatically sets a beautiful new wallpaper from [Unsplash](https://unsplash.com) every day. Lives quietly in your system tray.

**[Documentation & Download](https://teyk0o.github.io/unsplashpaper/)**

---

## Features

- **Automatic wallpaper refresh** — every hour, every day, or any interval you choose
- **Skip or like** — skip to the next photo instantly, or save your favorites
- **Configurable categories** — nature, space, architecture, or any keyword
- **Photographer credit** — every notification credits the photographer with a link to their profile
- **Start with system** — one toggle, no admin rights needed
- **Minimal footprint** — only one image on disk at any time, no storage bloat
- **Cross-platform** — Windows, macOS, and Linux

## Installation

Download the latest release for your platform from the [releases page](https://github.com/Teyk0o/unsplashpaper/releases/latest):

| Platform | Format |
|----------|--------|
| Windows | `.exe` installer (Inno Setup) |
| macOS | `.dmg` (drag to Applications) |
| Linux | `.deb` (Debian/Ubuntu) or `.AppImage` (universal) |

### Prerequisites

You need a free Unsplash API key. See the [step-by-step guide](https://teyk0o.github.io/unsplashpaper/#api-guide) on the documentation site.

## Usage

On first launch, a setup window asks for your API key, preferred photo category, screen resolution, and refresh interval. After that, UnsplashPaper runs in your system tray.

**Right-click the tray icon** to access all options:

- **Next wallpaper** — fetch a new photo immediately
- **Like this wallpaper** — save to your favorites
- **View on Unsplash** — open the photo on Unsplash
- **Settings** — change category, resolution, or interval
- **Start with system** — toggle auto-start
- **Open likes** — browse your saved favorites

## Development

```bash
# Clone the repo
git clone https://github.com/Teyk0o/unsplashpaper.git
cd unsplashpaper

# Install dependencies
pip install -r requirements.txt

# Run
python unsplashpaper.py

# Build standalone executable
pip install pyinstaller
python build.py
```

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## License

MIT License. See [LICENSE](LICENSE) for details.

---

Photos provided by [Unsplash](https://unsplash.com/?utm_source=unsplashpaper&utm_medium=referral).
