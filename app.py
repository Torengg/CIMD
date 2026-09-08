"""Analyse behavioural outcomes from the discount-framing study."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from scipy import stats


BASE_DIR = Path(__file__).resolve().parent
RESPONSES_FILE = BASE_DIR / "data" / "behavioural_responses.csv"


def cohens_d(group_a: pd.Series, group_b: pd.Series) -> float:
    """Pooled-standard-deviation Cohen's d, reported as Version A minus B."""
    n_a, n_b = len(group_a), len(group_b)
    pooled_sd = (((n_a - 1) * group_a.var(ddof=1) + (n_b - 1) * group_b.var(ddof=1)) / (n_a + n_b - 2)) ** 0.5
    return (group_a.mean() - group_b.mean()) / pooled_sd if pooled_sd else float("nan")


def compare_continuous(data: pd.DataFrame, column: str, label: str) -> None:
    clean = data.dropna(subset=[column])
    a = clean.loc[clean["assigned_group"] == "A", column]
    b = clean.loc[clean["assigned_group"] == "B", column]
    if len(a) < 2 or len(b) < 2:
        print(f"\n{label}: at least two valid responses are needed in each group.")
        return
    t_stat, p_value = stats.ttest_ind(a, b, equal_var=True)
    print(f"\n{label}")
    print(f"  Version A (20% OFF): n={len(a)}, mean={a.mean():.3f}, SD={a.std(ddof=1):.3f}, median={a.median():.3f}")
    print(f"  Version B (SAVE ₹500): n={len(b)}, mean={b.mean():.3f}, SD={b.std(ddof=1):.3f}, median={b.median():.3f}")
    print(f"  Difference (A − B): {a.mean() - b.mean():.3f}")
    print(f"  Independent-samples t-test: t={t_stat:.3f}, p={p_value:.4f}; Cohen's d={cohens_d(a, b):.3f}")


def compare_add_to_cart(data: pd.DataFrame) -> None:
    decision_data = data.dropna(subset=["decision"])
    table = pd.crosstab(decision_data["assigned_group"], decision_data["decision"]).reindex(
        index=["A", "B"], columns=["ADD_TO_CART", "NOT_INTERESTED"], fill_value=0
    )
    if (table.sum(axis=1) == 0).any():
        print("\nADD-TO-CART RATE: at least one decision is needed in each group.")
        return
    print("\nADD-TO-CART RATE")
    for group, name in [("A", "Version A (20% OFF)"), ("B", "Version B (SAVE ₹500)")]:
        total = table.loc[group].sum()
        count = table.loc[group, "ADD_TO_CART"]
        print(f"  {name}: {count}/{total} ({100 * count / total:.1f}%)")
    try:
        chi2, p_value, _, expected = stats.chi2_contingency(table)
        if (expected < 5).any():
            _, p_value = stats.fisher_exact(table.to_numpy())
            print(f"  Fisher's exact test (small expected counts): p={p_value:.4f}")
        else:
            print(f"  Chi-square test: χ²={chi2:.3f}, p={p_value:.4f}")
    except ValueError:
        print("  Test unavailable because one outcome has no variation yet.")


def main() -> None:
    if not RESPONSES_FILE.exists():
        raise SystemExit("No data found yet. Collect responses first using app.py.")
    data = pd.read_csv(RESPONSES_FILE)
    for column in ("decision", "decision_time_seconds"):
        if column not in data.columns:
            data[column] = pd.NA
    data["decision_time_seconds"] = pd.to_numeric(data.get("decision_time_seconds"), errors="coerce")
    data = data.dropna(subset=["assigned_group"])
    print("\nDISCOUNT-FRAMING A/B TEST")
    print(f"Completed responses: {len(data)}")
    compare_add_to_cart(data)
    compare_continuous(data, "decision_time_seconds", "DECISION TIME (SECONDS)")


if __name__ == "__main__":
    main()
