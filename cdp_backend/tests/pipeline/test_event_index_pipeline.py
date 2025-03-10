#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from datetime import datetime
from pathlib import Path
from typing import List
from unittest import mock
from unittest.mock import MagicMock

import pandas as pd
import pytest
import pytz
from prefect import Flow

from cdp_backend.database import functions as db_functions
from cdp_backend.database import models as db_models
from cdp_backend.pipeline import event_index_pipeline as pipeline
from cdp_backend.pipeline.pipeline_config import EventIndexPipelineConfig
from cdp_backend.utils.file_utils import resource_copy

#############################################################################

# NOTE:
# unittest mock patches are accesible in reverse order in params
# i.e. if we did the following patches
# @patch(module.func_a)
# @patch(module.func_b)
#
# the param order for the magic mocks would be
# def test_module(func_b, func_a):
#
# great system stdlib :upsidedownface:

PIPELINE_PATH = "cdp_backend.pipeline.event_index_pipeline"

#############################################################################


@pytest.mark.parametrize("n_grams", [1, 2, 3])
@pytest.mark.parametrize("store_local", [True, False])
def test_create_event_index_flow(n_grams: int, store_local: bool) -> None:
    flow = pipeline.create_event_index_pipeline(
        config=EventIndexPipelineConfig("/fake/creds.json", "doesn't-matter"),
        n_grams=n_grams,
        store_local=store_local,
    )
    assert isinstance(flow, Flow)


#############################################################################

event_one = db_models.Event.Example()
session_one = db_models.Session.Example()
session_one.event_ref = event_one

file_one = db_models.File()
file_one.name = "transcript1.json"
file_one.uri = "fake://transcript1.json"

session_one_transcript_one = db_models.Transcript()
session_one_transcript_one.session_ref = session_one
session_one_transcript_one.file_ref = file_one
session_one_transcript_one.confidence = 0.99
session_one_transcript_one = db_functions.generate_and_attach_doc_hash_as_id(
    session_one_transcript_one
)

file_two = db_models.File()
file_two.name = "transcript2.json"
file_two.uri = "fake://transcript2.json"

session_one_transcript_two = db_models.Transcript()
session_one_transcript_two.session_ref = session_one
session_one_transcript_two.file_ref = file_two
session_one_transcript_two.confidence = 0.97
session_one_transcript_two = db_functions.generate_and_attach_doc_hash_as_id(
    session_one_transcript_two
)

session_two = db_models.Session.Example()
session_two.event_ref = event_one
session_two.video_uri = "fake://no-video.mp4"

file_three = db_models.File()
file_three.name = "transcript3.json"
file_three.uri = "fake://transcript3.json"

session_two_transcript_one = db_models.Transcript()
session_two_transcript_one.session_ref = session_two
session_two_transcript_one.file_ref = file_three
session_two_transcript_one.confidence = 0.2
session_two_transcript_one = db_functions.generate_and_attach_doc_hash_as_id(
    session_two_transcript_one
)

event_two = db_models.Event.Example()
event_two.event_datetime = datetime(2021, 1, 1)

session_three = db_models.Session.Example()
session_three.event_ref = event_two
session_three.video_uri = "fake://really-no-video.mp4"

file_four = db_models.File()
file_four.name = "transcript4.json"
file_four.uri = "fake://transcript4.json"

session_three_transcript_one = db_models.Transcript()
session_three_transcript_one.session_ref = session_three
session_three_transcript_one.file_ref = file_four
session_three_transcript_one.confidence = 0.612
session_three_transcript_one = db_functions.generate_and_attach_doc_hash_as_id(
    session_three_transcript_one
)

#############################################################################


@pytest.mark.parametrize(
    "transcripts, expected_selections",
    [
        (
            [session_one_transcript_one, session_one_transcript_two],
            [session_one_transcript_one],
        ),
        (
            [
                session_one_transcript_one,
                session_one_transcript_two,
                session_two_transcript_one,
            ],
            [session_one_transcript_one, session_two_transcript_one],
        ),
    ],
)
def test_get_highest_confidence_transcript_for_each_session(
    transcripts: List[db_models.Transcript],
    expected_selections: List[db_models.Transcript],
) -> None:
    """
    All we are really testing here is that we are reducing the set properly.
    """
    result_selections = (
        pipeline.get_highest_confidence_transcript_for_each_session.run(  # type: ignore
            transcripts
        )
    )
    assert set(result_selections) == set(expected_selections)


