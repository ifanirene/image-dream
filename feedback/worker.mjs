const FEELINGS = new Set(['surprised', 'curious', 'resonates', 'research-connection', 'share', 'confused', 'unmoved']);
const ID = /^[a-z0-9][a-z0-9-]{0,95}$/;
let manifestCache = { url: '', until: 0, ids: new Set() };
function reply(data, status = 200, origin = null) {
  const headers = { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', 'Vary': 'Origin' };
  if (origin) Object.assign(headers, { 'Access-Control-Allow-Origin': origin,
    'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' });
  return new Response(JSON.stringify(data), { status, headers });
}
async function digest(value) {
  const bytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value));
  return [...new Uint8Array(bytes)].map((x) => x.toString(16).padStart(2, '0')).join('');
}
export function validate(input) {
  const keys = ['artwork_id', 'token', 'beauty', 'inspiration', 'feelings', 'comment'];
  if (!input || typeof input !== 'object' || Array.isArray(input) || Object.keys(input).some((x) => !keys.includes(x))) throw new Error('Invalid response fields.');
  if (typeof input.artwork_id !== 'string' || !ID.test(input.artwork_id)) throw new Error('Invalid artwork.');
  if (typeof input.token !== 'string' || !/^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/.test(input.token)) throw new Error('Invalid anonymous browser token.');
  for (const name of ['beauty', 'inspiration']) {
    if (input[name] !== null && (!Number.isInteger(input[name]) || input[name] < 1 || input[name] > 5)) throw new Error('Ratings must be 1–5 or unanswered.');
  }
  if (!Array.isArray(input.feelings) || input.feelings.length > FEELINGS.size || input.feelings.some((x) => !FEELINGS.has(x))) throw new Error('Invalid feeling.');
  if (typeof input.comment !== 'string' || input.comment.length > 2000) throw new Error('Keep your note within 2,000 characters.');
  return { ...input, feelings: [...new Set(input.feelings)].sort(), comment: input.comment.trim() };
}
async function jsonBody(request) {
  if (!request.headers.get('content-type')?.toLowerCase().startsWith('application/json')) throw new Error('Send JSON.');
  if (!request.body) throw new Error('Missing response.');
  const reader = request.body.getReader();
  const chunks = []; let length = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    length += value.byteLength;
    if (length > 12000) { await reader.cancel(); throw new Error('Response is too large.'); }
    chunks.push(value);
  }
  const bytes = new Uint8Array(length); let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
  return JSON.parse(new TextDecoder().decode(bytes));
}
async function published(id, env) {
  const base = new URL(env.GALLERY_URL);
  const local = ['localhost', '127.0.0.1'].includes(base.hostname);
  if (base.protocol !== 'https:' && !(local && base.protocol === 'http:')) throw new Error('Invalid gallery configuration');
  if (base.username || base.password || base.search || base.hash) throw new Error('Invalid gallery configuration');
  const url = base.href.replace(/\/$/, '') + '/site-manifest.json';
  if (manifestCache.url !== url || manifestCache.until < Date.now()) {
    const response = await fetch(url, { signal: AbortSignal.timeout(10000), redirect: 'manual' });
    if (!response.ok) throw new Error('Gallery not available');
    const manifest = await response.json();
    if (!Array.isArray(manifest.ids) || manifest.ids.length > 100000 || manifest.ids.some((x) => typeof x !== 'string' || !ID.test(x))) throw new Error('Invalid gallery manifest');
    manifestCache = { url, until: Date.now() + 60000, ids: new Set(manifest.ids) };
  }
  return manifestCache.ids.has(id);
}
async function admin(request, env) {
  const supplied = request.headers.get('Authorization')?.replace(/^Bearer /, '') || '';
  if (!env.ADMIN_TOKEN || env.ADMIN_TOKEN.length < 32 || (await digest(supplied)) !== (await digest(env.ADMIN_TOKEN))) return reply({ error: 'Unauthorized' }, 401);
  if (request.method !== 'GET') return reply({ error: 'Method not allowed' }, 405);
  const url = new URL(request.url);
  const offset = Number(url.searchParams.get('offset') || 0);
  if (!Number.isSafeInteger(offset) || offset < 0 || offset > 10000000) return reply({ error: 'Invalid offset' }, 400);
  const result = await env.DB.prepare('SELECT * FROM feedback ORDER BY artwork_id, viewer_hash LIMIT 500 OFFSET ?1').bind(offset).all();
  const rows = result.results.map((row) => ({ ...row, feelings: JSON.parse(row.feelings) }));
  return reply({ schema_version: 1, ratings: { beauty: '1 = Not for me; 5 = Love it', inspiration: '1 = Not yet; 5 = Very much', unanswered: null },
    unit: 'anonymous browser, not a verified person', rows, next_offset: rows.length === 500 ? offset + 500 : null });
}
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    try {
      if (url.pathname === '/admin/export') return await admin(request, env);
      if (url.pathname === '/health' && request.method === 'GET') {
        await env.DB.prepare('SELECT COUNT(*) AS n FROM feedback WHERE 0').first();
        return reply({ ok: true, service: 'nightwork-feedback' });
      }
      if (url.pathname !== '/feedback') return reply({ error: 'Not found' }, 404);
      const origin = request.headers.get('Origin');
      if (!origin || origin !== env.ALLOWED_ORIGIN) return reply({ error: 'Origin not allowed' }, 403);
      if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: {
        'Access-Control-Allow-Origin': origin, 'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type', 'Access-Control-Max-Age': '600', 'Vary': 'Origin' } });
      if (request.method !== 'POST') return reply({ error: 'Method not allowed' }, 405, origin);
      let input;
      try { input = validate(await jsonBody(request)); }
      catch (error) { return reply({ error: error.message || 'Invalid response' }, 400, origin); }
      const viewer = await digest(input.token);
      if (env.FEEDBACK_LIMITER) {
        const { success } = await env.FEEDBACK_LIMITER.limit({ key: viewer });
        if (!success) return reply({ error: 'Please wait a minute before sending another response.' }, 429, origin);
      }
      const empty = input.beauty === null && input.inspiration === null && !input.feelings.length && !input.comment;
      // Removal remains possible after an artwork is hidden.
      if (empty) {
        await env.DB.prepare('DELETE FROM feedback WHERE artwork_id = ?1 AND viewer_hash = ?2').bind(input.artwork_id, viewer).run();
        return reply({ ok: true, deleted: true }, 200, origin);
      }
      if (!(await published(input.artwork_id, env))) return reply({ error: 'This artwork is no longer in the gallery.' }, 404, origin);
      const now = new Date().toISOString();
      await env.DB.prepare(`INSERT INTO feedback (artwork_id, viewer_hash, beauty, inspiration, feelings, comment, created_at, updated_at)
        VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)
        ON CONFLICT (artwork_id, viewer_hash) DO UPDATE SET beauty=excluded.beauty,
        inspiration=excluded.inspiration, feelings=excluded.feelings, comment=excluded.comment, updated_at=excluded.updated_at`)
        .bind(input.artwork_id, viewer, input.beauty, input.inspiration, JSON.stringify(input.feelings), input.comment, now, now).run();
      return reply({ ok: true }, 200, origin);
    } catch {
      const origin = request.headers.get('Origin') === env.ALLOWED_ORIGIN ? env.ALLOWED_ORIGIN : null;
      return reply({ error: 'The feedback service is temporarily unavailable. Please try again.' }, 503, origin);
    }
  },
};
