#!/bin/sh
cd /app/bin
# Force light theme: GMAT's wxWidgets UI does not support dark mode (text/icon contrast breaks)
export GTK_THEME=Adwaita:light
# Preload libpython so dlopen'd C extensions (math, etc.) can find Python symbols (RTLD_GLOBAL workaround)
export LD_PRELOAD=/app/lib/libpython3.12.so.1.0
exec /app/bin/GMAT "$@"
