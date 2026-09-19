#!/usr/bin/env python3
import json
import math
import os
import socket
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import swisseph as swe

ROOT = Path(__file__).resolve().parent
DEFAULT_PORT = 8899
APP_VERSION = "V36-final-complete"
PORT = int(os.environ.get("PORT", os.environ.get("JOTHIDAM_PORT", str(DEFAULT_PORT))))

SIGNS_TA = ["மேஷம்","ரிஷபம்","மிதுனம்","கடகம்","சிம்மம்","கன்னி","துலாம்","விருச்சிகம்","தனுசு","மகரம்","கும்பம்","மீனம்"]
PLANETS = [
    (swe.SUN, "சூரியன்"), (swe.MOON, "சந்திரன்"), (swe.MARS, "செவ்வாய்"),
    (swe.MERCURY, "புதன்"), (swe.JUPITER, "குரு"), (swe.VENUS, "சுக்கிரன்"),
    (swe.SATURN, "சனி")
]
NAKSHATRAS = ["அசுவினி","பரணி","கார்த்திகை","ரோகிணி","மிருகசீரிஷம்","திருவாதிரை","புனர்பூசம்","பூசம்","ஆயில்யம்","மகம்","பூரம்","உத்திரம்","ஹஸ்தம்","சித்திரை","சுவாதி","விசாகம்","அனுஷம்","கேட்டை","மூலம்","பூராடம்","உத்திராடம்","திருவோணம்","அவிட்டம்","சதயம்","பூரட்டாதி","உத்திரட்டாதி","ரேவதி"]
NAK_LORDS = ["கேது","சுக்கிரன்","சூரியன்","சந்திரன்","செவ்வாய்","ராகு","குரு","சனி","புதன்"]
DASHA_NAMES = ["கேது","சுக்கிரன்","சூரியன்","சந்திரன்","செவ்வாய்","ராகு","குரு","சனி","புதன்"]
DASHA_YEARS = [7,20,6,10,7,18,16,19,17]

HOUSE_LORDS = ["செவ்வாய்","சுக்கிரன்","புதன்","சந்திரன்","சூரியன்","புதன்","சுக்கிரன்","செவ்வாய்","குரு","சனி","சனி","குரு"]
HOUSE_MEANINGS = [
    "உடல், தன்மை, சுயநம்பிக்கை மற்றும் வாழ்க்கை அணுகுமுறை",
    "செல்வம், குடும்பம், பேச்சு, சேமிப்பு மற்றும் உணவு",
    "முயற்சி, தைரியம், தொடர்பு மற்றும் உடன்பிறப்புகள்",
    "வீடு, தாய், நிலம், வாகனம் மற்றும் மன அமைதி",
    "கல்வி, புத்தி, குழந்தைகள், படைப்பாற்றல்",
    "வேலை, சேவை, போட்டி, கடன் மற்றும் உடல்நலம்",
    "திருமணம், துணை, கூட்டாண்மை மற்றும் பொதுத் தொடர்பு",
    "மாற்றம், கூட்டு வளங்கள், ஆயுள் மற்றும் மறைவு சார்ந்த அம்சங்கள்",
    "பாக்கியம், தந்தை, தர்மம், உயர்கல்வி மற்றும் நீண்ட பயணம்",
    "தொழில், பதவி, பொறுப்பு மற்றும் சமூக நிலை",
    "லாபம், நண்பர்கள், தொடர்புகள் மற்றும் ஆசை நிறைவேற்றம்",
    "செலவு, வெளிநாடு, ஓய்வு, தனிமை மற்றும் ஆன்மிகம்"
]
PLANET_ROLES = {
    "சூரியன்":"தன்னம்பிக்கை, தலைமை, தந்தை, அதிகாரம்",
    "சந்திரன்":"மனம், தாய், உணர்வு, பழக்கம்",
    "செவ்வாய்":"தைரியம், முயற்சி, செயல், போட்டி",
    "புதன்":"புத்தி, கல்வி, கணக்கு, பேச்சு",
    "குரு":"அறிவு, ஆசான், பாக்கியம், வளர்ச்சி",
    "சுக்கிரன்":"உறவு, கலை, வசதி, அழகு",
    "சனி":"உழைப்பு, பொறுப்பு, ஒழுக்கம், தாமதம்",
    "ராகு":"ஆசை, புதுமை, வெளிப்புற அனுபவம்",
    "கேது":"பற்றின்மை, உள்நோக்கம், ஆன்மிகம்"
}

