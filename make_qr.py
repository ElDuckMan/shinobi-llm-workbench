#!/usr/bin/env python3
"""Regenerate the workbench QR code for your own hosted URL.
Usage:  python make_qr.py https://your-service.onrender.com
Requires:  pip install "qrcode[pil]"
"""
import sys, qrcode
from qrcode.constants import ERROR_CORRECT_H
url = sys.argv[1] if len(sys.argv) > 1 else "https://shinobi-llm-workbench.onrender.com"
qr = qrcode.QRCode(error_correction=ERROR_CORRECT_H, box_size=16, border=3)
qr.add_data(url); qr.make(fit=True)
img = qr.make_image(fill_color=(20, 40, 75), back_color="white").convert("RGB")
out = "qr_workbench.png"; img.save(out)
print(f"wrote {out} -> {url}")
print("Drop it onto slide 18 of the deck (replace the existing QR).")
