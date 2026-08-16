#!/usr/bin/env python3
"""Source-disjoint semantic column gate for BGS v021 candidates."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np

from geologparser.layout import DepthBoundaryCandidate

from scripts.run_bgs_layout_method_development import (
    boundary_metrics,
    interval_metrics,
    monotonic_sequence,
)


FEATURES = (
    "center_x", "width", "activity", "rank_score", "distance_to_depth",
    "candidate_count_log", "mean_line", "maximum_line", "mean_change",
    "maximum_change", "mean_cross_column", "maximum_cross_column",
    "mean_scale_quality",
)


@dataclass
class Column:
    record_id: str
    page: int
    key: tuple[int, int]
    candidates: list[dict]
    features: dict[str, float]
    label: int


class Ranker:
    def __init__(self) -> None:
        self.mean=np.zeros(len(FEATURES)); self.scale=np.ones(len(FEATURES)); self.weights=np.zeros(len(FEATURES)); self.bias=0.0
    def matrix(self,rows): return np.asarray([[r.features.get(k,0.0) for k in FEATURES] for r in rows],dtype=float)
    def fit(self,rows):
        x=self.matrix(rows); y=np.asarray([r.label for r in rows],dtype=float)
        if len(set(y.tolist()))<2: raise ValueError('column gate needs positive and negative columns')
        self.mean=x.mean(0); self.scale=x.std(0); self.scale[self.scale<1e-8]=1; x=(x-self.mean)/self.scale
        weight=np.where(y==1,max(1.0,float((y==0).sum())/max(1,int((y==1).sum()))),1.0)
        for _ in range(1600):
            z=np.clip(x@self.weights+self.bias,-30,30); p=1/(1+np.exp(-z)); error=(p-y)*weight
            self.weights-=.035*((x.T@error)/weight.sum()+.025*self.weights); self.bias-=.035*float(error.sum()/weight.sum())
        return self
    def predict(self,rows):
        if not rows: return np.asarray([],dtype=float)
        x=(self.matrix(rows)-self.mean)/self.scale; z=np.clip(x@self.weights+self.bias,-30,30); return 1/(1+np.exp(-z))
    def to_dict(self): return {'features':list(FEATURES),'mean':self.mean.tolist(),'scale':self.scale.tolist(),'weights':self.weights.tolist(),'bias':self.bias}


def refs(source): return sorted({float(x[k]) for x in source['intervals'] for k in ('top_depth_m','bottom_depth_m')})


def build_columns(prediction, reference):
    groups={}
    for candidate in prediction['ranked_candidates']:
        if candidate['page_family']!='calibrated_graphic': continue
        center=float(candidate['features'].get('graphic_column_center',(candidate['bbox'][0]+candidate['bbox'][2])/2))
        key=(int(candidate['page']),round(center*10000)); groups.setdefault(key,[]).append(candidate)
    output=[]
    for key,candidates in groups.items():
        fs=[c['features'] for c in candidates]
        def mean(name): return sum(float(x.get(name,0)) for x in fs)/len(fs)
        def maximum(name): return max(float(x.get(name,0)) for x in fs)
        feature={
          'center_x':mean('graphic_column_center'),'width':mean('graphic_column_width'),'activity':mean('graphic_column_activity'),
          'rank_score':mean('graphic_column_rank'),'distance_to_depth':mean('depth_x_distance'),'candidate_count_log':min(1.0,math.log1p(len(candidates))/math.log(501)),
          'mean_line':mean('graphic_line_support'),'maximum_line':maximum('graphic_line_support'),'mean_change':mean('graphic_change_support'),
          'maximum_change':maximum('graphic_change_support'),'mean_cross_column':mean('graphic_cross_column_support'),'maximum_cross_column':maximum('graphic_cross_column_support'),
          'mean_scale_quality':mean('page_scale_inliers')*(1-mean('page_scale_rmse')),
        }
        label=int(any(any(abs(float(c['value_m'])-r)<=.10 for r in reference) for c in candidates))
        output.append(Column(prediction['record_id'],key[0],key,candidates,feature,label))
    return output


def reconstruct(row):
    return DepthBoundaryCandidate(float(row['value_m']),int(row['page']),tuple(float(x) for x in row['bbox']),row['candidate_source'],dict(row['features']),tuple(row['provenance']))


def gated_candidates(prediction,columns,scores,top_k):
    keep={column.key for column,_ in sorted(zip(columns,scores),key=lambda x:x[1],reverse=True)[:top_k]}
    rows=[]; probabilities=[]
    for row in prediction['ranked_candidates']:
        if row['page_family']=='calibrated_graphic':
            center=float(row['features'].get('graphic_column_center',(row['bbox'][0]+row['bbox'][2])/2)); key=(int(row['page']),round(center*10000))
            if key not in keep: continue
        rows.append(reconstruct(row)); probabilities.append(float(row['probability']))
    return rows,probabilities


def tune(predictions,columns_by_id,scores_by_id,references):
    best=None
    for top_k in range(1,9):
        candidates={}; probabilities={}
        for record_id in predictions:
            candidates[record_id],probabilities[record_id]=gated_candidates(predictions[record_id],columns_by_id[record_id],scores_by_id[record_id],top_k)
        for threshold in [x/100 for x in range(10,91,2)]:
            values={rid:[x[0].value_m for x in monotonic_sequence(candidates[rid],probabilities[rid],threshold)] for rid in candidates}
            interval=interval_metrics(values,references,.05); boundary=boundary_metrics(values,references,.05)
            key=(interval['f1'],boundary['f1'],boundary['precision'],-top_k,-threshold)
            if best is None or key>best[0]: best=(key,top_k,threshold)
    return best[1],best[2]


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--analysis',type=Path,required=True); parser.add_argument('--manifest',type=Path,required=True); parser.add_argument('--output',type=Path,required=True); parser.add_argument('--sequence-threshold',type=float); parser.add_argument('--top-k',type=int); args=parser.parse_args()
    started=time.perf_counter(); analysis=json.loads(args.analysis.read_text()); sources={r['record_id']:r for r in map(json.loads,args.manifest.open())}; references={k:refs(v) for k,v in sources.items()}
    predictions={r['record_id']:r for r in analysis['predictions']}; folds={k:int(v['fold']) for k,v in predictions.items()}; columns={k:build_columns(v,references[k]) for k,v in predictions.items()}
    output_values={}; models=[]; column_scores={}
    for fold in sorted(set(folds.values())):
        train_ids=[k for k in predictions if folds[k]!=fold]; test_ids=[k for k in predictions if folds[k]==fold]
        ranker=Ranker().fit([c for k in train_ids for c in columns[k]])
        train_scores={k:ranker.predict(columns[k]).tolist() for k in train_ids}; tuned_top_k,tuned_threshold=tune({k:predictions[k] for k in train_ids},{k:columns[k] for k in train_ids},train_scores,{k:references[k] for k in train_ids}); top_k=args.top_k if args.top_k is not None else tuned_top_k; threshold=args.sequence_threshold if args.sequence_threshold is not None else tuned_threshold
        for record_id in test_ids:
            score=ranker.predict(columns[record_id]).tolist(); column_scores[record_id]=score
            candidates,probabilities=gated_candidates(predictions[record_id],columns[record_id],score,top_k)
            output_values[record_id]=[x[0].value_m for x in monotonic_sequence(candidates,probabilities,threshold)]
        models.append({'fold':fold,'train_documents':len(train_ids),'test_documents':len(test_ids),'top_k':top_k,'sequence_threshold':threshold,'ranker':ranker.to_dict()})
    boundary=boundary_metrics(output_values,references,.05); interval=interval_metrics(output_values,references,.05)
    report={
      'analysis_scope':'BGS v001 source-disjoint semantic column gate over v021 candidates','source_analysis':str(args.analysis),'source_analysis_sha256':hashlib.sha256(args.analysis.read_bytes()).hexdigest(),
      'manifest':str(args.manifest),'manifest_sha256':hashlib.sha256(args.manifest.read_bytes()).hexdigest(),'document_count':len(predictions),'column_count':sum(map(len,columns.values())),
      'positive_column_count':sum(c.label for values in columns.values() for c in values),'boundary_at_0_05m':boundary,'interval_at_0_05m':interval,'fold_models':models,
      'predictions':[{'record_id':k,'fold':folds[k],'predicted_boundaries_m':output_values[k],'columns':[{'page':c.page,'key':list(c.key),'label':c.label,'probability':p,'features':c.features} for c,p in zip(columns[k],column_scores[k])]} for k in sorted(predictions)],
      'reference_blinding':'outer test references are used only for scoring; column gate, top-k and sequence threshold use other source folds','wall_time_seconds':time.perf_counter()-started,
    }
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:report[k] for k in ('column_count','positive_column_count','boundary_at_0_05m','interval_at_0_05m','wall_time_seconds')},indent=2))


if __name__=='__main__': main()
