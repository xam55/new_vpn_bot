import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


@dataclass
class DatabaseConfig:
    """Конфигурация базы данных"""
    type: str = os.getenv("DB_TYPE", "sqlite")
    path: str = os.getenv("DB_PATH", "data/database/vpn_bot.db")

    @property
    def url(self) -> str:
        if self.type == "postgres":
            host = os.getenv("DB_HOST", "localhost")
            port = os.getenv("DB_PORT", "5432")
            name = os.getenv("DB_NAME", "vpnbot")
            user = os.getenv("DB_USER", "vpnbot")
            password = os.getenv("DB_PASSWORD", "")
            return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
        else:
            return f"sqlite+aiosqlite:///{self.path}"


@dataclass
class BotConfig:
    """Конфигурация бота"""
    token: str = os.getenv("BOT_TOKEN", "")
    admin_ids: List[int] = field(default_factory=list)

    def __post_init__(self):
        ids_str = os.getenv("ADMIN_IDS", "")
        if ids_str:
            self.admin_ids = [int(id_str.strip()) for id_str in ids_str.split(",") if id_str.strip()]


@dataclass
class SSHConfig:
    """Конфигурация SSH"""
    host: str = os.getenv("SSH_HOST", "")
    port: int = int(os.getenv("SSH_PORT", "22"))
    username: str = os.getenv("SSH_USERNAME", "root")
    password: str = os.getenv("SSH_PASSWORD", "")
    key_path: str = os.getenv("SSH_KEY_PATH", "")


@dataclass
class WireGuardConfig:
    """Конфигурация WireGuard"""
    server_config_path: str = os.getenv("WG_SERVER_CONFIG_PATH", "/etc/wireguard/wg0.conf")
    server_ip: str = os.getenv("WG_SERVER_IP", "10.0.0.1")
    network: str = os.getenv("WG_NETWORK", "10.0.0.0/24")
    client_ip_start: str = os.getenv("WG_CLIENT_IP_START", "10.0.0.2")
    client_ip_end: str = os.getenv("WG_CLIENT_IP_END", "10.0.0.254")


@dataclass
class PaymentConfig:
    """Конфигурация платежей"""
    price_per_day: int = int(os.getenv("PRICE_PER_DAY", "10"))
    payment_methods: List[str] = field(default_factory=list)

    def __post_init__(self):
        methods_str = os.getenv("PAYMENT_METHODS", "card,qiwi")
        self.payment_methods = [m.strip() for m in methods_str.split(",")]


@dataclass
class Config:
    """Основной конфиг"""
    db: DatabaseConfig = field(default_factory=DatabaseConfig)
    bot: BotConfig = field(default_factory=BotConfig)
    ssh: SSHConfig = field(default_factory=SSHConfig)
    wireguard: WireGuardConfig = field(default_factory=WireGuardConfig)
    payment: PaymentConfig = field(default_factory=PaymentConfig)

    # Системные настройки
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    timezone: str = os.getenv("TIMEZONE", "Europe/Moscow")

    def validate(self):
        """Проверка конфигурации"""
        if not self.bot.token:
            raise ValueError("BOT_TOKEN не установлен в .env файле")
        if not self.bot.admin_ids:
            print("⚠️  ADMIN_IDS не установлен - админ-панель будет недоступна")


# Создаем глобальный экземпляр
config = Config()
config.validate()