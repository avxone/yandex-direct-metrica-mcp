"""Extra Direct HF tools: videos, feeds, smart-targets, businesses, etc."""

from __future__ import annotations

import time
import base64
import json
from typing import Any

from .hf_common import HFError, hf_payload, ensure_hf_enabled, ensure_hf_write_enabled, should_apply


def handle(name: str, ctx: Any, args: dict[str, Any]) -> dict[str, Any] | None:
    """Dispatch to extra handlers. Returns None if name is not handled here."""
    # ─── Videos ────────────────────────────────────────────────────────
    if name == "direct.hf.video_list":
        return _video_list(ctx, args)
    if name == "direct.hf.video_upload":
        return _video_upload(ctx, args)

    # ─── Feeds (v501) ──────────────────────────────────────────────────
    if name == "direct.hf.feed_list":
        return _feed_list(ctx, args)
    if name == "direct.hf.feed_create":
        return _feed_create(ctx, args)
    if name == "direct.hf.feed_delete":
        return _feed_delete(ctx, args)
    if name == "direct.hf.feed_update":
        return _feed_update(ctx, args)

    # ─── Smart targets (v501) ──────────────────────────────────────────
    if name == "direct.hf.smart_target_list":
        return _smart_target_list(ctx, args)
    if name == "direct.hf.smart_target_create":
        return _smart_target_create(ctx, args)
    if name == "direct.hf.smart_target_action":
        return _smart_target_action(ctx, args)

    # ─── Businesses ────────────────────────────────────────────────────
    if name == "direct.hf.businesses_get":
        return _businesses_get(ctx, args)

    # ─── Creatives ─────────────────────────────────────────────────────
    if name == "direct.hf.creative_add":
        return _creative_add(ctx, args)
    if name == "direct.hf.creative_list":
        return _creative_list(ctx, args)

    # ─── VCards ────────────────────────────────────────────────────────
    if name == "direct.hf.vcard_create":
        return _vcard_create(ctx, args)
    if name == "direct.hf.vcard_list":
        return _vcard_list(ctx, args)
    if name == "direct.hf.vcard_delete":
        return _vcard_delete(ctx, args)

    # ─── Blocked IPs / Excluded sites ──────────────────────────────────
    if name == "direct.hf.blocked_ips_update":
        return _blocked_ips_update(ctx, args)
    if name == "direct.hf.excluded_sites_get":
        return _excluded_sites_get(ctx, args)
    if name == "direct.hf.excluded_sites_update":
        return _excluded_sites_update(ctx, args)

    # ─── Minus-phrases sets (shared) ───────────────────────────────────
    if name == "direct.hf.neg_keyword_set_create":
        return _neg_keyword_set_create(ctx, args)
    if name == "direct.hf.neg_keyword_set_list":
        return _neg_keyword_set_list(ctx, args)
    if name == "direct.hf.neg_keyword_set_update":
        return _neg_keyword_set_update(ctx, args)
    if name == "direct.hf.neg_keyword_set_delete":
        return _neg_keyword_set_delete(ctx, args)

    # ─── Keyword tools ─────────────────────────────────────────────────
    if name == "direct.hf.keyword_bids_set_auto":
        return _keyword_bids_set_auto(ctx, args)
    if name == "direct.hf.keywords_has_volume":
        return _keywords_has_volume(ctx, args)
    if name == "direct.hf.keywords_research":
        return _keywords_research(ctx, args)

    # ─── Bid modifiers ─────────────────────────────────────────────────
    if name == "direct.hf.bid_modifiers_toggle":
        return _bid_modifiers_toggle(ctx, args)

    # ─── Callouts link ─────────────────────────────────────────────────
    if name == "direct.hf.callouts_link":
        return _callouts_link(ctx, args)

    # ─── Dynamic / Image / Shopping ads ────────────────────────────────
    if name == "direct.hf.create_dynamic_ads":
        return _create_dynamic_ads(ctx, args)
    if name == "direct.hf.create_image_ads":
        return _create_image_ads(ctx, args)
    if name == "direct.hf.create_shopping_ads":
        return _create_shopping_ads(ctx, args)

    # ─── Ad images ─────────────────────────────────────────────────────
    if name == "direct.hf.ad_images_add":
        return _ad_images_add(ctx, args)
    if name == "direct.hf.ad_images_get":
        return _ad_images_get(ctx, args)
    if name == "direct.hf.ad_images_delete":
        return _ad_images_delete(ctx, args)

    # ─── Audience targets ──────────────────────────────────────────────
    if name == "direct.hf.audience_targets_add":
        return _audience_targets_add(ctx, args)
    if name == "direct.hf.audience_targets_get":
        return _audience_targets_get(ctx, args)
    if name == "direct.hf.audience_targets_delete":
        return _audience_targets_delete(ctx, args)

    # ─── Retargeting lists ─────────────────────────────────────────────
    if name == "direct.hf.retargeting_lists_add":
        return _retargeting_lists_add(ctx, args)
    if name == "direct.hf.retargeting_lists_get":
        return _retargeting_lists_get(ctx, args)
    if name == "direct.hf.retargeting_lists_delete":
        return _retargeting_lists_delete(ctx, args)

    # ─── Sitelinks delete ──────────────────────────────────────────────
    if name == "direct.hf.sitelinks_delete":
        return _sitelinks_delete(ctx, args)

    # ─── Ad extensions get/delete ──────────────────────────────────────
    if name == "direct.hf.ad_extensions_get":
        return _ad_extensions_get(ctx, args)
    if name == "direct.hf.ad_extensions_delete":
        return _ad_extensions_delete(ctx, args)

    # ─── Interests dictionary ──────────────────────────────────────────
    if name == "direct.hf.interests_get":
        return _interests_get(ctx, args)

    # ─── NEW TOOLS BATCH: Create campaign ──────────────────────────────
    if name == "direct.hf.create_campaign":
        return _create_campaign(ctx, args)

    # ─── NEW TOOLS BATCH: Combinator TextAds ───────────────────────────
    if name == "direct.hf.create_textads_combinator":
        return _create_textads_combinator(ctx, args)

    # ─── NEW TOOLS BATCH: Leads ────────────────────────────────────────
    if name == "direct.hf.get_leads":
        return _get_leads(ctx, args)

    # ─── NEW TOOLS BATCH: Creative update/delete ───────────────────────
    if name == "direct.hf.creative_update":
        return _creative_update(ctx, args)
    if name == "direct.hf.creative_delete":
        return _creative_delete(ctx, args)

    # ─── NEW TOOLS BATCH: Video delete ─────────────────────────────────
    if name == "direct.hf.video_delete":
        return _video_delete(ctx, args)

    # ─── NEW TOOLS BATCH: Keywords resume/update ───────────────────────
    if name == "direct.hf.keywords_resume":
        return _keywords_resume(ctx, args)
    if name == "direct.hf.update_keywords":
        return _update_keywords(ctx, args)

    # ─── NEW TOOLS BATCH: Audience targets setBids ─────────────────────
    if name == "direct.hf.audience_targets_set_bids":
        return _audience_targets_set_bids(ctx, args)

    # ─── NEW TOOLS BATCH: VCard update ─────────────────────────────────
    if name == "direct.hf.vcard_update":
        return _vcard_update(ctx, args)

    # ─── NEW TOOLS BATCH: Sitelinks update ─────────────────────────────
    if name == "direct.hf.sitelinks_update":
        return _sitelinks_update(ctx, args)

    # ─── NEW TOOLS BATCH: Video extension add (adextensions) ───────────
    if name == "direct.hf.video_extension_add":
        return _video_extension_add(ctx, args)

    # ─── NEW TOOLS BATCH: Card extensions ──────────────────────────────
    if name == "direct.hf.card_extension_add":
        return _card_extension_add(ctx, args)
    if name == "direct.hf.card_extension_delete":
        return _card_extension_delete(ctx, args)

    # ─── NEW TOOLS BATCH: Client update ────────────────────────────────
    if name == "direct.hf.client_update":
        return _client_update(ctx, args)

    # ─── NEW TOOLS BATCH: Turbo pages ──────────────────────────────────
    if name == "direct.hf.turbo_pages_list":
        return _turbo_pages_list(ctx, args)
    if name == "direct.hf.turbo_page_get":
        return _turbo_page_get(ctx, args)

    # ─── NEW TOOLS BATCH: Video presets ────────────────────────────────
    if name == "direct.hf.video_presets":
        return _video_presets(ctx, args)

    # ─── NEW TOOLS BATCH: Retargeting lists update ─────────────────────
    if name == "direct.hf.retargeting_lists_update":
        return _retargeting_lists_update(ctx, args)

    # Not our tool
    return None


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════

