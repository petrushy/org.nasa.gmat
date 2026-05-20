# Licensing Notes

This document covers the licensing of all components bundled in the
`org.nasa.gmat` Flatpak, and what is required before submitting to Flathub.

---

## Short answer

**Yes, this package is publishable on Flathub.**

All components are either standard FOSS licenses or permissive government /
research licenses that Flathub accepts. The only non-standard license is NAIF
cspice, which is functionally equivalent to a 2-clause BSD license and is
already bundled by NASA's own GMAT distribution under Apache 2.0.

---

## Component licenses

| Component | Version | License | Notes |
|-----------|---------|---------|-------|
| GMAT | R2026a | Apache-2.0 | NASA Goddard Space Flight Center |
| TLEPropagatorPlugin | (bundled with GMAT) | Apache-2.0 | ThinksysLab; confirmed in `plugins/TLEPropagatorPlugin/License-TlePropagator.txt` inside GMAT source |
| OpenFramesInterface | R2025a_v1 | Apache-2.0 | Emergent Space Technologies |
| XercesC | 3.2.5 | Apache-2.0 | Apache Software Foundation |
| Python | 3.12.13 | PSF-2.0 | Python Software Foundation |
| wxWidgets | 3.2.9 | LicenseRef-wxWindows | LGPL-2.0-or-later with wxWindows exception; Flathub-standard |
| libglu | 9.0.3 | MIT | Mesa / SGI |
| GLEW | (via shared-modules) | MIT AND BSD-3-Clause | |
| tcsh | 6.24.10 | BSD-3-Clause | Build-time only; stripped from final bundle |
| **cspice** | N0067 | LicenseRef-NAIF-CSPICE | See below |

---

## cspice / NAIF SPICE toolkit

cspice is developed by the Navigation and Ancillary Information Facility (NAIF)
at NASA's Jet Propulsion Laboratory (JPL), operated by Caltech under NASA
contract. It is **not** distributed under a formally OSI-approved license —
NAIF publishes license terms on their website rather than including a license
file inside the toolkit archive.

**Key terms (from https://naif.jpl.nasa.gov/naif/rules.html):**
- Free to use for any purpose (academic, commercial, government)
- Free to copy, modify, and redistribute
- Must retain JPL/Caltech copyright notices in redistributions
- Provided "AS IS" without warranty

This is functionally equivalent to a 2-clause BSD license. The strongest
precedent for bundling it is that NASA's own GMAT project distributes cspice
as part of its Apache 2.0 source release.

For Flathub metainfo, represent it as `LicenseRef-NAIF-CSPICE` in the SPDX
expression (the `LicenseRef-` prefix is the correct SPDX mechanism for
licenses not in the standard SPDX list).

---

## Required metainfo fix before Flathub submission

The current `<project_license>` in `org.nasa.gmat.metainfo.xml` only declares
`Apache-2.0`. Update it to the full SPDX expression covering all bundled
components:

```xml
<project_license>Apache-2.0 AND LicenseRef-wxWindows AND PSF-2.0 AND LicenseRef-NAIF-CSPICE</project_license>
```

---

## Apache 2.0 NOTICE requirement

Apache License 2.0 (Section 4d) requires that redistributions include a copy
of any NOTICE file from the original work. GMAT does not ship a top-level
`NOTICE` file in R2026a, so this requirement does not currently apply.
If a future GMAT release includes a `NOTICE` file, install it to
`/app/share/licenses/org.nasa.gmat/GMAT/NOTICE` in the `gmat-config` module.

---

## Remaining blockers for Flathub submission

1. **Screenshot** — Flathub requires at least one screenshot with a real image
   URL. Add `<image>https://…/screenshot.png</image>` inside the `<screenshot>`
   block in `org.nasa.gmat.metainfo.xml`.

2. **Update `<project_license>`** — as described above.

3. **Sandbox tightening** — `--filesystem=home` is broader than Flathub
   recommends; narrow to `xdg-documents` plus any other specific paths GMAT
   actually needs.

4. **aarch64** — cspice is distributed by NAIF as an x86_64 pre-compiled
   binary only. The manifest currently restricts cspice (and therefore the
   whole package) to `x86_64`. To support aarch64, cspice would need to be
   built from source.
