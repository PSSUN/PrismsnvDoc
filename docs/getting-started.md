# Getting Started

## 1. Environment Requirements

### 1.1 Recommended Software Versions

| Component | Recommended Version | Notes |
|---|---|---|
| Python | 3.12+ | Required by the current package metadata; examples use 3.12 |
| Bash | system/Git Bash/WSL | Required by `prismsnv bam2vcf` |
| samtools | 1.10+ | Used by `prismsnv bam2vcf` for filtering/indexing/mpileup |
| bedtools | 2.29+ | Used to remove known RNA editing sites |
| Java | 8+ | Required to run VarScan |
| awk/gawk | system/gawk | Used by the BAM-to-VCF shell pipeline |

### 1.2 Python Environment Setup

```bash
conda create -n prismsnv python=3.12 -y
conda activate prismsnv
pip install --upgrade pip
pip install -e .
```

Run the install command from the PrismSNV repository root. Use `pip install .` instead of `pip install -e .` if you want a non-editable install.

`prismsnv bam2vcf` also needs command-line tools available in `PATH`:

```bash
conda install -c conda-forge -c bioconda bash samtools bedtools openjdk gawk -y
```

PrismSNV includes `VarScan.v2.4.6.jar` and always uses this bundled version. No
separate download or JAR path is needed; Java remains required. Older commands
containing `--varscan-jar` must have that option and its value removed.

The current PrismSNV package version is `0.1.0`. Python dependencies are pinned
in its `pyproject.toml` and installed by pip; use the metadata from the same
checkout instead of combining dependency instructions from older versions.
The Python requirement above follows that metadata, even if older repository
README or Conda recipe text still mentions Python 3.10.

VarScan has separate licensing terms from PrismSNV: the bundled release notes
describe free non-commercial use by academic, government, and nonprofit
institutions. Commercial use and redistribution require checking the upstream
terms; see `src/prismsnv/preprocess/vendor/README.md` in the PrismSNV checkout.

After installation, confirm that the package command is available:

```bash
prismsnv --help
prismsnv bam2vcf --help
prismsnv snv2barcode --help
prismsnv pre_train --help
prismsnv snv_effect --help
prismsnv get_template --help
```

### 1.3 External Tool Sanity Check

```bash
bash --version
samtools --version
bedtools --version
java -version
awk --version
```

Proceed once these commands return version information.

---

## 2. Required Inputs

The full workflow uses two groups of inputs.

### 2.1 Preprocessing Inputs

| Input | Purpose | Required |
|---|---|---|
| `reference.fa` + `reference.fa.fai` | Reference genome and readable FASTA index | Yes |
| `RNA_editing.bed` | Known RNA editing sites; you can download [here](https://doi.org/10.6084/m9.figshare.30460229) | Yes |
| `*.bam` | Per-sample alignment data; `bam2vcf` creates missing indexes | Yes |
| sample-level VCF | SNV source for `prismsnv snv2barcode` | Yes |
| barcode file | Build barcode×SNV matrix | Yes |

### 2.2 Training Inputs

| Input | Source | Required |
|---|---|---|
| Raw RNA AnnData paths | `pre_train.align.pretrain_adata` and `pre_train.align.finetune_adata` | Yes (`prismsnv pre_train`) |
| `all_samples_merged_barcode_snv_matrix.h5ad` | Output from `prismsnv snv2barcode` | Yes (`prismsnv snv_effect`) |
| `ann_csv` | SNV annotation table | Optional (`prismsnv snv_effect`) |

Notes:

- `prismsnv pre_train` consumes the raw RNA AnnData paths configured in YAML and generates the aligned training artifacts itself; `pretrain_adata.h5ad` and `finetune_adata.h5ad` should not be listed here as standalone user-prepared training inputs.
- `prismsnv snv_effect` reads the RNA-side artifact from `result_folder/finetune_aligned.h5ad`, which is produced by `prismsnv pre_train`.

Important for pretraining batch-aware behavior:

- Batch metadata should be stored in `pretrain_adata.obs[batch_key]`.
- Default key is `batch` (i.e., `pretrain_adata.obs["batch"]`).
- If you use another key, set `pre_train.training.batch_key` in YAML.

---

## 3. Recommended Directory Layout

```text
project-root/
├─ data/
│  ├─ bam/
│  ├─ reference/
│  ├─ barcode/
│  └─ anndata/
├─ result/
└─ config/
```

---

## 4. Minimal Execution Order

```bash
# Step 0: Generate and fill in the training config template
prismsnv get_template --output /path/to/train_config.yaml
# Edit train_config.yaml before proceeding.

# Step 1: Preprocessing
# If you start from raw BAM files, run BAM-to-VCF calling first.
prismsnv bam2vcf \
  --outer-jobs 6 \
  --inner-threads 4 \
  --reference /path/to/genome.fa \
  --rna-edit-bed /path/to/RNA_editing.bed \
  --out-dir ./snv_call_out \
  --bam-files /path/to/sample1.bam /path/to/sample2.bam

prismsnv snv2barcode /path/to/snv2barcode_config.yaml

# Step 2: Training
# 2.1 Pretrain RNA backbone
prismsnv pre_train -y /path/to/train_config.yaml

# 2.2 Train and score SNV perturbation effects
prismsnv snv_effect -y /path/to/train_config.yaml
```

This is the full user-facing flow: preprocessing first, then training.

On Windows, use a WSL Conda environment for installation and execution, with
input paths visible inside WSL (for example, `/mnt/e/...`). Keep Python, Bash,
Java, samtools, and bedtools in the same environment.

---

## 5. Pre-run Checklist

- The reference FASTA has a readable `.fai` index; create it with `samtools faidx reference.fa` if needed
- Input BAM indexes are readable (`.bai` or `.csi`); if absent, the BAM directory must be writable so `bam2vcf` can create an index
- Chromosome naming is consistent between `reference.fa` and `RNA_editing.bed` (`chr1` vs `1`)
- All paths in `train_config.yaml` are valid
- Output directories are writable
- RNA cell IDs match the merged SNV matrix IDs (`<sample_name>_<barcode>`)

This checklist reduces first-run failures significantly.
