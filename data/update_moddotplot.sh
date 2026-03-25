#!/bin/bash

set -euo pipefail

mkdir -p data/ModDotPlot
awk -v OFS="\t" '{
    match($1, "^(.+):([0-9]+)-([0-9]+)$", mtch);
    $1=mtch[1]; $4=mtch[1];
    $2=$2+mtch[2]; $3=$3+mtch[2];
    $5=$5+mtch[2]; $6=$6+mtch[2];
    # Header or invalid chromosome
    if ($1 == "") { next };
    fname="data/ModDotPlot/"$1".bed";
    print > fname
}' /project/logsdon_shared/projects/HGSVC3/HGSVC_centromere_annotation/Moddotplot/*.bed

xargs -P 8 -I {} bash -c "bgzip -@ 8 {} && tabix -p bed {}.gz" < <(realpath data/ModDotPlot/*.bed)
