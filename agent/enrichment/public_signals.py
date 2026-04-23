from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from agent.models.schemas import ConfidenceLevel, ScoredSignal, SourceRef

try:  # pragma: no cover - optional dependency.
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - Playwright is optional in this scaffold.
    PlaywrightTimeoutError = TimeoutError
    sync_playwright = None


_COMPANY_SUFFIXES = {
    "inc",
    "incorporated",
    "corp",
    "corporation",
    "co",
    "company",
    "llc",
    "ltd",
    "limited",
    "plc",
    "gmbh",
    "ag",
}

_BLOCKED_TEXT_PATTERNS = (
    "captcha",
    "verify you are human",
    "access denied",
    "cloudflare",
    "robot check",
    "unusual traffic",
)

_FUNDING_PATTERNS = (
    re.compile(r"\bseries\s+[abc]\b", re.IGNORECASE),
    re.compile(r"\bseed round\b", re.IGNORECASE),
    re.compile(r"\braised\s+\$?\d", re.IGNORECASE),
    re.compile(r"\bfunding round\b", re.IGNORECASE),
    re.compile(r"\bbacked by\b", re.IGNORECASE),
    re.compile(r"\bvaluation\b", re.IGNORECASE),
)

_JOB_PATTERNS = (
    "engineer",
    "software",
    "data",
    "product",
    "platform",
    "machine learning",
    "ml",
    "security",
    "sales",
    "customer",
    "support",
    "designer",
    "recruiter",
)

_LEADERSHIP_PATTERNS = (
    re.compile(r"\bappointed\b", re.IGNORECASE),
    re.compile(r"\bnamed\b.*\b(ceo|cto|cfo|coo|chief)\b", re.IGNORECASE),
    re.compile(r"\bjoins as\b", re.IGNORECASE),
    re.compile(r"\bpromoted to\b", re.IGNORECASE),
    re.compile(r"\bsteps down\b", re.IGNORECASE),
    re.compile(r"\bresigns\b", re.IGNORECASE),
    re.compile(r"\bleadership\b", re.IGNORECASE),
)


def _slugify(value: str) -> str:
    tokens = re.findall(r"[a-z0-9]+", value.lower())
    tokens = [token for token in tokens if token not in _COMPANY_SUFFIXES]
    return "-".join(tokens)


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        unique_values.append(normalized)
    return unique_values


def _split_sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", cleaned) if sentence.strip()]


def _looks_blocked(text: str) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in _BLOCKED_TEXT_PATTERNS)


def _normalize_company_domain(domain: str) -> str:
    normalized = domain.strip().lower()
    if normalized.startswith("http://") or normalized.startswith("https://"):
        return normalized
    return f"https://{normalized}"


def _is_synthetic_domain(domain: str) -> bool:
    lowered = domain.lower()
    return any(token in lowered for token in (".example", "localhost", "127.0.0.1"))


def _public_source_ref(title: str, url: str, note: str) -> SourceRef:
    return SourceRef(title=title, url=url, note=note)


@dataclass(frozen=True)
class PublicPageSnapshot:
    url: str
    final_url: str
    title: str
    text: str
    links: tuple[str, ...] = ()
    link_texts: tuple[str, ...] = ()
    blocked: bool = False


class _VisibleContentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self.links: list[tuple[str, str]] = []
        self._in_title = False
        self._in_ignored_block = False
        self._current_link_href: str | None = None
        self._current_link_text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._in_ignored_block = True
        if tag == "title":
            self._in_title = True
        if tag == "a":
            attrs_map = {key: value for key, value in attrs}
            href = attrs_map.get("href")
            if href:
                self._current_link_href = href
                self._current_link_text_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            self._in_ignored_block = False
        if tag == "title":
            self._in_title = False
        if tag == "a" and self._current_link_href is not None:
            text = " ".join(part for part in self._current_link_text_parts if part).strip()
            self.links.append((self._current_link_href, text))
            self._current_link_href = None
            self._current_link_text_parts = []

    def handle_data(self, data: str) -> None:
        stripped = data.strip()
        if not stripped or self._in_ignored_block:
            return
        if self._in_title:
            self.title_parts.append(stripped)
        else:
            self.text_parts.append(stripped)
        if self._current_link_href is not None:
            self._current_link_text_parts.append(stripped)

    def build_snapshot(self, url: str, final_url: str) -> PublicPageSnapshot:
        title = " ".join(self.title_parts).strip()
        text = "\n".join(self.text_parts).strip()
        links: list[str] = []
        link_texts: list[str] = []
        for href, link_text in self.links:
            links.append(urljoin(final_url, href))
            if link_text:
                link_texts.append(link_text)
        return PublicPageSnapshot(
            url=url,
            final_url=final_url,
            title=title,
            text=text,
            links=tuple(_dedupe_preserve_order(links)),
            link_texts=tuple(_dedupe_preserve_order(link_texts)),
            blocked=_looks_blocked(f"{title}\n{text}"),
        )


