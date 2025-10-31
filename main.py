import requests
import csv
import time
import datetime
import os
import subprocess

# ==== KONFIGURASI ====
API_KEY = "MASUKKAN_API_KEY_AQICN_ANDA"
UIDS = {
    "Jakarta": "@1234",
    "Depok": "@5678",
    "Bogor": "@91011",
    "Tangerang": "@1213",
    "Bekasi": "@1415"
}
SLEEP_PER_CITY = 2  # detik antar kota
SAVE_INTERVAL_HOURS = 24  # simpan per 24 jam
GITHUB_REPO = "https://github.com/username/nama_repo.git"
GITHUB_LOCAL_PATH = "/root/aqi_collector/github_repo"
TELEGRAM_BOT_TOKEN = "MASUKKAN_BOT_TOKEN"
TELEGRAM_CHAT_ID = "MASUKKAN_CHAT_ID"

# ==== FUNGSI ====
def send_telegram(msg):
    try:
        requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            params={"chat_id": TELEGRAM_CHAT_ID, "text": msg}
        )
    except:
        pass

def init_repo():
    if not os.path.exists(GITHUB_LOCAL_PATH):
        subprocess.run(["git", "clone", GITHUB_REPO, GITHUB_LOCAL_PATH])
    os.chdir(GITHUB_LOCAL_PATH)

def fetch_data(city, uid):
    url = f"https://api.waqi.info/feed/{uid}/?token={API_KEY}"
    try:
        res = requests.get(url).json()
        if res.get("status") == "ok":
            data = res["data"]
            iaqi = data.get("iaqi", {})
            return {
                "city": city,
                "time": data["time"]["s"],
                "pm25": iaqi.get("pm25", {}).get("v"),
                "pm10": iaqi.get("pm10", {}).get("v"),
                "aqi": data.get("aqi")
            }
    except Exception as e:
        print(f"Gagal ambil data {city}: {e}")
    return None

def save_csv(data_list):
    now = datetime.datetime.now()
    file_name = f"aqi_{now.strftime('%Y-%m-%d')}.csv"
    file_path = os.path.join(GITHUB_LOCAL_PATH, file_name)

    write_header = not os.path.exists(file_path)
    with open(file_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["city", "time", "pm25", "pm10", "aqi"])
        if write_header:
            writer.writeheader()
        writer.writerows(data_list)
    return file_name

def push_to_github(file_name):
    subprocess.run(["git", "add", file_name])
    subprocess.run(["git", "commit", "-m", f"Update {file_name}"])
    subprocess.run(["git", "push"])

# ==== PROGRAM UTAMA ====
if __name__ == "__main__":
    send_telegram("🚀 AQI collector dimulai...")
    init_repo()
    while True:
        start_day = datetime.datetime.now().strftime("%Y-%m-%d")
        all_data = []
        while datetime.datetime.now().strftime("%Y-%m-%d") == start_day:
            for city, uid in UIDS.items():
                data = fetch_data(city, uid)
                if data:
                    all_data.append(data)
                    print(data)
                time.sleep(SLEEP_PER_CITY)
            time.sleep(60)  # jeda antar batch kota
        # simpan setelah 24 jam
        file_name = save_csv(all_data)
        push_to_github(file_name)
        send_telegram(f"✅ Data harian {file_name} telah diunggah ke GitHub.")
