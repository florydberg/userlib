"""Interactive browser for CSV files created by the Lyse N-D ROI analysis."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Qt5Agg")  # Must be before importing pyplot.

import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons
import numpy as np
import pandas as pd
import seaborn as sns


RESULT_COLUMNS = {
    "shot",
    "mean_roi_integral",
    "sem_roi_integral",
    "n_tweezers",
    "n_repetitions",
}


class HeatmapBrowser:
    def __init__(self, csv_path: Path):
        self.csv_path = csv_path
        self.results = pd.read_csv(csv_path)

        missing = {"shot", "mean_roi_integral"} - set(self.results.columns)
        if missing:
            raise ValueError(
                "Not an N-D ROI CSV; missing: " + ", ".join(missing)
            )

        self.parameters = [
            column
            for column in self.results.columns
            if column not in RESULT_COLUMNS
        ]

        if len(self.parameters) < 2:
            raise ValueError(
                "The CSV needs at least two scan parameters for a heatmap."
            )

        self.x_parameter = self.parameters[0]
        self.y_parameter = self.parameters[1]

        self.fixed = {
            name: self.values(name)[len(self.values(name)) // 2]
            for name in self.parameters[2:]
        }

        # Keeps references to buttons so Matplotlib does not delete them.
        self.radio_buttons = []

        # Holds the two currently displayed colorbar axes.
        self.colorbar_axes = []

        self.make_window()

    def values(self, parameter_name):
        """All scanned values of one parameter."""
        return np.sort(
            self.results[parameter_name]
            .dropna()
            .unique()
        )

    def make_window(self):
        n_fixed = max(1, len(self.parameters) - 2)

        self.fig, self.axes = plt.subplots(
            2,
            1,
            figsize=(17, max(8, 2.5 * n_fixed + 3)),
        )

        self.fig.subplots_adjust(
            left=0.06,
            right=0.57,
            top=0.93,
            bottom=0.08,
            hspace=0.42,
        )

        # Save the full original area for each heatmap.
        # We restore this before every redraw, preventing progressive shrinking.
        self.original_heatmap_positions = [
            axis.get_position().frozen()
            for axis in self.axes
        ]

        self.fig.canvas.manager.set_window_title(
            f"N-D heatmap browser — {self.csv_path.name}"
        )

        # ---------------------------------------------------------------------
        # X-axis selector
        # ---------------------------------------------------------------------
        x_axis_selector = self.fig.add_axes(
            [0.63, 0.82, 0.14, 0.13]
        )

        x_axis_selector.set_title(
            "X axis",
            loc="left",
            fontsize=10,
            fontweight="bold",
        )

        self.x_radio = RadioButtons(
            x_axis_selector,
            self.parameters,
            active=0,
        )

        self.x_radio.on_clicked(
            lambda label: self.change_axis("x", label)
        )

        # ---------------------------------------------------------------------
        # Y-axis selector
        # ---------------------------------------------------------------------
        y_axis_selector = self.fig.add_axes(
            [0.82, 0.82, 0.14, 0.13]
        )

        y_axis_selector.set_title(
            "Y axis",
            loc="left",
            fontsize=10,
            fontweight="bold",
        )

        self.y_radio = RadioButtons(
            y_axis_selector,
            self.parameters,
            active=1,
        )

        self.y_radio.on_clicked(
            lambda label: self.change_axis("y", label)
        )

        self.build_fixed_controls()
        self.redraw()

    def change_axis(self, axis, parameter_name):
        """Change x or y heatmap axis."""
        other_axis_parameter = (
            self.y_parameter
            if axis == "x"
            else self.x_parameter
        )

        if parameter_name == other_axis_parameter:
            print("X and Y axes must be different.")
            return

        if axis == "x":
            self.x_parameter = parameter_name
        else:
            self.y_parameter = parameter_name

        self.build_fixed_controls()
        self.redraw()

    def build_fixed_controls(self):
        """
        Rebuild clickable selectors for all parameters which are not
        currently chosen as heatmap axes.
        """
        for radio in self.radio_buttons:
            radio.ax.remove()

        self.radio_buttons = []

        fixed_parameter_names = [
            parameter_name
            for parameter_name in self.parameters
            if parameter_name not in (
                self.x_parameter,
                self.y_parameter,
            )
        ]

        # Preserve a selection if possible. Otherwise select middle scan value.
        self.fixed = {
            parameter_name: self.fixed.get(
                parameter_name,
                self.values(parameter_name)[
                    len(self.values(parameter_name)) // 2
                ],
            )
            for parameter_name in fixed_parameter_names
        }

        if not fixed_parameter_names:
            return

        control_height = min(
            0.14,
            0.62 / len(fixed_parameter_names),
        )

        for index, parameter_name in enumerate(fixed_parameter_names):
            y_position = (
                0.74
                - index * (0.66 / len(fixed_parameter_names))
            )

            control_axis = self.fig.add_axes(
                [0.63, y_position, 0.33, control_height]
            )

            parameter_values = self.values(parameter_name)

            labels = [
                f"{value:g}"
                for value in parameter_values
            ]

            selected_index = int(
                np.argmin(
                    np.abs(
                        parameter_values
                        - self.fixed[parameter_name]
                    )
                )
            )

            control_axis.set_title(
                parameter_name,
                loc="left",
                fontsize=10,
                fontweight="bold",
            )

            radio = RadioButtons(
                control_axis,
                labels,
                active=selected_index,
            )

            radio.on_clicked(
                lambda label, name=parameter_name:
                self.change_fixed(name, float(label))
            )

            self.radio_buttons.append(radio)

    def change_fixed(self, parameter_name, value):
        """Update one fixed parameter and redraw both heatmaps."""
        self.fixed[parameter_name] = value
        self.redraw()

    def slice_data(self, shot):
        """
        Select one N-D slice and reshape it into a 2D heatmap table.
        """
        data = self.results[
            self.results["shot"] == shot
        ].copy()

        for parameter_name, value in self.fixed.items():
            data = data[
                np.isclose(
                    data[parameter_name],
                    value,
                )
            ]

        return (
            data.pivot_table(
                index=self.y_parameter,
                columns=self.x_parameter,
                values="mean_roi_integral",
                aggfunc="mean",
            )
            .sort_index()
            .sort_index(axis=1)
        )

    def redraw(self):
        """
        Redraw both images without accumulating colorbars or shrinking plots.
        """
        # Remove colorbars from the preceding redraw:
        for colorbar_axis in self.colorbar_axes:
            colorbar_axis.remove()

        self.colorbar_axes = []

        for axis, original_position, shot in zip(
            self.axes,
            self.original_heatmap_positions,
            ("first", "second"),
        ):
            axis.clear()

            # Seaborn shrinks the axis when adding a colorbar.
            # Restore the original full heatmap area before each new redraw.
            axis.set_position(original_position)

            grid = self.slice_data(shot)

            sns.heatmap(
                grid,
                annot=True,
                fmt=".2f",
                cmap="viridis",
                linewidths=0.5,
                ax=axis,
            )

            # Store its colorbar axis so it can be removed next redraw.
            self.colorbar_axes.append(
                axis.collections[0].colorbar.ax
            )

            fixed_text = ", ".join(
                f"{parameter_name}={value:g}"
                for parameter_name, value in self.fixed.items()
            )

            title = f"{shot.capitalize()} image"
            if fixed_text:
                title += f" — {fixed_text}"

            axis.set_title(title)
            axis.set_xlabel(self.x_parameter)
            axis.set_ylabel(self.y_parameter)

        self.fig.canvas.draw_idle()

    def show(self):
        """Keep the Qt window open and interactive."""
        plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Browse a Lyse N-D ROI CSV interactively."
    )

    parser.add_argument(
        "csv",
        type=Path,
        help="Path to the *_ND_tweezer_ROI.csv file",
    )

    args = parser.parse_args()

    if not args.csv.is_file():
        parser.error(f"CSV not found: {args.csv}")

    HeatmapBrowser(args.csv).show()


if __name__ == "__main__":
    main()