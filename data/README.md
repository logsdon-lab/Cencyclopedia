# Data:
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

## CDRs
```bash
awk -v OFS="\t"  '{match($1, "^(.+):", chrom); print chrom[1], $2, $3}' /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/all_cdrs_revised.0908.working.bed | \
sort -k1,1 -k2,2n | \
bgzip > data/all_cdrs.bed.gz
tabix -p bed data/all_cdrs.bed.gz
```

## CpG methylation
```bash
awk -v OFS="\t"  '{match($1, "^(.+):", chrom); $1=chrom[1]; print}' /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/all_methyl_w_chm.bed | \
sort -k1,1 -k2,2n | \
bgzip > data/all_CpG_methyl.bedgraph.gz
tabix -p bed data/all_CpG_methyl.bedgraph.gz
```

## AS-HOR
```bash
python data/update_as_hor.py /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/HOR/all_AS-HOR_stv_row.bed | \
bgzip > data/all_AS-HOR_stv_row.bed.gz
tabix -p bed data/all_AS-HOR_stv_row.bed.gz
```

## AS-HOR strand
```bash
awk -v OFS="\t"  '{match($1, "^(.+):", chrom); print chrom[1], $2, $3, ".", 0, $4, $2, $3, ($4 == "+") ? "#ff0000" : "#0000ff"}' /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/Ort/*.bed | \
sort -k1,1 -k2,2n | \
bgzip > data/all_AS-HOR_stv_row_strand.bed.gz
tabix -p bed data/all_AS-HOR_stv_row_strand.bed.gz
```

## Satellite annotation
```bash
awk -v OFS="\t"  '{match($1, "^(.+):", chrom); $1=chrom[1]; print}' /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/RM/*.out | \
sort -k1,1 -k2,2n | \
bgzip > data/all_RM_satellite_annotation.bed.gz
tabix -p bed data/all_RM_satellite_annotation.bed.gz
```

## ModDotPlot
Convert to absolute coordinates.
```bash
awk -v OFS="\t" '{
    match($1, "^(.+):([0-9]+)-([0-9]+)$", mtch);
    $1=mtch[1]; $4=mtch[1];
    $2=$2+mtch[2]; $3=$3+mtch[2];
    $5=$5+mtch[2]; $6=$6+mtch[2];
    print
}' /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/Moddotplot/*.bed | \
sort -k1,1 -k2,2n | \
bgzip > data/all_ModDotPlot.bed.gz
tabix -p bed data/all_ModDotPlot.bed.gz
```

# Sample metadata:
* `/project/logsdon_shared/project_archive/HGSVC3/non-redundant_centromeres/sample_populations_sex.tsv`

# Clades:
```bash
awk -v FS="\t" -v OFS="\t" -v RS='\r\n' '{ name=FILENAME; match(name, "_(p|q).xls", arms); print $1, $2, arms[1] }' $(realpath /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/tree_clade/clades/chr*.xls)
```
