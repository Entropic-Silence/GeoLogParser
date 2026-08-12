const boreholeNames = ["borehole_id","project_name","x_coordinate","y_coordinate","coordinate_system","collar_elevation_m","final_depth_m","groundwater_depth_m","groundwater_elevation_m","drilling_date"];
const numericNames = new Set(["x_coordinate","y_coordinate","collar_elevation_m","final_depth_m","groundwater_depth_m","groundwater_elevation_m","top_depth_m","bottom_depth_m","thickness_m"]);
let annotation = null;
let reviewSession = null;
let originalRecord = null;
let selectedFieldPath = null;
let rereadResult = null;

function setEnvelopeValue(envelope, raw, name) {
  envelope.value = raw === "" ? null : (numericNames.has(name) ? Number(raw) : raw);
  if (envelope.source_page == null) envelope.source_page = annotation?.panel?.source_page ?? null;
  envelope.extraction_method = "human";
  envelope.validation_status = "human_verified";
  envelope.confidence = null;
}

function confirmEnvelope(envelope) {
  if (envelope.source_page == null) envelope.source_page = annotation?.panel?.source_page ?? null;
  envelope.extraction_method = "human";
  envelope.validation_status = "human_verified";
  envelope.confidence = null;
}

function highlight(envelope) {
  const box = envelope?.display_bbox ?? envelope?.source_bbox;
  const image = document.querySelector("#panel-image");
  const marker = document.querySelector("#highlight");
  if (!box || !annotation?.panel?.source_page) { marker.style.display = "none"; return; }
  // Source PDF-point bboxes may be rotated and cannot be mapped to rendered
  // pixels without transform metadata. The API keeps both spaces explicit;
  // until transform_v001 lands, show evidence text and do not draw a false box.
  if (!envelope?.display_bbox && annotation.record.document.bbox_coordinate_space !== "pixels") {
    marker.style.display = "none";
    document.querySelector("#message").textContent = `Evidence p${envelope.source_page}: ${envelope.source_text ?? ""}`;
    return;
  }
  const [x1,y1,x2,y2] = box, sx = image.clientWidth / image.naturalWidth, sy = image.clientHeight / image.naturalHeight;
  Object.assign(marker.style, {display:"block",left:`${x1*sx}px`,top:`${y1*sy}px`,width:`${(x2-x1)*sx}px`,height:`${(y2-y1)*sy}px`});
}

function selectNumericField(path, envelope) {
  selectedFieldPath = path; rereadResult = null;
  document.querySelector("#selected-field").textContent = path;
  document.querySelector("#reread-field").disabled = false;
  document.querySelector("#apply-reread").disabled = true;
  document.querySelector("#reread-roi").style.display = "none";
  document.querySelector("#reread-output").textContent = "Ready for non-mutating OCR re-reading.";
  highlight(envelope);
}

function envelopeInput(name, envelope) {
  const row = document.createElement("div"); row.className = "field-row";
  const label = document.createElement("label"); label.textContent = name;
  const input = document.createElement("input"); input.value = envelope.value ?? "";
  input.addEventListener("change", () => setEnvelopeValue(envelope, input.value, name));
  const evidence = document.createElement("button"); evidence.textContent = "Evidence"; evidence.onclick = () => numericNames.has(name) ? selectNumericField(`borehole.${name}`, envelope) : highlight(envelope);
  const confirm = document.createElement("button"); confirm.textContent = envelope.validation_status === "human_verified" ? "Confirmed" : "Confirm";
  confirm.onclick = () => { confirmEnvelope(envelope); confirm.textContent = "Confirmed"; };
  row.append(label,input,evidence,confirm); return row;
}

