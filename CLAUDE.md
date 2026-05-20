# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository is a **Flatpak manifest** for packaging NASA's GMAT (General Mission Analysis Tool) R2026a as a sandboxed Linux Flatpak application. It is not the GMAT source code itself — it contains only the build manifest, configuration files, and submodules needed to produce a distributable Flatpak.

## Key Files

- `org.nasa.gmat.yaml` — The Flatpak manifest (main file to edit)
- `gmat_startup_file.txt` — GMAT runtime configuration installed to `/app/bin/`; defines plugin paths, data paths, and output directories
- `gmat-launch.sh` — Wrapper script installed to `/app/bin/`; sets working directory to `/app/bin` before exec so GMAT resolves relative data paths correctly
- `org.nasa.gmat.desktop` — Desktop entry file for the application launcher
- `org.nasa.gmat.metainfo.xml` — AppStream metadata for Flathub submission
- `shared-modules/` — Git submodule from the Flathub shared-modules repo (provides reusable module definitions like `glew`, etc.)

## Common Commands

### Initial setup
```bash
git submodule update --init
```

### Build and install the Flatpak (user installation)
```bash
flatpak run org.flatpak.Builder --user --install --force-clean build-dir org.nasa.gmat.yaml
```

`flatpak-builder` is installed as `org.flatpak.Builder` (Flatpak app), not a system package. Do NOT pass `--keep-build-dirs` — it gets forwarded to `flatpak install` and fails.

### Rebuild only config/scripts (fast — skips GMAT recompile)
```bash
flatpak run org.flatpak.Builder --user --install --force-clean build-dir org.nasa.gmat.yaml
```
Without `--force-clean` the build dir won't be empty and will error. With `--force-clean`, unchanged modules hit the cache and only changed modules rebuild. Changing only `gmat_startup_file.txt` or `gmat-launch.sh` rebuilds only `gmat-config` (seconds).

### Run the application
```bash
flatpak run org.nasa.gmat
```

### Debug shell inside the Flatpak sandbox
```bash
flatpak run --command=sh --devel org.nasa.gmat
```

### Update submodules
```bash
git submodule update --remote --merge
```

## Build Architecture

The manifest builds and installs all dependencies from source into `/app`, in this order:

1. **glew** — via `shared-modules/glew/glew.json`
2. **Python 3.12.13** — built with `--enable-shared`; required for GMAT's Python plugin (`libPythonInterface_py312`)
3. **libglu** — mesa/glu 9.0.3, built with meson
4. **wxWidgets 3.2.9** — built with GTK3 backend (`--with-gtk=3`) and OpenGL support; GTK3 is provided by the freedesktop 25.08 runtime
5. **tcsh** — required to run the cspice `makeall.csh` build script
6. **XercesC 3.2.5** — XML library required by GMAT, built with curl network accessor and gnuiconv transcoder
7. **cspice** — NAIF/JPL SPICE toolkit (pre-compiled C library from JPL); the build script patches the csh shebang lines to use the just-built tcsh
8. **gmat** — GMAT R2026a source + OpenFramesInterface R2025a_v1 plugin, built with CMake pointing at `/app` for cspice; source patches applied before cmake (see below)
9. **gmat-config** — Installs `gmat_startup_file.txt`, `org.nasa.gmat.desktop`, `org.nasa.gmat.metainfo.xml`, and `gmat-launch.sh`

### flatpak-builder cmake-ninja build phase order

Within each cmake module, the phases run in this order:
1. Shell commands (`type: shell`) — run BEFORE cmake configure; use for source patching
2. cmake configure
3. cmake build (ninja)
4. `build-commands` — run AFTER ninja build but BEFORE `cmake install`; `/app` is read-only overlay at this point for prior modules
5. cmake install

Implication: file copies intended to override installed files must be done in shell commands (step 1), not build-commands (step 4).

### Runtime

- Base: `org.freedesktop.Platform` / `org.freedesktop.Sdk`, version `25.08`
- Java (openjdk17) required at build time via `PATH` and `JAVA_HOME` in `build-options.env`; not a separate SDK extension in the manifest
- Both Wayland and X11 sockets active (`--socket=wayland`, `--socket=x11`, `--socket=fallback-x11`)
- Output and log files go to `/var/tmp/` (via `--env=OUTPUT_PATH=/var/tmp` and `TMPDIR=/var/tmp`)
- The sandbox has broad filesystem access: `--filesystem=home` and `--filesystem=xdg-documents`

### Source patches applied to GMAT

All patches live in the `type: shell` commands of the `gmat` module and are applied before cmake runs.

**1. GCC 15 buffer overflow — `DeFile.hpp`**
`char constName[400][6]` and `char label[3][84]` are fixed-width binary fields with no null terminators. GCC 15's `__strcpy_chk` detects the destination size and aborts. Fixed by replacing `strcpy` with `memcpy`/`memset` using the correct field widths (6 and 84 bytes).

**2. HiDPI quarter-screen OpenGL viewport — `ViewCanvas.cpp`, `OrbitViewCanvas.cpp`, `GroundTrackCanvas.cpp`, `VisualModelCanvas.cpp`**
GMAT calls `GetClientSize()` → `glViewport()` directly. On HiDPI displays (e.g. 200% Wayland), `GetClientSize()` returns logical pixels but the GL framebuffer is physical pixels, so only the bottom-left quarter renders. Fixed by multiplying by `GetContentScaleFactor()` in all four `glViewport` call sites.

**3. GMATWin32.ico replacement**
GMAT's cmake installs `GMATWin32.ico` (Windows ICO format) as the app icon, but wxWidgets on Linux cannot load ICO files, causing a warning dialog at startup. Fixed by overwriting the `.ico` in the source tree with a PNG before cmake runs, so cmake installs the PNG.

### Plugin configuration

`gmat_startup_file.txt` lists all GMAT plugins loaded at runtime (all resolved under `/app/plugins/`). Notable:
- Python plugin is pinned to `libPythonInterface_py312` to match the bundled Python 3.12 build
- `libMatlabInterface` is **commented out** — MATLAB is not installed in the Flatpak
- `libOpenFramesInterface` and `libOVtoOFI` are **commented out** — these require OpenSceneGraph (OSG), which is not in the freedesktop 25.08 runtime. Future enhancement: add OSG as a module and enable `-DPLUGIN_OPENFRAMESINTERFACE=ON`

### Remaining work for Flathub submission

- Add a real screenshot to `org.nasa.gmat.metainfo.xml`
- Tighten sandbox: `--filesystem=home` is too broad; narrow to specific paths
- Add a `cleanup` section to strip dev headers and static libs from the bundle
