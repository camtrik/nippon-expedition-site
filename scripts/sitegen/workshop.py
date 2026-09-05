"""The one list of Workshop listings the whole site links to."""
from __future__ import annotations


def workshop_ctas() -> list[tuple[str, str]]:
    """Every workshop listing: the mod itself, its English translation, then the
    optional submods — same order on both language pages, since the English
    listing is a translation of the first one rather than a second main mod.
    The hero CTAs and the footer row are both generated from this list, so a new
    listing only has to be added here — and to home.json's `submods` if it is a
    compatibility patch, which is the one place the copy actually differs."""
    return [
        ("WS_MAIN_ZH", "https://steamcommunity.com/workshop/filedetails/?id=3790908242"),
        ("WS_MAIN_EN", "https://steamcommunity.com/workshop/filedetails/?id=3790908523"),
        ("WS_AI", "https://steamcommunity.com/workshop/filedetails/?id=3790907897"),
        ("WS_NRS", "https://steamcommunity.com/sharedfiles/filedetails/?id=3792001152"),
        ("WS_CATHAY", "https://steamcommunity.com/sharedfiles/filedetails/?id=3792252212"),
        ("WS_YINYIN", "https://steamcommunity.com/sharedfiles/filedetails/?id=3792695478"),
        ("WS_WUH", "https://steamcommunity.com/sharedfiles/filedetails/?id=3795596611"),
    ]
