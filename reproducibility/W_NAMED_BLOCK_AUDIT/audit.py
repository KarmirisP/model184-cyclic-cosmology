#!/usr/bin/env python3

from pathlib import Path
import hashlib
import json
import runpy
import sys
import numpy as np

AUTH = Path(
    "/home/unbinder/mcv2_theory_runs/cyclic_program/"
    "CYCLIC_SOURCE_EXACT_MERGER_REPAIR_20260924T195600"
)

REPO = Path(
    "/home/unbinder/projects/model184-cyclic-cosmology"
)

OUT = REPO / "reproducibility" / "W_NAMED_BLOCK_AUDIT"

STEP2 = AUTH / "run_step2_vector_integration.py"
CAND = AUTH / "CANDIDATE_MATCHING_STATES.npz"
VEC = AUTH / "VECTOR_INTEGRATION_MATCHING.npz"
FULLP = AUTH / "FULL_VECTOR_THRESHOLD_VS_P.npz"
METRIC = AUTH / "CANONICAL_PHYSICAL_MATCHING_METRIC.json"

# Source grid is 8 x 16.
NY = 8
NQ = 16

STRICT = 1.0e-4
IDENTITY_TOL = 1.0e-12


def progress(stage, **kw):
    rest = " ".join(
        f"{k}={v}" for k, v in kw.items()
    )
    print(
        f"[W-NAMED-BLOCK] stage={stage} {rest}",
        flush=True
    )


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(
            lambda: f.read(1024 * 1024),
            b""
        ):
            h.update(b)
    return h.hexdigest()


def load_npz(p):
    with np.load(p, allow_pickle=True) as z:
        return {
            k: np.asarray(z[k])
            for k in z.files
        }


for p in (STEP2, CAND, VEC, FULLP, METRIC):
    if not p.exists():
        raise SystemExit(
            f"FATAL missing authority: {p}"
        )


# ------------------------------------------------------------
# 1. Check that importing STEP2 will not invoke main().
# ------------------------------------------------------------

source = STEP2.read_text(errors="replace")

if 'if __name__ == "__main__"' not in source \
and "if __name__ == '__main__'" not in source:
    raise SystemExit(
        "FATAL: STEP2 has no __main__ guard; "
        "refusing runpy import."
    )


progress("load_source_namespace")

# Executes imports/definitions only; main() is not entered because
# run_name != "__main__".
ns = runpy.run_path(
    str(STEP2),
    run_name="__MODEL184_W_AUDIT__"
)


# ------------------------------------------------------------
# 2. Locate the exact system objects used by STEP2.
# ------------------------------------------------------------

uv_system = ns.get("uv_system")
eft_system = ns.get("eft_system")

if uv_system is None:
    candidates = [
        v for v in ns.values()
        if hasattr(v, "unpack_state")
    ]

    if not candidates:
        raise SystemExit(
            "FATAL: could not recover uv_system/unpack_state"
        )

    uv_system = candidates[0]

if eft_system is None:
    candidates = [
        v for v in ns.values()
        if hasattr(v, "unpack_state")
        and hasattr(v, "pack_state")
    ]

    if not candidates:
        raise SystemExit(
            "FATAL: could not recover eft_system"
        )

    # Usually the same callable engine is used for both.
    eft_system = candidates[-1]


print(
    "uv_system =",
    getattr(
        uv_system,
        "__file__",
        repr(uv_system)
    )
)

print(
    "eft_system =",
    getattr(
        eft_system,
        "__file__",
        repr(eft_system)
    )
)


# ------------------------------------------------------------
# 3. Load EXACT objects used by STEP2 at M=7.
# ------------------------------------------------------------


# ------------------------------------------------------------
# Materialize system classes recovered by runpy.
#
# runpy may expose the class definitions rather than constructed
# objects. unpack_state()/pack_state() are instance methods, so using
# the class directly shifts all positional arguments by one.
#
# First prefer any existing instance already created in the imported
# namespace. If none exists, create a raw instance with __new__.
# These state packing methods are structural and should not require
# the dynamical constructor state.
# ------------------------------------------------------------