function render() {
  document.querySelector("#status").value = annotation.annotation_status;
  document.querySelector("#panel-image").src = `/api/annotations/${annotation.annotation_id}/image?revision=${annotation.revision}`;
  const fields = document.querySelector("#borehole-fields"); fields.replaceChildren();
  boreholeNames.forEach(name => fields.append(envelopeInput(name, annotation.record.borehole[name])));
  const tbody = document.querySelector("#intervals"); tbody.replaceChildren();
  annotation.record.intervals.forEach((interval, intervalIndex) => {
    const row = document.createElement("tr");
    const specs = [["interval_id",false],["top_depth_m",false],["bottom_depth_m",false],["thickness_m",false],["stratum_code_raw",false],["lithology_raw",false],["description_raw",true]];
    specs.forEach(([name,multiline]) => {
      const cell=document.createElement("td"), value=name==="interval_id"?interval[name]:interval[name].value;
      const input=document.createElement(multiline?"textarea":"input"); input.value=value??"";
      input.onchange=()=> name==="interval_id" ? interval[name]=input.value : setEnvelopeValue(interval[name],input.value,name);
      if(name!=="interval_id") input.onclick=()=>numericNames.has(name)?selectNumericField(`intervals[${intervalIndex}].${name}`,interval[name]):highlight(interval[name]); cell.append(input); row.append(cell);
    });
    const actionCell=document.createElement("td"), confirm=document.createElement("button"), remove=document.createElement("button");
    confirm.textContent="Confirm row";
    confirm.onclick=()=>{Object.entries(interval).forEach(([name,envelope])=>{if(name!=="interval_id")confirmEnvelope(envelope);});render();};
    remove.textContent="Delete";
    remove.onclick=()=>{annotation.record.intervals.splice(intervalIndex,1);renumberIntervals();render();};
    actionCell.append(confirm,remove);row.append(actionCell);tbody.append(row);
  });
}

function renderGate(item) {
  const gate=document.querySelector("#gate-status"), failures=item?.ground_truth_gate_failures??[];
  gate.className=failures.length?"failed":"passed";
  gate.textContent=failures.length?`NOT GT — ${failures.join("; ")}`:"Ground Truth gate PASSED for this annotation";
}

async function loadStatus(){const status=await(await fetch("/api/status")).json();document.querySelector("#progress").textContent=`GT progress: ${status.ground_truth_exportable_count}/${status.annotation_count}; statuses=${JSON.stringify(status.status_counts)}; failures=${JSON.stringify(status.ground_truth_gate_failure_counts)}`;}

function renumberIntervals(){annotation.record.intervals.forEach((interval,index)=>{interval.interval_id=`I${String(index+1).padStart(3,"0")}`;});}

async function loadList() {
  const items=await (await fetch("/api/annotations")).json(), select=document.querySelector("#annotation-list"); select.replaceChildren();
  items.forEach(item=>{const option=document.createElement("option"); option.value=item.annotation_id; option.textContent=`${item.borehole_id??item.annotation_id} [${item.annotation_status} r${item.revision}] ${item.ground_truth_exportable?"GT":"NOT GT"}`; select.append(option);});
  select.dataset.items=JSON.stringify(items);
  select.onchange=()=>load(select.value); if(items.length) await load(items[0].annotation_id);
}
async function load(id) { annotation=await (await fetch(`/api/annotations/${id}`)).json(); originalRecord=structuredClone(annotation.record); reviewSession=null; selectedFieldPath=null; rereadResult=null;document.querySelector("#selected-field").textContent="none";document.querySelector("#reread-field").disabled=true;document.querySelector("#apply-reread").disabled=true;document.querySelector("#reread-roi").style.display="none";document.querySelector("#reread-output").textContent="Select a numeric field with pixel evidence."; render();const items=JSON.parse(document.querySelector("#annotation-list").dataset.items||"[]");renderGate(items.find(x=>x.annotation_id===id));await loadStatus(); await loadReviewQueue(); }
async function validate() { const response=await fetch("/api/validate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({record:annotation.record})}); document.querySelector("#validation-output").textContent=JSON.stringify(await response.json(),null,2); }
function countCorrections(a,b){let n=0;for(const name of boreholeNames)if(JSON.stringify(a.borehole[name].value)!==JSON.stringify(b.borehole[name].value))n++;const count=Math.max(a.intervals.length,b.intervals.length);for(let i=0;i<count;i++){if(!a.intervals[i]||!b.intervals[i]){n++;continue;}for(const name of ["top_depth_m","bottom_depth_m","thickness_m","stratum_code_raw","lithology_raw","description_raw"])if(JSON.stringify(a.intervals[i][name].value)!==JSON.stringify(b.intervals[i][name].value))n++;}return n;}
async function loadReviewQueue(){const all=await(await fetch("/api/review-queue")).json();document.querySelector("#review-output").textContent=JSON.stringify(all.filter(x=>x.annotation_id===annotation.annotation_id),null,2);}
async function startReview(){const response=await fetch("/api/review-sessions/start",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({annotation_id:annotation.annotation_id,annotator_id:document.querySelector("#annotator").value})});reviewSession=await response.json();document.querySelector("#message").textContent=`Timer started ${reviewSession.session_id}`;}
async function save() { const corrected=countCorrections(originalRecord,annotation.record), response=await fetch(`/api/annotations/${annotation.annotation_id}`,{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify({base_revision:annotation.revision,record:annotation.record,annotator_id:document.querySelector("#annotator").value,annotation_status:document.querySelector("#status").value})}); if(!response.ok){document.querySelector("#message").textContent=await response.text();return;} annotation=await response.json();if(reviewSession){await fetch(`/api/review-sessions/${reviewSession.session_id}/complete`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({corrected_fields:corrected})});reviewSession=null;}originalRecord=structuredClone(annotation.record);document.querySelector("#message").textContent=`Saved revision ${annotation.revision}; corrected fields ${corrected}`;render();await loadList();}

