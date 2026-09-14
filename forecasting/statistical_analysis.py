"""Statistical analysis module: Spearman correlations, FDR correction, and non-causal reporting."""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, false_discovery_control

def run_correlation_tests(pairs_dict):
    """
    Computes Spearman rank correlation for each pair in pairs_dict.
    pairs_dict format:
      {
        "pair_name": (array_x, array_y, description)
      }
    Applies Benjamini-Hochberg FDR if > 10 tests.
    Strict rule: say 'associated with', never 'causes'.
    """
    records = []
    for name, (x, y, desc) in pairs_dict.items():
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        valid = ~(np.isnan(x) | np.isnan(y) | np.isinf(x) | np.isinf(y))
        x_clean, y_clean = x[valid], y[valid]
        n = len(x_clean)
        if n < 3:
            continue
        
        # Check for constant arrays (std == 0)
        if np.std(x_clean) == 0 or np.std(y_clean) == 0:
            rho, p_val = 0.0, 1.0
        else:
            res = spearmanr(x_clean, y_clean)
            rho, p_val = float(res.statistic), float(res.pvalue)

        records.append({
            "pair": name,
            "description": desc,
            "spearman_rho": round(rho, 4),
            "p_value": float(p_val),
            "n": int(n),
        })

    if not records:
        return pd.DataFrame()

    results_df = pd.DataFrame(records)

    # Benjamini-Hochberg FDR if > 10 tests
    if len(results_df) > 10:
        p_vals = results_df["p_value"].to_numpy()
        p_adj = false_discovery_control(p_vals, method="bh")
        results_df["p_adjusted"] = p_adj.round(6)
        sig_col = "p_adjusted"
    else:
        results_df["p_adjusted"] = results_df["p_value"].round(6)
        sig_col = "p_value"

    results_df["is_significant"] = results_df[sig_col] < 0.05
    results_df["status"] = results_df["is_significant"].map(
        lambda s: "significant" if s else "not significant"
    )

    # Non-causal phrasing
    def format_association(row):
        dir_str = "positively" if row["spearman_rho"] > 0 else "negatively"
        if row["is_significant"]:
            return f"Statistically significantly {dir_str} associated with (rho={row['spearman_rho']}, p={row[sig_col]:.2e}, n={row['n']})"
        else:
            return f"Not statistically significantly associated with (rho={row['spearman_rho']}, p={row[sig_col]:.2e}, n={row['n']})"

    results_df["finding"] = results_df.apply(format_association, axis=1)
    return results_df
