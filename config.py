# -*- coding: utf-8 -*-
import os

# ================== بيانات البوت الأساسية ==================
BOT_TOKEN = "8207472950:AAHS9FqJzNARdhSj1iBu_y1WxzFOSe7VOZs"
MIRROR_BOT_TOKEN = ""  # توكن احتياطي
API_ID = 30301641
API_HASH = "9a4144e4215946eb14540c659f173852"
ADMIN_IDS = [6056642165]

# ================== قاعدة البيانات ==================
DATABASE_NAME = "data.db"
ENCRYPTION_KEY = "mysecretkeymustbe32byteslong!"  # 32 حرفاً

# ================== حدود المستخدم ==================
MAX_NUMBERS_PER_USER = 5
MAX_ADS_PER_USER = 20

# ================== إعدادات السيرفر ==================
MAX_LOG_SIZE_MB = 10
MAX_TEMP_SIZE_MB = 50
LOG_FILE = "logs/bot.log"
ERROR_LOG_FILE = "logs/error.log"
PAUSE_FILE = "last_shutdown.txt"

# ================== إعدادات البوت المتغيرة (تعدل من لوحة الأدمن) ==================
SETTINGS = {
    "subscription_price": "10$",
    "payment_number": "123456789",
    "whatsapp_link": "https://wa.me/123456789",
    "mirror_token": "",
    "backup_channel": "",  # معرف قناة النسخ الاحتياطي
}
