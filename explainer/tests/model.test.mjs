import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { compareProfile, escapeHtml, recordFields } from '../src/model.js';
import { useCases } from '../src/content.js';

const readJson = relative => JSON.parse(readFileSync(new URL(relative, import.meta.url), 'utf8'));
const fixture = readJson('../../examples/multidimensional-analysis/scalogram.json');
const data = readJson('../dist/data.json');

for (const profile of fixture.profiles) {
  test(`reproduces the published comparisons for ${profile.label}`, () => {
    const result = compareProfile(fixture, profile.uri);
    for (const expected of fixture.comparisons.filter(row => row.profile_uri === profile.uri)) {
      const actual = result.comparisons.find(row => row.target.uri === expected.right_target_uri);
      assert.equal(actual.distance, expected.normalized_distance);
      assert.equal(actual.comparable, expected.comparable_dimensions);
      assert.deepEqual(actual.excluded, expected.excluded_dimension_uris);
    }
    assert.deepEqual(result.winners, fixture.nearest_by_profile.filter(row => row.profile_uri === profile.uri).map(row => row.target_uri));
  });
}
for (const status of ['not-observed', 'indeterminate', 'not-applicable']) {
  test(`${status} removes a dimension and never becomes zero evidence`, () => {
    const profile = fixture.profiles[0];
    const result = compareProfile(fixture, profile.uri, { [profile.dimension_uris[0]]: status });
    assert.deepEqual(result.winners, []);
    for (const row of result.comparisons) {
      assert.equal(row.comparable, 2);
      assert.equal(row.distance, null);
      assert.deepEqual(row.excluded, [profile.dimension_uris[0]]);
    }
  });
}
test('an actual negative result remains a comparable value', () => {
  const profile = fixture.profiles[0];
  const result = compareProfile(fixture, profile.uri, { [profile.dimension_uris[0]]: 'not-detected' });
  assert.equal(result.comparisons[0].comparable, 3);
  assert.equal(result.comparisons[0].distance, 1 / 3);
});
test('teaching overrides never mutate the source fixture', () => {
  const before = JSON.stringify(fixture);
  compareProfile(fixture, fixture.profiles[0].uri, { [fixture.profiles[0].dimension_uris[0]]: 'not-observed' });
  assert.equal(JSON.stringify(fixture), before);
});
test('unknown methods and assessment statuses fail explicitly', () => {
  assert.throws(() => compareProfile(fixture, 'unregistered'), /Unknown comparison profile/);
  assert.throws(() => compareProfile(fixture, fixture.profiles[0].uri, { [fixture.profiles[0].dimension_uris[0]]: 'unknown-spelling' }), /Unknown assessment status/);
});
test('record presentation preserves entity and activity identity', () => {
  for (const row of data.double_bass.classification_occurrences) {
    const fields = new Map(recordFields(row, data));
    assert.equal(fields.get('Assertion entity'), row.claim.uri);
    assert.equal(fields.get('Assignment activity'), row.claim.assignment_uri);
    assert.equal(row.endorsement.assertion_uri, fields.get('Assertion entity'));
    assert.notEqual(fields.get('Assertion entity'), fields.get('Assignment activity'));
    assert.ok([...fields.values()].every(value => typeof value === 'string' && value.length > 0));
  }
});
test('displayed claims are exact canonical occurrences, with unknown scope and no endorsement', () => {
  const canonical = readFileSync(new URL('../../data/canonical/classification_assertions.jsonl', import.meta.url), 'utf8').trim().split('\n').map(JSON.parse);
  const expected = canonical.filter(row => row.target_uri === data.double_bass.target.uri).sort((a, b) => a.uri.localeCompare(b.uri));
  const actual = data.double_bass.classification_occurrences.map(row => row.claim).sort((a, b) => a.uri.localeCompare(b.uri));
  assert.deepEqual(actual, expected);
  for (const row of data.double_bass.classification_occurrences) {
    assert.equal(row.endorsement.eligible, false);
    assert.equal(row.endorsement.scopes[0].match, null);
    assert.equal(row.endorsement.reviews.independent_reviewer_count, 0);
  }
});
test('six distinct learning paths include an example, limitation, and next step', () => {
  assert.equal(new Set(useCases.map(row => row.id)).size, 6);
  for (const row of useCases) {
    assert.equal(row.steps.length, 3);
    assert.ok(row.limit && row.example && row.terms);
    assert.match(row.tag, /^(REAL SOURCE|SYNTHETIC)/);
    assert.match(row.link, /^#[a-z-]+$/);
  }
});
test('source literals cannot inject markup into the interface', () => {
  assert.equal(escapeHtml('<img src=x onerror="alert(1)">&\''), '&lt;img src=x onerror=&quot;alert(1)&quot;&gt;&amp;&#39;');
});