@pytest.mark.parametrize(
    "transcripts, expected_selections",
    [
        (
            [session_one_transcript_one, session_two_transcript_one],
            [
                pipeline.EventTranscripts(
                    event=event_one,
                    transcripts=[
                        session_one_transcript_one,
                        session_two_transcript_one,
                    ],
                )
            ],
        ),
        (
            [
                session_one_transcript_one,
                session_two_transcript_one,
                session_three_transcript_one,
            ],
            [
                pipeline.EventTranscripts(
                    event=event_one,
                    transcripts=[
                        session_one_transcript_one,
                        session_two_transcript_one,
                    ],
                ),
                pipeline.EventTranscripts(
                    event=event_two,
                    transcripts=[
                        session_three_transcript_one,
                    ],
                ),
            ],
        ),
    ],
)
def test_get_transcripts_per_event(
    transcripts: List[db_models.Transcript],
    expected_selections: List[pipeline.EventTranscripts],
) -> None:
    result_selections = pipeline.get_transcripts_per_event.run(  # type: ignore
        transcripts
    )
    for result_et, expected_et in zip(result_selections, expected_selections):
        assert result_et.event.id == expected_et.event.id
        assert set([t.id for t in result_et.transcripts]) == set(
            [t.id for t in expected_et.transcripts]
        )


@mock.patch(f"{PIPELINE_PATH}.get_transcripts.run")
@mock.patch("gcsfs.credentials.GoogleCredentials.connect")
@mock.patch("gcsfs.GCSFileSystem.get")
def test_mocked_pipeline_run(
    mocked_file_get: MagicMock,
    mocked_gcs_connect: MagicMock,
    mocked_get_transcript_models: MagicMock,
    resources_dir: Path,
) -> None:
    # Set up mock data
    session_one_transcript_one.file_ref.uri = "fake_captions.json"
    session_three_transcript_one.file_ref.uri = "brief_080221_2012161.json"

    session_one_transcript_one.session_ref.event_ref.event_datetime = pytz.timezone(
        "UTC"
    ).localize(session_one_transcript_one.session_ref.event_ref.event_datetime)
    session_three_transcript_one.session_ref.event_ref.event_datetime = pytz.timezone(
        "UTC"
    ).localize(session_three_transcript_one.session_ref.event_ref.event_datetime)

    mocked_get_transcript_models.return_value = [
        session_one_transcript_one,
        session_three_transcript_one,
    ]

    def copy_test_file(rpath: str, lpath: str) -> None:
        if "fake_captions.json" in rpath:
            resource_copy(
                str(resources_dir / "generated_transcript_from_fake_captions.json"),
                lpath,
                overwrite=True,
            )
        elif "brief_080221_2012161.json" in rpath:
            resource_copy(
                str(
                    resources_dir
                    / "generated_transcript_from_brief_080221_2012161.json"
                ),
                lpath,
                overwrite=True,
            )

    mocked_file_get.side_effect = copy_test_file

    # Run pipeline to local storage
    flow = pipeline.create_event_index_pipeline(
        config=EventIndexPipelineConfig("/fake/creds.json", "doesn't-matter"),
        n_grams=1,
        store_local=True,
    )
    flow.run()

    # Compare produced index
    expected_values = pd.read_parquet(resources_dir / "expected_1_gram_index.parquet")
    result_values = pd.read_parquet("tfidf-1.parquet")

    # Sort dataframes and reset indices to ensure consistency
    expected_values = expected_values.sort_values(by="stemmed_gram").reset_index(
        drop=True
    )
    result_values = result_values.sort_values(by="stemmed_gram").reset_index(drop=True)

    # Drop certain columns that change based off datetime of test run
    expected_values = expected_values.drop(
        columns=[
            "event_id",
            "event_datetime",
            "datetime_weighted_tfidf",
        ]
    )
    result_values = result_values.drop(
        columns=[
            "event_id",
            "event_datetime",
            "datetime_weighted_tfidf",
        ]
    )
    pd._testing.assert_frame_equal(result_values, expected_values)

    # Cleanup
    os.remove("tfidf-1.parquet")
