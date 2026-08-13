const boreholeNames = ["borehole_id","project_name","x_coordinate","y_coordinate","coordinate_system","collar_elevation_m","final_depth_m","groundwater_depth_m","groundwater_elevation_m","drilling_date"];
const numericNames = new Set(["x_coordinate","y_coordinate","collar_elevation_m","final_depth_m","groundwater_depth_m","groundwater_elevation_m","top_depth_m","bottom_depth_m","thickness_m"]);
let annotation = null;
let reviewSession = null;
let originalRecord = null;
let selectedFieldPath = null;
let rereadResult = null;
let drawnBBoxPixels = null;
let drawStart = null;
let drawMode = false;

function setEnvelopeValue(envelope, raw, name) {
  envelope.value = raw === "" ? null : (numericNames.has(name) ? Number(raw) : raw);
  if (envelope.source_page == null) envelope.source_page = annotation && annotation.panel ? annotation.panel.source_page : null;
  envelope.extraction_method = "human";
  envelope.validation_status = "human_verified";
  envelope.confidence = null;
}

function confirmEnvelope(envelope) {
  if (envelope.source_page == null) envelope.source_page = annotation && annotation.panel ? annotation.panel.source_page : null;
  envelope.extraction_method = "human";
  envelope.validation_status = "human_verified";
  envelope.confidence = null;
}

function highlight(envelope) {
  const box = envelope && envelope.display_bbox != null ? envelope.display_bbox : (envelope ? envelope.source_bbox : null);
  const image = document.querySelector("#panel-image");
  const marker = document.querySelector("#highlight");
  if (!box || !annotation || !annotation.panel || !annotation.panel.source_page) { marker.style.display = "none"; return; }
  // A PDF-point source bbox without an explicit transformed display bbox must
  // never be drawn directly over rendered pixels.
  if (!envelope.display_bbox && annotation.record.document.bbox_coordinate_space !== "pixels") {
    marker.style.display = "none";
    document.querySelector("#message").textContent = `Evidence p${envelope.source_page}: ${envelope.source_text == null ? "" : envelope.source_text}`;
    return;
  }
  const [x1,y1,x2,y2] = box, sx = image.clientWidth / image.naturalWidth, sy = image.clientHeight / image.naturalHeight;
  Object.assign(marker.style, {display:"block",left:`${x1*sx}px`,top:`${y1*sy}px`,width:`${(x2-x1)*sx}px`,height:`${(y2-y1)*sy}px`});
}

function selectField(path, envelope, name) {
  selectedFieldPath = path; rereadResult = null; drawnBBoxPixels = null; setDrawMode(false); drawDraft();
  document.querySelector("#selected-field").textContent = path;
  document.querySelector("#reread-field").disabled = !numericNames.has(name);
  document.querySelector("#draw-bbox").disabled = false;
  document.querySelector("#bind-bbox").disabled = true;
  document.querySelector("#clear-bbox").disabled = true;
  document.querySelector("#apply-reread").disabled = true;
  document.querySelector("#reread-roi").style.display = "none";
  document.querySelector("#reread-output").textContent = numericNames.has(name) ? "Ready for non-mutating ROI re-reading." : "Draw and bind pixel evidence; text re-reading is not implemented.";
  highlight(envelope);
}

function envelopeInput(name, envelope) {
  const row = document.createElement("div"); row.className = "field-row";
  const label = document.createElement("label"); label.textContent = name;
  const input = document.createElement("input"); input.value = envelope.value == null ? "" : envelope.value;
  input.addEventListener("change", () => setEnvelopeValue(envelope, input.value, name));
  const evidence = document.createElement("button"); evidence.textContent = "Evidence"; evidence.onclick = () => selectField(`borehole.${name}`, envelope, name);
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
      const input=document.createElement(multiline?"textarea":"input"); input.value=value==null?"":value;
      input.onchange=()=> name==="interval_id" ? interval[name]=input.value : setEnvelopeValue(interval[name],input.value,name);
      if(name!=="interval_id") input.onclick=()=>selectField(`intervals[${intervalIndex}].${name}`,interval[name],name); cell.append(input); row.append(cell);
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
  const gate=document.querySelector("#gate-status"), failures=item&&item.ground_truth_gate_failures?item.ground_truth_gate_failures:[];
  gate.className=failures.length?"failed":"passed";
  const attestors=item&&item.valid_attestor_ids?item.valid_attestor_ids:[];
  const evidence=`attestations=${item?item.valid_attestation_count:0}; attestors=${attestors.length?attestors.join(","):"none"}; expert=${item&&item.has_valid_expert_attestation?"yes":"no"}`;
  gate.textContent=(failures.length?`NOT GT — ${failures.join("; ")}`:"Ground Truth gate PASSED for this annotation")+` | ${evidence}`;
}

