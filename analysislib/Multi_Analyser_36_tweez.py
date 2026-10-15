"""
N-dimensional fluorescence tweezer ROI analysis for Lyse.

- Supports any number of scan parameters.
- Averages over all tweezers at each N-D scan coordinate.
- Treats first and second fluorescence images separately.
- 1D scan: error-bar plot
- 2D scan: heatmap
- 3D+ scan: 2D heatmap slice with other dimensions fixed
- Saves the complete N-D results table as CSV
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from scipy.optimize import curve_fit

import lyse
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns



# =============================================================================
# CONFIGURATION

# sem == standard error of the mean
# =============================================================================

N_TWEEZERS = 36
TWEEZERS_TO_PLOT = list(range(1, N_TWEEZERS + 1))
# TWEEZERS_TO_PLOT = [1,7,13,19,25,31]  # solo alcuni
# TWEEZERS_TO_PLOT = [1,2,3,4,5,6]  # solo alcuni
#TWEEZERS_TO_PLOT = [33]                  # un solo tweezer



PLOT_SURV_PROB=True
PLOT_INDIVIDUAL_TWEEZERS = False
PLOT_SURVIVAL_PER_TWEEZER = True
PLOT_ALL_TWEEZERS = False
SAVE_PLOTS = True
SAVE_CSV = False
One_D = True
FIT_MJ0_LOSS_GAUSSIAN = False
MJ0_FIT_X_MIN = None
MJ0_FIT_X_MAX = None
FIT_SIGMOID = False
FIT_SIGMOID_MEAN = False
FIT_X_MIN = -3.0
FIT_X_MAX = -2.0
sigma_array = np.full(N_TWEEZERS, np.nan)
PLOT_SIGMA = False

if One_D:
    PLOT_AXES = (2,)      # 1D: plot FluoImgPulse_Dt6
else:
    PLOT_AXES = (2, 4)    # 2D: plot FluoImgPulse_Dt × LAC_duration

if One_D:
    MJ1_SCAN_NAME = "MJ1_Recap_Release_duration"
    MJ1_X_LABEL = "MJ1 Recap Release duration (us)"
    MJ1_X_SCALE = 1  # Use 1e6 if the stored values are in seconds
else:
    MJ1_SCAN_NAME = "SisyphusMJ1_Freq"
    MJ1_X_LABEL = "SisyphusMJ1_Freq (MHz)"
    MJ1_X_SCALE = 1.0
    
SCAN_NAMES = [
    # "FluoImgPulse_Dt", # 0
    # "LAC_duration", # 1
    "LAC_Frq", # 2
    "LAC_Pow", # 3 
    "SisyphusImg_Frq", # 4
    "SisyphusPrecool_Pow", # 5 
    # "Blue_LACPower_SetPoint",
    # "FluoImaging_duration",
    # "ImagingFluo_SetPoint",
    "ImagingFluo_SetPoint",
    "QuantizAxis_Y_Coils_Current",
    "MJ1_Recap_Release_duration", # 6
    # "SisyphusPrecool_Pow", # 7
    # "ImagingTweez_Frq", # 8
    "FluoImaging_duration", # 9
    # "ImagingFluo_SetPoint", # 10
    # "TweezerCooling_duration"

]

SCAN_UNITS = [
    # "ms", # 0
    # "s", # 1
     "MHz", # 2
     "dB", # 3
      "MHz", # 4
     "dB", # 5
    #  "V",
    #  "ms",
    #  "V",
    "MHz",
     "V",
     "us",
    # "MHz", # 6
    #  "dB", # 7
    #  "MHz", # 8
    "ms", # 9
    # "V", # 10
    # "ms"
]

# For more than two scan parameters:
# Which two parameters should be displayed as the heatmap axes?
# Indices refer to SCAN_NAMES.
FIXED_VALUES = {
    # "LAC_Frq": -1.2,
    # "LAC_Pow": 17,
    # "SisyphusImg_Frq": -2.9,
}
# Fix dimensions not included in PLOT_AXES.
# Example:
# FIXED_VALUES = {
#     "LAC_Frq": -1.25,
#     "LAC_power": 0.8,
# }
#
# Leave empty to automatically select the middle measured value of every
# non-plotted scan dimension.
FIXED_VALUES = {}

# =========================================================
# SIGMOID FIT - SECOND IMAGE
# =========================================================


# =============================================================================


def scalar_per_shot(values, name: str) -> np.ndarray:
    """
    Convert one Lyse dataframe column to exactly one finite scalar per shot.

    Raises a clear error instead of silently accepting arrays or lists.
    """
    output = []

    for index, value in enumerate(values):
        array = np.asarray(value)

        if array.size != 1:
            raise ValueError(
                f"'{name}' must contain one scalar per shot. "
                f"Shot {index} contains shape {array.shape}."
            )

        output.append(float(array.reshape(-1)[0]))

    return np.asarray(output, dtype=float)

def plot_mj0_survival(
    df: pd.DataFrame,
    analyser: pd.DataFrame,
    dataset_label: str,
):
    """
    Plot conditional survival versus SisyphusMJ0_Freq.

    For each frequency:

        P_survival =
            sum(N_survived) / sum(N_initial)

    where N_initial is the number of occupied tweezers in image 1,
    and N_survived is the number of those same tweezers occupied
    in image 2.
    """

    figure_name = "MJ0 loss spectroscopy"

    # ---------------------------------------------------------
    # Check required globals/results
    # ---------------------------------------------------------

    required_globals = [
        "MJ0_Spectroscopy",
        "SisyphusMJ0_Freq",
    ]

    required_results = [
        "mj0_n_initial",
        "mj0_n_survived",
    ]

    missing_globals = [
        name for name in required_globals
        if name not in df.columns
    ]

    missing_results = [
        name for name in required_results
        if name not in analyser.columns
    ]

    if missing_globals or missing_results:
        print(
            "Skipping MJ0 plot. Missing:",
            missing_globals + missing_results,
        )
        return None


    # ---------------------------------------------------------
    # Read values for every loaded shot
    # ---------------------------------------------------------

    mj0_raw = scalar_per_shot(
        df["MJ0_Spectroscopy"],
        "MJ0_Spectroscopy",
    )

    mj0_enabled = (
        np.isfinite(mj0_raw)
        & (mj0_raw != 0)
    )

    # If the CURRENT shot does not have MJ0 enabled,
    # do not show an old/stale spectroscopy plot.
    if not mj0_enabled[-1]:
        plt.close(figure_name)
        return None


    frequencies = scalar_per_shot(
        df["SisyphusMJ0_Freq"],
        "SisyphusMJ0_Freq",
    )

    n_initial = scalar_per_shot(
        analyser["mj0_n_initial"],
        "mj0_n_initial",
    )

    n_survived = scalar_per_shot(
        analyser["mj0_n_survived"],
        "mj0_n_survived",
    )


    # ---------------------------------------------------------
    # Only use valid MJ0 shots
    # ---------------------------------------------------------

    valid = (
        mj0_enabled
        & np.isfinite(frequencies)
        & np.isfinite(n_initial)
        & np.isfinite(n_survived)
        & (n_initial > 0)
    )

    if not np.any(valid):
        print("No valid MJ0 spectroscopy shots yet.")
        return None


    mj0_data = pd.DataFrame({
        "frequency": frequencies[valid],
        "n_initial": n_initial[valid],
        "n_survived": n_survived[valid],
    })


    # ---------------------------------------------------------
    # Combine repetitions at each frequency
    # ---------------------------------------------------------

    grouped = (
        mj0_data
        .groupby("frequency", sort=True)
        .agg(
            n_initial=("n_initial", "sum"),
            n_survived=("n_survived", "sum"),
            n_shots=("frequency", "size"),
        )
        .reset_index()
    )

    grouped["survival"] = (
        grouped["n_survived"]
        / grouped["n_initial"]
    )

    # Binomial standard error
    grouped["sem"] = np.sqrt(
        grouped["survival"]
        * (1.0 - grouped["survival"])
        / grouped["n_initial"]
    )


    # ---------------------------------------------------------
    # Plot
    # ---------------------------------------------------------

    fig = plt.figure(
        figure_name,
        figsize=(9, 6),
    )

    fig.clear()

    ax = fig.add_subplot(111)

    ax.errorbar(
        grouped["frequency"],
        grouped["survival"],
        yerr=grouped["sem"],
        fmt="o-",
        capsize=4,
    )

    ax.set_xlabel("SisyphusMJ0_Freq")
    ax.set_ylabel(
        r"$P(\mathrm{image\ 2\ occupied}\mid"
        r"\mathrm{image\ 1\ occupied})$"
    )

    ax.set_ylim(-0.05, 1.05)

    ax.set_title(
        f"mJ = 0 loss spectroscopy - {dataset_label}"
    )

    ax.grid(alpha=0.25)

    fig.tight_layout()


    # ---------------------------------------------------------
    # Useful terminal output
    # ---------------------------------------------------------

    # print("\nMJ0 CONDITIONAL SURVIVAL:")

    # print(
    #     grouped.to_string(
    #         index=False,
    #         formatters={
    #             "frequency": "{:.6f}".format,
    #             "survival": "{:.4f}".format,
    #             "sem": "{:.4f}".format,
    #         },
    #     )
    # )

    return fig
def fit_mj0_loss_gaussian(
    ax, frequencies, n_initial, n_survived,
    tweezer, color, x_min=None, x_max=None,
):
    def loss_gaussian(x, baseline, loss_fraction, x0, sigma):
        return baseline * (
            1 - loss_fraction * np.exp(-0.5 * ((x - x0) / sigma) ** 2)
        )

    x = np.asarray(frequencies, dtype=float)
    n = np.asarray(n_initial, dtype=float)
    survived = np.asarray(n_survived, dtype=float)

    mask = (
        np.isfinite(x)
        & np.isfinite(n)
        & np.isfinite(survived)
        & (n > 0)
        & (survived >= 0)
        & (survived <= n)
    )

    if x_min is not None:
        mask &= x >= x_min
    if x_max is not None:
        mask &= x <= x_max

    x, n, survived = x[mask], n[mask], survived[mask]

    if np.unique(x).size < 5:
        print(f"TW {tweezer}: not enough frequencies for Gaussian fit")
        return None

    y = survived / n

    if np.ptp(y) == 0:
        print(f"TW {tweezer}: survival is flat")
        return None

    # Positive fit uncertainties, including survival values of 0 and 1.
    p_regularized = (survived + 0.5) / (n + 1)
    yerr = np.sqrt(
        p_regularized * (1 - p_regularized) / (n + 2)
    )

    span = np.ptp(x)
    baseline_guess = np.clip(np.max(y), 1e-6, 1 - 1e-6)
    loss_guess = np.clip(
        1 - np.min(y) / baseline_guess, 1e-6, 1 - 1e-6
    )

    try:
        popt, pcov = curve_fit(
            loss_gaussian,
            x,
            y,
            p0=[
                baseline_guess,
                loss_guess,
                x[np.argmin(y)],
                span / 6,
            ],
            bounds=(
                [0, 0, np.min(x), span * 1e-6],
                [1, 1, np.max(x), np.inf],
            ),
            sigma=yerr,
            absolute_sigma=True,
            maxfev=20000,
        )
    except (RuntimeError, ValueError) as error:
        print(f"TW {tweezer}: Gaussian fit failed: {error}")
        return None

    baseline, loss_fraction, x0, sigma = popt
    dx0 = np.sqrt(max(pcov[2, 2], 0))

    p_min = baseline * (1 - loss_fraction)

    # Include covariance when calculating the minimum's uncertainty.
    gradient = np.array([1 - loss_fraction, -baseline, 0, 0])
    dp_min = (
        np.sqrt(max(float(gradient @ pcov @ gradient), 0))
        if np.all(np.isfinite(pcov))
        else np.nan
    )

    x_curve = np.linspace(np.min(x), np.max(x), 500)

    ax.plot(
        x_curve,
        loss_gaussian(x_curve, *popt),
        "--",
        color=color,
        linewidth=2,
        label=f"TW {tweezer} Gaussian loss",
    )

    ax.plot(
        x0, p_min,
        marker="v",
        linestyle="none",
        color=color,
        markersize=9,
    )
    #print(f"SIGMA {sigma}")
    # print(
    #     f"TW {tweezer}: loss minimum = {x0:.6f} ± {dx0:.6f} MHz; "
    #     f"P_min = {p_min:.4f} ± {dp_min:.4f}"
    # )

    return popt, pcov
def plot_mj0_survival_per_tweezer(
    df: pd.DataFrame,
    analyser: pd.DataFrame,
    dataset_label: str,
):
    """
    Plot conditional survival versus SisyphusMJ0_Freq
    separately for selected tweezers.

    For tweezer i:

        P_i =
            N(first occupied AND second occupied)
            / N(first occupied)

    Only tweezers listed in TWEEZERS_TO_PLOT are shown.
    """

    figure_name = "MJ0 survival per tweezer"

    # ---------------------------------------------------------
    # Check globals
    # ---------------------------------------------------------

    if "MJ0_Spectroscopy" not in df.columns:
        return None

    if "SisyphusMJ0_Freq" not in df.columns:
        return None

    mj0_raw = scalar_per_shot(
        df["MJ0_Spectroscopy"],
        "MJ0_Spectroscopy",
    )

    mj0_enabled = (
        np.isfinite(mj0_raw)
        & (mj0_raw != 0)
    )

    # Do not show a stale MJ0 plot if current shot has MJ0 off
    if not mj0_enabled[-1]:
        plt.close(figure_name)
        return None

    frequencies = scalar_per_shot(
        df["SisyphusMJ0_Freq"],
        "SisyphusMJ0_Freq",
    )

    fig = plt.figure(
        figure_name,
        figsize=(10, 6),
    )
    fig.clear()

    ax = fig.add_subplot(111)

    colors = plt.cm.turbo(
        np.linspace(0, 1, N_TWEEZERS)
    )

    # ---------------------------------------------------------
    # One survival curve per selected tweezer
    # ---------------------------------------------------------
    valley_array = np.full(N_TWEEZERS, np.nan)
    for tweezer in TWEEZERS_TO_PLOT:

        first_column = f"tw{tweezer}_occupied"
        second_column = f"tw{tweezer}_occupied_2nd"

        if first_column not in analyser.columns:
            print(
                f"Skipping TW {tweezer}: "
                f"missing {first_column}"
            )
            continue

        if second_column not in analyser.columns:
            print(
                f"Skipping TW {tweezer}: "
                f"missing {second_column}"
            )
            continue

        first_occ = scalar_per_shot(
            analyser[first_column],
            first_column,
        )

        second_occ = scalar_per_shot(
            analyser[second_column],
            second_column,
        )

        valid = (
            mj0_enabled
            & np.isfinite(frequencies)
            & np.isfinite(first_occ)
            & np.isfinite(second_occ)
        )

        unique_frequencies = np.sort(
            np.unique(frequencies[valid])
        )

        survival_values = []
        survival_errors = []
        initial_counts = []
        survived_counts = []
        for frequency in unique_frequencies:

            frequency_mask = (
                valid
                & np.isclose(
                    frequencies,
                    frequency,
                )
            )

            # Only repetitions where THIS tweezer
            # contained an atom in image 1
            initially_loaded = (
                frequency_mask
                & (first_occ == 1)
            )

            n_initial = np.count_nonzero(
                initially_loaded
            )

            survived = (
                initially_loaded
                & (second_occ == 1)
            )

            n_survived = np.count_nonzero(
                survived
            )
            initial_counts.append(n_initial)
            survived_counts.append(n_survived)
            if n_initial > 0:

                p_survival = (
                    n_survived / n_initial
                )

                sem = np.sqrt(
                    p_survival
                    * (1.0 - p_survival)
                    / n_initial
                )

            else:

                p_survival = np.nan
                sem = np.nan

            survival_values.append(
                p_survival
            )

            survival_errors.append(
                sem
            )

        color = colors[tweezer - 1]

        ax.errorbar(
            unique_frequencies,
            survival_values,
            yerr=survival_errors,
            fmt="o-",
            capsize=3,
            markersize=5,
            linewidth=1.2,
            color=color,
            label=f"TW {tweezer}",
        )

        if FIT_MJ0_LOSS_GAUSSIAN:
            fit_result = fit_mj0_loss_gaussian(
                ax=ax,
                frequencies=unique_frequencies,
                n_initial=initial_counts,
                n_survived=survived_counts,
                tweezer=tweezer,
                color=color,
                x_min=None,
                x_max=None,
            )

            if fit_result is not None:
                popt, pcov = fit_result

                valley_array[tweezer - 1] = popt[2]
                sigma_array[tweezer - 1] = abs(popt[3])
    values = ", ".join(
        repr(float(value)) if np.isfinite(value) else "np.nan"
        for value in valley_array
    )
    print(f"\nvalley_array = np.array([{values}])")

    if PLOT_SIGMA:
        sigma_fig = plot_sigma_heatmap(
            sigma_array,
            dataset_label=dataset_label,
        )

    # ---------------------------------------------------------
    # Figure formatting
    # ---------------------------------------------------------

    ax.set_xlabel(
        "SisyphusMJ0_Freq (MHz)"
    )

    ax.set_ylabel(
        "Conditional survival"
    )

    ax.set_ylim(
        -0.05,
        1.05,
    )

    ax.set_title(
        f"mJ = 0 loss spectroscopy - "
        f"{dataset_label}"
    )

    ax.grid(alpha=0.25)

    ax.legend(
        title="Tweezer",
        ncol=2,
    )

    fig.tight_layout()

    return fig
def plot_sigma_heatmap(
    sigma_array,
    dataset_label="",
    plot_number=1,
):
    """
    Display sigma values for 36 tweezers in a 6x6 heatmap.
    Each cell is labeled with its tweezer number and sigma.
    """

    sigma_array = np.asarray(sigma_array, dtype=float)

    if sigma_array.size != 36:
        raise ValueError("Expected exactly 36 sigma values.")

    sigma_grid = sigma_array.reshape(6, 6)

    fig, ax = plt.subplots(figsize=(9, 7))

    sns.heatmap(
        sigma_grid,
        annot=True,
        fmt=".4f",
        cmap="viridis",
        linewidths=1,
        linecolor="white",
        mask=~np.isfinite(sigma_grid),
        cbar_kws={"label": "Fitted sigma"},
        ax=ax,
    )

    # Tweezer numbers: 1-6, 7-12, ..., 31-36
    ax.set_xticklabels(range(1, 7))
    ax.set_yticklabels(
        [f"{i*6 + 1}-{i*6 + 6}" for i in range(6)],
        rotation=0,
    )

    ax.set_xlabel("Column within tweezer array")
    ax.set_ylabel("Tweezer row")

    ax.set_title(
        f"Gaussian fit sigma - {dataset_label}\n"
        f"Heatmap {plot_number}"
    )

    fig.tight_layout()

    return fig
def plot_survival_per_tweezer(
    df,
    analyser,
    dataset_label,
    mode_flag,
    scan_name,
    x_label,
    figure_name,
    x_scale=1.0,
):
    """
    Plot conditional survival for selected individual tweezers.

    MJ1: Image 2 -> Image 3 vs SisyphusMJ1_Freq
    R&R: Image 2 -> Image 3 vs release_time

    Only shots where the selected experiment is enabled are used.
    """

    if mode_flag not in df.columns or scan_name not in df.columns:
        print(f"Skipping {figure_name}: missing experiment globals.")
        return None

    # ---------------------------------------------------------
    # Select shots belonging to this experiment.
    # ---------------------------------------------------------

    mode_values = scalar_per_shot(df[mode_flag], mode_flag)

    enabled = (
        np.isfinite(mode_values)
        & (mode_values != 0)
    )

    if not enabled[-1]:
        plt.close(figure_name)
        return None

    x_values = (
        scalar_per_shot(df[scan_name], scan_name)
        * x_scale
    )

    # Group identical scan values, suppressing tiny float differences.
    x_values = np.round(x_values, 6)

    fig = plt.figure(figure_name, figsize=(10, 6))
    fig.clear()

    ax = fig.add_subplot(111)

    colors = plt.cm.turbo(
        np.linspace(0, 1, N_TWEEZERS)
    )

    plotted = 0

    # ---------------------------------------------------------
    # Plot one conditional-survival curve per selected tweezer.
    # ---------------------------------------------------------

    for tweezer in TWEEZERS_TO_PLOT:

        if not 1 <= tweezer <= N_TWEEZERS:
            raise ValueError(
                f"Invalid tweezer index: {tweezer}"
            )

        initial_column = f"tw{tweezer}_occupied_2nd"
        final_column = f"tw{tweezer}_occupied_3rd"

        if (
            initial_column not in analyser.columns
            or final_column not in analyser.columns
        ):
            print(
                f"Skipping TW {tweezer}: "
                "missing occupancy results."
            )
            continue

        initial_occ = scalar_per_shot(
            analyser[initial_column],
            initial_column,
        )

        final_occ = scalar_per_shot(
            analyser[final_column],
            final_column,
        )

        valid = (
            enabled
            & np.isfinite(x_values)
            & np.isfinite(initial_occ)
            & np.isfinite(final_occ)
        )

        if not np.any(valid):
            continue

        unique_x = np.sort(np.unique(x_values[valid]))

        survival_values = []
        survival_errors = []

        # -----------------------------------------------------
        # Calculate conditional survival at each scan value.
        # -----------------------------------------------------

        for x in unique_x:

            frequency_mask = valid & (x_values == x)

            # Only count shots where THIS tweezer was occupied
            # before MJ1 spectroscopy or release-and-recapture.
            initially_loaded = (
                frequency_mask
                & (initial_occ == 1)
            )

            n_initial = np.count_nonzero(initially_loaded)

            survived = (
                initially_loaded
                & (final_occ == 1)
            )

            n_survived = np.count_nonzero(survived)

            if n_initial > 0:

                p_survival = n_survived / n_initial

                sem = np.sqrt(
                    p_survival
                    * (1.0 - p_survival)
                    / n_initial
                )

            else:

                p_survival = np.nan
                sem = np.nan

            survival_values.append(p_survival)
            survival_errors.append(sem)

        # Don't draw an empty curve.
        if not np.any(np.isfinite(survival_values)):
            continue

        color = colors[tweezer - 1]

        ax.errorbar(
            unique_x,
            survival_values,
            yerr=survival_errors,
            fmt="o-",
            capsize=3,
            markersize=5,
            linewidth=1.2,
            color=color,
            label=f"TW {tweezer}",
        )

        plotted += 1

    if plotted == 0:
        plt.close(fig)
        print(f"No valid individual-tweezer data for {figure_name}.")
        return None

    # ---------------------------------------------------------
    # Figure formatting
    # ---------------------------------------------------------

    ax.set_xlabel(x_label)

    ax.set_ylabel(
        r"$P(\mathrm{image\ 3\ occupied}\mid"
        r"\mathrm{image\ 2\ occupied})$"
    )

    ax.set_ylim(-0.05, 1.05)

    ax.set_title(
        f"{figure_name} - {dataset_label}"
    )

    ax.grid(alpha=0.25)

    ax.legend(
        title="Tweezer",
        ncol=2,
    )

    fig.tight_layout()

    return fig
def validate_scan_configuration(df: pd.DataFrame):
    """Check scan-parameter and plot configuration before running."""
    if not SCAN_NAMES:
        raise ValueError("SCAN_NAMES cannot be empty.")

    if len(SCAN_NAMES) != len(SCAN_UNITS):
        raise ValueError(
            "SCAN_NAMES and SCAN_UNITS must have the same number of entries."
        )

    duplicates = sorted(
        name
        for name in set(SCAN_NAMES)
        if SCAN_NAMES.count(name) > 1
    )

    if duplicates:
        raise ValueError(
            f"Duplicate names in SCAN_NAMES: {', '.join(duplicates)}"
        )

    missing = [
        name
        for name in SCAN_NAMES
        if name not in df.columns
    ]

    if missing:
        raise KeyError(
            "The following scan globals are not present in Lyse data: "
            + ", ".join(missing)
        )

    # PLOT_AXES may select either one plotted parameter or two:
    if len(PLOT_AXES) not in (1, 2):
        raise ValueError(
            "PLOT_AXES must contain either one index, e.g. (0,), "
            "or two indices, e.g. (0, 1)."
        )

    if len(set(PLOT_AXES)) != len(PLOT_AXES):
        raise ValueError("PLOT_AXES cannot contain duplicate indices.")

    if any(index < 0 or index >= len(SCAN_NAMES) for index in PLOT_AXES):
        raise ValueError(
            "PLOT_AXES contains an index outside SCAN_NAMES."
        )

    unknown_fixed = set(FIXED_VALUES) - set(SCAN_NAMES)

    if unknown_fixed:
        raise KeyError(
            "FIXED_VALUES contains unknown scan names: "
            + ", ".join(sorted(unknown_fixed))
        )

def load_roi_integrals(analyser: pd.DataFrame, suffix: str = "") -> np.ndarray:
    """
    Return ROI integrals as an array of shape:

        (number_of_tweezers, number_of_shots)
    """
    columns = [
        f"tw{i}_integral{suffix}"
        for i in range(1, N_TWEEZERS + 1)
    ]

    missing = [column for column in columns if column not in analyser.columns]
    if missing:
        raise KeyError(
            f"Missing ROI-integral columns for suffix '{suffix}': "
            + ", ".join(missing)
        )

    values = analyser.loc[:, columns].to_numpy(dtype=float).T

    if values.shape[0] != N_TWEEZERS:
        raise RuntimeError("Unexpected number of loaded tweezer ROIs.")

    return values


def make_dataset_label(paths: pd.Series) -> str:
    """Create a useful label such as dataset 0042-0054."""
    runs = paths.str.extract(r"_(\d{4})_")[0].dropna()

    if runs.empty:
        return "loaded dataset"

    runs = runs.astype(int)
    if runs.min() == runs.max():
        return f"dataset {runs.min():04d}"

    return f"dataset {runs.min():04d}-{runs.max():04d}"


def output_directory(paths: pd.Series) -> Path:
    """
    Keep the original convention:
    save one directory above the run-file directory.
    """
    return Path(paths.iloc[-1]).parent.parent


def aggregate_nd_scan(
    scan_values: list[np.ndarray],
    roi_integrals: np.ndarray,
    shot_name: str,
) -> pd.DataFrame:
    """
    Aggregate all loaded shots by their full N-dimensional scan coordinate.

    For each coordinate:
    1. average repeated experimental shots for each tweezer;
    2. calculate the mean across the 36 tweezers;
    3. calculate SEM across the 36 tweezer means.
    """
    n_shots = roi_integrals.shape[1]

    if any(values.size != n_shots for values in scan_values):
        raise ValueError("Each scan parameter must have one value per shot.")

    bins = defaultdict(list)

    for shot_index in range(n_shots):
        coordinate = tuple(
            values[shot_index]
            for values in scan_values
        )
        bins[coordinate].append(shot_index)

    rows = []

    for coordinate in sorted(bins):
        shot_indices = bins[coordinate]

        # Shape: (N_TWEEZERS, repetitions at this N-D coordinate)
        samples = roi_integrals[:, shot_indices]

        # One mean value per tweezer at this coordinate:
        tweezer_means = np.nanmean(samples, axis=1)

        n_valid = np.sum(np.isfinite(samples), axis=1)

        tweezer_sems = np.full(N_TWEEZERS, np.nan)

        valid = n_valid > 1

        tweezer_sems[valid] = (
            np.nanstd(samples[valid], axis=1, ddof=1)
            / np.sqrt(n_valid[valid])
        )


        n_valid_tweezers = np.sum(np.isfinite(tweezer_means))
        mean_value = np.nanmean(tweezer_means)

        if n_valid_tweezers > 1:
            sem_value = (
                np.nanstd(tweezer_means, ddof=1)
                / np.sqrt(n_valid_tweezers)
            )
        else:
            sem_value = np.nan

        row = {
            "shot": shot_name,
            "mean_roi_integral": mean_value,
            "sem_roi_integral": sem_value,
            "n_tweezers": n_valid_tweezers,
            "n_repetitions": len(shot_indices),
        }

        for i, (mean, sem) in enumerate(
            zip(tweezer_means, tweezer_sems),
            start=1,
        ):
            row[f"tw{i}_mean"] = mean
            row[f"tw{i}_sem"] = sem


        for name, value in zip(SCAN_NAMES, coordinate):
            row[name] = value

        rows.append(row)

    return pd.DataFrame(rows)


def choose_fixed_value(results, parameter_name):
    available = np.sort(
        results[parameter_name].dropna().unique()
    )
    available = available[np.isfinite(available)]

    if available.size == 0:
        raise ValueError(
            f"No valid values found for {parameter_name}."
        )

    if parameter_name in FIXED_VALUES:
        requested = FIXED_VALUES[parameter_name]
        return available[
            np.argmin(np.abs(available - requested))
        ]

    return available[len(available) // 2]

def plot_1d(results: pd.DataFrame, dataset_label: str):
    """Plot both fluorescence shots for a one-parameter scan."""
    parameter = SCAN_NAMES[0]
    unit = SCAN_UNITS[0]

    fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)

    for shot, color, marker in (
        ("first", "black", "o"),
        ("second", "tab:blue", "s"),
    ):
        data = results[results["shot"] == shot].sort_values(parameter)

        ax.errorbar(
            data[parameter],
            data["mean_roi_integral"],
            yerr=data["sem_roi_integral"],
            fmt=f"{marker}--",
            color=color,
            capsize=4,
            label=shot.capitalize() + " shot",
        )

    ax.set_title(f"Tweezer ROI integral - {dataset_label}")
    ax.set_xlabel(f"{parameter} ({unit})")
    ax.set_ylabel("Mean ROI integral")
    ax.grid(alpha=0.25)
    ax.legend()

    return fig


def plot_2d_heatmap(
    results: pd.DataFrame,
    shot_name: str,
    x_parameter: str,
    y_parameter: str,
    fixed_dimensions: dict[str, float],
    dataset_label: str,
):
    """Create one heatmap, optionally at a fixed slice of higher dimensions."""
    data = results[results["shot"] == shot_name].copy()

    for parameter, value in fixed_dimensions.items():
        data = data[np.isclose(data[parameter], value)]

    heatmap = data.pivot_table(
        index=y_parameter,
        columns=x_parameter,
        values="mean_roi_integral",
        aggfunc="mean",
    )

    heatmap = heatmap.sort_index().sort_index(axis=1)

    fig, ax = plt.subplots(figsize=(10, 7), constrained_layout=True)

    sns.heatmap(
        heatmap,
        cmap="viridis",
        annot=True,
        fmt=".1f",
        linewidths=0.4,
        ax=ax,
    )

    # Force one tick per heatmap value and format to 2 decimal places
    ax.set_xticks(np.arange(len(heatmap.columns)) + 0.5)
    ax.set_xticklabels([f"{x:.2f}" for x in heatmap.columns])

    ax.set_yticks(np.arange(len(heatmap.index)) + 0.5)
    ax.set_yticklabels([f"{y:.2f}" for y in heatmap.index])

    x_unit = SCAN_UNITS[SCAN_NAMES.index(x_parameter)]
    y_unit = SCAN_UNITS[SCAN_NAMES.index(y_parameter)]

    slice_text = ", ".join(
        f"{name}={value:g}"
        for name, value in fixed_dimensions.items()
    )

    title = f"Tweezer ROI integral - {shot_name} shot ({dataset_label})"
    if slice_text:
        title += f"\n{slice_text}"

    ax.set_title(title)
    ax.set_xlabel(f"{x_parameter} ({x_unit})")
    ax.set_ylabel(f"{y_parameter} ({y_unit})")

    return fig


def plot_nd(
    results: pd.DataFrame,
    dataset_label: str,
) -> list[tuple[str, plt.Figure]]:
    """
    Plot either:

    PLOT_AXES = (i,)      -> 1D error-bar plot versus SCAN_NAMES[i]
    PLOT_AXES = (i, j)    -> 2D heatmap with all other parameters fixed

    Any number of scan parameters in SCAN_NAMES is supported.
    """
    n_plot_axes = len(PLOT_AXES)

    if n_plot_axes not in (1, 2):
        raise ValueError(
            "PLOT_AXES must contain either one index, e.g. (0,), "
            "or two indices, e.g. (0, 1)."
        )

    if len(set(PLOT_AXES)) != n_plot_axes:
        raise ValueError("PLOT_AXES cannot contain the same index twice.")

    if any(index < 0 or index >= len(SCAN_NAMES) for index in PLOT_AXES):
        raise ValueError(
            "An index in PLOT_AXES is outside SCAN_NAMES."
        )

    # =====================================================================
    # 1D plot
    # =====================================================================
    if n_plot_axes == 1:
        parameter = SCAN_NAMES[PLOT_AXES[0]]
        unit = SCAN_UNITS[PLOT_AXES[0]]

        # Fix every other scan parameter to the chosen/default value:
        fixed_dimensions = {
            name: choose_fixed_value(results, name)
            for name in SCAN_NAMES
            if name != parameter
        }

        fig, ax = plt.subplots(
            figsize=(10, 6),
            constrained_layout=True,
        )

        for shot_name, color, marker in (
            ("first", "black", "o"),
            ("second", "tab:blue", "s"),
             ("third", "tab:red", "^"),
        ):
            data = results[
                results["shot"] == shot_name
            ].copy()

            # Select the desired N-D slice:
            for name, value in fixed_dimensions.items():
                data = data[
                    np.isclose(data[name], value)
                ]

            data = data.sort_values(parameter)

            ax.errorbar(
                data[parameter],
                data["mean_roi_integral"],
                yerr=data["sem_roi_integral"],
                fmt=f"{marker}--",
                color=color,
                ecolor=color,
                capsize=4,
                label=f"{shot_name.capitalize()} image",
            )

        fixed_text = ", ".join(
            f"{name}={value:g}"
            for name, value in fixed_dimensions.items()
        )

        title = f"Tweezer ROI integral - {dataset_label}"
        if fixed_text:
            title += f"\n{fixed_text}"

        ax.set_title(title)
        ax.set_xlabel(f"{parameter} ({unit})")
        ax.set_ylabel("Mean ROI integral")
        ax.grid(alpha=0.25)
        ax.legend()

        return [("1D_scan", fig)]

    # =====================================================================
    # 2D plot
    # =====================================================================
    x_parameter = SCAN_NAMES[PLOT_AXES[0]]
    y_parameter = SCAN_NAMES[PLOT_AXES[1]]

    fixed_dimensions = {
        name: choose_fixed_value(results, name)
        for name in SCAN_NAMES
        if name not in (x_parameter, y_parameter)
    }

    figures = []

    for shot_name in ("first", "second","third"):
        figure = plot_2d_heatmap(
            results=results,
            shot_name=shot_name,
            x_parameter=x_parameter,
            y_parameter=y_parameter,
            fixed_dimensions=fixed_dimensions,
            dataset_label=dataset_label,
        )

        figures.append((f"{shot_name}_heatmap", figure))

    return figures

def plot_individual_tweezers(results, dataset_label):
    parameter = SCAN_NAMES[PLOT_AXES[0]]
    unit = SCAN_UNITS[PLOT_AXES[0]]

    fig, axes = plt.subplots(
        6, 6,
        figsize=(18, 16),
        constrained_layout=True,
    )

    axes = axes.flatten()

    for tweezer in range(1, N_TWEEZERS + 1):
        ax = axes[tweezer - 1]

        for shot_name, color, marker in (
            ("first", "black", "o"),
            ("second", "tab:blue", "s"),
            ("third", "tab:red", "^"),
        ):
            data = results[
                results["shot"] == shot_name
            ].copy()

            data = data.sort_values(parameter)

            ax.plot(
                data[parameter],
                data[f"tw{tweezer}_mean"],
                f"{marker}--",
                color=color,
                markersize=3,
                label=shot_name.capitalize(),
            )

        ax.set_title(f"TW {tweezer}", fontsize=10)
        ax.grid(alpha=0.25)

    fig.suptitle(
        f"Individual tweezer ROI - {dataset_label}",
        fontsize=16,
    )

    # Una sola legenda per tutta la figura
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper right",
    )

    return [("individual_tweezers", fig)]
def plot_survival_scan(
    df,
    analyser,
    dataset_label,
    mode_flag,
    scan_name,
    x_label,
    figure_name,
    x_scale=1.0,
):
    """
    Plot conditional survival over all tweezers and repetitions.

    MJ1: Image 2 -> Image 3 vs SisyphusMJ1_Freq
    R&R: Image 2 -> Image 3 vs release_time
    """

    required_globals = [mode_flag, scan_name]
    required_results = [
        "recapture_n_initial",
        "recapture_n_survived",
    ]

    missing = (
        [name for name in required_globals if name not in df.columns]
        + [name for name in required_results if name not in analyser.columns]
    )

    if missing:
        print(f"Skipping {figure_name}. Missing: {missing}")
        return None

    # Only use shots where this experiment was enabled.
    mode_values = scalar_per_shot(df[mode_flag], mode_flag)
    enabled = np.isfinite(mode_values) & (mode_values != 0)

    if not enabled[-1]:
        plt.close(figure_name)
        return None

    x_values = (
        scalar_per_shot(df[scan_name], scan_name) * x_scale
    )

    n_initial = scalar_per_shot(
        analyser["recapture_n_initial"],
        "recapture_n_initial",
    )

    n_survived = scalar_per_shot(
        analyser["recapture_n_survived"],
        "recapture_n_survived",
    )

    valid = (
        enabled
        & np.isfinite(x_values)
        & np.isfinite(n_initial)
        & np.isfinite(n_survived)
        & (n_initial > 0)
        & (n_survived >= 0)
        & (n_survived <= n_initial)
    )

    if not np.any(valid):
        print(f"No valid measurements for {figure_name}.")
        return None

    # Group repetitions at each scanned value.
    measurements = pd.DataFrame({
        "x": np.round(x_values[valid], 6),
        "n_initial": n_initial[valid],
        "n_survived": n_survived[valid],
    })

    grouped = (
        measurements
        .groupby("x", sort=True)
        .agg(
            n_initial=("n_initial", "sum"),
            n_survived=("n_survived", "sum"),
            n_shots=("x", "size"),
        )
        .reset_index()
    )

    grouped["survival"] = (
        grouped["n_survived"] / grouped["n_initial"]
    )

    grouped["sem"] = np.sqrt(
        grouped["survival"]
        * (1.0 - grouped["survival"])
        / grouped["n_initial"]
    )

    # Plot.
    fig = plt.figure(figure_name, figsize=(9, 6))
    fig.clear()
    ax = fig.add_subplot(111)

    ax.errorbar(
        grouped["x"],
        grouped["survival"],
        yerr=grouped["sem"],
        fmt="o-",
        capsize=4,
        markersize=6,
    )

    ax.set_xlabel(x_label)
    ax.set_ylabel(
        r"$P(\mathrm{image\ 3\ occupied}\mid"
        r"\mathrm{image\ 2\ occupied})$"
    )
    ax.set_ylim(-0.05, 1.05)
    ax.set_title(f"{figure_name} - {dataset_label}")
    ax.grid(alpha=0.25)

    fig.tight_layout()

    print(f"\n{figure_name.upper()}:")
    print(grouped.to_string(index=False))

    return fig


def plot_mj1_multiple_curves(
    df,
    analyser,
    dataset_label,
    x_scale=1.0,
    duration_scale=1.0,
):
    figure_name = "MJ1 cooling spectroscopy"

    x_name = "MJ1_Recap_Release_duration"
    duration_name = "MJ1_Spectroscopy_duration"

    required_globals = [
        "MJ1_Spectroscopy",
        x_name,
        duration_name,
    ]
    required_results = [
        "recapture_n_initial",
        "recapture_n_survived",
    ]

    missing = (
        [name for name in required_globals if name not in df.columns]
        + [name for name in required_results
           if name not in analyser.columns]
    )

    if missing:
        print(f"Skipping {figure_name}. Missing: {missing}")
        return None

    # Seleziona solo gli shot MJ1 attivi
    enabled = scalar_per_shot(
        df["MJ1_Spectroscopy"], "MJ1_Spectroscopy"
    ) != 0

    if not enabled[-1]:
        plt.close(figure_name)
        return None

    # Parametro sull'asse X
    x_values = (
        scalar_per_shot(df[x_name], x_name) * x_scale
    )

    # Parametro che distingue le curve
    duration_values = (
        scalar_per_shot(df[duration_name], duration_name)
        * duration_scale
    )

    n_initial = scalar_per_shot(
        analyser["recapture_n_initial"],
        "recapture_n_initial",
    )

    n_survived = scalar_per_shot(
        analyser["recapture_n_survived"],
        "recapture_n_survived",
    )

    valid = (
        enabled
        & np.isfinite(x_values)
        & np.isfinite(duration_values)
        & np.isfinite(n_initial)
        & np.isfinite(n_survived)
        & (n_initial > 0)
        & (n_survived >= 0)
        & (n_survived <= n_initial)
    )

    if not np.any(valid):
        print("No valid MJ1 measurements.")
        return None

    # Una riga per ogni shot valido
    measurements = pd.DataFrame({
        "x": np.round(x_values[valid], 6),
        "duration": np.round(duration_values[valid], 6),
        "n_initial": n_initial[valid],
        "n_survived": n_survived[valid],
    })

    # Raggruppa per entrambe le variabili
    grouped = (
        measurements
        .groupby(["duration", "x"], sort=True)
        .agg(
            n_initial=("n_initial", "sum"),
            n_survived=("n_survived", "sum"),
        )
        .reset_index()
    )

    # Probabilità di sopravvivenza
    grouped["survival"] = (
        grouped["n_survived"] / grouped["n_initial"]
    )

    # Errore binomiale
    grouped["sem"] = np.sqrt(
        grouped["survival"]
        * (1 - grouped["survival"])
        / grouped["n_initial"]
    )

    # Grafico con una curva per ogni durata
    fig = plt.figure(figure_name, figsize=(10, 6))
    fig.clear()
    ax = fig.add_subplot(111)

    durations = np.sort(grouped["duration"].unique())
    colors = plt.cm.viridis(
        np.linspace(0, 1, len(durations))
    )

    for color, duration in zip(colors, durations):
        data = grouped[
            grouped["duration"] == duration
        ].sort_values("x")

        ax.errorbar(
            data["x"],
            data["survival"],
            yerr=data["sem"],
            fmt="o-",
            capsize=4,
            markersize=5,
            linewidth=1.5,
            color=color,
            label=f"{duration:g} ms",
        )

    ax.set_xlabel("MJ1 Recap Release duration (us)")
    ax.set_ylabel(
        r"$P(\mathrm{image\ 3\ occupied}\mid"
        r"\mathrm{image\ 2\ occupied})$"
    )

    ax.set_ylim(-0.05, 1.05)
    ax.set_title(
        f"MJ1 cooling spectroscopy - {dataset_label}"
    )
    ax.grid(alpha=0.25)
    ax.legend(
        title="MJ1 Spectroscopy duration",
        loc="best",
    )

    fig.tight_layout()

    print("\nMJ1 MULTIPLE CURVES:")
    print(grouped.to_string(index=False))

    return fig



def plot_all_tweezers_three_shots(results, dataset_label):
    """
    Create one figure with three subplots:
        - first image
        - second image
        - third image

    Only the tweezers listed in TWEEZERS_TO_PLOT are plotted.

    Each tweezer has:
        - a unique color
        - points
        - connecting line
        - error bars
    """

    parameter = SCAN_NAMES[PLOT_AXES[0]]
    unit = SCAN_UNITS[PLOT_AXES[0]]

    shot_configs = (
        ("first", "o"),
        ("second", "s"),
        ("third", "^"),
    )

    # -------------------------------------------------------------
    # Colors are assigned according to tweezer number,
    # not according to the selected subset.
    # -------------------------------------------------------------
    colors = plt.cm.turbo(
        np.linspace(0, 1, N_TWEEZERS)
    )

    fig, axes = plt.subplots(
        3,
        1,
        figsize=(12, 16),
        sharex=True,
        constrained_layout=True,
    )

    fit_results_table = []

    for ax, (shot_name, marker) in zip(
        axes,
        shot_configs,
    ):

        data = results[
            results["shot"] == shot_name
        ].copy()

        data = data.sort_values(parameter)


        # ---------------------------------------------------------
        # Plot only selected tweezers
        # ---------------------------------------------------------
        for tweezer in TWEEZERS_TO_PLOT:

            color = colors[tweezer - 1]

            ax.errorbar(
                data[parameter],
                data[f"tw{tweezer}_mean"],
                yerr=data[f"tw{tweezer}_sem"],
                fmt=f"{marker}-",
                color=color,
                ecolor=color,
                linewidth=1.0,
                markersize=4,
                alpha=0.75,
                capsize=2,
                elinewidth=0.8,
                label=f"TW {tweezer}",
            )

            # =====================================================
            # SIGMOID FIT - SOLO SECOND IMAGE
            # =====================================================

            if FIT_SIGMOID and shot_name == "second":

                try:

                    fit_result = fit_sigmoid_tweezer(
                        data,
                        parameter,
                        tweezer,
                    )

                    if fit_result is not None:

                        popt = fit_result["popt"]
                        perr = fit_result["perr"]

                        y0, A, x0, k = popt
                        dy0, dA, dx0, dk = perr

                        # curva liscia del fit
                        x_curve = np.linspace(
                            FIT_X_MIN,
                            FIT_X_MAX,
                            300,
                        )

                        y_curve = sigmoid(
                            x_curve,
                            *popt,
                        )

                        ax.plot(
                            x_curve,
                            y_curve,
                            "--",
                            color=color,
                            linewidth=2,
                        )

                        fit_results_table.append({
                            "Tweezer": tweezer,
                            "y0": y0,
                            "dy0": dy0,
                            "A": A,
                            "dA": dA,
                            "x0_MHz": x0,
                            "dx0_MHz": dx0,
                            "k_MHz": k,
                            "dk_MHz": dk,
                        })

                        
                except Exception as error:

                    print(
                        f"Fit fallito per TW {tweezer}: {error}"
                    )

        ax.set_title(
            f"{shot_name.capitalize()} image",
            fontsize=13,
        )

        ax.set_ylabel("ROI integral")
        ax.grid(alpha=0.25)

    axes[-1].set_xlabel(
        f"{parameter} ({unit})"
    )

    fig.suptitle(
        f"Individual tweezer ROI - selected tweezers ({dataset_label})",
        fontsize=16,
    )

    # -------------------------------------------------------------
    # Single legend
    # -------------------------------------------------------------
    handles, labels = axes[0].get_legend_handles_labels()

    fig.legend(
        handles,
        labels,
        loc="center left",
        bbox_to_anchor=(1.01, 0.5),
        ncol=2,
        fontsize=9,
        title="Tweezers",
    )

    if fit_results_table:
    
        fit_df = pd.DataFrame(fit_results_table)

        print("\nSIGMOID FIT RESULTS - SECOND IMAGE")
        print(
            fit_df.to_string(
                index=False,
                formatters={
                    "y0": "{:.3f}".format,
                    "dy0": "{:.3f}".format,
                    "A": "{:.3f}".format,
                    "dA": "{:.3f}".format,
                    "x0_MHz": "{:.6f}".format,
                    "dx0_MHz": "{:.6f}".format,
                    "k_MHz": "{:.6f}".format,
                    "dk_MHz": "{:.6f}".format,
                }
            )
        )

        print("x0_array = np.array(" + repr(fit_df["x0_MHz"].to_numpy().tolist()) + ")")


    return [
        ("all_tweezers_three_shots", fig)
    ]


def sigmoid(x, y0, A, x0, k):
    """
    y0 = baseline
    A  = amplitude
    x0 = midpoint of the sigmoid
    k  = width/slope parameter
    """
    return y0 + A / (1 + np.exp(-(x - x0) / k))

def fit_sigmoid_tweezer(data, parameter, tweezer):
    
    x = data[parameter].to_numpy(dtype=float)
    y = data[f"tw{tweezer}_mean"].to_numpy(dtype=float)
    yerr = data[f"tw{tweezer}_sem"].to_numpy(dtype=float)

    # Seleziona solo la parte sinistra del grafico
    mask = (
        np.isfinite(x)
        & np.isfinite(y)
        & (x >= FIT_X_MIN)
        & (x <= FIT_X_MAX)
    )

    x_fit = x[mask]
    y_fit = y[mask]
    yerr_fit = yerr[mask]

    if len(x_fit) < 4:
        print(f"TW {tweezer}: non abbastanza punti per il fit")
        return None

    # -----------------------------------------------------
    # Initial guesses
    # -----------------------------------------------------

    y0_guess = np.min(y_fit)
    A_guess = np.max(y_fit) - np.min(y_fit)

    # metà altezza
    half_height = y0_guess + A_guess / 2

    x0_guess = x_fit[
        np.argmin(np.abs(y_fit - half_height))
    ]

    k_guess = 0.05

    p0 = [
        y0_guess,
        A_guess,
        x0_guess,
        k_guess,
    ]

    # -----------------------------------------------------
    # Usa le errorbar come pesi, se sono valide
    # -----------------------------------------------------

    valid_sigma = (
        np.all(np.isfinite(yerr_fit))
        and np.all(yerr_fit > 0)
    )

    if valid_sigma:

        popt, pcov = curve_fit(
            sigmoid,
            x_fit,
            y_fit,
            p0=p0,
            sigma=yerr_fit,
            absolute_sigma=True,
            maxfev=20000,
        )

    else:

        popt, pcov = curve_fit(
            sigmoid,
            x_fit,
            y_fit,
            p0=p0,
            maxfev=20000,
        )

    perr = np.sqrt(np.diag(pcov))

    return {
        "popt": popt,
        "perr": perr,
        "x_fit": x_fit,
        "y_fit": y_fit,
    }

def fit_sigmoid_mean(data, parameter):
    
    x = data[parameter].to_numpy(dtype=float)
    y = data["mean_roi_integral"].to_numpy(dtype=float)
    yerr = data["sem_roi_integral"].to_numpy(dtype=float)

    mask = (
        np.isfinite(x)
        & np.isfinite(y)
        & (x >= FIT_X_MIN)
        & (x <= FIT_X_MAX)
    )

    x_fit = x[mask]
    y_fit = y[mask]
    yerr_fit = yerr[mask]

    if len(x_fit) < 4:
        print("Mean second image: non abbastanza punti per il fit")
        return None

    # Initial guesses
    y0_guess = np.min(y_fit)
    A_guess = np.max(y_fit) - np.min(y_fit)

    half_height = y0_guess + A_guess / 2

    x0_guess = x_fit[
        np.argmin(np.abs(y_fit - half_height))
    ]

    k_guess = 0.05

    p0 = [
        y0_guess,
        A_guess,
        x0_guess,
        k_guess,
    ]

    # Use SEM as weights if valid
    valid_sigma = (
        np.all(np.isfinite(yerr_fit))
        and np.all(yerr_fit > 0)
    )

    if valid_sigma:

        popt, pcov = curve_fit(
            sigmoid,
            x_fit,
            y_fit,
            p0=p0,
            sigma=yerr_fit,
            absolute_sigma=True,
            maxfev=20000,
        )

    else:

        popt, pcov = curve_fit(
            sigmoid,
            x_fit,
            y_fit,
            p0=p0,
            maxfev=20000,
        )

    perr = np.sqrt(np.diag(pcov))

    return {
        "popt": popt,
        "perr": perr,
        "x_fit": x_fit,
        "y_fit": y_fit,
    }


def plot_hold_survival_1_2(df, analyser, dataset_label):

    figure_name = "Survival Image 1 to 2"

    scan_name = "holdTime_between_images_1_2"

    if scan_name not in df.columns:
        print(f"Missing global: {scan_name}")
        return None

    if "second_shot" in df.columns:
        second_enabled = scalar_per_shot(
            df["second_shot"], "second_shot"
        ) != 0
    else:
        print("Missing global: second_shot")
        return None

    hold_times = scalar_per_shot(
        df[scan_name], scan_name
    )

    # Use the units stored in GLOBALS (typically us).
    hold_times = np.round(hold_times / 1000, 9)

    n_initial = np.zeros(len(df))
    n_survived = np.zeros(len(df))

    for tweezer in TWEEZERS_TO_PLOT:

        col1 = f"tw{tweezer}_occupied"
        col2 = f"tw{tweezer}_occupied_2nd"

        if col1 not in analyser.columns or col2 not in analyser.columns:
            print(f"Missing occupancy data for TW {tweezer}")
            continue

        occ1 = scalar_per_shot(analyser[col1], col1)
        occ2 = scalar_per_shot(analyser[col2], col2)

        valid = (
            np.isfinite(occ1)
            & np.isfinite(occ2)
        )

        n_initial += (
            valid & (occ1 == 1)
        ).astype(int)

        n_survived += (
            valid & (occ1 == 1) & (occ2 == 1)
        ).astype(int)

    valid_shots = (
        second_enabled
        & np.isfinite(hold_times)
        & (n_initial > 0)
    )

    if not np.any(valid_shots):
        print("No valid Image 1 -> Image 2 survival data.")
        return None

    measurements = pd.DataFrame({
        "hold_time": hold_times[valid_shots],
        "n_initial": n_initial[valid_shots],
        "n_survived": n_survived[valid_shots],
    })

    grouped = (
        measurements
        .groupby("hold_time", sort=True)
        .agg(
            n_initial=("n_initial", "sum"),
            n_survived=("n_survived", "sum"),
            n_shots=("hold_time", "size"),
        )
        .reset_index()
    )

    grouped["survival"] = (
        grouped["n_survived"] / grouped["n_initial"]
    )

    grouped["sem"] = np.sqrt(
        grouped["survival"]
        * (1 - grouped["survival"])
        / grouped["n_initial"]
    )

    fig = plt.figure(figure_name, figsize=(9, 6))
    fig.clear()
    ax = fig.add_subplot(111)

    ax.errorbar(
        grouped["hold_time"],
        grouped["survival"],
        yerr=grouped["sem"],
        fmt="o-",
        capsize=4,
        markersize=6,
    )

    ax.set_xlabel("Hold time between images 1 and 2 (s)")
    ax.set_ylabel("Conditional survival probability")
    ax.set_ylim(-0.05, 1.05)
    ax.set_title(f"Survival Image 1 -> 2 - {dataset_label}")
    ax.grid(alpha=0.25)

    fig.tight_layout()

    print("\nSURVIVAL IMAGE 1 -> 2:")
    print(grouped.to_string(index=False))

    return fig


def main():
    df = lyse.data()
    print(df["filepath"].iloc[0])

    if df.empty:
        raise RuntimeError("Lyse has no loaded shots to analyse.")

    if "filepath" not in df.columns:
        raise KeyError("Lyse data does not contain the 'filepath' column.")

    if "FluoAnalyser_tweez" not in df.columns:
        raise KeyError(
            "No 'FluoAnalyser_tweez' results group was found in Lyse data."
        )
    # =========================================================
    # SURVIVAL ANALYSIS: MJ0, MJ1 OR RELEASE-AND-RECAPTURE
    # =========================================================

    paths = df["filepath"]
    analyser = df["FluoAnalyser_tweez"]
    dataset_label = make_dataset_label(paths)
    output_dir = output_directory(paths)

    if PLOT_SURV_PROB:
        hold_survival_figure = plot_hold_survival_1_2(
        df=df,
        analyser=analyser,
        dataset_label=dataset_label,
        )

        if hold_survival_figure is not None:
            if SAVE_PLOTS:
                output_path = output_dir / (
                    f"{dataset_label.replace(' ', '_')}_hold_survival_1_2.png"
                )
                hold_survival_figure.savefig(
                    output_path,
                    dpi=200,
                    bbox_inches="tight",
                )
                print(f"Saved hold survival plot: {output_path}")

            plt.show()

    survival_figure = None
    plot_suffix = None

    individual_figure = None
    individual_suffix = None

    # Check which experiment is enabled in the latest shot.
    mj0_enabled = (
        "MJ0_Spectroscopy" in df.columns
        and bool(df["MJ0_Spectroscopy"].iloc[-1])
    )

    mj1_enabled = (
        "MJ1_Spectroscopy" in df.columns
        and bool(df["MJ1_Spectroscopy"].iloc[-1])
    )

    rr_enabled = (
        "release_recapture" in df.columns
        and bool(df["release_recapture"].iloc[-1])
    )

    # ---------------------------------------------------------
    # MJ0: Image 1 -> Image 2
    # ---------------------------------------------------------

    if mj0_enabled:

        survival_figure = plot_mj0_survival(
            df=df,
            analyser=analyser,
            dataset_label=dataset_label,
        )

        plot_suffix = "MJ0_loss_spectroscopy"
        if PLOT_SURVIVAL_PER_TWEEZER:

            individual_figure = plot_mj0_survival_per_tweezer(
                df=df,
                analyser=analyser,
                dataset_label=dataset_label,
            )

            individual_suffix = "MJ0_survival_per_tweezer"
    # ---------------------------------------------------------
    # MJ1: Image 2 -> Image 3
    # ---------------------------------------------------------


    elif mj1_enabled:

        # survival_figure = plot_survival_scan(
        #     df=df,
        #     analyser=analyser,
        #     dataset_label=dataset_label,
        #     mode_flag="MJ1_Spectroscopy",
        #     scan_name=MJ1_SCAN_NAME,
        #     x_label=MJ1_X_LABEL,
        #     figure_name="MJ1 cooling spectroscopy",
        #     x_scale=MJ1_X_SCALE,
        # )

    
        survival_figure = plot_mj1_multiple_curves(
            df=df,
            analyser=analyser,
            dataset_label=dataset_label,
            x_scale=MJ1_X_SCALE,
            duration_scale=1.0,
        )

        plot_suffix = "MJ1_cooling_spectroscopy"

        if PLOT_SURVIVAL_PER_TWEEZER:

            individual_figure = plot_survival_per_tweezer(
                df=df,
                analyser=analyser,
                dataset_label=dataset_label,
                mode_flag="MJ1_Spectroscopy",
                scan_name=MJ1_SCAN_NAME,
                x_label=MJ1_X_LABEL,
                figure_name="MJ1 survival per tweezer",
                x_scale=MJ1_X_SCALE,
            )

            individual_suffix = "MJ1_survival_per_tweezer"
    # ---------------------------------------------------------
    # Release-and-recapture: Image 2 -> Image 3
    # ---------------------------------------------------------

    elif rr_enabled:

        survival_figure = plot_survival_scan(
            df=df,
            analyser=analyser,
            dataset_label=dataset_label,
            mode_flag="release_recapture",
            scan_name="release_time",
            x_label="Release time (µs)",
            figure_name="Release and recapture",
            x_scale=1e6,
        )

        plot_suffix = "release_recapture"
        if PLOT_SURVIVAL_PER_TWEEZER:

            individual_figure = plot_survival_per_tweezer(
                df=df,
                analyser=analyser,
                dataset_label=dataset_label,
                mode_flag="release_recapture",
                scan_name="release_time",
                x_label="Release time (µs)",
                figure_name="Release and recapture per tweezer",
                x_scale=1e6,
            )

            individual_suffix = "release_recapture_per_tweezer"

    # ---------------------------------------------------------
    # Save and display the selected survival plot
    # ---------------------------------------------------------

    # =========================================================
    # SAVE AND DISPLAY SURVIVAL FIGURES
    # =========================================================

    if plot_suffix is not None:

        figures_to_save = []

        if survival_figure is not None:
            figures_to_save.append(
                (plot_suffix, survival_figure)
            )

        if individual_figure is not None:
            figures_to_save.append(
                (individual_suffix, individual_figure)
            )

        if SAVE_PLOTS:

            for suffix, fig in figures_to_save:

                output_path = output_dir / (
                    f"{dataset_label.replace(' ', '_')}_{suffix}.png"
                )

                fig.savefig(
                    output_path,
                    dpi=200,
                    bbox_inches="tight",
                )

                print(f"Saved survival plot: {output_path}")

        if figures_to_save:
            plt.show()

        return
    validate_scan_configuration(df)

    paths = df["filepath"]
    analyser = df["FluoAnalyser_tweez"]
    dataset_label = make_dataset_label(paths)

    scan_values = [
        scalar_per_shot(df[name], name)
        for name in SCAN_NAMES
    ]

    first_shot = load_roi_integrals(analyser, suffix="")
    second_shot = load_roi_integrals(analyser, suffix="_2nd")
    third_shot = load_roi_integrals(analyser, suffix="_3rd")

    first_results = aggregate_nd_scan(
        scan_values=scan_values,
        roi_integrals=first_shot,
        shot_name="first",
    )

    second_results = aggregate_nd_scan(
        scan_values=scan_values,
        roi_integrals=second_shot,
        shot_name="second",
    )

    third_results = aggregate_nd_scan(
        scan_values=scan_values,
        roi_integrals=third_shot,
        shot_name="third",
    )
    

    results = pd.concat(
        [first_results, second_results, third_results,],
        ignore_index=True,
    )


    # Print every scanned value available for every parameter:
    parameter_values = {
        parameter_name: np.sort(results[parameter_name].unique())
        for parameter_name in SCAN_NAMES
    }

    print("\nAVAILABLE SCAN VALUES:")
    for parameter_name, values in parameter_values.items():
        print(f"{parameter_name}: {values}")




    date = Path(paths.iloc[0]).name[:10]

    # Numeri degli shot effettivamente analizzati
    shot_numbers = (
        paths.str.extract(r"_(\d{4})_")[0]
        .dropna()
        .astype(int)
        .unique()
    )

    shot_numbers = sorted(shot_numbers)

    if len(shot_numbers) == 1:
        shot_label = f"shot_{shot_numbers[0]:04d}"
    else:
        shot_label = "shots_" + "_".join(
            f"{number:04d}" for number in shot_numbers
        )

    output_dir = output_directory(paths)

    stem = f"{date}_{shot_label}_{'_'.join(SCAN_NAMES[index] for index in PLOT_AXES)}_ND_tweezer_ROI"

    if SAVE_CSV:
        csv_path = output_dir / f"{stem}.csv"
        results.to_csv(csv_path, index=False)
        print(f"Saved complete N-D data: {csv_path}")
    
    figures = plot_nd(results, dataset_label)
 
    if PLOT_INDIVIDUAL_TWEEZERS:
        figures += plot_individual_tweezers(results, dataset_label)

    if PLOT_ALL_TWEEZERS:
        figures += plot_all_tweezers_three_shots(
        results,
        dataset_label,
    )

    if SAVE_PLOTS:
        for suffix, figure in figures:
            image_path = output_dir / f"{stem}_{suffix}.png"
            figure.savefig(image_path, dpi=200)
            print(f"Saved plot: {image_path}")

    plt.show()




    top_five_first = (
        results[results["shot"] == "first"]
        .sort_values("mean_roi_integral", ascending=False)
        .head(5)
    )

    top_five_second = (
        results[results["shot"] == "second"]
        .sort_values("mean_roi_integral", ascending=False)
        .head(5)
    )

    # print("\nTOP 5 - FIRST IMAGE")
    # print(top_five_first.to_string(index=False))

    # print("\nTOP 5 - SECOND IMAGE")
    # print(top_five_second.to_string(index=False))

    top_five = pd.concat(
        [top_five_first, top_five_second],
        ignore_index=True,
    )

    top_five.to_csv(
        output_dir / f"{stem}_top_5_first_and_second.csv",
        index=False,
    )






    
    available_values_csv = pd.DataFrame(
        [
            {
                "parameter": parameter_name,
                "available_value": value,
            }
            for parameter_name, values in parameter_values.items()
            for value in values
        ]
    )

    available_values_path = (
        output_dir / f"{stem}_available_parameter_values.csv"
    )

    available_values_csv.to_csv(
        available_values_path,
        index=False,
    )

    print(f"\nSaved available parameter values: {available_values_path}")






if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"N-D analysis failed: {error}")