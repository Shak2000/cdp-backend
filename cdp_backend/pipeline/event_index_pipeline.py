#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from prefect import Flow, task

from ..database import functions as db_functions
from ..database import models as db_models

###############################################################################

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)4s: %(module)s:%(lineno)4s %(asctime)s] %(message)s",
)
log = logging.getLogger(__name__)

###############################################################################


def create_event_index_flow(credentials_file: str, n_grams: int = 1) -> Flow:
    """
    Create the Prefect Flow object responsible for indexing the events found in
    the CDP instance database.

    Parameters
    ----------
    credentials_file: str
        Path to Google Service Account Credentials JSON file.
    n_grams: int
        Number of grams per stored-phrase.
        Default: 1 (unigrams, store single words / tokens)

    Returns
    -------
    flow: Flow
        The constructed CDP Event Index Pipeline as a Prefect Flow.
    """
    # Create flow
    with Flow("CDP Event Index Pipeline") as flow:
        # Get all transcript metadata
        transcript_meta_df = db_functions.get_all_docs_from_collection_task(
            model=db_models.Transcript, creds_file=credentials_file
        )

    return flow
