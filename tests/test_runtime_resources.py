from geologparser.runtime_resources import peak_process_rss_kib


def test_peak_process_rss_is_nonnegative_or_unavailable():
    value = peak_process_rss_kib()
    assert value is None or value >= 0
