// Vercel serverless function: /api/proxy?u=<encoded TBC webhook url>
// Forwards the mini app's JSON to the bot's webhook server-to-server (no browser CORS).
// Only https URLs on allowed hosts are forwarded. Add more hosts with the
// ALLOWED_HOSTS env var on Vercel (comma separated), e.g. "telebotcreator.com,example.com".

const DEFAULT_ALLOWED = ["telebotcreator.com"];

function allowedHosts() {
  const extra = (process.env.ALLOWED_HOSTS || "")
    .split(",")
    .map((s) => s.trim().toLowerCase())
    .filter(Boolean);
  return DEFAULT_ALLOWED.concat(extra);
}

function hostOk(host) {
  host = host.toLowerCase();
  return allowedHosts().some((h) => host === h || host.endsWith("." + h));
}

module.exports = async (req, res) => {
  res.setHeader("Content-Type", "application/json");
  res.setHeader("Cache-Control", "no-store");

  if (req.method !== "POST") {
    return res.status(405).send(JSON.stringify({ ok: false, error: "POST only" }));
  }

  let target;
  try {
    target = new URL(String(req.query.u || ""));
  } catch (e) {
    return res.status(400).send(JSON.stringify({ ok: false, error: "Bad webhook url" }));
  }

  if (target.protocol !== "https:" || !hostOk(target.hostname)) {
    return res.status(403).send(
      JSON.stringify({
        ok: false,
        error: "Host not allowed: " + target.hostname + " (add it to ALLOWED_HOSTS on Vercel)",
      })
    );
  }

  let body = req.body;
  if (typeof body !== "string") body = JSON.stringify(body || {});

  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), 25000);
  try {
    const r = await fetch(target.toString(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      signal: ctl.signal,
    });
    const text = await r.text();
    clearTimeout(timer);
    if (!r.ok) {
      return res
        .status(200)
        .send(JSON.stringify({ ok: false, error: "Bot server replied HTTP " + r.status + ": " + text.slice(0, 80) }));
    }
    return res.status(200).send(text);
  } catch (e) {
    clearTimeout(timer);
    return res.status(200).send(JSON.stringify({ ok: false, error: "Bot server did not answer: " + String(e.message || e).slice(0, 80) }));
  }
};
