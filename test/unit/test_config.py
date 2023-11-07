from pathlib import Path

import pytest

from howler.common.exceptions import HowlerValueError

yml_config_good = Path(__file__).parent / "config.yml"
yml_config_bad = Path(__file__).parent / "config-broken.yml"


def test_builtin_config():
    from howler.config import config

    assert config.auth


def test_custom_config():
    from howler.common.loader import get_config

    config = get_config(yml_config_good)

    assert config.auth.oauth.enabled


def test_custom_bad_config():
    from howler.common.loader import get_config

    with pytest.raises(HowlerValueError):
        get_config(yml_config_bad)
