#!/bin/sh
cd /app/bin
export GTK_THEME=Adwaita:light
exec /app/bin/GMAT "$@"
