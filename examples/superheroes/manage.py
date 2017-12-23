"""Management script for project 'superheroes'
"""
from __future__ import print_function
from __future__ import absolute_import

import sys
from os import path
import argparse
import requests
import shutil
import zipfile


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

    parser.add_argument("--target", help="For 'analyze': analysis to create, 'all' to create all (default)")
    parser.add_argument("--dir", help="For 'analyze' and 'diagrams': output directory")

    args = parser.parse_args()

    # do stuff

    if args.command == 'getdata':
        url = "https://github.com/trycs/ozelot-example-data/raw/master/superheroes/superheroes_web_cache.db.zip"
        out_path = path.join(path.dirname(__file__), "superheroes_web_cache.db.zip")

        print ("Downloading and unpacking " + url + " ...")
        download_and_unzip(url, out_path)
        print ("done.")

    elif args.command == 'initdb':
        from superheroes import models

        print("Re-initializing the database ... ", end=' ')
        models.reinitialize()
        print("done.")

    elif args.command == 'ingest':
        import luigi
        from superheroes import pipeline

        print("Running the full ingestion pipeline\n")
        luigi.build([pipeline.LoadEverything()], local_scheduler=True)

        # exit with error if pipeline didn't finish successfully
        if not pipeline.LoadEverything().complete():
            sys.exit("Pipeline didn't complete successfully.")

    elif args.command == 'analyze':
        from superheroes import analysis

        if args.target:
            target = args.target
        else:
            target = 'all'

        if args.dir:
            analysis.out_dir = args.dir
        else:
            analysis.out_dir = path.dirname(__file__)

        # try to interpret target as function name in 'analysis.py'
        func = getattr(analysis, target, None)
        if func is None:
            print("Unknown analysis target: " + target)
        else:
            func()

    elif args.command == 'diagrams':
        from superheroes import models
        from superheroes import pipeline
        from ozelot.etl.util import render_diagram

        if args.dir:
            out_dir = args.dir
        else:
            out_dir = path.dirname(__file__)

        render_diagram(root_task=pipeline.LoadEverything(),
                       out_base=path.join(out_dir, 'superheroes_pipeline'))

        out_base = path.join(out_dir, 'superheroes_schema')
        models.base.render_diagram(out_base)

    else:
        print("Unknown command: " + args.command)
