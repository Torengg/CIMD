"""Run the planned independent-samples A/B analysis after collecting responses."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from scipy import stats


BASE_DIR = Path(__file__).resolve().parent
RESPONSES_FILE = BASE_DIR / "data" / "responses.csv"


def cohens_d(group_a: pd.Series, group_b: pd.Series) -> float:
    """Cohen's d using pooled sample standard deviation (A minus B)."""
    n_a, n_b = len(group_a), len(group_b)
    pooled_sd = (((n_a - 1) * group_a.var(ddof=1) + (n_b - 1) * group_b.var(ddof=1)) / (n_a + n_b - 2)) ** 0.5
    return (group_a.mean() - group_b.mean()) / pooled_sd if pooled_sd else float("nan")


def main() -> None:
    if not RESPONSES_FILE.exists():
        raise SystemExit("No data found yet. Collect responses first using app.py.")

    data = pd.read_csv(RESPONSES_FILE)
    data["purchase_intention_index"] = pd.to_numeric(data["purchase_intention_index"], errors="coerce")
    data = data.dropna(subset=["assigned_group", "purchase_intention_index"])
    a = data.loc[data["assigned_group"] == "A", "purchase_intention_index"]
    b = data.loc[data["assigned_group"] == "B", "purchase_intention_index"]

    if len(a) < 2 or len(b) < 2:
        raise SystemExit("At least two valid responses are needed in each group before running the t-test.")

    t_stat, p_value = stats.ttest_ind(a, b, equal_var=True)
    difference = a.mean() - b.mean()
    d = cohens_d(a, b)
    result = pd.DataFrame(
        {
            "Version A (20% OFF)": [len(a), a.mean(), a.std(ddof=1)],
            "Version B (SAVE ₹500)": [len(b), b.mean(), b.std(ddof=1)],
        },
        index=["Sample size", "Mean purchase-intention index", "Standard deviation"],
    )

    print("\nDISCOUNT-FRAMING A/B TEST\n")
    print(result.round(3).to_string())
    print(f"\nMean difference (A − B): {difference:.3f}")
    print(f"Independent-samples t-test: t = {t_stat:.3f}, p = {p_value:.4f}")
    print(f"Cohen's d (A − B): {d:.3f}")
    if p_value < 0.05:
        direction = "Version A" if difference > 0 else "Version B"
        print(f"Conclusion at α = .05: evidence of a difference; {direction} has the higher mean PII.")
    else:
        print("Conclusion at α = .05: insufficient evidence of a difference in purchase intention.")


if __name__ == "__main__":
    main()
