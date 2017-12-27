"""Management script for project 'leonardo'
"""
from __future__ import print_function
from __future__ import absolute_import

from os import path
import argparse
import requests
import shutil
import zipfile

from ozelot import config, client
from leonardo.common import analysis


def download_and_unzip(url_, out_path_):
    r = requests.get(url_, stream=True)
    if r.status_code == 200:
        with open(out_path_, 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)

    zip_arch = zipfile.ZipFile(out_path_, 'r')
    zip_arch.extractall(path.dirname(out_path_))
    zip_arch.close()


if __name__ == '__main__':
    # configure the argument parser
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    # configure options
    parser.add_argument("command", help="Command to execute\n"
                                        "\t'getdata':  download and unpack input data\n"
                                        "\t'initdb':   drop and re-create all database tables\n"
                                        "\t'ingest':   run the ingestion pipeline\n"
                                        "\t'analyze':  generate analysis\n"
                                        "\t'diagrams': generate data model and pipeline diagrams\n"
                                        "              NOTE: this requires GraphViz to be installed.")

    parser.add_argument("--mode", help="Model/pipeline variant, one of 'standard', 'inheritance', "
                                       "'kvstore' or 'extracols'")
    parser.add_argument("--dir", help="For 'analyze' and 'diagrams': output directory (default: current directory)")

    args = parser.parse_args()

    # conditional import, depending on 'mode'
    models = queries = pipeline = None
    if args.mode:
        if args.mode in ['standard', 'inheritance', 'kvstore', 'extracols']:
            # this looks a bit hacky ... probably there's a nicer way to do these imports
            pipeline = getattr(__import__('leonardo.' + args.mode + '.pipeline'), args.mode).pipeline
            models = getattr(__import__('leonardo.' + args.mode + '.models'), args.mode).models
            queries = getattr(__import__('leonardo.' + args.mode + '.queries'), args.mode).queries
        else:
            raise RuntimeError('Invalid parameter for --mode: ' + args.mode)

    # do stuff

    if args.command == 'getdata':
        url = "https://github.com/trycs/ozelot-example-data/raw/master/leonardo/leonardo_data.zip"
        out_path = path.join(config.DATA_DIR, "data.zip")

        print ("Downloading and unpacking " + url + " ...")
        download_and_unzip(url, out_path)
        print ("done.")

    elif args.command == 'initdb':

        if not args.mode:
            raise RuntimeError('Please supply the parameter --mode to initialize the database')

        print("Re-initializing the database ... ", end=' ')

        from ozelot.orm import base

        # import all additional models needed in this project
        # noinspection PyUnresolvedReferences
        from ozelot.orm.target import ORMTargetMarker

        client = client.get_client()
        base.Base.drop_all(client)
        base.Base.create_all(client)

        print("done.")

    elif args.command == 'ingest':
        import luigi

        if not args.mode:
            raise RuntimeError('Please supply the parameter --mode to ingest the data')

        print("Running the full ingestion pipeline\n")
        luigi.build([pipeline.LoadEverything()], local_scheduler=True)

    elif args.command == 'analyze':

        if not args.mode:
            raise RuntimeError('Please supply the parameter --mode to produce output')

        if args.dir:
            analysis.out_dir = args.dir
        else:
            analysis.out_dir = path.dirname(__file__)

        analysis.plots_html_page(queries)

    elif args.command == 'diagrams':
        from ozelot.etl.util import render_diagram

        if not args.mode:
            raise RuntimeError('Please supply the parameter --mode to draw diagrams')

        if args.dir:
            out_dir = args.dir
        else:
            out_dir = path.dirname(__file__)

        render_diagram(root_task=pipeline.LoadEverything(),
                       out_base=path.join(out_dir, 'leonardo_pipeline_' + args.mode))

        out_base = path.join(out_dir, 'leonardo_schema_' + args.mode)
        models.base.render_diagram(out_base)

    else:
        print("Unknown command: " + args.command)
