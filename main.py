import os
import asyncio
import socket
import ssl
import urllib.parse
import requests
from fastapi import FastAPI
import uvicorn
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# --- ÇEVRE DEĞİŞKENLERİ ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "9082287913:AAEw9lMwKXfRTGf4LzQiF1UEgLZDHzNuc8o")

# --- FASTAPI (Render 7/24 Aktif Kalma Altyapısı) ---
app = FastAPI()

@app.get("/")
def home():
    return {"status": "Active", "system": "Advanced Recon & Vulnerability Engine Running"}

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
        response = requests.get(target_url, timeout=6, verify=False, headers={ "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" })
        headers = response.headers
        report += f"📊 **HTTP Status Code:** `{response.status_code}`\n"
        report += f"🛡️ **Web Server / Teknoloji:** `{headers.get('Server', 'Gizlenmiş')}`\n"
        
        missing_sec = [h for h in ["X-Frame-Options", "X-Content-Type-Options", "Strict-Transport-Security", "Content-Security-Policy"] if h not in headers]
        if missing_sec:
            report += f"⚠️ **Eksik Güvenlik Başlıkları:** {', '.join(missing_sec)}\n"
    except Exception:
        report += "❌ **Bağlantı Hatası:** Ana dizine erişilemedi.\n"

    # 4. Hassas Dosya ve Veritabanı Yedek Taraması (Sensitive Path Fuzzing)
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
            r = requests.get(test_url, timeout=3, verify=False, headers={ "User-Agent": "Mozilla/5.0" })
            if r.status_code == 200:
                report += f"  🚨 **[BULUNDU - 200]** `{path}` (Erişilebilir!)\n"
                found_paths += 1
            elif r.status_code == 403:
                report += f"  🔒 **[403 Yasaklı]** `{path}` (Korunuyor ama var)\n"
        except:
            pass
            
    if found_paths == 0:
        report += "  ✅ Kritik hassas dosya eşleşmesi bulunamadı.\n"

    # 5. Zafiyet / SQL Enjeksiyon Vektör Testi (Heuristic Check)
    report += "\n🔍 **Zafiyet Vektör Analizi (Parametre / Giriş):**\n"
    try:
        test_param_url = f"{target_url}/?id=1"
        r_test = requests.get(test_param_url, timeout=4, verify=False)
        if any(err in r_test.text.lower() for err in ["sql syntax", "mysql", "syntax error", "ora-", "postgresql"]):
            report += "  🚨 **KRİTİK UYARI:** Veritabanı hata mesajı (SQL Syntax) yakalandı! Potansiyel SQL Injection açığı olabilir.\n"
        else:
            report += "  ✅ Standart parametrelerde açık SQL hatası dönmedi.\n"
    except:
        report += "  ℹ️ Parametre testleri atlandı.\n"

    report += "\n" + "—" * 30 + "\n🏁 **Tarama Tamamlandı.**"
    return report

# --- TELEGRAM BOTU ALTYAPISI ---
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🚀 **Profesyonel Recon & Zafiyet Tarayıcı Aktif!**\n\n"
        "Hedef sistem üzerinde derinlemesine analiz başlatmak için:\n"
        "`/scan siteadi.com`"
    )

@dp.message(Command("scan"))
async def cmd_scan(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ Lütfen geçerli bir hedef adres gir!\nÖrnek: `/scan example.com`")
        return
        
    target = args[1].strip()
    status_msg = await message.answer(f"⏳ `{target}` için kapsamlı zafiyet ve veri tabanı yolu taraması başlatıldı...")
    
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, deep_security_scan, target)
    
    if len(result) > 4000:
        result = result[:4000] + "\n\n... (Rapor uzunluğu nedeniyle kesildi)"
        
    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=status_msg.message_id,
        text=result,
        parse_mode="Markdown"
    )

# --- BAŞLANGIÇ YÖNETİCİSİ ---
async def start_telegram_bot():
    print("Telegram bot polling başlatıldı...")
    await dp.start_polling(bot)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_telegram_bot())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
