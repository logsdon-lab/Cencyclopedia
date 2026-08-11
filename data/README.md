# Data:

## T2T-primates
Reformat track DB information so makes more sense.
```bash
pixi run snakemake -s data/t2t-primates/Snakefile \
-c 8 \
--rerun-triggers mtime \
-np format_track_db_data
```

Then generate merged bigwigs/bigbeds.
```bash
pixi run snakemake -s data/t2t-primates/Snakefile \
-c 8 \
-np \
--rerun-triggers mtime
```

## HGSVC
```
HOR annotation: /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/HOR
RM annotation: /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/RM
Ort annotation: /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/Ort
CDR annotation: /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/all_cdrs_revised.0908.working.bed
Moddotplot annotation: /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/ModDotPlot
1DModdotplot annotation: /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/1DModplot.bed
Methy annotation: /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/all_methyl_w_chm.bed
Array name: /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/all_array_name
MEI inside HOR: /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/MEI/MEI.HOR.bed
Live Array length: /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/all_array_length.bed
```
* `/project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/README.md`

Also add HPRC cases.
```
RM:
/project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/add_two_chr22_HPRC/RM/all_cens_chr22.annotation.fa.out
HOR:
/project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/add_two_chr22_HPRC/HOR/chr22_AS-HOR_stv_row.all.bed
CDR:
/project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/add_two_chr22_HPRC/all_cdrs.bed
1D:
/project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/add_two_chr22_HPRC/1DModplot.bed
Ort:
/project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/add_two_chr22_HPRC/Ort/chr22_AS-HOR_stv_row.ort.bed
MEI:
None
```

## Script
On UPenn LPC, run `update_all_data.sh`.
```bash
bash hgsvc/update_all_data.sh
```

ModDotPlot takes a while so is done separately with `update_moddotplot.sh`.
```bash
bash hgsvc/update_moddotplot.sh
```

# Sample metadata:
```bash
# Add CHMs and special HPRC chr22 cases
cat /project/logsdon_shared/project_archive/HGSVC3/non-redundant_centromeres/sample_populations_sex.tsv \
    <(printf "chm13\tEUR\tN\nchm1\tEUR\tN\nHG00235\tEUR\tF\nHG00639\tAMR\tF\n") | \
gzip > data/hgsvc/sample_metadata.tsv.gz
```

# Clades:
```bash
awk -v FS="\t" -v OFS="\t" -v RS='\r\n' '{
    name=FILENAME;
    match(name, "(_|.)(p|q).xls", arms);
    print $1, $2, arms[2]
}' $(realpath /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/tree_clade/clades/chr*.xls) | \
gzip > data/hgsvc/clades.tsv.gz
```
