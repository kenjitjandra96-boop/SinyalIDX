# TradingView IDX EMA5 Webhook — versi Vercel (gratis, tanpa kartu)

Fungsinya identik dengan versi sebelumnya: validasi saham IDX, filter persentase
closing di atas EMA5 (bisa diatur), kirim ke Telegram. Ini pakai Python
Serverless Function bawaan Vercel (`api/webhook.py`), yang dukungannya lebih
matang dan stabil dibanding Netlify untuk Python.

## Struktur

```
tradingview-idx-webhook-vercel/
├── vercel.json              # bikin URL /webhook/tradingview mengarah ke api/webhook
├── api/webhook.py           # logika webhook (Python, tanpa dependency luar)
└── pine/ema5_idx_alert.pine
```

## Langkah 1 — Upload ke GitHub

Sama seperti sebelumnya (via web github.com):
1. Buat repo baru kosong di github.com, misal `tradingview-idx-webhook-vercel`.
2. Buka repo → "uploading an existing file" → drag semua isi folder ini
   (vercel.json, api/, pine/, README.md, .gitignore).
3. Commit ke branch main.
4. **Cek strukturnya**: pastikan folder `api` di repo berisi file `webhook.py`
   langsung di dalamnya (path: `api/webhook.py`), bukan tersarang lagi.

## Langkah 2 — Import ke Vercel

1. Buka [vercel.com](https://vercel.com) → daftar/login pakai akun GitHub (tidak perlu kartu).
2. Klik **Add New... → Project**.
3. Pilih repo `tradingview-idx-webhook-vercel` → klik **Import**.
4. Biarkan semua pengaturan default (Vercel otomatis mengenali `api/*.py` sebagai
   Python Function) → klik **Deploy**.

## Langkah 3 — Isi environment variables

Setelah deploy pertama selesai:
1. Buka project di dashboard Vercel → **Settings → Environment Variables**.
2. Tambahkan satu per satu, untuk environment **Production** (centang juga
   Preview & Development kalau mau):

| Key | Value |
|---|---|
| `WEBHOOK_SECRET` | string rahasia buatanmu |
| `THRESHOLD_PERCENT` | contoh: `1.5` |
| `TELEGRAM_BOT_TOKEN` | token dari BotFather |
| `TELEGRAM_CHAT_ID` | chat_id kamu |

3. Buka tab **Deployments** → klik titik tiga di deployment terakhir → **Redeploy**,
   supaya environment variable baru terpakai.

## Langkah 4 — Ambil URL & tes

URL webhook kamu:
```
https://nama-project-kamu.vercel.app/webhook/tradingview?secret=ISI_SECRET_KAMU
```

Tes dari terminal:
```bash
curl -X POST "https://nama-project-kamu.vercel.app/webhook/tradingview?secret=ISI_SECRET_KAMU" \
  -H "Content-Type: application/json" \
  -d '{"ticker":"BBCA","exchange":"IDX","close":9250,"ema5":9000,"time":"2026-09-25T00:00:00Z"}'
```

Kalau muncul `{"status":"sent",...}` dan pesan masuk ke Telegram, berarti berhasil.

## Langkah 5 — Pasang ke TradingView

Sama seperti sebelumnya: pasang `pine/ema5_idx_alert.pine` ke chart saham IDX,
buat alert, aktifkan Webhook URL, isi dengan URL dari Langkah 4. Pastikan akun
TradingView sudah mengaktifkan Two-Factor Authentication (2FA).

## Catatan

- Paket gratis (Hobby) Vercel: 100 GB bandwidth/bulan, fungsi serverless dengan
  jatah generous — jauh lebih dari cukup untuk alert harian.
- Tidak perlu kartu kredit untuk mendaftar maupun memakai paket gratis ini.
- Python runtime Vercel berstatus **Beta** secara resmi, tapi sudah lama stabil
  dipakai banyak proyek publik — berbeda dari isu "No Functions found" yang
  kita alami di Netlify.
