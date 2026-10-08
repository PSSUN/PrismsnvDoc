# Introduction: Why PrismSNV?

PrismSNV addresses the following question:

Single-nucleotide variants (SNVs) are central to tumor evolution, yet their functional consequences remain largely unresolved at single-cell resolution. Crucially, it remains unknown how the impact of specific SNVs varies across patients, cell types, or cellular states, hindering mechanistic understanding and therapeutic stratification. Current strategies operate predominantly at the bulk level and depend on population recurrence or evolutionary constraint, capturing signatures of long-term selection rather than direct, acute cellular effects. Here, we present PrismSNV, a single-cell causal modeling framework that redefines SNVs as endogenous perturbations of cellular state. By quantifying mutation-induced displacement in transcriptomic space, PrismSNV directly measures functional impact and uncovers the dynamic roles of individual SNVs throughout the spatiotemporal evolution of tumors. 

```{figure} _static/Figure-1.png
:align: center
:width: 92%
:alt: PrismSNV workflow overview

Figure 1. PrismSNV workflow overview. The pipeline consists of SNV evidence construction, state representation learning, and perturbation effect estimation.
```

---

## 1. Background and Challenges

Typical analyses can separately obtain:

1. Variant-layer information (ALT support at cell level);
2. Expression-layer information (cell states, cell types, transcriptomic patterns).

The main challenge is not obtaining either layer alone, but linking them at single-cell resolution in a statistically stable way. This is difficult because of:

- **Evidence uncertainty**: missing ALT support does not necessarily indicate true absence of variant;
- **Technical and batch noise**: platform/sample effects can inflate spurious associations;
- **Limited interpretability depth**: aggregate association alone is insufficient for cell-level and cell-type-level interpretation.

---

## 2. Methodological Framework

PrismSNV uses a three-stage framework: evidence construction → representation learning → perturbation scoring.

1. **SNV evidence construction (preprocess)**
   - `prismsnv bam2vcf`: BAM filtering, pileup, SNV calling, and RNA editing-site exclusion;
   - `prismsnv snv2barcode`: barcode×SNV sparse matrix construction with ALT/REF support layers.

2. **State representation learning (pre-train)**
   - `prismsnv pre_train`: VAE-based RNA backbone pretraining to learn latent cell-state representations;
   - optional adversarial branch for batch-effect attenuation.

3. **SNV perturbation effect estimation (snv-effect)**
   - `prismsnv snv_effect`: SNV embeddings and independent sigmoid gates in latent space for conditional perturbation scoring;
   - outputs at both cell and cell-type granularity.

---

## 3. Methodological Characteristics

### 3.1 Probabilistic treatment of missing ALT support

In `prismsnv snv2barcode`, REF-only observations are not naively collapsed to zero. Instead, posterior probabilities are computed from priors and read counts, and retained as `-1` evidence when criteria are satisfied.

### 3.2 State-first, perturbation-second strategy

PrismSNV first learns a stable latent representation of cell state from RNA data, then estimates SNV perturbation effects in that space, reducing noise amplification from direct high-dimensional modeling.

### 3.3 Multi-level interpretability

The framework provides latent-contribution ranking and counterfactual effect scores at both cell-level and cell-type-level to prioritize candidate SNVs for biological interpretation.

### 3.4 Context-aware relative perturbation scoring

PrismSNV measures the relative perturbation strength between SNVs under different cellular backgrounds, keeping the comparison at single-cell resolution rather than collapsing effects into a single bulk-level score.

---

## 4. Intended Use Cases

This method is intended for settings where:

- single-cell expression matrices are available, preferably from full-length protocols;
- SNV evidence matrices can be built from BAM/VCF data at the cell level;
- the goal is to estimate perturbation effects rather than simple co-occurrence statistics.

Continue with **Getting Started** for environment setup and a minimal reproducible run.
