"""Small statistical helpers used by TrialCheck.

No scipy dependency is required. The approximations are intentionally limited to
what v0.2 needs: two-arm SRM, two-proportion z-tests, and Welch's t-test for
continuous metrics.
"""

from __future__ import annotations

import math
from typing import Optional, Tuple


def chi_square_df1_survival(x: float) -> float:
    """Survival function P(ChiSq(df=1) >= x)."""

    if x < 0:
        raise ValueError("chi-square statistic cannot be negative")
    return math.erfc(math.sqrt(x / 2.0))


def normal_two_sided_pvalue(z: float) -> float:
    """Two-sided p-value for standard normal z using erfc."""

    return math.erfc(abs(z) / math.sqrt(2.0))


def two_proportion_z_test(
    control_successes: int,
    control_n: int,
    treatment_successes: int,
    treatment_n: int,
) -> Tuple[Optional[float], Optional[float]]:
    """Return z-statistic and two-sided p-value for a two-proportion test."""

    if control_n <= 0 or treatment_n <= 0:
        return None, None
    if not (0 <= control_successes <= control_n and 0 <= treatment_successes <= treatment_n):
        return None, None

    pooled = (control_successes + treatment_successes) / (control_n + treatment_n)
    se = math.sqrt(pooled * (1.0 - pooled) * (1.0 / control_n + 1.0 / treatment_n))
    if se == 0:
        return None, None
    z = (treatment_successes / treatment_n - control_successes / control_n) / se
    return z, normal_two_sided_pvalue(z)


def welch_t_test(
    control_mean: float,
    control_std: float,
    control_n: int,
    treatment_mean: float,
    treatment_std: float,
    treatment_n: int,
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """Welch's two-sample t-test for continuous metrics.

    Returns (t_statistic, degrees_of_freedom, two_sided_p_value).
    Returns (None, None, None) if inputs are invalid or variance is zero.

    Welch's t-test does not assume equal variances between arms — the correct
    default for A/B experiments where treatment may affect metric variance.
    """
    if control_n <= 1 or treatment_n <= 1:
        return None, None, None
    if control_std < 0 or treatment_std < 0:
        return None, None, None

    var_c = (control_std ** 2) / control_n
    var_t = (treatment_std ** 2) / treatment_n
    se2 = var_c + var_t
    if se2 <= 0:
        return None, None, None

    se = math.sqrt(se2)
    t = (treatment_mean - control_mean) / se

    # Welch-Satterthwaite degrees of freedom
    if var_c == 0 and var_t == 0:
        return None, None, None
    dof_num = se2 ** 2
    dof_denom = (var_c ** 2) / (control_n - 1) + (var_t ** 2) / (treatment_n - 1)
    if dof_denom <= 0:
        return None, None, None
    dof = dof_num / dof_denom

    # Two-sided p-value via incomplete beta function (regularized).
    # P(T > |t|) = I(dof/(dof+t^2), dof/2, 0.5) for t-distribution.
    # math.dist is not the right tool; use the relation to the incomplete beta.
    # betainc is available in Python 3.12+; fall back to normal approximation
    # for older versions (conservative for large n, acceptable for v0.2).
    try:
        # Python 3.12+
        x = dof / (dof + t * t)
        p_value = math.betainc(dof / 2.0, 0.5, x)
    except AttributeError:
        # Fallback: normal approximation — valid when dof > 30
        p_value = normal_two_sided_pvalue(t)

    return t, dof, p_value


def safe_float(value: object) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_int(value: object) -> Optional[int]:
    try:
        if value is None or value == "":
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None
