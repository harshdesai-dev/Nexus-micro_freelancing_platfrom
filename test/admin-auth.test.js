import test from 'node:test';
import assert from 'node:assert/strict';
import { requireAuth, adminOnly } from '../src/auth.js';

test('requireAuth rejects missing token', async () => {
  let called = false; const req = { get: () => null }; const res = { status(code){ this.code = code; return this; }, json(obj){ this.body = obj; } };
  await requireAuth(req, res, () => { called = true; });
  assert.equal(called, false);
  assert.equal(res.code, 401);
});
test('requireAuth accepts TEST_STUDENT token in test env', async () => {
  process.env.NODE_ENV = 'test';
  let called = false; const req = { get: (h) => 'Bearer TEST_STUDENT' }; const res = { status(){ return this; }, json(){} };
  await requireAuth(req, res, () => { called = true; });
  assert.equal(called, true); assert.equal(req.userRole, 'STUDENT');
});
test('adminOnly allows TEST_ADMIN and rejects TEST_STUDENT in test env', async () => {
  process.env.NODE_ENV = 'test';
  let called = false; const adminReq = { get: (h) => 'Bearer TEST_ADMIN' }; const res = { status(code){ this.code = code; return this; }, json(obj){ this.body = obj; } };
  await adminOnly(adminReq, res, () => { called = true; });
  assert.equal(called, true);
  // student should be rejected
  called = false; const studReq = { get: (h) => 'Bearer TEST_STUDENT' }; const res2 = { status(code){ this.code = code; return this; }, json(obj){ this.body = obj; } };
  await adminOnly(studReq, res2, () => { called = true; });
  assert.equal(called, false); assert.equal(res2.code, 403);
});
