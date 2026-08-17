#!/usr/bin/env python3
"""Propagate all available frozen image-derived interval boundaries to surfaces.

Boundary positions are aligned by interval order because the upstream parser
outputs ordered stratigraphy. Missing predicted intervals remain missing and
therefore alter both boundary coverage and spatial support; no reference-guided
matching or repair is performed before interpolation.
"""
from __future__ import annotations

import argparse, json, platform, subprocess, time
from geologparser.runtime_resources import peak_process_rss_kib
from datetime import date, datetime, timezone
from pathlib import Path

from geologparser.evaluation import SurfacePoint, idw_predict, surface_error_metrics
from geologparser.experiment import create_run_directory
from geologparser.result_index import file_sha256, write_artifact_manifest

ROOT = Path(__file__).resolve().parents[1]

def convex_hull(points):
    unique = sorted(set(points))
    if len(unique) <= 1:
        return unique
    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lower=[]
    for p in unique:
        while len(lower)>=2 and cross(lower[-2],lower[-1],p)<=0: lower.pop()
        lower.append(p)
    upper=[]
    for p in reversed(unique):
        while len(upper)>=2 and cross(upper[-2],upper[-1],p)<=0: upper.pop()
        upper.append(p)
    return lower[:-1]+upper[:-1]

def inside(point, polygon):
    if len(polygon)<3: return True
    signs=[]
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        v=(b[0]-a[0])*(point[1]-a[1])-(b[1]-a[1])*(point[0]-a[0])
        if abs(v)>1e-9: signs.append(v>0)
    return not signs or all(v==signs[0] for v in signs)

