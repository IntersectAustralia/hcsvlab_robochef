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
    args     = parse_args()
    corpus   = args.corpus
    output   = args.output
    xlsx     = args.xlsx
    manifest = args.manifest or 'turtle'
    
    # create output dir if not exist
    create_output_dir(corpus, output)

    # ingest metadata from xlsx
    ingest_xlsx(corpus, output, xlsx, manifest)


def parse_args():
    parser = argparse.ArgumentParser(description='Convert microsoft excel corpus metadata to rdf format')
    parser.add_argument('corpus', metavar='CORPUS', help='corpus directory')
    parser.add_argument('-o', '--output', help='output directory, default: corpus_dir/processed')
    parser.add_argument('-x', '--xlsx', help='excel xlsx metadata file')
    parser.add_argument('-m', '--manifest', help='manifest format, default: turtle')
    return parser.parse_args()


def create_output_dir(corpus_dir, output_dir):
    # create output directory structure, current is one single dir, should be extensible to a whole dir tree if necessary
    # output_dir by default is corpus_dir/processed if not specified
    o_dir = output_dir or os.path.join(corpus, 'processed')
    # create output dir
    os.mkdir(o_dir)


def ingest_xlsx(corpus_dir, output_dir, xlsx_file, manifest_format):
    xlsx_ingester = XLSXIngester(corpus_dir, output_dir, xlsx_file, manifest_format)
    xlsx_ingester.set_metadata()
    xlsx_ingester.ingest_corpus()
    xlsx_ingester.generate_manifest()


if __name__ == "__main__":
    main()
