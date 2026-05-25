# contact_summary.py
#
# GMAT Python interface module.  Called from the mission sequence after
# propagation to produce a per-day contact-minutes summary from the
# SiteViewMaxElevationReport output file.
#
# Usage in GMAT script:
#   Create Variable dummy;
#   [dummy] = Python.contact_summary.summarize(dummy);
#
# Input:  /var/tmp/Kiruna_Alaska_contacts_maxel.txt
# Output: /var/tmp/Kiruna_Alaska_daily_summary.txt

import os
from collections import defaultdict

INPUT_FILE  = '/var/tmp/Kiruna_Alaska_contacts_maxel.txt'
OUTPUT_FILE = '/var/tmp/Kiruna_Alaska_daily_summary.txt'

_MONTHS = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
    'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
    'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
}


def _parse_date(time_str):
    """'24 May 2025 01:23:45.000'  ->  '2025-05-24'"""
    parts = time_str.strip().split()
    try:
        day   = int(parts[0])
        month = _MONTHS[parts[1]]
        year  = int(parts[2])
        return f'{year}-{month:02d}-{day:02d}'
    except (IndexError, KeyError, ValueError):
        return None


def _find_columns(header_line, dashes_line):
    """Return list of (name, col_start, col_end) derived from dashes separator.
    Column spacing between fields is 5 spaces (GMAT hard-codes columnSpacing)."""
    columns = []
    i = 0
    n = len(dashes_line.rstrip())
    while i < n:
        if dashes_line[i] == '-':
            start = i
            while i < n and dashes_line[i] == '-':
                i += 1
            col_end = i
            name = header_line[start:col_end].strip()
            columns.append((name, start, col_end))
        else:
            i += 1
    return columns


def _extract(row, columns, col_name):
    """Return the trimmed value of the first column whose header contains col_name."""
    for idx, (name, start, _) in enumerate(columns):
        if col_name in name:
            field_end = columns[idx + 1][1] if idx + 1 < len(columns) else len(row)
            return row[start:field_end].strip()
    return ''


def _fmt_mssms(total_seconds):
    """Convert decimal seconds to 'm:ss.ms' string."""
    rounded_ms = round(total_seconds * 1000)
    ms      = rounded_ms % 1000
    total_s = rounded_ms // 1000
    return f'{total_s // 60}:{total_s % 60:02d}.{ms:03d}'


def summarize(dummy=0):
    """Compute per-day contact minutes and write summary report.
    The dummy argument is required so GMAT's Python interface can pass
    a Variable; its value is ignored."""

    if not os.path.exists(INPUT_FILE):
        return 0.0

    with open(INPUT_FILE) as fh:
        lines = fh.readlines()

    # Locate the column header row
    header_idx = None
    for i, line in enumerate(lines):
        if 'Observer' in line and 'Start Time' in line:
            header_idx = i
            break
    if header_idx is None or header_idx + 1 >= len(lines):
        return 0.0

    columns = _find_columns(lines[header_idx], lines[header_idx + 1])

    # Accumulate totals: {(date, observer): [total_seconds, pass_count]}
    daily = defaultdict(lambda: [0.0, 0])
    for line in lines[header_idx + 2:]:
        if not line.strip():
            continue
        obs  = _extract(line, columns, 'Observer')
        ts   = _extract(line, columns, 'Start Time')
        dur  = _extract(line, columns, 'Duration')
        if not (obs and ts and dur):
            continue
        try:
            secs = float(dur)
        except ValueError:
            continue
        date = _parse_date(ts)
        if date is None:
            continue
        daily[(date, obs)][0] += secs
        daily[(date, obs)][1] += 1

    with open(OUTPUT_FILE, 'w') as fh:
        fh.write('Contact summary by day and ground station\n')
        fh.write('=========================================\n\n')
        if not daily:
            fh.write('No contacts detected.\n')
            return 0.0
        fh.write(f'{"Date":<12}  {"Station":<12}  {"Passes":>6}  {"Total contact":>13}\n')
        fh.write(f'{"-"*12}  {"-"*12}  {"-"*6}  {"-"*13}\n')
        for (date, obs) in sorted(daily):
            total_secs, passes = daily[(date, obs)]
            fh.write(f'{date:<12}  {obs:<12}  {passes:>6}  {_fmt_mssms(total_secs):>13}\n')

    return 0.0
