const boreholeNames = ["borehole_id","project_name","x_coordinate","y_coordinate","coordinate_system","collar_elevation_m","final_depth_m","groundwater_depth_m","groundwater_elevation_m","drilling_date"];
const numericNames = new Set(["x_coordinate","y_coordinate","collar_elevation_m","final_depth_m","groundwater_depth_m","groundwater_elevation_m","top_depth_m","bottom_depth_m","thickness_m"]);
let annotation = null;

function setEnvelopeValue(envelope, raw, name) {
  envelope.value = raw === "" ? null : (numericNames.has(name) ? Number(raw) : raw);
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

function envelopeInput(name, envelope) {
  const row = document.createElement("div"); row.className = "field-row";
  const label = document.createElement("label"); label.textContent = name;
  const input = document.createElement("input"); input.value = envelope.value ?? "";
  input.addEventListener("change", () => setEnvelopeValue(envelope, input.value, name));
  const evidence = document.createElement("button"); evidence.textContent = "Evidence"; evidence.onclick = () => highlight(envelope);
  row.append(label,input,evidence); return row;
}

function render() {
  document.querySelector("#status").value = annotation.annotation_status;
  document.querySelector("#panel-image").src = `/api/annotations/${annotation.annotation_id}/image?revision=${annotation.revision}`;
  const fields = document.querySelector("#borehole-fields"); fields.replaceChildren();
  boreholeNames.forEach(name => fields.append(envelopeInput(name, annotation.record.borehole[name])));
  const tbody = document.querySelector("#intervals"); tbody.replaceChildren();
  annotation.record.intervals.forEach(interval => {
    const row = document.createElement("tr");
    const specs = [["interval_id",false],["top_depth_m",false],["bottom_depth_m",false],["thickness_m",false],["stratum_code_raw",false],["lithology_raw",false],["description_raw",true]];
    specs.forEach(([name,multiline]) => {
      const cell=document.createElement("td"), value=name==="interval_id"?interval[name]:interval[name].value;
      const input=document.createElement(multiline?"textarea":"input"); input.value=value??"";
      input.onchange=()=> name==="interval_id" ? interval[name]=input.value : setEnvelopeValue(interval[name],input.value,name);
      if(name!=="interval_id") input.onclick=()=>highlight(interval[name]); cell.append(input); row.append(cell);
    }); tbody.append(row);
  });
}

async function loadList() {
  const items=await (await fetch("/api/annotations")).json(), select=document.querySelector("#annotation-list"); select.replaceChildren();
  items.forEach(item=>{const option=document.createElement("option"); option.value=item.annotation_id; option.textContent=`${item.borehole_id??item.annotation_id} [${item.annotation_status} r${item.revision}]`; select.append(option);});
  select.onchange=()=>load(select.value); if(items.length) await load(items[0].annotation_id);
}
async function load(id) { annotation=await (await fetch(`/api/annotations/${id}`)).json(); render(); }
async function validate() { const response=await fetch("/api/validate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({record:annotation.record})}); document.querySelector("#validation-output").textContent=JSON.stringify(await response.json(),null,2); }
async function save() { const response=await fetch(`/api/annotations/${annotation.annotation_id}`,{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify({base_revision:annotation.revision,record:annotation.record,annotator_id:document.querySelector("#annotator").value,annotation_status:document.querySelector("#status").value})}); if(!response.ok){document.querySelector("#message").textContent=await response.text();return;} annotation=await response.json(); document.querySelector("#message").textContent=`Saved revision ${annotation.revision}`; render(); }

document.querySelector("#validate").onclick=validate; document.querySelector("#save").onclick=save;
document.querySelector("#add-interval").onclick=()=>{const template=structuredClone(annotation.record.intervals.at(-1)); template.interval_id=`I${String(annotation.record.intervals.length+1).padStart(3,"0")}`; Object.values(template).forEach(v=>{if(v&&typeof v==="object"&&"value" in v){v.value=null;v.source_bbox=null;v.source_text=null;v.extraction_method="human";}}); annotation.record.intervals.push(template);render();};
loadList();
