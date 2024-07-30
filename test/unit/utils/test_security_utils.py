from howler.security.utils import get_disco_url


def test_get_disco_url():
    result = get_disco_url("https://howler.dev.analysis.cyber.gc.ca")

    assert result == "https://discover.dev.analysis.cyber.gc.ca/eureka/apps"
