#!/usr/bin/env python3
"""Source-disjoint post-sequence risk pruning for BGS v022."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace
import time

import numpy as np

from scripts.analyze_bgs_column_gate import gated_candidates
from scripts.run_bgs_layout_method_development import (
    boundary_metrics,
    interval_metrics,
    monotonic_sequence,
)


FEATURES = (
    "candidate_probability", "column_probability", "combined_probability",
    "source_printed", "source_graphic", "source_metadata", "line_support",
    "change_support", "cross_column_support", "scale_quality", "value_support",
    "cross_family_value_support", "previous_gap_log", "next_gap_log",
    "minimum_gap_log", "is_sequence_endpoint", "is_zero", "is_terminal_like",
)


@dataclass
class Event:
    record_id: str
    value_m: float
    probability: float
    features: dict[str, float]
    label: int


class LogisticRiskRanker:
    def __init__(self) -> None:
        self.mean=np.zeros(len(FEATURES)); self.scale=np.ones(len(FEATURES)); self.weights=np.zeros(len(FEATURES)); self.bias=0.0
    def matrix(self,events):
        if not events: return np.empty((0,len(FEATURES)),dtype=float)
        return np.asarray([[event.features.get(name,0.0) for name in FEATURES] for event in events],dtype=float)
    def fit(self,events):
        matrix=self.matrix(events); target=np.asarray([event.label for event in events],dtype=float)
        if len(set(target.tolist()))<2: raise ValueError('risk ranker requires correct and incorrect events')
        self.mean=matrix.mean(0); self.scale=matrix.std(0); self.scale[self.scale<1e-8]=1; matrix=(matrix-self.mean)/self.scale
        positive_weight=max(1.0,float((target==0).sum())/max(1,int((target==1).sum()))); weights=np.where(target==1,positive_weight,1.0)
        for _ in range(1600):
            logits=np.clip(matrix@self.weights+self.bias,-30,30); probability=1/(1+np.exp(-logits)); error=(probability-target)*weights
            self.weights-=.035*((matrix.T@error)/weights.sum()+.025*self.weights); self.bias-=.035*float(error.sum()/weights.sum())
        return self
    def predict(self,events):
        if not events: return np.asarray([],dtype=float)
        matrix=(self.matrix(events)-self.mean)/self.scale; logits=np.clip(matrix@self.weights+self.bias,-30,30); return 1/(1+np.exp(-logits))
    def to_dict(self): return {'features':list(FEATURES),'mean':self.mean.tolist(),'scale':self.scale.tolist(),'weights':self.weights.tolist(),'bias':self.bias}


def references(source): return sorted({float(row[key]) for row in source['intervals'] for key in ('top_depth_m','bottom_depth_m')})


def event_rows(record_id,prediction,column_rows,reference,top_k=6,sequence_threshold=.32):
    columns=[SimpleNamespace(key=tuple(row['key'])) for row in column_rows]; scores=[float(row['probability']) for row in column_rows]
    candidates,probabilities=gated_candidates(prediction,columns,scores,top_k,0.0)
    selected=monotonic_sequence(candidates,probabilities,sequence_threshold)
    score_by_key={tuple(row['key']):float(row['probability']) for row in column_rows}
    output=[]
    for index,(candidate,probability) in enumerate(selected):
        value=float(candidate.value_m); feature=candidate.features
        if candidate.candidate_source=='graphic_scale_transition':
            center=float(feature.get('graphic_column_center',(candidate.bbox[0]+candidate.bbox[2])/2)); column_probability=score_by_key.get((candidate.page,round(center*10000)),0.0)
        else: column_probability=1.0
        supports=[row for row in candidates if abs(float(row.value_m)-value)<=.05]
        families={row.candidate_source for row in supports}
        previous_gap=value-float(selected[index-1][0].value_m) if index else value
        next_gap=float(selected[index+1][0].value_m)-value if index+1<len(selected) else previous_gap
        terminal=max(reference) if reference else value
        features={
          'candidate_probability':float(probability),'column_probability':column_probability,'combined_probability':float(probability)*column_probability,
          'source_printed':float(candidate.candidate_source=='printed_depth'),'source_graphic':float(candidate.candidate_source=='graphic_scale_transition'),'source_metadata':float(candidate.candidate_source=='metadata_final_depth'),
          'line_support':max(float(feature.get('printed_line_support',0)),float(feature.get('graphic_line_support',0))),
          'change_support':float(feature.get('graphic_change_support',0)),'cross_column_support':float(feature.get('graphic_cross_column_support',0)),
          'scale_quality':float(feature.get('page_scale_inliers',0))*(1-float(feature.get('page_scale_rmse',1))),
          'value_support':min(1.0,len(supports)/4),'cross_family_value_support':min(1.0,len(families)/2),
          'previous_gap_log':min(1.0,math.log1p(max(0,previous_gap))/math.log(101)),'next_gap_log':min(1.0,math.log1p(max(0,next_gap))/math.log(101)),
          'minimum_gap_log':min(1.0,math.log1p(max(0,min(previous_gap,next_gap)))/math.log(101)),'is_sequence_endpoint':float(index==0 or index+1==len(selected)),
          'is_zero':float(abs(value)<=.05),'is_terminal_like':float(abs(value-terminal)<=.10),
        }
        output.append(Event(record_id,value,float(probability),features,int(any(abs(value-r)<=.05 for r in reference))))
    return output


def metrics(events_by_id,scores_by_id,threshold,reference_by_id):
    predictions={record_id:sorted(event.value_m for event,score in zip(events,scores_by_id[record_id]) if score>=threshold) for record_id,events in events_by_id.items()}
    return boundary_metrics(predictions,reference_by_id,.05),interval_metrics(predictions,reference_by_id,.05),predictions


def tune(events_by_id,scores_by_id,reference_by_id,minimum_precision=None):
    best=None
    for threshold in [index/100 for index in range(5,100)]:
        boundary,interval,predictions=metrics(events_by_id,scores_by_id,threshold,reference_by_id); accepted=sum(map(len,predictions.values()))
        if minimum_precision is not None and boundary['precision']<minimum_precision: continue
        key=((accepted if minimum_precision is not None else interval['f1']),boundary['f1'],boundary['precision'],-threshold)
        if best is None or key>best[0]: best=(key,threshold)
    return best[1] if best else .99


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--source-analysis',type=Path,required=True); parser.add_argument('--column-analysis',type=Path,required=True); parser.add_argument('--manifest',type=Path,required=True); parser.add_argument('--output',type=Path,required=True); args=parser.parse_args()
    started=time.perf_counter(); source=json.loads(args.source_analysis.read_text()); column=json.loads(args.column_analysis.read_text()); sources={row['record_id']:row for row in map(json.loads,args.manifest.open())}; refs={key:references(value) for key,value in sources.items()}
    predictions={row['record_id']:row for row in source['predictions']}; column_rows={row['record_id']:row['columns'] for row in column['predictions']}; folds={row['record_id']:int(row['fold']) for row in source['predictions']}
    events={record_id:event_rows(record_id,predictions[record_id],column_rows[record_id],refs[record_id]) for record_id in predictions}
    oof_scores={}; thresholds={}; selective_thresholds={}; models=[]
    for fold in sorted(set(folds.values())):
        train_ids=[record_id for record_id in events if folds[record_id]!=fold]; test_ids=[record_id for record_id in events if folds[record_id]==fold]
        ranker=LogisticRiskRanker().fit([event for record_id in train_ids for event in events[record_id]])
        train_scores={record_id:ranker.predict(events[record_id]).tolist() for record_id in train_ids}
        threshold=tune({record_id:events[record_id] for record_id in train_ids},train_scores,{record_id:refs[record_id] for record_id in train_ids})
        selective=tune({record_id:events[record_id] for record_id in train_ids},train_scores,{record_id:refs[record_id] for record_id in train_ids},.95)
        for record_id in test_ids: oof_scores[record_id]=ranker.predict(events[record_id]).tolist(); thresholds[record_id]=threshold; selective_thresholds[record_id]=selective
        models.append({'fold':fold,'train_documents':len(train_ids),'test_documents':len(test_ids),'threshold':threshold,'selective_threshold':selective,'ranker':ranker.to_dict()})
    predictions_by_id={record_id:sorted(event.value_m for event,score in zip(events[record_id],oof_scores[record_id]) if score>=thresholds[record_id]) for record_id in events}
    selective_by_id={record_id:sorted(event.value_m for event,score in zip(events[record_id],oof_scores[record_id]) if score>=selective_thresholds[record_id]) for record_id in events}
    boundary=boundary_metrics(predictions_by_id,refs,.05); interval=interval_metrics(predictions_by_id,refs,.05); selective_boundary=boundary_metrics(selective_by_id,refs,.05); selective_interval=interval_metrics(selective_by_id,refs,.05)
    report={
      'analysis_scope':'BGS v001 source-disjoint post-sequence risk pruning over v022','source_analysis':str(args.source_analysis),'source_analysis_sha256':hashlib.sha256(args.source_analysis.read_bytes()).hexdigest(),'column_analysis':str(args.column_analysis),'column_analysis_sha256':hashlib.sha256(args.column_analysis.read_bytes()).hexdigest(),
      'manifest':str(args.manifest),'manifest_sha256':hashlib.sha256(args.manifest.read_bytes()).hexdigest(),'document_count':len(events),'input_event_count':sum(map(len,events.values())),'accepted_event_count':sum(map(len,predictions_by_id.values())),'selective_event_count':sum(map(len,selective_by_id.values())),
      'boundary_at_0_05m':boundary,'interval_at_0_05m':interval,'selective_boundary_at_0_05m':selective_boundary,'selective_interval_at_0_05m':selective_interval,'fold_models':models,
      'predictions':[{'record_id':record_id,'fold':folds[record_id],'threshold':thresholds[record_id],'selective_threshold':selective_thresholds[record_id],'predicted_boundaries_m':predictions_by_id[record_id],'selective_boundaries_m':selective_by_id[record_id],'events':[{'value_m':event.value_m,'label':event.label,'risk_probability':score,'features':event.features} for event,score in zip(events[record_id],oof_scores[record_id])]} for record_id in sorted(events)],
      'reference_blinding':'outer source-fold labels are used only for scoring; risk model and thresholds use other source folds','wall_time_seconds':time.perf_counter()-started,
    }
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n'); print(json.dumps({key:report[key] for key in ('input_event_count','accepted_event_count','boundary_at_0_05m','interval_at_0_05m','selective_event_count','selective_boundary_at_0_05m','wall_time_seconds')},indent=2))


if __name__=='__main__': main()
