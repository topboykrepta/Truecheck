from __future__ import annotations

from urllib.parse import urlparse

from app.models import SourceCredibility


TRUSTED_DOMAINS = {
    "reuters.com",
    "apnews.com",
    "bbc.co.uk",
    "bbc.com",
    "citizentv.co.ke",
    "ktntv.com",
    "aljazeera.com",
    "cnn.com",
    "foxnews.com",
    "kbc.co.ke",
    "ntv.co.ke",
    "who.int",
    "cdc.gov",
    "nih.gov",
    "nature.com",
    "science.org",
    "snopes.com",
    "politifact.com",
    "factcheck.org",
}

LOW_CRED_DOMAINS = {
    "beforeitsnews.com",
}


def label_credibility(url: str | None, publisher: str | None = None) -> SourceCredibility:
    if not url:
        return SourceCredibility.unknown

    host = (urlparse(url).hostname or "").lower()
    host = host.replace("www.", "")

    if host in TRUSTED_DOMAINS or any(host.endswith("." + d) for d in TRUSTED_DOMAINS):
        return SourceCredibility.trusted
    if host in LOW_CRED_DOMAINS or any(host.endswith("." + d) for d in LOW_CRED_DOMAINS):
        return SourceCredibility.low

    # Default neutral if it looks like a known publisher domain.
    if host and "." in host:
        return SourceCredibility.neutral

    return SourceCredibility.unknown
