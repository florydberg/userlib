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
SAVE_PLOTS = True
SAVE_CSV = True
One_D = False

if One_D:
    PLOT_AXES = (0,)      # 1D: plot FluoImgPulse_Dt
else:
    PLOT_AXES = (0, 1)    # 2D: plot FluoImgPulse_Dt × LAC_duration


    
SCAN_NAMES = [
    "FluoImgPulse_Dt",
    "LAC_duration",
    "LAC_Frq",
    "LAC_Pow",
    "SisyphusImg_Frq",
]

SCAN_UNITS = [
    "ms",
    "s",
     "MHz",
     "",
     "MHz",
]

# For more than two scan parameters:
# Which two parameters should be displayed as the heatmap axes?
# Indices refer to SCAN_NAMES.
FIXED_VALUES = {
    "LAC_Frq": -1.2,
    "LAC_Pow": 17,
    "SisyphusImg_Frq": -2.9,
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

        for name, value in zip(SCAN_NAMES, coordinate):
            row[name] = value

        rows.append(row)

    return pd.DataFrame(rows)


def choose_fixed_value(
    results: pd.DataFrame,
    parameter_name: str,
) -> float:
    """Use a user-selected fixed value or the middle measured scan value."""
    if parameter_name in FIXED_VALUES:
        requested = FIXED_VALUES[parameter_name]
        available = np.sort(results[parameter_name].unique())

        return available[np.argmin(np.abs(available - requested))]

    available = np.sort(results[parameter_name].unique())
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

    ax.set_title(f"Tweezer ROI integral — {dataset_label}")
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

    fig, ax = plt.subplots(figsize=(10, 7), constrained_layout=True)

    sns.heatmap(
        heatmap.sort_index().sort_index(axis=1),
        cmap="viridis",
        annot=True,
        fmt=".1f",
        linewidths=0.4,
        ax=ax,
    )

    x_unit = SCAN_UNITS[SCAN_NAMES.index(x_parameter)]
    y_unit = SCAN_UNITS[SCAN_NAMES.index(y_parameter)]

    slice_text = ", ".join(
        f"{name}={value:g}"
        for name, value in fixed_dimensions.items()
    )

    title = f"Tweezer ROI integral — {shot_name} shot ({dataset_label})"
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

        title = f"Tweezer ROI integral — {dataset_label}"
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

    for shot_name in ("first", "second"):
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


def main():
    df = lyse.data()

    if df.empty:
        raise RuntimeError("Lyse has no loaded shots to analyse.")

    if "filepath" not in df.columns:
        raise KeyError("Lyse data does not contain the 'filepath' column.")

    if "FluoAnalyser_tweez" not in df.columns:
        raise KeyError(
            "No 'FluoAnalyser_tweez' results group was found in Lyse data."
        )

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

    results = pd.concat(
        [first_results, second_results],
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




    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_dir = output_directory(paths)
    stem = f"{timestamp}_{'_'.join(SCAN_NAMES)}_ND_tweezer_ROI"

    if SAVE_CSV:
        csv_path = output_dir / f"{stem}.csv"
        results.to_csv(csv_path, index=False)
        print(f"Saved complete N-D data: {csv_path}")
    
    figures = plot_nd(results, dataset_label)

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

    print("\nTOP 5 — FIRST IMAGE")
    print(top_five_first.to_string(index=False))

    print("\nTOP 5 — SECOND IMAGE")
    print(top_five_second.to_string(index=False))

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