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

**3. HiDPI quarter-screen viewport — OpenFramesInterface (OFGLCanvas.cpp, OFScene.cpp)**
Same root cause as patch 2, but in the OFI plugin. `OFGLCanvas::Resized` passes `event.GetSize().GetWidth/Height()` (logical) to `windowProxy->resizeWindow()`; all mouse event handlers pass `event.GetX()/GetY()` (logical) to `windowProxy->mouseMotion/buttonPress/buttonRelease()`. `OFScene` creates the `WindowProxy` with `mCanvas->GetSize().GetWidth/Height()` (logical). All fixed by multiplying by `GetContentScaleFactor()`. Mouse coordinates must be in the same pixel space as the window dimensions, so they are scaled too. sed cannot be used (strings contain regex metacharacters); Python `str.replace()` one-liners are used instead.

**4. GMATWin32.ico replacement**
GMAT's cmake installs `GMATWin32.ico` (Windows ICO format) as the app icon, but wxWidgets on Linux cannot load ICO files, causing a warning dialog at startup. Fixed by overwriting the `.ico` in the source tree with a PNG before cmake runs, so cmake installs the PNG.

### Plugin configuration

`gmat_startup_file.txt` lists all GMAT plugins loaded at runtime (all resolved under `/app/plugins/`). Notable:
- Python plugin is pinned to `libPythonInterface_py312` to match the bundled Python 3.12 build
- `libMatlabInterface` is **commented out** — MATLAB is not installed in the Flatpak
- `libOpenFramesInterface` and `libOVtoOFI` are **enabled** — OSG and OpenFrames are built as Flatpak modules (openscenegraph, openframes). `-DPLUGIN_OPENFRAMESINTERFACE=ON` is set in the gmat cmake config. Known issue: the OFI window crashes when dragged between Wayland outputs ("Broken pipe").

### Cleanup

A global `cleanup` section strips development artifacts and unused tools from the final bundle before export. It runs during the finish phase and does NOT invalidate module build caches. Current cleanup removes: all headers (`/include`), pkg-config files, static libs (`.a`, `.la`), wxWidgets build-system files (`bakefile`, `aclocal`), tcsh (only needed at build time for cspice), Xerces-C CLI tools, unused Python tools (idle, pydoc, 2to3), and the Python test suite and lib2to3.

### OSG font configuration

OSG searches `OSG_FILE_PATH` (set via finish-args: `/app/share/osg-fonts`) for fonts. The freedesktop runtime puts Liberation fonts at `/usr/share/fonts/liberation-fonts/` — a path OFI's hardcoded font list doesn't know. The `gmat-config` module copies the needed fonts into `/app/share/osg-fonts/` at build time:
- `arial.ttf` ← LiberationSans-Regular (metric-compatible; proprietary Arial not redistributable)
- `LiberationMono-Bold.ttf` ← direct copy (for OFI HUD epoch text)
- `courbd.ttf` ← LiberationMono-Bold (monospace bold substitute for Courier New Bold)

### Remaining work for Flathub submission

- Add a real screenshot to `org.nasa.gmat.metainfo.xml` (required by Flathub — add `<image>` URL inside the `<screenshot>` block)
- Tighten sandbox: `--filesystem=home` is too broad; narrow to specific paths
- aarch64 support: cspice is currently x86_64-only (pre-compiled binary from NAIF); building cspice from source would enable aarch64
- Investigate OFI crash when dragging between Wayland outputs ("Broken pipe" / Wayland surface invalidation)
