#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import asyncio
import time
import logging
import subprocess
from datetime import datetime
sys.path.append(os.path.dirname(__file__))

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.warnings import PTBUserWarning
from telegram.error import Conflict, Unauthorized
import warnings

warnings.filterwarnings("ignore", category=PTBUserWarning, message=".*CallbackQueryHandler.*")

from config import BOT_TOKEN, API_ID, API_HASH, ADMIN_IDS, DATABASE_NAME, ENCRYPTION_KEY, MAX_LOG_SIZE_MB, SETTINGS
from database.db_handler import Database
from utils.logger import setup_logger
from services.auth_service import AuthService
from services.publish_service import PublishService
from services.join_service import JoinService
from services.fetch_service import FetchService
from services.proxy_manager import ProxyManager
from handlers.user_handlers import UserHandlers
from handlers.admin_handlers import AdminHandlers
from handlers.callback_handlers import CallbackHandlers

logger = setup_logger("Muharram", "logs/bot.log", max_bytes=MAX_LOG_SIZE_MB * 1024 * 1024)

# ================== تهيئة قاعدة البيانات والخدمات ==================
db = Database(DATABASE_NAME, ENCRYPTION_KEY)
auth_service = AuthService(db, API_ID, API_HASH)
publish_service = PublishService(db, API_ID, API_HASH)
join_service = JoinService(db, API_ID, API_HASH)
fetch_service = FetchService(db, API_ID, API_HASH)
proxy_manager = ProxyManager(db)

user_handlers = UserHandlers(db, auth_service, publish_service, join_service, fetch_service, ADMIN_IDS)
admin_handlers = AdminHandlers(db, ADMIN_IDS, publish_service, join_service, proxy_manager, bot=None)
callback_handlers = CallbackHandlers(user_handlers, admin_handlers)

# ================== بناء التطبيق ==================
application = Application.builder().token(BOT_TOKEN).build()
admin_handlers.bot = application.bot

# ================== إضافة المعالجات ==================
application.add_handler(CommandHandler("start", user_handlers.start))
application.add_handler(CallbackQueryHandler(callback_handlers.handle))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user_handlers.handle_message))

# ================== مهمة تنظيف الملفات المؤقتة ==================
async def cleanup_job():
    while True:
        await asyncio.sleep(3600)  # كل ساعة
        # تنظيف المجلد المؤقت
        temp_dir = "temp"
        if os.path.exists(temp_dir):
            now = time.time()
            for f in os.listdir(temp_dir):
                f_path = os.path.join(temp_dir, f)
                if os.path.isfile(f_path):
                    if now - os.path.getmtime(f_path) > 3600:
                        os.remove(f_path)
                        logger.info(f"تم حذف ملف مؤقت: {f}")
        # نسخ احتياطي لقاعدة البيانات
        await backup_database()

# ================== النسخ الاحتياطي لقاعدة البيانات ==================
async def backup_database():
    channel_id = db.fetch_one("SELECT value FROM global_settings WHERE key='backup_channel'")
    if channel_id and channel_id['value']:
        try:
            backup_dir = "backups"
            os.makedirs(backup_dir, exist_ok=True)
            backup_name = f"{backup_dir}/data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            import shutil
            shutil.copy2(DATABASE_NAME, backup_name)
            with open(backup_name, 'rb') as f:
                await application.bot.send_document(
                    chat_id=int(channel_id['value']),
                    document=f,
                    caption=f"📦 نسخة احتياطية لقاعدة البيانات - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
            # الاحتفاظ بآخر 5 نسخ فقط
            backups = sorted(os.listdir(backup_dir))
            for old_backup in backups[:-5]:
                os.remove(os.path.join(backup_dir, old_backup))
            logger.info("تم النسخ الاحتياطي بنجاح")
        except Exception as e:
            logger.error(f"خطأ في النسخ الاحتياطي: {e}")

# ================== بدء المهام الخلفية ==================
loop = asyncio.get_event_loop()
loop.create_task(cleanup_job())

# ================== تشغيل البوت مع معالجة الأعطال ==================
def main():
    try:
        logger.info("بدء تشغيل البوت...")
        application.run_polling()
    except (Conflict, Unauthorized) as e:
        logger.critical(f"البوت محظور أو متعارض: {e}. جاري التبديل إلى التوكن الاحتياطي...")
        if SETTINGS.get('mirror_token'):
            # حفظ التوكن الحالي
            with open("last_token.txt", "w") as f:
                f.write(BOT_TOKEN)
            # إعادة التشغيل بالتوكن الجديد
            os.environ['BOT_TOKEN'] = SETTINGS['mirror_token']
            os.execv(sys.executable, ['python'] + sys.argv)
        else:
            logger.critical("لا يوجد توكن احتياطي. البوت متوقف.")
    except Exception as e:
        logger.exception(f"خطأ غير متوقع: {e}")

if __name__ == "__main__":
    main()
