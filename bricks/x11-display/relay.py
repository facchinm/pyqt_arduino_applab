"""Expose the host X11 display and Qt system libs inside the app folder for the main container."""

import asyncio
import os
import shutil
import signal
import struct

OUT = "/app/.x11"
DISPLAY = os.environ.get("X_DISPLAY", "10")
HOST_SOCKET = f"/tmp/.X11-unix/X{DISPLAY}"


def copy_libs():
    os.makedirs(f"{OUT}/lib", exist_ok=True)
    for name in os.listdir("/host-libs"):
        shutil.copyfile(f"/host-libs/{name}", f"{OUT}/lib/{name}")


def write_wildcard_cookie():
    # Set every entry's family to FamilyWild so the cookie matches the container's hostname.
    with open("/host-x11/Xauthority", "rb") as f:
        data = f.read()
    out, i = bytearray(), 0
    while i < len(data):
        out += struct.pack(">H", 0xFFFF)
        i += 2
        for _ in range(4):
            (n,) = struct.unpack_from(">H", data, i)
            out += data[i : i + 2 + n]
            i += 2 + n
    path = f"{OUT}/Xauthority"
    with open(path, "wb") as f:
        f.write(out)
    os.chmod(path, 0o600)


async def pipe(reader, writer):
    try:
        while data := await reader.read(65536):
            writer.write(data)
            await writer.drain()
    finally:
        writer.close()


async def handle(client_r, client_w):
    try:
        x_r, x_w = await asyncio.open_unix_connection(HOST_SOCKET)
    except OSError:
        client_w.close()
        return
    await asyncio.gather(pipe(client_r, x_w), pipe(x_r, client_w), return_exceptions=True)


async def main():
    copy_libs()
    write_wildcard_cookie()
    sock = f"{OUT}/X{DISPLAY}"
    if os.path.lexists(sock):
        os.unlink(sock)
    server = await asyncio.start_unix_server(handle, path=sock)
    print(f"Relaying {HOST_SOCKET} -> {sock}", flush=True)
    stop = asyncio.Event()
    asyncio.get_running_loop().add_signal_handler(signal.SIGTERM, stop.set)
    try:
        await stop.wait()
    finally:
        server.close()
        os.unlink(sock)


asyncio.run(main())
