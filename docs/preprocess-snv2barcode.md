# Step 1 (Preprocessing): SNV-to-Barcode Matrix Construction

`prismsnv snv2barcode` converts sample-level SNV evidence into barcode×SNV `AnnData` matrices and produces a merged matrix for training.

## 1. Run Command

```bash
prismsnv snv2barcode /path/to/snv2barcode_config.yaml
```

---

## 2. Configuration Template

```yaml
settings:
  output_dir: /path/to/output
  percentage: 20
  threads: 16
  data_type: sc               # sc / spatial
  count_unit: reads           # reads / umis
  p_alt_if_variant: 0.5
  alt_error_rate: 0.001
  default_prior: 0.001
  prior_scale: 2.0
  prior_cap: 0.95
  estimate_p_per_sample: false
  neg1_prob_threshold:
  af_filter_enabled: false
  af_field: gnomad41_genome_AF
  af_max: 0.001

samples:
  sample01:
    bam: /path/to/sample01.bam
    vcf: /path/to/sample01.vcf
    cb: /path/to/sample01_cb.csv
    # Required if af_filter_enabled=true:
    # annotated_vcf: /path/to/sample01.annotated.vcf

file_paths:
  snv_union: auto
```

---

## 3. `settings` Reference

If you do not have a specific reason to tune these parameters, it is recommended to keep the default settings unchanged.

### 3.1 Core Runtime Parameters

| Parameter | Default | Description |
|---|---|---|
| `output_dir` | required | Output root directory |
| `percentage` | required; example: 20 | Keep ALT alleles with sample frequency strictly below this percentage (20 means 20%) |
| `threads` | required | Positive integer parallel worker count |
| `data_type` | required; example: `sc` | `sc` or `spatial` |
| `count_unit` | `reads` | `reads` or `umis` |

If `percentage <= 0`, VCF records are copied without AF filtering.

For positive thresholds, frequency is read from the **first sample column** of
each sample-level VCF: per-ALT FORMAT `FREQ` (percentage) takes precedence, with
FORMAT `AD/DP` as fallback. Standard `AD` is REF followed by each ALT count;
scalar `AD` is accepted for a single VarScan ALT. INFO `AF` is not used for this
sample-frequency filter. Missing or unparseable frequencies are excluded.

For multiallelic records, the intermediate VCF retains the complete record if
any ALT passes; automatic union construction then splits the ALT alleles and
applies the threshold to each allele independently. Population AF filtering
below is a separate operation using the configured INFO field.

### 3.2 Pileup Quality Filters

| Parameter | Default | Description |
|---|---|---|
| `pileup_base_quality_min` | 20 | Excludes bases below this quality |
| `pileup_mapping_quality_min` | 20 | Excludes reads below this mapping quality |

### 3.3 Posterior Modeling Parameters

| Parameter | Default | Description |
|---|---|---|
| `p_alt_if_variant` | 0.5 | Probability of observing ALT if truly variant |
| `alt_error_rate` | 0.001 | Probability of ALT observation in true REF background |
| `default_prior` | 0.001 | Lower bound for variant prior |
| `prior_scale` | 2.0 | Prior scaling factor from sample frequency |
| `prior_cap` | 0.95 | Upper bound for variant prior |
| `neg1_prob_threshold` | `None` | Optional threshold to keep/drop `-1` entries |

### 3.4 Optional Per-sample Estimation of `p_alt_if_variant`

| Parameter | Default | Description |
|---|---|---|
| `estimate_p_per_sample` | `false` | Enable per-sample estimation |
| `p_estimation_min_alt_count` | 2 | Minimum ALT count for candidate observations |
| `p_estimation_min_total_count` | 2 | Minimum total count for candidate observations |
| `p_estimation_min_observations` | 25 | Minimum observations required to estimate |
| `p_estimation_min_snvs` | 5 | Minimum SNVs required to estimate |

### 3.5 Optional Population AF Filtering

| Parameter | Default | Description |
|---|---|---|
| `af_filter_enabled` | `false` | Enable AF-based post-filtering on `.h5ad` |
| `af_field` | `gnomad41_genome_AF` | INFO field to read from annotated VCF |
| `af_max` | 0.001 | Remove SNVs with AF above this value |
| `af_strict_snv_format` | `false` | Strict format check for SNV IDs |

---

## 4. `samples` and `file_paths`

### 4.1 `samples`

Each sample must provide:

- `bam`
- `vcf`
- `cb`

