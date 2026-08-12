
# T2T-primates
Data wrangling for T2T-primates.

## Why?
Why build another "genome browser"?
* Cannot view multiple haplotypes easily.
* Setup on IGV/UCSC genome browser is difficult.
* Already had a scaffold of a program from our paper.

## Setup.
```bash
pushd ../..
pixi install
```

## Reformat track DB information so makes more sense.
```bash
pixi run snakemake -s data/t2t-primates/Snakefile \
-c 8 \
--rerun-triggers mtime \
-np format_track_db_data
```

## Convert centromere coordinates to BED file
```bash
pixi run snakemake -s data/t2t-primates/Snakefile \
-c 8 \
--rerun-triggers mtime \
-np convert_bedfile_to_long
```

## Then generate merged bigwigs/bigbeds.
```bash
pixi run snakemake -s data/t2t-primates/Snakefile \
-c 8 \
-np \
--rerun-triggers mtime
```

## Scripts
* `convert_regions_to_long.py`
    * Converts T2T-primate centromere coordinates to "long" format.
* `convert_track_data_manifest_to_long.py`
    * Converts T2T-primates censat hub to "long" format.
* `wab`
    * For averaging values across windows in bedgraphs/bigwigs/bedMethyls
    * See [`wab`](https://github.com/koisland/wab/tree/4fcc0c340197b75f0fded39920b7db5444e24b13)
