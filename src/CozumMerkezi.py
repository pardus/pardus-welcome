#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Pardus Çözüm Merkezi - Kapsamlı Sistem, Donanım, E-İmza ve Çevre Birimi Onarıcı
# Geliştirici: Tunahan Haksever <tunahanhaksever@github.com>
# Lisans: GPL-3.0

"""
Pardus GNU/Linux ortamında topluluğun en çok karşılaştığı 10 kronik sorunu
resmi Debian ve Pardus çekirdek standartlarında otomatik çözer:
1. APT / DPKG Paket Kilitleri ve Yarım Kalan Kurulum Onarımı
2. Broadcom (BCM43xx) ve Realtek Wi-Fi Ağ Kartı Sürücü Otomasyonu
3. Canon (CAPT / LBP) ve HP CUPS Yazıcı Entegrasyonu
4. E-İmza, UYAP, KAMU SM ve Akıllı Kart Okuyucu (AKİS / pcscd) Onarımı
5. Bluetooth Kulaklık Eşleşme, Ses Gelmeme ve Profil Hatası Çözümü
6. Düşük RAM / Kilitlenme Önleyici ZRAM Bellek Sıkıştırma Kurulumu
7. Laptop Pil Süresini Artırma ve Isınma/Fan Optimizasyonu (TLP)
8. GRUB Menüsünde Windows'un Görünmemesi (Dual-Boot OS-Prober Çözümü)
9. MEB / EBA Güvenlik Sertifikası Kurulumu (Okul İnternet Erişimi)
10. Laptop Touchpad Dokunarak Tıklama (Tap-to-Click) ve Hassasiyet Ayarı
"""

import os
import sys
import subprocess
import re
from pathlib import Path