async function loadStatus(){const status=await(await fetch("/api/status")).json(),annotator=document.querySelector("#annotator");if(status.fixed_annotator_id){annotator.value=status.fixed_annotator_id;annotator.readOnly=true;}else{annotator.readOnly=false;}document.querySelector("#progress").textContent=`GT progress: ${status.ground_truth_exportable_count}/${status.annotation_count}; statuses=${JSON.stringify(status.status_counts)}; failures=${JSON.stringify(status.ground_truth_gate_failure_counts)}`;}

function renumberIntervals(){annotation.record.intervals.forEach((interval,index)=>{interval.interval_id=`I${String(index+1).padStart(3,"0")}`;});}

async function loadList() {
  const items=await (await fetch("/api/annotations")).json(), select=document.querySelector("#annotation-list"); select.replaceChildren();
  items.forEach(item=>{const option=document.createElement("option"); option.value=item.annotation_id; option.textContent=`${item.borehole_id==null?item.annotation_id:item.borehole_id} [${item.annotation_status} r${item.revision}] ${item.ground_truth_exportable?"GT":"NOT GT"}`; select.append(option);});
  select.dataset.items=JSON.stringify(items);
  select.onchange=()=>load(select.value); if(items.length) await load(items[0].annotation_id);
}
async function load(id) { annotation=await (await fetch(`/api/annotations/${id}`)).json(); originalRecord=structuredClone(annotation.record); reviewSession=null; selectedFieldPath=null; rereadResult=null;drawnBBoxPixels=null;setDrawMode(false);drawDraft();document.querySelector("#selected-field").textContent="none";document.querySelector("#reread-field").disabled=true;document.querySelector("#draw-bbox").disabled=true;document.querySelector("#bind-bbox").disabled=true;document.querySelector("#clear-bbox").disabled=true;document.querySelector("#apply-reread").disabled=true;document.querySelector("#reread-roi").style.display="none";document.querySelector("#reread-output").textContent="Select a field with pixel evidence."; render();const items=JSON.parse(document.querySelector("#annotation-list").dataset.items||"[]");renderGate(items.find(x=>x.annotation_id===id));await loadStatus(); await loadReviewQueue(); }
async function validate() { const response=await fetch("/api/validate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({record:annotation.record})}); document.querySelector("#validation-output").textContent=JSON.stringify(await response.json(),null,2); }
function countCorrections(a,b){let n=0;for(const name of boreholeNames)if(JSON.stringify(a.borehole[name].value)!==JSON.stringify(b.borehole[name].value))n++;const count=Math.max(a.intervals.length,b.intervals.length);for(let i=0;i<count;i++){if(!a.intervals[i]||!b.intervals[i]){n++;continue;}for(const name of ["top_depth_m","bottom_depth_m","thickness_m","stratum_code_raw","lithology_raw","description_raw"])if(JSON.stringify(a.intervals[i][name].value)!==JSON.stringify(b.intervals[i][name].value))n++;}return n;}
async function loadReviewQueue(){const all=await(await fetch("/api/review-queue")).json();document.querySelector("#review-output").textContent=JSON.stringify(all.filter(x=>x.annotation_id===annotation.annotation_id),null,2);}
async function startReview(){const response=await fetch("/api/review-sessions/start",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({annotation_id:annotation.annotation_id,annotator_id:document.querySelector("#annotator").value})});reviewSession=await response.json();document.querySelector("#message").textContent=`Timer started ${reviewSession.session_id}`;}
async function save() { const corrected=countCorrections(originalRecord,annotation.record), response=await fetch(`/api/annotations/${annotation.annotation_id}`,{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify({base_revision:annotation.revision,record:annotation.record,annotator_id:document.querySelector("#annotator").value,annotation_status:document.querySelector("#status").value})}); if(!response.ok){document.querySelector("#message").textContent=await response.text();return;} annotation=await response.json();if(reviewSession){await fetch(`/api/review-sessions/${reviewSession.session_id}/complete`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({corrected_fields:corrected})});reviewSession=null;}originalRecord=structuredClone(annotation.record);document.querySelector("#message").textContent=`Saved revision ${annotation.revision}; corrected fields ${corrected}`;render();await loadList();}

