#!/bin/bash

set -euo pipefail

awk -v FS=',' -v OFS=',' '{
    if (NR==1) {
        print "chrom", "xpos_st", "xpos_end", "ypos_st", "ypos_end", "rows";
        next
    } else {
        # 1000 DPI / 96 DPI
        fct=10.416666667;
        print $1, $2 * fct, $3 * fct, $4 * fct, $5 * fct, ($5-$4) / 10
    }
}' assets/Figure1_chrom_bboxes.csv > assets/Figure1_chrom_bboxes_scaled.csv
