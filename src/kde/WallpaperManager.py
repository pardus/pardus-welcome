import os
import subprocess

folders = ["/usr/share/backgrounds/", "/usr/share/wallpapers/"]
prefixs = ["jpg", "png", "bmp", "jpeg", "svg"]


def getWallpaperList():
    pictures = []
    for path in folders:
        if os.path.exists(path):
            for dirpath, _, files in os.walk(path):
                for file in files:
                    for prefix in prefixs:
                        if file.lower().endswith(prefix):
                            pictures.append(os.path.join(dirpath, file))
                            break
    return pictures


def setWallpaper(wallpaper):
    try:
        subprocess.call(["plasma-apply-wallpaperimage", wallpaper])
    except Exception:
        script = f"""
        var allDesktops = desktops();
        for (var i = 0; i < allDesktops.length; i++) {{
            var d = allDesktops[i];
            d.wallpaperPlugin = "org.kde.image";
            d.currentConfigGroup = Array("Wallpaper", "org.kde.image", "General");
            d.writeConfig("Image", "file://{wallpaper}");
        }}
        """
        subprocess.call([
            "qdbus",
            "org.kde.plasmashell",
            "/PlasmaShell",
            "org.kde.PlasmaShell.evaluateScript",
            script
        ])
