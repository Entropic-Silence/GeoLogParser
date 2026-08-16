#!/usr/bin/env python3
"""Source-disjoint interval-pair ranker over v021 boundary candidates."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np


FEATURES = (
    "left_probability", "right_probability", "minimum_probability", "probability_product",
    "depth_gap_log", "same_page", "page_gap", "visual_order_consistent",
    "left_graphic", "right_graphic", "both_graphic", "both_printed", "contains_metadata",
    "minimum_line_support", "minimum_change_support", "cross_column_support",
    "minimum_scale_quality", "candidate_rank_gap",
)


@dataclass
class Pair:
    record_id: str
    left: dict
    right: dict
    features: dict[str, float]
    label: int


class LogisticPairRanker:
    def __init__(self) -> None:
        self.mean=np.zeros(len(FEATURES)); self.scale=np.ones(len(FEATURES)); self.weights=np.zeros(len(FEATURES)); self.bias=0.0
    def matrix(self,pairs):
        if not pairs: return np.empty((0,len(FEATURES)),dtype=float)
        return np.asarray([[p.features.get(k,0.0) for k in FEATURES] for p in pairs],dtype=float)
    def fit(self,pairs):
        x=self.matrix(pairs); y=np.asarray([p.label for p in pairs],dtype=float)
        if len(set(y.tolist()))<2: raise ValueError('pair ranker requires both classes')
        self.mean=x.mean(0); self.scale=x.std(0); self.scale[self.scale<1e-8]=1; x=(x-self.mean)/self.scale
        weight=np.where(y==1,max(1.0,float((y==0).sum())/max(1,int((y==1).sum()))),1.0)
        for _ in range(1800):
            logits=np.clip(x@self.weights+self.bias,-30,30); p=1/(1+np.exp(-logits)); error=(p-y)*weight
            self.weights-=.035*((x.T@error)/weight.sum()+.02*self.weights); self.bias-=.035*float(error.sum()/weight.sum())
        return self
    def predict(self,pairs):
        if not pairs: return np.asarray([],dtype=float)
        x=(self.matrix(pairs)-self.mean)/self.scale; z=np.clip(x@self.weights+self.bias,-30,30); return 1/(1+np.exp(-z))
    def to_dict(self): return {'features':list(FEATURES),'mean':self.mean.tolist(),'scale':self.scale.tolist(),'weights':self.weights.tolist(),'bias':self.bias}


def references(row): return sorted({float(x[k]) for x in row['intervals'] for k in ('top_depth_m','bottom_depth_m')})
def matches(value,reference,tolerance=.05): return abs(float(value)-float(reference))<=tolerance


def make_pairs(prediction, refs, maximum_rank_gap=14):
    best={}
    for candidate in prediction['ranked_candidates']:
        key=round(float(candidate['value_m'])*20)
        if key not in best or float(candidate['probability'])>float(best[key]['probability']): best[key]=candidate
    candidates=sorted(best.values(),key=lambda x:float(x['value_m']))
    ref_pairs=list(zip(refs,refs[1:])); output=[]
    for i,left in enumerate(candidates):
        for j in range(i+1,min(len(candidates),i+1+maximum_rank_gap)):
            right=candidates[j]; lv=float(left['value_m']); rv=float(right['value_m'])
            if rv<=lv+.025: continue
            lf=left['features']; rf=right['features']; lp=float(left['probability']); rp=float(right['probability'])
            left_y=(left['bbox'][1]+left['bbox'][3])/2; right_y=(right['bbox'][1]+right['bbox'][3])/2
            lfam=left['page_family']; rfam=right['page_family']
            feature={
              'left_probability':lp,'right_probability':rp,'minimum_probability':min(lp,rp),'probability_product':lp*rp,
              'depth_gap_log':min(1.0,math.log1p(rv-lv)/math.log(101.0)),'same_page':float(left['page']==right['page']),
              'page_gap':min(1.0,abs(int(right['page'])-int(left['page']))/4),'visual_order_consistent':float((right['page'],right_y)>(left['page'],left_y)),
              'left_graphic':float(lfam=='calibrated_graphic'),'right_graphic':float(rfam=='calibrated_graphic'),
              'both_graphic':float(lfam==rfam=='calibrated_graphic'),'both_printed':float(lfam==rfam=='printed_boundary'),
              'contains_metadata':float('terminal_metadata' in (lfam,rfam)),
              'minimum_line_support':min(float(lf.get('graphic_line_support',lf.get('printed_line_support',0))),float(rf.get('graphic_line_support',rf.get('printed_line_support',0)))),
              'minimum_change_support':min(float(lf.get('graphic_change_support',0)),float(rf.get('graphic_change_support',0))),
              'cross_column_support':min(float(lf.get('graphic_cross_column_support',0)),float(rf.get('graphic_cross_column_support',0))),
              'minimum_scale_quality':min(float(lf.get('page_scale_inliers',0))*(1-float(lf.get('page_scale_rmse',1))),float(rf.get('page_scale_inliers',0))*(1-float(rf.get('page_scale_rmse',1)))),
              'candidate_rank_gap':min(1.0,(j-i)/maximum_rank_gap),
            }
            label=int(any(matches(lv,a) and matches(rv,b) for a,b in ref_pairs))
            output.append(Pair(prediction['record_id'],left,right,feature,label))
    return output


def pair_metrics(selected, reference_by_id):
    tp=fp=fn=0
    for record_id,values in selected.items():
        expected=list(zip(reference_by_id[record_id],reference_by_id[record_id][1:])); remaining=set(range(len(expected)))
        for left,right,_ in values:
            options=[i for i in remaining if matches(left,expected[i][0]) and matches(right,expected[i][1])]
            if options: tp+=1; remaining.remove(options[0])
            else: fp+=1
        fn+=len(remaining)
    p=tp/(tp+fp) if tp+fp else 0; r=tp/(tp+fn) if tp+fn else 0
    return {'precision':p,'recall':r,'f1':2*p*r/(p+r) if p+r else 0,'true_positive':tp,'false_positive':fp,'false_negative':fn}


def boundary_metrics(selected, reference_by_id):
    tp=fp=fn=0
    for record_id,pairs in selected.items():
        predicted=sorted({v for left,right,_ in pairs for v in (left,right)}); remaining=set(range(len(reference_by_id[record_id])))
        for value in predicted:
            options=sorted((abs(value-reference_by_id[record_id][i]),i) for i in remaining)
            if options and options[0][0]<=.05: tp+=1; remaining.remove(options[0][1])
            else: fp+=1
        fn+=len(remaining)
    p=tp/(tp+fp) if tp+fp else 0; r=tp/(tp+fn) if tp+fn else 0
    return {'precision':p,'recall':r,'f1':2*p*r/(p+r) if p+r else 0,'true_positive':tp,'false_positive':fp,'false_negative':fn,'critical_numerical_error_rate':fp/(tp+fp) if tp+fp else None}


def select(pairs_by_id,probabilities_by_id,threshold):
    output={}
    for record_id,pairs in pairs_by_id.items():
        best={}
        for pair,probability in zip(pairs,probabilities_by_id[record_id]):
            if probability<threshold: continue
            key=(round(float(pair.left['value_m'])*20),round(float(pair.right['value_m'])*20))
            if key not in best or probability>best[key][2]: best[key]=(float(pair.left['value_m']),float(pair.right['value_m']),float(probability))
        output[record_id]=list(best.values())
    return output


def tune(pairs_by_id,probabilities_by_id,refs):
    best=None
    for threshold in [x/100 for x in range(5,100)]:
        chosen=select(pairs_by_id,probabilities_by_id,threshold); metric=pair_metrics(chosen,refs); boundary=boundary_metrics(chosen,refs)
        key=(metric['f1'],boundary['f1'],metric['precision'],-threshold)
        if best is None or key>best[0]: best=(key,threshold)
    return best[1]


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--analysis',type=Path,required=True); parser.add_argument('--manifest',type=Path,required=True); parser.add_argument('--output',type=Path,required=True); args=parser.parse_args()
    started=time.perf_counter(); analysis=json.loads(args.analysis.read_text()); sources={r['record_id']:r for r in map(json.loads,args.manifest.open())}; refs={k:references(v) for k,v in sources.items()}
    predictions={r['record_id']:r for r in analysis['predictions']}; pairs={k:make_pairs(v,refs[k]) for k,v in predictions.items()}; folds={k:int(v['fold']) for k,v in predictions.items()}
    oof={}; thresholds={}; models=[]
    for fold in sorted(set(folds.values())):
        train_ids=[k for k in pairs if folds[k]!=fold]; test_ids=[k for k in pairs if folds[k]==fold]
        train_pairs=[p for k in train_ids for p in pairs[k]]; ranker=LogisticPairRanker().fit(train_pairs)
        train_prob={k:ranker.predict(pairs[k]).tolist() for k in train_ids}; threshold=tune({k:pairs[k] for k in train_ids},train_prob,{k:refs[k] for k in train_ids})
        for k in test_ids: oof[k]=ranker.predict(pairs[k]).tolist(); thresholds[k]=threshold
        models.append({'fold':fold,'train_documents':len(train_ids),'test_documents':len(test_ids),'threshold':threshold,'ranker':ranker.to_dict()})
    selected={}
    for k in pairs: selected[k]=select({k:pairs[k]},{k:oof[k]},thresholds[k])[k]
    interval=pair_metrics(selected,refs); boundary=boundary_metrics(selected,refs)
    oracle_pairs=sum(sum(p.label for p in values)>0 for values in pairs.values())
    report={
      'analysis_scope':'BGS v001 source-disjoint pairwise interval reconstruction over v021 candidates','source_analysis':str(args.analysis),'source_analysis_sha256':hashlib.sha256(args.analysis.read_bytes()).hexdigest(),
      'manifest':str(args.manifest),'manifest_sha256':hashlib.sha256(args.manifest.read_bytes()).hexdigest(),'document_count':len(pairs),'candidate_pair_count':sum(map(len,pairs.values())),
      'positive_pair_count':sum(p.label for values in pairs.values() for p in values),'documents_with_positive_pair':oracle_pairs,
      'interval_at_0_05m':interval,'boundary_at_0_05m':boundary,'fold_models':models,'wall_time_seconds':time.perf_counter()-started,
      'predictions':[{'record_id':k,'fold':folds[k],'threshold':thresholds[k],'selected_intervals':[{'top_m':a,'bottom_m':b,'probability':p} for a,b,p in selected[k]]} for k in sorted(selected)],
      'reference_blinding':'outer-fold test references are used only for scoring; pair ranker and threshold use other source folds',
    }
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n'); print(json.dumps({k:report[k] for k in ('interval_at_0_05m','boundary_at_0_05m','candidate_pair_count','wall_time_seconds')},indent=2))


if __name__=='__main__': main()
