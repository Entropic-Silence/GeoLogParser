#!/usr/bin/env python3
"""Train a column-aware dense NativeMM boundary detector and its ablations."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import subprocess
import time

import numpy as np
from PIL import Image
import torch
from transformers import AutoModelForImageTextToText, AutoProcessor

from geologparser.nativemm.dense_boundary import (
    SpatialBoundaryHead,
    boundary_loss,
    extract_peaks,
    gaussian_targets,
)


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cache_path(root: Path, row: dict, revision: str, height: int, width: int) -> Path:
    key = hashlib.sha256(f"{row['sample_id']}|{row['image']}|{revision}|{height}|{width}|spatial-v001".encode()).hexdigest()
    return root / f"{key}.pt"


def feature(
    row: dict, *, processor, backbone, root: Path, revision: str,
    height: int, width: int, device: str,
) -> dict[str, torch.Tensor]:
    path = cache_path(root, row, revision, height, width)
    if path.exists():
        return torch.load(path, map_location="cpu", weights_only=True)
    image = Image.open(row["image"]).convert("RGB")
    inputs = processor.image_processor(images=image, return_tensors="pt")
    with torch.inference_mode():
        output = backbone.get_image_features(
            inputs["pixel_values"].to(device),
            image_grid_thw=inputs["image_grid_thw"].to(device),
        )
    grid = inputs["image_grid_thw"][0].tolist()
    gh, gw = int(grid[1] // 2), int(grid[2] // 2)
    visual = output.pooler_output.detach().float().cpu().reshape(gh, gw, -1).permute(2, 0, 1)
    gray = np.asarray(image.convert("L").resize((width, height), Image.Resampling.BILINEAR), dtype=np.uint8)
    image.close()
    value = {"visual_grid": visual.to(torch.float16), "pixels": torch.from_numpy(gray)}
    root.mkdir(parents=True, exist_ok=True); torch.save(value, path)
    return value


def model_inputs(value: dict[str, torch.Tensor], device: str) -> tuple[torch.Tensor, torch.Tensor]:
    visual = value["visual_grid"].unsqueeze(0).to(device, dtype=torch.float32)
    pixels = value["pixels"].unsqueeze(0).unsqueeze(0).to(device, dtype=torch.float32) / 255.0
    pixels = 1.0 - pixels
    return visual, pixels


def greedy(predicted: list[float], expected: list[float], tolerance: float) -> tuple[int, int, int, list[float]]:
    remaining = set(range(len(expected))); tp = fp = 0; errors = []
    for value in predicted:
        options = sorted((abs(value - expected[index]), index) for index in remaining)
        if options and options[0][0] <= tolerance:
            tp += 1; errors.append(options[0][0]); remaining.remove(options[0][1])
        else:
            fp += 1
    return tp, fp, len(remaining), errors


def prf(tp: int, fp: int, fn: int) -> dict:
    p = tp / (tp + fp) if tp + fp else 0.0; r = tp / (tp + fn) if tp + fn else 0.0
    return {"precision": p, "recall": r, "f1": 2*p*r/(p+r) if p+r else 0.0, "true_positive": tp, "false_positive": fp, "false_negative": fn}


def infer(model, selected: list[dict], cache: dict[str, dict[str, torch.Tensor]], device: str) -> list[dict]:
    model.eval(); output = []
    with torch.inference_mode():
        for row in selected:
            visual, pixels = model_inputs(cache[row["sample_id"]], device)
            logits, roles = model(visual, pixels)
            output.append({"row": row, "probabilities": torch.sigmoid(logits[0]).cpu(), "roles": roles[0].cpu()})
    return output


def predicted_depths(item: dict, threshold: float, separation: int) -> list[tuple[float, float, float]]:
    row = item["row"]; geometry = row["geometry"]
    slope, intercept = geometry.get("depth_per_pixel"), geometry.get("intercept_m")
    if slope is None or intercept is None:
        return []
    _, crop_y1, _, crop_y2 = geometry["crop_bbox_page"]
    return [
        (float(slope) * (crop_y1 + y * (crop_y2 - crop_y1)) + float(intercept), y, confidence)
        for y, confidence in extract_peaks(item["probabilities"], threshold=threshold, minimum_separation_bins=separation)
    ]


def evaluate(inferences: list[dict], threshold: float, separation: int, tolerance: float) -> dict:
    btp = bfp = bfn = itp = ifp = ifn = 0; errors = []; predictions = []
    for item in inferences:
        row = item["row"]
        predicted = predicted_depths(item, threshold, separation)
        pdepth = sorted({round(value[0], 8) for value in predicted})
        edepth = sorted(float(value["depth_m"]) for value in row["boundaries"])
        tp, fp, fn, local = greedy(pdepth, edepth, tolerance)
        btp += tp; bfp += fp; bfn += fn; errors.extend(local)
        pinterval = list(zip(pdepth, pdepth[1:])); einterval = list(zip(edepth, edepth[1:])); remaining = set(range(len(einterval)))
        for top, bottom in pinterval:
            options = [index for index in remaining if abs(top-einterval[index][0]) <= tolerance and abs(bottom-einterval[index][1]) <= tolerance]
            if options: itp += 1; remaining.remove(options[0])
            else: ifp += 1
        ifn += len(remaining)
        predictions.append({
            "sample_id": row["sample_id"], "source_group": row["source_group"],
            "expected_depths_m": edepth,
            "predicted": [{"depth_m": d, "normalized_y": y, "confidence": c} for d,y,c in predicted],
            "column_role_weights": item["roles"].tolist(),
        })
    boundary = prf(btp,bfp,bfn); boundary["mae_m"] = sum(errors)/len(errors) if errors else None
    return {
        "boundary": boundary, "interval": prf(itp,ifp,ifn),
        "critical_numerical_error_rate": bfp/(btp+bfp) if btp+bfp else None,
        "structural_evidence_coverage": boundary["recall"], "predictions": predictions,
    }


def threshold_search(inferences: list[dict], separation: int, tolerance: float) -> tuple[float, dict, str]:
    scored = [(float(t), evaluate(inferences,float(t),separation,tolerance)) for t in np.linspace(.05,.95,91)]
    reliable = [row for row in scored if row[1]["boundary"]["precision"] >= .90]
    if reliable:
        chosen=max(reliable,key=lambda row:(row[1]["boundary"]["recall"],row[1]["boundary"]["f1"],row[0])); policy="max_recall_precision_ge_0.90"
    else:
        chosen=max(scored,key=lambda row:(row[1]["boundary"]["f1"],row[1]["boundary"]["precision"],row[0])); policy="max_f1_no_precision_ge_0.90_point"
    return chosen[0], chosen[1], policy


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--experiment-id",required=True); parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--dataset-root",type=Path,default=Path("/data/GeoLogParser/datasets/paper2_nativemm_dense_boundary_v001"))
    parser.add_argument("--model",type=Path,default=Path("/data/GeoLogParser/models/huggingface/PaddleOCR-VL-1.6"))
    parser.add_argument("--model-revision",default="c5630abae1d940eafe0697512a0325494b02ab42")
    parser.add_argument("--cache-root",type=Path,default=Path("/root/GeoLogParser/.cache/nativemm_spatial_v001"))
    parser.add_argument("--device",default="cuda:0"); parser.add_argument("--mode",choices=["fused","pixel_only","visual_only"],default="fused")
    parser.add_argument("--height",type=int,default=512); parser.add_argument("--width",type=int,default=256)
    parser.add_argument("--hidden-dim",type=int,default=64); parser.add_argument("--role-heads",type=int,default=4)
    parser.add_argument("--synthetic-epochs",type=int,default=14); parser.add_argument("--real-epochs",type=int,default=55)
    parser.add_argument("--learning-rate",type=float,default=2e-4); parser.add_argument("--seed",type=int,default=20260816)
    parser.add_argument("--minimum-separation-bins",type=int,default=3); parser.add_argument("--tolerance-m",type=float,default=.05)
    args=parser.parse_args()
    if args.output.exists(): raise FileExistsError(f"immutable result path already exists: {args.output}")
    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)
    torch.cuda.set_device(args.device); torch.cuda.empty_cache(); torch.cuda.reset_peak_memory_stats(args.device)
    train=rows(args.dataset_root/'train.jsonl'); development=rows(args.dataset_root/'development.jsonl'); all_rows=train+development
    processor=AutoProcessor.from_pretrained(args.model,trust_remote_code=False)
    backbone=AutoModelForImageTextToText.from_pretrained(args.model,trust_remote_code=False,dtype=torch.bfloat16).to(args.device).eval()
    for parameter in backbone.parameters(): parameter.requires_grad_(False)
    cache={}; feature_started=time.perf_counter()
    for index,row in enumerate(all_rows,1):
        cache[row['sample_id']]=feature(row,processor=processor,backbone=backbone,root=args.cache_root,revision=args.model_revision,height=args.height,width=args.width,device=args.device)
        if index%25==0: print(f"cached {index}/{len(all_rows)}",flush=True)
    feature_seconds=time.perf_counter()-feature_started; del backbone; torch.cuda.empty_cache()
    model=SpatialBoundaryHead(1024,args.hidden_dim,args.role_heads,args.mode).to(args.device)
    optimizer=torch.optim.AdamW(model.parameters(),lr=args.learning_rate,weight_decay=1e-4)
    synthetic=[r for r in train if r['source_tier']=='SYNTHETIC']; real_fit=[r for r in train if r['source_tier']!='SYNTHETIC' and r['fold']!=1]; calibration=[r for r in train if r['source_tier']!='SYNTHETIC' and r['fold']==1]
    losses=[]
    def fit(selected,epochs,phase):
        model.train()
        for epoch in range(epochs):
            shuffled=list(selected); random.Random(args.seed+epoch+(1000 if phase=='real' else 0)).shuffle(shuffled)
            for row in shuffled:
                visual,pixels=model_inputs(cache[row['sample_id']],args.device); logits,_=model(visual,pixels)
                target=gaussian_targets([x['y'] for x in row['boundaries']],args.height).unsqueeze(0).to(args.device)
                loss=boundary_loss(logits,target); optimizer.zero_grad(set_to_none=True); loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(),1.0); optimizer.step()
                losses.append({'phase':phase,'loss':float(loss.detach().cpu())})
    training_started=time.perf_counter(); fit(synthetic,args.synthetic_epochs,'synthetic')
    for group in optimizer.param_groups: group['lr']=args.learning_rate*.30
    fit(real_fit+synthetic[::6],args.real_epochs,'real'); training_seconds=time.perf_counter()-training_started
    calibration_inference=infer(model,calibration,cache,args.device); threshold,cal_metrics,policy=threshold_search(calibration_inference,args.minimum_separation_bins,args.tolerance_m)
    evaluation_rows=[r for r in development if r['source_dataset']=='bgs_offshore_gold_v001' and r['fold']==0]
    evaluation_started=time.perf_counter(); evaluation=evaluate(infer(model,evaluation_rows,cache,args.device),threshold,args.minimum_separation_bins,args.tolerance_m); evaluation_seconds=time.perf_counter()-evaluation_started
    predictions=evaluation.pop('predictions'); calibration_predictions=cal_metrics.pop('predictions')
    args.output.mkdir(parents=True); checkpoint=args.output/'spatial_boundary_head.pt'; torch.save({'state_dict':model.state_dict(),'mode':args.mode,'hidden_dim':args.hidden_dim,'role_heads':args.role_heads,'threshold':threshold,'height':args.height,'width':args.width},checkpoint)
    metrics={
      'experiment_id':args.experiment_id,'status':'completed','timestamp_utc':datetime.now(timezone.utc).isoformat(),
      'git_commit':subprocess.run(['git','rev-parse','HEAD'],check=True,text=True,stdout=subprocess.PIPE).stdout.strip(),
      'architecture':'column_role_attention_spatial_boundary_head','evidence_mode':args.mode,'backbone':str(args.model),'model_revision':args.model_revision,
      'dataset_root':str(args.dataset_root),'train_sha256':digest(args.dataset_root/'train.jsonl'),'development_sha256':digest(args.dataset_root/'development.jsonl'),
      'training_counts':{'synthetic':len(synthetic),'real_fit':len(real_fit),'real_calibration':len(calibration)},'evaluation_sample_count':len(evaluation_rows),
      'threshold':threshold,'threshold_policy':policy,'calibration_metrics':cal_metrics,
      'boundary_at_0_05m':evaluation['boundary'],'interval_at_0_05m':evaluation['interval'],'critical_numerical_error_rate':evaluation['critical_numerical_error_rate'],'structural_evidence_coverage':evaluation['structural_evidence_coverage'],
      'feature_extraction_seconds':feature_seconds,'training_seconds':training_seconds,'evaluation_seconds':evaluation_seconds,'seconds_per_evaluation_page':evaluation_seconds/len(evaluation_rows) if evaluation_rows else None,
      'peak_allocated_gib':torch.cuda.max_memory_allocated(args.device)/1024**3,'peak_reserved_gib':torch.cuda.max_memory_reserved(args.device)/1024**3,
      'mean_loss':sum(x['loss'] for x in losses)/len(losses),'final_loss':losses[-1]['loss'],'checkpoint_sha256':digest(checkpoint),
      'scope':'source-disjoint BGS v001 development; BGS v002 and California v004/v005 unopened',
    }
    (args.output/'metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    (args.output/'predictions.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in predictions),encoding='utf-8')
    (args.output/'calibration_predictions.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in calibration_predictions),encoding='utf-8')
    (args.output/'losses.jsonl').write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in losses),encoding='utf-8')
    print(json.dumps(metrics,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
