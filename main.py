import os
import time
import socket
import ssl
import urllib.parse
import requests
import threading
import subprocess
import re
from bs4 import BeautifulSoup
from flask import Flask, render_template_string, request, jsonify, Response, send_file
from datetime import datetime
from fpdf import FPDF
import io

# --- ÇEVRE DEĞİŞKENLERİ ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "9082287913:AAEw9lMwKXfRTGf4LzQiF1UEgLZDHzNuc8o")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

SITE_DATABASE = []
NOTIFY_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Linux Red Team Operations & Visual Recon Center</title>
    <style>
        body { background-color: #0b0f19; color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; }
        .container { max-width: 1250px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.6); }
        h1 { color: #38bdf8; text-align: center; margin-bottom: 25px; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; border-bottom: 2px solid #334155; padding-bottom: 10px; }
        .tab-btn { background: #334155; color: #cbd5e1; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; transition: 0.2s; }
        .tab-btn.active { background: #0284c7; color: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .form-group { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
        input[type="text"], textarea { padding: 14px; border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: #fff; font-size: 15px; }
        textarea { resize: vertical; height: 100px; font-family: monospace; }
        button { padding: 14px 24px; background: #0284c7; color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; transition: 0.2s; font-weight: bold; }
        button:hover { background: #0369a1; }
        button.secondary { background: #0d9488; }
        button.success { background: #16a34a; }
        button.danger { background: #dc2626; }
        .actions { display: flex; gap: 10px; margin-top: 15px; display: none; }
        .terminal { background: #000; color: #34d399; padding: 20px; border-radius: 8px; border: 1px solid #334155; white-space: pre-wrap; font-family: 'Courier New', Courier, monospace; margin-top: 20px; max-height: 500px; overflow-y: auto; font-size: 13px; line-height: 1.5; }
        .loading { color: #facc15; font-style: italic; font-weight: bold; font-size: 15px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; background: #0f172a; border-radius: 8px; overflow: hidden; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #334155; font-size: 14px; }
        th { background: #0284c7; color: white; }
        tr:hover { background: #1e293b; }
        a.file-link { color: #38bdf8; text-decoration: underline; font-weight: bold; }
        .thumb { width: 100px; height: 60px; object-fit: cover; border-radius: 4px; border: 1px solid #475569; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🐧 Linux Red Team Operations & Visual Recon Center</h1>
        
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('scanTab')">🚀 Canlı Keşif & Fuzzing</button>
            <button class="tab-btn" onclick="switchTab('dataTab')" id="dataTabBtn">📁 Site Verileri & Görsel Arşiv</button>
        </div>

        <!-- Canlı Tarama Sekmesi -->
        <div id="scanTab" class="tab-content active">
            <div class="form-group">
                <label><b>Hedef Site:</b></label>
                <input type="text" id="targetUrl" placeholder="Hedef siteyi gir (örn: example.com)">
            </div>
            <div class="form-group">
                <label><b>Özel Kelime Listesi (Wordlist - Her satıra bir yol):</b></label>
                <textarea id="customWordlist" placeholder="/admin/&#10;/secret.php&#10;/.env&#10;/backup.zip"></textarea>
            </div>
            <button onclick="startScan()">Linux Terminal Taramasını Başlat</button>
            
            <div id="status" class="loading" style="margin-top: 15px;"></div>
            
            <div class="actions" id="actionButtons">
                <button class="secondary" onclick="downloadReport('txt')">📥 Rapor TXT İndir</button>
                <button class="danger" onclick="downloadReport('pdf')">📄 Profesyonel PDF İndir</button>
                <button class="success" onclick="sendToTelegram()">📤 Telegram'a Gönder</button>
            </div>

            <div id="results" class="terminal" style="display:none;"></div>
        </div>

        <!-- Site Verileri Arşiv Sekmesi -->
        <div id="dataTab" class="tab-content">
            <h3>📊 Otomatik İzlenen Hedefler ve Görsel Keşif (Visual Recon)</h3>
            <div id="databaseTableContainer">
                <p style="color: #94a3b8;">Henüz kaydedilmiş site verisi yok.</p>
            </div>
        </div>
    </div>

    <script>
        let currentReportText = "";
        let lastTarget = "";

        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
            if(tabId === 'dataTab') { loadSiteDatabase(); }
        }

        async function startScan() {
            const url = document.getElementById('targetUrl').value.trim();
            const wordlist = document.getElementById('customWordlist').value.trim();
            const statusDiv = document.getElementById('status');
            const resultsDiv = document.getElementById('results');
            const actionButtons = document.getElementById('actionButtons');
            
            if(!url) { alert('Lütfen geçerli bir hedef gir!'); return; }
            lastTarget = url;
            
            statusDiv.innerHTML = "root@red-team-box:~# executing visual-recon, fuzzing & grading suite...";
            resultsDiv.style.display = "none";
            actionButtons.style.display = "none";
            resultsDiv.innerHTML = "";
            
            try {
                const response = await fetch('/api/scan', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ target: url, wordlist: wordlist })
                });
                const data = await response.json();
                statusDiv.innerHTML = "";
                resultsDiv.style.display = "block";
                resultsDiv.innerHTML = data.report;
                currentReportText = data.report;
                actionButtons.style.display = "flex";
            } catch (err) {
                statusDiv.innerHTML = "❌ [HATA] Linux alt sistem komutu yürütülemedi!";
            }
        }

        async function loadSiteDatabase() {
            const res = await fetch('/api/all-data');
            const data = await res.json();
            const container = document.getElementById('databaseTableContainer');
            
            if(data.database.length === 0) {
                container.innerHTML = "<p style='color: #94a3b8;'>Veritabanında kayıtlı veri bulunmuyor.</p>";
                return;
            }

            let html = `<table>
                <thead>
                    <tr>
                        <th>Görsel Önizleme</th>
                        <th>Son Kontrol</th>
                        <th>Hedef Site</th>
                        <th>WAF</th>
                        <th>Not</th>
                        <th>Dosyalar & PDF</th>
                    </tr>
                </thead>
                <tbody>`;
            
            data.database.forEach(item => {
                let fileLinks = item.files.length > 0 ? item.files.map(f => `<a class="file-link" href="/api/view-file?url=${encodeURIComponent(f)}" target="_blank">${f}</a>`).join('<br>') : 'Yok';
                let thumbUrl = `https://image.thum.io/get/width/200/crop/150/${item.target}`;
                
                html += `<tr>
                    <td><img src="${thumbUrl}" class="thumb" alt="Preview" onerror="this.src='https://via.placeholder.com/100x60?text=No+Preview'"></td>
                    <td>${item.time}</td>
                    <td><b>${item.target}</b></td>
                    <td>${item.waf}</td>
                    <td>${item.grade}</td>
                    <td>${fileLinks}<br><a href="/api/download-pdf?target=${encodeURIComponent(item.target)}" style="color: #f87171; font-weight: bold; text-decoration: underline;" target="_blank">📥 PDF İndir</a></td>
                </tr>`;
            });
            html += `</tbody></table>`;
            container.innerHTML = html;
        }

        function downloadReport(type) {
            if(type === 'txt') {
                const blob = new Blob([currentReportText], { type: 'text/plain' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'red_team_report.txt';
                a.click();
            } else if(type === 'pdf') {
                if(!lastTarget) { alert('Önce bir tarama yapmalısın!'); return; }
                window.open(`/api/download-pdf?target=${encodeURIComponent(lastTarget)}`, '_blank');
            }
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
    custom_wordlist = data.get("wordlist", "")
    
    custom_paths = [p.strip() for p in custom_wordlist.splitlines() if p.strip()]
    report, record = red_team_comprehensive_recon(target, custom_paths)
    
    existing = next((item for item in SITE_DATABASE if item["target"] == record["target"]), None)
    if existing: SITE_DATABASE.remove(existing)
    SITE_DATABASE.insert(0, record)
    if len(SITE_DATABASE) > 20: SITE_DATABASE.pop()
    
    return jsonify({"report": report})

@app.route("/api/all-data")
def api_all_data():
    return jsonify({"database": SITE_DATABASE})

@app.route("/api/view-file")
def api_view_file():
    file_url = request.args.get("url", "")
    try:
        r = requests.get(file_url, timeout=5, verify=False, headers={"User-Agent": "Mozilla/5.0"})
        return Response(r.text, mimetype="text/plain")
    except Exception as e:
        return f"Dosya içeriği okunamadı: {str(e)}", 500

@app.route("/api/download-pdf")
def api_download_pdf():
    target = request.args.get("target", "")
    record = next((item for item in SITE_DATABASE if item["target"] == target), None)
    
    report_content = record["full_report"] if record else f"Red Team Recon Report for {target}\nNo detailed report found in cache."
    
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 12)
            self.set_text_color(2, 132, 199)
            self.cell(0, 10, 'Linux Red Team - Professional Security Report', 0, 1, 'C')
            self.ln(5)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, f'Generated by Red Team Operations Center', 0, 0, 'C')

    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Courier', '', 9)
    pdf.set_text_color(30, 41, 59)
    
    safe_text = report_content.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 5, safe_text)
    
    pdf_output = pdf.output(dest='S').encode('latin-1')
    return send_file(
        io.BytesIO(pdf_output),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'recon_report_{urllib.parse.urlparse(target).netloc or target}.pdf'
    )

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

def background_monitor_loop():
    while True:
        time.sleep(3600)
        for item in SITE_DATABASE:
            try:
                target = item["target"]
                _, new_record = red_team_comprehensive_recon(target, [])
                old_files = set(item["files"])
                new_files = set(new_record["files"])
                diff = new_files - old_files
                if diff and NOTIFY_CHAT_ID:
                    alert_msg = f"🚨 *OTOMATİK ALARM: Yeni Açık/Dosya Bulundu!*\nHedef: `{target}`\nYeni Dosyalar:\n" + "\n".join(diff)
                    requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": NOTIFY_CHAT_ID, "text": alert_msg, "parse_mode": "Markdown"}, timeout=10)
                item["files"] = new_record["files"]
                item["time"] = new_record["time"]
            except: pass

def detect_waf(headers, cookies_str):
    header_str = str(headers).lower()
    if "cf-ray" in header_str or "cloudflare" in header_str: return "Cloudflare WAF 🛡️"
    elif "incap_ses" in cookies_str or "incapsula" in header_str: return "Incapsula WAF 🛡️"
    elif "akamai" in header_str: return "Akamai WAF 🛡️"
    elif "awsalb" in cookies_str: return "AWS WAF 🛡️"
    elif "server" in headers and "angie" in headers["server"].lower(): return "Angie Web Server"
    return "Standart Koruma"

def calculate_security_grading(headers, is_https):
    score = 100
    deductions = []
    if not is_https:
        score -= 30
        deductions.append("HTTPS aktif değil (-30)")
    for h in ["Strict-Transport-Security", "Content-Security-Policy", "X-Frame-Options", "X-Content-Type-Options"]:
        if h not in headers:
            score -= 15
            deductions.append(f"Eksik başlık: {h} (-15)")
    if score >= 90: grade = "A (Güvenli)"
    elif score >= 75: grade = "B (İyi)"
    elif score >= 60: grade = "C (Orta)"
    else: grade = "F (Riskli)"
    return grade, score, deductions

def run_linux_command(cmd):
    try:
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=5)
        return output.decode('utf-8', errors='ignore')
    except Exception as e:
        return f"Komut çalıştırılamadı: {str(e)}"

def banner_grabbing(domain, open_ports):
    banners = {}
    for port in open_ports:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.5)
            s.connect((domain, port))
            if port in [80, 443, 8080, 8443]:
                s.send(f"HEAD / HTTP/1.1\r\nHost: {domain}\r\nUser-Agent: Mozilla/5.0\r\n\r\n".encode())
            data = s.recv(1024).decode('utf-8', errors='ignore')
            if data: banners[port] = data.split('\r\n')[0]
            s.close()
        except: pass
    return banners

def analyze_javascript_endpoints(target_url, html_content):
    found = set()
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup.find_all('script'):
            src = script.get('src')
            if src:
                if src.startswith('http'): s_url = src
                elif src.startswith('/'):
                    p = urllib.parse.urlparse(target_url)
                    s_url = f"{p.scheme}://{p.netloc}{src}"
                else: continue
                try:
                    js_res = requests.get(s_url, timeout=2, verify=False)
                    if js_res.status_code == 200:
                        matches = re.findall(r'["\'](/api/[a-zA-Z0-9_/.-]+|/v[1-9]/[a-zA-Z0-9_/.-]+)["\']', js_res.text)
                        for m in matches: found.add(m)
                except: pass
    except: pass
    return list(found)

def red_team_comprehensive_recon(target_url, custom_paths=[]):
    if not target_url.startswith("http"): target_url = f"https://{target_url}"
    is_https = target_url.startswith("https")
    parsed = urllib.parse.urlparse(target_url)
    domain = parsed.netloc or parsed.path
    domain = domain.split('/')[0]
    
    report = f"root@red-team-box:~# ./recon-suite.sh --target {target_url}\n"
    report += "=" * 65 + "\n\n"
    
    accessible_files = []
    waf_info = "Bilinmeyen"
    grade_info = "F"
    
    try:
        r = requests.get(target_url, timeout=5, verify=False, headers={"User-Agent": "Mozilla/5.0"})
        headers = r.headers
        waf_info = detect_waf(headers, str(r.cookies.get_dict()))
        grade_info, score, deductions = calculate_security_grading(headers, is_https)
        
        report += f"[+] WAF Tespiti: {waf_info}\n"
        report += f"[+] Güvenlik Puanı: {grade_info} ({score}/100)\n"
        report += "-" * 45 + "\n"
    except Exception as e:
        report += f"[!] HTTP Bağlantı Uyarısı: {str(e)}\n"

    report += "[*] Çözümleniyor: nslookup...\n"
    report += run_linux_command(f"nslookup {domain}") + "\n" + "-" * 40 + "\n"

    report += "[*] Port Taraması ve Banner Grabbing...\n"
    common_ports = [21, 22, 80, 443, 3306, 8080, 8443]
    open_ports = []
    for p in common_ports:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            if s.connect_ex((domain, p)) == 0: open_ports.append(p)
            s.close()
        except: pass
    report += f"  -> Açık Portlar: {open_ports}\n"
    if open_ports:
        banners = banner_grabbing(domain, open_ports)
        for port, b in banners.items(): report += f"     Port {port} Banner: {b}\n"
    report += "-" * 40 + "\n"

    report += "[*] Subdomain Enumeration...\n"
    for sub in ["www", "api", "admin", "test", "dev", "panel", "login"]:
        s_dom = f"{sub}.{domain}"
        try:
            ip = socket.gethostbyname(s_dom)
            report += f"  [FOUND] {s_dom} -> {ip}\n"
        except: pass
    report += "-" * 40 + "\n"

    report += "[*] JavaScript API Endpoint Taraması...\n"
    try:
        endpoints = analyze_javascript_endpoints(target_url, r.text)
        if endpoints:
            for ep in endpoints[:10]: report += f"  [API] {ep}\n"
        else: report += "  -> Harici API endpoint bulunamadı.\n"
    except: pass
    report += "-" * 40 + "\n"

    report += "[*] Hassas Dosya ve Dizin Taraması (Custom Wordlist Fuzzing)...\n"
    default_paths = [
        "/robots.txt", "/sitemap.xml", "/.env", "/config.json", "/config.php",
        "/database.sql", "/backup.sql", "/db.bak", "/admin/", "/phpmyadmin/", "/db/"
    ]
    all_paths = list(set(default_paths + custom_paths))
    
    for path in all_paths:
        t_url = f"{target_url.rstrip('/')}{path}"
        try:
            res = requests.get(t_url, timeout=3, verify=False, headers={"User-Agent": "Mozilla/5.0"})
            if res.status_code == 200:
                report += f"  [ALERT - 200 OK] {t_url}\n"
                accessible_files.append(t_url)
            elif res.status_code == 403:
                report += f"  [FORBIDDEN - 403] {path}\n"
        except: pass

    report += "\n" + "=" * 65 + "\nroot@red-team-box:~# Scan Completed."
    
    record = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "target": target_url,
        "waf": waf_info,
        "grade": grade_info,
        "files": accessible_files,
        "full_report": report
    }
    
    return report, record

def run_telegram_bot():
    print("Telegram bot aktif...")
    offset = 0
    while True:
        try:
            response = requests.get(f"{BASE_URL}/getUpdates", params={"offset": offset, "timeout": 30}, timeout=35)
            if response.status_code == 200:
                for result in response.json().get("result", []):
                    offset = result["update_id"] + 1
                    msg = result.get("message")
                    if not msg or "text" not in msg: continue
                    chat_id = msg["chat"]["id"]
                    text = msg["text"].strip()
                    if text.startswith("/scan"):
                        parts = text.split(maxsplit=1)
                        if len(parts) < 2: continue
                        target = parts[1].strip()
                        requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": f"⏳ `{target}` taranıyor...", "parse_mode": "Markdown"})
                        report, _ = red_team_comprehensive_recon(target, [])
                        if len(report) > 4000: report = report[:4000] + "\n...(Kısaltıldı)"
                        requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": f"```\n{report}\n```", "parse_mode": "Markdown"})
        except: time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_telegram_bot, daemon=True).start()
    threading.Thread(target=background_monitor_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
