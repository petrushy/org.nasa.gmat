# Flatpak manifest for GMAT

This is a flatpak manifest to build the GMAT tool in a reproducable flatpak container.

This manifest is not from the GMAT project and has no affiliaction with it. Use it at your own risk.

To build it and install on user do:

    flatpak-builder --user --install  --force-clean --install-deps-from --keep-build-dirs  build-dir 

To run:

    flatpak run org.nasa.gmat

To debug
    flatpak run --command=sh --devel org.nasa.gmat

## Inspiration and links

https://invent.kde.org/packaging/flatpak-kde-runtime

https://gmat.atlassian.net/wiki/spaces/GW/pages/380273314/Compiling

https://gmat.atlassian.net/wiki/spaces/GW/pages/380273355/Compiling+GMAT+CMake+Build+System

https://docs.flatpak.org/en/latest/index.html

https://gitlab.com/digitalsats/gmat2020a-box

https://discourse.flathub.org/

https://github.com/flathub

