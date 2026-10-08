# Step 2 (Training): SNV Perturbation Modeling

`prismsnv snv_effect` trains the SNV perturbation model on top of RNA backbone representations and exports ranking/scoring outputs.

## 1. Run Command

```bash
prismsnv snv_effect -y /path/to/train_config.yaml
```

Multi-GPU distributed mode (pass `--n_gpu` to launch `torchrun` automatically):

```bash
prismsnv snv_effect --n_gpu 4 -y /path/to/train_config.yaml
```

---

## 2. Key YAML Fields

```yaml
result_folder: ./snv_result

snv_eff:
  adata_snv: /path/to/all_samples_merged_barcode_snv_matrix.h5ad
  ann_csv: /path/to/annotation.csv  # optional
  min_cnt: 50
  n_top: 50
  batch_size_train: 64
  num_epochs: 200
  latent_dim: 128
  snv_emb_dim: 64
  top_k_attention: 5000
  attn_batch: 128
  score_attn_batch: 128
  score_cell_batch: 128
  seed: 42
  rank_lambda_max: 0.05
  rank_margin_max: 0.05
  decoder_lr: 0.0001
  decoder_l2_sp_lambda: 0.0
  delta_ratio_cap: 0.8
  delta_ratio_lambda: 100.0
  freeze_backbone: true
  celltype_key: cell_cluster
  cluster_resolution: 0.4
  cell_type_free: false
  eval_only: false
  pair_chunk: 20000
  batch_key: sample
```

### 2.1 Required Fields

The example uses values from the packaged template. Omitted keys can have
different CLI defaults; for example, `min_cnt` defaults to 100,
`batch_size_train` to 256, `num_epochs` to 500, `top_k_attention` to 2000, and
`attn_batch` to 256. Use `prismsnv get_template` to make choices explicit.

- `snv_eff.adata_snv`

`snv_eff.ann_csv` is optional. If omitted, scoring still runs and annotation metadata columns in the score CSVs are left empty.

Accepted `ann_csv` formats in the current code:

- `.csv` comma-delimited tables
- `.tsv` or `.txt` tab-delimited tables
- some whitespace-delimited text tables (fallback parsing), which is useful for certain ANNOVAR exports

Recommended content patterns:

- Either provide a direct SNV identifier column such as `name`, `snv`, `variant`, or `id`, with values like `chr1:123456_A>T`
- Or provide separate variant columns that can be combined by the script: `chr` / `#chr` / `chrom` / `#chrom`, `pos` / `position` / `start`, plus `ref` and `alt`

If present, the score export will try to carry through annotation fields such as `Func.refGene*`, `Gene.refGene*`, `GeneDetail.refGene*`, `ExonicFunc.refGene*`, `CLNDN`, `CLNALLELEID`, and `CLNSIG`.

### 2.2 Common Parameter Guidance

| Parameter | Role | Tuning Advice |
|---|---|---|
| `min_cnt` | SNV filtering threshold; an SNV is kept when both its positive and negative barcode support counts reach `min_cnt` | Lower for small datasets |
| `n_top` | Number of top SNVs shown in the diagnostic stacked-bar plot (`snv_top_stacked_bar.png`); does not affect the SNVs used for training | Plot-only knob |
| `top_k_attention` | Number of SNVs retained by latent-contribution screening | Increase for larger cohorts |
| `attn_batch` | Batch size for latent-contribution screening | Memory-sensitive |
| `score_attn_batch` | Batch size for per-cell-type latent-contribution ranking during scoring; falls back to `attn_batch` when omitted | Lower if scoring runs out of memory |
| `score_cell_batch` | Batch size for per-cell counterfactual SNV scoring; falls back to `attn_batch` when omitted | Lower if scoring runs out of memory |
| `pair_chunk` | Sparse decode chunk size | Lower first when hitting OOM |
| `cell_type_free` | Skip cell-type-aware scoring | Useful for fast global screening |
| `cluster_resolution` | Leiden clustering resolution used to group cells into cell types (cell-type mode only) | Raise for more, smaller clusters; lower for fewer, larger clusters |

### 2.3 Training-Control Fields

| Parameter | Role | Tuning Advice |
|---|---|---|
| `rank_lambda_max` | Maximum weight of the rank loss contrasting true SNV assignments against same-batch shuffled negatives; the weight ramps up with training progress | Keep small (0–0.1); set 0 to disable |
| `rank_margin_max` | Maximum margin enforced between true-pair loss and shuffled-negative loss | Keep small (0–0.1) |
| `decoder_lr` | Learning rate for the copied RNA decoder parameters; SNV-specific modules keep the main `1e-3` learning rate | Typical 1e-4 |
| `decoder_l2_sp_lambda` | L2-SP weight anchoring copied decoder parameters to their pretrained values | 0 disables anchoring |
| `delta_ratio_cap` | Per-cell soft cap on the latent perturbation magnitude `||delta_z|| / ||z||` | Typical 0.8 |
| `delta_ratio_lambda` | Weight of the squared soft penalty applied above `delta_ratio_cap` | 0 disables the penalty |

Both `delta_ratio_*` terms constrain how far a single SNV may push a cell's latent representation, which keeps counterfactual scores locally plausible.

---

## 3. Internal Stages

