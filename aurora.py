#!/usr/bin/env python3
"""aurora-gen: a small night-sky landscape generator.

    python aurora.py --seed 7 --out sky.png
"""
import argparse
import numpy as np
from PIL import Image

W, H, HORIZON = 1920, 1200, 820


def noise_1d(rng, n, scales):
    out, amp = np.zeros(n), 1.0
    for s in scales:
        k = max(2, n // s + 2)
        out += amp * np.interp(np.linspace(0, k - 1, n), np.arange(k), rng.uniform(-1, 1, k))
        amp *= 0.5
    return out / np.abs(out).max()


def render(seed):
    rng = np.random.default_rng(seed)
    y = np.arange(H)[:, None].astype(float)
    x = np.arange(W)[None, :].astype(float)
    t = np.clip(y / HORIZON, 0, 1)[..., None]
    img = np.array([4, 7, 20.0]) * (1 - t) + np.array([14, 32, 48.0]) * t
    img = np.broadcast_to(img, (H, W, 3)).copy()

    # stars
    sx, sy = rng.integers(0, W, 2600), rng.integers(0, HORIZON - 40, 2600)
    img[sy, sx] += (rng.power(4, 2600) * 230)[:, None]

    # aurora curtains
    green, teal, magenta = np.array([70, 255, 150.0]), np.array([40, 200, 210.0]), np.array([235, 70, 200.0])
    for base, amp, wl, hgt, strength in [(470, 70, 900, 330, 1.0), (400, 55, 650, 280, 0.75), (540, 40, 1200, 220, 0.55)]:
        edge = base + amp * np.sin(2 * np.pi * x[0] / wl + rng.uniform(0, 6)) + 25 * noise_1d(rng, W, [400, 120, 40])
        rays = np.clip(0.55 + 0.45 * noise_1d(rng, W, [90, 30, 9]), 0.05, 1)
        d = edge[None, :] - y
        inten = np.where(d >= 0, np.exp(-np.clip(d, 0, None) / hgt), np.exp(-np.clip(-d, 0, None) / 10)) * rays * strength
        frac = np.clip(d / hgt, 0, 1)[..., None]
        col = green * (1 - frac) ** 1.5 + teal * np.clip(1 - np.abs(frac - .45) * 3, 0, 1) * .6
        col += magenta * np.exp(-((frac - .85) ** 2) / .02) * .9
        img += col * inten[..., None] * 0.62 * (y < HORIZON)[..., None]

    # ridges
    for base, rough, colr in [(700, 45, (18, 30, 44)), (745, 35, (11, 20, 31)), (790, 20, (6, 11, 18))]:
        prof = base + rough * noise_1d(rng, W, [400, 120, 30])
        m = (y >= prof[None, :]) & (y < HORIZON)
        img = np.where(m[..., None], np.array(colr, float), img)

    # lake
    refl = img[HORIZON - (H - HORIZON):HORIZON][::-1]
    img[HORIZON:] = refl * np.linspace(.55, .3, H - HORIZON)[:, None, None]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default="sky.png")
    a = ap.parse_args()
    render(a.seed).save(a.out)
    print("saved", a.out)
