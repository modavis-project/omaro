const state = { data: null, language: "en", selected: null, languages: [] };
const $ = (selector) => document.querySelector(selector);
const languageDisplayNames = typeof Intl.DisplayNames === "function"
  ? new Intl.DisplayNames([navigator.language || "en"], { type: "language" })
  : null;

function text(value) {
  const span = document.createElement("span");
  span.textContent = value ?? "";
  return span.innerHTML;
}

function label(item, language = state.language) {
  return item.labels[language] || item.labels.en || Object.values(item.labels)[0] || item.uri;
}

function languageName(code) {
  if (code === "und") return "Undetermined language";
  try {
    return languageDisplayNames?.of(code) || code;
  } catch (_error) {
    return code;
  }
}

function updateUrl(mode = "push") {
  const url = new URL(window.location.href);
  url.searchParams.set("lang", state.language);
  if (state.selected) url.searchParams.set("concept", state.selected);
  else url.searchParams.delete("concept");
  if (url.href === window.location.href) return;
  const method = mode === "replace" ? "replaceState" : "pushState";
  window.history[method]({}, "", url);
}

function buttonFor(item, className = "item") {
  const button = document.createElement("button");
  button.type = "button";
  button.className = className;
  button.dataset.uri = item.uri;
  button.innerHTML = item.kind === "classification"
    ? `<span class="notation">${text(item.notation)}</span>${text(label(item))}`
    : text(label(item));
  button.addEventListener("click", () => showDetail(item.uri));
  return button;
}

function treeNode(uri) {
  const item = state.data.byUri[uri];
  const li = document.createElement("li");
  li.append(buttonFor(item));
  if (item.children.length) {
    const ul = document.createElement("ul");
    item.children.forEach((child) => ul.append(treeNode(child)));
    li.append(ul);
  }
  return li;
}

function renderTree() {
  const root = document.createElement("ul");
  state.data.roots.forEach((uri) => root.append(treeNode(uri)));
  $("#tree").replaceChildren(root);
}

function showEmptyDetail() {
  state.selected = null;
  document.querySelectorAll("button[data-uri]").forEach((button) => {
    button.setAttribute("aria-current", "false");
  });
  $("#detail").innerHTML = `
    <h2>Choose a classification or instrument</h2>
    <p>Browse the hierarchy or search the multilingual vocabulary.</p>`;
}

function showDetail(uri, { historyMode = "push" } = {}) {
  const item = state.data.byUri[uri];
  if (!item) return;
  state.selected = uri;
  if (historyMode) updateUrl(historyMode);
  document.querySelectorAll("button[data-uri]").forEach((button) => {
    button.setAttribute("aria-current", String(button.dataset.uri === uri));
  });
  const related = item.kind === "classification" ? item.instruments : item.classifications;
  const relatedTitle = item.kind === "classification"
    ? "Instruments appearing in classification claims"
    : "Classification claims";
  const languageRows = Object.entries(item.labels)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([lang, value]) => `<dt title="${text(lang)}">${text(languageName(lang))} <span class="language-code">${text(lang)}</span></dt><dd lang="${text(lang)}">${text(value)}</dd>`)
    .join("");
  const relatedItems = related.map((relatedUri) => state.data.byUri[relatedUri]).filter(Boolean);
  const assignmentRows = item.classificationAssignments
    .map((assignment) => `
      <li>
        <strong>${text(assignment.stance)}</strong> ·
        perspective <span class="uri">${text(assignment.perspectiveUri)}</span><br>
        scope <span class="uri">${text(assignment.applicabilityScopeUris.join(", "))}</span><br>
        active reviews: ${text(assignment.activeReviewDecisions.length)}<br>
        assertion <span class="uri">${text(assignment.assertionUri)}</span><br>
        assignment activity <span class="uri">${text(assignment.assignmentUri)}</span>
      </li>`)
    .join("");
  $("#detail").innerHTML = `
    <p class="kind">${text(item.kind)}</p>
    <h2>${item.notation ? `<span class="notation">${text(item.notation)}</span>` : ""}${text(label(item))}</h2>
    ${item.definition ? `<p>${text(item.definition)}</p>` : ""}
    <h3>Preferred labels</h3><dl class="labels">${languageRows}</dl>
    <p class="notice">${text(state.data.lexicalNotice)} Label review: ${text(item.labelAssertionReviewStatuses.join(", ") || "none")}. Note review: ${text(item.noteAssertionReviewStatuses.join(", ") || "none")}.</p>
    <p class="notice">Language tags checked against IANA registry ${text(state.data.languageRegistryDate)}. Tag status: ${text(item.languageTagStatuses.join(", ") || "none")}.</p>
    ${item.qualityFindings.length ? `<p class="notice">${text(state.data.qualityNotice)} Signals: ${text(item.qualityFindings.join(", "))}.</p>` : ""}
    ${item.alternativeLabels.length ? `<h3>Alternative labels</h3><p>${item.alternativeLabels.map(text).join(" · ")}</p>` : ""}
    <h3>${relatedTitle} <small>(${relatedItems.length})</small></h3>
    ${relatedItems.length ? `<p class="notice">${text(state.data.classificationNotice)}</p>` : ""}
    <ul class="pill-list" id="related"></ul>
    ${assignmentRows ? `<h3>Qualified assignment occurrences <small>(${item.classificationAssignments.length})</small></h3><ul>${assignmentRows}</ul>` : ""}
    <h3>Stable identifier</h3>
    <p class="uri"><a href="${text(item.uri)}">${text(item.uri)}</a></p>
    <p><a href="${text(window.location.href)}">Share this record and language</a></p>`;
  const list = $("#related");
  relatedItems.sort((a, b) => label(a).localeCompare(label(b), state.language));
  relatedItems.forEach((relatedItem) => {
    const li = document.createElement("li");
    li.append(buttonFor(relatedItem));
    list.append(li);
  });
}

