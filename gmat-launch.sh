#!/bin/sh
cd /app/bin
# Force light theme: GMAT's wxWidgets UI does not support dark mode (text/icon contrast breaks)
export GTK_THEME=Adwaita:light
exec /app/bin/GMAT "$@"
