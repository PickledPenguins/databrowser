// Mockup-only helpers: placeholder plot images and row click handling.
// The real generator would write <img src="..."> pointing at the tool's output files.

function rng(seed) {
  let s = seed >>> 0 || 1;
  return () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296;
}

function heat(v) {
  // viridis-ish ramp, v in [0, 1]
  const stops = [[68, 1, 84], [59, 82, 139], [33, 145, 140], [94, 201, 98], [253, 231, 37]];
  const x = Math.min(0.999, Math.max(0, v)) * (stops.length - 1);
  const i = Math.floor(x), f = x - i, a = stops[i], b = stops[i + 1];
  return `rgb(${a.map((c, k) => Math.round(c + (b[k] - c) * f)).join(",")})`;
}

function plotSvg(kind, seed) {
  const r = rng(seed), W = 240, H = 180;
  let body = "";
  if (kind === "heatmap") {
    const n = 24, fx = 1 + r() * 3, fy = 1 + r() * 3, ph = r() * 6;
    for (let i = 0; i < n; i++)
      for (let j = 0; j < n; j++) {
        const v = 0.5 + 0.25 * Math.sin(i / n * fx * 6 + ph) + 0.25 * Math.cos(j / n * fy * 6) + (r() - 0.5) * 0.15;
        body += `<rect x="${i * W / n}" y="${j * H / n}" width="${W / n + 0.5}" height="${H / n + 0.5}" fill="${heat(v)}"/>`;
      }
  } else {
    body += `<rect width="${W}" height="${H}" fill="#fff"/>`;
    body += `<path d="M30 10V160H232" stroke="#888" fill="none"/>`;
    if (kind === "line") {
      const f = 1 + r() * 4, d = r() * 3;
      let p = "";
      for (let x = 0; x <= 200; x += 4) {
        const y = 85 - 60 * Math.exp(-x / 200 * d) * Math.sin(x / 200 * f * 6) + (r() - 0.5) * 6;
        p += (x ? "L" : "M") + (32 + x) + " " + y.toFixed(1);
      }
      body += `<path d="${p}" stroke="#2f5fa7" stroke-width="1.6" fill="none"/>`;
    } else {
      const k = r() * 1.5 - 0.75;
      for (let i = 0; i < 80; i++) {
        const x = r() * 196, y = 85 - k * (x - 98) * 0.6 + (r() - 0.5) * 50;
        body += `<circle cx="${34 + x}" cy="${Math.min(158, Math.max(12, y)).toFixed(1)}" r="2" fill="#c0504d" fill-opacity=".7"/>`;
      }
    }
  }
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}">${body}</svg>`;
  return "data:image/svg+xml," + encodeURIComponent(svg);
}

function fillPlaceholders() {
  document.querySelectorAll("img[data-fake]").forEach(img => {
    const [kind, seed] = img.dataset.fake.split(":");
    img.src = plotSvg(kind, Number(seed));
  });
}

function wireRows() {
  document.querySelectorAll("tr[data-href]").forEach(tr =>
    tr.addEventListener("click", e => {
      if (e.target.closest("a")) return;
      location.href = tr.dataset.href;
    }));
}

function wireFilter() {
  const box = document.querySelector("#filter");
  if (!box) return;
  box.addEventListener("input", () => {
    const q = box.value.toLowerCase();
    document.querySelectorAll("table.groups tbody tr").forEach(tr =>
      tr.style.display = tr.textContent.toLowerCase().includes(q) ? "" : "none");
  });
}

document.addEventListener("DOMContentLoaded", () => {
  fillPlaceholders();
  wireRows();
  wireFilter();
});
