// Draws the hero horizon in the app icon's dithered style: a planet's rim
// rising out of the bottom of the frame, one PNG pixel per dither cell. The
// site scales it up with `image-rendering: pixelated`, so the cells stay crisp.
//
//   node scripts/make-horizon.mjs
//
// Writes public/horizon-dark.png and public/horizon-light.png.
import { writeFileSync } from "node:fs";
import { deflateSync } from "node:zlib";

const W = 640;
const H = 220;

const BAYER = [
  [0, 8, 2, 10],
  [12, 4, 14, 6],
  [3, 11, 1, 9],
  [15, 7, 13, 5],
].map((row) => row.map((v) => (v + 0.5) / 16));

const themes = {
  dark: ["#050a1f", "#0a124a", "#1a35b8", "#4271ff", "#86a5ff", "#dfe6fb"],
  light: ["#f4f6fc", "#e1e8fd", "#b6c8ff", "#7b9bff", "#4271ff", "#2d5cf0"],
};

const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));

// 0 is empty sky, 1 is the brightest part of the rim.
function intensity(x, y) {
  const cx = W / 2;
  const r = W * 1.15;
  const top = H * 0.42;
  const dx = x - cx;
  const arcY = top + r - Math.sqrt(Math.max(0, r * r - dx * dx));
  const d = y - arcY;
  const edge = 1 - Math.min(1, Math.abs(dx) / (W * 0.62)) ** 2;
  if (d < 0) return Math.exp(d / (H * 0.16)) * 0.62 * (0.35 + 0.65 * edge);
  const body = Math.exp(-d / (H * 0.2));
  return Math.min(1, 0.55 + 0.45 * body) * (0.55 + 0.45 * edge);
}

function png(w, h, rgb) {
  const crcTable = Array.from({ length: 256 }, (_, n) => {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    return c >>> 0;
  });
  const crc = (buf) => {
    let c = 0xffffffff;
    for (const b of buf) c = crcTable[(c ^ b) & 0xff] ^ (c >>> 8);
    return (c ^ 0xffffffff) >>> 0;
  };
  const chunk = (type, data) => {
    const len = Buffer.alloc(4);
    len.writeUInt32BE(data.length);
    const body = Buffer.concat([Buffer.from(type), data]);
    const sum = Buffer.alloc(4);
    sum.writeUInt32BE(crc(body));
    return Buffer.concat([len, body, sum]);
  };
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(w, 0);
  ihdr.writeUInt32BE(h, 4);
  ihdr[8] = 8;
  ihdr[9] = 2;
  const raw = Buffer.alloc((w * 3 + 1) * h);
  for (let y = 0; y < h; y++) {
    raw[y * (w * 3 + 1)] = 0;
    rgb.copy(raw, y * (w * 3 + 1) + 1, y * w * 3, (y + 1) * w * 3);
  }
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk("IHDR", ihdr),
    chunk("IDAT", deflateSync(raw, { level: 9 })),
    chunk("IEND", Buffer.alloc(0)),
  ]);
}

for (const [name, ramp] of Object.entries(themes)) {
  const stops = ramp.map(hex);
  const out = Buffer.alloc(W * H * 3);
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const v = intensity(x, y) * (stops.length - 1);
      const i = Math.min(stops.length - 2, Math.floor(v));
      const pick = v - i > BAYER[y % 4][x % 4] ? i + 1 : i;
      stops[pick].forEach((c, k) => (out[(y * W + x) * 3 + k] = c));
    }
  }
  writeFileSync(new URL(`../public/horizon-${name}.png`, import.meta.url), png(W, H, out));
}
