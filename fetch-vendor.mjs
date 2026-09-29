// یک‌بار روی کامپیوتر (با اینترنت/VPN) اجرا کنید:  node fetch-vendor.mjs www
// Tailwind، Font Awesome و فونت‌های فارسی را در www/vendor/ ذخیره می‌کند تا برنامه بدون CDN و آفلاین کار کند.
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';

const OUT = path.join(process.argv[2] || 'www', 'vendor');
const GH = 'https://cdn.jsdelivr.net/gh/rastikerdar/';
const SETS = [ // [پوشه, ریشه‌ی URL, مسیر CSS نسبت به ریشه]
  ['vazirmatn', GH + 'vazirmatn@v33.003/', 'Vazirmatn-font-face.css'],
  ['vazir', GH + 'vazir-font@v30.1.0/', 'dist/font-face.css'],
  ['sahel', GH + 'sahel-font@v3.4.0/', 'dist/font-face.css'],
  ['samim', GH + 'samim-font@v3.0.0/', 'dist/font-face.css'],
  ['shabnam', GH + 'shabnam-font@v4.0.1/', 'dist/font-face.css'],
  ['fontawesome', 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/', 'css/all.min.css']
];

async function get(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} ${url}`);
  return Buffer.from(await r.arrayBuffer());
}
async function save(file, buf) {
  await mkdir(path.dirname(file), { recursive: true });
  await writeFile(file, buf);
  console.log('✓', file, Math.round(buf.length / 1024) + ' KB');
}

await save(path.join(OUT, 'tailwind.js'), await get('https://cdn.tailwindcss.com'));
for (const [name, root, cssPath] of SETS) {
  const cssUrl = root + cssPath;
  const css = await get(cssUrl);
  await save(path.join(OUT, name, cssPath), css);
  const refs = [...new Set([...css.toString().matchAll(/url\(\s*['"]?([^'")]+?)['"]?\s*\)/g)]
    .map(m => { try { const u = new URL(m[1], cssUrl); u.hash = ''; u.search = ''; return u.protocol.startsWith('http') ? u.href : null; } catch { return null; } })
    .filter(Boolean))];
  const w2 = refs.filter(u => u.endsWith('.woff2')); // فقط woff2 کافی است (WebView اندروید و مرورگرهای جدید)
  for (const u of (w2.length ? w2 : refs)) {
    if (!u.startsWith(root)) { console.warn('رد شد (خارج از ریشه):', u); continue; }
    await save(path.join(OUT, name, u.slice(root.length)), await get(u));
  }
}
console.log('\nتمام شد. حالا: npx cap sync android  و ساخت دوباره‌ی APK');
