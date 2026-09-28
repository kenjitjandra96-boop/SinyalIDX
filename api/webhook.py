import json
import os
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

APP_SECRET = os.environ.get("WEBHOOK_SECRET", "")
THRESHOLD_MIN_PERCENT = float(os.environ.get("THRESHOLD_MIN_PERCENT", "7"))
_max_raw = os.environ.get("THRESHOLD_MAX_PERCENT", "12").strip()
THRESHOLD_MAX_PERCENT = float(_max_raw) if _max_raw else None
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
ALLOWED_EXCHANGE = "IDX"


def send_telegram(text: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = json.dumps(
        {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    ).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req, timeout=5)
    except urllib.error.URLError:
        pass  # jangan sampai error Telegram bikin function gagal total


def process_alert(data: dict, secret: str | None):
    """Logika inti, dipisah dari I/O supaya mudah diuji. Return (status_code, body_dict)."""
    if APP_SECRET and secret != APP_SECRET:
        return 403, {"status": "error", "detail": "Invalid secret"}

    ticker = str(data.get("ticker", "")).replace("IDX:", "").upper()
    exchange = str(data.get("exchange", "")).upper()
    close = data.get("close")
    ema5 = data.get("ema5")

    if exchange != ALLOWED_EXCHANGE:
        return 200, {"status": "ignored", "reason": "not_idx"}

    if close is None or ema5 is None:
        return 400, {"status": "error", "detail": "close/ema5 wajib ada"}

    try:
        close = float(close)
        ema5 = float(ema5)
    except (TypeError, ValueError):
        return 400, {"status": "error", "detail": "close/ema5 harus angka"}

    if ema5 == 0:
        return 200, {"status": "ignored", "reason": "ema5_zero"}

    percent_above = (close - ema5) / ema5 * 100

    if percent_above < THRESHOLD_MIN_PERCENT:
        return 200, {
            "status": "ignored",
            "reason": "below_range",
            "percent_above": round(percent_above, 2),
        }

    if THRESHOLD_MAX_PERCENT is not None and percent_above > THRESHOLD_MAX_PERCENT:
        return 200, {
            "status": "ignored",
            "reason": "above_range",
            "percent_above": round(percent_above, 2),
        }

    chart_url = f"https://www.tradingview.com/chart/?symbol=IDX:{ticker}"
    message = (
        f"<b>{ticker}</b> (IDX)\n"
        f"Close: {close:,.2f}\n"
        f"EMA5: {ema5:,.2f}\n"
        f"Selisih: {percent_above:.2f}% di atas EMA5\n"
        f"Timeframe: Daily\n"
        f'<a href="{chart_url}">Lihat Chart</a>'
    )
    send_telegram(message)

    return 200, {"status": "sent", "ticker": ticker, "percent_above": round(percent_above, 2)}


class handler(BaseHTTPRequestHandler):

    def _send_json(self, status_code: int, body: dict):
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        query = parse_qs(urlparse(self.path).query)
        secret = query.get("secret", [None])[0]

        length = int(self.headers.get("Content-Length", 0) or 0)
        raw_body = self.rfile.read(length) if length else b"{}"

        try:
            data = json.loads(raw_body or b"{}")
        except json.JSONDecodeError:
            self._send_json(400, {"status": "error", "detail": "Payload bukan JSON valid"})
            return

        status_code, body = process_alert(data, secret)
        self._send_json(status_code, body)

    def do_GET(self):
        self._send_json(
            200,
            {
                "status": "ok",
                "threshold_min_percent": THRESHOLD_MIN_PERCENT,
                "threshold_max_percent": THRESHOLD_MAX_PERCENT,
            },
        )
