import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const sql = fs.readFileSync(new URL('../migrations/001_initial_schema.sql', import.meta.url), 'utf8');
test('schema includes every required entity', () => {
  for (const table of ['users','student_profiles','client_profiles','verifications','jobs','applications','messages','submissions','payments','ratings','reports','disputes']) assert.match(sql, new RegExp(`CREATE TABLE ${table}`));
});
test('schema protects core relationships and verification history', () => {
  assert.match(sql, /REFERENCES users\(id\)/); assert.match(sql, /REFERENCES jobs\(id\)/); assert.match(sql, /CREATE TABLE verification_history/); assert.match(sql, /enforce_verification_transition/);
  assert.match(sql, /student_profile_role/); assert.match(sql, /verification_initial_history/);
});
