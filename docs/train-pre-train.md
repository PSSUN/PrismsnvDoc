# Step 2 (Training): RNA Backbone Pretraining

`prismsnv pre_train` builds the RNA backbone and writes encoder-derived latent representations into the finetuning dataset used by `prismsnv snv_effect`.

## 1. Run Command

```bash
prismsnv pre_train -y /path/to/train_config.yaml
```

Positional config path is also supported:

```bash
prismsnv pre_train /path/to/train_config.yaml
```

---

## 2. Key YAML Fields

```yaml
result_folder: ./snv_result

pre_train:
  align:
    pretrain_adata: /path/to/pretrain.h5ad
    finetune_adata: /path/to/finetune.h5ad
    expected_doublet_rate: 0.05
    remove_scrublet: false
    mt_percent: 15
  training:
    num_epochs: 200
    latent_dim: 128
    mu_activation: umi
    use_nb: true
    batch_size: 512
    lr: 0.001
    weight_decay: 1e-5
    kl_warmup_epochs: 20
    beta_max: 3.0
    grad_clip: 5.0
    device: cuda
    hvg_only: false
    batch_key: batch
    batch_emb_dim: 16
    lambda_adv: 1.0
    disc_hidden_dim: 128
```

### 2.1 Required Fields

The example follows the packaged template. Template values are explicit choices
and can differ from defaults used when keys are omitted: `hvg_only` is `false`
in the template but defaults to `true` in the CLI, and `lambda_adv` is `1.0` in
the template but defaults to `0.0` when omitted. Generate a fresh template with
`prismsnv get_template` when updating an older configuration.

- `pre_train.align.pretrain_adata`
- `pre_train.align.finetune_adata`
- `pre_train.training.num_epochs`

### 2.2 Common Parameter Recommendations

| Parameter | Typical Start | Notes |
|---|---|---|
| `latent_dim` | 128 | Latent representation size |
| `mu_activation` | `umi` | Decoder mean activation; must be one of `umi`, `softplus`, `identity` |
| `use_nb` | `true` | Recommended for raw UMI count modeling (expects `mu_activation: umi`) |
| `batch_size` | 256–1024 | Adjust by memory budget |
| `kl_warmup_epochs` | 20 | Helps stabilize KL term learning |
| `beta_max` | 1.0–3.0 | Final KL weight reached after warmup; early-stopping patience activates once reached |
| `lambda_adv` | 0.0–1.0 | Adversarial strength for batch-effect mitigation |
| `disc_hidden_dim` | unset | Hidden size of the adversarial discriminator; falls back to `latent_dim` when omitted |
| `mt_percent` | 15 | Alignment QC: drops cells whose mitochondrial read fraction exceeds this threshold (0–100) |

### 2.3 Note

For pretraining, batch metadata must be stored in:

- `pretrain_adata.obs[batch_key]`

By default, `batch_key` is set to:

- `batch`

So the default expectation is:

- `pretrain_adata.obs["batch"]`

If you use a different field name, set it explicitly in YAML:

```yaml
pre_train:
  training:
    batch_key: sample   # example
```

Behavior note:

- If `pretrain_adata.obs[batch_key]` is missing, batch embedding/adversarial batch removal will not be applied.
- If you introduce external data for pretraining, it is recommended that `pretrain_adata` also includes the data represented in `finetune_adata` (or a sufficiently overlapping distribution), so representation transfer remains stable.
- If you do not want to introduce external data, set both `pretrain_adata` and `finetune_adata` to the same `.h5ad` file.

Alignment QC note:

- `pre_train.align.mt_percent` (default 15) removes cells with a mitochondrial read percentage above the threshold from both `pretrain_adata` and `finetune_adata` before alignment. Mitochondrial genes are recognized by the `MT-` prefix in gene symbols (`var["gene_name"]`, `var["gene_symbol"]`, or `var_names`).
- Set `mt_percent: 100` to keep all cells.

Training dynamics note:

- The KL weight ramps linearly from 0 to `beta_max` over `kl_warmup_epochs`; validation-based early stopping only starts once the full `beta_max` is reached.
- `mu_activation` accepts `umi` (raw UMI counts, recommended with `use_nb: true`), `softplus`, or `identity` (corrected/normalized data). Other values are rejected with a config error.
- `disc_hidden_dim` only takes effect when `lambda_adv` > 0 and `batch_key` has more than one level; when omitted it defaults to `latent_dim`.

---

## 3. Internal Stages

1. Align gene space between pretrain and finetune RNA datasets, removing cells above the `mt_percent` mitochondrial threshold (and doublets, if `remove_scrublet: true`).
2. Train `RNAOnlyBackbone` (VAE with NB reconstruction and optional adversarial branch).
3. Save backbone checkpoint.
4. Encode finetune RNA into `obsm["X_latent"]`.

Additional notes:

- If `hvg_only=true` and `highly_variable` exists, training uses HVGs only.
- If `batch_key` exists with >1 levels, batch embedding and adversarial removal can be enabled.
- Learning rate uses warmup + cosine schedule; early stopping is based on validation loss.

---

## 4. Outputs and Downstream Handoff

- `pretrain_aligned.h5ad`
- `finetune_aligned.h5ad`
- `rna_backbone_pretrained.pt`
- `rna_backbone_pretrained.pt.genes.npy`

Downstream usage:

- `finetune_aligned.h5ad` is auto-loaded by `prismsnv snv_effect` from `result_folder`
- `rna_backbone_pretrained.pt` is used for optional weight transfer in `prismsnv snv_effect`

---

## 5. Post-run Checks

At minimum, verify:

1. The four key output files exist in `result_folder`.
2. `finetune_aligned.h5ad` contains `obsm["X_latent"]`.
3. Logs do not report major fallback failures for latent precomputation.
