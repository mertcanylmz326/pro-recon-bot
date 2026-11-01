import os
import time
import socket
import ssl
import urllib.parse
import requests
import threading
from flask import Flask, render_template_string, request, jsonify, send_file
from datetime import datetime
import io

# --- ÇEVRE DEĞİŞKENLERİ ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "9082287913:AAEw9lMwKXfRTGf4LzQiF1UEgLZDHzNuc8o")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# Tarama geçmişini geçici hafızada tutmak için liste
SCAN_HISTORY = []

# --- FLASK WEB PANELİ ---
app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Pro Recon & Security Command Center</title>
    <style>
        body { background-color: #0f172a; color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; }
        .container { max-width: 1000px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        h1 { color: #38bdf8; text-align: center; margin-bottom: 25px; }
        .form-group { display: flex; gap: 10px; margin-bottom: 20px; }
        input[type="text"] { flex: 1; padding: 12px; border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: #fff; font-size: 16px; }
        button { padding: 12px 20px; background: #0284c7; color: white; border: none; border-radius: 8px; font-size: 15px; cursor: pointer; transition: 0.2s; font-weight: bold; }
        button:hover { background: #0369a1; }
        button.secondary { background: #0d9488; }
        button.secondary:hover { background: #0f766e; }
        button.success { background: #16a34a; }
        button.success:hover { background: #15803d; }
        .actions { display: flex; gap: 10px; margin-top: 15px; display: none; }
        .results { background: #0f172a; padding: 20px; border-radius: 8px; border: 1px solid #334155; white-space: pre-wrap; font-family: monospace; margin-top: 20px; max-height: 450px; overflow-y: auto; font-size: 14px; }
        .loading { color: #facc15; font-style: italic; font-weight: bold; }
        .history-section { margin-top: 30px; background: #0f172a; padding: 15px; border-radius: 8px; border: 1px solid #334155; }
        .history-item { padding: 8px 0; border-bottom: 1px solid #1e293b; display: flex; justify-content: space-between; align-items: center; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Pro Recon & Security Command Center</h1>
        <div class="form-group">
            <input type="text" id="targetUrl" placeholder="Hedef siteyi gir (örn: example.com)">
            <button onclick="startScan()">Kapsamlı Taramayı Başlat</button>
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
            
            statusDiv.innerHTML = "⏳ Derinlemesine tarama başlatıldı (Subdomainler, Portlar, Hassas Dosyalar analiz ediliyor)...";
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
                statusDiv.innerHTML = "❌ Tarama sırasında bir hata oluştu!";
            }
        }

        async function downloadReport() {
            const blob = new Blob([currentReportText], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'recon_report.txt';
            a.click();
        }

        async function sendToTelegram() {
            const chatId = prompt("Telegram Chat ID giriniz (Kendi ID'niz):");
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
            if(data.history.length === 0) {
                historyList.innerHTML = "Henüz tarama yapılmadı.";
                return;
            }
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
    report = comprehensive_recon(target)
    
    # Geçmişe ekle
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
    
    if len(report) > 4000: report = report[:4000] + "\n...(Rapor kısaltıldı)"
    
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": f"```\n{report}\n```", "parse_mode": "Markdown"}
    res = requests.post(url, json=payload, timeout=10)
    
    if res.status_code == 200:
        return jsonify({"status": "✅ Rapor başarıyla Telegram'a gönderildi!"})
    else:
        return jsonify({"status": "❌ Gönderim başarısız, Chat ID'yi kontrol edin."})

# --- KAPSAMLI KEŞİF VE TARAMA MOTORU ---
def check_subdomains(domain):
    common_subs = ["www", "api", "admin", "test", "dev", "panel", "login", "mail", "shop", "portal"]
    found = []
    for sub in common_subs:
        sub_domain = f"{sub}.{domain}"
        try:
            socket.gethostbyname(sub_domain)
            found.append(sub_domain)
        except:
            pass
    return found

def check_ports(domain):
    common_ports = [21, 22, 80, 443, 3306, 8080, 8443]
    open_ports = []
    for port in common_ports:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.5)
            result = s.connect_ex((domain, port))
            if result == 0:
                open_ports.append(port)
            s.close()
        except:
            pass
    return open_ports

def comprehensive_recon(target_url):
    if not target_url.startswith("http"):
        target_url = f"https://{target_url}"
        
    parsed = urllib.parse.urlparse(target_url)
    domain = parsed.netloc
    report = f"🎯 HEDEF KAPSAMLI KEŞİF RAPORU: {target_url}\n" + "—" * 45 + "\n\n"
    
    # 1. IP Adresi
    try:
        ip = socket.gethostbyname(domain)
        report += f"[i] Ana Sunucu IP: {ip}\n"
    except:
        report += "[!] IP adresi çözümlenemedi.\n"

    # 2. Açık Port Taraması
    report += "\n🔍 HIZLI PORT KONTROLÜ:\n"
    open_ports = check_ports(domain)
    if open_ports:
        report += f"  🚨 Açık Portlar Tespit Edildi: {open_ports}\n"
    else:
        report += "  - Standart kritik portlar kapalı veya filtreli.\n"

    # 3. Alt Alan Adı (Subdomain) Taraması
    report += "\n🌐 ALT ALAN ADI (SUBDOMAIN) TARAMASI:\n"
    subdomains = check_subdomains(domain)
    if subdomains:
        for sub in subdomains:
            report += f"  ✅ Aktif Subdomain: {sub}\n"
    else:
        report += "  - Yaygın subdomain eşleşmesi bulunamadı.\n"

    # 4. SSL Durumu
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=4) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                issuer = dict(x[0] for x in cert.get('issuer', []))
                report += f"\n[+] SSL Sertifikası: Aktif ({issuer.get('organizationName', 'Bilinmiyor')})\n"
    except:
        report += "\n[!] SSL kurulamadı veya sertifika zayıf.\n"

    # 5. HTTP Başlıkları
    try:
        response = requests.get(target_url, timeout=5, verify=False, headers={"User-Agent": "Mozilla/5.0"})
        headers = response.headers
        report += f"[+] HTTP Durum: {response.status_code} | Sunucu: {headers.get('Server', 'Gizlenmiş')}\n"
    except:
        report += "[!] Ana dizine HTTP bağlantısı kurulamadı.\n"

    # 6. Hassas Dosya / Dizin Fuzzing
    report += "\n📂 ERİŞİLEBİLİR DOSYA & DİZİN TARAMASI:\n"
    sensitive_paths = [
        "/robots.txt", "/sitemap.xml", "/.env", "/config.json", "/config.php",
        "/database.sql", "/backup.sql", "/db.bak", "/admin/", "/phpmyadmin/", "/uploads/"
    ]
    
    found_count = 0
    for path in sensitive_paths:
        test_url = f"{target_url.rstrip('/')}{path}"
        try:
            r = requests.get(test_url, timeout=3, verify=False, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                report += f"  🚨 [200 OK - ERİŞİLEBİLİR] {test_url}\n"
                found_count += 1
            elif r.status_code == 403:
                report += f"  🔒 [403 YASAKLI] {path}\n"
        except:
            pass
            
    if found_count == 0:
        report += "  - Doğrudan açıkta kritik dosya saptanamadı.\n"

    report += "\n" + "—" * 45 + "\n🏁 TARAMA TAMAMLANDI."
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
                        send_telegram_message(chat_id, "🚀 **Pro Recon Bot & Panel Aktif!**\n\nKomutlar:\n`/scan siteadi.com`")
                    elif text.startswith("/scan"):
                        parts = text.split(maxsplit=1)
                        if len(parts) < 2:
                            send_telegram_message(chat_id, "⚠️ Lütfen hedef gir! Örnek: `/scan example.com`")
                            continue
                        target = parts[1].strip()
                        send_telegram_message(chat_id, f"⏳ `{target}` için alt alan adı, port ve dosya taraması başlatıldı...")
                        res = comprehensive_recon(target)
                        if len(res) > 4000: res = res[:4000] + "\n...(Kısaltıldı)"
                        send_telegram_message(chat_id, f"```\n{res}\n```")
        except Exception as e:
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
