import json
import os
import platform
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path

import pystray
import requests
from PIL import Image, ImageDraw

APP_NAME = "UnsplashPaper"
PLATFORM = platform.system()

if getattr(sys, "frozen", False):
    SCRIPT_DIR = Path(sys.executable).parent.resolve()
else:
    SCRIPT_DIR = Path(__file__).parent.resolve()

if PLATFORM == "Linux" and getattr(sys, "frozen", False):
    _config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    _data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    CONFIG_DIR = _config_home / "unsplashpaper"
    DATA_DIR = _data_home / "unsplashpaper"
else:
    CONFIG_DIR = SCRIPT_DIR
    DATA_DIR = SCRIPT_DIR / "data"

CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = CONFIG_DIR / "config.json"
CURRENT_WALLPAPER = DATA_DIR / "current.jpg"
LIKES_PATH = DATA_DIR / "likes.json"
UNSPLASH_API = "https://api.unsplash.com"

current_photo = None
icon = None


# ── Config ───��─────────��────────────────────────────────

def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def needs_setup():
    if not CONFIG_PATH.exists():
        return True
    try:
        cfg = load_config()
        key = cfg.get("unsplash_access_key", "")
        return not key or key == "YOUR_ACCESS_KEY"
    except Exception:
        return True


# ── Likes ─────���──────────────────────────���──────────────

