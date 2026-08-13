const checkNames = [
  "organization_or_project",
  "person_or_signature",
  "contact_or_address",
  "coordinates_or_sensitive_location",
  "stamp_or_watermark",
  "third_party_content",
];

let item = null;
let items = [];
const $ = (selector) => document.querySelector(selector);

function valueOr(value, fallback) {
  return value === null || value === undefined ? fallback : value;
}

function reviewCheck(review, name) {
  return review && review.checks && review.checks[name] ? review.checks[name] : null;
}

function checkRow(name) {
  const row = document.createElement("div");
  row.className = "check-row";
  const label = document.createElement("span");
  label.textContent = name;
  const status = document.createElement("select");
  status.id = `status-${name}`;
  for (const value of ["uncertain", "absent", "present"]) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    status.append(option);
  }
  const action = document.createElement("select");
  action.id = `action-${name}`;
  for (const value of ["restrict", "not_applicable", "cleared", "redact", "exclude"]) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    action.append(option);
  }
  const notes = document.createElement("input");
  notes.id = `check-notes-${name}`;
  notes.placeholder = "required when present";
  status.onchange = () => {
    if (status.value === "absent") action.value = "not_applicable";
    if (status.value === "uncertain") action.value = "restrict";
    if (status.value === "present" && action.value === "not_applicable") {
      action.value = "restrict";
    }
  };
  row.append(label, status, action, notes);
  return row;
}

for (const name of checkNames) {
  $("#checks").append(checkRow(name));
}

function renderEvidence() {
  const values = {
    Dataset: item.dataset_id,
    DOI: item.dataset_doi,
    File: item.source_filename,
    Page: item.source_page,
    Class: item.provisional_content_class,
    Language: item.language,
    License: item.license_id,
  };
  const root = $("#evidence");
  root.replaceChildren();
  for (const [label, value] of Object.entries(values)) {
    const term = document.createElement("dt");
    term.textContent = label;
    const description = document.createElement("dd");
    description.textContent = valueOr(value, "not recorded");
    root.append(term, description);
  }
}

function render() {
  if (!item) return;
  $("#image").src = `/api/items/${item.review_item_id}/image`;
  const review = item.review;
  renderEvidence();
  $("#decision").value = review ? review.decision : "internal_only";
  $("#phase1").checked = review ? review.phase1_borehole_content : false;
  $("#complete").checked = review ? review.render_complete : false;
  $("#redactions").checked = review ? review.redactions_required : false;
  $("#notes").value = review ? valueOr(review.notes, "") : "";
  $("#existing").textContent = review
    ? JSON.stringify(review, null, 2)
    : "No saved human review";
  for (const name of checkNames) {
    const check = reviewCheck(review, name);
    $(`#status-${name}`).value = check ? check.status : "uncertain";
    $(`#action-${name}`).value = check ? check.action : "restrict";
    $(`#check-notes-${name}`).value = check ? valueOr(check.notes, "") : "";
  }
  const reviewed = items.filter((value) => Boolean(value.review)).length;
  $("#progress").textContent = `${reviewed}/${items.length} reviewed`;
}

async function load() {
  items = await (await fetch("/api/items")).json();
  const select = $("#items");
  select.replaceChildren();
  for (const value of items) {
    const option = document.createElement("option");
    option.value = value.review_item_id;
    option.textContent = `${value.review_item_id} [${value.review ? value.review.decision : "unreviewed"}]`;
    select.append(option);
  }
  select.onchange = () => {
    item = items.find((value) => value.review_item_id === select.value);
    render();
  };
  item = items.length ? items[0] : null;
  render();
}

async function save() {
  const checks = Object.fromEntries(checkNames.map((name) => [name, {
    status: $(`#status-${name}`).value,
    action: $(`#action-${name}`).value,
    notes: $(`#check-notes-${name}`).value || null,
  }]));
  const payload = {
    base_revision: item.review ? item.review.revision : 0,
    reviewer_id: $("#reviewer").value,
    decision: $("#decision").value,
    phase1_borehole_content: $("#phase1").checked,
    render_complete: $("#complete").checked,
    redactions_required: $("#redactions").checked,
    checks,
    notes: $("#notes").value || null,
  };
  const response = await fetch(`/api/items/${item.review_item_id}/review`, {
    method: "PUT",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const error = await response.json();
    $("#message").textContent = error.detail || response.statusText;
    return;
  }
  item.review = await response.json();
  $("#message").textContent = `Saved revision ${item.review.revision}`;
  const option = Array.from($("#items").options).find(
    (value) => value.value === item.review_item_id,
  );
  option.textContent = `${item.review_item_id} [${item.review.decision}]`;
  render();
}

$("#save").onclick = save;
load();