If `af_filter_enabled: true`, each sample must also provide:

- `annotated_vcf`

### 4.2 `file_paths.snv_union`

- `auto`: build `SNV_union.tsv` from filtered per-sample VCF files.
- custom path: use external SNV union file (frequency annotations may be missing).

The union is a headerless, tab-delimited file with four columns: chromosome,
1-based position, REF, and a single ALT per row. A custom union defines the
sites directly; it bypasses automatic per-ALT union selection.

---

## 5. Barcode Input Formats

### 5.1 Single-cell (`data_type: sc`)

- Headerless, one-column barcode file.

### 5.2 Spatial (`data_type: spatial`)

- Headerless CSV with six columns: `barcode, in_tissue, x, y, px, py`
- Only rows with `in_tissue == 1` are used.

---

## 6. Internal Processing Stages

1. Filter per-sample VCF records by `percentage`.
2. Build or load `SNV_union.tsv`.
3. Perform parallel pileup and extract ALT/REF-supporting barcodes and counts.
4. Build sparse `AnnData`:
   - `adata.X`: `1` (ALT), `-1` (retained REF evidence), `0` (no retained evidence)
   - `layers`: `alt_count`, `ref_count`, `ref_posterior`
5. Optionally run population AF filtering (`af_filter_enabled`).
6. Merge all samples into `all_samples_merged_barcode_snv_matrix.h5ad`.

Additional behavior:

- Loci with pileup depth `> 50000` are skipped.
- ALT/REF counts support either read-level or UMI-level aggregation.
- During merge, barcode IDs become `<sample_name>_<barcode>` and `obs["sample"]` stores the sample name. RNA AnnData cell IDs must match these IDs for downstream alignment.

---

## 7. Main Outputs

Per-sample directory:

- `{sample}_reads_supporting_snvs.txt`
- `{sample}_reads_supporting_ref.txt`
- `{sample}_alt_counts.txt`
- `{sample}_ref_counts.txt`
- `{sample}_barcode_snv_binary_matrix.h5ad`
- `{sample}_neg1_ref_posterior_hist.png`
- `{sample}_neg1_ref_posterior_summary.tsv`

Optional per-sample AF-filtered outputs:

- `{sample}_barcode_snv_binary_matrix_af_filtered.h5ad`
- `{sample}_barcode_snv_binary_matrix_af_filtered.af_filter_summary.tsv`
- `{sample}_barcode_snv_binary_matrix_af_filtered.af_filter_details.tsv`

Global outputs:

- `SNV_union.tsv`
- `all_samples_merged_barcode_snv_matrix.h5ad`
- `all_samples_neg1_ref_posterior_hist.png`
- `all_samples_neg1_ref_posterior_summary.tsv`

Optional global AF-filtered output:

- `all_samples_merged_barcode_snv_matrix_af_filtered.h5ad`

The ordinary merged matrix remains unfiltered by population AF. To train on
the population-filtered matrix, explicitly set `snv_eff.adata_snv` to
`all_samples_merged_barcode_snv_matrix_af_filtered.h5ad`.

---

## 8. Matrix Semantics

In per-sample and merged matrices:

- `adata.X`
  - `1`: ALT-supporting evidence present
  - `-1`: REF-only evidence retained after posterior criteria
  - `0`: no retained evidence
- `adata.layers["alt_count"]`: ALT counts
- `adata.layers["ref_count"]`: REF counts
- `adata.layers["ref_posterior"]`: posterior probability of REF interpretation

---

## 9. Common Errors and Debugging

### 9.1 Missing Files

The script validates required files up front and raises `FileNotFoundError` with details.

### 9.2 Invalid Parameters

Validation includes:

- `count_unit` must be `reads` or `umis`
- `p_alt_if_variant`, `alt_error_rate`, `default_prior`, `prior_cap` must be in `(0, 1)`
- `af_max` must be non-negative
- `neg1_prob_threshold` (if set) must be in `[0, 1]`

### 9.3 Missing AF Field in Annotated VCF

If `af_filter_enabled=true` and `af_field` is absent in VCF INFO, a `KeyError` is raised.

Recommendation: validate with one sample first, then scale up.

### 9.4 Reusing Outputs After a Configuration or Version Change

Several intermediate files and per-sample matrices are reused based on file
existence, without validating their inputs or parameters. Use a fresh
`settings.output_dir` after changing VCFs, the union, filtering/counting
settings, or upgrading from older multiallelic handling. Regenerating only the
union does not refresh cached count files and matrices.
