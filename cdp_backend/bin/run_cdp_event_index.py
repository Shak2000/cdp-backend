#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import sys
import traceback
from pathlib import Path

from cdp_backend.pipeline import event_index_pipeline as pipeline

###############################################################################

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)4s: %(module)s:%(lineno)4s %(asctime)s] %(message)s",
)
log = logging.getLogger(__name__)

###############################################################################


class Args(argparse.Namespace):
    def __init__(self) -> None:
        self.__parse()

    def __parse(self) -> None:
        p = argparse.ArgumentParser(
            prog="run_cdp_event_index",
            description="Index all session transcripts found in CDP infrastructure",
        )
        p.add_argument(
            "-g",
            "--google-credentials-file",
            default=(Path(__file__).parent.parent.parent / "cdp-creds.json"),
            type=Path,
            dest="google_credentials_file",
            help="Path to the Google Service Account Credentials JSON file.",
        )
        p.add_argument(
            "-n",
            "--n-grams",
            default=1,
            type=int,
            dest="n_grams",
            help="Number of tokens per n-gram.",
        )
        p.parse_args(namespace=self)


def main() -> None:
    try:
        args = Args()

        flow = pipeline.create_event_index_flow(
            credentials_file=args.google_credentials_file,
            n_grams=args.n_grams,
        )

        flow.run()

    except Exception as e:
        log.error("=============================================")
        log.error("\n\n" + traceback.format_exc())
        log.error("=============================================")
        log.error("\n\n" + str(e) + "\n")
        log.error("=============================================")
        sys.exit(1)


###############################################################################
# Allow caller to directly run this module (usually in development scenarios)

if __name__ == "__main__":
    main()
