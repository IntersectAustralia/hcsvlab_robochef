import os
import os.path
import sys
import logging
import argparse

from hcsvlab_robochef.ingesters.xlsx.xlsxingester import XLSXIngester


# Main
def main():
    """
    Primary application entry point
    """
    args = parse_args()
    corpus_dir = args.corpus
    output_dir = args.output
    xlsx_metadata_file = args.xlsx
    n3_metadata_file = args.metadata
    manifest_format = args.mformat
    
    # ingest metadata from xlsx
    ingest_xlsx(corpus_dir, output_dir, xlsx_metadata_file, n3_metadata_file, manifest_format)


def parse_args():
    parser = argparse.ArgumentParser(description='Convert microsoft excel corpus metadata to rdf format')
    parser.add_argument('corpus', metavar='CORPUS', help='corpus directory')
    parser.add_argument('-o', '--output', help='output directory, default: corpus/processed')
    parser.add_argument('-x', '--xlsx', help='xlsx metadata file, default: corpus/metadata.xlsx')
    parser.add_argument('-m', '--metadata', help='n3 metadata file, default: corpus/metadata.n3')
    parser.add_argument('-f', '--mformat', help='manifest format, default: turtle')
    return parser.parse_args()


def ingest_xlsx(corpus_dir, output_dir, xlsx_metadata_file, n3_metadata_file, manifest_format):
    xlsx_ingester = XLSXIngester(corpus_dir, output_dir, xlsx_metadata_file, n3_metadata_file, manifest_format)
    xlsx_ingester.set_metadata()
    xlsx_ingester.copy_collection_metadata()
    xlsx_ingester.ingest_corpus()
    xlsx_ingester.generate_manifest()


if __name__ == "__main__":
    main()
