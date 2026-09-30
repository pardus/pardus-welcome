import subprocess


def setScale(scaling_factor):
    try:
        subprocess.call([
            "kwriteconfig5",
            "--file", "kdeglobals",
            "--group", "KScreen",
            "--key", "ScaleFactor",
            str(scaling_factor)
        ])
    except Exception:
        pass


def getScale():
    try:
        val = subprocess.check_output([
            "kreadconfig5",
            "--file", "kdeglobals",
            "--group", "KScreen",
            "--key", "ScaleFactor"
        ]).decode("utf-8").rstrip()
        return float(val) if val else 1.0
    except Exception:
        return 1.0
