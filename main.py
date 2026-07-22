import io
import os
from datetime import datetime
from fractions import Fraction
from PIL import Image as PILImage
from PIL.ExifTags import TAGS, GPSTAGS

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image as KivyImage
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock
from plyer import filechooser

Window.clearcolor = (0.07, 0.07, 0.07, 1)

class ExifAnalyzerApp(App):
    def build(self):
        self.title = "Yerel EXIF Analiz"
        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        title_label = Label(
            text="[b]🔒 EXIF Forensic Analiz (Offline)[/b]", 
            markup=True, font_size='20sp', size_hint_y=None, height=40, color=(0.3, 0.85, 0.4, 1)
        )
        main_layout.add_widget(title_label)
        
        select_btn = Button(
            text="📸 Galeriden Fotoğraf Seç", 
            size_hint_y=None, height=50, background_color=(0.13, 0.59, 0.95, 1), font_size='16sp'
        )
        select_btn.bind(on_press=self.galeri_ac)
        main_layout.add_widget(select_btn)
        
        self.img_preview = KivyImage(size_hint_y=0.35, allow_stretch=True, keep_ratio=True)
        main_layout.add_widget(self.img_preview)
        
        scroll = ScrollView(size_hint=(1, 0.5))
        self.result_label = Label(
            text="Lütfen analiz edilecek fotoğrafı seçin.", 
            markup=True, font_size='14sp', size_hint_y=None, halign='left', valign='top', color=(0.9, 0.9, 0.9, 1)
        )
        self.result_label.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        self.result_label.bind(width=lambda instance, value: setattr(instance, 'text_size', (value, None)))
        scroll.add_widget(self.result_label)
        main_layout.add_widget(scroll)
        
        return main_layout

    def galeri_ac(self, instance):
        """Android yerel galerisini çağırır."""
        try:
            filechooser.open_file(
                on_selection=self.dosya_secildi_cb,
                filters=[("Görseller", "*.jpg", "*.jpeg", "*.png")]
            )
        except Exception as e:
            self.result_label.text = f"[color=ff5252]Galeri açılamadı: {str(e)}[/color]"

    def dosya_secildi_cb(self, selection):
        """Galeriden dosya seçildiğinde arka plandan UI iş parçacığına aktarır."""
        if not selection:
            return
        Clock.schedule_once(lambda dt: self.analiz_et(selection[0]), 0)

    def tarih_formatla(self, tarih_str):
        if not tarih_str or tarih_str == "Bilinmiyor": return "Bilinmiyor"
        try:
            dt = datetime.strptime(str(tarih_str).strip(), "%Y:%m:%d %H:%M:%S")
            aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylul", "Ekim", "Kasım", "Aralık"]
            return f"{dt.day} {aylar[dt.month - 1]} {dt.year} - {dt.strftime('%H:%M:%S')}"
        except Exception:
            return str(tarih_str).replace(":", ".", 2)

    def enstantane_formatla(self, val):
        try:
            f_val = float(val)
            if f_val <= 0: return str(val)
            if f_val < 1:
                frac = Fraction(f_val).limit_denominator(1000)
                return f"{frac.numerator}/{frac.denominator} s"
            return f"{round(f_val, 2)} s"
        except Exception:
            return str(val)

    def rasyonel_floata_cevir(self, deger):
        if isinstance(deger, (tuple, list)):
            if len(deger) == 0: return 0.0
            val = deger[0]
        else: val = deger
        try: return float(val)
        except (TypeError, ValueError, ZeroDivisionError): return 0.0

    def koordinatlari_ondaliga_cevir(self, koordinat, referans):
        if not koordinat or len(koordinat) < 3: return None
        derece = self.rasyonel_floata_cevir(koordinat[0])
        dakika = self.rasyonel_floata_cevir(koordinat[1])
        saniye = self.rasyonel_floata_cevir(koordinat[2])
        ondalik = derece + (dakika / 60.0) + (saniye / 3600.0)
        if referans in ['S', 'W']: ondalik = -ondalik
        return round(ondalik, 6)

    def analiz_et(self, dosya_yolu):
        try:
            self.img_preview.source = dosya_yolu
            self.img_preview.reload()
            with PILImage.open(dosya_yolu) as img:
                exif = img.getexif()
                metadata = {}
                gps_verisi = {}
                if exif:
                    for etiket_id, deger in exif.items(): metadata[TAGS.get(etiket_id, etiket_id)] = deger
                    exif_ifd = exif.get_ifd(0x8769)
                    for etiket_id, deger in exif_ifd.items(): metadata[TAGS.get(etiket_id, etiket_id)] = deger
                    gps_ifd = exif.get_ifd(0x8825)
                    for etiket_id, deger in gps_ifd.items(): gps_verisi[GPSTAGS.get(etiket_id, etiket_id)] = deger

                cekim_tarihi_ham = metadata.get("DateTimeOriginal", metadata.get("DateTime", "Bilinmiyor"))
                diyafram_ham = metadata.get("FNumber", "-")
                enstantane_ham = metadata.get("ExposureTime", "-")
                
                diyafram = f"f/{round(float(diyafram_ham), 2)}" if diyafram_ham != "-" else "-"
                enstantane = self.enstantane_formatla(enstantane_ham)
                
                enlem_ref = gps_verisi.get("GPSLatitudeRef")
                enlem_verisi = gps_verisi.get("GPSLatitude")
                boylam_ref = gps_verisi.get("GPSLongitudeRef")
                boylam_verisi = gps_verisi.get("GPSLongitude")
                
                gps_metin = "Konum Verisi Yok"
                if enlem_verisi and boylam_ref:
                    enlem = self.koordinatlari_ondaliga_cevir(enlem_verisi, enlem_ref)
                    boylam = self.koordinatlari_ondaliga_cevir(boylam_verisi, boylam_ref)
                    if enlem is not None and boylam is not None: gps_metin = f"{enlem}, {boylam}"

                rapor = (
                    f"[b][color=4caf50]📊 TEMEL BİLGİLER[/color][/b]\n"
                    f"• [b]Marka:[/b] {metadata.get('Make', 'Bilinmiyor')}\n"
                    f"• [b]Model:[/b] {metadata.get('Model', 'Bilinmiyor')}\n"
                    f"• [b]Çekim Tarihi:[/b] {self.tarih_formatla(cekim_tarihi_ham)}\n"
                    f"• [b]ISO:[/b] {metadata.get('ISOSpeedRatings', '-')}\n"
                    f"• [b]Diyafram:[/b] {diyafram}\n"
                    f"• [b]Enstantane:[/b] {enstantane}\n"
                    f"• [b]Odak Uzaklığı:[/b] {metadata.get('FocalLength', '-')} mm\n"
                    f"• [b]GPS:[/b] {gps_metin}\n\n"
                    f"[b][color=2196f3]📜 TÜM HAM EXIF VERİLERİ[/color][/b]\n"
                )
                tum_veriler = {**metadata, **gps_verisi}
                for k, v in tum_veriler.items():
                    if k not in ["JPEGThumbnail", "TIFFThumbnail"]: rapor += f"• [b]{k}:[/b] {v}\n"
                self.result_label.text = rapor
        except Exception as e:
            self.result_label.text = f"[color=ff5252]Hata oluştu: {str(e)}[/color]"

if __name__ == "__main__":
    ExifAnalyzerApp().run()
    
