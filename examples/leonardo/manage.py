"""Management script for project 'leonardo'
"""
from __future__ import print_function
from __future__ import absolute_import

import sys
from os import path, remove
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

    parser.add_argument("--dir", help="For 'analyze' and 'diagrams': output directory (default: current directory)")

    args = parser.parse_args()

    # conditional import, depending on 'mode'
    if config.MODE in ['standard', 'inheritance', 'kvstore', 'extracols']:
        # this looks a bit hacky ... probably there's a nicer way to do these imports
        pipeline = getattr(__import__('leonardo.' + config.MODE + '.pipeline'), config.MODE).pipeline
        models = getattr(__import__('leonardo.' + config.MODE + '.models'), config.MODE).models
        queries = getattr(__import__('leonardo.' + config.MODE + '.queries'), config.MODE).queries
    else:
        raise RuntimeError('Invalid value for MODE: ' + config.MODE)

    # do stuff

    print ("Running in mode '{}'".format(config.MODE))

    if args.command == 'getdata':
        url = "https://github.com/trycs/ozelot-example-data/raw/master/leonardo/data.zip"
        out_path = path.join(config.DATA_DIR, "data.zip")

        print ("Downloading and unpacking " + url + " ...")
        download_and_unzip(url, out_path)
        print ("done.")

    elif args.command == 'initdb':

        print("Re-initializing the database ... ", end=' ')

        from ozelot.orm import base

        # import all additional models needed in this project
        # noinspection PyUnresolvedReferences
        from ozelot.orm.target import ORMTargetMarker

        client = client.get_client()

        # delete database file instead of dropping the tables only; the latter fails
        # when switching between different schemas
        db_file = config.DB_PARAMS['database']
        if path.exists(db_file) and config.DB_PARAMS['driver'] == 'sqlite':
            print ("Removing " + db_file + " before re-initializing the DB ... ", end=' ')
        else:
            base.Base.drop_all(client)

        base.Base.create_all(client)

        print("done.")

    elif args.command == 'ingest':
        import luigi

        print("Running the full ingestion pipeline\n")
        luigi.build([pipeline.LoadEverything()], local_scheduler=True)

        # exit with error if pipeline didn't finish successfully
        if not pipeline.LoadEverything().complete():
            sys.exit("Pipeline didn't complete successfully.")

    elif args.command == 'analyze':

        if args.dir:
            analysis.out_dir = args.dir
        else:
            analysis.out_dir = path.dirname(__file__)

        analysis.plots_html_page(queries)

    elif args.command == 'diagrams':
        from ozelot.etl.util import render_diagram

        if args.dir:
            out_dir = args.dir
        else:
            out_dir = path.dirname(__file__)

        render_diagram(root_task=pipeline.LoadEverything(),
                       out_base=path.join(out_dir, 'leonardo_pipeline_' + config.MODE))

        out_base = path.join(out_dir, 'leonardo_schema_' + config.MODE)
        models.base.render_diagram(out_base)

    else:
        print("Unknown command: " + args.command)
