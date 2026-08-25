"""
handlers/phone.py — Phase 1 phone status commands.

Each function maps to exactly one hard-coded shell command.
No user input is ever interpolated into a shell string.

Commands registered here:
  /battery      — charge level, status, temperature (via termux-battery-status)
  /storage      — internal storage free/total (via df)
  /ram          — memory usage (via /proc/meminfo)
  /temperature  — battery temp from termux-battery-status
  /uptime       — system uptime
  /ip           — local Wi-Fi IP address
  /wifi         — connected SSID and signal (via termux-wifi-connectioninfo)
"""

import asyncio
import json
import logging

from telegram import Update
from telegram.ext import ContextTypes

from auth import restricted
from config import COMMAND_TIMEOUT

logger = logging.getLogger(__name__)


# ── Shell helper ──────────────────────────────────────────────────────────────

async def _run(cmd: str) -> tuple[str, str]:
    """
    Run a shell command asynchronously and return (stdout, stderr).

    Uses asyncio subprocess so the bot event loop is never blocked.
    The command string is always a hard-coded literal — never user input.
    """
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=COMMAND_TIMEOUT
        )
        return stdout.decode().strip(), stderr.decode().strip()
    except asyncio.TimeoutError:
        logger.error("Command timed out: %s", cmd)
        return "", "Command timed out"
    except Exception as exc:  # noqa: BLE001
        logger.exception("Command failed: %s", cmd)
        return "", str(exc)


def _parse_json(raw: str) -> dict | None:
    """Return parsed JSON dict or None on failure."""
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return None


# ── /battery ─────────────────────────────────────────────────────────────────

