
import h5py
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ============================================================
# SETTINGS
# ============================================================

DATA_DIR = Path(
    r"D:\Experiments\Sr\Selection_experiment\2026\10\20\0005"
)

TARGET_INDICES = np.array([
    7, 8, 9, 10,
    13, 14, 15, 16,
    19, 20, 21, 22,
    25, 26, 27, 28
], dtype=int)

RESULT_GROUP = "results/FluoAnalyser_tweez"

MIN_INITIAL_ATOMS = 16
SAVE_PLOTS = True

# ============================================================
# LOAD SHOTS
# ============================================================

files = sorted(DATA_DIR.glob("*.h5"))

total_files = len(files)
analyzed_shots = 0
invalid_shots = 0
missing_shots = 0

shot_numbers = []
n_initial = []
n_second = []
n_third = []

second_sites = []
third_sites = []

for file in files:

    try:
        with h5py.File(file, "r") as f:

            if RESULT_GROUP not in f:
                missing_shots += 1
                continue

            r = f[RESULT_GROUP]
            attrs = r.attrs

            # Verify that all required results exist
            required = [
                "n_atoms_first",
                "rearrangement_valid"
            ]

            required += [
                f"tw{i+1}_occupied_2nd"
                for i in TARGET_INDICES
            ]

            required += [
                f"tw{i+1}_occupied_3rd"
                for i in TARGET_INDICES
            ]

            if any(key not in attrs for key in required):
                missing_shots += 1
                continue

            analyzed_shots += 1

            initial_atoms = int(attrs["n_atoms_first"])

            # Only include shots where rearrangement
            # was possible
            if (
                initial_atoms < MIN_INITIAL_ATOMS
                or int(attrs["rearrangement_valid"]) != 1
            ):
                invalid_shots += 1
                continue

            # Load 16 target ROI occupancies
            second = np.array([
                int(attrs[f"tw{i+1}_occupied_2nd"])
                for i in TARGET_INDICES
            ], dtype=np.uint8)

            third = np.array([
                int(attrs[f"tw{i+1}_occupied_3rd"])
                for i in TARGET_INDICES
            ], dtype=np.uint8)

            # Validate binary occupancy
            if not (
                np.all(second <= 1)
                and np.all(third <= 1)
            ):
                missing_shots += 1
                analyzed_shots -= 1
                continue

            # Extract actual shot number
            try:
                shot_number = int(file.stem.split("_")[-1])
            except ValueError:
                shot_number = len(shot_numbers)

            shot_numbers.append(shot_number)
            n_initial.append(initial_atoms)
            n_second.append(int(second.sum()))
            n_third.append(int(third.sum()))

            second_sites.append(second)
            third_sites.append(third)

    except (OSError, KeyError, ValueError) as error:
        missing_shots += 1
        continue

# ============================================================
# CHECK DATA
# ============================================================

print("\n===== REARRANGEMENT SHOT SUMMARY =====")
print(f"Files found: {total_files}")
print(f"Analyzed shots: {analyzed_shots}")
print(f"Invalid (<16 initial atoms): {invalid_shots}")
print(f"Missing/incomplete shots: {missing_shots}")

if len(n_second) == 0:
    print("No valid rearrangement shots available yet.")

