"""
patch_libs.py  —  post-install library compatibility patches
Runs as a PlatformIO pre-build extra_script, after libraries are installed.
"""
Import("env")  # noqa: F821
import os

def patch_file(path, old, new, description):
    if not os.path.isfile(path):
        print(f"patch_libs: {description} — file not found, skipping")
        return
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if old not in content:
        print(f"patch_libs: {description} — already patched or pattern missing")
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.replace(old, new))
    print(f"patch_libs: applied — {description}")

libdeps = os.path.join(
    env.subst("$PROJECT_LIBDEPS_DIR"),
    env.subst("$PIOENV"),
)

# GAACE_Core debug.cpp: analogWriteResolution() gained a mandatory pin arg in
# ESP32 Arduino core v3.  Pass pin 0 (arbitrary — ESP32-S3 has no DAC anyway).
patch_file(
    os.path.join(libdeps, "GAACE_Core", "src", "debug.cpp"),
    "analogWriteResolution(i);",
    "analogWriteResolution(0, i);",
    "GAACE_Core/debug.cpp — analogWriteResolution pin arg (core v3)",
)
