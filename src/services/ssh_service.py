import asyncio
import paramiko
from io import StringIO
from typing import Optional, Dict, Any
import logging

from src.config import config

logger = logging.getLogger(__name__)


class SSHService:
    """Сервис для работы с SSH подключениями"""

    def __init__(self):
        self.ssh_client: Optional[paramiko.SSHClient] = None

    async def connect(self) -> bool:
        """Установка SSH соединения"""
        try:
            # Создаем SSH клиент
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Подключаемся с использованием ключа или пароля
            if config.ssh.key_path:
                # Загружаем приватный ключ
                key = paramiko.RSAKey.from_private_key_file(config.ssh.key_path)
                self.ssh_client.connect(
                    hostname=config.ssh.host,
                    port=config.ssh.port,
                    username=config.ssh.username,
                    pkey=key,
                    timeout=10
                )
            else:
                # Используем пароль
                self.ssh_client.connect(
                    hostname=config.ssh.host,
                    port=config.ssh.port,
                    username=config.ssh.username,
                    password=config.ssh.password,
                    timeout=10
                )

            logger.info(f"SSH подключение установлено к {config.ssh.host}")
            return True

        except Exception as e:
            logger.error(f"Ошибка SSH подключения: {e}")
            return False

    async def execute_command(self, command: str) -> Dict[str, Any]:
        """Выполнение команды на удаленном сервере"""
        try:
            if not self.ssh_client or not self.ssh_client.get_transport().is_active():
                await self.connect()

            # Выполняем команду
            stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=30)

            exit_code = stdout.channel.recv_exit_status()
            output = stdout.read().decode('utf-8').strip()
            error = stderr.read().decode('utf-8').strip()

            return {
                "success": exit_code == 0,
                "exit_code": exit_code,
                "output": output,
                "error": error
            }

        except Exception as e:
            logger.error(f"Ошибка выполнения команды: {command[:50]}... - {e}")
            return {"success": False, "error": str(e)}

    async def close(self):
        """Закрытие SSH соединения"""
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None
            logger.info("SSH соединение закрыто")

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()