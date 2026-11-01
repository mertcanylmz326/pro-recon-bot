import os
import time
import socket
import ssl
import urllib.parse
import requests
import threading
from flask import Flask, render_template_string, request, jsonify

# --- ÇEVRE DEĞİŞKENLERİ ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "9082287913:AAEw9lMwKXfRTGf4LzQiF1UEgLZDHzNuc8o")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# --- FLASK WEB PANELİ ---
app = Flask(__name__)

# Web Paneli Arayüzü (HTML + CSS)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Pro Recon & Vulnerability Panel</title>
    <style>
        body { background-color: #0f172a; color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; }
        .container { max-width: 900px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        h1 { color: #38bdf8; text-align: center; margin-bottom: 25px; }
        .form-group { display: flex; gap: 10px; margin-bottom: 20px; }
        input[type="text"] { flex: 1; padding: 12px; border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: #fff; font-size: 16px; }
        button { padding: 12px 24px; background: #0284c7; color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; transition: 0.2s; }
        button:hover { background: #0369a1; }
        .results { background: #0f172a; padding: 20px; border-radius: 8px; border: 1px solid #334155; white-space: pre-wrap; font-family: monospace; margin-top: 20px; max-height: 500px; overflow-y: auto; }
        .loading { color: #facc15; font-style: italic; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Pro Recon & Security Panel</h1>
        <div class="form-group">
            <input type="text" id="targetUrl" placeholder="Hedef siteyi gir (örn: example.com)">
            <button onclick="startScan()">Taramayı Başlat</button>
        </div>
        <div id="status" class="loading"></div>
        <div id="results" class="results" style="display:none;"></div>
    </div>

    <script>
        async function startScan() {
            const url = document.getElementById('targetUrl').value.trim();
            const statusDiv = document.getElementById('status');
            const resultsDiv = document.getElementById('results');
            
            if(!url) {
                alert('Lütfen geçerli bir hedef gir!');
                return;
            }
            
            statusDiv.innerHTML = "⏳ Hedef taranıyor, hassas dosyalar ve açıklar listeleniyor...";
            resultsDiv.style.display = "none";
            resultsDiv.innerHTML = "";
            
            try {
                const response = await fetch('/api/scan', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ target: url })
                });
                const data = await response.json();
                statusDiv.innerHTML = "";
                resultsDiv.style.display = "block";
                resultsDiv.innerHTML = data.report;
            } catch (err) {
                statusDiv.innerHTML = "❌ Tarama sırasında bir hata oluştu!";
            }
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/scan", methods=["POST"])
def api_scan():
    data = request.get_json()
    target = data.get("target", "")
    report = deep_security_scan(target)
    return jsonify({"report": report})

# --- KAPSAMLI TARAMA VE LİSTELEME MOTORU ---
def deep_security_scan(target_url):
    if not target_url.startswith("http"):
        target_url = f"https://{target_url}"
        
    parsed = urllib.parse.urlparse(target_url)
    domain = parsed.netloc
    report = f"🎯 HEDEF ANALİZ RAPORU: {target_url}\n" + "—" * 40 + "\n\n"
    
    # 1. IP ve Ağ Bilgisi
    try:
        ip = socket.gethostbyname(domain)
        report += f"[i] Sunucu IP Adresi: {ip}\n"
    except Exception:
        report += "[!] Sunucu IP adresi çözümlenemedi.\n"

    # 2. SSL Durumu
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                issuer = dict(x[0] for x in cert.get('issuer', []))
                report += f"[+] SSL Sertifikası: Aktif ({issuer.get('organizationName', 'Bilinmiyor')})\n"
    except Exception:
        report += "[!] SSL bağlantı uyarısı veya zayıf sertifika.\n"

    # 3. HTTP Güvenlik Başlıkları
    try:
        response = requests.get(target_url, timeout=6, verify=False, headers={"User-Agent": "Mozilla/5.0"})
        headers = response.headers
        report += f"[+] HTTP Durum Kodu: {response.status_code}\n"
        report += f"[+] Sunucu Yazılımı: {headers.get('Server', 'Gizlenmiş')}\n"
        
        missing = [h for h in ["X-Frame-Options", "X-Content-Type-Options", "Strict-Transport-Security", "Content-Security-Policy"] if h not in headers]
        if missing:
            report += f"[!] Eksik Güvenlik Başlıkları: {', '.join(missing)}\n"
    except Exception:
        report += "[!] Ana dizine HTTP isteği atılamadı.\n"

    # 4. ERİŞİLEBİLİR DOSYALARI VE LİNKLERİ LİSTELEME (Fuzzing)
    report += "\n📂 ERİŞİLEBİLİRLİK VE DOSYA TARAMA SONUÇLARI:\n"
    sensitive_paths = [
        "/robots.txt", "/sitemap.xml", "/.env", "/config.json", "/config.php",
        "/database.sql", "/backup.sql", "/db.bak", "/dump.sql", "/admin/",
        "/phpmyadmin/", "/wp-login.php", "/api/v1/users", "/server-status",
        "/uploads/", "/assets/", "/backup/", "/db/", "/old/", "/test.txt"
    ]
    
    found_count = 0
    for path in sensitive_paths:
        test_url = f"{target_url.rstrip('/')}{path}"
        try:
            r = requests.get(test_url, timeout=3, verify=False, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                report += f"  🚨 [ERİŞİLEBİLİR - 200 OK] {test_url}\n"
                found_count += 1
            elif r.status_code == 403:
                report += f"  🔒 [YASAKLI - 403] {path} (Mevcut ama kilitli)\n"
        except:
            pass
            
    if found_count == 0:
        report += "  - Doğrudan açıkta bulunan kritik dosya eşleşmesi saptanamadı.\n"
    else:
        report += f"\n  -> Toplam {found_count} adet erişilebilir hassas yol/dosya tespit edildi!\n"

    # 5. SQL Enjeksiyon / Zafiyet Testi
    report += "\n🔍 ZAFİYET VE PARAMETRE ANALİZİ:\n"
    try:
        test_param_url = f"{target_url}/?id=1"
        r_test = requests.get(test_param_url, timeout=4, verify=False)
        if any(err in r_test.text.lower() for err in ["sql syntax", "mysql", "syntax error", "ora-", "postgresql"]):
            report += "  🚨 KRİTİK: Veritabanı hata mesajı yakalandı! Potansiyel SQL Injection açığı bulunuyor.\n"
        else:
            report += "  - Standart parametre testlerinde açık hata dönmedi.\n"
    except:
        report += "  - Parametre analizi atlandı.\n"

    report += "\n" + "—" * 40 + "\n🏁 TARAMA TAMAMLANDI."
    return report

def send_telegram_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram mesaj hatası: {e}")

# --- TELEGRAM BOT DÖNGÜSÜ ---
def run_telegram_bot():
    print("Telegram bot polling başlatıldı...")
    offset = 0
    while True:
        try:
            response = requests.get(f"{BASE_URL}/getUpdates", params={"offset": offset, "timeout": 30}, timeout=35)
            if response.status_code == 200:
                data = response.json()
                for result in data.get("result", []):
                    offset = result["update_id"] + 1
                    message = result.get("message")
                    if not message or "text" not in message:
                        continue
                        
                    chat_id = message["chat"]["id"]
                    text = message["text"].strip()
                    
                    if text.startswith("/start"):
                        send_telegram_message(
                            chat_id, 
                            "🚀 **Pro Recon Bot & Panel Aktif!**\n\n"
                            "İster Telegram'dan `/scan siteadi.com` yaz, ister kurduğumuz Web Paneline girerek siteleri tarayıp erişilebilir dosyaları anında ekranda listelet kanka!"
                        )
                    elif text.startswith("/scan"):
                        parts = text.split(maxsplit=1)
                        if len(parts) < 2:
                            send_telegram_message(chat_id, "⚠️ Lütfen hedef site gir!\nÖrnek: `/scan example.com`")
                            continue
                            
                        target = parts[1].strip()
                        send_telegram_message(chat_id, f"⏳ `{target}` taranıyor, erişilebilir dosyalar listeleniyor...")
                        
                        scan_result = deep_security_scan(target)
                        if len(scan_result) > 4000:
                            scan_result = scan_result[:4000] + "\n\n... (Rapor çok uzun olduğu için kesildi)"
                        send_telegram_message(chat_id, f"```\n{scan_result}\n```")
        except Exception as e:
            print(f"Telegram polling hatası: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # Telegram botunu arka planda thread olarak çalıştırıyoruz
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    
    # Flask Web Sunucusunu ana akışta başlatıyoruz (Render bu portu dinler)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
