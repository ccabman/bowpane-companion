"""Real Home Assistant fixtures, isolated from the legacy module doubles."""
import shutil
from pathlib import Path

import pytest


@pytest.fixture
def hass_config_dir(tmp_path):
    source = Path(__file__).parents[1] / 'custom_components' / 'bowpane'
    shutil.copytree(source, tmp_path / 'custom_components' / 'bowpane')
    return str(tmp_path)

@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations):
    pass
