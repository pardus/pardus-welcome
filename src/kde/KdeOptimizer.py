#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Pardus KDE Plasma Sistem Yapılandırıcısı ve Uyumluluk Modülü
# Geliştirici: Tunahan Haksever <tunahanhaksever@github.com>

import os
import subprocess
from pathlib import Path


class KdeOptimizer:
    """KDE Plasma masaüstü ortamındaki yaygın yapılandırma ve uyumluluk sorunlarını çözer."""

    def __init__(self):
        self.home_dir = Path.home()
        self.config_dir = self.home_dir / ".config"
        self.desktop_dirs = [
            self.home_dir / "Masaüstü",
            self.home_dir / "Desktop"
        ]

    def run_all_fixes(self):
        """Tüm sistem yapılandırmalarını sırayla uygular."""
        results = {
            "launchers": self.fix_untrusted_launchers(),
            "desktop_icons": self.ensure_desktop_links(),
            "dolphin_root": self.check_dolphin_root(),
            "deb_mime": self.fix_deb_associations(),
            "gtk_theme": self.synchronize_gtk_themes(),
            "splash": self.stabilize_splash_screen(),
            "wallpaper": self.ensure_default_wallpaper()
        }
        return results

    def fix_untrusted_launchers(self):
        """Masaüstü simgelerindeki 'Güvenilmeyen Başlatıcı' uyarısını kaldırır."""
        count = 0
        try:
            # 1. KIO güvenlik yapılandırmasını ayarla
            kio_config = self.config_dir / "kiorc"
            subprocess.call([
                "kwriteconfig5",
                "--file", str(kio_config),
                "--group", "Executable scripts",
                "--key", "behaviourOnLaunch",
                "alwaysExecute"
            ])

            # 2. Masaüstündeki tüm .desktop dosyalarını çalıştırılabilir ve güvenilir yap
            for desktop_dir in self.desktop_dirs:
                if desktop_dir.exists():
                    for item in desktop_dir.glob("*.desktop"):
                        try:
                            item.chmod(0o755)
                            subprocess.call(["gio", "set", str(item), "metadata::trusted", "true"])
                            count += 1
                        except OSError:
                            pass
            return True
        except Exception:
            return False

    def ensure_desktop_links(self):
        """Masaüstünde Ev Dizini ve Çöp Kutusu kısayollarını oluşturur."""
        try:
            target_dir = None
            for d in self.desktop_dirs:
                if d.exists():
                    target_dir = d
                    break

            if not target_dir:
                target_dir = self.home_dir / "Masaüstü"
                target_dir.mkdir(parents=True, exist_ok=True)

            # Ev Dizini bağlantısı
            home_desktop = target_dir / "home.desktop"
            if not home_desktop.exists():
                content = (
                    "[Desktop Entry]\n"
                    "Type=Link\n"
                    f"URL=file://{self.home_dir}\n"
                    "Icon=user-home\n"
                    "Name=Ev Dizini\n"
                    "Name[tr]=Ev Dizini\n"
                )
                home_desktop.write_text(content, encoding="utf-8")
                home_desktop.chmod(0o755)
                subprocess.call(["gio", "set", str(home_desktop), "metadata::trusted", "true"])

            # Çöp Kutusu bağlantısı
            trash_desktop = target_dir / "trash.desktop"
            if not trash_desktop.exists():
                content = (
                    "[Desktop Entry]\n"
                    "Type=Link\n"
                    "URL=trash:/\n"
                    "Icon=user-trash-full\n"
                    "Name=Çöp Kutusu\n"
                    "Name[tr]=Çöp Kutusu\n"
                )
                trash_desktop.write_text(content, encoding="utf-8")
                trash_desktop.chmod(0o755)
                subprocess.call(["gio", "set", str(trash_desktop), "metadata::trusted", "true"])

            return True
        except Exception:
            return False

    def check_dolphin_root(self):
        """Dolphin dosya yöneticisinde yönetici (root) eylemi için kio-admin kontrolü yapar."""
        try:
            res = subprocess.call(["which", "kio-admin"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return res == 0
        except Exception:
            return False

    def fix_deb_associations(self):
        """.deb paketlerinin varsayılan paket kurucu ile açılmasını sağlar."""
        try:
            mime_types = [
                "application/vnd.debian.binary-package",
                "application/x-deb",
                "application/x-debian-package"
            ]
            desktop_file = "tr.org.pardus.package-installer.desktop"

            # xdg-mime ile varsayılanı ayarla
            for m in mime_types:
                subprocess.call(["xdg-mime", "default", desktop_file, m])

            # mimeapps.list dosyasını güncelle
            mime_file = self.config_dir / "mimeapps.list"
            if mime_file.exists():
                content = mime_file.read_text(encoding="utf-8", errors="ignore")
                if "[Default Applications]" in content:
                    lines = content.splitlines()
                    new_lines = []
                    for line in lines:
                        new_lines.append(line)
                        if line.strip() == "[Default Applications]":
                            for m in mime_types:
                                if m not in content:
                                    new_lines.append(f"{m}={desktop_file};")
                    mime_file.write_text("\n".join(new_lines), encoding="utf-8")
            return True
        except Exception:
            return False

    def synchronize_gtk_themes(self):
        """GTK3, GTK4 ve Flatpak uygulamaları için tema uyumluluğunu sağlar."""
        try:
            theme_name = "Breeze-Dark"
            icon_theme = "breeze-dark"

            # GTK 3.0 yapılandırması
            gtk3_dir = self.config_dir / "gtk-3.0"
            gtk3_dir.mkdir(parents=True, exist_ok=True)
            gtk3_settings = gtk3_dir / "settings.ini"
            gtk3_content = (
                "[Settings]\n"
                f"gtk-theme-name={theme_name}\n"
                f"gtk-icon-theme-name={icon_theme}\n"
                "gtk-font-name=Sans 10\n"
                "gtk-cursor-theme-name=breeze_cursors\n"
                "gtk-application-prefer-dark-theme=1\n"
            )
            gtk3_settings.write_text(gtk3_content, encoding="utf-8")

            # GTK 4.0 yapılandırması
            gtk4_dir = self.config_dir / "gtk-4.0"
            gtk4_dir.mkdir(parents=True, exist_ok=True)
            gtk4_settings = gtk4_dir / "settings.ini"
            gtk4_settings.write_text(gtk3_content, encoding="utf-8")

            # Flatpak tema erişim geçersiz kılmaları
            try:
                subprocess.call([
                    "flatpak", "override",
                    "--filesystem=xdg-config/gtk-3.0:ro",
                    "--filesystem=xdg-config/gtk-4.0:ro"
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

            return True
        except Exception:
            return False

    def stabilize_splash_screen(self):
        """Açılış ekranı (Splash) kilitlenme sorununu çözer."""
        try:
            splash_config = self.config_dir / "ksplashrc"
            subprocess.call([
                "kwriteconfig5",
                "--file", str(splash_config),
                "--group", "KSplash",
                "--key", "Engine",
                "None"
            ])
            return True
        except Exception:
            return False

    def ensure_default_wallpaper(self):
        """Varsayılan Pardus duvar kağıdını Plasma kabuğu üzerinden sabitler."""
        try:
            wallpaper_paths = [
                "/usr/share/backgrounds/pardus23-0.svg",
                "/usr/share/wallpapers/Pardus/contents/images/3840x2160.jpg",
                "/usr/share/desktop-base/active-theme/wallpaper/contents/images/1920x1080.svg"
            ]
            selected = None
            for p in wallpaper_paths:
                if os.path.exists(p):
                    selected = p
                    break

            if selected:
                script = f"""
                var allDesktops = desktops();
                for (var i = 0; i < allDesktops.length; i++) {{
                    var d = allDesktops[i];
                    d.wallpaperPlugin = "org.kde.image";
                    d.currentConfigGroup = Array("Wallpaper", "org.kde.image", "General");
                    d.writeConfig("Image", "file://{selected}");
                }}
                """
                subprocess.call([
                    "qdbus",
                    "org.kde.plasmashell",
                    "/PlasmaShell",
                    "org.kde.PlasmaShell.evaluateScript",
                    script
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False


if __name__ == "__main__":
    optimizer = KdeOptimizer()
    res = optimizer.run_all_fixes()
    print("Pardus KDE Plasma Yapilandirma Sonuclari:")
    for k, v in res.items():
        print(f" - {k}: {'Basarili' if v else 'Gecildi/Hata'}")