function applyUrlState() {
  if (!state.data) return;
  const params = new URLSearchParams(window.location.search);
  const requestedLanguage = params.get("lang");
  const nextLanguage = state.languages.includes(requestedLanguage) ? requestedLanguage : "en";
  const languageChanged = nextLanguage !== state.language;
  state.language = nextLanguage;
  $("#language").value = nextLanguage;
  if (languageChanged) {
    renderTree();
    search();
  }
  const requestedConcept = params.get("concept");
  if (requestedConcept && state.data.byUri[requestedConcept]) {
    showDetail(requestedConcept, { historyMode: null });
  } else {
    showEmptyDetail();
  }
}

function search() {
  const query = $("#search").value.trim().toLocaleLowerCase();
  if (!query) {
    $("#results").hidden = true;
    return;
  }
  const matches = state.data.items.filter((item) => item.search.includes(query)).slice(0, 100);
  const list = $("#result-list");
  list.replaceChildren(...matches.map((item) => {
    const button = buttonFor(item, "result");
    button.innerHTML = `<span class="kind">${text(item.kind)}</span><br>${item.notation ? `<span class="notation">${text(item.notation)}</span>` : ""}${text(label(item))}`;
    return button;
  }));
  $("#results").hidden = false;
  $("#results h2").textContent = `Search results (${matches.length}${matches.length === 100 ? "+" : ""})`;
}

async function init() {
  const response = await fetch("data.json");
  const payload = await response.json();
  payload.byUri = Object.fromEntries(payload.items.map((item) => [item.uri, item]));
  state.data = payload;
  $("#version").textContent = payload.version;
  $("#doi").href = `https://doi.org/${payload.doi}`;
  $("#doi").firstChild.textContent = `${payload.doi} `;
  state.languages = [...new Set(payload.items.flatMap((item) => Object.keys(item.labels)))].sort();
  $("#language").replaceChildren(...state.languages.map((language) => new Option(`${languageName(language)} (${language})`, language)));
  $("#summary").textContent = `${payload.classificationCount.toLocaleString()} classifications · ${payload.instrumentCount.toLocaleString()} instruments · ${state.languages.length} languages`;
  $("#search").addEventListener("input", search);
  $("#language").addEventListener("change", (event) => {
    state.language = event.target.value;
    renderTree(); search();
    if (state.selected) showDetail(state.selected, { historyMode: "replace" });
    else updateUrl("replace");
  });
  renderTree();
  applyUrlState();
  window.addEventListener("popstate", applyUrlState);
}

init().catch((error) => {
  $("#summary").textContent = `Dataset could not be loaded: ${error.message}`;
});
