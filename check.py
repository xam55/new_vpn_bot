import sys
import os
sys.path.append('src')

from src.config import config
print("✅ Конфиг загружен!")
print(f"Токен: {config.bot.token[:15]}...")
print(f"Админы: {config.bot.admin_ids}")
print(f"SSH хост: {config.ssh.host}")