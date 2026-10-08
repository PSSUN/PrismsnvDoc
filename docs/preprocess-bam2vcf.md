# Step 1 (Preprocessing): BAM-to-VCF Calling

`prismsnv bam2vcf` calls the packaged BAM-to-VCF pipeline from an installed PrismSNV environment. It calls SNVs from BAM files and removes known RNA editing sites in the final filtering step.

It always uses the bundled **VarScan v2.4.6** JAR. The former `--varscan-jar`
option has been removed and is rejected as an unknown option. Direct invocation
of `bam2vcf.sh` also locates the bundled JAR relative to the script directory.

## 1. Command and Arguments

```bash
prismsnv bam2vcf \
  --outer-jobs <OUTER_JOBS> \
  --inner-threads <INNER_THREADS> \
  --reference <reference.fa> \
  --rna-edit-bed <RNA_editing.bed> \
  --out-dir <output_dir> \
  --bam-files <bam1> [bam2 ...]
```

### Argument Reference

| Argument | Meaning | Typical Values |
|---|---|---|
| `--outer-jobs` | Number of BAMs processed in parallel (sample-level) | 4 / 6 / 8 |
| `--inner-threads` | samtools threads per BAM | 2 / 4 / 8 |
| `--reference` | Reference genome FASTA with a readable `.fai` index | `hg38.fa` |
| `--rna-edit-bed` | Known RNA editing BED file | `RNA_editing.bed` |
| `--out-dir` | Output directory | `./snv_call_out` |
| `--bam-files` | One or more BAM files | `sample1.bam sample2.bam` |

### Example

```bash
prismsnv bam2vcf \
  --outer-jobs 6 \
  --inner-threads 4 \
  --reference genome.fa \
  --rna-edit-bed RNA_edit.bed \
  --out-dir ./out \
  --bam-files sample1.bam sample2.bam
```

The command requires `bash`, `samtools`, `bedtools`, `java`, and `awk` in `PATH`.
On Windows, use WSL with PrismSNV and these tools installed in the same Conda
environment. Bundling the JAR does not remove the Java requirement.

---

## 2. Per-sample Processing Steps

1. `samtools view -F 1804 -q 20` filters BAM reads.
2. `samtools index` creates index for the filtered BAM.
3. `samtools mpileup -B -q 20 -Q 20` generates pileup.
4. `VarScan mpileup2snp --min-coverage 8 --min-var-freq 0.01 --min-reads2 3` calls SNVs.
5. `bedtools intersect -v` removes known RNA editing sites.

### Threshold Summary

| Threshold | Step | Effect |
|---|---|---|
| `-q 20` | samtools view/mpileup | Filters low mapping-quality reads |
| `-Q 20` | samtools mpileup | Filters low base-quality observations |
| `--min-coverage 8` | VarScan | Excludes low-depth loci |
| `--min-var-freq 0.01` | VarScan | Keeps variants with allele frequency ≥ 1% |
| `--min-reads2 3` | VarScan | Requires at least 3 ALT-supporting reads |

---

## 3. Parallelization and Performance Notes

The script uses two levels of parallelism:

- Outer level: `--outer-jobs` (how many BAM files run simultaneously)
- Inner level: `--inner-threads` (threads used by samtools per BAM)

Practical guidance:

- If machine CPU core count is `N`, keep `outer_jobs * inner_threads` near `N`.
- On slow storage, prefer moderate `outer_jobs` and slightly higher `inner_threads`.

---

## 4. Built-in Input Validation

Before execution, the script checks:

1. Positive integer values for `--outer-jobs` and `--inner-threads`, and required commands in `PATH`.
2. Existence and readability of the reference FASTA, bundled JAR, BED, and input BAM files, plus a readable `<reference.fa>.fai`.
3. Readable input BAM indexes: `sample.bam.bai`, `sample.bai`, `sample.bam.csi`, or `sample.csi`. Missing indexes are created with `samtools index`; an existing but unreadable index is reported as an error.
4. Duplicate BAM basenames that would collide in the output directory, and output directory writability.

Preflight failures abort the pipeline. Preflight can create BAM indexes and the
output directory, so it is not a read-only dry run. A chromosome naming check
compares the first FASTA/BED contigs and only emits a warning for `chr*` versus
non-`chr*` differences; it does not validate all contigs or stop the run.

---

## 5. Output Naming (Per Sample)

- `{sample}.f1804q20.bam`
- `{sample}.f1804q20.bam.bai`
- `{sample}.f1804q20.mpileup`
- `{sample}.f1804q20.vcf`
- `{sample}.f1804q20.no_rna_editing.vcf` (recommended downstream input)

In most workflows, `no_rna_editing.vcf` is used as `samples.<name>.vcf` in the `prismsnv snv2barcode` configuration.

Existing nonempty intermediate/output files are reused without checking input,
parameter, or VarScan version changes. Use a fresh `--out-dir` when any of these
change so that stale results are not reused.

---

## 6. Common Failure Cases

- Missing or unreadable reference `.fai`
- An unreadable BAM index, or failure to create a missing index (for example, a read-only BAM directory)
- Missing Java or an incomplete installation without the bundled JAR
- Duplicate BAM basenames from different input directories
- Mismatched chromosome naming, which can cause RNA editing sites to remain despite a completed run

Recommended troubleshooting order:

1. Confirm command has all required arguments
2. Confirm all file paths exist
3. Confirm index readability, indexing permissions, and chromosome naming compatibility
4. Confirm runtime tools are available: `samtools`, `bedtools`, `java`
