# Workflow Overview

## Data Preparation

The full workflow requires BAM files, a reference FASTA and its `.fai` index,
an RNA editing BED file, barcode files, and raw RNA AnnData inputs. BAM files
alone are insufficient: `snv2barcode` uses cell barcode tags and `pre_train`
requires expression matrices. Align RNA cell IDs with the merged SNV matrix's
`<sample_name>_<barcode>` IDs. See {doc}`getting-started` for the input checklist.

## Pipeline Stages (User-Facing 2-Step View)

0. **Setup**
   - `prismsnv get_template`: write a `train_config.yaml` template for use with `pre_train` and `snv_effect`.
1. **Step 1: Preprocessing**
   - `prismsnv bam2vcf`: call SNVs from multiple BAM files and remove known RNA editing sites.
   - `prismsnv snv2barcode`: build per-sample and merged barcode×SNV matrices.
2. **Step 2: Training**
   - `prismsnv pre_train`: pretrain RNA backbone and prepare aligned finetuning data.
   - `prismsnv snv_effect`: train SNV perturbation model and export latent-contribution rankings and score outputs.

## Stage Handoffs (Critical)

| Upstream Stage | Key Output | Downstream Consumer |
|---|---|---|
| `bam2vcf` | `{sample}.f1804q20.no_rna_editing.vcf` | `snv2barcode` |
| `snv2barcode` | `all_samples_merged_barcode_snv_matrix.h5ad` | `snv_effect` |
| `pre_train` | `finetune_aligned.h5ad`, `rna_backbone_pretrained.pt` | `snv_effect` |

## Core Bridge Files

- `all_samples_merged_barcode_snv_matrix.h5ad` (from `snv2barcode`, consumed by `snv_effect`)
- `finetune_aligned.h5ad` (from `pre_train`, auto-loaded by `snv_effect`)
- `rna_backbone_pretrained.pt` (from `pre_train`, optionally loaded by `snv_effect`)
