import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const BOOKING_JSON_PATH = path.resolve(__dirname, '../public/data/booking_hotel_benchmarks.json');

test('booking_hotel_benchmarks.json satisfies client interface schema', () => {
  assert.ok(fs.existsSync(BOOKING_JSON_PATH), 'booking_hotel_benchmarks.json must exist in public/data');
  const raw = fs.readFileSync(BOOKING_JSON_PATH, 'utf-8');
  const data = JSON.parse(raw);

  // Metadata assertions
  assert.equal(data.metadata.status, 'UNVALIDATED_SUPPORTING');
  assert.equal(data.metadata.snapshot_year, 2026);
  assert.equal(data.metadata.total_properties, 360);
  assert.equal(data.metadata.destinations_count, 18);
  assert.equal(data.metadata.states_covered, 16);

  // National Benchmark assertions
  assert.ok(data.national_benchmark.median_price_myr > 0);
  assert.ok(data.national_benchmark.mean_rating >= 0 && data.national_benchmark.mean_rating <= 10);
  assert.equal(data.national_benchmark.sample_size, 360);

  // Destinations assertions
  const destKeys = Object.keys(data.destinations);
  assert.equal(destKeys.length, 18);
  assert.ok(destKeys.includes('cameron'));
  assert.ok(destKeys.includes('langkawi'));

  for (const slug of destKeys) {
    const d = data.destinations[slug];
    assert.equal(d.sample_size, 20);
    assert.equal(d.hotels.length, 20);
    assert.ok(d.median_price_myr > 0);
    assert.ok(d.star_breakdown.luxury_4_5_star_pct >= 0);
  }

  // States assertions
  const stateKeys = Object.keys(data.states);
  assert.equal(stateKeys.length, 16);
  assert.ok(data.states['Pahang'].has_subdestinations);
  assert.deepEqual(data.states['Pahang'].subdestinations, ['cameron']);
  assert.ok(data.states['Kedah'].has_subdestinations);
  assert.deepEqual(data.states['Kedah'].subdestinations, ['langkawi']);
});
