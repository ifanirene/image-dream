import test from 'node:test';
import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';
import { readFileSync } from 'node:fs';
import worker from './worker.mjs';
function setup() {
  const db = new DatabaseSync(':memory:');
  db.exec(readFileSync(new URL('./migrations/0001_feedback.sql', import.meta.url), 'utf8'));
  const env = {
    ALLOWED_ORIGIN: 'https://gallery.example', GALLERY_URL: 'https://gallery.example/' + crypto.randomUUID() + '/',
    ADMIN_TOKEN: 'a'.repeat(64),
    DB: { prepare(sql) {
      let params = [];
      const bindings = () => params.length ? [Object.fromEntries(params.map((value, i) => ['?' + (i + 1), value]))] : [];
      return { bind(...values) { params = values; return this; },
        async run() { return db.prepare(sql).run(...bindings()); },
        async all() { return { results: db.prepare(sql).all(...bindings()) }; },
        async first() { return db.prepare(sql).get(...bindings()); } };
    } },
    FEEDBACK_LIMITER: { async limit() { return { success: true }; } },
  };
  const token = crypto.randomUUID();
  const body = { token, artwork_id: 'work-one', beauty: 5, inspiration: null, feelings: ['curious'], comment: '' };
  const send = (data = body, origin = env.ALLOWED_ORIGIN) => worker.fetch(new Request('https://feedback.example/feedback', {
    method: 'POST', headers: { 'Content-Type': 'application/json', 'Origin': origin }, body: JSON.stringify(data),
  }), env);
  return { db, env, body, send };
}
test('unanswered dimensions, replacement, anonymous identity and deletion', async () => {
  const savedFetch = globalThis.fetch;
  globalThis.fetch = async () => new Response(JSON.stringify({ ids: ['work-one'] }));
  const { db, body, send } = setup();
  try {
    assert.equal((await send()).status, 200);
    let row = db.prepare('SELECT * FROM feedback').get();
    assert.equal(row.beauty, 5); assert.equal(row.inspiration, null);
    assert.notEqual(row.viewer_hash, body.token); assert.equal(row.viewer_hash.length, 64);
    assert.equal((await send({ ...body, beauty: 2, inspiration: 4, feelings: ['surprised', 'share'], comment: '<script>plain text</script>' })).status, 200);
    assert.equal(db.prepare('SELECT COUNT(*) AS n FROM feedback').get().n, 1);
    row = db.prepare('SELECT * FROM feedback').get();
    assert.equal(row.beauty, 2); assert.equal(row.inspiration, 4);
    assert.equal(row.comment, '<script>plain text</script>'); assert.deepEqual(JSON.parse(row.feelings), ['share', 'surprised']);
    const removed = await send({ ...body, beauty: null, inspiration: null, feelings: [], comment: '' });
    assert.equal((await removed.json()).deleted, true);
    assert.equal(db.prepare('SELECT COUNT(*) AS n FROM feedback').get().n, 0);
  } finally { db.close(); globalThis.fetch = savedFetch; }
});
test('invalid and unpublished submissions are not recorded', async () => {
  const savedFetch = globalThis.fetch;
  globalThis.fetch = async () => new Response(JSON.stringify({ ids: ['work-one'] }));
  const { db, body, send } = setup();
  try {
    assert.equal((await send(body, 'https://unrelated.example')).status, 403);
    assert.equal((await send({ ...body, beauty: 0 })).status, 400);
    assert.equal((await send({ ...body, email: 'unrequested@example.com' })).status, 400);
    assert.equal((await send({ ...body, feelings: ['unrecognized'] })).status, 400);
    assert.equal((await send({ ...body, artwork_id: 'hidden-art' })).status, 404);
    assert.equal((await send({ ...body, comment: 'x'.repeat(13000) })).status, 400);
    assert.equal(db.prepare('SELECT COUNT(*) AS n FROM feedback').get().n, 0);
  } finally { db.close(); globalThis.fetch = savedFetch; }
});
test('admin export requires a secret', async () => {
  const { db, env } = setup();
  try {
    assert.equal((await worker.fetch(new Request('https://feedback.example/admin/export'), env)).status, 401);
    const result = await worker.fetch(new Request('https://feedback.example/admin/export', { headers: { Authorization: `Bearer ${env.ADMIN_TOKEN}` } }), env);
    assert.equal(result.status, 200); assert.deepEqual((await result.json()).rows, []);
    assert.equal(result.headers.get('Access-Control-Allow-Origin'), null);
  } finally { db.close(); }
});
test('service errors never report a saved response', async () => {
  const savedFetch = globalThis.fetch;
  globalThis.fetch = async () => { throw new Error('upstream down'); };
  const { db, send } = setup();
  try {
    const result = await send(); assert.equal(result.status, 503);
    assert.notEqual((await result.json()).ok, true);
    assert.equal(db.prepare('SELECT COUNT(*) AS n FROM feedback').get().n, 0);
  } finally { db.close(); globalThis.fetch = savedFetch; }
});
