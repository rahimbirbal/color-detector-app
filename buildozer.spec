[app]
# (str) Title of your application
title = Color Detector

# (str) Package name
package.name = colordetector

# (str) Package domain (needed for android/ios packaging)
package.domain = org.colordetector

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,jpeg,kv,csv,txt

# (str) Application versioning (method 1)
version = 1.0

# (list) Application requirements
# Simplified requirements for better Android compatibility
requirements = python3,kivy==2.1.0,numpy==1.24.4,pillow

# (str) Supported orientation
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

[android]
# (int) Target Android API, should be as high as possible.
android.api = 34

# (int) Minimum API your APK / AAB will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (str) Android SDK version to use  
android.sdk = 34

# (list) Permissions
android.permissions = CAMERA,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,INTERNET

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (str) Android logcat filters to use
android.logcat_filters = *:S python:D

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (str) Bootstrap to use for android builds
# Run `buildozer android possible_bootstraps` to see available bootstraps.
# android.bootstrap = sdl2

# (str) Android entry point, default is ok for Kivy-based app
android.entrypoint = org.kivy.android.PythonActivity

# (str) Full name including package path of the Java class that implements Python Service
# android.service_class_name = org.kivy.android.PythonService

# (str) Android app theme, default is ok for Kivy-based app
# android.apptheme = "@android:style/Theme.NoTitleBar"

# (list) Pattern to whitelist for the whole project. More details
# https://python-for-android.readthedocs.io/en/latest/buildoptions/#whitelist
# android.whitelist =

# (str) Path to a custom whitelist file
# android.whitelist_src =

# (str) Path to a custom blacklist file
# android.blacklist_src =

# (str) Path to the android-24 SDK platform
# p4a.local_recipes =

# (str) python-for-android branch to use, defaults to master
p4a.branch = master

# (str) python-for-android git clone directory (if empty, it will be automatically cloned from github)
# p4a.source_dir =

# (str) The directory in which python-for-android should look for your own build recipes (if any)
# p4a.local_recipes =

# (str) Filename of a directory that will be turned into the root of the java build, so you can put your
# java files in there.
# android.java_src_dir =

# (str) python-for-android whitelist
# android.p4a_whitelist =

# (str) python-for-android blacklist
# android.p4a_blacklist =