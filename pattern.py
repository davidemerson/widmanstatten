import math, random, secrets
from datetime import datetime, timezone
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color

# --- noise helpers (same as before) ---
def hash2(ix, iy, seed=0):
    n = (ix * 374761393 + iy * 668265263 + seed * 69069) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFFFFFF) / 2**32

def smoothstep(t): return t*t*(3-2*t)

def value_noise(x, y, seed=0, cell=256.0):
    fx, fy = x / cell, y / cell
    ix, iy = int(math.floor(fx)), int(math.floor(fy))
    tx, ty = fx - ix, fy - iy
    sx, sy = smoothstep(tx), smoothstep(ty)

    v00 = hash2(ix,   iy,   seed)
    v10 = hash2(ix+1, iy,   seed)
    v01 = hash2(ix,   iy+1, seed)
    v11 = hash2(ix+1, iy+1, seed)

    a = v00*(1-sx) + v10*sx
    b = v01*(1-sx) + v11*sx
    return a*(1-sy) + b*sy

def fbm(x, y, seed=0, base_cell=512.0, octaves=5, lacunarity=2.0, gain=0.5):
    amp, freq = 1.0, 1.0
    s = 0.0
    norm = 0.0
    for o in range(octaves):
        s += amp * value_noise(x*freq, y*freq, seed=seed+101*o, cell=base_cell)
        norm += amp
        amp *= gain
        freq *= lacunarity
    return s / norm

def sample_angle_mixture(modes):
    total = sum(w for _, _, w in modes)
    r = random.random() * total
    acc = 0.0
    for mu, sigma, w in modes:
        acc += w
        if r <= acc:
            return (random.gauss(mu, sigma)) % math.pi
    return modes[-1][0] % math.pi

def in_bounds(x, y, W, H, pad=0):
    return (-pad <= x <= W + pad) and (-pad <= y <= H + pad)

def timestamp_slug():
    # YYYY-MM-DD-HH-MM-SS.SS (UTC)
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%d-%H-%M-%S.") + f"{int(now.microsecond/10000):02d}"

def generate_meteorite_pdf(
    W=3000, H=1800,
    out_prefix="meteorite",
    out_dir=".",
    seed=None,   # None => random every run
    angle_modes=((45, 4, 4.0), (135, 4, 4.0), (0, 6, 1.3), (90, 6, 1.3), (60, 5, 1.5)),
    families=7,
    base_spacing=18.0,
    spacing_logn_sigma=0.25,
    base_stroke=1.2,
    alpha_min=0.18,
    alpha_max=0.55,
    ghost_min=0,
    ghost_max=2,
    ghost_offset=2.2,
    lateral_jitter=1.6,
    jitter_freq=120.0,
    gap_prob=0.10,
    grain_cell=520.0
):
    # Seed handling:
    # - If seed is None, pick a fresh unpredictable seed each run.
    if seed is None:
        seed = secrets.randbits(64)

    # Ensure all randomness uses this seed (pattern is reproducible if you pass it explicitly)
    random.seed(seed)

    modes = [(math.radians(mu), math.radians(sig), w) for mu, sig, w in angle_modes]

    # Timestamped output so we never overwrite
    stamp = timestamp_slug()
    out_path = f"{out_dir.rstrip('/')}/{out_prefix}-{stamp}.pdf"

    c = canvas.Canvas(out_path, pagesize=(W, H))

    # Background
    c.setFillColor(Color(0.91, 0.89, 0.84, alpha=1.0))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    def G(x, y):
        return fbm(x, y, seed=int(seed & 0x7FFFFFFF), base_cell=grain_cell, octaves=5)

    ink_rgb = (0.23, 0.21, 0.19)

    for _fam in range(families):
        theta = sample_angle_mixture(modes)
        dx, dy = math.cos(theta), math.sin(theta)
        nx, ny = -dy, dx

        fam_spacing = base_spacing * (0.75 + 0.7 * random.random())
        span = abs(nx) * W + abs(ny) * H
        n_lines = int(span / fam_spacing) + 80

        offset = -span / 2 - 200.0
        cx, cy = W / 2, H / 2

        L = math.hypot(W, H) * 1.3
        t0, t1 = -L, L
        step_t = 30.0
        n_steps = int((t1 - t0) / step_t)

        for _i in range(n_lines):
            offset += fam_spacing * math.exp(random.gauss(0.0, spacing_logn_sigma))
            px, py = cx + offset * nx, cy + offset * ny

            run = []
            for s in range(n_steps + 1):
                t = t0 + (t1 - t0) * (s / n_steps)
                x = px + t * dx
                y = py + t * dy

                g = G(x, y)
                wig = math.sin((t + 1000 * g) / jitter_freq * 2 * math.pi)
                j = (wig * 0.6 + (g - 0.5) * 0.8) * lateral_jitter

                xj = x + j * nx
                yj = y + j * ny

                if (random.random() < gap_prob * (0.6 + 0.8 * g)) or (not in_bounds(xj, yj, W, H, pad=80)):
                    if len(run) >= 2:
                        mx, my = run[len(run)//2]
                        gmid = G(mx, my)

                        stroke_w = base_stroke * (0.65 + 1.0 * gmid) * (0.7 + 0.6 * random.random())
                        alpha = alpha_min + (alpha_max - alpha_min) * gmid

                        c.setStrokeColor(Color(*ink_rgb, alpha=alpha))
                        c.setLineWidth(stroke_w)
                        c.setLineCap(1)
                        c.setLineJoin(1)

                        p = c.beginPath()
                        p.moveTo(run[0][0], run[0][1])
                        for (xx, yy) in run[1:]:
                            p.lineTo(xx, yy)
                        c.drawPath(p, stroke=1, fill=0)

                        ghosts = random.randint(ghost_min, ghost_max)
                        for _g in range(ghosts):
                            off = random.uniform(-ghost_offset, ghost_offset) * (0.3 + 1.2 * gmid)
                            c.setStrokeColor(Color(*ink_rgb, alpha=alpha * 0.55))
                            c.setLineWidth(max(0.35, stroke_w * 0.75))

                            pg = c.beginPath()
                            pg.moveTo(run[0][0] + off * nx, run[0][1] + off * ny)
                            for (xx, yy) in run[1:]:
                                pg.lineTo(xx + off * nx, yy + off * ny)
                            c.drawPath(pg, stroke=1, fill=0)

                    run = []
                else:
                    run.append((xj, yj))

            if len(run) >= 2:
                mx, my = run[len(run)//2]
                gmid = G(mx, my)

                stroke_w = base_stroke * (0.65 + 1.0 * gmid) * (0.7 + 0.6 * random.random())
                alpha = alpha_min + (alpha_max - alpha_min) * gmid

                c.setStrokeColor(Color(*ink_rgb, alpha=alpha))
                c.setLineWidth(stroke_w)
                c.setLineCap(1)
                c.setLineJoin(1)

                p = c.beginPath()
                p.moveTo(run[0][0], run[0][1])
                for (xx, yy) in run[1:]:
                    p.lineTo(xx, yy)
                c.drawPath(p, stroke=1, fill=0)

    c.showPage()
    c.save()

    return out_path, seed

if __name__ == "__main__":
    path, seed_used = generate_meteorite_pdf(W=3000, H=1800, seed=None)
    print("Wrote:", path)
    print("Seed:", seed_used)
