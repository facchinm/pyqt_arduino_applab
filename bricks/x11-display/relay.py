"""Expose the host X11 display and Qt system libs inside the app folder for the main container."""

import asyncio
import os
import re
import shutil
import signal
import struct

OUT = "/app/.x11"
HOST_X11 = "/tmp/.X11-unix"
# Main always sees the relayed display as :0, whichever host display is chosen.
RELAY_SOCKET = f"{OUT}/X0"
host_socket = None


def copy_libs():
    os.makedirs(f"{OUT}/lib", exist_ok=True)
    for name in os.listdir("/host-libs"):
        shutil.copyfile(f"/host-libs/{name}", f"{OUT}/lib/{name}")


def read_cookies():
    with open("/host-home/.Xauthority", "rb") as f:
        data = f.read()
    cookies, i = {}, 2
    while i < len(data):
        fields = []
        for _ in range(4):
            (n,) = struct.unpack_from(">H", data, i)
            fields.append(data[i + 2 : i + 2 + n])
            i += 2 + n
        i += 2
        _addr, number, name, value = fields
        cookies[number.decode()] = (name, value)
    return cookies


def pick_display(cookies):
    displays = [m.group(1) for s in os.listdir(HOST_X11) if (m := re.fullmatch(r"X(\d+)", s))]
    wanted = os.environ.get("X_DISPLAY")
    if wanted:
        return wanted
    usable = [d for d in displays if d in cookies]
    if not usable:
        raise SystemExit(f"No X display with a cookie in ~/.Xauthority (sockets: {displays})")
    # The newest socket is the most recent session (e.g. an RDP login over the local screen).
    return max(usable, key=lambda d: os.stat(f"{HOST_X11}/X{d}").st_mtime)


def write_cookie(name, value):
    def field(b):
        return struct.pack(">H", len(b)) + b

    # FamilyWild + display "0" so it matches the container's hostname and the relayed :0.
    entry = struct.pack(">H", 0xFFFF) + field(b"") + field(b"0") + field(name) + field(value)
    path = f"{OUT}/Xauthority"
    with open(path, "wb") as f:
        f.write(entry)
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
        x_r, x_w = await asyncio.open_unix_connection(host_socket)
    except OSError:
        client_w.close()
        return
    await asyncio.gather(pipe(client_r, x_w), pipe(x_r, client_w), return_exceptions=True)


async def main():
    global host_socket
    copy_libs()
    for stale in os.listdir(OUT):
        if re.fullmatch(r"X\d+", stale):
            os.unlink(f"{OUT}/{stale}")
    cookies = read_cookies()
    display = pick_display(cookies)
    host_socket = f"{HOST_X11}/X{display}"
    write_cookie(*cookies[display])
    server = await asyncio.start_unix_server(handle, path=RELAY_SOCKET)
    print(f"Relaying {host_socket} (:{display}) -> {RELAY_SOCKET}", flush=True)
    stop = asyncio.Event()
    asyncio.get_running_loop().add_signal_handler(signal.SIGTERM, stop.set)
    try:
        await stop.wait()
    finally:
        server.close()
        if os.path.lexists(RELAY_SOCKET):
            os.unlink(RELAY_SOCKET)


asyncio.run(main())
