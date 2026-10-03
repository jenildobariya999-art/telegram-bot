// Vercel serverless function: /api/logo?u=<telegram username>
// Reads the public photo of a bot/channel from its t.me page and streams it back (no bot token needed).

module.exports = async (req, res) => {
  const u = String(req.query.u || "").replace(/^@/, "");
  if (!/^[A-Za-z][A-Za-z0-9_]{3,31}$/.test(u)) return res.status(400).end();
  try {
    const page = await fetch("https://t.me/" + u, { headers: { "User-Agent": "Mozilla/5.0" } });
    const html = await page.text();
    const m = html.match(/<meta property="og:image" content="([^"]+)"/);
    if (!m || /t_logo|telegram\.org\/img/i.test(m[1])) return res.status(404).end();
    const img = await fetch(m[1].replace(/&amp;/g, "&"));
    if (!img.ok) return res.status(404).end();
    const buf = Buffer.from(await img.arrayBuffer());
    res.setHeader("Content-Type", img.headers.get("content-type") || "image/jpeg");
    res.setHeader("Cache-Control", "public, max-age=86400, s-maxage=86400");
    return res.status(200).send(buf);
  } catch (e) {
    return res.status(502).end();
  }
};