function confirmAllMvp(){boreholeNames.forEach(name=>confirmEnvelope(annotation.record.borehole[name]));annotation.record.intervals.forEach(interval=>Object.entries(interval).forEach(([name,envelope])=>{if(name!=="interval_id")confirmEnvelope(envelope);}));render();document.querySelector("#message").textContent="All displayed fields explicitly confirmed; inspect validation before saving.";}

async function rereadSelected(){if(!selectedFieldPath)return;const payload={base_revision:annotation.revision,field_path:selectedFieldPath,record:annotation.record};if(drawnBBoxPixels)payload.bbox_pixels=drawnBBoxPixels;const response=await fetch(`/api/annotations/${annotation.annotation_id}/reread`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});const value=await response.json();if(!response.ok){document.querySelector("#reread-output").textContent=JSON.stringify(value,null,2);return;}rereadResult=value;document.querySelector("#reread-output").textContent=JSON.stringify(value,null,2);document.querySelector("#apply-reread").disabled=value.decision.status!=="ACCEPT_PROPOSAL";const roi=document.querySelector("#reread-roi");roi.src=`/api/rereading/${annotation.annotation_id}/${value.run_id}/roi`;roi.style.display="block";}
function applyReread(){if(!rereadResult||!rereadResult.decision||!rereadResult.decision.proposed_record)return;annotation.record=rereadResult.decision.proposed_record;document.querySelector("#apply-reread").disabled=true;document.querySelector("#message").textContent="Applied a fusion proposal locally as needs_review; inspect and Confirm before GT save.";render();}

function setDrawMode(enabled){drawMode=enabled;drawStart=null;document.querySelector("#image-stage").classList.toggle("drawing",enabled);const button=document.querySelector("#draw-bbox");button.textContent=enabled?"Drawing…":"Draw bbox";}
function imagePoint(event){const image=document.querySelector("#panel-image"),rect=image.getBoundingClientRect();const clientX=Math.min(rect.right,Math.max(rect.left,event.clientX)),clientY=Math.min(rect.bottom,Math.max(rect.top,event.clientY));return {displayX:clientX-rect.left,displayY:clientY-rect.top,pixelX:(clientX-rect.left)*image.naturalWidth/rect.width,pixelY:(clientY-rect.top)*image.naturalHeight/rect.height};}
function drawDraft(displayBox=null){const marker=document.querySelector("#drawn-bbox"),image=document.querySelector("#panel-image");if(displayBox){const [x1,y1,x2,y2]=displayBox;Object.assign(marker.style,{display:"block",left:`${x1}px`,top:`${y1}px`,width:`${x2-x1}px`,height:`${y2-y1}px`});return;}if(!drawnBBoxPixels||!image.naturalWidth){marker.style.display="none";return;}const sx=image.clientWidth/image.naturalWidth,sy=image.clientHeight/image.naturalHeight,[x1,y1,x2,y2]=drawnBBoxPixels;Object.assign(marker.style,{display:"block",left:`${x1*sx}px`,top:`${y1*sy}px`,width:`${(x2-x1)*sx}px`,height:`${(y2-y1)*sy}px`});}
function clearDrawnBBox(){drawnBBoxPixels=null;drawStart=null;setDrawMode(false);drawDraft();document.querySelector("#bind-bbox").disabled=true;document.querySelector("#clear-bbox").disabled=true;}
async function bindDrawnBBox(){if(!selectedFieldPath||!drawnBBoxPixels)return;const response=await fetch(`/api/annotations/${annotation.annotation_id}/display-bbox`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({base_revision:annotation.revision,field_path:selectedFieldPath,bbox_pixels:drawnBBoxPixels,annotator_id:document.querySelector("#annotator").value,record:annotation.record})});const value=await response.json();if(!response.ok){document.querySelector("#message").textContent=JSON.stringify(value);return;}annotation.record=value.record;document.querySelector("#message").textContent="Bound human-drawn pixel evidence locally; field value status is unchanged until explicit Confirm and Save.";render();}

