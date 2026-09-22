import { test } from 'node:test';
import assert from 'node:assert/strict';
import { stateMedian } from '../src/lib/stateComparison.ts';

test('state benchmark handles odd/even samples and preserves zero observations', () => {
  assert.equal(stateMedian([4, 1, 2]), 2);
  assert.equal(stateMedian([4, 0, 2, 6]), 3);
});
test('state benchmark excludes missing observations without fabricating zeroes', () => {
  assert.equal(stateMedian([null, undefined, NaN, Infinity, 2, 4]), 3);
  assert.equal(stateMedian([null, undefined, NaN]), null);
  assert.equal(stateMedian([]), null);
});
