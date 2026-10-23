"""
Requirements estimates from the sample — backend/specs/market-health/api.md — Business Logic —
Sampling — Estimates; design/market-health/experience.md — Requirements estimates.

The only place requirements shares, margins and confidence are computed. Used by
market_query.query_requirements_data (chat + MCP get_skill_demand), Story 1's skills block and
the curated skills answers.

Post-stratified by group g = (role_category, specialization, month first stored):
    N_g  classified postings in the slice          (population, slice filters on postings only)
    n_g  of those with extracted requirements       (the sample)
    w_g  = N_g / n_g                                 (each read posting stands for w_g postings)
A count x over the read postings becomes Σ w_g x_g, and a share is Σ w_g x_g / Σ w_g n'_g, where
n'_g is the read postings matching every filter (including requirement-level filters such as
work arrangement). Groups nobody has read yet (n_g = 0) are excluded and reported as unread_n.

Margin: one per response, the widest it can be (p = 0.5), 95%, with the finite-population
correction:  ceil(100 · 1.96 · sqrt(Σ (N'_g/N')² · 0.25/n'_g · (N'_g − n'_g)/(N'_g − 1))).
"""

from __future__ import annotations

import math

import method_text

# Groups by the posting's current classification and the month it was first stored.
GROUP_KEY_SQL = "c.role_category, COALESCE(c.specialization, ''), date_trunc('month', rp.created_at)::date"

_SMALL_SAMPLE = 30   # n ≥ 30: an estimate with a margin
_TOO_FEW = 10        # n < 10: no shares


def population(conn, where_sql: str, params: list) -> dict[tuple, tuple[int, int]]:
    """{group: (N_g, n_g)} for the slice. `where_sql` may reference rp and c only."""
    rows = conn.execute(
        f"""
        SELECT {GROUP_KEY_SQL}, count(*), count(pr.posting_id)
        FROM raw_postings rp
        JOIN classifications c ON c.posting_id = rp.id
        LEFT JOIN posting_requirements pr ON pr.posting_id = rp.id
        WHERE {where_sql}
        GROUP BY 1, 2, 3
        """,
        params,
    ).fetchall()
    return {(r[0], r[1], r[2]): (r[3], r[4]) for r in rows}


class Estimator:
    """Weights from a population, applied to per-group counts of read postings."""

    def __init__(self, groups: dict[tuple, tuple[int, int]], sample_by_group: dict[tuple, int]):
        self.weights = {g: N / n for g, (N, n) in groups.items() if n > 0}
        self.sample = {g: sample_by_group.get(g, 0) for g in self.weights}
        self.groups = groups
        self.base = sum(self.weights[g] * self.sample[g] for g in self.weights)
        self.sample_n = sum(self.sample.values())
        self.unread_n = sum(N for N, n in groups.values() if n == 0)
        self.is_estimate = any(groups[g][1] < groups[g][0] and self.sample[g] > 0 for g in self.weights)

    def weighted(self, counts_by_group: dict[tuple, int]) -> float:
        return sum(self.weights[g] * x for g, x in counts_by_group.items() if g in self.weights)

    def share_pct(self, counts_by_group: dict[tuple, int]) -> float | None:
        if self.base <= 0:
            return None
        return round(100 * self.weighted(counts_by_group) / self.base, 1)

    def margin_pts(self) -> int | None:
        if not self.is_estimate or self.base <= 0:
            return None
        variance = 0.0
        for g, w in self.weights.items():
            n = self.sample[g]
            if n == 0:
                continue
            big_n = w * n
            if big_n <= 1 or n >= big_n:
                continue
            fpc = (big_n - n) / (big_n - 1)
            variance += (big_n / self.base) ** 2 * 0.25 / n * fpc
        return math.ceil(100 * 1.96 * math.sqrt(variance)) if variance > 0 else 0

    def confidence(self) -> str:
        n = self.sample_n
        if not self.is_estimate:
            return "full" if n >= _TOO_FEW else "full_small"
        if n >= _SMALL_SAMPLE:
            return "estimate"
        if n >= _TOO_FEW:
            return "small_sample"
        return "too_few"

    def estimate(self) -> dict:
        confidence = self.confidence()
        population_n = round(self.base)
        margin = self.margin_pts()
        return {
            "is_estimate": self.is_estimate,
            "sample_n": self.sample_n,
            "population_n": population_n,
            "unread_n": self.unread_n,
            "margin_pts": margin,
            "confidence": confidence,
            "qualifier": method_text.qualifier(confidence, self.sample_n, population_n, margin),
        }

    @property
    def shows_shares(self) -> bool:
        """too_few → no shares at all; full_small → plain counts instead of shares."""
        return self.confidence() not in ("too_few", "full_small")


def about_level(a_pct: float, b_pct: float, margin_pts: int | None) -> bool:
    """Two estimated shares closer than the margin are "about level" — never ranked in words."""
    return margin_pts is not None and abs(a_pct - b_pct) < margin_pts