def _dedupe_ints(items: list[int]) -> list[int]:
    seen: set[int] = set()
    result: list[int] = []
    for x in items:
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result


def _b64encode(obj: dict[str, Any]) -> str:
    raw = json.dumps(obj, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(text: str) -> dict[str, Any]:
    padded = text + "=" * (-len(text) % 4)
    raw = base64.urlsafe_b64decode(padded.encode("ascii"))
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise HFError("plan_id must decode to a JSON object")
    return data


# ═══════════════════════════════════════════════════════════════════════
# Video
# ═══════════════════════════════════════════════════════════════════════

def _video_list(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """List uploaded videos."""
    params: dict[str, Any] = {}
    video_ids = args.get("video_ids")
    if video_ids:
        params["SelectionCriteria"] = {"Ids": video_ids}
    params["FieldNames"] = args.get("field_names") or ["Id", "Name"]
    result = ctx._direct_raw_post("json/v5/video", {"method": "get", "params": params})
    return {"videos": result.get("result", {}).get("Videos", [])}


def _video_upload(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Upload a video file to Yandex Direct (base64-encoded)."""
    file_path = args.get("file_path")
    if not file_path:
        raise HFError("file_path is required")
    name = args.get("name") or file_path.rsplit("/", 1)[-1]
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode("ascii")
    payload = {
        "Video": {
            "Name": name,
            "VideoSource": {"Type": "FILE", "VideoFile": b64},
        }
    }
    result = ctx._direct_raw_post("json/v5/video", {"method": "add", "params": payload})
    return {"result": result.get("result", {}), "errors": result.get("error", {}).get("Errors", [])}


# ════════════════════════��══════════════════════════════════════════════
# Feeds (v501)
# ═══════════════════════════════════════════════════════════════════════

def _feed_list(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """List feeds."""
    params: dict[str, Any] = {}
    feed_ids = args.get("feed_ids")
    if feed_ids:
        params["SelectionCriteria"] = {"Ids": feed_ids}
    params["FieldNames"] = ["Id", "Name", "BusinessType", "SourceType", "Status", "UpdatedAt"]
    result = ctx._direct_v501_call("feeds", "get", params)
    return {"feeds": result.get("result", {}).get("Feeds", [])}


def _feed_create(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Create a feed."""
    business_type = args.get("business_type", "RETAIL")
    name = args.get("name")
    url = args.get("url")
    if not name or not url:
        raise HFError("name and url are required")
    payload: dict[str, Any] = {
        "Feeds": [{
            "Name": name,
            "BusinessType": business_type,
            "FeedType": "YML_VENDOR_MODEL",
            "FeedUrl": url,
        }]
    }
    if args.get("login") and args.get("password"):
        payload["Feeds"][0]["Auth"] = {"Login": args["login"], "Password": args["password"]}
    if args.get("remove_utm_tags"):
        payload["Feeds"][0]["RemoveUtmTags"] = args["remove_utm_tags"]
    result = ctx._direct_v501_call("feeds", "add", payload)
    return {"result": result.get("result", {}), "errors": result.get("error", {}).get("Errors", [])}


def _feed_delete(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Delete feeds."""
    feed_ids = args.get("feed_ids")
    if not feed_ids:
        raise HFError("feed_ids are required")
    params = {"SelectionCriteria": {"Ids": feed_ids}}
    result = ctx._direct_v501_call("feeds", "delete", params)
    return {"result": result.get("result", {})}


def _feed_update(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Update a feed."""
    feed_id = args.get("feed_id")
    if not feed_id:
        raise HFError("feed_id is required")
    patch: dict[str, Any] = {"Id": feed_id}
    if args.get("name"):
        patch["Name"] = args["name"]
    if args.get("url"):
        patch["FeedUrl"] = args["url"]
    if args.get("login") and args.get("password"):
        patch["Auth"] = {"Login": args["login"], "Password": args["password"]}
    payload = {"Feeds": [patch]}
    result = ctx._direct_v501_call("feeds", "update", payload)
    return {"result": result.get("result", {}), "errors": result.get("error", {}).get("Errors", [])}


# ═══════════════════════════════════════════════════════════════════════
# Smart targets (v501)
# ═══════════════════════════════════════════════════════════════════════

def _smart_target_list(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """List smart ad targets."""
    params: dict[str, Any] = {}
    sc: dict[str, Any] = {}
    if args.get("campaign_ids"):
        sc["CampaignIds"] = args["campaign_ids"]
    if args.get("adgroup_ids"):
        sc["AdGroupIds"] = args["adgroup_ids"]
    if args.get("target_ids"):
        sc["Ids"] = args["target_ids"]
    params["SelectionCriteria"] = sc or {}
    params["FieldNames"] = ["Id", "Name", "AdGroupId", "CampaignId", "State", "Conditions"]
    result = ctx._direct_v501_call("smartadtargets", "get", params)
    return {"targets": result.get("result", {}).get("SmartAdTargets", [])}


def _smart_target_create(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Create a smart ad target."""
    adgroup_id = args.get("adgroup_id")
    name = args.get("name")
    if not adgroup_id or not name:
        raise HFError("adgroup_id and name are required")
    payload: dict[str, Any] = {
        "SmartAdTargets": [{
            "AdGroupId": adgroup_id,
            "Name": name,
        }]
    }
    if args.get("available_items_only"):
        payload["SmartAdTargets"][0]["AvailableItemsOnly"] = args["available_items_only"]
    if args.get("conditions"):
        payload["SmartAdTargets"][0]["Conditions"] = args["conditions"]
    result = ctx._direct_v501_call("smartadtargets", "add", payload)
    return {"result": result.get("result", {}), "errors": result.get("error", {}).get("Errors", [])}


def _smart_target_action(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Suspend, resume, or delete smart ad targets."""
    target_ids = args.get("target_ids")
    action = args.get("action")
    if not target_ids or not action:
        raise HFError("target_ids and action (suspend|resume|delete) are required")
    method_map = {"suspend": "suspend", "resume": "resume", "delete": "delete"}
    method = method_map.get(action)
    if not method:
        raise HFError(f"Unknown action: {action}. Use suspend|resume|delete")
    params = {"SelectionCriteria": {"Ids": target_ids}}
    result = ctx._direct_v501_call("smartadtargets", method, params)
    return {"result": result.get("result", {})}


# ═══════════════════════════════════════════════════════════════════════
# Businesses (organization profiles)
# ═══════════════════════════════════════════════════════════════════════

def _businesses_get(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Get organization profiles from Yandex Business."""
    ids = args.get("ids")
    if not ids:
        raise HFError("ids are required")
    params = {
        "SelectionCriteria": {"Ids": ids},
        "FieldNames": ["Id", "Name", "Type", "Address", "Phone", "ProfileUrl", "Rubric"],
    }
    result = ctx._direct_v501_call("businesses", "get", params)
    return {"businesses": result.get("result", {}).get("Businesses", [])}


# ═══════════════════════════════════════════════════════════════════════
# Creatives (video extensions)
# ═══════════════════════════════════════════════════════════════════════

def _creative_add(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Create a video extension creative."""
    video_id = args.get("video_id")
    if not video_id:
        raise HFError("video_id is required")
    payload = {"Creative": {"Type": "VIDEO_EXTENSION", "VideoExtension": {"VideoId": video_id}}}
    result = ctx._direct_v501_call("creatives", "add", payload)
    return {"result": result.get("result", {})}


def _creative_list(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """List creatives."""
    params: dict[str, Any] = {}
    ids = args.get("creative_ids")
    sc: dict[str, Any] = {"Ids": ids} if ids else {"Ids": []}
    if args.get("types"):
        sc["Types"] = args["types"]
    params["SelectionCriteria"] = sc
    params["FieldNames"] = ["Id", "Type", "Name", "PreviewUrl", "Associated", "IsAdaptive"]
    result = ctx._direct_v501_call("creatives", "get", params)
    return {"creatives": result.get("result", {}).get("Creatives", [])}


# ═══════════════════════════════════════════════════════════════════════
# VCards
# ════════════════════��══════════════════════════════════════════════════

def _vcard_create(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Create a VCard (business card) for a campaign."""
    campaign_id = args.get("campaign_id")
    country = args.get("country")
    city = args.get("city")
    company = args.get("company")
    phone = args.get("phone_number")
    if not all([campaign_id, country, city, company, phone]):
        raise HFError("campaign_id, country, city, company, phone_number are required")
    vcard_data: dict[str, Any] = {
        "CampaignId": campaign_id,
        "Country": country,
        "City": city,
        "CompanyName": company,
        "Phone": {"CountryCode": "7", "CityCode": args.get("city_code") or "", "PhoneNumber": phone},
    }
    if args.get("street"):
        vcard_data["Street"] = args["street"]
    if args.get("house"):
        vcard_data["House"] = args["house"]
    if args.get("work_time"):
        vcard_data["WorkTime"] = args["work_time"]
    if args.get("extra_message"):
        vcard_data["ExtraMessage"] = args["extra_message"]
    payload = {"VCards": [vcard_data]}
    result = ctx._direct_v501_call("vcards", "add", payload)
    return {"result": result.get("result", {})}


def _vcard_list(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """List VCards."""
    params: dict[str, Any] = {}
    ids = args.get("vcard_ids")
    if ids:
        params["SelectionCriteria"] = {"Ids": ids}
    params["FieldNames"] = ["Id", "CampaignId", "CompanyName", "Phone"]
    result = ctx._direct_v501_call("vcards", "get", params)
    return {"vcards": result.get("result", {}).get("VCards", [])}


def _vcard_delete(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Delete VCards."""
    vcard_ids = args.get("vcard_ids")
    if not vcard_ids:
        raise HFError("vcard_ids are required")
    params = {"SelectionCriteria": {"Ids": vcard_ids}}
    result = ctx._direct_v501_call("vcards", "delete", params)
    return {"result": result.get("result", {})}


# ═══════════════════════════════════════════════════════════════════════
# Blocked IPs / Excluded sites
# ═══════════════════════════════════════════════════════════════════════

def _blocked_ips_update(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Set blocked IPs for a campaign (max 25)."""
    campaign_id = args.get("campaign_id")
    ips = args.get("ips")
    if not campaign_id or ips is None:
        raise HFError("campaign_id and ips are required")
    payload = {
        "Campaigns": [{
            "Id": campaign_id,
            "BlockedIps": {"Items": ips},
        }]
    }
    result = ctx._direct_call("campaigns", "update", payload)
    return {"result": result.get("result", {})}


def _excluded_sites_get(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Get excluded sites (blocked placements) for a campaign."""
    campaign_id = args.get("campaign_id")
    if not campaign_id:
        raise HFError("campaign_id is required")
    params = {"SelectionCriteria": {"Ids": [campaign_id]}, "FieldNames": ["Id", "ExcludedSites"]}
    result = ctx._direct_call("campaigns", "get", params)
    camps = result.get("result", {}).get("Campaigns", [])
    sites = camps[0].get("ExcludedSites", []) if camps else []
    return {"campaign_id": campaign_id, "excluded_sites": sites}


def _excluded_sites_update(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Set excluded sites for a campaign."""
    campaign_id = args.get("campaign_id")
    sites = args.get("sites")
    if not campaign_id or sites is None:
        raise HFError("campaign_id and sites are required")
    payload = {
        "Campaigns": [{
            "Id": campaign_id,
            "ExcludedSites": {"Items": sites},
        }]
    }
    result = ctx._direct_call("campaigns", "update", payload)
    return {"result": result.get("result", {})}


# ═══════════════════════════════════════════════════════════════════════
# Minus-phrases sets (shared negative keyword sets)
# ═══════════════════════════════════════════════════════════════════════

def _neg_keyword_set_create(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Create a shared negative keyword set."""
    name = args.get("name")
    keywords = args.get("negative_keywords")
    if not name or not keywords:
        raise HFError("name and negative_keywords are required")
    payload = {"NegativeKeywordSets": [{"Name": name, "NegativeKeywords": {"Items": keywords}}]}
    result = ctx._direct_v501_call("negativekeywordsets", "add", payload)
    return {"result": result.get("result", {})}


def _neg_keyword_set_list(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """List shared negative keyword sets."""
    params: dict[str, Any] = {}
    ids = args.get("ids")
    if ids:
        params["SelectionCriteria"] = {"Ids": ids}
    params["FieldNames"] = ["Id", "Name", "NegativeKeywords"]
    result = ctx._direct_v501_call("negativekeywordsets", "get", params)
    return {"sets": result.get("result", {}).get("NegativeKeywordSets", [])}


def _neg_keyword_set_update(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Update a shared negative keyword set."""
    set_id = args.get("id")
    if not set_id:
        raise HFError("id is required")
    patch: dict[str, Any] = {"Id": set_id}
    if args.get("name"):
        patch["Name"] = args["name"]
    if args.get("negative_keywords"):
        patch["NegativeKeywords"] = {"Items": args["negative_keywords"]}
    payload = {"NegativeKeywordSets": [patch]}
    result = ctx._direct_v501_call("negativekeywordsets", "update", payload)
    return {"result": result.get("result", {})}


def _neg_keyword_set_delete(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Delete shared negative keyword sets."""
    ids = args.get("ids")
    if not ids:
        raise HFError("ids are required")
    params = {"SelectionCriteria": {"Ids": ids}}
    result = ctx._direct_v501_call("negativekeywordsets", "delete", params)
    return {"result": result.get("result", {})}


# ═══════════════════════════════════════════════════════════════════════
# Keyword tools
# ═══════════════════════════════════════════════════════════════════════

def _keyword_bids_set_auto(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Set automatic bidding for keywords by target position."""
    bids = args.get("bids")
    if not bids:
        raise HFError("bids array is required")
    payload = {"KeywordBids": []}
    for bid in bids:
        item: dict[str, Any] = {"KeywordId": bid["keyword_id"]}
        if bid.get("position"):
            item["AuctionBids"] = [{"Position": bid["position"], "Scope": bid.get("scope", "SEARCH_AND_NETWORK")}]
            if bid.get("max_bid"):
                item["AuctionBids"][0]["MaxBid"] = bid["max_bid"]
            if bid.get("increase_percent"):
                item["AuctionBids"][0]["IncreasePercent"] = bid["increase_percent"]
        payload["KeywordBids"].append(item)
    result = ctx._direct_v501_call("bids", "setAuto", payload)
    return {"result": result.get("result", {})}


def _keywords_has_volume(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Check if keywords have search volume in regions."""
    keywords = args.get("keywords")
    region_ids = args.get("region_ids")
    if not keywords or not region_ids:
        raise HFError("keywords and region_ids are required")
    params = {
        "SelectionCriteria": {"RegionIds": region_ids},
        "Keywords": keywords,
        "FieldNames": ["Keyword", "RegionIds", "SearchedRecently"],
    }
    result = ctx._direct_v501_call("keywordbids", "get", params)
    items = result.get("result", {}).get("KeywordBidItems", [])
    return {"results": items}


def _keywords_research(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Deduplicate keywords: merge duplicates, eliminate overlapping."""
    keywords = args.get("keywords")
    operations = args.get("operations", ["MERGE_DUPLICATES", "ELIMINATE_OVERLAPPING"])
    if not keywords:
        raise HFError("keywords are required")
    params = {"Keywords": keywords, "Operations": operations}
    result = ctx._direct_v501_call("keywordbids", "deduplicate", params)
    return {"result": result.get("result", {})}


# ═══════════════════════════════════════════════════════════════════════
# Bid modifiers
# ═══════════════════════════════════════════════════════════════════════

def _bid_modifiers_toggle(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Enable or disable bid modifiers."""
    modifier_ids = args.get("bid_modifier_ids")
    enabled = args.get("enabled")
    if not modifier_ids or enabled is None:
        raise HFError("bid_modifier_ids and enabled are required")
    payload = {
        "BidModifiers": [{"Id": mid, "Enabled": bool(enabled)} for mid in modifier_ids]
    }
    result = ctx._direct_call("bidmodifiers", "set", payload)
    return {"result": result.get("result", {})}


# ═══════════════════════════════════════════════════════════════════════
# Callouts link
# ═══════════════════════════════════════════════════════════════════════

def _callouts_link(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Link callout extensions to an ad."""
    ad_id = args.get("ad_id")
    callout_ids = args.get("callout_ids")
    if not ad_id or not callout_ids:
        raise HFError("ad_id and callout_ids are required")
    payload = {
        "Ads": [{
            "Id": ad_id,
            "TextAd": {"AdExtensions": {"CalloutExtensionIds": callout_ids}},
        }]
    }
    result = ctx._direct_call("ads", "update", payload)
    return {"result": result.get("result", {})}


# ═══════════════════════════════════════════════════════════════════════
# Dynamic / Image / Shopping ads
# ═══════════════════════════════════════════════════════════════════════

def _create_dynamic_ads(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Create dynamic text ads."""
    ads = args.get("ads", [])
    if not ads:
        raise HFError("ads array is required")
    payload = {"Ads": []}
    for a in ads:
        ad = {
            "AdGroupId": a["ad_group_id"],
            "DynamicTextAd": {
                "Text": a.get("text", ""),
                "Href": a.get("href", ""),
            },
        }
        if a.get("title"):
            ad["DynamicTextAd"]["Title"] = a["title"]
        if a.get("sitelink_set_id"):
            ad["DynamicTextAd"]["SitelinkSetId"] = a["sitelink_set_id"]
        payload["Ads"].append(ad)
    result = ctx._direct_call("ads", "add", payload)
    return {"result": result.get("result", {}), "errors": result.get("error", {}).get("Errors", [])}


def _create_image_ads(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Create image/text-image ads."""
    ads = args.get("ads", [])
    if not ads:
        raise HFError("ads array is required")
    payload = {"Ads": []}
    for a in ads:
        ad = {
            "AdGroupId": a["ad_group_id"],
        }
        if a.get("title") and a.get("href") and a.get("ad_image_hash"):
            # Image-ad (with text overlay)
            ad["TextAd"] = {
                "Title": a["title"],
                "Text": a.get("text", ""),
                "Href": a["href"],
                "AdImageHash": a["ad_image_hash"],
            }
            if a.get("title2"):
                ad["TextAd"]["Title2"] = a["title2"]
        elif a.get("ad_image_hash"):
            # Pure image ad (CMBanner)
            ad["TextAd"] = {"AdImageHash": a["ad_image_hash"]}
        payload["Ads"].append(ad)
    result = ctx._direct_call("ads", "add", payload)
    return {"result": result.get("result", {}), "errors": result.get("error", {}).get("Errors", [])}


def _create_shopping_ads(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Create shopping ads."""
    ads = args.get("ads", [])
    if not ads:
        raise HFError("ads array is required")
    payload = {"Ads": []}
    for a in ads:
        ad = {
            "AdGroupId": a["ad_group_id"],
            "ShoppingAd": {"Title": a.get("title", "")},
        }
        if a.get("sitelink_set_id"):
            ad["ShoppingAd"]["SitelinkSetId"] = a["sitelink_set_id"]
        payload["Ads"].append(ad)
    result = ctx._direct_v501_call("ads", "add", payload)
    return {"result": result.get("result", {}), "errors": result.get("error", {}).get("Errors", [])}


# ═══════════════════════════════════════════════════════════════════════
# Ad images
# ═══════════════════════════════════════════════════════════════════════

def _ad_images_add(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Upload ad images (base64-encoded)."""
    images = args.get("images", [])
    if not images:
        raise HFError("images array is required")
    payload = {"AdImages": [{"Name": img["name"], "ImageData": img["image_data"]} for img in images]}
    result = ctx._direct_call("adimages", "add", payload)
    return {"result": result.get("result", {}), "errors": result.get("error", {}).get("Errors", [])}


def _ad_images_get(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Get ad images by hashes or associated status."""
    params: dict[str, Any] = {}
    ids = args.get("ids")
    if ids:
        params["SelectionCriteria"] = {"Ids": ids}
    if args.get("associated"):
        params.setdefault("SelectionCriteria", {})["Associated"] = "YES"
    result = ctx._direct_call("adimages", "get", params)
    return {"images": result.get("result", {}).get("AdImages", [])}


def _ad_images_delete(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Delete ad images by hashes."""
    ids = args.get("ids")
    if not ids:
        raise HFError("ids are required")
    params = {"SelectionCriteria": {"Ids": ids}}
    result = ctx._direct_call("adimages", "delete", params)
    return {"result": result.get("result", {})}


# ═══════════════════════════════════════════════════════════════════════
# Audience targets
# ═══════════════════════════════════════════════════════════════════════

def _audience_targets_add(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Add audience targeting conditions to ad groups (retargeting lists or interests)."""
    targets = args.get("targets", [])
    if not targets:
        raise HFError("targets array is required")
    payload = {"AudienceTargets": []}
    for t in targets:
        item = {"AdGroupId": t["ad_group_id"]}
        if t.get("retargeting_list_id"):
            item["RetargetingListId"] = t["retargeting_list_id"]
        if t.get("interest_id"):
            item["InterestId"] = t["interest_id"]
        if t.get("context_bid"):
            item["ContextBid"] = int(t["context_bid"] * 1_000_000)
        if t.get("strategy_priority"):
            item["StrategyPriority"] = t["strategy_priority"]
        payload["AudienceTargets"].append(item)
    result = ctx._direct_call("audiencetargets", "add", payload)
    return {"result": result.get("result", {}), "errors": result.get("error", {}).get("Errors", [])}


def _audience_targets_get(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Get audience targets by campaign/ad group/target IDs."""
    sc: dict[str, Any] = {}
    if args.get("campaign_ids"):
        sc["CampaignIds"] = args["campaign_ids"]
    if args.get("ad_group_ids"):
        sc["AdGroupIds"] = args["ad_group_ids"]
    if args.get("ids"):
        sc["Ids"] = args["ids"]
    params = {
        "SelectionCriteria": sc or {},
        "FieldNames": ["Id", "AdGroupId", "CampaignId", "RetargetingListId", "InterestId", "ContextBid", "StrategyPriority", "State"],
    }
    result = ctx._direct_call("audiencetargets", "get", params)
    return {"targets": result.get("result", {}).get("AudienceTargets", [])}


def _audience_targets_delete(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Delete audience targeting conditions."""
    ids = args.get("ids")
    if not ids:
        raise HFError("ids are required")
    params = {"SelectionCriteria": {"Ids": ids}}
    result = ctx._direct_call("audiencetargets", "delete", params)
    return {"result": result.get("result", {})}


# ═══════════════════════════════════════════════════════════════════════
# Retargeting lists
# ═══════════════════════════════════════════════════════════════════════

def _retargeting_lists_add(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Create retargeting/audience conditions based on Metrika goals or audience segments."""
    name = args.get("name")
    rules = args.get("rules", [])
    if not name or not rules:
        raise HFError("name and rules are required")
    payload_rules = []
    for r in rules:
        rule = {"Operator": r["operator"], "Goals": []}
        for g in r.get("goals", []):
            rule["Goals"].append({"GoalId": g["goal_id"], "MembershipLifeSpan": g.get("membership_life_span", 30)})
        payload_rules.append(rule)
    payload = {
        "RetargetingLists": [{
            "Name": name,
            "Rules": payload_rules,
        }]
    }
    if args.get("description"):
        payload["RetargetingLists"][0]["Description"] = args["description"]
    result = ctx._direct_v501_call("retargetinglists", "add", payload)
    return {"result": result.get("result", {}), "errors": result.get("error", {}).get("Errors", [])}


def _retargeting_lists_get(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Get retargeting lists."""
    params: dict[str, Any] = {}
    ids = args.get("ids")
    if ids:
        params["SelectionCriteria"] = {"Ids": ids}
    result = ctx._direct_v501_call("retargetinglists", "get", params)
    return {"lists": result.get("result", {}).get("RetargetingLists", [])}


def _retargeting_lists_delete(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Delete retargeting lists."""
    ids = args.get("ids")
    if not ids:
        raise HFError("ids are required")
    params = {"SelectionCriteria": {"Ids": ids}}
    result = ctx._direct_v501_call("retargetinglists", "delete", params)
    return {"result": result.get("result", {})}


# ═══════════════════════════════════════════════════════════════════════
# Sitelinks delete
# ═══════════════════════════════════════════════════════════════════════

def _sitelinks_delete(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Delete sitelinks sets."""
    ids = args.get("ids")
    if not ids:
        raise HFError("ids are required")
    params = {"SelectionCriteria": {"Ids": ids}}
    result = ctx._direct_call("sitelinks", "delete", params)
    return {"result": result.get("result", {})}


# ═══════════════════════════════════════════════════════════════════════
# Ad extensions get/delete
# ═══════════════════════════════════════════════════════════════════════

def _ad_extensions_get(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Get ad extensions by IDs."""
    ids = args.get("ids")
    if not ids:
        raise HFError("ids are required")
    params = {"SelectionCriteria": {"Ids": ids}, "FieldNames": ["Id", "Type", "Callout", "Status"]}
    result = ctx._direct_call("adextensions", "get", params)
    return {"extensions": result.get("result", {}).get("AdExtensions", [])}


def _ad_extensions_delete(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Delete ad extensions."""
    ids = args.get("ids")
    if not ids:
        raise HFError("ids are required")
    params = {"SelectionCriteria": {"Ids": ids}}
    result = ctx._direct_call("adextensions", "delete", params)
    return {"result": result.get("result", {})}


# ═══════════════════════════════════════════════════════════════════════
# Interests dictionary
# ═══════════════════════════════════════════════════════════════════════

def _interests_get(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Get interest categories (for mobile app targeting)."""
    params = {"DictionaryNames": ["Interests"]}
    result = ctx._direct_call("dictionaries", "get", params)
    return {"interests": result.get("result", {}).get("Interests", [])}


# ═══════════════════════════════════════════════════════════════════════
# NEW TOOLS BATCH — создание кампании
# ═══════════════════════════════════════════════════════════════════════

def _create_campaign(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Create a campaign from scratch."""
    from .hf_common import micros_from_rub

    name = args.get("name")
    if not name:
        raise HFError("name is required")

    # Determine campaign type
    ctype = args.get("type", "TEXT_CAMPAIGN")  # TEXT_CAMPAIGN, SMART_CAMPAIGN, etc.

    # Build base campaign
    campaign: dict[str, Any] = {"Name": name}

    # Daily budget (in rubles -> micros)
    daily_budget_rub = args.get("daily_budget_rub")
    if daily_budget_rub is not None:
        campaign["DailyBudget"] = micros_from_rub(daily_budget_rub)

    # Strategy
    strategy = args.get("strategy")
    if strategy:
        strategy_type = strategy.get("type", "WB_MAXIMUM_CONVERSION_RATE")
        campaign["BiddingStrategy"] = {
            "Search": {"BiddingStrategyType": strategy_type}
        }
        weekly_limit = strategy.get("weekly_spend_limit_rub")
        if weekly_limit:
            campaign["BiddingStrategy"]["Search"]["WeeklySpendLimit"] = micros_from_rub(weekly_limit)
        avg_cpc = strategy.get("avg_cpc_rub")
        if avg_cpc:
            campaign["BiddingStrategy"]["Search"]["AvgCpc"] = micros_from_rub(avg_cpc)

    # Regions
    region_ids = args.get("region_ids")
    if region_ids:
        campaign["RegionIds"] = region_ids

    # Start date
    start_date = args.get("start_date")
    if start_date:
        campaign["StartDate"] = start_date

    # UTM template
    utm_template = args.get("utm_template")
    if utm_template:
        campaign["TrackingParams"] = utm_template

    # Wrap in type-specific container
    if ctype == "SMART_CAMPAIGN":
        payload = {"SmartCampaigns": [campaign]}
        result = ctx._direct_v501_call("campaigns", "add", payload)
    elif ctype == "UNIFIED_CAMPAIGN":
        payload = {"UnifiedCampaigns": [campaign]}
        result = ctx._direct_v501_call("campaigns", "add", payload)
    else:
        # TEXT_CAMPAIGN (default)
        payload = {"TextCampaigns": [campaign]}
        result = ctx._direct_call("campaigns", "add", payload)

    return {"result": result.get("result", {}), "errors": result.get("error", {}).get("Errors", [])}


# ═══════════════════════════════════════════════════════════════════════
# NEW TOOLS BATCH — комбинаторные объявления (ContentBlocks)
# ═══════════════════════════════════════════════════════════════════════

def _create_textads_combinator(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Create text ads using modern ContentBlocks format (combinator ads).

    Blocks format:
    [
      {"type": "TEXT", "content": "Заголовок"},
      {"type": "TEXT", "content": "Подзаголовок"},
      {"type": "TEXT", "content": "Текст"},
      {"type": "MEDIA", "media_type": "IMAGE", "ad_image_hash": "..."},
    ]
    """
    ad_group_id = args.get("ad_group_id")
    blocks = args.get("blocks")
    href = args.get("href")
    if not ad_group_id or not blocks or not href:
        raise HFError("ad_group_id, blocks, and href are required")

    content_blocks = []
    for b in blocks:
        block_type = b.get("type")
        if block_type == "TEXT":
            content_blocks.append({
                "BlockType": "TEXT",
                "TextProperty": {"Append": b["content"]}
            })
        elif block_type == "MEDIA":
            media_type = b.get("media_type", "IMAGE")
            media_block = {
                "BlockType": "MEDIA",
                "MediaBlockProperty": {"MediaType": media_type}
            }
            if media_type == "IMAGE" and b.get("ad_image_hash"):
                media_block["MediaBlockProperty"]["AdImageHash"] = b["ad_image_hash"]
            elif media_type == "VIDEO" and b.get("creative_id"):
                media_block["MediaBlockProperty"]["CreativeId"] = b["creative_id"]
            content_blocks.append(media_block)
        elif block_type == "BUTTON":
            content_blocks.append({
                "BlockType": "BUTTON",
                "ButtonProperty": {"Text": b.get("text", "Подробнее"), "Href": b.get("href", href)}
            })

    ad: dict[str, Any] = {"AdGroupId": ad_group_id, "TextAd": {"ContentBlocks": content_blocks, "Href": href}}

    # Attach sitelinks/callouts
    sitelink_set_id = args.get("sitelink_set_id")
    if sitelink_set_id:
        ad["TextAd"]["SitelinkSetId"] = sitelink_set_id
    callout_ids = args.get("callout_ids")
    if callout_ids:
        ad["TextAd"]["AdExtensions"] = {"AdExtensionIds": callout_ids}

    payload = {"Ads": [ad]}
    result = ctx._direct_call("ads", "add", payload)
    return {"result": result.get("result", {}), "errors": result.get("error", {}).get("Errors", [])}


# ═══════════════════════════════════════════════════════════════════════
# NEW TOOLS BATCH — лиды (leads)
# ═══════════════════════════════════════════════════════════════════════

def _get_leads(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Get leads from lead-based campaigns."""
    campaign_id = args.get("campaign_id")
    if not campaign_id:
        raise HFError("campaign_id is required")
    params: dict[str, Any] = {
        "SelectionCriteria": {"CampaignIds": [campaign_id]},
        "FieldNames": [
            "Id", "CampaignId", "SubmitTime", "TurboPageId",
            "Contacts", "UtmParameters", "State"
        ],
    }
    date_from = args.get("date_from")
    date_to = args.get("date_to")
    if date_from and date_to:
        params["SelectionCriteria"]["DateFrom"] = date_from
        params["SelectionCriteria"]["DateTo"] = date_to
    limit = args.get("limit", 50)
    offset = args.get("offset", 0)
    params["Page"] = {"Limit": limit, "Offset": offset}
    result = ctx._direct_v501_call("leads", "get", params)
    return {"leads": result.get("result", {}).get("Leads", []), "total": result.get("result", {}).get("TotalCount", 0)}


# ═══════════════════════════════════════════════════════════════════════
# NEW TOOLS BATCH — creatives update/delete
# ═══════════════════════════════════════════════════════════════════════

def _creative_update(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Update a creative (video extension)."""
    creative_id = args.get("creative_id")
    if not creative_id:
        raise HFError("creative_id is required")
    patch_data: dict[str, Any] = {"Id": creative_id}
    if args.get("video_id"):
        patch_data["VideoExtension"] = {"VideoId": args["video_id"]}
    if args.get("name"):
        patch_data["Name"] = args["name"]
    payload = {"Creatives": [patch_data]}
    result = ctx._direct_v501_call("creatives", "update", payload)
    return {"result": result.get("result", {})}


def _creative_delete(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Delete creatives."""
    creative_ids = args.get("creative_ids")
    if not creative_ids:
        raise HFError("creative_ids are required")
    params = {"SelectionCriteria": {"Ids": creative_ids}}
    result = ctx._direct_v501_call("creatives", "delete", params)
    return {"result": result.get("result", {})}


# ═══════════════════════════════════════════════════════════════════════
# NEW TOOLS BATCH — video delete
# ═══════════════════════════════════════════════════════════════════════

def _video_delete(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Delete uploaded videos."""
    video_ids = args.get("video_ids")
    if not video_ids:
        raise HFError("video_ids are required")
    params = {"SelectionCriteria": {"Ids": video_ids}}
    result = ctx._direct_raw_post("json/v5/video", {"method": "delete", "params": params})
    return {"result": result.get("result", {})}


# ═══════════════════════════════════════════════════════════════════════
# NEW TOOLS BATCH — keywords resume/update
# ═══════════════════════════════════════════════════════════════════════

def _keywords_resume(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Resume auto-paused keywords."""
    keyword_ids = args.get("keyword_ids")
    if not keyword_ids:
        raise HFError("keyword_ids are required")
    params = {"SelectionCriteria": {"Ids": keyword_ids}}
    result = ctx._direct_call("keywords", "resume", params)
    return {"result": result.get("result", {})}


def _update_keywords(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Update keyword properties (text, bid, priority)."""
    from .hf_common import micros_from_rub

    keyword_id = args.get("keyword_id")
    if not keyword_id:
        raise HFError("keyword_id is required")
    patch_data: dict[str, Any] = {"Id": keyword_id}
    if args.get("keyword"):
        patch_data["Keyword"] = args["keyword"]
    bid_rub = args.get("bid_rub")
    if bid_rub is not None:
        patch_data["Bid"] = micros_from_rub(bid_rub)
        patch_data["ContextBid"] = micros_from_rub(bid_rub)
    if args.get("strategy_priority"):
        patch_data["StrategyPriority"] = args["strategy_priority"]
    payload = {"Keywords": [patch_data]}
    result = ctx._direct_call("keywords", "update", payload)
    return {"result": result.get("result", {}), "warnings": result.get("error", {}).get("Warnings", [])}


# ═══════════════════════════════════════════════════════════════════════
# NEW TOOLS BATCH — audience targets setBids
# ═══════════════════════════════════════════════════════════════════════

def _audience_targets_set_bids(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Set bids on audience targets."""
    from .hf_common import micros_from_rub

    bids = args.get("bids")
    if not bids:
        raise HFError("bids are required")
    api_bids = []
    for b in bids:
        target_id = b.get("target_id")
        if not target_id:
            raise HFError("Each bid must have target_id")
        bid_entry: dict[str, Any] = {"Id": target_id}
        context_bid = b.get("context_bid")
        if context_bid is not None:
            bid_entry["ContextBid"] = micros_from_rub(context_bid)
        api_bids.append(bid_entry)
    params = {"Bids": api_bids}
    result = ctx._direct_call("audiencetargets", "setBids", params)
    return {"result": result.get("result", {})}


# ═══════════════════════════════════════════════════════════════════════
# NEW TOOLS BATCH — vcard update
# ═══════════════════════════════════════════════════════════════════════

def _vcard_update(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Update a VCard."""
    vcard_id = args.get("vcard_id")
    if not vcard_id:
        raise HFError("vcard_id is required")
    patch_data: dict[str, Any] = {"Id": vcard_id}
    if args.get("company"):
        patch_data["CompanyName"] = args["company"]
    if args.get("phone_number"):
        patch_data["Phone"] = {
            "CountryCode": args.get("country_code", "7"),
            "CityCode": args.get("city_code", ""),
            "PhoneNumber": args["phone_number"]
        }
    if args.get("street"):
        patch_data["Street"] = args["street"]
    if args.get("house"):
        patch_data["House"] = args["house"]
    if args.get("work_time"):
        patch_data["WorkTime"] = args["work_time"]
    if args.get("extra_message"):
        patch_data["ExtraMessage"] = args["extra_message"]
    payload = {"VCards": [patch_data]}
    result = ctx._direct_v501_call("vcards", "update", payload)
    return {"result": result.get("result", {})}


# ═══════════════════════════════════════════════════════════════════════
# NEW TOOLS BATCH — sitelinks update
# ═══════════════════════════════════════════════════════════════════════

def _sitelinks_update(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Update a sitelinks set."""
    sitelinks_set_id = args.get("sitelinks_set_id")
    sitelinks = args.get("sitelinks")
    if not sitelinks_set_id or not sitelinks:
        raise HFError("sitelinks_set_id and sitelinks are required")
    api_sitelinks = []
    for sl in sitelinks:
        if not sl.get("title") or not sl.get("href"):
            raise HFError("Each sitelink must have title and href")
        api_sitelinks.append({"Title": sl["title"], "Href": sl["href"]})
    payload = {"SitelinksSets": [{"Id": sitelinks_set_id, "Sitelinks": api_sitelinks}]}
    result = ctx._direct_call("sitelinks", "update", payload)
    return {"result": result.get("result", {})}


# ═══════════════════════════════════════════════════════════════════════
# NEW TOOLS BATCH — video extension add (adextensions)
# ═══════════════════════════════════════════════════════════════════════

def _video_extension_add(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Add a VIDEO_EXTENSION ad extension to a campaign."""
    campaign_id = args.get("campaign_id")
    creative_id = args.get("creative_id")
    if not campaign_id or not creative_id:
        raise HFError("campaign_id and creative_id are required")
    payload = {
        "AdExtensions": [{
            "CampaignId": campaign_id,
            "Type": "VIDEO_EXTENSION",
            "VideoExtension": {"CreativeId": creative_id}
        }]
    }
    result = ctx._direct_call("adextensions", "add", payload)
    return {"result": result.get("result", {})}


# ═══════════════════════════════════════════════════════════════════════
# NEW TOOLS BATCH — card extensions
# ═══════════════════════════════════════════════════════════════════════

def _card_extension_add(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Add card extension (EXTENDED_TEXT) to a campaign."""
    campaign_id = args.get("campaign_id")
    cards = args.get("cards")
    if not campaign_id or not cards:
        raise HFError("campaign_id and cards are required")
    items = []
    for card in cards:
        c: dict[str, Any] = {
            "Title": card["title"],
            "Description": card.get("description", ""),
            "Href": card["href"],
        }
        if card.get("price"):
            c["Price"] = card["price"]
        items.append(c)
    payload = {
        "AdExtensions": [{
            "CampaignId": campaign_id,
            "Type": "EXTENDED_TEXT",
            "ExtendedText": {"Items": items}
        }]
    }
    result = ctx._direct_call("adextensions", "add", payload)
    return {"result": result.get("result", {})}


def _card_extension_delete(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Delete card (EXTENDED_TEXT) extensions by IDs."""
    extension_ids = args.get("extension_ids")
    if not extension_ids:
        raise HFError("extension_ids are required")
    params = {"SelectionCriteria": {"Ids": extension_ids}}
    result = ctx._direct_call("adextensions", "delete", params)
    return {"result": result.get("result", {})}


# ═══════════════════════════════════════════════════════════════════════
# NEW TOOLS BATCH — client update (agency)
# ═══════════════════════════════════════════════════════════════════════

def _client_update(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Update client info (agency operation)."""
    client_id = args.get("client_id")
    if not client_id:
        raise HFError("client_id is required")
    patch_data: dict[str, Any] = {"ClientId": client_id}
    if args.get("phone"):
        patch_data["Phone"] = args["phone"]
    if args.get("email"):
        patch_data["Email"] = args["email"]
    payload = {"Clients": [patch_data]}
    result = ctx._direct_call("clients", "update", payload)
    return {"result": result.get("result", {})}


# ═══════════════════════════════════════════════════════════════════════
# NEW TOOLS BATCH — turbo pages
# ═══════════════════════════════════════════════════════════════════════

def _turbo_pages_list(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """List turbo landing pages."""
    params: dict[str, Any] = {}
    campaign_id = args.get("campaign_id")
    if campaign_id:
        params["SelectionCriteria"] = {"CampaignIds": [campaign_id]}
    limit = args.get("limit", 50)
    offset = args.get("offset", 0)
    params["Page"] = {"Limit": limit, "Offset": offset}
    params["FieldNames"] = ["Id", "CampaignId", "Name", "Domain", "Status", "Href", "ModerationStatus"]
    result = ctx._direct_v501_call("turbolandingpages", "list", params)
    return {"pages": result.get("result", {}).get("TurboLandingPages", [])}


def _turbo_page_get(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Get a single turbo landing page by ID."""
    page_id = args.get("page_id")
    if not page_id:
        raise HFError("page_id is required")
    params = {
        "SelectionCriteria": {"Ids": [page_id]},
        "FieldNames": [
            "Id", "CampaignId", "Name", "Domain", "Status",
            "Href", "ModerationStatus", "ModerationRejectionDescription"
        ],
    }
    result = ctx._direct_v501_call("turbolandingpages", "get", params)
    return {"page": result.get("result", {}).get("TurboLandingPages", [])}


# ═══════════════════════════════════════════════════════════════════════
# NEW TOOLS BATCH — video presets
# ═══════════════════════════════════════════════════════════════════════

def _video_presets(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Get video presets (supported formats, sizes)."""
    params = {"FieldNames": ["Id", "Name", "Type", "Params"]}
    result = ctx._direct_raw_post("json/v5/videopresets", {"method": "get", "params": params})
    return {"presets": result.get("result", {}).get("VideoPresets", [])}


# ═══════════════════════════════════════════════════════════════════════
# NEW TOOLS BATCH — retargeting lists update
# ═══════════════════════════════════════════════════════════════════════

def _retargeting_lists_update(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Update a retargeting list."""
    list_id = args.get("id")
    if not list_id:
        raise HFError("id is required")
    patch_data: dict[str, Any] = {"Id": list_id}
    if args.get("name"):
        patch_data["Name"] = args["name"]
    if args.get("description"):
        patch_data["Description"] = args["description"]
    rules = args.get("rules")
    if rules:
        payload_rules = []
        for r in rules:
            rule = {"Operator": r["operator"], "Goals": []}
            for g in r.get("goals", []):
                rule["Goals"].append({
                    "GoalId": g["goal_id"],
                    "MembershipLifeSpan": g.get("membership_life_span", 30)
                })
            payload_rules.append(rule)
        patch_data["Rules"] = payload_rules
    payload = {"RetargetingLists": [patch_data]}
    result = ctx._direct_v501_call("retargetinglists", "update", payload)
    return {"result": result.get("result", {})}
