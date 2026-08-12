#!/bin/bash

set -euo pipefail

WD=$(dirname $0)

mkdir -p "${WD}/ModDotPlot"
awk -v OFS="\t" -v WD="${WD}" '{
    match($1, "^(.+):([0-9]+)-([0-9]+)$", mtch);
    $1=mtch[1]; $4=mtch[1];
    $2=$2+mtch[2]; $3=$3+mtch[2];
    $5=$5+mtch[2]; $6=$6+mtch[2];
    # Header or invalid chromosome
    if ($1 == "") { next };
    fname=WD"/ModDotPlot/"$1".bed";
    print > fname
}' /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/Moddotplot/*.bed \
    /project/logsdon_shared/projects/HPRC/CenMAP/results_hifiasm_b2-3_v0.4.2/11-moddotplot/original/chr22/HG00235_chr22_HG00235#1#CM094380.1:9804542-13020241/HG00235_chr22_HG00235#1#CM094380.1:9804542-13020241.bed \
    /project/logsdon_shared/projects/HPRC/CenMAP/results_hifiasm_b2-3_v0.4.2/11-moddotplot/original/chr22/HG00639_chr22_HG00639#1#JBHIHE010000015.1:7204354-10503203/HG00639_chr22_HG00639#1#JBHIHE010000015.1:7204354-10503203.bed

xargs -P 8 -I {} bash -c "bgzip -@ 8 {} && tabix -p bed {}.gz" < <(realpath "${WD}/ModDotPlot"/*.bed)
