import os
import pwd
import subprocess

USER = pwd.getpwuid(os.getuid()).pw_name if hasattr(os, "getuid") else ""

themePath = ["/usr/share/themes/", f"/home/{USER}/.themes/"]
plasmaThemes = ["/usr/share/plasma/desktoptheme/", f"/home/{USER}/.local/share/plasma/desktoptheme/"]


def getThemeList():
    themes = []
    windowThemes = []

    for path in themePath:
        try:
            files = os.scandir(path)
            for file in files:
                if file.is_dir():
                    themes.append(file.name)
        except FileNotFoundError:
            pass

    themes.sort()
    return [themes, windowThemes]


def setTheme(theme):
    subprocess.call([
        "kwriteconfig5",
        "--file", "kdeglobals",
        "--group", "General",
        "--key", "ColorScheme",
        theme
    ])


def setIconTheme(theme):
    subprocess.call([
        "kwriteconfig5",
        "--file", "kdeglobals",
        "--group", "Icons",
        "--key", "Theme",
        theme
    ])


def getTheme():
    try:
        return subprocess.check_output([
            "kreadconfig5",
            "--file", "kdeglobals",
            "--group", "General",
            "--key", "ColorScheme"
        ]).decode("utf-8").rstrip()
    except Exception:
        return ""


def getIconTheme(theme=None):
    try:
        return subprocess.check_output([
            "kreadconfig5",
            "--file", "kdeglobals",
            "--group", "Icons",
            "--key", "Theme"
        ]).decode("utf-8").rstrip()
    except Exception:
        return ""
