import test from 'node:test';
import assert from 'node:assert/strict';
import { casePatch, verificationPatch } from '../src/validation.js';

test('verification accepts only final status with an audit action', () => {
  assert.equal(verificationPatch.safeParse({ verification_status: 'VERIFIED', admin_action: 'ID reviewed' }).success, true);
  assert.equal(verificationPatch.safeParse({ verification_status: 'PENDING', admin_action: 'later' }).success, false);
  assert.equal(verificationPatch.safeParse({ verification_status: 'REJECTED' }).success, false);
});
test('case updates validate allowed status and nonempty fields', () => {
  assert.equal(casePatch.safeParse({ status: 'RESOLVED', admin_action: 'Warning issued' }).success, true);
  assert.equal(casePatch.safeParse({ status: 'INVALID' }).success, false);
  assert.equal(casePatch.safeParse({}).success, false);
});