def materialize_system(obj, label):

    if not isinstance(obj, type):
        print(
            f"{label}: existing instance "
            f"{type(obj).__module__}.{type(obj).__name__}"
        )
        return obj

    # Prefer a genuine instance already present in the runpy namespace.
    for name, candidate in ns.items():

        if isinstance(candidate, type):
            continue

        try:
            if isinstance(candidate, obj):
                print(
                    f"{label}: using namespace instance "
                    f"{name} -> "
                    f"{type(candidate).__module__}."
                    f"{type(candidate).__name__}"
                )
                return candidate
        except Exception:
            pass

    # State pack/unpack routines are structural.  Construct without
    # invoking a potentially argument-heavy dynamical __init__.
    instance = obj.__new__(obj)

    print(
        f"{label}: materialized raw instance "
        f"{obj.__module__}.{obj.__name__}"
    )

    return instance


uv_system = materialize_system(
    uv_system,
    "uv_system"
)

eft_system = materialize_system(
    eft_system,
    "eft_system"
)


progress("load_frozen_states")

cand = load_npz(CAND)
vec = load_npz(VEC)

for k in (
    "x_M7",
):
    if k not in cand:
        raise SystemExit(
            f"FATAL: {k} missing from candidate authority"
        )

for k in (
    "x_eft_M_7",
    "M_7_delta_W",
):
    if k not in vec:
        raise SystemExit(
            f"FATAL: {k} missing from vector authority. "
            f"Available={sorted(vec)}"
        )

x_uv = np.asarray(
    cand["x_M7"],
    dtype=float
)

x_eft = np.asarray(
    vec["x_eft_M_7"],
    dtype=float
)

delta_W_stored = np.asarray(
    vec["M_7_delta_W"],
    dtype=float
)

print(
    "x_uv.shape =",
    x_uv.shape
)

print(
    "x_eft.shape =",
    x_eft.shape
)

print(
    "delta_W.shape =",
    delta_W_stored.shape
)


# ------------------------------------------------------------
# 4. Unpack by SEMANTIC FIELD NAME.
#
# This is the key audit.
# No numerical slice is assumed.
# ------------------------------------------------------------

progress("unpack_named_blocks")

b_uv = uv_system.unpack_state(
    x_uv,
    NQ,
    NY
)

b_eft = eft_system.unpack_state(
    x_eft,
    NQ,
    NY
)

if "W" not in b_uv:
    raise SystemExit(
        f"FATAL: UV unpack has no W. keys={list(b_uv)}"
    )

if "W" not in b_eft:
    raise SystemExit(
        f"FATAL: EFT unpack has no W. keys={list(b_eft)}"
    )

W_uv = np.asarray(
    b_uv["W"],
    dtype=float
)

W_eft = np.asarray(
    b_eft["W"],
    dtype=float
)

print(
    "W_uv.shape =",
    W_uv.shape
)

print(
    "W_eft.shape =",
    W_eft.shape
)

if W_uv.shape != delta_W_stored.shape:
    raise SystemExit(
        "FATAL: W_uv shape differs from stored delta_W: "
        f"{W_uv.shape} vs {delta_W_stored.shape}"
    )

if W_eft.shape != delta_W_stored.shape:
    raise SystemExit(
        "FATAL: W_eft shape differs from stored delta_W: "
        f"{W_eft.shape} vs {delta_W_stored.shape}"
    )


# ------------------------------------------------------------
# 5. Definitive coefficient identity
#
# W_EFT - W_UV = delta_W
# ------------------------------------------------------------

progress("test_W_identity")

delta_W_from_states = (
    W_eft - W_uv
)

identity_difference = (
    delta_W_from_states
    - delta_W_stored
)

identity_abs_max = float(
    np.max(
        np.abs(
            identity_difference
        )
    )
)

identity_l2 = float(
    np.linalg.norm(
        identity_difference
    )
)

delta_abs_max = float(
    np.max(
        np.abs(
            delta_W_stored
        )
    )
)

W_uv_max = float(
    np.max(
        np.abs(
            W_uv
        )
    )
)