@restricted
async def battery(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Uses: termux-battery-status  (part of the Termux:API package)
    Returns JSON like:
      {"health":"GOOD","percentage":87,"plugged":"UNPLUGGED",
       "status":"DISCHARGING","temperature":28.600000381469727}
    """
    stdout, stderr = await _run("termux-battery-status")
    data = _parse_json(stdout)

    if data is None:
        await update.message.reply_text(
            f"⚠️ Could not read battery info.\n"
            f"Make sure `termux-api` is installed:\n"
            f"`pkg install termux-api`\n\nError: {stderr or stdout}"
        )
        return

    pct = data.get("percentage", "?")
    status = data.get("status", "?").capitalize()
    plugged = data.get("plugged", "?").replace("_", " ").capitalize()
    health = data.get("health", "?").capitalize()
    temp = data.get("temperature", None)
    temp_str = f"{temp:.1f} °C" if isinstance(temp, (int, float)) else "?"

    lines = [
        "🔋 *Battery*",
        f"Charge:      {pct}%",
        f"Status:      {status}",
        f"Plugged:     {plugged}",
        f"Health:      {health}",
        f"Temperature: {temp_str}",
    ]
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ── /storage ──────────────────────────────────────────────────────────────────

@restricted
async def storage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Uses: df -h /data/data/com.termux
    Reports the filesystem that Termux's home directory lives on.
    Also checks /sdcard for the shared storage partition.
    """
    stdout_internal, _ = await _run("df -h /data/data/com.termux 2>/dev/null || df -h ~")
    stdout_sdcard, _ = await _run("df -h /sdcard 2>/dev/null || echo ''")

    def _parse_df(output: str) -> str:
        lines = [l for l in output.splitlines() if l and not l.startswith("Filesystem")]
        if not lines:
            return "unavailable"
        parts = lines[0].split()
        # df -h columns: Filesystem  Size  Used  Avail  Use%  Mounted
        if len(parts) >= 5:
            return f"{parts[3]} free of {parts[1]} ({parts[4]} used)"
        return output

    internal = _parse_df(stdout_internal)
    sdcard = _parse_df(stdout_sdcard)

    lines = [
        "💾 *Storage*",
        f"Internal (Termux): {internal}",
        f"SD / shared:       {sdcard}",
    ]
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ── /ram ──────────────────────────────────────────────────────────────────────

@restricted
async def ram(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Uses: /proc/meminfo  (always available on Android/Linux)
    Reads MemTotal, MemAvailable, and calculates used RAM.
    """
    stdout, stderr = await _run("cat /proc/meminfo")
    if not stdout:
        await update.message.reply_text(f"⚠️ Could not read memory info: {stderr}")
        return

    info: dict[str, int] = {}
    for line in stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            # e.g. "MemTotal:        7812084 kB"
            key = parts[0].rstrip(":")
            try:
                info[key] = int(parts[1])
            except ValueError:
                pass

    total_kb = info.get("MemTotal", 0)
    avail_kb = info.get("MemAvailable", 0)
    used_kb = total_kb - avail_kb

    def _fmt(kb: int) -> str:
        mb = kb / 1024
        return f"{mb:.0f} MB" if mb < 1024 else f"{mb / 1024:.1f} GB"

    pct = (used_kb / total_kb * 100) if total_kb else 0

    lines = [
        "🧠 *RAM*",
        f"Total:     {_fmt(total_kb)}",
        f"Used:      {_fmt(used_kb)} ({pct:.0f}%)",
        f"Available: {_fmt(avail_kb)}",
    ]
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ── /temperature ──────────────────────────────────────────────────────────────

@restricted
async def temperature(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Primary source: termux-battery-status (most reliable on Android).
    Fallback: /sys/class/thermal/thermal_zone* sysfs nodes.
    """
    stdout, _ = await _run("termux-battery-status")
    data = _parse_json(stdout)

    temp_lines = ["🌡️ *Temperature*"]

    if data and isinstance(data.get("temperature"), (int, float)):
        temp_lines.append(f"Battery: {data['temperature']:.1f} °C")
    else:
        temp_lines.append("Battery: unavailable (install termux-api)")

    # Try sysfs thermal zones for additional sensors
    stdout2, _ = await _run(
        "for f in /sys/class/thermal/thermal_zone*/temp; do "
        "  zone=$(echo $f | grep -o 'thermal_zone[0-9]*'); "
        "  val=$(cat $f 2>/dev/null); "
        "  echo \"$zone $val\"; "
        "done"
    )
    if stdout2:
        for line in stdout2.splitlines():
            parts = line.split()
            if len(parts) == 2:
                try:
                    millideg = int(parts[1])
                    deg = millideg / 1000.0
                    if 0 < deg < 120:  # sanity check
                        temp_lines.append(f"{parts[0]}: {deg:.1f} °C")
                except ValueError:
                    pass

    await update.message.reply_text("\n".join(temp_lines), parse_mode="Markdown")


# ── /uptime ───────────────────────────────────────────────────────────────────

@restricted
async def uptime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Uses: /proc/uptime  (always available on Android/Linux)
    First field is seconds since last boot.
    """
    stdout, stderr = await _run("cat /proc/uptime")
    if not stdout:
        await update.message.reply_text(f"⚠️ Could not read uptime: {stderr}")
        return

    try:
        total_seconds = float(stdout.split()[0])
    except (ValueError, IndexError):
        await update.message.reply_text(f"⚠️ Unexpected uptime format: {stdout!r}")
        return

    days = int(total_seconds // 86400)
    hours = int((total_seconds % 86400) // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")

    await update.message.reply_text(f"⏱️ *Uptime*\n{' '.join(parts)}", parse_mode="Markdown")


# ── /ip ───────────────────────────────────────────────────────────────────────

@restricted
async def ip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Uses: ip addr  (available in Termux via the iproute2 package)
    Extracts the first non-loopback IPv4 address (typically the Wi-Fi IP).
    Fallback: hostname -I if ip is not installed.
    """
    stdout, _ = await _run(
        "ip -4 addr show scope global 2>/dev/null "
        "| grep -oP '(?<=inet )[\d.]+' "
        "| head -n1"
    )

    if not stdout:
        # Fallback for environments without iproute2
        stdout, _ = await _run("hostname -I 2>/dev/null | awk '{print $1}'")

    if not stdout:
        await update.message.reply_text(
            "⚠️ Could not determine IP address.\n"
            "Install iproute2: `pkg install iproute2`",
            parse_mode="Markdown",
        )
        return

    await update.message.reply_text(f"🌐 *Local IP*\n`{stdout}`", parse_mode="Markdown")


# ── /wifi ─────────────────────────────────────────────────────────────────────

@restricted
async def wifi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Uses: termux-wifi-connectioninfo  (part of the Termux:API package)
    Returns JSON with ssid, bssid, ip, link_speed, rssi, etc.
    """
    stdout, stderr = await _run("termux-wifi-connectioninfo")
    data = _parse_json(stdout)

    if data is None:
        await update.message.reply_text(
            f"⚠️ Could not read Wi-Fi info.\n"
            f"Make sure `termux-api` is installed:\n"
            f"`pkg install termux-api`\n\nError: {stderr or stdout}",
            parse_mode="Markdown",
        )
        return

    ssid = data.get("ssid", "?")
    bssid = data.get("bssid", "?")
    ip_addr = data.get("ip", "?")
    link_speed = data.get("link_speed", "?")
    rssi = data.get("rssi", "?")
    freq = data.get("frequency_mhz", data.get("frequency", "?"))

    # Map RSSI to a rough signal label
    signal = "excellent" if isinstance(rssi, int) and rssi >= -50 else \
             "good" if isinstance(rssi, int) and rssi >= -65 else \
             "fair" if isinstance(rssi, int) and rssi >= -75 else \
             "poor"

    lines = [
        "📶 *Wi-Fi*",
        f"SSID:       {ssid}",
        f"BSSID:      {bssid}",
        f"IP:         {ip_addr}",
        f"Speed:      {link_speed} Mbps",
        f"RSSI:       {rssi} dBm ({signal})",
        f"Frequency:  {freq} MHz",
    ]
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