else:

    shot_numbers = np.asarray(shot_numbers)
    n_initial = np.asarray(n_initial)
    n_second = np.asarray(n_second)
    n_third = np.asarray(n_third)

    second_sites = np.asarray(second_sites)
    third_sites = np.asarray(third_sites)

    # Sort by actual shot number
    order = np.argsort(shot_numbers)

    shot_numbers = shot_numbers[order]
    n_initial = n_initial[order]
    n_second = n_second[order]
    n_third = n_third[order]

    second_sites = second_sites[order]
    third_sites = third_sites[order]

    # ========================================================
    # STATISTICS
    # ========================================================

    n_valid = len(n_second)

    filling = n_second / 16.0
    defect_free = n_second == 16

    # Site-resolved survival Image 2 -> Image 3
    survived_sites = (
        (second_sites == 1)
        & (third_sites == 1)
    )

    total_occupied_image2 = int(second_sites.sum())
    total_survived = int(survived_sites.sum())

    retention = (
        total_survived / total_occupied_image2
        if total_occupied_image2 > 0
        else np.nan
    )

    # Fraction of valid shots with all 16 atoms
    defect_free_probability = np.mean(defect_free)

    # Probability of each site being occupied
    site_filling = np.mean(
        second_sites,
        axis=0
    ).reshape(4, 4)

    # Probability of survival for each occupied site
    site_initial = second_sites.sum(axis=0)
    site_survived = survived_sites.sum(axis=0)

    site_survival = np.divide(
        site_survived,
        site_initial,
        out=np.full(16, np.nan),
        where=site_initial > 0
    ).reshape(4, 4)

    print("\n===== REARRANGEMENT RESULTS =====")
    print(f"Valid shots: {n_valid}")

    print(
        f"Mean initial atoms: "
        f"{np.mean(n_initial):.2f}/36"
    )

    print(
        f"Mean final atoms: "
        f"{np.mean(n_second):.2f}/16"
    )

    print(
        f"Mean 4x4 filling: "
        f"{100*np.mean(filling):.2f}%"
    )

    print(
        f"Defect-free shots: "
        f"{np.sum(defect_free)}/{n_valid}"
    )

    print(
        f"Defect-free probability: "
        f"{100*defect_free_probability:.2f}%"
    )

    print(
        f"Image 2 -> 3 survival: "
        f"{total_survived}/{total_occupied_image2} "
        f"= {100*retention:.2f}%"
    )

    # ========================================================
    # PLOT 1: ATOM NUMBER DISTRIBUTION
    # ========================================================

    fig1, ax1 = plt.subplots(figsize=(8, 5))

    ax1.hist(
        n_second,
        bins=np.arange(-0.5, 17.5, 1),
        edgecolor="black"
    )

    ax1.set_xlabel("Number of atoms in final 4x4")
    ax1.set_ylabel("Number of shots")
    ax1.set_title(
        f"Rearrangement atom distribution "
        f"(N={n_valid})"
    )

    ax1.set_xticks(range(17))
    ax1.grid(alpha=0.3)

    fig1.tight_layout()

    # ========================================================
    # PLOT 2: CUMULATIVE DEFECT-FREE PROBABILITY
    # ========================================================

    cumulative = (
        np.cumsum(defect_free)
        / np.arange(1, n_valid + 1)
    )

    fig2, ax2 = plt.subplots(figsize=(8, 5))

    ax2.plot(
        shot_numbers,
        cumulative * 100,
        linewidth=2
    )

    ax2.axhline(
        100 * defect_free_probability,
        linestyle="--",
        color="red",
        label=(
            f"Final: "
            f"{100*defect_free_probability:.2f}%"
        )
    )

    ax2.set_xlabel("Shot number")
    ax2.set_ylabel("Cumulative defect-free probability (%)")
    ax2.set_title("4x4 defect-free rearrangement probability")
    ax2.set_ylim(0, 105)
    ax2.legend()
    ax2.grid(alpha=0.3)

    fig2.tight_layout()

    # ========================================================
    # PLOT 3: FILLING VERSUS SHOT NUMBER
    # ========================================================

    fig3, ax3 = plt.subplots(figsize=(10, 5))

    ax3.plot(
        shot_numbers,
        filling * 100,
        ".-",
        markersize=4,
        linewidth=0.8
    )

    ax3.axhline(
        100 * np.mean(filling),
        color="red",
        linestyle="--",
        label=(
            f"Mean filling: "
            f"{100*np.mean(filling):.2f}%"
        )
    )

    ax3.set_xlabel("Shot number")
    ax3.set_ylabel("4x4 filling (%)")
    ax3.set_title("Rearrangement filling versus shot")
    ax3.set_ylim(0, 105)
    ax3.legend()
    ax3.grid(alpha=0.3)

    fig3.tight_layout()

    # ========================================================
    # PLOT 4: SITE-RESOLVED FILLING
    # ========================================================

    fig4, axes = plt.subplots(
        1, 2,
        figsize=(12, 5)
    )

    im1 = axes[0].imshow(
        site_filling,
        vmin=0,
        vmax=1,
        cmap="viridis"
    )

    axes[0].set_title("Image 2: 4x4 filling")

    im2 = axes[1].imshow(
        site_survival,
        vmin=0,
        vmax=1,
        cmap="viridis"
    )

    axes[1].set_title("Image 2 -> 3 site survival")

    for ax, values in zip(
        axes,
        [site_filling, site_survival]
    ):

        for row in range(4):
            for col in range(4):

                value = values[row, col]

                label = (
                    f"{100*value:.1f}%"
                    if np.isfinite(value)
                    else "N/A"
                )

                ax.text(
                    col,
                    row,
                    label,
                    ha="center",
                    va="center",
                    color=(
                        "white"
                        if not np.isfinite(value) or value < 0.5
                        else "black"
                    )
                )

        ax.set_xticks(range(4))
        ax.set_yticks(range(4))
        ax.set_xlabel("Column")
        ax.set_ylabel("Row")

    fig4.colorbar(
        im1,
        ax=axes[0],
        label="Probability"
    )

    fig4.colorbar(
        im2,
        ax=axes[1],
        label="Probability"
    )

    # ========================================================
    # SAVE PLOTS
    # ========================================================

    if SAVE_PLOTS:

        output_files = [
            (
                fig1,
                "rearrangement_atom_distribution.png"
            ),
            (
                fig2,
                "rearrangement_defect_free.png"
            ),
            (
                fig3,
                "rearrangement_filling_vs_shot.png"
            ),
            (
                fig4,
                "rearrangement_site_filling_survival.png"
            )
        ]

        for fig, filename in output_files:

            output_path = DATA_DIR / filename

            fig.savefig(
                output_path,
                dpi=200,
                bbox_inches="tight"
            )

            print(f"Saved: {output_path}")

    plt.show()
