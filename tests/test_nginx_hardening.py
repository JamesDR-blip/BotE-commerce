from pathlib import Path


NGINX_CONFIG = Path(__file__).resolve().parents[1] / "nginx" / "nginx.conf"


def test_nginx_api_rate_limiting_is_configured() -> None:
    config = NGINX_CONFIG.read_text(encoding="utf-8")

    assert "limit_req_zone $binary_remote_addr zone=api_rate_limit:10m rate=10r/s;" in config
    assert "limit_req zone=api_rate_limit burst=20 nodelay;" in config
    assert "limit_req_status 429;" in config


def test_nginx_healthcheck_is_not_rate_limited() -> None:
    config = NGINX_CONFIG.read_text(encoding="utf-8")

    healthz_start = config.index("location = /healthz")
    healthz_end = config.index("}", healthz_start)

    healthz_block = config[healthz_start:healthz_end]

    assert "limit_req" not in healthz_block


def test_nginx_dashboard_is_not_rate_limited() -> None:
    config = NGINX_CONFIG.read_text(encoding="utf-8")

    dashboard_start = config.index("location /dashboard/")
    dashboard_end = config.index("}", dashboard_start)

    dashboard_block = config[dashboard_start:dashboard_end]

    assert "limit_req" not in dashboard_block
