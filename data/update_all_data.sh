#!/bin/bash

set -euo pipefail

WD=$(dirname $0)

# CDR
echo "CDRs"
awk -v OFS="\t"  '{
    match($1, "^(.+):", chrom);
    if (chrom[1] in chroms) {
        chroms[chrom[1]] += 1;
    } else {
        chroms[chrom[1]] = 0
    };
    name="cdr_"chroms[chrom[1]]
    print chrom[1], $2, $3, name
}' /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/all_cdrs_revised.0309.working.bed \
    <(grep -P "HG00235_chr22_HG00235#1|HG00639_chr22_HG00639#1" /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/add_two_chr22_HPRC/all_cdrs.bed) | \
sort -k1,1 -k2,2n | \
bgzip > ${WD}/all_cdrs.bed.gz
tabix -p bed ${WD}/all_cdrs.bed.gz

# CpG methylation
echo "CpG methylation"
awk -v OFS="\t"  '{match($1, "^(.+):", chrom); $1=chrom[1]; print}' \
    /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/all_methyl_w_chm.bed \
    <(
        grep -P "HG00235_chr22_HG00235#1|HG00639_chr22_HG00639#1" /project/logsdon_shared/projects/HPRC/paper_analyses/chr13_22_fusion/all_binned_freq.bed | \
        awk -v OFS="\t" '{ print $1, $2, $3, $4 / 100}'
    ) | \
sort -k1,1 -k2,2n | \
bgzip > ${WD}/all_CpG_methyl.bedgraph.gz
tabix -p bed ${WD}/all_CpG_methyl.bedgraph.gz

# AS-HOR
echo "AS-HOR"
tmp_bed=/tmp/hgsvc_stv_row.bed
cat /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/HOR/all_AS-HOR_stv_row.bed \
    <(grep -P "HG00235_chr22_HG00235#1|HG00639_chr22_HG00639#1" /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/add_two_chr22_HPRC/HOR/chr22_AS-HOR_stv_row.all.bed | \
    awk -v OFS="\t" '{match($1, "^(.+):", chrom); print chrom[1], $2, $3, $4, $5, $6}') > "${tmp_bed}"
python ${WD}/update_as_hor.py "${tmp_bed}" | \
bgzip > ${WD}/all_AS-HOR_stv_row.bed.gz
tabix -p bed ${WD}/all_AS-HOR_stv_row.bed.gz
rm -f "${tmp_bed}"

# AS-HOR strand
echo "AS-HOR strand"
awk -v OFS="\t"  '{match($1, "^(.+):", chrom); print chrom[1], $2, $3, ".", 0, $4, $2, $3, ($4 == "+") ? "#ff0000" : "#0000ff"}' \
    /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/Ort/*.bed \
    <(grep -P "HG00235_chr22_HG00235#1|HG00639_chr22_HG00639#1" /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/add_two_chr22_HPRC/Ort/chr22_AS-HOR_stv_row.ort.bed) | \
sort -k1,1 -k2,2n | \
bgzip > ${WD}/all_AS-HOR_stv_row_strand.bed.gz
tabix -p bed ${WD}/all_AS-HOR_stv_row_strand.bed.gz

# Satellite annotation
echo "Satellite annotation"
awk -v OFS="\t"  '{match($1, "^(.+):", chrom); $1=chrom[1]; print}' \
    /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/RM/*.out \
    <(grep -P "HG00235_chr22_HG00235#1|HG00639_chr22_HG00639#1" /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/add_two_chr22_HPRC/RM/all_cens_chr22.annotation.fa.out) | \
sort -k1,1 -k2,2n | \
bgzip > ${WD}/all_RM_satellite_annotation.bed.gz
tabix -p bed ${WD}/all_RM_satellite_annotation.bed.gz

# Local ModDotPlot
echo "Local ModDotPlot"
awk -v OFS="\t"  '{match($1, "^(.+):", chrom); $1=chrom[1]; print}' \
    /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/1DModplot.bed \
    <(grep -P "HG00235_chr22_HG00235#1|HG00639_chr22_HG00639#1" /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/add_two_chr22_HPRC/1DModplot.bed) | \
sort -k1,1 -k2,2n | \
bgzip > ${WD}/all_local_self_identity.bed.gz
tabix -p bed ${WD}/all_local_self_identity.bed.gz

# MEI
echo "MEI"
awk -v OFS="\t" '{
    match($1, "^(.+):", chrom);
    $1=chrom[1];
    if ($1 in chroms) {
        chroms[$1] += 1;
    } else {
        chroms[$1] = 0
    };
    name=$5"_"chroms[$1]
    color=($5 ~ "^L1") ? "#0080FF" : "#FB0000";
    print $1, $2, $3, name, 0, ".", $2, $3, color
}' /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/MEI/MEI.HOR.bed | \
sort -k1,1 -k2,2n | \
bgzip > data/all_MEI.bed.gz
tabix -p bed data/all_MEI.bed.gz
