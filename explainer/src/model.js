export function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]);
}

// This is the example's declared analytical method, never an endorsement rule.
export function compareProfile(fixture, profileUri, overrides = {}) {
  const profile = fixture.profiles.find(row => row.uri === profileUri);
  if (!profile) throw new Error('Unknown comparison profile');
  const focus = fixture.assessments.find(row => row.target_uri === fixture.focus_target_uri);
  if (!focus) throw new Error('Missing focus assessments');
  const encoding = fixture.method.status_to_value;
  const value = status => {
    if (!Object.hasOwn(encoding, status)) throw new Error('Unknown assessment status');
    return encoding[status];
  };
  const minimum = fixture.method.minimum_comparable_dimensions;
  const comparisons = fixture.targets.filter(target => target.uri !== fixture.focus_target_uri).map(target => {
    const assessment = fixture.assessments.find(row => row.target_uri === target.uri);
    if (!assessment) throw new Error('Missing target assessments');
    let comparable = 0;
    let disagreements = 0;
    const excluded = [];
    const dimensions = profile.dimension_uris.map(uri => {
      const leftStatus = overrides[uri] ?? focus.values[uri];
      const rightStatus = assessment.values[uri];
      const left = value(leftStatus);
      const right = value(rightStatus);
      if (left === null || right === null) excluded.push(uri);
      else { comparable++; if (left !== right) disagreements++; }
      return { uri, leftStatus, rightStatus };
    });
    return { target, comparable, disagreements, excluded, dimensions, distance: comparable >= minimum ? disagreements / comparable : null };
  });
  const complete = comparisons.length > 0 && comparisons.every(row => row.distance !== null);
  const smallest = complete ? Math.min(...comparisons.map(row => row.distance)) : null;
  return { profile, minimum, comparisons, winners: complete ? comparisons.filter(row => row.distance === smallest).map(row => row.target.uri) : [] };
}

export function targetName(target) {
  return target.label.replace(/^Synthetic /, '').replace(/ configuration$/, '');
}

export function recordFields(row, data) {
  const claim = row.claim;
  const scope = data.scopes.find(item => item.uri === claim.applicability_scope_uris[0]);
  const perspective = data.perspectives.find(item => item.uri === claim.perspective_uri);
  return [
    ['Target', claim.target_uri], ['Classification', row.classification.uri],
    ['Assertion entity', claim.uri], ['Assignment activity', claim.assignment_uri],
    ['Source record', claim.source_record_uri],
    ['Perspective', perspective?.label || claim.perspective_uri],
    ['Scope', scope?.scope_mode || 'Unresolved'], ['Evaluated as of', row.endorsement.as_of],
  ];
}