class PublicSignalCollector:
    """Collect public hiring signals without logins or captcha bypass."""

    def __init__(self, company_name: str, domain: str, timeout_ms: int = 10_000) -> None:
        self.company_name = company_name
        self.domain = domain.strip()
        self.timeout_ms = timeout_ms

    def collect_all(self) -> tuple[ScoredSignal, ScoredSignal, ScoredSignal]:
        return (
            self.collect_crunchbase_signal(),
            self.collect_job_post_signal(),
            self.collect_leadership_change_signal(),
        )

    def collect_crunchbase_signal(self) -> ScoredSignal:
        url = self._crunchbase_url()
        source_ref = _public_source_ref(
            title="Crunchbase public organization page",
            url=url,
            note="Public Crunchbase page collected without login or captcha bypass.",
        )
        if self._should_skip_live_collection():
            return ScoredSignal(
                name="recent_funding",
                value=f"Live Crunchbase collection was skipped for synthetic domain {self.domain}.",
                confidence=ConfidenceLevel.LOW,
                evidence=["Synthetic test domains are intentionally not scraped against public providers."],
                source_refs=[source_ref],
            )

        snapshot = self._capture_public_page(url)
        if snapshot.blocked:
            return ScoredSignal(
                name="recent_funding",
                value="Public Crunchbase page appears blocked or inaccessible without login.",
                confidence=ConfidenceLevel.LOW,
                evidence=[
                    f"Attempted to collect from {snapshot.final_url}.",
                    "The rendered page contained a login, captcha, or anti-bot block and was not bypassed.",
                ],
                source_refs=[source_ref],
            )

        text = snapshot.text or f"{snapshot.title} {' '.join(snapshot.link_texts)}"
        sentence = self._first_matching_sentence(text, _FUNDING_PATTERNS)
        if sentence:
            confidence = ConfidenceLevel.HIGH if self._has_strong_funding_phrase(sentence) else ConfidenceLevel.MEDIUM
            return ScoredSignal(
                name="recent_funding",
                value=f"Crunchbase public page indicates funding activity: {sentence}",
                confidence=confidence,
                evidence=[
                    f"Collected the public Crunchbase organization page at {snapshot.final_url}.",
                    f"Matched a public funding phrase in the rendered page text: {sentence}",
                ],
                source_refs=[source_ref],
            )

        confidence = ConfidenceLevel.MEDIUM if text else ConfidenceLevel.LOW
        return ScoredSignal(
            name="recent_funding",
            value="No explicit funding round was visible on the public Crunchbase page.",
            confidence=confidence,
            evidence=[
                f"Collected the public Crunchbase organization page at {snapshot.final_url}.",
                "The rendered page did not expose a clear funding round, but the page itself loaded successfully.",
            ],
            source_refs=[source_ref],
        )

    def collect_job_post_signal(self) -> ScoredSignal:
        homepage_url = self._homepage_url()
        homepage_ref = _public_source_ref(
            title="Company homepage",
            url=homepage_url,
            note="Public company page used to discover careers and jobs links.",
        )
        if self._should_skip_live_collection():
            return ScoredSignal(
                name="job_post_velocity",
                value=f"Live job-post collection was skipped for synthetic domain {self.domain}.",
                confidence=ConfidenceLevel.LOW,
                evidence=["Synthetic test domains are intentionally not scraped against public providers."],
                source_refs=[homepage_ref],
            )

        homepage_snapshot = self._capture_public_page(homepage_url)
        if homepage_snapshot.blocked:
            return ScoredSignal(
                name="job_post_velocity",
                value="Public company homepage appears blocked or inaccessible without login.",
                confidence=ConfidenceLevel.LOW,
                evidence=[
                    f"Attempted to collect from {homepage_snapshot.final_url}.",
                    "The rendered page contained a login, captcha, or anti-bot block and was not bypassed.",
                ],
                source_refs=[homepage_ref],
            )

        candidate_urls = self._discover_candidate_urls(
            homepage_snapshot,
            standard_paths=("/careers", "/jobs", "/join-us", "/openings", "/company/careers"),
            keywords=("careers", "jobs", "open roles", "join us", "join-us", "apply"),
        )
        snapshots = [homepage_snapshot]
        source_refs = [homepage_ref]
        for candidate_url in candidate_urls[:4]:
            candidate_snapshot = self._capture_public_page(candidate_url)
            snapshots.append(candidate_snapshot)
            source_refs.append(
                _public_source_ref(
                    title="Public careers page",
                    url=candidate_snapshot.final_url,
                    note="Rendered public job page discovered from the company website.",
                )
            )

        job_titles = self._extract_job_titles(snapshots)
        if job_titles:
            confidence = ConfidenceLevel.HIGH if len(job_titles) >= 3 else ConfidenceLevel.MEDIUM
            return ScoredSignal(
                name="job_post_velocity",
                value=f"Public careers pages surface {len(job_titles)} open roles: {', '.join(job_titles[:4])}.",
                confidence=confidence,
                evidence=[
                    f"Discovered public careers/join-us pages from {homepage_snapshot.final_url}.",
                    f"Extracted role titles from rendered public pages: {', '.join(job_titles[:6])}.",
                ],
                source_refs=source_refs,
            )

        accessible_page_count = sum(1 for snapshot in snapshots if not snapshot.blocked and snapshot.text)
        confidence = ConfidenceLevel.MEDIUM if accessible_page_count else ConfidenceLevel.LOW
        return ScoredSignal(
            name="job_post_velocity",
            value="Public careers pages were reachable, but no explicit open role cards were visible.",
            confidence=confidence,
            evidence=[
                f"Collected {accessible_page_count} accessible public careers-related page(s).",
                "No job title patterns were visible in the rendered page text.",
            ],
            source_refs=source_refs,
        )

    def collect_leadership_change_signal(self) -> ScoredSignal:
        homepage_url = self._homepage_url()
        homepage_ref = _public_source_ref(
            title="Company homepage",
            url=homepage_url,
            note="Public company page used to discover press, news, and leadership pages.",
        )
        if self._should_skip_live_collection():
            return ScoredSignal(
                name="leadership_change",
                value=f"Live leadership-change collection was skipped for synthetic domain {self.domain}.",
                confidence=ConfidenceLevel.LOW,
                evidence=["Synthetic test domains are intentionally not scraped against public providers."],
                source_refs=[homepage_ref],
            )

        homepage_snapshot = self._capture_public_page(homepage_url)
        if homepage_snapshot.blocked:
            return ScoredSignal(
                name="leadership_change",
                value="Public company homepage appears blocked or inaccessible without login.",
                confidence=ConfidenceLevel.LOW,
                evidence=[
                    f"Attempted to collect from {homepage_snapshot.final_url}.",
                    "The rendered page contained a login, captcha, or anti-bot block and was not bypassed.",
                ],
                source_refs=[homepage_ref],
            )

        candidate_urls = self._discover_candidate_urls(
            homepage_snapshot,
            standard_paths=("/news", "/press", "/blog", "/company/news", "/company/press", "/about/news"),
            keywords=("news", "press", "blog", "media", "updates", "announcements"),
        )
        snapshots = [homepage_snapshot]
        source_refs = [homepage_ref]
        for candidate_url in candidate_urls[:5]:
            candidate_snapshot = self._capture_public_page(candidate_url)
            snapshots.append(candidate_snapshot)
            source_refs.append(
                _public_source_ref(
                    title="Public leadership/news page",
                    url=candidate_snapshot.final_url,
                    note="Rendered public news page discovered from the company website.",
                )
            )

        snippets = self._extract_leadership_snippets(snapshots)
        if snippets:
            explicit_change_terms = (
                "appointed",
                "named",
                "joins as",
                "promoted to",
                "steps down",
                "resigns",
            )
            confidence = (
                ConfidenceLevel.HIGH
                if any(term in snippets[0].lower() for term in explicit_change_terms) or len(snippets) >= 2
                else ConfidenceLevel.MEDIUM
            )
            return ScoredSignal(
                name="leadership_change",
                value=f"Public news pages mention a leadership change: {snippets[0]}",
                confidence=confidence,
                evidence=[
                    f"Discovered public news or press pages from {homepage_snapshot.final_url}.",
                    f"Matched leadership-change language in the rendered page text: {snippets[0]}",
                ],
                source_refs=source_refs,
            )

        accessible_page_count = sum(1 for snapshot in snapshots if not snapshot.blocked and snapshot.text)
        confidence = ConfidenceLevel.MEDIUM if accessible_page_count else ConfidenceLevel.LOW
        return ScoredSignal(
            name="leadership_change",
            value="Public news pages were reachable, but no explicit leadership change was visible.",
            confidence=confidence,
            evidence=[
                f"Collected {accessible_page_count} accessible public news or press page(s).",
                "No leadership appointment, promotion, resignation, or transition language was visible.",
            ],
            source_refs=source_refs,
        )

    def _capture_public_page(self, url: str) -> PublicPageSnapshot:
        if sync_playwright is not None:
            try:
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch(headless=True)
                    context = browser.new_context(viewport={"width": 1280, "height": 900})
                    page = context.new_page()
                    page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                    title = page.title().strip()
                    text = page.locator("body").inner_text(timeout=self.timeout_ms).strip()
                    link_rows = page.locator("a[href]").evaluate_all(
                        """
                        elements => elements.map(element => ({
                            href: element.href,
                            text: (element.innerText || element.textContent || '').trim(),
                        }))
                        """
                    )
                    final_url = page.url
                    browser.close()
                    links: list[str] = []
                    link_texts: list[str] = []
                    for row in link_rows:
                        href = str(row.get("href", "")).strip()
                        if href:
                            links.append(href)
                        link_text = str(row.get("text", "")).strip()
                        if link_text:
                            link_texts.append(link_text)
                    return PublicPageSnapshot(
                        url=url,
                        final_url=final_url,
                        title=title,
                        text=text,
                        links=tuple(_dedupe_preserve_order(links)),
                        link_texts=tuple(_dedupe_preserve_order(link_texts)),
                        blocked=_looks_blocked(f"{title}\n{text}"),
                    )
            except (PlaywrightTimeoutError, Exception):
                pass

        request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; TenaciousBot/1.0)"})
        try:
            with urlopen(request, timeout=self.timeout_ms / 1000) as response:
                html = response.read().decode("utf-8", errors="replace")
                final_url = response.geturl() or url
        except (HTTPError, URLError, TimeoutError):
            return PublicPageSnapshot(url=url, final_url=url, title="", text="", blocked=True)

        parser = _VisibleContentParser()
        parser.feed(html)
        snapshot = parser.build_snapshot(url=url, final_url=final_url)
        return PublicPageSnapshot(
            url=snapshot.url,
            final_url=snapshot.final_url,
            title=snapshot.title,
            text=snapshot.text,
            links=snapshot.links,
            link_texts=snapshot.link_texts,
            blocked=snapshot.blocked,
        )

    def _should_skip_live_collection(self) -> bool:
        return _is_synthetic_domain(self.domain)

    def _homepage_url(self) -> str:
        return _normalize_company_domain(self.domain)

    def _crunchbase_url(self) -> str:
        return f"https://www.crunchbase.com/organization/{_slugify(self.company_name)}"

    def _discover_candidate_urls(
        self,
        snapshot: PublicPageSnapshot,
        standard_paths: tuple[str, ...],
        keywords: tuple[str, ...],
    ) -> list[str]:
        candidate_urls: list[str] = []
        base_url = snapshot.final_url or snapshot.url
        parsed = urlparse(base_url)
        origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else base_url.rstrip("/")
        for path in standard_paths:
            candidate_urls.append(urljoin(origin + "/", path.lstrip("/")))

        for index, link_url in enumerate(snapshot.links):
            link_text = snapshot.link_texts[index] if index < len(snapshot.link_texts) else ""
            lower = f"{link_url} {link_text}".lower()
            if any(keyword in lower for keyword in keywords):
                candidate_urls.append(link_url)

        return _dedupe_preserve_order(candidate_urls)

    def _extract_job_titles(self, snapshots: list[PublicPageSnapshot]) -> list[str]:
        candidates: list[str] = []
        for snapshot in snapshots:
            for line in snapshot.text.splitlines():
                normalized = re.sub(r"\s+", " ", line).strip(" -\t")
                if not normalized or len(normalized) > 120:
                    continue
                lowered = normalized.lower()
                if lowered.startswith(("apply", "cookie", "privacy", "learn more", "sign up", "contact us")):
                    continue
                if any(pattern in lowered for pattern in _JOB_PATTERNS):
                    candidates.append(normalized)
            for link_text in snapshot.link_texts:
                normalized = re.sub(r"\s+", " ", link_text).strip(" -\t")
                if normalized and any(pattern in normalized.lower() for pattern in _JOB_PATTERNS):
                    candidates.append(normalized)
        return _dedupe_preserve_order(candidates)

    def _extract_leadership_snippets(self, snapshots: list[PublicPageSnapshot]) -> list[str]:
        snippets: list[str] = []
        for snapshot in snapshots:
            for sentence in _split_sentences(snapshot.text):
                lowered = sentence.lower()
                if any(pattern.search(sentence) for pattern in _LEADERSHIP_PATTERNS):
                    snippets.append(sentence)
                elif any(
                    keyword in lowered
                    for keyword in (
                        "chief executive",
                        "chief technology",
                        "chief financial",
                        "chief operating",
                        "ceo",
                        "cto",
                        "cfo",
                        "coo",
                    )
                ):
                    snippets.append(sentence)
        return _dedupe_preserve_order(snippets)

    def _first_matching_sentence(self, text: str, patterns: tuple[re.Pattern[str], ...]) -> str:
        for sentence in _split_sentences(text):
            if any(pattern.search(sentence) for pattern in patterns):
                return sentence
        return ""

    def _has_strong_funding_phrase(self, sentence: str) -> bool:
        lowered = sentence.lower()
        return any(keyword in lowered for keyword in ("series a", "series b", "series c", "seed round", "funding round")) or "$" in sentence