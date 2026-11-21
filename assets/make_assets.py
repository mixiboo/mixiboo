"""mixiboo 프로필용 배너/푸터 SVG 생성기.

글자는 폰트를 그대로 넣지 않고 SVG 경로(path)로 바꿔서 넣는다.
그래서 어떤 기기·브라우저에서 봐도 똑같이 보인다.

글자를 바꾸는 방법:
  1. 아래 TITLE, SUBTITLE, FOOTER_TEXT 문장을 원하는 대로 고친다
  2. pip install fonttools
  3. assets 폴더 안에서 python make_assets.py 실행
  4. 새로 생긴 banner.svg, footer.svg 를 커밋해서 올린다
"""
import io
import math
import random
import re
import sys
import urllib.parse
import urllib.request

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

OUT = sys.argv[1] if len(sys.argv) > 1 else "."

TITLE = "mixiboo"
SUBTITLE = "최민준의 작은 은하수"
FOOTER_TEXT = "들러줘서 고마워요"


def fetch_font(family_query, text):
    url = "https://fonts.googleapis.com/css2?family=%s&text=%s" % (
        family_query,
        urllib.parse.quote(text),
    )
    css = urllib.request.urlopen(url, timeout=30).read().decode()
    font_url = re.search(r"url\((.*?)\)", css).group(1)
    data = urllib.request.urlopen(font_url, timeout=30).read()
    return TTFont(io.BytesIO(data))


def text_to_path(font, text, size, letter_spacing=0.0):
    """글자를 path 문자열로 바꾸고 (path, (xmin, ymin, xmax, ymax))를 돌려준다."""
    glyphs = font.getGlyphSet()
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    scale = size / font["head"].unitsPerEm
    x = 0.0
    parts = []
    bounds = BoundsPen(glyphs)
    for ch in text:
        name = cmap.get(ord(ch))
        if name is None:
            x += size * 0.3 + letter_spacing
            continue
        pen = SVGPathPen(glyphs, ntos=lambda v: ("%.2f" % v).rstrip("0").rstrip("."))
        transform = (scale, 0, 0, -scale, x, 0)
        glyphs[name].draw(TransformPen(pen, transform))
        glyphs[name].draw(TransformPen(bounds, transform))
        cmd = pen.getCommands()
        if cmd:
            parts.append(cmd)
        x += hmtx[name][0] * scale + letter_spacing
    return " ".join(parts), bounds.bounds


def placed(path_and_bounds, cx, cy):
    """글자 묶음의 가운데가 (cx, cy)에 오도록 옮기는 transform을 만든다."""
    _, (x0, y0, x1, y1) = path_and_bounds
    dx = cx - (x0 + x1) / 2
    dy = cy - (y0 + y1) / 2
    return "translate(%.2f %.2f)" % (dx, dy)


def sparkle_path(r):
    return "M0 %.1f Q0 0 %.1f 0 Q0 0 0 %.1f Q0 0 %.1f 0 Q0 0 0 %.1f Z" % (-r, r, r, -r, -r)


STAR_COLORS = ["#FFFFFF", "#FFFFFF", "#E9D5FF", "#F5D0FE", "#FDE68A", "#C7D2FE"]


def stars(rng, count, w, h, avoid=None, rmin=0.6, rmax=2.0, animated=True, region=None):
    out = []
    tries = 0
    while len(out) < count and tries < count * 50:
        tries += 1
        x = rng.uniform(8, w - 8)
        y = rng.uniform(8, h - 8)
        if region and not region(x, y):
            continue
        r = rmin + (rmax - rmin) * (rng.random() ** 2.4)
        if avoid and r > 1.0:
            ax0, ay0, ax1, ay1 = avoid
            if ax0 < x < ax1 and ay0 < y < ay1:
                continue
        color = rng.choice(STAR_COLORS)
        if animated:
            dur = rng.uniform(2.4, 5.2)
            delay = -rng.uniform(0, dur)
            out.append(
                '<circle class="tw" cx="%.1f" cy="%.1f" r="%.2f" fill="%s" '
                'style="animation-duration:%.1fs;animation-delay:%.1fs"/>'
                % (x, y, r, color, dur, delay)
            )
        else:
            out.append(
                '<circle cx="%.1f" cy="%.1f" r="%.2f" fill="%s" opacity="%.2f"/>'
                % (x, y, r, color, rng.uniform(0.25, 0.75))
            )
    return "\n    ".join(out)


