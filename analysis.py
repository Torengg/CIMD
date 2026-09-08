"""Analyse the completed Google Sheet export (CSV) from the discount A/B study."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from scipy import stats


def cohens_d(a: pd.Series, b: pd.Series) -> float:
    pooled = (((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2)) ** 0.5
    return (a.mean() - b.mean()) / pooled if pooled else float("nan")


def binary_outcome(data: pd.DataFrame, column: str, positive: str, label: str) -> None:
    table = pd.crosstab(data["assigned_group"], data[column]).reindex(index=["A", "B"], columns=[positive, "NO"], fill_value=0)
    print(f"\n{label}")
    for group, name in [("A", "A — 20% OFF"), ("B", "B — SAVE ₹500")]:
        total, selected = table.loc[group].sum(), table.loc[group, positive]
        print(f"  {name}: {selected}/{total} ({selected / total:.1%})" if total else f"  {name}: no data")
    if (table.sum(axis=1) > 0).all() and table.to_numpy().sum() > 0:
        chi2, p, _, expected = stats.chi2_contingency(table)
        if (expected < 5).any():
            _, p = stats.fisher_exact(table.to_numpy())
            print(f"  Fisher's exact test p={p:.4f}")
        else:
            print(f"  Chi-square χ²={chi2:.3f}, p={p:.4f}")


def continuous_outcome(data: pd.DataFrame, column: str, label: str) -> None:
    clean = data.dropna(subset=[column]).copy()
    clean[column] = pd.to_numeric(clean[column], errors="coerce")
    clean = clean.dropna(subset=[column])
    a, b = clean.loc[clean.assigned_group == "A", column], clean.loc[clean.assigned_group == "B", column]
    print(f"\n{label}")
    if len(a) < 2 or len(b) < 2:
        print("  Need at least two valid observations in each group.")
        return
    t, p = stats.ttest_ind(a, b, equal_var=True)
    print(f"  A — 20% OFF: n={len(a)}, mean={a.mean():.3f}, SD={a.std(ddof=1):.3f}, median={a.median():.3f}")
    print(f"  B — SAVE ₹500: n={len(b)}, mean={b.mean():.3f}, SD={b.std(ddof=1):.3f}, median={b.median():.3f}")
    print(f"  Difference (A − B)={a.mean()-b.mean():.3f}; t={t:.3f}, p={p:.4f}; Cohen's d={cohens_d(a,b):.3f}")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Download the Google Sheet as CSV, then run: python analysis.py Responses.csv")
    data = pd.read_csv(Path(sys.argv[1]))
    print(f"\nDISCOUNT-FRAMING A/B TEST — {len(data)} completed responses")
    binary_outcome(data, "add_to_cart", "YES", "ADD-TO-CART RATE")
    binary_outcome(data[data.add_to_cart == "YES"], "checkout", "YES", "CHECKOUT RATE AMONG CART ADDERS")
    continuous_outcome(data, "decision_time_seconds", "DECISION TIME (SECONDS)")
    continuous_outcome(data, "purchase_intention_index", "PURCHASE INTENTION INDEX")


if __name__ == "__main__":
    main()
