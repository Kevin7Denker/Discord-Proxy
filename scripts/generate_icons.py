from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
BG = (40, 42, 54, 255)
SURFACE = (68, 71, 90, 115)
PURPLE = (189, 147, 249, 255)
CYAN = (139, 233, 253, 255)
GREEN = (80, 250, 123, 255)
MUTED = (98, 114, 164, 255)
PINK = (255, 121, 198, 255)
RED = (255, 85, 85, 255)
WHITE = (248, 248, 242, 255)


def shield_points(size: int, scale_factor: float = 1.0) -> list[tuple[float, float]]:
    points = [
        (0.50 * size, 0.18 * size),
        (0.72 * size, 0.27 * size),
        (0.72 * size, 0.48 * size),
        (0.67 * size, 0.62 * size),
        (0.50 * size, 0.77 * size),
        (0.33 * size, 0.62 * size),
        (0.28 * size, 0.48 * size),
        (0.28 * size, 0.27 * size),
    ]
    if scale_factor == 1.0:
        return points
    center_x = 0.50 * size
    center_y = 0.49 * size
    return [
        (center_x + (x - center_x) * scale_factor, center_y + (y - center_y) * scale_factor)
        for x, y in points
    ]


def make_icon(size: int, *, active: bool = False, app_icon: bool = True) -> Image.Image:
    scale = size / 256
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    radius = int(52 * scale)
    shadow_draw.rounded_rectangle(
        (int(22 * scale), int(22 * scale), int(234 * scale), int(234 * scale)),
        radius=radius,
        fill=(12, 14, 24, 210),
    )
    image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(max(1, int(10 * scale)))))

    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (int(20 * scale), int(18 * scale), int(236 * scale), int(236 * scale)),
        radius=radius,
        fill=BG,
    )
    draw.rounded_rectangle(
        (int(25 * scale), int(23 * scale), int(231 * scale), int(231 * scale)),
        radius=int(44 * scale),
        outline=(255, 255, 255, 22),
        width=max(1, int(2 * scale)),
    )
    draw.pieslice(
        (int(-60 * scale), int(-55 * scale), int(265 * scale), int(250 * scale)),
        205,
        342,
        fill=SURFACE,
    )
    draw.line(
        (int(35 * scale), int(211 * scale), int(221 * scale), int(45 * scale)),
        fill=(139, 233, 253, 26),
        width=max(1, int(7 * scale)),
    )

    ring_box = (int(58 * scale), int(55 * scale), int(198 * scale), int(195 * scale))
    draw.ellipse(ring_box, outline=(139, 233, 253, 48), width=max(2, int(5 * scale)))
    draw.arc(ring_box, start=210, end=42, fill=PURPLE, width=max(3, int(8 * scale)))
    draw.arc(
        (int(72 * scale), int(69 * scale), int(184 * scale), int(181 * scale)),
        start=28,
        end=190,
        fill=CYAN if active else MUTED,
        width=max(2, int(5 * scale)),
    )

    symbol_scale = 0.84 if app_icon else 0.92
    vertical_offset = int(10 * scale) if app_icon else int(16 * scale)
    points = [(x, y + vertical_offset) for x, y in shield_points(size, symbol_scale)]
    draw.line(points + [points[0]], fill=WHITE, width=max(3, int(11 * scale)), joint="curve")
    draw.line(
        points + [points[0]],
        fill=PURPLE if app_icon else (GREEN if active else MUTED),
        width=max(2, int(7 * scale)),
        joint="curve",
    )
    draw.line(
        (
            int(0.50 * size),
            int(0.36 * size) + vertical_offset,
            int(0.50 * size),
            int(0.58 * size) + vertical_offset,
        ),
        fill=(139, 233, 253, 210),
        width=max(2, int(4 * scale)),
    )

    if app_icon:
        draw.rounded_rectangle(
            (int(158 * scale), int(185 * scale), int(215 * scale), int(202 * scale)),
            radius=int(8 * scale),
            fill=CYAN,
        )
        draw.rounded_rectangle(
            (int(158 * scale), int(207 * scale), int(198 * scale), int(224 * scale)),
            radius=int(8 * scale),
            fill=PINK,
        )
    else:
        status = GREEN if active else RED
        draw.ellipse(
            (int(169 * scale), int(169 * scale), int(224 * scale), int(224 * scale)),
            fill=status,
            outline=BG,
            width=max(2, int(8 * scale)),
        )

    return image


def make_tray_icon(size: int, *, active: bool) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    scale = size / 64
    status = GREEN if active else MUTED
    glow = GREEN if active else RED

    draw.rounded_rectangle(
        (int(5 * scale), int(5 * scale), int(59 * scale), int(59 * scale)),
        radius=int(14 * scale),
        fill=BG,
        outline=(255, 255, 255, 46),
        width=max(1, int(2 * scale)),
    )
    draw.arc(
        (int(10 * scale), int(10 * scale), int(54 * scale), int(54 * scale)),
        218,
        38,
        fill=PURPLE,
        width=max(2, int(5 * scale)),
    )
    draw.arc(
        (int(10 * scale), int(10 * scale), int(54 * scale), int(54 * scale)),
        38,
        210,
        fill=CYAN,
        width=max(2, int(4 * scale)),
    )

    shield = [
        (32 * scale, 15 * scale),
        (46 * scale, 21 * scale),
        (46 * scale, 34 * scale),
        (42 * scale, 43 * scale),
        (32 * scale, 51 * scale),
        (22 * scale, 43 * scale),
        (18 * scale, 34 * scale),
        (18 * scale, 21 * scale),
    ]
    draw.line(shield + [shield[0]], fill=WHITE, width=max(2, int(5 * scale)), joint="curve")
    draw.line(shield + [shield[0]], fill=status, width=max(1, int(3 * scale)), joint="curve")
    draw.line((32 * scale, 25 * scale, 32 * scale, 42 * scale), fill=CYAN, width=max(1, int(3 * scale)))

    draw.ellipse(
        (int(42 * scale), int(42 * scale), int(58 * scale), int(58 * scale)),
        fill=glow,
        outline=BG,
        width=max(1, int(3 * scale)),
    )
    return image


def main() -> None:
    ASSETS_DIR.mkdir(exist_ok=True)
    sizes = [16, 24, 32, 48, 64, 128, 256]
    icon_images = [make_icon(size, app_icon=True) for size in sizes]
    icon_images[-1].save(
        ASSETS_DIR / "icon.ico",
        sizes=[(size, size) for size in sizes],
        append_images=icon_images[:-1],
    )
    make_icon(256, app_icon=True).save(ASSETS_DIR / "icon.png")
    make_tray_icon(64, active=False).save(ASSETS_DIR / "tray-idle.png")
    make_tray_icon(64, active=True).save(ASSETS_DIR / "tray-active.png")


if __name__ == "__main__":
    main()