W_eft_max = float(
    np.max(
        np.abs(
            W_eft
        )
    )
)

# Useful diagnostics for identifying how the historical R_W
# normalization was formed.
R_global = (
    delta_abs_max
    / max(
        W_uv_max,
        1e-300
    )
)

R_pointwise = float(
    np.max(
        np.abs(
            delta_W_stored
        )
        / np.maximum(
            np.abs(W_uv),
            1e-300
        )
    )
)


# ------------------------------------------------------------
# 6. Prove W positions using pack_state itself.
#
# This is only for documentation. It is NOT needed for the
# named-block identity above.
# ------------------------------------------------------------

progress("derive_W_indices_from_packer")

marker = {}

for key, value in b_eft.items():
    a = np.asarray(value)

    if np.issubdtype(
        a.dtype,
        np.number
    ):
        marker[key] = np.zeros_like(
            a,
            dtype=float
        )
    else:
        marker[key] = value

marker["W"] = np.ones_like(
    W_eft,
    dtype=float
)

try:
    packed_marker = np.asarray(
        eft_system.pack_state(marker),
        dtype=float
    )
except TypeError:
    packed_marker = np.asarray(
        eft_system.pack_state(
            marker,
            include_bridge=False
        ),
        dtype=float
    )

W_indices = np.where(
    np.abs(
        packed_marker
    ) > 0.5
)[0]

contiguous = bool(
    len(W_indices) == delta_W_stored.size
    and np.all(
        np.diff(W_indices) == 1
    )
)

if len(W_indices):
    W_slice = [
        int(W_indices[0]),
        int(W_indices[-1] + 1)
    ]
else:
    W_slice = None

print(
    "semantic W indices =",
    W_slice
)

print(
    "semantic W index count =",
    len(W_indices)
)

print(
    "semantic W contiguous =",
    contiguous
)


# ------------------------------------------------------------
# 7. Raw exact vs p^8-reconstructed threshold remainder
# ------------------------------------------------------------

progress("raw_momentum_remainder")

fp = load_npz(FULLP)

inv_exact = np.asarray(
    fp["inv_prop_exact"],
    dtype=float
)

inv_recon = np.asarray(
    fp["inv_prop_recon"],
    dtype=float
)

R_inv = float(
    np.max(
        np.abs(
            inv_exact - inv_recon
        )
        / np.maximum(
            1.0,
            np.abs(inv_exact)
        )
    )
)

tree_exact = np.asarray(
    fp["tree_exchange_exact"],
    dtype=float
)

tree_recon = np.asarray(
    fp["tree_exchange_recon"],
    dtype=float
)

R_tree = float(
    np.max(
        np.abs(
            tree_exact - tree_recon
        )
        / np.maximum(
            1.0,
            np.abs(tree_exact)
        )
    )
)


# ------------------------------------------------------------
# 8. Historical reported R_W for diagnostic comparison only.
#
# It is NEVER used to construct either W state.
# ------------------------------------------------------------

metric = json.loads(
    METRIC.read_text()
)

decl = metric.get(
    "declared_channels",
    metric
)

reported_R_W = (
    float(decl["R_W"])
    if "R_W" in decl
    else None
)


# ------------------------------------------------------------
# 9. Circularity test
# ------------------------------------------------------------

forbidden = (
    "STRICT_RMATCH_VERDICT",
    "matching_ledger.csv",
    "w_matching_audit.json",
    "W_STATE_TRANSITION_VERDICT",
    "W_FINAL_NONCIRCULAR_VERDICT",
)

circular = [
    x for x in forbidden
    if x in source
]

no_circular = (
    len(circular) == 0
)


# ------------------------------------------------------------
# 10. Verdict
# ------------------------------------------------------------

coefficient_identity_pass = (
    identity_abs_max
    < IDENTITY_TOL
)

remainder_pass = (
    R_inv < STRICT
    and R_tree < STRICT
)

packer_proven = (
    contiguous
    and len(W_indices)
    == delta_W_stored.size
)