def milky_dust(rng, count, x0, y0, x1, y1, spread):
    """은하수 띠를 따라 아주 작은 별가루를 뿌린다."""
    out = []
    length = math.hypot(x1 - x0, y1 - y0)
    nx, ny = -(y1 - y0) / length, (x1 - x0) / length
    for _ in range(count):
        t = rng.random()
        off = rng.gauss(0, spread)
        x = x0 + (x1 - x0) * t + nx * off
        y = y0 + (y1 - y0) * t + ny * off
        r = rng.uniform(0.35, 0.9)
        out.append(
            '<circle cx="%.1f" cy="%.1f" r="%.2f" fill="#F3E8FF" opacity="%.2f"/>'
            % (x, y, r, rng.uniform(0.25, 0.8))
        )
    return "\n    ".join(out)


STYLE = """
    .tw { animation: twinkle 3.6s ease-in-out infinite; }
    @keyframes twinkle { 0%, 100% { opacity: .25; } 50% { opacity: 1; } }
    .sp { transform-box: fill-box; transform-origin: center; animation: sparkle 4.2s ease-in-out infinite; }
    @keyframes sparkle {
      0%, 100% { transform: scale(.55) rotate(0deg); opacity: .55; }
      50% { transform: scale(1.1) rotate(45deg); opacity: 1; }
    }
    .shoot { opacity: 0; animation: shoot 9s linear infinite; }
    @keyframes shoot {
      0% { transform: translate(0, 0); opacity: 0; }
      2% { opacity: 1; }
      13% { transform: translate(-440px, 220px); opacity: 0; }
      100% { transform: translate(-440px, 220px); opacity: 0; }
    }
    .glow { animation: breathe 5s ease-in-out infinite; }
    @keyframes breathe { 0%, 100% { opacity: .55; } 50% { opacity: .9; } }
    @media (prefers-reduced-motion: reduce) {
      .tw, .sp, .shoot, .glow { animation: none; }
      .shoot { display: none; }
    }
"""


def shooting_star(head_x, head_y, length, delay, gid):
    ang = math.atan2(-220, 440)  # 진행 방향: 왼쪽 아래
    tx = head_x - math.cos(ang) * length
    ty = head_y - math.sin(ang) * length
    return (
        '<linearGradient id="%s" gradientUnits="userSpaceOnUse" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f">'
        '<stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>'
        "</linearGradient>"
        % (gid, head_x, head_y, tx, ty),
        '<g class="shoot" style="animation-delay:%.1fs">'
        '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="url(#%s)" stroke-width="2.2" stroke-linecap="round"/>'
        '<circle cx="%.1f" cy="%.1f" r="2.2" fill="#FFFFFF"/>'
        "</g>"
        % (delay, head_x, head_y, tx, ty, gid, head_x, head_y),
    )


def sparkle(x, y, r, color, delay):
    return (
        '<g transform="translate(%.1f %.1f)"><path class="sp" d="%s" fill="%s" style="animation-delay:%.1fs"/></g>'
        % (x, y, sparkle_path(r), color, delay)
    )


def make_banner(fredoka, jua):
    W, H = 1200, 300
    rng = random.Random(20261121)
    title = text_to_path(fredoka, TITLE, 118, letter_spacing=3)
    sub = text_to_path(jua, SUBTITLE, 32, letter_spacing=2)
    t_cx, t_cy = 600, 122
    s_cx, s_cy = 600, 205
    tx0, ty0, tx1, ty1 = title[1]
    tw, th = tx1 - tx0, ty1 - ty0
    avoid = (t_cx - tw / 2 - 30, t_cy - th / 2 - 25, t_cx + tw / 2 + 30, s_cy + 30)

    shape = (
        "M0 20 Q0 0 20 0 H1180 Q1200 0 1200 20 V250 "
        "C1080 302 960 214 800 246 C640 278 520 214 360 244 C220 270 100 258 0 236 Z"
    )
    g1 = shooting_star(1090, 24, 150, 1.5, "tail1")
    g2 = shooting_star(760, 6, 120, 6.0, "tail2")

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="title desc">
  <title id="title">{TITLE}</title>
  <desc id="desc">{SUBTITLE}</desc>
  <defs>
    <style>{STYLE}</style>
    <linearGradient id="sky" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0A0A1F"/>
      <stop offset=".5" stop-color="#1C1650"/>
      <stop offset="1" stop-color="#3B1C72"/>
    </linearGradient>
    <radialGradient id="nebula" cx=".82" cy=".9" r=".55">
      <stop offset="0" stop-color="#C026D3" stop-opacity=".35"/>
      <stop offset="1" stop-color="#C026D3" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="nebula2" cx=".12" cy=".15" r=".45">
      <stop offset="0" stop-color="#4F46E5" stop-opacity=".35"/>
      <stop offset="1" stop-color="#4F46E5" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="titleFill" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FFFFFF"/>
      <stop offset="1" stop-color="#E9D5FF"/>
    </linearGradient>
    <filter id="band" x="-20%" y="-200%" width="140%" height="500%"><feGaussianBlur stdDeviation="26"/></filter>
    <filter id="soft" x="-30%" y="-60%" width="160%" height="220%"><feGaussianBlur stdDeviation="12"/></filter>
    <clipPath id="frame"><path d="{shape}"/></clipPath>
    {g1[0]}
    {g2[0]}
  </defs>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#sky)"/>
    <rect width="{W}" height="{H}" fill="url(#nebula)"/>
    <rect width="{W}" height="{H}" fill="url(#nebula2)"/>
    <g filter="url(#band)" transform="rotate(-9 600 150)">
      <ellipse cx="600" cy="150" rx="700" ry="46" fill="#6D28D9" opacity=".55"/>
      <ellipse cx="520" cy="146" rx="420" ry="24" fill="#A855F7" opacity=".5"/>
      <ellipse cx="780" cy="158" rx="280" ry="16" fill="#F0ABFC" opacity=".35"/>
    </g>
    {milky_dust(rng, 260, -20, 245, 1220, 55, 26)}
    {stars(rng, 70, W, H, avoid=avoid, rmin=0.6, rmax=2.1)}
    {sparkle(278, 70, 11, "#FDE68A", 0)}
    {sparkle(930, 92, 9, "#F5D0FE", -1.4)}
    {sparkle(1058, 186, 7, "#FFFFFF", -2.6)}
    {sparkle(150, 188, 6, "#E9D5FF", -0.8)}
    {sparkle(860, 36, 5, "#FFFFFF", -3.1)}
    {g1[1]}
    {g2[1]}
    <g class="glow"><path d="{title[0]}" transform="{placed(title, t_cx, t_cy)}" fill="#A78BFA" filter="url(#soft)"/></g>
    <g><path d="{title[0]}" transform="{placed(title, t_cx, t_cy)}" fill="url(#titleFill)"/></g>
    <g><path d="{sub[0]}" transform="{placed(sub, s_cx, s_cy)}" fill="#E9D5FF"/></g>
  </g>
