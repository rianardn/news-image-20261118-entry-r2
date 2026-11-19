#!/usr/bin/env python3
"""Render the 18 November 2026 front page: one 1024x1024 PNG.

Layout: navy masthead, red rule, one full-width lead, a 2x2 grid of
mid stories, a navy bottom strip for the science story, thin footer.
Everything is drawn from the STORIES table below; output is
deterministic (same bytes every run).
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
MARGIN = 36
INK = (18, 18, 18)
NAVY = (15, 30, 61)
GOLD = (212, 175, 55)
RED = (178, 34, 34)
PAPER = (250, 247, 240)
GREY = (110, 110, 110)
RULE = (200, 200, 200)
WHITE = (255, 255, 255)

BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
PLAIN = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# (section, headline, summary, sources)
STORIES = [
    (
        "THE GULF WAR",
        "Iran strikes US bases in Kuwait and Bahrain as the war widens",
        "Iranian drones hit Ali Al Salem Air Base in Kuwait \u2014 its first "
        "attack there since September \u2014 and Bahrain intercepted more "
        "strikes before dawn, hours after US jets hit an IRGC missile site "
        "on Qeshm Island. Three ships were struck near the Strait of Hormuz.",
        "Reuters \u00b7 AFP \u00b7 Al Jazeera",
    ),
    (
        "DIPLOMACY \u00b7 SHENZHEN",
        "Xi and Putin set the stage for a first Trump trilateral",
        "Xi Jinping and Vladimir Putin met in Shenzhen on the APEC sidelines, "
        "a day before their first-ever three-way meeting with Donald Trump, "
        "with Ukraine, Iran, nuclear arms and trade on the table.",
        "AFP \u00b7 AP \u00b7 NPR",
    ),
    (
        "WASHINGTON",
        "Peltola flips Alaska, handing Democrats a 56\u201344 Senate",
        "Democrat Mary Peltola defeated Republican Dan Sullivan, the ninth "
        "Democratic Senate flip of the midterms and the party\u2019s largest "
        "majority since 2009.",
        "AP \u00b7 Alaska Public Media",
    ),
    (
        "UKRAINE",
        "Ukraine hits the Crimean Bridge again as Russia strikes Odesa",
        "Kyiv struck the Kerch Bridge for a second straight night, shutting "
        "it down, as Russian strikes killed four people in the port city "
        "of Odesa.",
        "AP \u00b7 Kyiv Independent",
    ),
    (
        "HEALTH",
        "America loses measles-free status after 26 years",
        "The US lost its measles elimination status, held since 2000, with "
        "5,412 cases this year \u2014 the most since 1991 \u2014 and 10 deaths "
        "across 45 states.",
        "PAHO \u00b7 CDC",
    ),
    (
        "SPACE",
        "Voyager 1 crosses one light-day from Earth",
        "At 5:16 a.m. ET, Voyager 1 reached about 16 billion miles from "
        "home \u2014 the farthest any human-made object has ever travelled.",
        "NASA JPL",
    ),
]


class Typesetter:
    """Font cache plus word-wrap that returns fitted line lists."""

    def __init__(self):
        self._cache = {}

    def font(self, path, size):
        key = (path, size)
        if key not in self._cache:
            self._cache[key] = ImageFont.truetype(path, size)
        return self._cache[key]

    def wrap(self, draw, text, path, size, width, max_lines=None):
        fnt = self.font(path, size)
        words = text.split()
        lines, cur = [], ""
        for word in words:
            trial = f"{cur} {word}".strip()
            if draw.textlength(trial, font=fnt) <= width:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        if max_lines is not None:
            lines = lines[:max_lines]
        return lines, fnt

    def block(self, draw, xy, text, path, size, width, fill, leading=None,
              max_lines=None):
        """Draw wrapped text; return the y just below the last line."""
        lines, fnt = self.wrap(draw, text, path, size, width, max_lines)
        x, y = xy
        step = leading or int(size * 1.28)
        for line in lines:
            draw.text((x, y), line, font=fnt, fill=fill)
            y += step
        return y


def paint_masthead(draw, ts):
    draw.rectangle([0, 0, W, 128], fill=NAVY)
    title = ts.font(BOLD, 84)
    draw.text((MARGIN, 14), "THE WORLD TODAY", font=title, fill=WHITE)
    sub = ts.font(BOLD, 23)
    draw.text((MARGIN, 102), "WEDNESDAY, 18 NOVEMBER 2026",
              font=sub, fill=GOLD)
    right = "SIX STORIES THAT DEFINED THE DAY"
    rw = draw.textlength(right, font=sub)
    draw.text((W - MARGIN - rw, 102), right, font=sub, fill=WHITE)
    draw.rectangle([0, 128, W, 136], fill=RED)


def paint_lead(draw, ts, story):
    section, headline, summary, sources = story
    y = 152
    kick = ts.font(BOLD, 21)
    draw.text((MARGIN, y), section, font=kick, fill=RED)
    y += 30
    y = ts.block(draw, (MARGIN, y), headline, BOLD, 47, W - 2 * MARGIN,
                 INK, leading=56, max_lines=2)
    y += 8
    y = ts.block(draw, (MARGIN, y), summary, PLAIN, 24, W - 2 * MARGIN,
                 INK, leading=32, max_lines=4)
    y += 10
    src = ts.font(PLAIN, 17)
    draw.text((MARGIN, y), f"Sources: {sources}", font=src, fill=GREY)
    return y + 22


def paint_grid(draw, ts, stories, top):
    col_w = (W - 2 * MARGIN - 28) // 2
    row_h = 164
    for idx, story in enumerate(stories):
        section, headline, summary, sources = story
        col = idx % 2
        row = idx // 2
        x = MARGIN + col * (col_w + 28)
        y = top + row * row_h
        # number chip
        draw.rectangle([x, y + 2, x + 34, y + 30], fill=NAVY)
        chip = ts.font(BOLD, 18)
        draw.text((x + 11, y + 4), str(idx + 2), font=chip, fill=WHITE)
        lab = ts.font(BOLD, 19)
        draw.text((x + 44, y + 4), section, font=lab, fill=RED)
        yy = y + 38
        yy = ts.block(draw, (x, yy), headline, BOLD, 27, col_w, INK,
                      leading=33, max_lines=2)
        yy += 4
        ts.block(draw, (x, yy), summary, PLAIN, 19, col_w, INK,
                 leading=25, max_lines=2)
    return top + 2 * row_h


def paint_strip(draw, ts, story, y0):
    section, headline, summary, sources = story
    y1 = y0 + 132
    draw.rectangle([0, y0, W, y1], fill=NAVY)
    draw.rectangle([0, y0, W, y0 + 5], fill=GOLD)
    lab = ts.font(BOLD, 20)
    draw.text((MARGIN, y0 + 14), section, font=lab, fill=GOLD)
    src = ts.font(PLAIN, 16)
    src_txt = f"Source: {sources}"
    sw = draw.textlength(src_txt, font=src)
    draw.text((W - MARGIN - sw, y0 + 14), src_txt, font=src, fill=GOLD)
    head = ts.font(BOLD, 32)
    draw.text((MARGIN, y0 + 42), headline, font=head, fill=WHITE)
    ts.block(draw, (MARGIN, y0 + 84), summary, PLAIN, 20, W - 2 * MARGIN,
             (225, 225, 225), leading=26, max_lines=2)
    return y1


def paint_footer(draw, ts, y):
    foot = ts.font(PLAIN, 16)
    draw.text((MARGIN, y), "The day in one page \u00b7 Wednesday 18 November 2026",
              font=foot, fill=GREY)
    tag = "make.fun"
    tw = draw.textlength(tag, font=foot)
    draw.text((W - MARGIN - tw, y), tag, font=foot, fill=GREY)


def render(out_path):
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)
    ts = Typesetter()
    paint_masthead(draw, ts)
    y = paint_lead(draw, ts, STORIES[0])
    draw.line([(MARGIN, y), (W - MARGIN, y)], fill=RULE, width=2)
    y = paint_grid(draw, ts, STORIES[1:5], y + 14)
    y = paint_strip(draw, ts, STORIES[5], y + 12)
    paint_footer(draw, ts, y + 14)
    img.save(out_path, "PNG")
    return out_path


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="validate an existing output file")
    ap.add_argument("--out", default=None, help="output PNG path")
    args = ap.parse_args(argv)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    out_path = args.out or os.path.join(out_dir, "entry.png")
    if args.check:
        img = Image.open(out_path)
        assert img.size == (W, H), f"bad size {img.size}"
        assert img.format == "PNG", f"bad format {img.format}"
        print(f"OK {out_path} {img.size} {img.format}")
        return 0
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    render(out_path)
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
