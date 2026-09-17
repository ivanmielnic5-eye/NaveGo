# Add project specific ProGuard rules here.
# By default, the flags in this file are appended to flags specified
# in /usr/local/Cellar/android-sdk/24.3.3/tools/proguard/proguard-android.txt
# You can edit the include path and order by changing the proguardFiles
# directive in build.gradle.
#
# For more details, see
#   http://developer.android.com/guide/developing/tools/proguard.html

# react-native-reanimated
-keep class com.swmansion.reanimated.** { *; }
-keep class com.facebook.react.turbomodule.** { *; }

# Add any project specific keep options here:

# ─── MapLibre Native ───
-keep class org.maplibre.android.** { *; }
-keep interface org.maplibre.android.** { *; }
-keep enum org.maplibre.android.** { *; }
-dontwarn org.maplibre.android.**
-dontwarn com.mapbox.**

# MapLibre usa reflexión en FontUtils
-keepclassmembers class * {
    @androidx.annotation.Keep *;
}

# Nitro Modules (HttpServer)
-keep class com.margelo.nitro.** { *; }
-dontwarn com.margelo.nitro.**
-keep class com.nitro.** { *; }
-dontwarn com.nitro.**

# TurboModules
-keep class com.facebook.react.turbomodule.** { *; }
