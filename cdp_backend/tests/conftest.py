#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configuration for tests! There are a whole list of hooks you can define in this file to
run before, after, or to mutate how tests run. Commonly for most of our work, we use
this file to define top level fixtures that may be needed for tests throughout multiple
test files.

In this case, while we aren't using this fixture in our tests, the prime use case for
something like this would be when we want to preload a file to be used in multiple
tests. File reading can take time, so instead of re-reading the file for each test,
read the file once then use the loaded content.

Docs: https://docs.pytest.org/en/latest/example/simple.html
      https://docs.pytest.org/en/latest/plugins.html#requiring-loading-plugins-in-a-test-module-or-conftest-file
"""

from pathlib import Path

import pytest


@pytest.fixture
def resources_dir() -> Path:
    return Path(__file__).parent / "resources"


EXAMPLE_VIDEO_FILENAME = "example_video.mp4"
EXAMPLE_VIDEO_HD_FILENAME = "example_video_large.mp4"


@pytest.fixture
def example_video(resources_dir: Path) -> Path:
    return resources_dir / EXAMPLE_VIDEO_FILENAME
