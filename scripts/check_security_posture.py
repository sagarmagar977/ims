import os
import sys
from pathlib import Path

import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_project.settings")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402


def _strict_mode():
    return str(os.getenv("SECURITY_STRICT", "0")).strip().lower() in {"1", "true", "yes", "on"}


def _read_render_debug_value():
    render_path = ROOT_DIR / "render.yaml"
    if not render_path.exists():
        return None
    data = yaml.safe_load(render_path.read_text(encoding="utf-8")) or {}
    for service in data.get("services", []):
        if service.get("type") != "web":
            continue
        for env_var in service.get("envVars", []):
            if env_var.get("key") == "DEBUG":
                return str(env_var.get("value"))
    return None


def main():
    errors = []

    if "rest_framework.throttling.AnonRateThrottle" not in settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_CLASSES", ()):
        errors.append("AnonRateThrottle must remain enabled.")
    if "rest_framework.throttling.UserRateThrottle" not in settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_CLASSES", ()):
        errors.append("UserRateThrottle must remain enabled.")
    if not getattr(settings, "LEGACY_API_DEPRECATION_ENABLED", False):
        errors.append("LEGACY_API_DEPRECATION_ENABLED should remain true until enforced removal.")

    render_debug = _read_render_debug_value()
    if render_debug is not None and render_debug.lower() != "false":
        errors.append("render.yaml web service DEBUG must be 'False'.")

    if _strict_mode():
        if settings.DEBUG:
            errors.append("settings.DEBUG must be false in strict mode.")
        if settings.CORS_ALLOW_ALL_ORIGINS:
            errors.append("CORS_ALLOW_ALL_ORIGINS must be false in strict mode.")
        if not getattr(settings, "NOTIFICATION_WEBHOOK_TOKEN", ""):
            errors.append("NOTIFICATION_WEBHOOK_TOKEN must be configured in strict mode.")
        if len(getattr(settings, "SECRET_KEY", "")) < 50:
            errors.append("SECRET_KEY must be at least 50 chars in strict mode.")

    if errors:
        print("Security posture gate failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Security posture gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
