#!/usr/bin/env python3
"""Adjudicate a strict Wilsonian matching ledger from raw exported channel values.

Input CSV columns:
channel,classification,full_value,eft_matched_value,normalization,raw_shift
classification must be one of:
WILSON_COEFFICIENT_SHIFT, REPRESENTED_POST_MATCH_RESIDUAL,
UNREPRESENTED_TRUNCATION_REMAINDER.

The script NEVER changes the threshold and never infers a class from magnitude.
"""
import argparse,csv,json,math
from pathlib import Path
VALID={'WILSON_COEFFICIENT_SHIFT','REPRESENTED_POST_MATCH_RESIDUAL','UNREPRESENTED_TRUNCATION_REMAINDER'}

def f(x):
    x=(x or '').strip(); return None if x=='' else float(x)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('csv'); ap.add_argument('--threshold',type=float,default=1e-4); ap.add_argument('--out',default='STRICT_RMATCH_VERDICT.json')
    a=ap.parse_args(); rows=[]; errors=[]
    with open(a.csv) as fh:
        for r in csv.DictReader(fh):
            c=r['classification'].strip()
            if c not in VALID: raise SystemExit(f"Bad classification {c!r} for {r['channel']}")
            full,eft,norm,shift=map(f,(r.get('full_value'),r.get('eft_matched_value'),r.get('normalization'),r.get('raw_shift')))
            if c=='WILSON_COEFFICIENT_SHIFT':
                metric=abs(shift) if shift is not None else None
            else:
                if full is None or eft is None or norm is None or norm<=0: raise SystemExit(f"Raw values required for error class: {r['channel']}")
                metric=abs(full-eft)/norm; errors.append(metric)
            rows.append({'channel':r['channel'],'classification':c,'raw_shift':shift,'metric':metric,'full':full,'eft_matched':eft,'normalization':norm})
    if not errors: raise SystemExit('No post-match/truncation error rows supplied')
    R=max(errors); w=[r for r in rows if r['channel'].strip().upper()=='W']
    out={'STRICT_THRESHOLD':a.threshold,'R_MATCH_ERROR':R,'CANONICAL_WILSONIAN_HANDOFF_PASS_STRICT':bool(R<a.threshold),
         'R_W_CLASSIFICATION':w[0]['classification'] if w else 'MISSING','rows':rows}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
if __name__=='__main__': main()