def grid(points, size):
    hull=convex_hull([(p.x,p.y) for p in points])
    if len(hull)<3: return [(p.x,p.y) for p in points]
    xs=[p.x for p in points]; ys=[p.y for p in points]; out=[]
    for row in range(size):
        y=min(ys)+(max(ys)-min(ys))*row/(size-1)
        for col in range(size):
            x=min(xs)+(max(xs)-min(xs))*col/(size-1)
            if inside((x,y),hull): out.append((x,y))
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--experiment-id", required=True)
    ap.add_argument("--prediction-run", type=Path, required=True)
    ap.add_argument("--evaluation-manifest", type=Path, required=True)
    ap.add_argument("--results-root", type=Path, default=ROOT/"results")
    ap.add_argument("--grid-size", type=int, default=25)
    args=ap.parse_args()
    prediction_path=args.prediction_run/"predictions.jsonl"
    predictions=[json.loads(x) for x in prediction_path.read_text(encoding="utf-8").splitlines() if x.strip()]
    manifest=[json.loads(x) for x in args.evaluation_manifest.read_text(encoding="utf-8").splitlines() if x.strip()]
    by_id={x["record_id"]:x for x in manifest}
    if not predictions or any(x["record_id"] not in by_id for x in predictions):
        raise ValueError("prediction run is empty or outside evaluation manifest")
    commit=subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,text=True,capture_output=True,check=True).stdout.strip()
    started=datetime.now(timezone.utc)
    run=create_run_directory(args.results_root,{"experiment_id":args.experiment_id,"git_commit":commit,"date":date.today().isoformat(),"dataset_version":"swissgeol_thurgau_v003_multiboundary_surface_from_frozen_reread","split_version":"v003_heldout_inherited_from_p2_reread","model":"frozen_paper2_all_ordered_boundaries_plus_idw","model_revision":"upstream_prediction_run_frozen","prompt_version":"not_applicable","seed":0,"hardware":{"device":"cpu","processor":platform.processor(),"gpu_used":False},"software":{"python":platform.python_version()},"config":{"ground_truth_sha256":file_sha256(args.evaluation_manifest),"upstream_prediction_run":str(args.prediction_run),"upstream_prediction_sha256":file_sha256(prediction_path),"prediction_reference_conditioning":"none_inherited_from_upstream_run","boundary_alignment":"ordered_interval_index_without_reference_guided_repair","spatial_metadata_source":"authoritative_structured_reference_borehole_coordinates_and_collar_elevation","coordinate_system":"CH1903+/LV95","interpolator":"IDW_power_2","grid_size":args.grid_size,"domain":"per_boundary_authoritative_reference_convex_hull","rights_review":"PENDING_MANUAL_PRE_SUBMISSION_REVIEW"},"started_utc":started.isoformat()})
    wall=time.perf_counter(); records=[]
    for pred in predictions:
        source=by_id[pred["record_id"]]; ref_path=Path(source["reference_path"])
        if file_sha256(ref_path)!=source["reference_sha256"]: raise ValueError(f"reference hash mismatch: {ref_path}")
        ref=json.loads(ref_path.read_text(encoding="utf-8")); borehole=ref["borehole"]
        intervals=sorted(ref["stratigraphy"]["intervals"],key=lambda x:(float(x["top_depth_m"]),float(x["bottom_depth_m"])))
        records.append({"record_id":pred["record_id"],"x":float(borehole["x_coordinate"]),"y":float(borehole["y_coordinate"]),"collar":float(borehole["collar_elevation_m"]),"reference":intervals,"raw":pred["first_pass_intervals"],"final":pred["final_intervals"],"decision":pred["decision"],"triggers":pred["triggers"]})
    max_boundaries=max(len(r["reference"]) for r in records)
    boundary_rows=[]; per_boundary=[]; aggregate={"raw":{"ref":[],"pred":[],"depth_abs":[]},"final":{"ref":[],"pred":[],"depth_abs":[]}}
    for index in range(max_boundaries):
        eligible=[r for r in records if len(r["reference"])>index]
        ref_points=[SurfacePoint(r["x"],r["y"],r["collar"]-float(r["reference"][index]["bottom_depth_m"]),r["record_id"]) for r in eligible]
        queries=grid(ref_points,args.grid_size); ref_surface=[idw_predict(ref_points,x,y) for x,y in queries]
        entry={"boundary_index":index+1,"reference_point_count":len(ref_points),"query_count":len(queries),"variants":{}}
        for variant in ("raw","final"):
            available=[r for r in eligible if len(r[variant])>index]
            points=[SurfacePoint(r["x"],r["y"],r["collar"]-float(r[variant][index]["bottom_depth_m"]),r["record_id"]) for r in available]
            surface=[idw_predict(points,x,y) for x,y in queries] if points else []
            errors=[abs(float(r[variant][index]["bottom_depth_m"])-float(r["reference"][index]["bottom_depth_m"])) for r in available]
            surf=surface_error_metrics(ref_surface,surface) if len(surface)==len(ref_surface) else {"count":0,"mae_m":None,"rmse_m":None,"max_abs_error_m":None}
            entry["variants"][variant]={"point_count":len(points),"coverage":len(points)/len(ref_points),"boundary_mae_m":sum(errors)/len(errors) if errors else None,"surface_error":surf}
            if surface and len(surface)==len(ref_surface):
                aggregate[variant]["ref"].extend(ref_surface); aggregate[variant]["pred"].extend(surface)
            aggregate[variant]["depth_abs"].extend(errors)
        per_boundary.append(entry)
        for r in eligible:
            row={"record_id":r["record_id"],"boundary_index":index+1,"x":r["x"],"y":r["y"],"reference_depth_m":float(r["reference"][index]["bottom_depth_m"]),"raw_depth_m":float(r["raw"][index]["bottom_depth_m"]) if len(r["raw"])>index else None,"final_depth_m":float(r["final"][index]["bottom_depth_m"]) if len(r["final"])>index else None,"decision":r["decision"],"triggers":r["triggers"]}
            boundary_rows.append(row)
    aggregate_metrics={}
    for variant,data in aggregate.items():
        aggregate_metrics[variant]={"boundary_observation_count":len(data["depth_abs"]),"boundary_mae_m":sum(data["depth_abs"])/len(data["depth_abs"]) if data["depth_abs"] else None,"surface_query_count":len(data["ref"]),"surface_error":surface_error_metrics(data["ref"],data["pred"]) if data["ref"] else {"count":0,"mae_m":None,"rmse_m":None,"max_abs_error_m":None}}
    metrics={"scope":"real image-derived multi-boundary downstream surface diagnostic","reference_ground_truth_tier":"GOLD_AUTHORITATIVE_SOURCE_AGREEMENT","data_status":"real_image_pdf_with_authoritative_structured_spatial_metadata","comparison":"raw_image_boundary_vs_constraint_reread_boundary_vs_authoritative_reference_surface","prediction_reference_conditioning":"none","reference_blinded_decision_policy":True,"document_count":len(records),"boundary_count":max_boundaries,"reference_point_count":sum(x["reference_point_count"] for x in per_boundary),"minimum_reference_points_per_boundary":min(x["reference_point_count"] for x in per_boundary),"per_boundary":per_boundary,"aggregate":aggregate_metrics,"triggered_document_count":sum(bool(r["triggers"]) for r in records),"accepted_reread_count":sum(r["decision"]=="ACCEPT_REREAD" for r in records),"needs_review_count":sum(str(r["decision"]).startswith("NEEDS_REVIEW") for r in records),"alignment_limitation":"ordered interval index is used without reference-guided repair; a missing or spurious upstream interval can shift deeper positional correspondence","spatial_metadata_limitation":"coordinates and collar elevations come from authoritative structured records rather than image extraction","selection_limitation":"one canton/source family and at most four ordered boundaries per record","upstream_prediction_run":str(args.prediction_run),"rights_review":"PENDING_MANUAL_PRE_SUBMISSION_REVIEW","wall_time_seconds":time.perf_counter()-wall,"peak_process_rss_kib":peak_process_rss_kib()}
    (run/"predictions.jsonl").write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in boundary_rows),encoding="utf-8")
    (run/"metrics.json").write_text(json.dumps(metrics,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (run/"errors.jsonl").write_text("",encoding="utf-8")
    (run/"run.log").write_text(f"started_utc={started.isoformat()}\ndocuments={len(records)}\nboundaries={max_boundaries}\nstatus=completed\n",encoding="utf-8")
    write_artifact_manifest(run); print(run)

if __name__=="__main__": main()
