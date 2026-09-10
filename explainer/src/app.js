import { escapeHtml as e, compareProfile, targetName, recordFields } from './model.js';
import { classLabels, useCases, reasonLabels } from './content.js';

let data;
let layer = 0;
let selectedProfile = 0;
const layerPanel = document.querySelector('#claim-layer');

function renderLayer() {
  if (!data) return;
  document.querySelector('.sheet-number').textContent = `0${layer + 1} / 03`;
  document.querySelectorAll('[data-layer]').forEach(button => button.setAttribute('aria-pressed', String(Number(button.dataset.layer) === layer)));
  const claims = data.double_bass.classification_occurrences;
  if (layer === 0) {
    layerPanel.innerHTML = claims.map((row, index) => `<div class="classification-row"><span class="class-symbol" aria-hidden="true">${index + 1}</span><div><code>${e(row.classification.notation)}</code><small>${e(classLabels[row.classification.notation] || 'Source classification')}</small></div><span class="occurrence">SEPARATE CLAIM</span></div>`).join('') + '<p class="micro" style="margin:1rem 0 0;color:var(--muted)">Hornbostel–Sachs notations preserved from MIMO.</p>';
  } else if (layer === 1) {
    layerPanel.innerHTML = '<span class="tag warning">Scope: source-silent</span><h3 class="layer-heading" style="margin-top:.8rem">What the source leaves open</h3><p class="layer-body">These records do not tell us when or where each classification applies. Even a technique in a notation does not supply a fully documented scope.</p><p class="layer-body"><strong>Unknown does not mean “everywhere”.</strong> OMARO keeps that uncertainty explicit.</p>';
  } else {
    layerPanel.innerHTML = '<span class="tag">Source-transcribed</span><h3 class="layer-heading" style="margin-top:.8rem">Recorded, but not endorsed</h3><p class="layer-body">The source and assignment are traceable. These claims have no project endorsement: they lack the required policy opt-in, scope and reviews.</p><a class="micro" href="#record-detail">Inspect the record and explanation ↓</a>';
  }
}
document.querySelectorAll('[data-layer]').forEach(button => button.addEventListener('click', () => { layer = Number(button.dataset.layer); renderLayer(); }));

