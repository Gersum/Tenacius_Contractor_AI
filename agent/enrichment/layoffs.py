from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import date, datetime
from functools import cached_property
from pathlib import Path

from agent.models.schemas import ConfidenceLevel, ScoredSignal, SourceRef

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


def _normalize_company_name(name: str) -> str:
    tokens = re.findall(r"[a-z0-9]+", name.lower())
    tokens = [token for token in tokens if token not in _COMPANY_SUFFIXES]
    return " ".join(tokens)


def _parse_int(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def _parse_float(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


@dataclass(frozen=True)
class LayoffRecord:
    company: str
    location_hq: str
    industry: str
    laid_off_count: int | None
    percentage: float | None
    event_date: date
    source: str
    country: str
    stage: str
    funds_raised_usd: int | None


class LayoffsLookup:
    """CSV-backed layoffs signal lookup using the provided layoffs dataset."""

    def __init__(self, csv_path: str | Path) -> None:
        self.csv_path = Path(csv_path).expanduser()

    @cached_property
    def records(self) -> list[LayoffRecord]:
        if not self.csv_path.exists():
            return []

        records: list[LayoffRecord] = []
        with self.csv_path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                raw_date = (row.get("Date") or "").strip()
                if not raw_date:
                    continue
                try:
                    event_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
                except ValueError:
                    continue

                records.append(
                    LayoffRecord(
                        company=(row.get("Company") or "").strip(),
                        location_hq=(row.get("Location_HQ") or "").strip(),
                        industry=(row.get("Industry") or "").strip(),
                        laid_off_count=_parse_int(row.get("Laid_Off_Count")),
                        percentage=_parse_float(row.get("Percentage")),
                        event_date=event_date,
                        source=(row.get("Source") or "").strip(),
                        country=(row.get("Country") or "").strip(),
                        stage=(row.get("Stage") or "").strip(),
                        funds_raised_usd=_parse_int(row.get("Funds_Raised_USD")),
                    )
                )
        return records

    def build_signal(self, company_name: str, recent_window_days: int = 120) -> ScoredSignal:
        source_ref = self._source_ref()
        if not self.csv_path.exists():
            return ScoredSignal(
                name="layoffs",
                value=f"layoffs.csv was not found at {self.csv_path}",
                confidence=ConfidenceLevel.LOW,
                evidence=["Layoffs lookup could not run because the configured CSV path does not exist."],
                source_refs=[source_ref],
            )

        matches = self.find_company(company_name)
        if not matches:
            return ScoredSignal(
                name="layoffs",
                value=f"no layoffs.csv match found for {company_name}",
                confidence=ConfidenceLevel.MEDIUM,
                evidence=[
                    "Searched the configured layoffs.csv snapshot by normalized company name and found no exact match."
                ],
                source_refs=[source_ref],
            )

        latest = matches[0]
        days_since = (date.today() - latest.event_date).days
        count_text = (
            f"{latest.laid_off_count} employees"
            if latest.laid_off_count is not None
            else "an undisclosed number of employees"
        )
        percentage_text = f" ({latest.percentage:.0%})" if latest.percentage is not None else ""

        if days_since <= recent_window_days:
            evidence = [
                f"Matched company '{latest.company}' in layoffs.csv.",
                f"Stage: {latest.stage or 'unknown'}; country: {latest.country or 'unknown'}.",
            ]
            if latest.source:
                evidence.append(f"Source article: {latest.source}")
            return ScoredSignal(
                name="layoffs",
                value=(
                    f"layoffs.csv shows a layoff on {latest.event_date.isoformat()} affecting "
                    f"{count_text}{percentage_text}"
                ),
                confidence=ConfidenceLevel.HIGH,
                evidence=evidence,
                source_refs=[source_ref],
                freshness_days=days_since,
            )

        return ScoredSignal(
            name="layoffs",
            value=(
                f"layoffs.csv shows a historical layoff on {latest.event_date.isoformat()}, "
                f"but nothing newer than {recent_window_days} days for {company_name}"
            ),
            confidence=ConfidenceLevel.MEDIUM,
            evidence=[
                f"Latest matched layoff event affected {count_text}{percentage_text}.",
                "This informs context, but it is outside the current recency window for pitch selection.",
            ],
            source_refs=[source_ref],
            freshness_days=days_since,
        )

    def find_company(self, company_name: str) -> list[LayoffRecord]:
        normalized = _normalize_company_name(company_name)
        matches = [record for record in self.records if _normalize_company_name(record.company) == normalized]
        return sorted(matches, key=lambda record: record.event_date, reverse=True)

    def _source_ref(self) -> SourceRef:
        url = self.csv_path.as_uri() if self.csv_path.is_absolute() else self.csv_path.as_posix()
        return SourceRef(
            title="layoffs.csv snapshot",
            url=url,
            note="Configured layoffs dataset used for layoff-signal enrichment.",
        )
