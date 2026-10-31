import socket

import pytest


@pytest.mark.parametrize("method", ["connect", "connect_ex"])
def test_external_connections_fail_before_network_io(method):
    with socket.socket() as client:
        with pytest.raises(AssertionError, match="External network access"):
            getattr(client, method)(("192.0.2.1", 443))


def test_local_socketpair_still_works_for_asyncio():
    reader, writer = socket.socketpair()
    try:
        reader.settimeout(1)
        writer.sendall(b"ok")
        assert reader.recv(2) == b"ok"
    finally:
        reader.close()
        writer.close()
