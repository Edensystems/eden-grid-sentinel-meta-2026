"""Block external connections; allow loopback for Windows asyncio socket pairs."""
import ipaddress
import socket

import pytest


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    def guarded(original):
        def connect(sock, address):
            if sock.family in (socket.AF_INET, socket.AF_INET6):
                try:
                    local = ipaddress.ip_address(address[0]).is_loopback
                except ValueError:
                    local = False
                if not local:
                    raise AssertionError("External network access is prohibited in the offline test suite")
            return original(sock, address)
        return connect

    monkeypatch.setattr(socket.socket, "connect", guarded(socket.socket.connect))
    monkeypatch.setattr(socket.socket, "connect_ex", guarded(socket.socket.connect_ex))
