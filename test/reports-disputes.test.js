import test from 'node:test';
import assert from 'node:assert/strict';
import { reportCreate, disputeCreate } from '../src/validation.js';

test('reportCreate requires a target and fields', () => {
  const ok = reportCreate.safeParse({ reported_user: '22222222-2222-2222-2222-222222222222', reason: 'Spam', details: 'Spam behaviour' });
  assert.equal(ok.success, true);
  const bad = reportCreate.safeParse({ reason: 'No target', details: 'Missing' });
  assert.equal(bad.success, false);
});
test('disputeCreate validates job id and details', () => {
  const ok = disputeCreate.safeParse({ job_id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', issue: 'Payment', details: 'Payment not released' });
  assert.equal(ok.success, true);
  const bad = disputeCreate.safeParse({ job_id: 'not-uuid', issue: '', details: '' });
  assert.equal(bad.success, false);
});
