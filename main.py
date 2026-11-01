import os
import time
import socket
import ssl
import urllib.parse
import requests
import threading
import subprocess
from flask import Flask, render_template_string, request, jsonify
from datetime import datetime

# --- ÇEVRE DEĞİŞKENLERİ ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "9082287913:AAEw9lMwKXfRTGf4LzQiF1UEgLZDHzNuc8o")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

SCAN_HISTORY = []

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>A-Z Ultimate Recon & Security Command Center</title>
    <style>
        body { background-color: #0b0f19; color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; }
        .container { max-width: 1100px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.6); }
        h1 { color: #38bdf8; text-align: center; margin-bottom: 25px; }
        .form-group { display: flex; gap: 10px; margin-bottom: 20px; }
        input[type="text"] { flex: 1; padding: 14px; border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: #fff; font-size: 16px; }
        button { padding: 14px 24px; background: #0284c7; color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; transition: 0.2s; font-weight: bold; }
        button:hover { background: #0369a1; }
        button.secondary { background: #0d9488; }
        button.secondary:hover { background: #0f766e; }
        button.success { background: #16a34a; }
        button.success:hover { background: #15803d; }
        .actions { display: flex; gap: 10px; margin-top: 15px; display: none; }
        .results { background: #0f172a; padding: 20px; border-radius: 8px; border: 1px solid #334155; white-space: pre-wrap; font-family: monospace; margin-top: 20px; max-height: 500px; overflow-y: auto; font-size: 13px; line-height: 1.5; color: #34d399; }
        .loading { color: #facc15; font-style: italic; font-weight: bold; font-size: 15px; }
        .history-section { margin-top: 30px; background: #0f172a; padding: 15px; border-radius: 8px; border: 1px solid #334155; }
        .history-item { padding: 8px 0; border-bottom: 1px solid #1e293b; display: flex; justify-content: space-between; align-items: center; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ A-Z Ultimate Linux Recon & Security Center</h1>
        <div class="form-group">
            <input type="text" id="targetUrl" placeholder="Hedef siteyi gir (örn: example.com)">
            <button onclick="startScan()">A-Z Kapsamlı Taramayı Başlat</button>
        </div>
        <div id="status" class="loading"></div>
        
        <div class="actions" id="actionButtons">
            <button class="secondary" onclick="downloadReport()">📥 Raporu TXT İndir</button>
            <button class="success" onclick="sendToTelegram()">📤 Telegram'a Gönder</button>
        </div>

        <div id="results" class="results" style="display:none;"></div>

        <div class="history-section">
            <h3>📜 Son Taramalar (Geçmiş)</h3>
            <div id="historyList">Tarama geçmişi yükleniyor...</div>
        </div>
    </div>

    <script>
        let currentReportText = "";

        async function startScan() {
            const url = document.getElementById('targetUrl').value.trim();
            const statusDiv = document.getElementById('status');
            const resultsDiv = document.getElementById('results');
            const actionButtons = document.getElementById('actionButtons');
            
            if(!url) { alert('Lütfen geçerli bir hedef gir!'); return; }
            
            statusDiv.innerHTML = "⏳ Linux altyapısı ve komutları çalıştırılıyor (WHOIS, DNS, Subdomain, Portlar ve A-Z Dosyalar taranıyor)...";
            resultsDiv.style.display = "none";
            actionButtons.style.display = "none";
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
                currentReportText = data.report;
                actionButtons.style.display = "flex";
                loadHistory();
            } catch (err) {
                statusDiv.innerHTML = "❌ Tarama sırasında hata oluştu!";
            }
        }

        async function downloadReport() {
            const blob = new Blob([currentReportText], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'a_z_recon_report.txt';
            a.click();
        }

        async function sendToTelegram() {
            const chatId = prompt("Telegram Chat ID giriniz:");
            if(!chatId) return;
            
            const res = await fetch('/api/telegram-send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ chat_id: chatId, report: currentReportText })
            });
            const data = await res.json();
            alert(data.status);
        }

        async function loadHistory() {
            const res = await fetch('/api/history');
            const data = await res.json();
            const historyList = document.getElementById('historyList');
            if(data.history.length === 0) { historyList.innerHTML = "Henüz tarama yapılmadı."; return; }
            historyList.innerHTML = data.history.map(h => 
                `<div class="history-item"><span>🌐 <b>${h.target}</b></span> <span style="color: #94a3b8;">${h.time}</span></div>`
            ).join('');
        }

        loadHistory();
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
    report = az_comprehensive_recon(target)
    
    SCAN_HISTORY.insert(0, {"target": target, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    if len(SCAN_HISTORY) > 10: SCAN_HISTORY.pop()
    
    return jsonify({"report": report})

@app.route("/api/history")
def api_history():
    return jsonify({"history": SCAN_HISTORY})

@app.route("/api/telegram-send", methods=["POST"])
def api_telegram_send():
    data = request.get_json()
    chat_id = data.get("chat_id")
    report = data.get("report")
    if len(report) > 4000: report = report[:4000] + "\n...(Kısaltıldı)"
    
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": f"```\n{report}\n```", "parse_mode": "Markdown"}
    res = requests.post(url, json=payload, timeout=10)
    return jsonify({"status": "✅ Rapor Telegram'a gönderildi!" if res.status_code == 200 else "❌ Gönderim başarısız."})

# --- LINUX & PYTHON A-Z KEŞİF MOTORU ---
def run_linux_command(cmd):
    try:
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=5)
        return output.decode('utf-8', errors='ignore')
    except Exception as e:
        return f"Çalıştırılamadı / Bulunamadı: {str(e)}"

def az_comprehensive_recon(target_url):
    if not target_url.startswith("http"):
        target_url = f"https://{target_url}"
        
    parsed = urllib.parse.urlparse(target_url)
    domain = parsed.netloc or parsed.path
    domain = domain.split('/')[0]
    
    report = f"🎯 A-Z KAPSAMLI LİNUX & GÜVENLİK KEŞİF RAPORU: {target_url}\n" + "—" * 60 + "\n\n"
    
    # 1. IP ve Nslookup (Linux Komutu)
    report += "🌐 1. DNS & IP BİLGİLERİ (Linux Nslookup):\n"
    nslookup_out = run_linux_command(f"nslookup {domain}")
    report += f"{nslookup_out}\n" + "—" * 40 + "\n"

    # 2. Whois Bilgileri (Linux Whois)
    report += "📋 2. WHOIS KAYIT ANALİZİ:\n"
    whois_out = run_linux_command(f"whois {domain}")
    if len(whois_out) > 1500: whois_out = whois_out[:1500] + "\n[Whois çıktısı kısaltıldı...]"
    report += f"{whois_out}\n" + "—" * 40 + "\n"

    # 3. Açık Port Taraması
    report += "🔍 3. KRİTİK PORT KONTROLÜ:\n"
    common_ports = [21, 22, 80, 443, 3306, 8080, 8443, 2082, 2083]
    open_ports = []
    for p in common_ports:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            if s.connect_ex((domain, p)) == 0:
                open_ports.append(p)
            s.close()
        except:
            pass
    report += f"  -> Açık Tespit Edilen Portlar: {open_ports if open_ports else 'Standart dışı açık port yok.'}\n" + "—" * 40 + "\n"

    # 4. Alt Alan Adı (Subdomain) Taraması
    report += "🌍 4. ALT ALAN ADI (SUBDOMAIN) TARAMASI:\n"
    subs = ["www", "api", "admin", "test", "dev", "panel", "login", "mail", "shop", "portal", "vpn", "cpanel"]
    found_subs = 0
    for sub in subs:
        sub_dom = f"{sub}.{domain}"
        try:
            ip_sub = socket.gethostbyname(sub_dom)
            report += f"  ✅ Bulundu: {sub_dom} ({ip_sub})\n"
            found_subs += 1
        except:
            pass
    if found_subs == 0: report += "  - Aktif yaygın subdomain eşleşmedi.\n"
    report += "—" * 40 + "\n"

    # 5. SSL Sertifika Detayları
    report += "🔒 5. SSL / TLS SERTİFİKA ANALİZİ:\n"
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=4) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                issuer = dict(x[0] for x in cert.get('issuer', []))
                report += f"  [+] Sertifika Sağlayıcı: {issuer.get('organizationName', 'Bilinmiyor')}\n"
                report += f"  [+] Sürüm / Versiyon: {cert.get('version')}\n"
    except Exception as e:
        report += f"  [!] SSL bağlantı hatası: {str(e)}\n"
    report += "—" * 40 + "\n"

    # 6. HTTP Başlıkları ve Teknoloji Tespiti
    report += "🛡️ 6. HTTP BAŞLIKLARI & WEB TEKNOLOJİSİ:\n"
    try:
        r = requests.get(target_url, timeout=5, verify=False, headers={"User-Agent": "Mozilla/5.0"})
        report += f"  [+] Durum Kodu: {r.status_code}\n"
        report += f"  [+] Sunucu Yazılımı: {r.headers.get('Server', 'Gizlenmiş')}\n"
        report += f"  [+] Güç Kaynağı / Teknoloji: {r.headers.get('X-Powered-By', 'Bilinmiyor')}\n"
    except:
        report += "  [!] Ana dizine HTTP isteği atılamadı.\n"
    report += "—" * 40 + "\n"

    # 7. A'dan Z'ye Genişletilmiş Hassas Dosya / Dizin Fuzzing
    report += "📂 7. A-Z HASSAS DOSYA VE DİZİN TARAMASI:\n"
    az_paths = [
        "/robots.txt", "/sitemap.xml", "/.env", "/config.json", "/config.php",
        "/database.sql", "/backup.sql", "/db.bak", "/dump.sql", "/admin/",
        "/phpmyadmin/", "/wp-login.php", "/api/v1/users", "/server-status",
        "/uploads/", "/assets/", "/backup/", "/db/", "/old/", "/test.txt",
        "/.git/config", "/composer.json", "/package.json", "/web.config"
    ]
    
    found_paths = 0
    for path in az_paths:
        test_url = f"{target_url.rstrip('/')}{path}"
        try:
            res = requests.get(test_url, timeout=3, verify=False, headers={"User-Agent": "Mozilla/5.0"})
            if res.status_code == 200:
                report += f"  🚨 [200 OK - ERİŞİLEBİLİR] {test_url}\n"
                found_paths += 1
            elif res.status_code == 403:
                report += f"  🔒 [403 YASAKLI] {path}\n"
        except:
            pass
            
    if found_paths == 0:
        report += "  - Doğrudan açıkta kritik dosya tespit edilemedi (WAF / Koruma aktif).\n"
    else:
        report += f"\n  -> Toplam {found_paths} adet erişilebilir dosya yakalandı!\n"

    report += "\n" + "—" * 60 + "\n🏁 A-Z KEŞİF VE TARAMA TAMAMLANDI."
    return report

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
                    if not message or "text" not in message: continue
                        
                    chat_id = message["chat"]["id"]
                    text = message["text"].strip()
                    
                    if text.startswith("/start"):
                        send_telegram_message(chat_id, "🛡️ **A-Z Linux Recon Bot Aktif!**\n\nKullanım:\n`/scan siteadi.com`")
                    elif text.startswith("/scan"):
                        parts = text.split(maxsplit=1)
                        if len(parts) < 2:
                            send_telegram_message(chat_id, "⚠️ Lütfen hedef gir! Örnek: `/scan example.com`")
                            continue
                        target = parts[1].strip()
                        send_telegram_message(chat_id, f"⏳ `{target}` için A-Z Linux altyapılı tarama başlatıldı...")
                        res = az_comprehensive_recon(target)
                        if len(res) > 4000: res = res[:4000] + "\n...(Kısaltıldı)"
                        send_telegram_message(chat_id, f"```\n{res}\n```")
        except:
            time.sleep(5)

def send_telegram_message(chat_id, text):
    try:
        requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except:
        pass

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