</svg>
"""
    return svg


def make_footer(jua):
    W, H = 1200, 170
    rng = random.Random(7)
    text = text_to_path(jua, FOOTER_TEXT, 30, letter_spacing=2)
    tx0, ty0, tx1, ty1 = text[1]
    cx, cy = 600, 116
    half = (tx1 - tx0) / 2
    shape = (
        "M0 62 C130 30 270 40 410 64 C570 92 690 42 850 54 C990 64 1090 98 1200 72 "
        "V150 Q1200 170 1180 170 H20 Q0 170 0 150 Z"
    )
    avoid = (cx - half - 40, cy - 30, cx + half + 40, cy + 30)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="title">
  <title id="title">{FOOTER_TEXT}</title>
  <defs>
    <style>{STYLE}</style>
    <linearGradient id="sky" x1="1" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#0A0A1F"/>
      <stop offset=".5" stop-color="#1C1650"/>
      <stop offset="1" stop-color="#3B1C72"/>
    </linearGradient>
    <radialGradient id="nebula" cx=".2" cy=".9" r=".6">
      <stop offset="0" stop-color="#C026D3" stop-opacity=".3"/>
      <stop offset="1" stop-color="#C026D3" stop-opacity="0"/>
    </radialGradient>
    <filter id="band" x="-20%" y="-200%" width="140%" height="500%"><feGaussianBlur stdDeviation="20"/></filter>
    <clipPath id="frame"><path d="{shape}"/></clipPath>
  </defs>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#sky)"/>
    <rect width="{W}" height="{H}" fill="url(#nebula)"/>
    <g filter="url(#band)" transform="rotate(5 600 110)">
      <ellipse cx="600" cy="112" rx="700" ry="26" fill="#6D28D9" opacity=".5"/>
      <ellipse cx="640" cy="114" rx="360" ry="14" fill="#A855F7" opacity=".45"/>
    </g>
    {milky_dust(rng, 120, -20, 70, 1220, 150, 16)}
    {stars(rng, 36, W, H, avoid=avoid, rmin=0.6, rmax=1.9, region=lambda x, y: y > 70)}
    <g><path d="{text[0]}" transform="{placed(text, cx, cy)}" fill="#F3E8FF"/></g>
    {sparkle(cx - half - 26, cy - 2, 8, "#FDE68A", 0)}
    {sparkle(cx + half + 26, cy - 2, 8, "#F5D0FE", -2.1)}
  </g>
</svg>
"""
    return svg


def main():
    fredoka = fetch_font("Fredoka:wght@600", TITLE)
    jua = fetch_font("Jua", SUBTITLE + FOOTER_TEXT)
    with open(f"{OUT}/banner.svg", "w", encoding="utf-8") as f:
        f.write(make_banner(fredoka, jua))
    with open(f"{OUT}/footer.svg", "w", encoding="utf-8") as f:
        f.write(make_footer(jua))
    print("ok")


if __name__ == "__main__":
    main()
