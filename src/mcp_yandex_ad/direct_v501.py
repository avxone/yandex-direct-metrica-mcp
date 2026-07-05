"""Direct API v501 support for tapi-yandex-direct.

The upstream `tapi-yandex-direct` library hardcodes v5 resource paths in its
resource mapping. For v501-only features (for example, Unified campaigns), we
only need to switch endpoints from `/json/v5/*` to `/json/v501/*`.

We intentionally keep this adapter minimal to avoid diverging from the upstream
request/response logic.
"""

from __future__ import annotations

from tapi2 import generate_wrapper_from_adapter
from tapi_yandex_direct.resource_mapping import RESOURCE_MAPPING_V5
from tapi_yandex_direct.tapi_yandex_direct import YandexDirectClientAdapter


# Extra resources not present in the v5 mapping but available in v501/v5 API.
EXTRA_RESOURCES = {
    "feeds": {"resource": "json/v501/feeds", "methods": ["get", "add", "delete", "update"]},
    "smartadtargets": {"resource": "json/v501/smartadtargets", "methods": ["get", "add", "suspend", "resume", "delete"]},
    "businesses": {"resource": "json/v501/businesses", "methods": ["get"]},
    "creatives": {"resource": "json/v501/creatives", "methods": ["get", "add", "update", "delete"]},
    "vcards": {"resource": "json/v501/vcards", "methods": ["get", "add", "delete", "update"]},
    "negativekeywordsharedsets": {"resource": "json/v5/negativekeywordsharedsets", "methods": ["get", "add", "delete", "update"]},
    "keywordbids": {"resource": "json/v501/keywordbids", "methods": ["get", "setAuto", "deduplicate"]},
    "retargetinglists": {"resource": "json/v5/retargetinglists", "methods": ["get", "add", "delete", "update"]},
    "leads": {"resource": "json/v501/leads", "methods": ["get"]},
    "turbolandingpages": {"resource": "json/v501/turbolandingpages", "methods": ["get", "list"]},
    "videopresets": {"resource": "json/v5/videopresets", "methods": ["get"]},
}


def _upgrade_resource_mapping(mapping: dict) -> dict:
    upgraded: dict = {}
    for key, value in mapping.items():
        resource = value.get("resource")
        if isinstance(resource, str) and "json/v5/" in resource:
            resource = resource.replace("json/v5/", "json/v501/")
        upgraded[key] = {**value, "resource": resource}
    # Add extra resources that don't exist in v5 mapping at all.
    for key, value in EXTRA_RESOURCES.items():
        if key not in upgraded:
            upgraded[key] = value
    return upgraded


RESOURCE_MAPPING_V501 = _upgrade_resource_mapping(RESOURCE_MAPPING_V5)


class YandexDirectClientAdapterV501(YandexDirectClientAdapter):
    resource_mapping = RESOURCE_MAPPING_V501


YandexDirectV501 = generate_wrapper_from_adapter(YandexDirectClientAdapterV501)

