"""
Unit tests for request_with_retry and call_gemini_with_retry.
Mocks all network and sleeps to ensure zero external calls and instant execution.
"""
import urllib.request
import urllib.error
import http.client
from unittest.mock import MagicMock, patch
import pytest
from dev_pipeline import request_with_retry, call_gemini_with_retry


def test_request_with_retry_immediate_success():
    req = urllib.request.Request("https://example.com/api")
    mock_resp = MagicMock()

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        resp = request_with_retry(req, max_retries=2, base_backoff=0.001)
        assert resp == mock_resp
        assert mock_urlopen.call_count == 1


def test_request_with_retry_on_429_with_retry_after():
    req = urllib.request.Request("https://example.com/api")
    mock_resp = MagicMock()

    # Create mock HTTP 429 error with Retry-After header
    mock_headers = MagicMock()
    mock_headers.get.side_effect = lambda key, default=None: "0.01" if key == "Retry-After" else default
    err_429 = urllib.error.HTTPError(
        url="https://example.com/api",
        code=429,
        msg="Too Many Requests",
        hdrs=mock_headers,
        fp=None
    )

    with patch("urllib.request.urlopen", side_effect=[err_429, mock_resp]) as mock_urlopen:
        with patch("time.sleep") as mock_sleep:
            resp = request_with_retry(req, max_retries=2, base_backoff=0.001)
            assert resp == mock_resp
            assert mock_urlopen.call_count == 2
            assert mock_sleep.call_count == 1


def test_request_with_retry_on_503_transient():
    req = urllib.request.Request("https://example.com/api")
    mock_resp = MagicMock()
    err_503 = urllib.error.HTTPError(
        url="https://example.com/api",
        code=503,
        msg="Service Unavailable",
        hdrs=None,
        fp=None
    )

    with patch("urllib.request.urlopen", side_effect=[err_503, mock_resp]) as mock_urlopen:
        with patch("time.sleep"):
            resp = request_with_retry(req, max_retries=2, base_backoff=0.001)
            assert resp == mock_resp
            assert mock_urlopen.call_count == 2


def test_request_with_retry_non_retryable_404():
    req = urllib.request.Request("https://example.com/api")
    err_404 = urllib.error.HTTPError(
        url="https://example.com/api",
        code=404,
        msg="Not Found",
        hdrs=None,
        fp=None
    )

    with patch("urllib.request.urlopen", side_effect=err_404) as mock_urlopen:
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            request_with_retry(req, max_retries=3, base_backoff=0.001)
        assert exc_info.value.code == 404
        assert mock_urlopen.call_count == 1  # Did NOT retry 404


def test_request_with_retry_exceeds_max_retries():
    req = urllib.request.Request("https://example.com/api")
    err_500 = urllib.error.HTTPError(
        url="https://example.com/api",
        code=500,
        msg="Internal Error",
        hdrs=None,
        fp=None
    )

    with patch("urllib.request.urlopen", side_effect=err_500) as mock_urlopen:
        with patch("time.sleep"):
            with pytest.raises(urllib.error.HTTPError):
                request_with_retry(req, max_retries=2, base_backoff=0.001)
            # 1 initial + 2 retries = 3 calls
            assert mock_urlopen.call_count == 3


def test_request_with_retry_timeout_error():
    req = urllib.request.Request("https://example.com/api")
    mock_resp = MagicMock()

    with patch("urllib.request.urlopen", side_effect=[TimeoutError("Timed out"), mock_resp]) as mock_urlopen:
        with patch("time.sleep"):
            resp = request_with_retry(req, max_retries=2, base_backoff=0.001)
            assert resp == mock_resp
            assert mock_urlopen.call_count == 2


def test_call_gemini_with_retry_immediate_success():
    func = MagicMock(return_value="gemini output")
    result = call_gemini_with_retry(func, "arg1", kw="val")
    assert result == "gemini output"
    assert func.call_count == 1


def test_call_gemini_with_retry_rate_limit_transient():
    func = MagicMock(side_effect=[
        Exception("429 Resource exhausted: quota exceeded"),
        "recovered output"
    ])
    with patch("time.sleep"):
        result = call_gemini_with_retry(func, max_retries=2, base_backoff=0.001)
        assert result == "recovered output"
        assert func.call_count == 2


def test_call_gemini_with_retry_non_transient_failure():
    func = MagicMock(side_effect=ValueError("Invalid model name parameter"))
    with pytest.raises(ValueError):
        call_gemini_with_retry(func, max_retries=3, base_backoff=0.001)
    assert func.call_count == 1
