#!/usr/bin/env python3
"""Crop, compress and embed photos into index.html as base64 JPGs.

Writes each image straight into the CONFIG block at the top of index.html,
so the page stays a single self-contained file.

Examples
  python3 tools/embed_images.py --portrait me.jpg --logo iqi-logo.png
  python3 tools/embed_images.py --namecard card.jpg
  python3 tools/embed_images.py --hero jb-skyline.jpg
  python3 tools/embed_images.py --project "EXSIM Kebun Teh=exsim.jpg"

Requires Pillow:  pip install pillow
"""
import argparse
import base64
import io
import re
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Pillow is required: pip install pillow")

ROOT = Path(__file__).resolve().parent.parent


def load(path, background=(255, 255, 255)):
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)  # respect phone camera rotation
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, background)  # flatten transparency (cut-out photos, logos)
        bg.paste(img, mask=img.split()[-1])
        return bg
    return img.convert("RGB")


def crop_to_ratio(img, ratio, focus_y=0.5):
    """Crop to width/height `ratio`; focus_y < .5 keeps more of the top (faces)."""
    w, h = img.size
    if w / h > ratio:
        nw = round(h * ratio)
        left = (w - nw) // 2
        return img.crop((left, 0, left + nw, h))
    nh = round(w / ratio)
    top = round((h - nh) * focus_y)
    return img.crop((0, top, w, top + nh))


def to_data_url(img, width, quality):
    if img.width > width:
        img = img.resize((width, round(img.height * width / img.width)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    kb = len(buf.getvalue()) / 1024
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode(), img.size, kb


def set_value(html, key, value, after=0):
    """Replace the first `key: "..."` found after position `after`."""
    pattern = re.compile(r'(\b' + re.escape(key) + r':\s*)"[^"]*"')
    m = pattern.search(html, after)
    if not m:
        sys.exit(f'Could not find `{key}: "..."` in the CONFIG block')
    return html[: m.start()] + m.group(1) + '"' + value + '"' + html[m.end():]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--portrait", help="portrait photo (cropped to 4:5)")
    ap.add_argument("--logo", help="company logo")
    ap.add_argument("--hero", help="large hero photo (city or project)")
    ap.add_argument("--namecard", help="name card image shown in the contact section")
    ap.add_argument("--project", action="append", default=[], metavar='"NAME=photo.jpg"',
                    help="project photo; NAME must match the project's name in CONFIG")
    ap.add_argument("--width", type=int, default=1000, help="output width in px (default 1000)")
    ap.add_argument("--hero-width", type=int, default=None, help="hero width in px (default: --width)")
    ap.add_argument("--quality", type=int, default=78, help="JPG quality 1-95 (default 78)")
    ap.add_argument("--html", default=str(ROOT / "index.html"), help="page to update")
    args = ap.parse_args()

    html_path = Path(args.html)
    html = html_path.read_text(encoding="utf-8")
    config_at = html.find("const CONFIG")
    if config_at < 0:
        sys.exit("CONFIG block not found")
    images_at = html.find("images:", config_at)

    def report(label, size, kb):
        print(f"  {label}: {size[0]}x{size[1]} px, {kb:.0f} KB")

    if args.portrait:
        backdrop = (0xF3, 0xEB, 0xDE)  # cut-out portraits sit on the page's Old Lace base
        url, size, kb = to_data_url(crop_to_ratio(load(args.portrait, backdrop), 4 / 5, focus_y=0.3), args.width, args.quality)
        html = set_value(html, "portrait", url, images_at)
        report("portrait", size, kb)
    if args.logo:
        logo = load(args.logo)
        url, size, kb = to_data_url(logo, min(args.width, logo.width), 90)
        html = set_value(html, "logo", url, images_at)
        report("logo", size, kb)
    if args.hero:
        url, size, kb = to_data_url(load(args.hero), args.hero_width or args.width, args.quality)
        html = set_value(html, "hero", url, images_at)
        report("hero", size, kb)
    if args.namecard:
        url, size, kb = to_data_url(load(args.namecard), args.width, 85)  # higher quality keeps small text crisp
        html = set_value(html, "namecard", url, images_at)
        report("namecard", size, kb)
    for spec in args.project:
        if "=" not in spec:
            sys.exit(f'--project expects "NAME=photo.jpg", got: {spec}')
        name, path = spec.rsplit("=", 1)
        m = re.search(r'\bname:\s*"' + re.escape(name.strip()) + '"', html[config_at:])
        if not m:
            sys.exit(f'Project "{name}" not found in CONFIG.projects')
        url, size, kb = to_data_url(load(path), args.width, args.quality)
        html = set_value(html, "image", url, config_at + m.end())
        report(f"project {name.strip()}", size, kb)

    html_path.write_text(html, encoding="utf-8")
    print(f"Updated {html_path}  ({html_path.stat().st_size / 1024:.0f} KB total)")


if __name__ == "__main__":
    main()