1. Load and filter SNV matrix (`min_cnt`) and retain standard chromosomes; `n_top` only controls the top-SNV diagnostic stacked-bar plot.
2. Build `SNVPerturbationModel` (SNV embeddings + independent sigmoid gates + conditional perturbation).
3. Optionally load pretrained backbone weights.
4. Train and save model checkpoint.
5. Export latent-contribution ranking, cell-level scores, cell-type-level scores, and plots.

Additional notes:

- When a pretrained backbone is loaded, `freeze_backbone: true` freezes encoder-side parameters while SNV-related components remain trainable. The alias `freeze_encoder` takes precedence if both keys are set.
- If `eval_only=true`, a compatible versioned `snv_perturbation_model.pt` must already exist; see the evaluation contract below.
- RNA input is auto-loaded from `result_folder/finetune_aligned.h5ad`.
- Training auto-detects `result_folder/rna_backbone_pretrained.pt`; when present, its `.genes.npy` sidecar is required to verify RNA feature order. Keep both pretraining outputs together.
- The current standard-chromosome filter keeps human autosomes 1–22, X, and Y; mitochondrial and other contigs are excluded.
- In cell-type mode, cells are clustered with Leiden on the encoder latent (`X_latent`) at `cluster_resolution`; the resulting labels are written to `obs[celltype_key]` and used for marker-gene identification and per-cell-type scoring.
- During optimization, copied decoder parameters use `decoder_lr` and can be anchored to pretrained values by `decoder_l2_sp_lambda`, while SNV-specific modules keep the main learning rate.
- The training loss includes a rank term (weight `rank_lambda_max`, margin `rank_margin_max`) that contrasts true SNV–cell pairs against same-batch shuffled negatives, plus a soft penalty (`delta_ratio_cap`, `delta_ratio_lambda`) that bounds the relative latent shift a single SNV can induce.

### Evaluation-only Checkpoint Contract

Set `snv_eff.eval_only: true` and run the same `prismsnv snv_effect` command.
This skips training and strictly loads the saved SNV model. A missing file,
legacy bare `state_dict`, unsupported checkpoint version, or incompatible
metadata raises an error; evaluation never falls back to training.

The current checkpoint format is `prismsnv.snv_perturbation`, version **1**
(independent of package version 0.1.0). It stores weights together with ordered
gene and SNV identifiers, the RNA batch key/category mapping, and model
dimensions. Evaluation aligns RNA genes to the saved gene order and validates
the remaining feature and batch contract. Keep the post-filter SNV identities
and order, batch mapping, `latent_dim`, `snv_emb_dim`, and `batch_emb_dim`
compatible with training. Changing `min_cnt` can change the retained SNVs and
cause validation to fail.

Evaluation uses metadata in the SNV checkpoint; it does not load a separate
RNA backbone or infer legacy metadata from `.snvs.npy`. Retrain legacy models
with the current code. Evaluation preserves the checkpoint and its SNV-list
sidecars, but regenerates score/plot outputs in `result_folder`, potentially
overwriting earlier scoring results.

---

## 4. Distributed Execution Notes

Pass `--n_gpu <N>` (where N > 1) to have the CLI automatically re-launch itself under `torchrun --standalone --nproc_per_node=N`. No manual `torchrun` invocation is needed. If the process is already running under a distributed launcher (i.e., `WORLD_SIZE > 1` or `LOCAL_RANK` is set), `--n_gpu` is ignored and the existing environment is used.

Behavior highlights:

- Automatic DDP initialization (NCCL backend)
- Rank 0 handles key logging and checkpoint persistence
- Synchronization barriers/object broadcasts keep scoring inputs consistent across ranks

---

## 5. Main Outputs

- `snv_perturbation_model.pt`
- `snv_perturbation_model.pt.snvs.npy` (ordered model input SNVs; training mode)
- `snv_perturbation_model.pt.final_snvs.npy` (final scored SNVs; training mode)
- `top_snv_attention.csv`
- `snv_perturbation_scores_by_cell.csv`
- `snv_perturbation_scores.csv` when `cell_type_free=true`
- `top_snv_attention_by_celltype.csv` when `cell_type_free=false`
- `snv_perturbation_scores_by_celltype.csv` when `cell_type_free=false`
- `snv_cooccurrence_dedup_removed.csv` when `cell_type_free=false`
- `cell_cluster_marker_genes_top10.csv` when `cell_type_free=false`
- `adata_rna_latent_labeled.h5ad` when `cell_type_free=false`
- `cell_perturbation_scores.csv` when `cell_type_free=false`
- `cell_perturbation/<celltype>_cell_perturbation.csv` for populated high/low perturbation cell lists when `cell_type_free=false`
- `cell_perturbation_and_celltype_umap.pdf` when `cell_type_free=false`

Output branches by mode:

The historical `top_snv_attention*.csv` filenames are retained, but ranking now
uses `Latent_Contribution_Score`, not `Attention_Score`. Score tables use
`score_euclidean` and `score_cosine_distance`, not cosine similarity. See
{doc}`outputs-and-faq` for the current columns.

- `cell_type_free=true`: produces global `snv_perturbation_scores.csv` and skips clustering/aggregation outputs
- `cell_type_free=false`: produces cell-type-aware score files, co-occurrence de-duplication audit, per-cell perturbation tables, and UMAP outputs

---

## 6. Post-run Checks

At minimum, verify:

1. `snv_perturbation_model.pt` was created
2. `top_snv_attention.csv` is non-empty
3. score CSVs contain reasonable SNV/cell counts
4. mode-specific outputs were generated; cell-type visualizations are not expected in `cell_type_free: true`
