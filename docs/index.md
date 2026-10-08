# PrismSNV User Documentation

These pages describe the current PrismSNV 0.1.0 source checkout (reviewed on
2026-10-08), which requires Python 3.12+ and bundles VarScan v2.4.6. Changes in
the checkout may precede a published release with the same package version.

This documentation describes the complete PrismSNV pipeline:
**BAM-to-VCF Calling → SNV-to-Barcode Matrix Construction → RNA Backbone Pretraining → SNV Perturbation Modeling**.

## Reader Guide

- If this is your first time using PrismSNV, read in this order:
  1. [Introduction](introduction.md)
  2. [Getting Started](getting-started.md)
  3. [Workflow Overview](workflow-overview.md)
  4. [End-to-End Example](end-to-end.md)
- If you already know the basics, think of the runtime flow as three steps:
  - Step 0 (Setup): Get Config Template
  - Step 1 (Preprocessing): BAM-to-VCF Calling, then SNV-to-Barcode Matrix Construction
  - Step 2 (Training): RNA Backbone Pretraining, then SNV Perturbation Modeling

```{toctree}
:maxdepth: 2
:caption: Documentation

introduction
getting-started
workflow-overview
preprocess-bam2vcf
preprocess-snv2barcode
train-pre-train
train-snv-eff
get-template
end-to-end
outputs-and-faq
contact
```
