import os
import time
import socket
import ssl
import urllib.parse
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- BOT TOKEN ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "9082287913:AAEw9lMwKXfRTGf4LzQiF1UEgLZDHzNuc8o")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# --- RENDER İÇİN HAFİF WEB SUNUCUSU (Port Açık Tutma) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Recon Bot is active and running 24/7!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    print(f"Web sunucu {port} portunda başlatıldı.")
    server.serve_forever()

# --- KAPSAMLI TARAMA MOTORU ---
def deep_security_scan(target_url):
    if not target_url.startswith("http"):
        target_url = f"https://{target_url}"
        
    parsed = urllib.parse.urlparse(target_url)
    domain = parsed.netloc
    report = f"🎯 **KAPSAMLI HEDEF ANALİZ RAPORU**\n`{target_url}`\n" + "—" * 30 + "\n\n"
    
    # 1. IP ve Ağ Bilgisi
    try:
        ip = socket.gethostbyname(domain)
        report += f"🌐 **Sunucu IP:** `{ip}`\n"
    except Exception:
        report += "🌐 **Sunucu IP:** Çözümlenemedi!\n"

    # 2. SSL / TLS Güvenlik Analizi
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                issuer = dict(x[0] for x in cert.get('issuer', []))
                report += f"🔒 **SSL Sertifikası:** Aktif ({issuer.get('organizationName', 'Bilinmiyor')})\n"
    except Exception:
        report += "⚠️ **SSL Uyarısı:** Güvenli bağlantı kurulamadı veya sertifika zayıf.\n"

    # 3. HTTP Güvenlik Başlıkları Kontrolü
    try:
        response = requests.get(target_url, timeout=6, verify=False, headers={"User-Agent": "Mozilla/5.0"})
        headers = response.headers
        report += f"📊 **HTTP Status Code:** `{response.status_code}`\n"
        report += f"🛡️ **Web Server / Teknoloji:** `{headers.get('Server', 'Gizlenmiş')}`\n"
        
        missing_sec = [h for h in ["X-Frame-Options", "X-Content-Type-Options", "Strict-Transport-Security", "Content-Security-Policy"] if h not in headers]
        if missing_sec:
            report += f"⚠️ **Eksik Güvenlik Başlıkları:** {', '.join(missing_sec)}\n"
    except Exception:
        report += "❌ **Bağlantı Hatası:** Ana dizine erişilemedi.\n"

    # 4. Hassas Dosya ve Veritabanı Yedek Taraması
    report += "\n📂 **Hassas Dosya & Veritabanı Taraması:**\n"
    sensitive_paths = [
        "/robots.txt", "/sitemap.xml", "/.env", "/config.json", "/config.php",
        "/database.sql", "/backup.sql", "/db.bak", "/dump.sql", "/admin/",
        "/phpmyadmin/", "/wp-login.php", "/api/v1/users", "/server-status"
    ]
    
    found_paths = 0
    for path in sensitive_paths:
        test_url = f"{target_url.rstrip('/')}{path}"
        try:
            r = requests.get(test_url, timeout=3, verify=False, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                report += f"  🚨 **[BULUNDU - 200]** `{path}` (Erişilebilir!)\n"
                found_paths += 1
            elif r.status_code == 403:
                report += f"  🔒 **[403 Yasaklı]** `{path}` (Korunuyor ama var)\n"
        except:
            pass
            
    if found_paths == 0:
        report += "  ✅ Kritik hassas dosya eşleşmesi bulunamadı.\n"

    # 5. Zafiyet / SQL Enjeksiyon Vektör Testi
    report += "\n🔍 **Zafiyet Vektör Analizi (Parametre / Giriş):**\n"
    try:
        test_param_url = f"{target_url}/?id=1"
        r_test = requests.get(test_param_url, timeout=4, verify=False)
        if any(err in r_test.text.lower() for err in ["sql syntax", "mysql", "syntax error", "ora-", "postgresql"]):
            report += "  🚨 **KRİTİK UYARI:** Veritabanı hata mesajı yakalandı! Potansiyel SQL Injection açığı olabilir.\n"
        else:
            report += "  ✅ Standart parametrelerde açık SQL hatası dönmedi.\n"
    except:
        report += "  ℹ️ Parametre testleri atlandı.\n"

    report += "\n" + "—" * 30 + "\n🏁 **Tarama Tamamlandı.**"
    return report

def send_telegram_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Mesaj gönderme hatası: {e}")

# --- TELEGRAM LONG-POLLING DÖNGÜSÜ ---
def run_telegram_bot():
    print("Telegram bot polling başlatıldı (Saf Python)...")
    offset = 0
    while True:
        try:
            response = requests.get(f"{BASE_URL}/getUpdates", params={"offset": offset, "timeout": 30}, timeout=35)
            if response.status_code == 200:
                data = response.json()
                for result in data.get("result", []):
                    offset = result["update_id"] + 1
                    message = result.get("message")
                    if not message or "text" not in message:
                        continue
                        
                    chat_id = message["chat"]["id"]
                    text = message["text"].strip()
                    
                    if text.startswith("/start"):
                        send_telegram_message(
                            chat_id, 
                            "🚀 **Profesyonel Recon & Zafiyet Tarayıcı Aktif!**\n\n"
                            "Hedef sistem üzerinde analiz başlatmak için komutu şu şekilde kullan:\n"
                            "`/scan siteadi.com`"
                        )
                    elif text.startswith("/scan"):
                        parts = text.split(maxsplit=1)
                        if len(parts) < 2:
                            send_telegram_message(chat_id, "⚠️ Lütfen taranacak bir hedef site gir!\nÖrnek: `/scan example.com`")
                            continue
                            
                        target = parts[1].strip()
                        send_telegram_message(chat_id, f"⏳ `{target}` için kapsamlı zafiyet ve veri tabanı yolu taraması başlatıldı...")
                        
                        # Taramayı çalıştır ve sonucu gönder
                        scan_result = deep_security_scan(target)
                        if len(scan_result) > 4000:
                            scan_result = scan_result[:4000] + "\n\n... (Rapor uzunluğu nedeniyle kesildi)"
                        send_telegram_message(chat_id, scan_result)
        except Exception as e:
            print(f"Polling döngüsü hatası: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # Web sunucusunu arka planda (thread) başlatıyoruz ki Render port kontrolünden geçsin
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Telegram bot döngüsünü ana akışta çalıştırıyoruz
    run_telegram_bot()