SIGN_LORDS = ["செவ்வாய்","சுக்கிரன்","புதன்","சந்திரன்","சூரியன்","புதன்","சுக்கிரன்","செவ்வாய்","குரு","சனி","சனி","குரு"]
OWN_SIGNS = {
    "சூரியன்": [0], "சந்திரன்": [3], "செவ்வாய்": [0,7], "புதன்": [2,5],
    "குரு": [8,11], "சுக்கிரன்": [1,6], "சனி": [9,10]
}
EXALT = {"சூரியன்":0,"சந்திரன்":1,"செவ்வாய்":9,"புதன்":5,"குரு":3,"சுக்கிரன்":11,"சனி":6}
DEBIL = {"சூரியன்":6,"சந்திரன்":7,"செவ்வாய்":3,"புதன்":11,"குரு":9,"சுக்கிரன்":5,"சனி":0}

def dignity_for(name: str, si: int) -> str:
    if name in EXALT and EXALT[name] == si: return "உச்சம்"
    if name in DEBIL and DEBIL[name] == si: return "நீசம்"
    if si in OWN_SIGNS.get(name, []): return "சொந்த ராசி"
    return "சாதாரண நிலை"

def aspect_targets(p):
    # Traditional Parashari-style house aspects, expressed as target house numbers.
    h = int(p.get("house", 0))
    targets = {((h + 5) % 12) + 1} if h else set()  # 7th aspect
    if p["name"] == "செவ்வாய்" and h:
        targets.update({((h + 2) % 12) + 1, ((h + 6) % 12) + 1})  # 4th, 8th
    elif p["name"] == "குரு" and h:
        targets.update({((h + 3) % 12) + 1, ((h + 7) % 12) + 1})  # 5th, 9th
    elif p["name"] == "சனி" and h:
        targets.update({((h + 1) % 12) + 1, ((h + 8) % 12) + 1})  # 3rd, 10th
    return sorted(targets)

swe.set_sid_mode(swe.SIDM_LAHIRI)


def norm(x: float) -> float:
    x = x % 360.0
    return x if x >= 0 else x + 360.0


