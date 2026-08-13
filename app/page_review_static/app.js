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
let serviceStatus = null;
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

function filteredItems() {
  const filter = $("#filter").value;
  if (filter === "unreviewed") return items.filter((value) => !value.review);
  if (filter === "reviewed") return items.filter((value) => Boolean(value.review));
  if (filter === "eligible") {
    return items.filter((value) => value.review && value.review.annotation_eligible);
  }
  if (filter === "restricted") {
    return items.filter((value) => value.review && !value.review.annotation_eligible);
  }
  return items;
}

function setCurrent(identifier) {
  item = items.find((value) => value.review_item_id === identifier) || null;
  rebuildItemSelect();
  render();
}

function rebuildItemSelect() {
  const select = $("#items");
  const currentId = item ? item.review_item_id : null;
  select.replaceChildren();
  for (const value of filteredItems()) {
    const option = document.createElement("option");
    option.value = value.review_item_id;
    option.textContent = `${value.review_item_id} [${value.review ? value.review.decision : "unreviewed"}]`;
    option.selected = value.review_item_id === currentId;
    select.append(option);
  }
  if (!select.options.length) {
    item = null;
  } else if (!Array.from(select.options).some((option) => option.value === currentId)) {
    item = items.find((value) => value.review_item_id === select.value) || null;
  }
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
    Render: `${item.rendered_width_px} x ${item.rendered_height_px} px`,
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

function renderProgress(progress = serviceStatus) {
  const reviewed = progress ? progress.reviewed_item_count : items.filter((value) => value.review).length;
  const eligible = progress ? progress.annotation_eligible_count : items.filter(
    (value) => value.review && value.review.annotation_eligible,
  ).length;
  $("#progress").textContent = `${reviewed}/${items.length} reviewed | ${eligible} eligible`;
}

function applyZoom() {
  const image = $("#image");
  const value = $("#zoom").value;
  if (value === "fit") {
    image.style.width = "100%";
    image.style.height = "auto";
  } else {
    image.style.width = `${value}%`;
    image.style.height = "auto";
  }
}

function render() {
  const empty = !item;
  $("#empty").hidden = !empty;
  $("#workspace").hidden = empty;
  $("#save").disabled = empty;
  if (empty) {
    renderProgress();
    return;
  }
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
  renderProgress();
  applyZoom();
}

function move(offset) {
  const visible = filteredItems();
  if (!visible.length) return;
  const current = Math.max(0, visible.findIndex((value) => value === item));
  const next = (current + offset + visible.length) % visible.length;
  setCurrent(visible[next].review_item_id);
}

function moveToNextUnreviewed(savedId) {
  const savedIndex = items.findIndex((value) => value.review_item_id === savedId);
  for (let step = 1; step <= items.length; step += 1) {
    const candidate = items[(savedIndex + step) % items.length];
    if (!candidate.review) {
      item = candidate;
      rebuildItemSelect();
      render();
      return;
    }
  }
  rebuildItemSelect();
  render();
}

async function load() {
  const [itemsResponse, statusResponse] = await Promise.all([
    fetch("/api/items"), fetch("/api/status"),
  ]);
  items = await itemsResponse.json();
  serviceStatus = await statusResponse.json();
  const reviewer = $("#reviewer");
  if (serviceStatus.fixed_reviewer_id) {
    reviewer.value = serviceStatus.fixed_reviewer_id;
    reviewer.disabled = true;
  } else {
    reviewer.value = localStorage.getItem("geologparser-page-reviewer-id") || "";
  }
  item = items.find((value) => !value.review) || items[0] || null;
  rebuildItemSelect();
  render();
}

async function save() {
  if (!item) return;
  const reviewerId = $("#reviewer").value.trim();
  if (!reviewerId) {
    $("#message").textContent = "Reviewer ID is required";
    $("#reviewer").focus();
    return;
  }
  if (!serviceStatus.fixed_reviewer_id) {
    localStorage.setItem("geologparser-page-reviewer-id", reviewerId);
  }
  const checks = Object.fromEntries(checkNames.map((name) => [name, {
    status: $(`#status-${name}`).value,
    action: $(`#action-${name}`).value,
    notes: $(`#check-notes-${name}`).value || null,
  }]));
  const payload = {
    base_revision: item.review ? item.review.revision : 0,
    reviewer_id: reviewerId,
    decision: $("#decision").value,
    phase1_borehole_content: $("#phase1").checked,
    render_complete: $("#complete").checked,
    redactions_required: $("#redactions").checked,
    checks,
    notes: $("#notes").value || null,
  };
  $("#save").disabled = true;
  const savedId = item.review_item_id;
  const response = await fetch(`/api/items/${savedId}/review`, {
    method: "PUT",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload),
  });
  $("#save").disabled = false;
  if (!response.ok) {
    const error = await response.json();
    $("#message").textContent = error.detail || response.statusText;
    return;
  }
  const result = await response.json();
  item.review = result.review;
  serviceStatus = {...serviceStatus, ...result.progress};
  $("#message").textContent = `${savedId} revision ${item.review.revision} saved`;
  moveToNextUnreviewed(savedId);
}

$("#items").onchange = () => setCurrent($("#items").value);
$("#filter").onchange = () => {
  rebuildItemSelect();
  render();
};
$("#previous").onclick = () => move(-1);
$("#next").onclick = () => move(1);
$("#zoom").onchange = applyZoom;
$("#all-absent").onclick = () => {
  for (const name of checkNames) {
    $(`#status-${name}`).value = "absent";
    $(`#action-${name}`).value = "not_applicable";
    $(`#check-notes-${name}`).value = "";
  }
};
$("#save").onclick = save;
load();
