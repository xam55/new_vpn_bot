import asyncio
import tempfile
import os
from typing import Dict, Optional
from datetime import datetime

from src.config import config
from src.utils.constants import WG_DNS_SERVERS, WG_KEEPALIVE
from src.services.ssh_service import SSHService


class WireGuardService:
    """Сервис для управления WireGuard через SSH"""

    def __init__(self):
        self.ssh_service = SSHService()

    async def _run_ssh_command(self, command: str) -> Dict[str, any]:
        """Выполнить команду на удаленном сервере через SSH"""
        try:
            result = await self.ssh_service.execute_command(command)
            return {
                'success': result.get('success', False),
                'output': result.get('output', ''),
                'error': result.get('error', '')
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def generate_keys(self) -> Dict[str, str]:
        """Сгенерировать пару ключей WireGuard"""
        # Генерируем приватный ключ
        priv_key_result = await self._run_ssh_command('wg genkey')
        if not priv_key_result['success']:
            raise Exception(f"Ошибка генерации приватного ключа: {priv_key_result['error']}")

        private_key = priv_key_result['output']

        # Генерируем публичный ключ из приватного
        # Создаем временный файл на сервере с приватным ключом
        temp_file = f"/tmp/wg_priv_{int(datetime.now().timestamp())}.tmp"
        create_file_cmd = f"echo '{private_key}' > {temp_file}"
        await self._run_ssh_command(create_file_cmd)

        # Генерируем публичный ключ
        pub_key_result = await self._run_ssh_command(f"wg pubkey < {temp_file}")

        # Удаляем временный файл
        await self._run_ssh_command(f"rm -f {temp_file}")

        if not pub_key_result['success']:
            raise Exception(f"Ошибка генерации публичного ключа: {pub_key_result['error']}")

        public_key = pub_key_result['output']

        return {
            'private_key': private_key,
            'public_key': public_key
        }

    async def get_server_info(self) -> Dict[str, str]:
        """Получить информацию о WireGuard сервере"""
        # Получаем публичный ключ сервера
        # Сначала читаем приватный ключ сервера
        priv_key_result = await self._run_ssh_command(
            f"sudo grep -oP 'PrivateKey = \\K[^\\n]+' {config.wireguard.server_config_path}"
        )

        if not priv_key_result['success']:
            raise Exception(f"Ошибка чтения приватного ключа сервера: {priv_key_result['error']}")

        server_private_key = priv_key_result['output']

        # Создаем временный файл с приватным ключом сервера
        temp_file = f"/tmp/wg_server_priv_{int(datetime.now().timestamp())}.tmp"
        create_file_cmd = f"echo '{server_private_key}' > {temp_file}"
        await self._run_ssh_command(create_file_cmd)

        # Генерируем публичный ключ сервера
        pub_key_result = await self._run_ssh_command(f"wg pubkey < {temp_file}")
        await self._run_ssh_command(f"rm -f {temp_file}")

        if not pub_key_result['success']:
            raise Exception(f"Ошибка генерации публичного ключа сервера: {pub_key_result['error']}")

        server_public_key = pub_key_result['output']

        # Получаем порт сервера
        port_result = await self._run_ssh_command(
            f"sudo grep -oP 'ListenPort = \\K[0-9]+' {config.wireguard.server_config_path}"
        )

        if not port_result['success']:
            raise Exception(f"Ошибка чтения порта сервера: {port_result['error']}")

        server_port = port_result['output']

        # Получаем публичный IP сервера (или используем указанный хост)
        server_ip = config.ssh.host

        return {
            'public_key': server_public_key,
            'port': server_port,
            'ip': server_ip,
            'endpoint': server_ip  # Для Endpoint используем IP
        }

    async def get_next_client_ip(self) -> str:
        """Получить следующий свободный IP адрес для клиента"""
        # Получаем список используемых IP адресов
        used_ips_result = await self._run_ssh_command(
            f"sudo grep -oP 'AllowedIPs = \\K[0-9.]+' {config.wireguard.server_config_path} || true"
        )

        used_ips = set()
        if used_ips_result['success'] and used_ips_result['output']:
            used_ips = set(used_ips_result['output'].split('\n'))

        # Парсим начальный IP и подсеть
        base_ip_parts = config.wireguard.client_ip_start.split('.')
        base_ip = '.'.join(base_ip_parts[:3])  # Первые три октета
        start_num = int(base_ip_parts[3])
        end_num = int(config.wireguard.client_ip_end.split('.')[3])

        # Ищем свободный IP
        for i in range(start_num, end_num + 1):
            test_ip = f"{base_ip}.{i}"
            if test_ip not in used_ips:
                return test_ip

        raise Exception("Нет свободных IP адресов в пуле")

    async def add_client_to_server(self, client_public_key: str, client_ip: str) -> bool:
        """Добавить клиента на сервер WireGuard"""
        # Команда для добавления клиента в конфиг
        add_peer_cmd = (
            f"sudo wg set {os.path.basename(config.wireguard.server_config_path).replace('.conf', '')} "
            f"peer {client_public_key} "
            f"allowed-ips {client_ip}/32"
        )

        result = await self._run_ssh_command(add_peer_cmd)

        if result['success']:
            # Сохраняем конфигурацию
            save_cmd = f"sudo wg-quick save {os.path.basename(config.wireguard.server_config_path).replace('.conf', '')}"
            await self._run_ssh_command(save_cmd)
            return True
        else:
            print(f"Ошибка добавления клиента: {result['error']}")
            return False

    async def remove_client_from_server(self, client_public_key: str) -> bool:
        """Удалить клиента с сервера WireGuard"""
        remove_cmd = (
            f"sudo wg set {os.path.basename(config.wireguard.server_config_path).replace('.conf', '')} "
            f"peer {client_public_key} remove"
        )

        result = await self._run_ssh_command(remove_cmd)

        if result['success']:
            save_cmd = f"sudo wg-quick save {os.path.basename(config.wireguard.server_config_path).replace('.conf', '')}"
            await self._run_ssh_command(save_cmd)
            return True

        return False

    async def generate_client_config(
            self,
            client_private_key: str,
            client_ip: str,
            server_public_key: str,
            server_endpoint: str,
            server_port: str
    ) -> str:
        """Сгенерировать конфигурационный файл для клиента"""
        config_template = f"""[Interface]
PrivateKey = {client_private_key}
Address = {client_ip}/24
DNS = {', '.join(WG_DNS_SERVERS)}

[Peer]
PublicKey = {server_public_key}
Endpoint = {server_endpoint}:{server_port}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = {WG_KEEPALIVE}
"""
        return config_template


# Создаем глобальный экземпляр сервиса
wireguard_service = WireGuardService()