[app]
title = EXIF Forensic
package.name = exifforensic
package.domain = org.exif.analiz
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy,pillow,plyer
orientation = portrait
osx.kivy_version = 2.0.0
fullscreen = 0
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.accept_sdk_licenses = True

[buildozer]
log_level = 2
warn_on_root = 0
