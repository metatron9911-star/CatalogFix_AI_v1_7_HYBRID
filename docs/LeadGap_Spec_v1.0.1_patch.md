# LeadGap Spec v1.0.1 — Operational Patch

**Base:** LeadGap Spec v1.0  
**Status:** patch to canonical v1.0  
**Scope:** operational determinism, grounding, dedupe, evidence handling, and channel safety.  
**Unchanged:** ICP, segment definitions, scoring rubric, thresholds (75/70), priority formula, outreach templates.

---

## P1. evidence_date must be verifiable

`evidence_date` may only be populated from source evidence.

Allowed:
- an explicit ISO/calendar date published by the source → `evidence_date_precision = "exact"`;
- a relative timestamp such as “3 weeks ago”, computed from the run timestamp in UTC → `evidence_date_precision = "approximate"`.

Not allowed:
- inventing a date when the page exposes none;
- inferring a date from undated evergreen copy;
- treating a quarter label such as “Q3” as a usable date unless the source also exposes a year and a publication timestamp/date sufficient to place it inside the 90-day window.

If no defensible date can be derived, the candidate goes to reserve with:
`exclude_stage = "no_recent_evidence"`.

### Main schema delta

Required field:

```json
"evidence_date_precision": {
  "type": "string",
  "enum": ["exact", "approximate"]
}
```

All age calculations use the run timestamp in **UTC**.

---

## P2. personalization_hook must be grounded

Every named entity, product/platform name, client name, job title, and numeric claim in `personalization_hook` must be supported by the content retrieved from `evidence_url`.

Examples:
- source says “large catalog” → hook MUST NOT say “12k-SKU catalog”;
- source says “Shopify Plus” → hook must preserve “Shopify Plus”, not silently generalize or mutate the claim;
- source names a client → the same client name may be used;
- source does not name a client → hook must not invent one.

### Main schema delta

Required field:

```json
"hook_grounding": {
  "type": "array",
  "minItems": 1,
  "items": {
    "type": "object",
    "additionalProperties": false,
    "required": ["claim", "grounded_in"],
    "properties": {
      "claim": { "type": "string", "maxLength": 160 },
      "grounded_in": { "type": "string", "format": "uri" }
    }
  }
}
```

Validation:
1. Generate hook.
2. Validate each claim against fetched source content.
3. If any claim is unsupported, regenerate once.
4. If the second attempt still fails, send candidate to reserve with:
   - `exclude_stage = "manual_exclude"`
   - `exclude_reason = "hook grounding failed"`

No unsupported claim may enter main output.

---

## P3. Deterministic exclusion precedence

When multiple exclusion conditions are true, the **first matching stage** below is the final `exclude_stage`:

```text
1. pre_filter
2. no_decision_maker
3. no_recent_evidence
4. low_fit_score
5. low_evidence_score
6. language_mismatch
7. manual_exclude
```

### batch_manifest delta

Add:

```json
"exclusion_precedence_applied": [
  "pre_filter",
  "no_decision_maker",
  "no_recent_evidence",
  "low_fit_score",
  "low_evidence_score",
  "language_mismatch",
  "manual_exclude"
]
```

This makes exclusion histograms comparable across runs.

---

## P4. first_line similarity is Jaccard on normalized token sets

Fixed procedure:

```text
normalize: lowercase → strip punctuation → collapse whitespace
tokenize: split on whitespace
stopwords: remove frozen English stopword list bundled with LeadGap v1.0.1
compare: Jaccard similarity on token sets
threshold: > 0.60 → regenerate the later candidate's first_line
reference: compare against every accepted first_line already in the current batch
```

The stopword list must be versioned/frozen with the implementation so repeated runs on identical data are reproducible.

Pseudo-code:

```python
def first_line_ok(candidate, accepted_batch):
    toks = tokens(normalize(candidate.first_line))
    for other in accepted_batch:
        other_toks = tokens(normalize(other.first_line))
        if jaccard(toks, other_toks) > 0.60:
            return False
    return True
```

---

## P5. Company dedupe across segments

Canonical company key = **registrable root domain (eTLD+1)** using a Public Suffix List-aware parser.

Examples:
- `www.example.com` → `example.com`
- `shop.example.com` → `example.com`
- `agency.example.co.uk` → `example.co.uk`

Do **not** dedupe by naïvely taking the last two labels.

Rules:
- one root-domain company → one passed lead per batch;
- primary segment = segment with highest `fit_score`;
- tie-break segment priority:
  1. `shopify_commerce_agency`
  2. `pim_mdm_integrator`
  3. `pl_cee_de_smb_agency`
- non-primary matching segments are preserved as `secondary_segments`.