const imageStage=document.querySelector("#image-stage");
imageStage.addEventListener("pointerdown",event=>{if(!drawMode||!selectedFieldPath)return;event.preventDefault();imageStage.setPointerCapture(event.pointerId);drawStart=imagePoint(event);drawDraft([drawStart.displayX,drawStart.displayY,drawStart.displayX+1,drawStart.displayY+1]);});
imageStage.addEventListener("pointermove",event=>{if(!drawMode||!drawStart)return;const point=imagePoint(event);drawDraft([Math.min(drawStart.displayX,point.displayX),Math.min(drawStart.displayY,point.displayY),Math.max(drawStart.displayX,point.displayX),Math.max(drawStart.displayY,point.displayY)]);});
imageStage.addEventListener("pointerup",event=>{if(!drawMode||!drawStart)return;const point=imagePoint(event),x1=Math.min(drawStart.pixelX,point.pixelX),y1=Math.min(drawStart.pixelY,point.pixelY),x2=Math.max(drawStart.pixelX,point.pixelX),y2=Math.max(drawStart.pixelY,point.pixelY);if(x2-x1<2||y2-y1<2){clearDrawnBBox();document.querySelector("#message").textContent="Drawn bbox is too small.";return;}drawnBBoxPixels=[x1,y1,x2,y2];setDrawMode(false);drawDraft();document.querySelector("#bind-bbox").disabled=false;document.querySelector("#clear-bbox").disabled=false;document.querySelector("#message").textContent=`Draft bbox ${drawnBBoxPixels.map(value=>value.toFixed(1)).join(", ")}`;});
document.querySelector("#panel-image").addEventListener("load",()=>{drawDraft();if(selectedFieldPath)highlight(getSelectedEnvelope());});
function getSelectedEnvelope(){if(!selectedFieldPath)return null;if(selectedFieldPath.startsWith("borehole."))return annotation.record.borehole[selectedFieldPath.split(".")[1]];const match=selectedFieldPath.match(/^intervals\[(\d+)]\.(.+)$/);return match?annotation.record.intervals[Number(match[1])][match[2]]:null;}

document.querySelector("#validate").onclick=validate; document.querySelector("#start-review").onclick=startReview; document.querySelector("#save").onclick=save;
document.querySelector("#confirm-all").onclick=confirmAllMvp;
document.querySelector("#reread-field").onclick=rereadSelected;
document.querySelector("#apply-reread").onclick=applyReread;
document.querySelector("#draw-bbox").onclick=()=>setDrawMode(!drawMode);
document.querySelector("#bind-bbox").onclick=bindDrawnBBox;
document.querySelector("#clear-bbox").onclick=clearDrawnBBox;
document.querySelector("#add-interval").onclick=async()=>{const intervalId=`I${String(annotation.record.intervals.length+1).padStart(3,"0")}`;const response=await fetch("/api/interval-template",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({interval_id:intervalId,source_page:annotation.panel.source_page})});if(!response.ok){document.querySelector("#message").textContent=await response.text();return;}annotation.record.intervals.push(await response.json());render();};
document.querySelectorAll(".exports button[data-format]").forEach(button=>button.onclick=()=>{window.location=`/api/exports/${annotation.annotation_id}?format=${button.dataset.format}`;});
document.querySelector("#download-verified").onclick=async()=>{const response=await fetch("/api/exports/verified/all.jsonl");if(!response.ok){document.querySelector("#message").textContent=await response.text();return;}const blob=await response.blob(),url=URL.createObjectURL(blob),link=document.createElement("a");link.href=url;link.download="verified_ground_truth.jsonl";link.click();URL.revokeObjectURL(url);};
loadList();
