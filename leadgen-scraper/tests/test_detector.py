from unittest.mock import patch, MagicMock
from detector import detect_platform, check_ssl

def make_response(text="", url="https://example.com"):
    r = MagicMock()
    r.text = text
    r.url = url
    return r

def test_detects_wix():
    with patch("detector.requests.get", return_value=make_response(text="WixCodeApi loaded")):
        assert detect_platform("https://example.com") == "wix"

def test_detects_squarespace():
    with patch("detector.requests.get", return_value=make_response(text="squarespace-cdn.com/asset")):
        assert detect_platform("https://example.com") == "squarespace"

def test_detects_weebly():
    with patch("detector.requests.get", return_value=make_response(text="weeblycloud.com/static")):
        assert detect_platform("https://example.com") == "weebly"

def test_detects_wordpress():
    with patch("detector.requests.get", return_value=make_response(text='<link href="/wp-content/themes/main.css">')):
        assert detect_platform("https://example.com") == "wordpress"

def test_returns_custom_for_unknown():
    with patch("detector.requests.get", return_value=make_response(text="<html><body>Hello</body></html>")):
        assert detect_platform("https://example.com") == "custom"

def test_returns_unknown_on_exception():
    with patch("detector.requests.get", side_effect=Exception("timeout")):
        assert detect_platform("https://example.com") == "unknown"

def test_check_ssl_true_for_https():
    with patch("detector.requests.get", return_value=make_response(url="https://example.com")):
        assert check_ssl("https://example.com") is True

def test_check_ssl_false_on_exception():
    with patch("detector.requests.get", side_effect=Exception("refused")):
        assert check_ssl("https://example.com") is False