function setupUseCases() {
  const root = document.querySelector('#use-case-content');
  root.innerHTML = `<div class="role-picker" role="group" aria-label="Choose a use case">${useCases.map((item, index) => `<button data-case="${e(item.id)}" aria-pressed="${index === 0}" aria-controls="case-panel"><span class="role-number">${e(item.number)}</span><span>${e(item.label)}</span><span aria-hidden="true">↗</span></button>`).join('')}</div><article id="case-panel" class="case-panel" aria-labelledby="case-title"></article><p class="sr-only" id="case-status" role="status"></p>`;
  const selectCase = (id, announce = true) => {
    const item = useCases.find(row => row.id === id);
    root.querySelectorAll('[data-case]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.case === id)));
    root.querySelector('#case-panel').innerHTML = `<p class="eyebrow">${e(item.audience)}</p><h3 id="case-title">${e(item.title)}</h3><p class="case-intro">${e(item.intro)}</p><div class="case-example"><span class="tag">${e(item.tag)}</span><p>${e(item.example)}</p></div><details class="disclosure"><summary>How would I use it?</summary><div><ol class="workflow-steps">${item.steps.map(step => `<li>${e(step)}</li>`).join('')}</ol><p><strong>The result:</strong> ${e(item.result)}</p></div></details><p class="case-limit">${e(item.limit)}</p><a class="case-action" href="${e(item.link)}">${e(item.action)} <span aria-hidden="true">→</span></a><details class="disclosure model-terms"><summary>See the model behind this example</summary><div>${e(item.terms)}</div></details>`;
    if (announce) root.querySelector('#case-status').textContent = `${item.label}: ${item.title}`;
  };
  root.querySelectorAll('[data-case]').forEach(button => button.addEventListener('click', () => selectCase(button.dataset.case)));
  selectCase(useCases[0].id, false);
}

function renderComparison() {
  if (!data) return;
  const fixture = data.comparison;
  const profile = fixture.profiles[selectedProfile];
  const missing = document.querySelector('#missing-assessment').checked;
  const overrides = missing ? { [profile.dimension_uris[0]]: 'not-observed' } : {};
  const analysis = compareProfile(fixture, profile.uri, overrides);
  const winner = analysis.winners.length === 1 ? fixture.targets.find(target => target.uri === analysis.winners[0]) : null;
  document.querySelector('#comparison-result').innerHTML = `<h3 class="result-title">${winner ? `Closer on these dimensions:<br><em>${e(targetName(winner))}.</em>` : 'More evidence is needed.'}</h3><p class="result-description">${winner ? 'The smallest distance in this synthetic comparison.' : 'Only two of the required three dimensions remain comparable. No distance or nearest target is reported.'}</p><div class="distance-results">${analysis.comparisons.map(row => `<div class="distance-item"><div class="distance-label"><strong>${e(targetName(row.target))}</strong><span>${row.distance === null ? 'Insufficient evidence' : `${row.disagreements} of ${row.comparable} differ`}</span></div><div class="distance-track ${row.distance === null ? 'unknown' : ''}" aria-hidden="true">${row.distance === null ? '' : `<span style="width:${row.distance * 100}%"></span>`}</div><p class="micro">${row.distance === null ? `${row.comparable} comparable · ${row.excluded.length} excluded` : `Distance ${row.distance.toFixed(1)} · ${row.comparable} comparable dimensions`}</p></div>`).join('')}</div>`;
  const names = new Map(fixture.dimensions.map(dimension => [dimension.uri, dimension.label]));
  const namesByTarget = new Map(fixture.targets.map(target => [target.uri, targetName(target)]));
  const rows = profile.dimension_uris.map((uri, index) => `<tr><th scope="row">${e(names.get(uri))}</th><td>${e(analysis.comparisons[0].dimensions[index].leftStatus)}</td>${analysis.comparisons.map(row => `<td>${e(row.dimensions[index].rightStatus)}</td>`).join('')}</tr>`).join('');
  document.querySelector('#dimension-table').innerHTML = `<div class="table-wrap"><table><caption>${e(profile.label)} · selected assessments</caption><thead><tr><th>Dimension</th><th>${e(namesByTarget.get(fixture.focus_target_uri))}</th>${analysis.comparisons.map(row => `<th>${e(targetName(row.target))}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table></div>${missing ? '<p class="micro">The unobserved value is a temporary teaching override in this page. The downloaded fixture retains its original assessments.</p>' : ''}`;
}
document.querySelectorAll('[name="profile"]').forEach(input => input.addEventListener('change', () => { selectedProfile = Number(input.value); renderComparison(); }));
document.querySelector('#missing-assessment').addEventListener('change', renderComparison);

function renderRecord(index = 0) {
  const rows = data.double_bass.classification_occurrences;
  const row = rows[index];
  const fields = recordFields(row, data);
  document.querySelector('#record-inspector').innerHTML = `<div class="record-toolbar"><label for="record-select">Classification occurrence</label><select id="record-select">${rows.map((item, itemIndex) => `<option value="${itemIndex}" ${itemIndex === index ? 'selected' : ''}>${e(item.classification.notation)} — ${e(classLabels[item.classification.notation] || 'Source claim')}</option>`).join('')}</select></div><div class="record-facts"><dl>${fields.map(([label, value]) => `<div><dt>${e(label)}</dt><dd>${e(value ?? 'Not recorded')}</dd></div>`).join('')}</dl><div class="endorsement-summary"><span class="tag ${row.endorsement.eligible ? '' : 'warning'}">${row.endorsement.eligible ? 'Eligible under the policy' : 'Not eligible for direct endorsement'}</span><ul>${row.endorsement.reason_codes.map(code => `<li>${e(reasonLabels[code] || code)}</li>`).join('')}</ul><p class="micro">Research selection: ${row.research_included ? 'included' : 'excluded'}. This is not a truth or permission judgment.</p></div></div><details class="disclosure"><summary>Show the complete machine-readable claim and explanation</summary><div><pre tabindex="0"><code>${e(JSON.stringify(row, null, 2))}</code></pre></div></details>`;
  document.querySelector('#record-select').addEventListener('change', event => {
    renderRecord(Number(event.target.value));
    document.querySelector('#record-select').focus({ preventScroll: true });
  });
}

function revealAnchor(hash) {
  if (!hash?.startsWith('#')) return;
  let target;
  try { target = document.getElementById(decodeURIComponent(hash.slice(1))); } catch { return; }
  if (!target) return;
  let parent = target;
  while (parent) {
    if (parent instanceof HTMLDetailsElement) parent.open = true;
    parent = parent.parentElement;
  }
}
document.addEventListener('click', event => {
  const link = event.target.closest('a[href^="#"]');
  if (link) revealAnchor(link.getAttribute('href'));
});
window.addEventListener('hashchange', () => revealAnchor(location.hash));
document.querySelectorAll('[data-copy]').forEach(button => button.addEventListener('click', async () => {
  const recipe = document.getElementById(button.dataset.copy);
  const status = document.querySelector('#copy-status');
  try {
    await navigator.clipboard.writeText(recipe.textContent);
    status.textContent = 'Command copied.';
  } catch {
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(recipe);
    selection.removeAllRanges();
    selection.addRange(range);
    status.textContent = 'Automatic copying is unavailable. The command is selected; use your device’s Copy command.';
  }
}));

async function loadData() {
  try {
    const response = await fetch(new URL('./data.json', import.meta.url));
    if (!response.ok) throw new Error('Could not load data');
    data = await response.json();
    if (!data.double_bass?.classification_occurrences?.length || !data.comparison?.profiles?.length) throw new Error('Incomplete example data');
    document.querySelector('#ontology-version').textContent = data.ontology_version;
    document.querySelector('#dataset-version').textContent = data.dataset_version;
    document.querySelector('#data-error').hidden = true;
    document.querySelector('#occurrence-count').textContent = new Intl.NumberFormat('en').format(data.counts.classification_occurrences);
    document.querySelector('#profile-picker').disabled = false;
    document.querySelector('#missing-assessment').disabled = false;
    renderLayer();
    renderRecord();
    renderComparison();
  } catch {
    data = undefined;
    document.querySelector('#data-error').hidden = false;
    layerPanel.innerHTML = '<p class="layer-body">The source example is unavailable. Continue with the guide below, or try loading it again.</p>';
    document.querySelector('#profile-picker').disabled = true;
    document.querySelector('#missing-assessment').disabled = true;
  }
}
document.querySelector('#retry-data').addEventListener('click', loadData);
setupUseCases();
document.documentElement.classList.add('js');
revealAnchor(location.hash);
loadData();