def sign_index(lon: float) -> int:
    return int(norm(lon) // 30)


def dms(deg: float) -> str:
    x = norm(deg) % 30.0
    d = int(x)
    m_float = (x - d) * 60
    m = int(m_float)
    s = round((m_float - m) * 60)
    if s == 60:
        s = 0; m += 1
    if m == 60:
        m = 0; d += 1
    return f"{d:02d}° {m:02d}′ {s:02d}″"


def full_lon_dms(deg: float) -> str:
    x = norm(deg)
    d = int(x)
    m_float = (x - d) * 60
    m = int(m_float)
    s = round((m_float - m) * 60)
    if s == 60:
        s = 0; m += 1
    if m == 60:
        m = 0; d += 1
    return f"{d:03d}° {m:02d}′ {s:02d}″"


def nav_sign(lon: float) -> int:
    s = sign_index(lon)
    nav_no = min(8, int((norm(lon) % 30.0) / (30.0/9.0)))
    # Movable -> same sign; Fixed -> 9th from sign; Dual -> 5th from sign.
    if s % 3 == 0:
        start = s
    elif s % 3 == 1:
        start = (s + 8) % 12
    else:
        start = (s + 4) % 12
    return (start + nav_no) % 12


def nav_lagna(lon: float) -> int:
    return nav_sign(lon)


def nak_info(lon: float) -> dict:
    q = 360.0/27.0
    idx = min(26, int(norm(lon) / q))
    within = norm(lon) - idx*q
    pada = min(4, int(within / (q/4.0)) + 1)
    return {"name": NAKSHATRAS[idx], "pada": pada, "lord": NAK_LORDS[idx % 9], "index": idx}


# Fixed-offset fallback for environments where Python's IANA timezone database
# is unavailable (common on Windows when tzdata is not installed).
FIXED_TZ_OFFSETS = {
    'UTC': 0, 'Etc/UTC': 0, 'Asia/Kolkata': 330, 'Asia/Calcutta': 330,
    'Asia/Dubai': 240, 'Asia/Singapore': 480, 'Asia/Kuala_Lumpur': 480,
    'Asia/Tokyo': 540, 'Asia/Seoul': 540, 'Asia/Bangkok': 420,
    'Asia/Colombo': 330, 'Asia/Kathmandu': 345, 'Asia/Dhaka': 360,
    'Australia/Perth': 480, 'Australia/Darwin': 570, 'Australia/Adelaide': 570,
    'Australia/Sydney': 600, 'Pacific/Auckland': 720,
    'Europe/London': 0, 'Europe/Paris': 60, 'Europe/Berlin': 60,
    'America/New_York': -300, 'America/Chicago': -360,
    'America/Denver': -420, 'America/Los_Angeles': -480,
    'America/Toronto': -300, 'America/Vancouver': -480,
}

def timezone_for_name(tzname: str):
    try:
        return ZoneInfo(tzname)
    except Exception:
        if tzname in FIXED_TZ_OFFSETS:
            return timezone(timedelta(minutes=FIXED_TZ_OFFSETS[tzname]), name=tzname)
        return None


def parse_local_datetime(date_str: str, time_str: str, tzname: str) -> datetime:
    # Accept both ISO dates (YYYY-MM-DD) and the UI's DD/MM/YYYY if needed.
    date_str = str(date_str).strip()
    if re_match := __import__('re').fullmatch(r"(\d{2})/(\d{2})/(\d{4})", date_str):
        d, m, y = re_match.groups()
        date_str = f"{y}-{m}-{d}"
    # Accept HH:MM or HH:MM:SS.
    time_str = str(time_str).strip()
    if __import__('re').fullmatch(r"\d{2}:\d{2}", time_str):
        time_str += ":00"
    local = datetime.fromisoformat(f"{date_str}T{time_str}")
    tzname = str(tzname or '').strip()
    if not tzname:
        raise ValueError("Timezone is missing. Please select the birth place so its timezone is known.")
    tz = timezone_for_name(tzname)
    if tz is None:
        raise ValueError(
            f"Invalid timezone: {tzname}. Install the Python 'tzdata' package or choose a location from the search results."
        )
    return local.replace(tzinfo=tz)


def jd_from_local(local_dt: datetime) -> float:
    utc = local_dt.astimezone(timezone.utc)
    ut_hours = utc.hour + utc.minute/60.0 + utc.second/3600.0 + utc.microsecond/3_600_000_000.0
    return swe.julday(utc.year, utc.month, utc.day, ut_hours)


def calculate(payload: dict) -> dict:
    date_str = payload["date"]
    time_str = payload["time"]
    tzname = payload["timezone"]
    lat = float(payload["lat"])
    lon = float(payload["lon"])
    place_name = str(payload.get("place_name") or payload.get("place") or "")
    name = str(payload.get("name") or "")
    if not math.isfinite(lat) or not math.isfinite(lon):
        raise ValueError(f"Invalid coordinates: lat={lat!r}, lon={lon!r}")
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        raise ValueError(f"Coordinates out of range: lat={lat}, lon={lon}")
    local_dt = parse_local_datetime(date_str, time_str, tzname)
    utc_dt = local_dt.astimezone(timezone.utc)
    jd = jd_from_local(local_dt)
    ayanamsa = float(swe.get_ayanamsa_ut(jd))

    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    planets = []
    for planet in PLANETS:
        pid = planet[0]
        pname = planet[1]
        calc_result = swe.calc_ut(jd, pid, flags)
        xx = calc_result[0]
        planets.append({
            "name": pname,
            "lon": norm(float(xx[0])),
            "speed": float(xx[3])
        })
    rahu_result = swe.calc_ut(jd, swe.MEAN_NODE, flags)
    rahu_x = rahu_result[0]
    rahu_lon = norm(float(rahu_x[0]))
    rahu_speed = float(rahu_x[3])
    planets += [
        {"name":"ராகு", "lon":rahu_lon, "speed":rahu_speed},
        {"name":"கேது", "lon":norm(rahu_lon+180), "speed":-rahu_speed}
    ]

    houses_result = swe.houses_ex(jd, lat, lon, b"W", swe.FLG_SIDEREAL)
    if not isinstance(houses_result, (tuple, list)) or len(houses_result) < 2:
        raise ValueError(f"Unexpected Swiss Ephemeris houses result: {type(houses_result).__name__}")
    cusps = houses_result[0]
    ascmc = houses_result[1]
    if not isinstance(ascmc, (tuple, list)) or len(ascmc) < 1:
        raise ValueError("Swiss Ephemeris did not return Ascendant data")
    asc = norm(float(ascmc[0]))
    moon = next(p["lon"] for p in planets if p["name"] == "சந்திரன்")
    lag_sign = sign_index(asc)

    for p in planets:
        si = sign_index(p["lon"])
        p["sign"] = SIGNS_TA[si]
        p["sign_index"] = si
        p["deg_in_sign"] = norm(p["lon"]) % 30.0
        p["nakshatra"] = nak_info(p["lon"])
        p["nav_sign_index"] = nav_sign(p["lon"])
        p["nav_sign"] = SIGNS_TA[p["nav_sign_index"]]
        p["house"] = ((si - lag_sign) % 12) + 1
        p["retrograde"] = (p["speed"] < -1e-7 and p["name"] not in ("ராகு","கேது"))
        p["dignity"] = dignity_for(p["name"], si)
        p["aspects_houses"] = aspect_targets(p)

    houses = [
        {"house": i+1, "sign_index": (lag_sign+i)%12, "sign": SIGNS_TA[(lag_sign+i)%12],
         "lord": SIGN_LORDS[(lag_sign+i)%12], "meaning": HOUSE_MEANINGS[i],
         "planets": [p["name"] for p in planets if p["sign_index"] == (lag_sign+i)%12]}
        for i in range(12)
    ]
    for h in houses:
        lord_planet = next((p for p in planets if p["name"] == h["lord"]), None)
        h["lord_house"] = lord_planet["house"] if lord_planet else None
        h["lord_sign"] = lord_planet["sign"] if lord_planet else None
        h["lord_dignity"] = lord_planet["dignity"] if lord_planet else None
        h["aspected_by"] = [p["name"] for p in planets if h["house"] in p.get("aspects_houses", [])]

    conjunctions = []
    by_sign = {}
    for p in planets:
        by_sign.setdefault(p["sign_index"], []).append(p)
    for si, ps in by_sign.items():
        if len(ps) >= 2:
            conjunctions.append({"sign": SIGNS_TA[si], "planets": [p["name"] for p in ps]})

    return {
        "name": name,
        "date": local_dt.strftime("%Y-%m-%d"),
        "time": local_dt.strftime("%H:%M:%S"),
        "place": place_name,
        "lat": lat,
        "lon": lon,
        "timezone": tzname,
        "utc": utc_dt.isoformat(),
        "jd": jd,
        "ayanamsa": ayanamsa,
        "lagna": {"lon": asc, "sign_index": lag_sign, "sign": SIGNS_TA[lag_sign], "nav_sign_index": nav_lagna(asc), "nav_sign": SIGNS_TA[nav_lagna(asc)]},
        "moon": moon,
        "planets": planets,
        "houses": houses,
        "conjunctions": conjunctions,
        "dasha": vimshottari(moon, local_dt),
    }


def iso_date(d: datetime) -> str:
    return d.strftime("%d/%m/%Y")


def vimshottari(moon_lon: float, birth_local: datetime) -> dict:
    span = 360.0 / 27.0
    nak_idx = min(26, int(norm(moon_lon) / span))
    fraction = (norm(moon_lon) - nak_idx*span) / span
    start_idx = nak_idx % 9
    remain_years = DASHA_YEARS[start_idx] * (1.0 - fraction)
    cursor = birth_local
    rows = []
    current_utc = datetime.now(timezone.utc)
    for i in range(9):
        idx = (start_idx+i) % 9
        dur = remain_years if i == 0 else DASHA_YEARS[idx]
        start = cursor
        end = start + timedelta(days=dur*365.25)
        bhuktis = []
        bcur = start
        md_year = DASHA_YEARS[idx]
        for j in range(9):
            bidx = (idx+j)%9
            b_years = md_year * DASHA_YEARS[bidx] / 120.0
            bend = bcur + timedelta(days=b_years*365.25)
            bhuktis.append({"lord": DASHA_NAMES[bidx], "start": iso_date(bcur), "end": iso_date(bend), "years": b_years})
            bcur = bend
        rows.append({"lord":DASHA_NAMES[idx], "start":iso_date(start), "end":iso_date(end), "years":dur, "bhuktis":bhuktis})
        cursor = end
    return {"birth_nakshatra": nak_info(moon_lon), "balance_years": remain_years, "rows": rows}


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body, content_type="text/html; charset=utf-8"):
        if isinstance(body, str): body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            self._send(200, json.dumps({"ok":True,"engine":"Swiss Ephemeris","sidereal":"Lahiri","version":APP_VERSION,"port":PORT}), "application/json; charset=utf-8")
            return
        if path == "/api/version":
            self._send(200, json.dumps({"ok":True,"version":APP_VERSION,"engine":"Swiss Ephemeris","sidereal":"Lahiri","port":PORT}), "application/json; charset=utf-8")
            return
        if path in ("/", "/index.html"):
            self._send(200, (ROOT/"index.html").read_text(encoding="utf-8"))
            return
        if path == "/README.txt":
            self._send(200, (ROOT/"README.txt").read_text(encoding="utf-8"), "text/plain; charset=utf-8")
            return
        self._send(404, "Not found")

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/calculate":
            self._send(404, json.dumps({"ok":False,"error":"Not found"}), "application/json; charset=utf-8")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            payload = json.loads(raw) if raw else {}
            required = ["date","time","lat","lon","timezone"]
            missing = [k for k in required if k not in payload or payload.get(k) in (None, "")]
            if missing:
                raise ValueError("Missing fields: " + ", ".join(missing))
            result = calculate(payload)
            self._send(200, json.dumps({"ok":True,"data":result}, ensure_ascii=False), "application/json; charset=utf-8")
        except Exception as e:
            # Return the real local error (and traceback) so the browser can show the cause instead of a generic HTTP 400.
            import traceback
            detail = f"{type(e).__name__}: {e}"
            tb = traceback.format_exc(limit=8)
            print("[CALC ERROR]", detail)
            print(tb)
            self._send(200, json.dumps({"ok":False,"error":detail,"traceback":tb,"version":APP_VERSION}, ensure_ascii=False), "application/json; charset=utf-8")

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} - {fmt % args}")


def find_free_port(start=8899, end=8915):
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise OSError("No free local port available.")

def main():
    global PORT
    if "JOTHIDAM_PORT" not in os.environ:
        PORT = find_free_port()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Jothidam server running on 0.0.0.0:{PORT}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == "__main__":
    main()
