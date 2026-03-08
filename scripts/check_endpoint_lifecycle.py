import json
import sys
from datetime import date, datetime, timezone
from email.utils import format_datetime
from pathlib import Path

import os

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_project.settings")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402


CALENDAR_PATH = ROOT_DIR / "PRD" / "ENDPOINT_LIFECYCLE_CALENDAR.json"
URLS_PATH = ROOT_DIR / "django_project" / "urls.py"


def _load_calendar():
    with CALENDAR_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _parse_iso_date(label, value, errors):
    try:
        return date.fromisoformat(value)
    except Exception:
        errors.append(f"{label} must be ISO format YYYY-MM-DD, got: {value!r}")
        return None


def _http_sunset_value(d):
    return format_datetime(datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=timezone.utc), usegmt=True)


def main():
    errors = []
    calendar = _load_calendar()
    policy = calendar.get("legacy_api_policy") or {}

    dep_date = _parse_iso_date("deprecation_effective_date", policy.get("deprecation_effective_date"), errors)
    sunset_date = _parse_iso_date("sunset_date", policy.get("sunset_date"), errors)
    enforcement_date = _parse_iso_date("enforcement_start_date", policy.get("enforcement_start_date"), errors)

    if dep_date and sunset_date and dep_date > sunset_date:
        errors.append("deprecation_effective_date must be on/before sunset_date.")
    if sunset_date and enforcement_date and sunset_date >= enforcement_date:
        errors.append("sunset_date must be before enforcement_start_date.")

    expected_legacy_prefix = policy.get("legacy_prefix", "/api/")
    expected_successor_prefix = policy.get("successor_prefix", "/api/v1/")
    if expected_legacy_prefix != getattr(settings, "LEGACY_API_PREFIX", "/api/"):
        errors.append("legacy_prefix in calendar does not match Django settings LEGACY_API_PREFIX.")
    if expected_successor_prefix != getattr(settings, "LEGACY_API_SUCCESSOR_PREFIX", "/api/v1/"):
        errors.append("successor_prefix in calendar does not match Django settings LEGACY_API_SUCCESSOR_PREFIX.")

    if sunset_date:
        expected_http_sunset = _http_sunset_value(sunset_date)
        if expected_http_sunset != getattr(settings, "LEGACY_API_SUNSET_HTTP_DATE", ""):
            errors.append(
                f"LEGACY_API_SUNSET_HTTP_DATE mismatch: expected '{expected_http_sunset}', "
                f"got '{getattr(settings, 'LEGACY_API_SUNSET_HTTP_DATE', '')}'."
            )

    api_modules = calendar.get("api_modules") or []
    if not isinstance(api_modules, list) or not api_modules:
        errors.append("api_modules must be a non-empty array.")
        api_modules = []

    urls_source = URLS_PATH.read_text(encoding="utf-8")
    for module in api_modules:
        legacy_mount = f'path("api/", include("{module}"))'
        v1_mount = f'path("api/v1/", include("{module}"))'
        if legacy_mount not in urls_source:
            errors.append(f"Missing legacy mount in django_project/urls.py: {legacy_mount}")
        if v1_mount not in urls_source:
            errors.append(f"Missing v1 mount in django_project/urls.py: {v1_mount}")

        if enforcement_date and date.today() >= enforcement_date and legacy_mount in urls_source:
            errors.append(
                f"Legacy mount still exists after enforcement_start_date ({enforcement_date.isoformat()}): {legacy_mount}"
            )

    if errors:
        print("Endpoint lifecycle gate failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("Endpoint lifecycle gate passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
