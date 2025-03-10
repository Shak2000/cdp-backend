#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, Optional
from unittest import mock

import pytest

from cdp_backend.database import models, validators
from cdp_backend.database.constants import (
    EventMinutesItemDecision,
    MatterStatusDecision,
    VoteDecision,
)

from .. import test_utils

#############################################################################

validator_kwargs = {"google_credentials_file": "filepath"}

"""
Uniqueness test constants 

Defined because Example() uses datetime.utcnow() which interferes 
with uniqueness testing
"""
body = models.Body.Example()
person = models.Person.Example()
event = models.Event.Example()


@pytest.mark.parametrize(
    "router_string, expected_result",
    [
        (None, True),
        ("lorena-gonzalez", True),
        ("lorena", True),
        ("LORENA", False),
        ("gonzález", False),
        ("lorena_gonzalez", False),
        ("lorena gonzalez", False),
    ],
)
def test_router_string_is_valid(router_string: str, expected_result: bool) -> None:
    actual_result = validators.router_string_is_valid(router_string)
    assert actual_result == expected_result


@pytest.mark.parametrize(
    "email, expected_result",
    [
        (None, True),
        ("Lorena.Gonzalez@seattle.gov", True),
        ("lorena.gonzalez@seattle.gov", True),
        ("Lorena.gov", False),
        ("Lorena@", False),
        ("Lorena@seattle", False),
        ("Lorena Gonzalez@seattle", False),
        ("Lorena.González@seattle.gov", False),
    ],
)
def test_email_is_valid(email: str, expected_result: bool) -> None:
    actual_result = validators.email_is_valid(email)
    assert actual_result == expected_result


@pytest.mark.parametrize(
    "uri, expected_result",
    [
        (None, True),
        (__file__, True),
        ("file://does-not-exist.txt", False),
    ],
)
def test_local_resource_exists(
    uri: str,
    expected_result: bool,
) -> None:
    actual_result = validators.resource_exists(uri)
    assert actual_result == expected_result


@pytest.mark.skipif(
    not test_utils.internet_is_available(),
    reason="No internet connection",
)
@pytest.mark.parametrize(
    "uri, expected_result, gcsfs_exists, kwargs",
    [
        (None, True, None, None),
        ("https://docs.pytest.org/en/latest/index.html", True, None, None),
        ("https://docs.pytest.org/en/latest/does-not-exist.html", False, None, None),
        ("gs://bucket/filename.txt", True, True, validator_kwargs),
        (
            "https://storage.googleapis.com/download/storage/v1/b/"
            + "bucket.appspot.com/o/wombo_combo.mp4?alt=media",
            True,
            True,
            validator_kwargs,
        ),
        ("gs://bucket/filename.txt", False, False, validator_kwargs),
        # Unconvertible JSON url case
        (
            "https://storage.googleapis.com/download/storage/v1/xxx/"
            + "bucket.appspot.com",
            True,
            None,
            None,
        ),
    ],
)
def test_remote_resource_exists(
    uri: str,
    expected_result: bool,
    gcsfs_exists: Optional[bool],
    kwargs: Optional[Dict],
) -> None:
    with mock.patch("gcsfs.credentials.GoogleCredentials.connect"):
        with mock.patch("gcsfs.GCSFileSystem.exists") as mock_exists:
            mock_exists.return_value = gcsfs_exists
            if kwargs:
                actual_result = validators.resource_exists(uri, **kwargs)
            else:
                actual_result = validators.resource_exists(uri)

            assert actual_result == expected_result


@pytest.mark.parametrize(
    "decision, expected_result",
    [
        (None, False),
        ("Approve", True),
        ("INVALID", False),
    ],
)
def test_vote_decision_is_valid(decision: str, expected_result: bool) -> None:
    validator_func = validators.create_constant_value_validator(VoteDecision, True)
    actual_result = validator_func(decision)
    assert actual_result == expected_result


@pytest.mark.parametrize(
    "decision, expected_result",
    [
        (None, True),
        ("Passed", True),
        ("INVALID", False),
    ],
)
def test_event_minutes_item_decision_is_valid(
    decision: str, expected_result: bool
) -> None:
    validator_func = validators.create_constant_value_validator(
        EventMinutesItemDecision, False
    )
    actual_result = validator_func(decision)
    assert actual_result == expected_result


@pytest.mark.parametrize(
    "decision, expected_result",
    [
        (None, False),
        ("Adopted", True),
        ("INVALID", False),
    ],
)
def test_matter_status_decision_is_valid(decision: str, expected_result: bool) -> None:
    validator_func = validators.create_constant_value_validator(
        MatterStatusDecision, True
    )
    actual_result = validator_func(decision)
    assert actual_result == expected_result