def load_likes():
    if LIKES_PATH.exists():
        with open(LIKES_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_likes(likes):
    with open(LIKES_PATH, "w", encoding="utf-8") as f:
        json.dump(likes, f, indent=2, ensure_ascii=False)


# ── Tray icon ──────────────────────────────────────────

def make_tray_icon():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([4, 4, 60, 60], radius=12, fill="white", outline=(80, 80, 80), width=2)
    draw.rounded_rectangle([14, 18, 50, 46], radius=6, fill=(60, 60, 60))
    draw.polygon([(18, 42), (28, 28), (38, 38), (44, 30), (50, 42)], fill=(100, 180, 100))
    draw.ellipse([38, 20, 48, 30], fill=(255, 220, 80))
    return img


# ── Unsplash API ───────────────────────────────────────

def fetch_random_photo(config):
    w, h = config["resolution"].split("x")
    resp = requests.get(
        f"{UNSPLASH_API}/photos/random",
        params={"query": config["category"], "orientation": "landscape"},
        headers={"Authorization": f"Client-ID {config['unsplash_access_key']}"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "id": data["id"],
        "url": data["urls"]["raw"] + f"&w={w}&h={h}&fit=crop&auto=format&q=90",
        "photographer": data["user"]["name"],
        "photographer_url": data["user"]["links"]["html"],
        "unsplash_url": data["links"]["html"],
        "download_location": data["links"]["download_location"],
    }


def trigger_download_event(config, photo):
    try:
        requests.get(
            photo["download_location"],
            headers={"Authorization": f"Client-ID {config['unsplash_access_key']}"},
            timeout=10,
        )
    except Exception:
        pass


def download_image(url):
    resp = requests.get(url, timeout=30, stream=True)
    resp.raise_for_status()
    with open(CURRENT_WALLPAPER, "wb") as f:
        for chunk in resp.iter_content(8192):
            f.write(chunk)


# ── Wallpaper (cross-platform) ─────────────────────────

def set_wallpaper():
    path = str(CURRENT_WALLPAPER.resolve())
    if PLATFORM == "Windows":
        import ctypes
        SPI_SETDESKWALLPAPER = 0x0014
        SPIF_UPDATEINIFILE = 0x01
        SPIF_SENDCHANGE = 0x02
        ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER, 0, path, SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
        )
    elif PLATFORM == "Darwin":
        script = f'''
        tell application "System Events"
            tell every desktop
                set picture to POSIX file "{path}"
            end tell
        end tell
        '''
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
    else:
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        if "gnome" in desktop or "unity" in desktop or "cinnamon" in desktop:
            subprocess.run([
                "gsettings", "set", "org.gnome.desktop.background", "picture-uri",
                f"file://{path}"
            ], check=True, capture_output=True)
            subprocess.run([
                "gsettings", "set", "org.gnome.desktop.background", "picture-uri-dark",
                f"file://{path}"
            ], capture_output=True)
        elif "kde" in desktop or "plasma" in desktop:
            script = f'''
            var allDesktops = desktops();
            for (var i = 0; i < allDesktops.length; i++) {{
                var d = allDesktops[i];
                d.wallpaperPlugin = "org.kde.image";
                d.currentConfigGroup = Array("Wallpaper", "org.kde.image", "General");
                d.writeConfig("Image", "file://{path}");
            }}
            '''
            subprocess.run([
                "qdbus", "org.kde.plasmashell", "/PlasmaShell",
                "org.kde.PlasmaShell.evaluateScript", script
            ], capture_output=True)
        elif "xfce" in desktop:
            result = subprocess.run(
                ["xfconf-query", "-c", "xfce4-desktop", "-l"],
                capture_output=True, text=True
            )
            for line in result.stdout.splitlines():
                if line.endswith("/last-image"):
                    subprocess.run([
                        "xfconf-query", "-c", "xfce4-desktop", "-p", line, "-s", path
                    ], capture_output=True)
        else:
            if _command_exists("feh"):
                subprocess.run(["feh", "--bg-fill", path], capture_output=True)
            elif _command_exists("nitrogen"):
                subprocess.run(["nitrogen", "--set-zoom-fill", path], capture_output=True)


def _command_exists(cmd):
    try:
        subprocess.run(["which", cmd], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def refresh_wallpaper(notify=True):
    global current_photo
    try:
        config = load_config()
        photo = fetch_random_photo(config)
        download_image(photo["url"])
        trigger_download_event(config, photo)
        set_wallpaper()
        current_photo = photo
        if icon and notify:
            icon.notify(f"Photo by {photo['photographer']}", APP_NAME)
        update_menu()
    except Exception as e:
        if icon:
            icon.notify(f"Error: {e}", APP_NAME)


# ── Autostart (cross-platform) ────────────────────────

def _get_exe_command():
    if getattr(sys, "frozen", False):
        return str(Path(sys.executable).resolve())
    return f'{sys.executable} {Path(__file__).resolve()}'


def _get_autostart_label():
    if PLATFORM == "Darwin":
        return "Start at login"
    return "Start with system"


def _macos_plist_path():
    return Path.home() / "Library" / "LaunchAgents" / "com.unsplashpaper.app.plist"


def _linux_autostart_path():
    return Path.home() / ".config" / "autostart" / "unsplashpaper.desktop"


def is_autostart_enabled():
    if PLATFORM == "Windows":
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run",
                                 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False
    elif PLATFORM == "Darwin":
        return _macos_plist_path().exists()
    else:
        return _linux_autostart_path().exists()


def toggle_autostart(_=None):
    try:
        if is_autostart_enabled():
            _disable_autostart()
            if icon:
                icon.notify("Auto-start disabled", APP_NAME)
        else:
            _enable_autostart()
            if icon:
                icon.notify("Auto-start enabled", APP_NAME)
        update_menu()
    except Exception as e:
        if icon:
            icon.notify(f"Error: {e}", APP_NAME)


def _enable_autostart():
    exe = _get_exe_command()
    if PLATFORM == "Windows":
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exe}"' if getattr(sys, "frozen", False) else exe)
        winreg.CloseKey(key)
    elif PLATFORM == "Darwin":
        plist = _macos_plist_path()
        plist.parent.mkdir(parents=True, exist_ok=True)
        parts = exe.split(" ", 1)
        program = parts[0]
        args_xml = ""
        if len(parts) > 1:
            args_xml = f"\n            <string>{parts[1]}</string>"
        plist.write_text(f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.unsplashpaper.app</string>
    <key>ProgramArguments</key>
    <array>
        <string>{program}</string>{args_xml}
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
''', encoding="utf-8")
    else:
        desktop_file = _linux_autostart_path()
        desktop_file.parent.mkdir(parents=True, exist_ok=True)
        desktop_file.write_text(f'''[Desktop Entry]
Type=Application
Name=UnsplashPaper
Exec={exe}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
''', encoding="utf-8")


def _disable_autostart():
    if PLATFORM == "Windows":
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
    elif PLATFORM == "Darwin":
        p = _macos_plist_path()
        if p.exists():
            p.unlink()
    else:
        p = _linux_autostart_path()
        if p.exists():
            p.unlink()


# ── Menu actions ───────────���───────────────────────────

def skip_wallpaper(_=None):
    threading.Thread(target=refresh_wallpaper, daemon=True).start()


def like_current(_=None):
    if not current_photo:
        return
    likes = load_likes()
    if any(l["id"] == current_photo["id"] for l in likes):
        if icon:
            icon.notify("Already liked!", APP_NAME)
        return
    likes.append({
        "id": current_photo["id"],
        "photographer": current_photo["photographer"],
        "photographer_url": current_photo["photographer_url"],
        "unsplash_url": current_photo["unsplash_url"],
        "liked_at": datetime.now().isoformat(),
    })
    save_likes(likes)
    if icon:
        icon.notify(f"Liked! Photo by {current_photo['photographer']}", APP_NAME)


def open_current_on_unsplash(_=None):
    if current_photo:
        webbrowser.open(current_photo["unsplash_url"] + "?utm_source=unsplashpaper&utm_medium=referral")


def open_photographer_page(_=None):
    if current_photo:
        webbrowser.open(current_photo["photographer_url"] + "?utm_source=unsplashpaper&utm_medium=referral")


def open_likes_file(_=None):
    if not LIKES_PATH.exists():
        if icon:
            icon.notify("No likes yet!", APP_NAME)
        return
    if PLATFORM == "Windows":
        os.startfile(str(LIKES_PATH))
    elif PLATFORM == "Darwin":
        subprocess.run(["open", str(LIKES_PATH)], capture_output=True)
    else:
        subprocess.run(["xdg-open", str(LIKES_PATH)], capture_output=True)


def open_settings_window(_=None):
    from gui import open_settings
    open_settings(CONFIG_PATH, on_save_callback=lambda: skip_wallpaper())


def quit_app(_=None):
    if icon:
        icon.stop()


# ── Tray menu ──────────────��──────────────────────────

def get_photographer_label(_=None):
    if current_photo:
        return f"Photo by {current_photo['photographer']}"
    return "Loading..."


def build_menu():
    return pystray.Menu(
        pystray.MenuItem(get_photographer_label, open_photographer_page),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Next wallpaper", skip_wallpaper),
        pystray.MenuItem("Like this wallpaper", like_current),
        pystray.MenuItem("View on Unsplash", open_current_on_unsplash),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Settings...", open_settings_window),
        pystray.MenuItem(_get_autostart_label(), toggle_autostart,
                         checked=lambda item: is_autostart_enabled()),
        pystray.MenuItem("Open likes", open_likes_file),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", quit_app),
    )


def update_menu():
    if icon:
        icon.menu = build_menu()


# ��─ Auto-refresh loop ─────────────────────────────────

def auto_refresh_loop():
    refresh_wallpaper(notify=False)
    while True:
        try:
            config = load_config()
            interval = config.get("interval_hours", 24) * 3600
        except Exception:
            interval = 86400
        time.sleep(interval)
        refresh_wallpaper()


# ── Entry point ─────────────────────────────���──────────

def main():
    global icon

    if needs_setup():
        from gui import run_wizard
        if not run_wizard(CONFIG_PATH):
            sys.exit(0)

    DATA_DIR.mkdir(exist_ok=True)

    icon = pystray.Icon(APP_NAME, make_tray_icon(), APP_NAME, menu=build_menu())

    threading.Thread(target=auto_refresh_loop, daemon=True).start()

    icon.run()


if __name__ == "__main__":
    main()
