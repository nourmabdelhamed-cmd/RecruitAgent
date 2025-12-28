"""Pytest configuration and shared fixtures."""

import pytest
from hypothesis import settings

# Configure hypothesis for minimum 100 iterations per property test
settings.register_profile("default", max_examples=100)
settings.load_profile("default")
