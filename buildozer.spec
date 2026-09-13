[app]
title = PK786 Casino
package.name = pk786casino
package.domain = com.pk786.app
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0.0

# CRITICAL: Remove hostpython3 - yeh hi problem hai!
requirements = python3,kivy==2.3.0,openssl,urllib3,certifi

orientation = portrait
fullscreen = 0
android.presplash_color = #070910

android.permissions = INTERNET, ACCESS_NETWORK_STATE

android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.allow_backup = True
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1