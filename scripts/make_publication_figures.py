#!/usr/bin/env python3
"""Generate CQG figures only from machine-readable released inputs.

Missing inputs skip the corresponding figure rather than inventing data.
Expected optional files under data/:
  rg_trajectory.npz: t, beta_norm, mu_A (and optional gap)
  matching_ledger.csv: channel,classification,metric
  bounce_transfer.npz: k, scalar_T11, tensor_T11, scalar_symplectic, tensor_symplectic
  mcmc_convergence.json: {parameter: Rminus1}
  heldout_chi2.json: {ACT_DR6: delta, fsigma8: delta, EG: delta, ...}
"""
from pathlib import Path
import csv,json
import numpy as np
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'; OUT=ROOT/'figures'; OUT.mkdir(exist_ok=True)

def save(fig,name):
    fig.tight_layout(); fig.savefig(OUT/name,bbox_inches='tight'); plt.close(fig); print('wrote',OUT/name)

# Pipeline schematic: no numerical claims.
fig,ax=plt.subplots(figsize=(10,2.5)); ax.axis('off')
labels=['UV FRG\nfixed point','695D\ntrajectory','Wilsonian\nthreshold','3-DOF\ncyclic EFT','bounce\ntransfer','CLASS +\nMCMC','held-out\ntests']
x=np.linspace(.05,.95,len(labels))
for i,(xx,l) in enumerate(zip(x,labels)):
    ax.text(xx,.5,l,ha='center',va='center',transform=ax.transAxes,bbox=dict(boxstyle='round,pad=.4',fc='white',ec='black'))
    if i<len(labels)-1: ax.annotate('',xy=(x[i+1]-.055,.5),xytext=(xx+.055,.5),xycoords=ax.transAxes,arrowprops=dict(arrowstyle='->'))
save(fig,'fig_pipeline.pdf')

p=DATA/'rg_trajectory.npz'
if p.exists():
    z=np.load(p); fig,ax=plt.subplots(figsize=(6.5,4.2)); ax.plot(z['t'],z['mu_A'],label=r'$\mu_A$'); ax.axhline(7,ls='--',label='matching threshold'); ax.set_xlabel(r'$t=\ln(k/k_0)$'); ax.set_ylabel(r'$\mu_A$'); ax.legend(); save(fig,'fig_rg_trajectory.pdf')

p=DATA/'matching_ledger.csv'
if p.exists():
    rows=list(csv.DictReader(p.open())); names=[r['channel'] for r in rows]; vals=[float(r['metric']) for r in rows]
    fig,ax=plt.subplots(figsize=(7.5,4.2)); ax.bar(names,vals); ax.axhline(1e-4,ls='--'); ax.set_yscale('log'); ax.set_ylabel('normalized magnitude'); ax.tick_params(axis='x',rotation=60); save(fig,'fig_matching_ledger.pdf')

p=DATA/'bounce_transfer.npz'
if p.exists():
    z=np.load(p); fig,ax=plt.subplots(figsize=(6.5,4.2)); ax.semilogx(z['k'],z['scalar_T11'],label='scalar $T_{11}$'); ax.semilogx(z['k'],z['tensor_T11'],label='tensor $T_{11}$'); ax.set_xlabel(r'$k\,[\mathrm{Mpc}^{-1}]$'); ax.set_ylabel('transfer amplitude'); ax.legend(); save(fig,'fig_bounce_transfer.pdf')

p=DATA/'mcmc_convergence.json'
if p.exists():
    d=json.loads(p.read_text()); names=list(d); vals=[d[k] for k in names]; fig,ax=plt.subplots(figsize=(7.5,4.2)); ax.bar(names,vals); ax.axhline(.01,ls='--'); ax.set_ylabel(r'$R-1$'); ax.tick_params(axis='x',rotation=60); save(fig,'fig_mcmc_convergence.pdf')

p=DATA/'heldout_chi2.json'
if p.exists():
    d=json.loads(p.read_text()); names=list(d); vals=[d[k] for k in names]; fig,ax=plt.subplots(figsize=(6.5,4.2)); ax.bar(names,vals); ax.axhline(0); ax.set_ylabel(r'$\Delta\chi^2=\chi^2_{cyc}-\chi^2_{\Lambda CDM}$'); save(fig,'fig_heldout_delta_chi2.pdf')