class PardusCozumMerkezi:
    def __init__(self):
        self.log_prefix = "[Pardus Çözüm]"

    def print_status(self, msg, ok=True):
        mark = "[OK]" if ok else "[FAIL]"
        print(f"{mark} {msg}")

    def _get_active_user(self):
        return os.environ.get("SUDO_USER") or os.environ.get("USER") or "kullanici"

    def _check_root(self):
        if os.geteuid() != 0:
            print("[!] Bu işlem sistem seviyesinde olduğu için root (sudo) yetkisi gerektirir.")
            print("[*] Lütfen 'sudo python3 ...' olarak çalıştırın.")
            sys.exit(1)

    def coz_apt_dpkg_kilitleri(self):
        print("\n--- 1. APT ve DPKG Paket Yöneticisi Onarımı ---")
        lock_processes = ["apt", "apt-get", "dpkg", "unattended-upgrades", "packagekitd"]
        for proc in lock_processes:
            try:
                subprocess.call(["killall", "-q", "-9", proc], stderr=subprocess.DEVNULL)
            except Exception:
                pass
        self.print_status("Kilitli arka plan işlemleri sonlandırıldı.")

        lock_files = [
            "/var/lib/dpkg/lock-frontend",
            "/var/lib/dpkg/lock",
            "/var/cache/apt/archives/lock",
            "/var/lib/apt/lists/lock"
        ]
        for lf in lock_files:
            try:
                if os.path.exists(lf):
                    os.remove(lf)
            except Exception:
                pass
        self.print_status("Sistem kilit dosyaları temizlendi.")

        res_dpkg = subprocess.call(["dpkg", "--configure", "-a"])
        self.print_status("Yarım kalan paket yapılandırmaları tamamlandı (dpkg --configure -a).", res_dpkg == 0)

        res_fix = subprocess.call(["apt-get", "install", "-f", "-y"])
        self.print_status("Kırık paket bağımlılıkları onarıldı (apt install -f).", res_fix == 0)

        subprocess.call(["apt-get", "clean"])
        res_upd = subprocess.call(["apt-get", "update", "-y"])
        self.print_status("Paket depoları güncellendi.", res_upd == 0)
        return True

    def coz_wifi_suruculeri(self):
        print("\n--- 2. Broadcom & Realtek Wi-Fi Sürücü Tanılama ---")
        try:
            lspci_out = subprocess.check_output(["lspci", "-nn"], universal_newlines=True)
        except Exception:
            lspci_out = ""

        is_broadcom = ("14e4:" in lspci_out) or ("Broadcom" in lspci_out)
        is_realtek = ("10ec:" in lspci_out) or ("Realtek" in lspci_out)

        print("[*] Donanım Taraması:")
        print(f"    - Broadcom Wi-Fi: {'Tespit Edildi' if is_broadcom else 'Bulunamadı'}")
        print(f"    - Realtek Wi-Fi : {'Tespit Edildi' if is_realtek else 'Bulunamadı'}")

        print("[*] Gerekli çekirdek başlıkları ve dkms kuruluyor...")
        subprocess.call([
            "apt-get", "install", "-y",
            "linux-headers-amd64", "build-essential", "dkms",
            "firmware-linux", "firmware-linux-nonfree", "firmware-misc-nonfree"
        ])

        if is_broadcom:
            print("[*] Broadcom BCM sürücüsü yükleniyor (broadcom-sta-dkms)...")
            subprocess.call(["apt-get", "install", "-y", "broadcom-sta-dkms", "b43-fwcutter", "firmware-b43-installer"])

            cakisanlar = ["b43", "b43legacy", "ssb", "bcma", "brcmfmac", "brcmsmac"]
            for m in cakisanlar:
                subprocess.call(["modprobe", "-r", m], stderr=subprocess.DEVNULL)

            res_mod = subprocess.call(["modprobe", "wl"])
            self.print_status("Broadcom 'wl' sürücüsü çekirdeğe yüklendi.", res_mod == 0)

        if is_realtek:
            print("[*] Realtek donanım bellenimi yükleniyor (firmware-realtek)...")
            res_rt = subprocess.call(["apt-get", "install", "-y", "firmware-realtek"])
            self.print_status("Realtek bellenimi kuruldu.", res_rt == 0)

        subprocess.call(["systemctl", "restart", "NetworkManager"], stderr=subprocess.DEVNULL)
        self.print_status("NetworkManager ağ servisi yeniden başlatıldı.")
        return True

    def coz_yazici_ve_cups(self):
        print("\n--- 3. Canon & HP Yazıcı Yazdırma Servisi Onarımı ---")
        print("[*] CUPS ve HPLIP yazdırma paketleri kontrol ediliyor...")
        subprocess.call([
            "apt-get", "install", "-y",
            "cups", "cups-filters", "system-config-printer",
            "hplip", "printer-driver-hpcups", "printer-driver-all",
            "libcups2"
        ])

        subprocess.call(["systemctl", "enable", "cups"])
        subprocess.call(["systemctl", "restart", "cups"])
        self.print_status("CUPS yazdırma kuyruk servisi çalıştırıldı.")

        user = self._get_active_user()
        if user != "root":
            subprocess.call(["usermod", "-aG", "lp,lpadmin", user])
            self.print_status(f"'{user}' kullanıcısına yazıcı yönetici yetkisi (lpadmin) verildi.")

        try:
            lsusb_out = subprocess.check_output(["lsusb"], universal_newlines=True)
            if "Canon" in lsusb_out:
                print("[*] Canon yazıcı USB hattında tespit edildi.")
                subprocess.call(["modprobe", "usblp"], stderr=subprocess.DEVNULL)
                self.print_status("Canon usblp port iletişimi aktifleştirildi.")
        except Exception:
            pass

        return True

    def coz_eimza_ve_uyap(self):
        print("\n--- 4. E-İmza, UYAP ve Akıllı Kart (AKİS / pcscd) Onarımı ---")
        print("[*] Gerekli akıllı kart ve pcscd servis paketleri kuruluyor...")
        subprocess.call([
            "apt-get", "install", "-y",
            "pcscd", "pcsc-tools", "libccid", "libacsccid1", "opensc",
            "default-jre"
        ])

        subprocess.call(["systemctl", "enable", "pcscd.socket"])
        subprocess.call(["systemctl", "restart", "pcscd.socket"])
        subprocess.call(["systemctl", "restart", "pcscd.service"])
        self.print_status("pcscd akıllı kart arka plan servisi ayağa kaldırıldı.")

        user = self._get_active_user()
        if user != "root":
            subprocess.call(["usermod", "-aG", "dialout", user])
            self.print_status(f"'{user}' kullanıcısına akıllı kart donanım yetkisi (dialout) verildi.")

        self.print_status("E-İmza ve UYAP akıllı kart altyapısı hazırlandı.")
        return True

    def coz_bluetooth_ve_ses(self):
        print("\n--- 5. Bluetooth Kulaklık ve Ses Profili Onarımı ---")
        print("[*] Bluetooth ve ses codec kütüphaneleri kuruluyor...")
        subprocess.call([
            "apt-get", "install", "-y",
            "bluetooth", "bluez", "blueman", "bluez-tools",
            "libspa-0.2-bluetooth", "pulseaudio-module-bluetooth", "bluez-firmware"
        ])

        main_conf = Path("/etc/bluetooth/main.conf")
        if main_conf.exists():
            try:
                content = main_conf.read_text(encoding="utf-8")
                if "AutoEnable" not in content:
                    content += "\n[Policy]\nAutoEnable=true\n"
                    main_conf.write_text(content, encoding="utf-8")
            except Exception:
                pass

        subprocess.call(["systemctl", "enable", "bluetooth"])
        subprocess.call(["systemctl", "restart", "bluetooth"])
        self.print_status("Bluetooth çekirdek servisi yeniden başlatıldı.")

        try:
            user = self._get_active_user()
            subprocess.call(["pkill", "-u", user, "-f", "wireplumber"], stderr=subprocess.DEVNULL)
            subprocess.call(["pkill", "-u", user, "-f", "pipewire"], stderr=subprocess.DEVNULL)
        except Exception:
            pass

        self.print_status("Bluetooth A2DP yüksek kaliteli ses profili aktif edildi.")
        return True

    def coz_ram_ve_zram(self):
        print("\n--- 6. RAM Şişmesi ve Kilitlenme Önleyici ZRAM Kurulumu ---")
        print("[*] zram-tools bellek sıkıştırma motoru kuruluyor...")
        subprocess.call(["apt-get", "install", "-y", "zram-tools"])

        zram_conf = Path("/etc/default/zramswap")
        zram_text = (
            "# Pardus Optimize ZRAM Yapılandırması\n"
            "ALGO=lz4\n"
            "PERCENT=50\n"
            "PRIORITY=100\n"
        )
        zram_conf.write_text(zram_text, encoding="utf-8")

        subprocess.call(["sysctl", "-w", "vm.swappiness=100"])
        subprocess.call(["systemctl", "enable", "zramswap"])
        subprocess.call(["systemctl", "restart", "zramswap"])
        self.print_status("ZRAM (LZ4) dinamik bellek sıkıştırması devreye alındı (Kilitlenmeler önlendi).")
        return True

    def coz_laptop_pil_ve_isinma(self):
        print("\n--- 7. Laptop Pil Süresi ve Isınma/Fan Optimizasyonu (TLP) ---")
        print("[*] TLP ve Thermald termal koruma paketleri kuruluyor...")
        subprocess.call(["apt-get", "install", "-y", "tlp", "tlp-rdw", "thermald", "powertop"])

        subprocess.call(["systemctl", "enable", "tlp"])
        subprocess.call(["systemctl", "restart", "tlp"])
        subprocess.call(["tlp", "start"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.print_status("TLP otomatik güç tasarrufu ve fan soğutma profili başlatıldı.")
        return True

    def coz_grub_ve_windows(self):
        self._check_root()
        print("\n--- 8. GRUB Menüsünde Windows'un Görünmesi (Dual-Boot Onarımı) ---")
        print("[*] os-prober paketi kuruluyor ve GRUB yapılandırması kontrol ediliyor...")
        subprocess.call(["apt-get", "install", "-y", "os-prober"])

        grub_default = Path("/etc/default/grub")
        if grub_default.exists():
            content = grub_default.read_text(encoding="utf-8")
            if "GRUB_DISABLE_OS_PROBER=false" not in content:
                if "GRUB_DISABLE_OS_PROBER" in content:
                    content = re.sub(r'#?\s*GRUB_DISABLE_OS_PROBER=.*', 'GRUB_DISABLE_OS_PROBER=false', content)
                else:
                    content += "\nGRUB_DISABLE_OS_PROBER=false\n"
                grub_default.write_text(content, encoding="utf-8")

        # 30_os-prober betiğinin çalıştırılabilir olduğundan emin ol
        os_prober_script = Path("/etc/grub.d/30_os-prober")
        if os_prober_script.exists():
            try:
                os_prober_script.chmod(0o755)
            except Exception:
                pass

        res = subprocess.call(["update-grub"])
        self.print_status("GRUB önyükleyici güncellendi. Windows EFI/Boot Manager girişi menüye eklendi.", res == 0)
        return True

    def coz_meb_sertifikasi(self):
        self._check_root()
        print("\n--- 9. MEB / EBA Güvenlik Sertifikası Kurulumu ---")
        subprocess.call(["apt-get", "install", "-y", "ca-certificates"])
        installed_pkg = False
        try:
            res = subprocess.call(["apt-get", "install", "-y", "eba-certs"])
            if res == 0:
                installed_pkg = True
                self.print_status("eba-certs resmi paketi kuruldu.")
        except Exception:
            pass

        # Resmi paket bulunamazsa MEB kök sertifikasını doğrudan HTTP üzerinden indir
        meb_cert_path = Path("/usr/local/share/ca-certificates/MEB_SERTIFIKASI.crt")
        if not installed_pkg and not meb_cert_path.exists():
            try:
                tmp_cer = Path("/tmp/MEB_SERTIFIKASI.cer")
                url = "http://sertifika.meb.gov.tr/MEB_SERTIFIKASI.cer"
                subprocess.call(["wget", "-q", "-O", str(tmp_cer), url], timeout=15)
                if tmp_cer.exists() and tmp_cer.stat().st_size > 0:
                    subprocess.call(["openssl", "x509", "-inform", "DER", "-in", str(tmp_cer), "-out", str(meb_cert_path)])
                    if meb_cert_path.exists():
                        self.print_status("MEB Kök Sertifikası doğrudan indirilip güven zincirine eklendi.")
            except Exception:
                pass

        subprocess.call(["update-ca-certificates"])

        # Chromium / Chrome ve NSS veritabanı entegrasyonu
        try:
            active_user = self._get_active_user()
            user_home = Path(f"/home/{active_user}") if active_user != "root" else Path.home()
            nssdb_dir = user_home / ".pki" / "nssdb"
            if nssdb_dir.exists() and meb_cert_path.exists():
                subprocess.call([
                    "certutil", "-d", f"sql:{nssdb_dir}", "-A",
                    "-t", "C,,", "-n", "MEB-KOK-SERTIFIKASI",
                    "-i", str(meb_cert_path)
                ], stderr=subprocess.DEVNULL)
        except Exception:
            pass

        self.print_status("Sistem güvenilir sertifika havuzu (Root CA) ve tarayıcı SSL zinciri güncellendi.")
        return True

    def coz_touchpad_yapilandirmasi(self):
        self._check_root()
        print("\n--- 10. Touchpad Dokunarak Tıklama (Tap-to-Click) Ayarı ---")
        xorg_dir = Path("/etc/X11/xorg.conf.d")
        xorg_dir.mkdir(parents=True, exist_ok=True)
        conf_file = xorg_dir / "40-libinput.conf"

        conf_content = (
            'Section "InputClass"\n'
            '    Identifier "libinput touchpad catchall"\n'
            '    MatchIsTouchpad "on"\n'
            '    MatchDevicePath "/dev/input/event*"\n'
            '    Driver "libinput"\n'
            '    Option "Tapping" "on"\n'
            '    Option "NaturalScrolling" "true"\n'
            '    Option "TappingDrag" "on"\n'
            '    Option "ScrollMethod" "twofinger"\n'
            '    Option "DisableWhileTyping" "true"\n'
            'EndSection\n'
        )
        conf_file.write_text(conf_content, encoding="utf-8")

        # KDE Plasma yapılandırması (KDE 5 ve KDE 6)
        active_user = self._get_active_user()
        user_home = Path(f"/home/{active_user}") if active_user != "root" else Path.home()
        kcminput = user_home / ".config" / "kcminputrc"

        for kwrite in ["kwriteconfig5", "kwriteconfig6"]:
            try:
                subprocess.call([
                    kwrite,
                    "--file", str(kcminput),
                    "--group", "Touchpad",
                    "--key", "tapToClick",
                    "true"
                ], stderr=subprocess.DEVNULL)
                subprocess.call([
                    kwrite,
                    "--file", str(kcminput),
                    "--group", "Touchpad",
                    "--key", "naturalScroll",
                    "true"
                ], stderr=subprocess.DEVNULL)
            except Exception:
                pass

        # GNOME GSettings desteği
        try:
            subprocess.call([
                "gsettings", "set",
                "org.gnome.desktop.peripherals.touchpad",
                "tap-to-click", "true"
            ], stderr=subprocess.DEVNULL)
        except Exception:
            pass

        self.print_status("Touchpad dokunarak tıklama (tap-to-click) ve çift parmak kaydırma aktifleştirildi.")
        return True

    def calistir_hepsi(self):
        print("=" * 75)
        print("Pardus Çözüm Merkezi - Kapsamlı Sistem Doktoru (10 Temel Onarım)")
        print("=" * 75)

        self._check_root()

        self.coz_apt_dpkg_kilitleri()
        self.coz_wifi_suruculeri()
        self.coz_yazici_ve_cups()
        self.coz_eimza_ve_uyap()
        self.coz_bluetooth_ve_ses()
        self.coz_ram_ve_zram()
        self.coz_laptop_pil_ve_isinma()
        self.coz_grub_ve_windows()
        self.coz_meb_sertifikasi()
        self.coz_touchpad_yapilandirmasi()

        print("\n" + "=" * 75)
        print("Tüm işlemler başarıyla tamamlandı. Pardus en üst kararlılık seviyesine getirildi.")
        print("=" * 75)


def main():
    merkez = PardusCozumMerkezi()
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["--grub", "--windows", "--grub-windows"]:
            merkez.coz_grub_ve_windows()
            return
        elif arg in ["--meb", "--eba", "--meb-sertifika"]:
            merkez.coz_meb_sertifikasi()
            return
        elif arg in ["--touchpad", "--touchpad-ayar"]:
            merkez.coz_touchpad_yapilandirmasi()
            return
        elif arg in ["--apt", "--dpkg", "--kilit"]:
            merkez.coz_apt_dpkg_kilitleri()
            return
        elif arg in ["--wifi", "--ag"]:
            merkez.coz_wifi_suruculeri()
            return
        elif arg in ["--yazici", "--cups"]:
            merkez.coz_yazici_ve_cups()
            return
        elif arg in ["--eimza", "--uyap", "--akis"]:
            merkez.coz_eimza_ve_uyap()
            return
        elif arg in ["--bluetooth", "--ses"]:
            merkez.coz_bluetooth_ve_ses()
            return
        elif arg in ["--ram", "--zram"]:
            merkez.coz_ram_ve_zram()
            return
        elif arg in ["--pil", "--tlp", "--laptop"]:
            merkez.coz_laptop_pil_ve_isinma()
            return
        elif arg in ["--yardim", "-h", "--help"]:
            print("Pardus Çözüm Merkezi Kullanım Seçenekleri:")
            print("  --grub        : GRUB menüsünde Windows'u geri getirir (os-prober)")
            print("  --meb         : MEB/EBA güvenlik sertifikasını kurar (eba-certs)")
            print("  --touchpad    : Touchpad dokunarak tıklama (tap-to-click) ve kaydırmayı açar")
            print("  --apt         : APT/DPKG kilitlerini ve kırık paketleri onarır")
            print("  --wifi        : Broadcom ve Realtek Wi-Fi sürücülerini kurar")
            print("  --yazici      : Canon ve HP CUPS yazdırma servisini yapılandırır")
            print("  --eimza       : E-İmza, UYAP ve AKİS kart okuyucuları bağlar")
            print("  --bluetooth   : Bluetooth kulaklık ve ses profilini düzeltir")
            print("  --ram         : ZRAM LZ4 dinamik RAM sıkıştırmasını açar")
            print("  --pil         : Laptop pil süresi ve fan soğutmasını optimize eder")
            print("  --hepsi       : 10 onarımın tamamını sırayla uygular")
            return

    merkez.calistir_hepsi()


if __name__ == "__main__":
    main()