function confirmAllMvp(){boreholeNames.forEach(name=>confirmEnvelope(annotation.record.borehole[name]));annotation.record.intervals.forEach(interval=>Object.entries(interval).forEach(([name,envelope])=>{if(name!=="interval_id")confirmEnvelope(envelope);}));render();document.querySelector("#message").textContent="All displayed fields explicitly confirmed; inspect validation before saving.";}

async function rereadSelected(){if(!selectedFieldPath)return;const response=await fetch(`/api/annotations/${annotation.annotation_id}/reread`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({base_revision:annotation.revision,field_path:selectedFieldPath,record:annotation.record})});const value=await response.json();if(!response.ok){document.querySelector("#reread-output").textContent=JSON.stringify(value,null,2);return;}rereadResult=value;document.querySelector("#reread-output").textContent=JSON.stringify(value,null,2);document.querySelector("#apply-reread").disabled=value.decision.status!=="ACCEPT_PROPOSAL";const roi=document.querySelector("#reread-roi");roi.src=`/api/rereading/${annotation.annotation_id}/${value.run_id}/roi`;roi.style.display="block";}
function applyReread(){if(!rereadResult?.decision?.proposed_record)return;annotation.record=rereadResult.decision.proposed_record;document.querySelector("#apply-reread").disabled=true;document.querySelector("#message").textContent="Applied a fusion proposal locally as needs_review; inspect and Confirm before GT save.";render();}

document.querySelector("#validate").onclick=validate; document.querySelector("#start-review").onclick=startReview; document.querySelector("#save").onclick=save;
document.querySelector("#confirm-all").onclick=confirmAllMvp;
document.querySelector("#reread-field").onclick=rereadSelected;
document.querySelector("#apply-reread").onclick=applyReread;
document.querySelector("#add-interval").onclick=async()=>{const intervalId=`I${String(annotation.record.intervals.length+1).padStart(3,"0")}`;const response=await fetch("/api/interval-template",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({interval_id:intervalId,source_page:annotation.panel.source_page})});if(!response.ok){document.querySelector("#message").textContent=await response.text();return;}annotation.record.intervals.push(await response.json());render();};
document.querySelectorAll(".exports button[data-format]").forEach(button=>button.onclick=()=>{window.location=`/api/exports/${annotation.annotation_id}?format=${button.dataset.format}`;});
document.querySelector("#download-verified").onclick=async()=>{const response=await fetch("/api/exports/verified/all.jsonl");if(!response.ok){document.querySelector("#message").textContent=await response.text();return;}const blob=await response.blob(),url=URL.createObjectURL(blob),link=document.createElement("a");link.href=url;link.download="verified_ground_truth.jsonl";link.click();URL.revokeObjectURL(url);};
loadList();
