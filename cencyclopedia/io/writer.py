import os
import pysam
import tempfile
import polars as pl

from io import BytesIO


def write_bgzip_file(df: pl.DataFrame, ofh: BytesIO):
    with tempfile.NamedTemporaryFile("wt") as tfh:
        # Write file
        df.write_csv(tfh.name, separator="\t", include_header=False)
        ofh.flush()
        # Compress
        compressed_file = f"{tfh.name}.gz"
        pysam.tabix_compress(tfh.name, compressed_file, force=True)
        # Write lines
        with open(compressed_file, "rb") as bfh:
            for line in bfh:
                ofh.write(line)
        try:
            os.remove(compressed_file)
        except FileNotFoundError:
            pass