PASS = (
    coefficient_identity_pass
    and remainder_pass
    and packer_proven
    and no_circular
)

if PASS:
    verdict = (
        "W_MATCHING_DEFINITIVE_NONCIRCULAR_PASS"
    )
else:
    verdict = (
        "W_MATCHING_DEFINITIVE_NONCIRCULAR_FAIL"
    )


result = {
    "audit":
        "MODEL184_DEFINITIVE_NAMED_W_BLOCK_AUDIT",

    "verdict":
        verdict,

    "PASS":
        PASS,

    "classification":
        (
            "RETAINED_WILSON_COEFFICIENT_SHIFT"
            if PASS
            else "NOT_CLOSED"
        ),

    "source_grid": {
        "NY": NY,
        "NQ": NQ,
    },

    "dimensions": {
        "UV": int(
            x_uv.size
        ),
        "EFT": int(
            x_eft.size
        ),
    },

    "semantic_W_slice":
        W_slice,

    "semantic_W_count":
        int(
            len(W_indices)
        ),

    "W_shapes": {
        "UV":
            list(W_uv.shape),
        "EFT":
            list(W_eft.shape),
        "delta":
            list(
                delta_W_stored.shape
            ),
    },

    "coefficient_identity": {
        "max_abs":
            identity_abs_max,

        "L2":
            identity_l2,

        "tolerance":
            IDENTITY_TOL,

        "PASS":
            coefficient_identity_pass,
    },

    "coefficient_shift": {
        "delta_W_maxabs":
            delta_abs_max,

        "W_uv_maxabs":
            W_uv_max,

        "W_eft_maxabs":
            W_eft_max,

        "relative_global":
            R_global,

        "relative_pointwise_max":
            R_pointwise,

        "historical_reported_R_W":
            reported_R_W,
    },

    "raw_p8_remainder": {
        "inverse_propagator":
            R_inv,

        "tree_exchange":
            R_tree,

        "strict_threshold":
            STRICT,

        "PASS":
            remainder_pass,
    },

    "packer_proven":
        packer_proven,

    "no_circular_dependencies":
        no_circular,

    "circular_dependencies":
        circular,

    "authority_hashes": {
        STEP2.name:
            sha256(STEP2),

        CAND.name:
            sha256(CAND),

        VEC.name:
            sha256(VEC),

        FULLP.name:
            sha256(FULLP),

        METRIC.name:
            sha256(METRIC),
    },
}


OUT.mkdir(
    parents=True,
    exist_ok=True
)

json_path = (
    OUT
    / "W_DEFINITIVE_NONCIRCULAR_VERDICT.json"
)

json_path.write_text(
    json.dumps(
        result,
        indent=2
    )
)


# Public compact authority
public_path = (
    REPO
    / "data"
    / "w_definitive_matching_audit.json"
)

public_path.write_text(
    json.dumps(
        result,
        indent=2
    )
)


print()
print(
    "============================================================"
)

print(verdict)

print(
    "============================================================"
)

print(
    "W_EFT_minus_W_UV_equals_delta_W_maxabs="
    f"{identity_abs_max:.16e}"
)

print(
    "identity_tolerance="
    f"{IDENTITY_TOL:.16e}"
)

print(
    "semantic_W_slice="
    f"{W_slice}"
)

print(
    "delta_W_maxabs="
    f"{delta_abs_max:.16e}"
)

print(
    "R_W_relative_global="
    f"{R_global:.16e}"
)

print(
    "R_W_relative_pointwise_max="
    f"{R_pointwise:.16e}"
)

print(
    "historical_reported_R_W="
    f"{reported_R_W}"
)

print(
    "raw_p8_inverse_prop_remainder="
    f"{R_inv:.16e}"
)

print(
    "raw_p8_tree_remainder="
    f"{R_tree:.16e}"
)

print(
    "strict_threshold="
    f"{STRICT:.16e}"
)

print(
    "packer_proven="
    f"{packer_proven}"
)

print(
    "no_circular_dependencies="
    f"{no_circular}"
)

print(
    f"JSON={json_path}"
)


if not PASS:
    sys.exit(2)

