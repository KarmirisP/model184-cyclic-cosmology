#!/usr/bin/env python3
"""Deterministic cross-machine S8 reconciliation for MODEL184.

Generate a manifest once from the final DAWN chains, copy the manifest and
identical raw chains to ASUS, and run again with --manifest.  The publication
value is accepted only from sample-by-sample parity, not from two independently
thinned subsets.
"""
from __future__ import annotations
import argparse, csv, glob, hashlib, json, os, sys
from pathlib import Path
import numpy as np

FIXED_SUM_S3S4 = 2.2352893378
OMEGA_R_H2 = 2.47e-5 * (1.0 + 0.2271 * 3.044)

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20), b''): h.update(chunk)
    return h.hexdigest()

def load_chains(pattern: str, burn: float):
    files=[Path(x) for x in sorted(glob.glob(pattern))]
    if not files: raise SystemExit(f'No chains match {pattern!r}')
    arrays=[]; header=None; provenance=[]
    for ci,p in enumerate(files):
        with p.open() as f:
            hdr=f.readline().strip().lstrip('#').split()
        if header is None: header=hdr
        if hdr != header: raise SystemExit(f'Header mismatch: {p}')
        a=np.loadtxt(p)
        cut=int(len(a)*burn)
        for ri,row in enumerate(a[cut:], start=cut): provenance.append((ci,ri,row))
        arrays.append(a)
    return files, header, provenance

def write_manifest(path: Path, files, header, provenance, n, seed):
    weights=np.array([x[2][0] for x in provenance],float)
    if np.any(weights < 0) or weights.sum() <= 0: raise SystemExit('Invalid Cobaya weights')
    rng=np.random.default_rng(seed)
    idx=rng.choice(len(provenance), size=n, replace=False, p=weights/weights.sum())
    with path.open('w',newline='') as f:
        w=csv.writer(f); w.writerow(['sample_id','chain_file','chain_sha256','row_index'])
        for sid,j in enumerate(idx):
            ci,ri,_=provenance[j]; p=files[ci]
            w.writerow([sid,p.name,sha256(p),ri])
    return idx

def read_manifest(path: Path, files, header):
    byname={p.name:p for p in files}; out=[]
    with path.open() as f:
        for r in csv.DictReader(f):
            p=byname.get(r['chain_file'])
            if p is None: raise SystemExit(f"Manifest chain absent: {r['chain_file']}")
            if sha256(p) != r['chain_sha256']: raise SystemExit(f'Hash mismatch: {p}')
            a=np.loadtxt(p)
            out.append((int(r['sample_id']), a[int(r['row_index'])]))
    return sorted(out)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--chains', required=True, help='glob, e.g. /path/bounce_bound_shoes.[1-4].txt')
    ap.add_argument('--class-python', required=True, help='directory containing classy module')
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--generate-manifest', action='store_true')
    ap.add_argument('--burn', type=float, default=0.30)
    ap.add_argument('--n', type=int, default=500)
    ap.add_argument('--seed', type=int, default=20260925)
    ap.add_argument('--out', default='S8_RECONCILIATION.json')
    ap.add_argument('--archived-npz')
    args=ap.parse_args()

    files,header,prov=load_chains(args.chains,args.burn)
    col={k:i for i,k in enumerate(header)}
    required=['H0','omega_b','omega_aest','vcdm_s4','n_s','A_s','tau_reio']
    miss=[k for k in required if k not in col]
    if miss: raise SystemExit(f'Missing columns: {miss}')
    manifest=Path(args.manifest)
    if args.generate_manifest:
        write_manifest(manifest,files,header,prov,args.n,args.seed)
    samples=read_manifest(manifest,files,header)

    sys.path.insert(0,args.class_python)
    from classy import Class
    rows=[]
    for j,(sid,row) in enumerate(samples,1):
        H0=float(row[col['H0']]); ob=float(row[col['omega_b']]); oa=float(row[col['omega_aest']]); s4=float(row[col['vcdm_s4']])
        h=H0/100.0
        Ov=1.0-(ob+oa+OMEGA_R_H2)/(h*h)
        pars={
            'output':'mPk','P_k_max_1/Mpc':5.0,'gauge':'newtonian',
            'H0':H0,'omega_b':ob,'omega_cdm':0.0,'Omega_Lambda':0.0,'Omega_fld':0.0,
            'omega_aest':oa,'vcdm_s4':s4,'vcdm_s3':FIXED_SUM_S3S4-s4,'Omega_vcdm_native':Ov,
            'vcdm_order':4.0,'vcdm_s1':4.3390577901,'vcdm_s2':-5.5743471279,
            'aest_KB':0.5,'aest_K2':7500.0,'aest_Q0':0.1,'aest_Z0':1e-9,
            'aest_x0':0.02672752,'aest_I0':4.009128e-7,
            'vcdm_has_turnaround':'yes','vcdm_kappa_turn':2.4643768482595156,
            'vcdm_has_bounce':'yes','vcdm_rho_bounce':0.0,'aest_lambda_cyc':0.0,
            'vcdm_a_min':1.0741318482258137e-13,'a_ini_over_a_today_default':1.09561448519033e-13,
            'n_s':float(row[col['n_s']]),'A_s':float(row[col['A_s']]),'tau_reio':float(row[col['tau_reio']])}
        c=Class(); c.set(pars); c.compute()
        sig8=float(c.sigma8()); Om=float(c.Omega0_m()); S8=sig8*np.sqrt(Om/0.3)
        rows.append({'sample_id':sid,'sigma8':sig8,'Omega0_m':Om,'S8':S8})
        c.struct_cleanup(); c.empty()
        if j==1 or j%25==0 or j==len(samples):
            print(f'[S8-RECON] sample={j}/{len(samples)} S8={S8:.9f}',flush=True)
    s=np.array([r['S8'] for r in rows])
    result={'manifest_sha256':sha256(manifest),'N':len(rows),'S8_mean':float(s.mean()),'S8_std':float(s.std(ddof=1)),
            'S8_sem':float(s.std(ddof=1)/np.sqrt(len(s))),'samples':rows,
            'chain_hashes':{p.name:sha256(p) for p in files}}
    if args.archived_npz:
        z=np.load(args.archived_npz)
        result['archived']={k:float(z[k]) for k in ('S8_mean','S8_std') if k in z.files}
    Path(args.out).write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!='samples'},indent=2))

if __name__=='__main__': main()
