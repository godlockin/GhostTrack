"""Site catalogue for username lookup.

Each entry declares how a platform responds for a non-existent profile, so the
probe can distinguish NOT_FOUND from an inconclusive anti-bot response.
`head=True` means a HEAD request is enough; otherwise a small GET chunk is
matched against `not_found_markers`.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Site:
    name: str
    url: str  # {} is replaced by the username
    head: bool = False
    not_found_markers: tuple[str, ...] = field(default_factory=tuple)


SITES: tuple[Site, ...] = (
    Site("Facebook", "https://www.facebook.com/{}",
         not_found_markers=("page isn't available", "isn't available", "Page Not Found")),
    Site("X", "https://x.com/{}", head=True),
    Site("Instagram", "https://www.instagram.com/{}/",
         not_found_markers=("Sorry, this page isn't available.",)),
    Site("LinkedIn", "https://www.linkedin.com/in/{}", head=True),
    Site("GitHub", "https://www.github.com/{}", head=True),
    Site("Pinterest", "https://www.pinterest.com/{}/", head=True),
    Site("Tumblr", "https://{}.tumblr.com/", head=True),
    Site("YouTube", "https://www.youtube.com/@{}", head=True),
    Site("SoundCloud", "https://soundcloud.com/{}", head=True),
    Site("Snapchat", "https://www.snapchat.com/add/{}", head=True),
    Site("TikTok", "https://www.tiktok.com/@{}",
         not_found_markers=("Couldn't find this account",)),
    Site("Behance", "https://www.behance.net/{}", head=True),
    Site("Medium", "https://medium.com/@{}", head=True),
    Site("Quora", "https://www.quora.com/profile/{}", head=True),
    Site("Flickr", "https://www.flickr.com/people/{}", head=True),
    Site("Twitch", "https://www.twitch.tv/{}", head=True),
    Site("Dribbble", "https://dribbble.com/{}", head=True),
    Site("Ello", "https://ello.co/{}", head=True),
    Site("Product Hunt", "https://www.producthunt.com/@{}", head=True),
    Site("Telegram", "https://t.me/{}", head=True),
    Site("We Heart It", "https://weheartit.com/{}", head=True),
    Site("Reddit", "https://www.reddit.com/user/{}", head=True),
    Site("Steam", "https://steamcommunity.com/id/{}", head=True),
    Site("GitLab", "https://gitlab.com/{}", head=True),
    Site("Keybase", "https://keybase.io/{}", head=True),
)
