# GMAT Examples

## Kiruna_Alaska_Visibility

Computes ground station visibility (contact windows) for a Sun-Synchronous
Orbit satellite from two high-latitude stations: ESRANGE (Kiruna, Sweden)
and the Alaska Satellite Facility (Fairbanks, Alaska).

The satellite model is Sentinel-3B (ESA/EUMETSAT, NORAD ID 43437), a polar
SSO at ~814 km altitude with 98.65° inclination — representative of Earth
observation and remote sensing missions.

### Files

| File | Description |
|------|-------------|
| `Kiruna_Alaska_Visibility.script` | Main GMAT script |
| `Sentinel3B.tle` | Example TLE (epoch: 2025-05-24; update for current use) |

### Prerequisites

- GMAT R2026a (Flatpak: `flatpak run org.nasa.gmat`)
- The SPICESGP4 propagator is built into this GMAT build — no extra plugin needed

### How to run

1. **Update the TLE** (recommended for meaningful results):
   - Fetch a current TLE for NORAD ID 43437 from CelesTrak:
     `https://celestrak.org/SOCRATES/` or
     `https://celestrak.org/satcat/tle.php?CATNR=43437`
   - Replace the contents of `Sentinel3B.tle` with the three-line result
     (name line + line 1 + line 2). The satellite name on line 0 can be
     anything; the script matches by NORAD catalog number (43437).

2. **Copy the examples to your home directory** so GMAT can find the TLE:
   ```
   cp -r <path-to-examples> ~/gmat-examples
   ```

3. **Open GMAT** and load the script:
   - File → Open → navigate to `Kiruna_Alaska_Visibility.script`
   - Click **Run** (F5)

4. **View results**:
   - **3D OpenFrames window** — top-down north-pole view showing the polar orbit
     with the two station visibility cones (amber = Kiruna, cyan = Alaska).
     Each cone is drawn to 2000 km and subtends the 5° elevation mask.
   - **Ground-track plot** — 2D world map with the satellite ground track and
     station markers.
   - **Contact report (legacy)** — `/var/tmp/Kiruna_Alaska_contacts.txt`:
     start time, stop time, duration (s) per pass per station.
   - **Max-elevation report** — `/var/tmp/Kiruna_Alaska_contacts_maxel.txt`:
     start time, stop time, duration (s), peak elevation angle (deg), and
     time of peak elevation per pass per station. Useful for assessing link
     quality — a high max-elevation pass has a longer usable window and
     better geometry. Note: duration is always written in decimal seconds
     by GMAT (hardcoded in the ContactLocator).
   - **Daily contact summary** — `/var/tmp/Kiruna_Alaska_daily_summary.txt`:
     written automatically by the embedded Python call after propagation.
     Lists total contact time (m:ss.ms) and pass count per station per day.
     Example output:
     ```
     Contact summary by day and ground station
     =========================================

     Date          Station       Passes  Total contact
     ------------  ------------  ------  -------------
     2025-05-24    KirunaGS           5        42:18.000
     2025-05-24    AlaskaGS           4        34:52.000
     2025-05-25    KirunaGS           5        43:01.000
     ```

### Expected output

The contact report lists every pass above 5° elevation for each station over
3 days from the TLE epoch, including start time, end time, duration, and
maximum elevation angle. For a polar SSO like Sentinel-3B you should see
approximately 4–6 passes per day per station (Kiruna and Alaska are both
at high latitudes and receive frequent passes).

### 3D visualization: elevation cones

Each ground station has a `CustomFOV` sensor attached (via an `Antenna` hardware
object) pointing straight up (zenith direction). GMAT does not allow `ConicalFOV`
on ground station antennas, so a `CustomFOV` with 24 uniformly-spaced (clock, cone)
pairs all at 85° cone angle is used instead -- this traces a circle identical to the
conical shape. 85° from zenith = 90° - 5° elevation, matching the `ContactLocator`
mask exactly. The cones are drawn to 2000 km (well past the satellite altitude of
~814 km) and are semi-transparent so the orbit and Earth surface remain visible.

| Station | Cone colour | Meaning |
|---------|-------------|---------|
| ESRANGE (Kiruna) | Amber | Satellite is visible when it enters the cone |
| Alaska Sat. Facility | Cyan | Same |

The default view is top-down from above the North Pole (`DefaultEye = [0, 0, 40000]`
in Earth body-fixed coordinates). You can freely rotate and zoom the view in the
OpenFrames window during or after the simulation. Use the playback toolbar to replay
the 3-day trajectory and watch passes develop.

### Ground station coordinates

| Station | Latitude | East Longitude | Altitude |
|---------|----------|----------------|----------|
| ESRANGE (Kiruna, SE) | 67.883°N | 21.067°E | 320 m |
| Alaska Satellite Facility (Fairbanks, AK) | 64.867°N | 212.183°E (= 147.817°W) | 167 m |

Minimum elevation mask: 5° (both stations).

### Accuracy note

SGP4 (the TLE propagation method) is accurate to roughly 1–2 km at epoch
and degrades at ~1–3 km/day. For analysis more than 1–2 weeks from the TLE
epoch, fetch a fresh TLE before running. For high-fidelity work, replace the
SPICESGP4 propagator with a numerical propagator (e.g., `RungeKutta89`) and
supply initial state from a precise ephemeris.