### Main schema delta

Optional field:

```json
"secondary_segments": {
  "type": "array",
  "items": {
    "type": "string",
    "enum": [
      "shopify_commerce_agency",
      "pim_mdm_integrator",
      "pl_cee_de_smb_agency"
    ]
  },
  "uniqueItems": true
}
```

---

## P6. email_confidence only comes from a verifier

`email_confidence` must never be model-generated or inferred from page presence.

Allowed sources:
- Hunter
- Clearbit
- Dropcontact
- NeverBounce
- another explicit verifier that returns a verification/confidence result

### Main schema delta

Optional field:

```json
"email_source": {
  "type": ["string", "null"],
  "enum": [
    "hunter",
    "clearbit",
    "dropcontact",
    "neverbounce",
    "other_verifier",
    null
  ]
}
```

Rules:
- if `email_source != null` AND source-reported `email_confidence >= 0.8` → email channel may be used;
- otherwise set `work_email = null`, `email_confidence = null`, and use LinkedIn DM or site form;
- a contact-page email alone does not qualify as verified confidence.

---

## P7. source_mix counts primary discovery source only

### Main schema delta

Required field:

```json
"primary_discovery_source": {
  "type": "string",
  "enum": [
    "linkedin",
    "clutch",
    "shopify_partners",
    "apify_store",
    "google",
    "referral",
    "other"
  ]
}
```

Definition:
- primary discovery source = the source where the company was first identified for this run;
- evidence sources remain in `source_urls`;
- each passed lead contributes exactly **one** count to `source_mix`.

Invariant:

```text
sum(source_mix.values()) == totals.passed_thresholds
```

---

## P8. Reserve stores evidence type + URL

### Reserve schema delta

Add nullable fields:

```json
"evidence_type": {
  "type": ["string", "null"],
  "enum": [
    "case_study",
    "job_posting",
    "linkedin_post",
    "press",
    "partner_page",
    "client_logo",
    null
  ]
},
"evidence_url": {
  "type": ["string", "null"],
  "format": "uri"
}
```

This distinguishes:
- evidence not found;
- evidence found but undated;
- evidence found but too old;
- weak evidence such as client-logo only.

---

## P9. No >90-day exception in wave 1

For the first wave:

```text
evidence_age_days <= 90 → eligible
evidence_age_days > 90  → reserve
unknown date             → reserve
```

No manual override for “still relevant” evidence in wave 1.

---

## Global date rule

All date arithmetic uses the **run timestamp in UTC**.

This includes:
- “3 weeks ago” conversion;
- 90-day evidence cutoff;
- day-90/day-91 boundary behavior.

The run timestamp used for calculations must be written to the manifest.

Recommended manifest field:

```json
"run_timestamp_utc": "2026-09-22T00:00:00Z"
```

---

## Deterministic priority tiebreaker

Primary sort:

```text
priority_score DESC
```

When `priority_score` is equal:

```text
1. evidence_score DESC
2. fit_score DESC
3. company_name ASC
```

This guarantees stable ordering for repeated runs on identical inputs.

---

## Schema delta summary

### main — add to required

```text
evidence_date_precision
hook_grounding
primary_discovery_source
```

### main — add optional

```text
secondary_segments
email_source
```

### reserve — add nullable

```text
evidence_type
evidence_url
```

---

## DoD v1.0.1

- [ ] Main schema contains required `evidence_date_precision`, `hook_grounding`, `primary_discovery_source`.
- [ ] Main schema contains optional `secondary_segments`, `email_source`.
- [ ] Reserve schema contains nullable `evidence_type`, `evidence_url`.
- [ ] Exclusion precedence is emitted in `batch_manifest.json` as `exclusion_precedence_applied`.
- [ ] `first_line` similarity uses Jaccard on normalized token sets with a frozen stopword list.
- [ ] Dedupe uses PSL-aware eTLD+1/root-domain normalization before main output.
- [ ] `email_confidence` is accepted only from an explicit verifier source.
- [ ] `primary_discovery_source` exists for every passed lead.
- [ ] Reserve retains evidence type/URL even when date is unavailable.
- [ ] All date computations use UTC and manifest records `run_timestamp_utc`.
- [ ] Priority ordering uses deterministic tie-break rules.

---

## Rollout

1. Commit this patch next to v1.0.
2. Apply schema deltas and operational rules to LeadGap code.
3. Run 12-candidate research batch (4 + 4 + 4).
4. Inspect precedence-aware histogram, email coverage, and source mix.
5. If one exclusion stage dominates, calibrate inputs/sources and publish v1.1; otherwise keep v1.0.1 as working baseline.
