import os
import time
import datetime
import copy

import h5py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle

import analysislib
from lyse import Run, data, path


# ============================================================
# SETTINGS
# ============================================================

NROWS = 6
NCOLS = 6

X0 = 105
Y0 = 68
DX = 18
DY = 18

# Preserves the original slice: centre-Tray+1 : centre+Tray.
# Tray=3 therefore gives a 5 x 5 integration region.
TRAY = 3

EFFECTIVE_PIXEL_SIZE_UM = 1.127

PLOT_FULL_IMAGES = True
PLOT_MOSAICS = True
PLOT_RAW_IMAGE = False
PLOT_BACKGROUND_MASK = False
SAVE_PLOT = False
SAVE_SCRIPT = True

# One common intensity scale for every panel.
VMIN = 0
VMAX = 50

MOSAIC_GAP = 2

# False preserves your original background masks.
# True uses the first-shot background region for both images.
USE_SAME_BACKGROUND_MASK = False

BACKGROUND_CENTER = (130, 120)
BACKGROUND_RADIUS = 55

FIGURE_NAME = "Tweezer_analysis"


# ============================================================
# FUNCTIONS
# ============================================================

def load_image(shot, image_name, n_loop):
    """Read the image, averaging repeated frames when configured."""
    raw = shot.get_image("Orca_Camera", image_name, "frame")

    if n_loop > 1:
        if raw.ndim != 3:
            raise ValueError(
                f"{image_name}: expected a frame stack for "
                f"n_loop={n_loop}, received shape {raw.shape}."
            )

        # Avoid a separate float32 copy of the entire stack.
        image = np.mean(raw, axis=0, dtype=np.float32)

    else:
        image = raw.astype(np.float32, copy=False)

        # Accept a single frame with a leading singleton dimension.
        if image.ndim == 3 and image.shape[0] == 1:
            image = image[0]

    if image.ndim != 2:
        raise ValueError(
            f"{image_name}: expected a 2D image, got {image.shape}."
        )

    return image


def background_mask(shape, exclusion_centers, radius):
    """True pixels contribute to the background estimate."""
    height, width = shape
    mask = np.ones(shape, dtype=bool)

    for cx, cy in exclusion_centers:
        xmin = max(cx - radius, 0)
        xmax = min(cx + radius + 1, width)
        ymin = max(cy - radius, 0)
        ymax = min(cy + radius + 1, height)

        mask[ymin:ymax, xmin:xmax] = False

    if not mask.any():
        raise ValueError(
            "The background mask excludes the entire image. "
            "Reduce BACKGROUND_RADIUS or change the exclusion centres."
        )

    return mask


def extract_rois(image, centers):
    """Extract and validate all integration regions."""
    height, width = image.shape
    spots = []

    for index, (cx, cy) in enumerate(centers, start=1):
        xmin = cx - TRAY + 1
        xmax = cx + TRAY
        ymin = cy - TRAY + 1
        ymax = cy + TRAY

        if (
            xmin < 0 or ymin < 0
            or xmax > width or ymax > height
        ):
            raise ValueError(
                f"ROI {index}, centre ({cx}, {cy}), lies outside "
                f"the image of shape {image.shape}. "
                "Check the centre coordinates and camera ROI."
            )

        spots.append(image[ymin:ymax, xmin:xmax])

    return np.stack(spots)


def make_roi_mosaic(rois):
    """Combine all ROIs into one small image."""
    count, height, width = rois.shape

    if count != NROWS * NCOLS:
        raise ValueError(
            f"Expected {NROWS * NCOLS} ROIs, got {count}."
        )

    mosaic = np.full(
        (
            NROWS * height + (NROWS - 1) * MOSAIC_GAP,
            NCOLS * width + (NCOLS - 1) * MOSAIC_GAP,
        ),
        np.nan,
        dtype=np.float32,
    )

    for index, roi in enumerate(rois):
        row, column = divmod(index, NCOLS)
        y = row * (height + MOSAIC_GAP)
        x = column * (width + MOSAIC_GAP)
        mosaic[y:y + height, x:x + width] = roi

    return mosaic


def save_script_copy(shot_path):
    """Archive this script once, using a single writable file handle."""
    file_path = os.path.realpath(__file__)
    prefix = os.path.dirname(os.path.realpath(analysislib.__file__))
    relative_path = os.path.relpath(file_path, prefix)

    # Avoid creating paths outside the analysislib archive group.
    if relative_path == ".." or relative_path.startswith(".." + os.sep):
        relative_path = os.path.basename(file_path)

    archive_path = "analysislib/" + relative_path.replace("\\", "/")

    with h5py.File(shot_path, "r+") as handle:
        if archive_path in handle:
            return

        with open(file_path, "r", encoding="utf-8-sig") as source:
            script_text = source.read()

        parent, name = archive_path.rsplit("/", 1)
        group = handle.require_group(parent)
        group.create_dataset(
            name,
            data=script_text,
            dtype=h5py.string_dtype(encoding="utf-8"),
        )


def plot_diagnostic_images(image, background_mask_array, centers, background_value):
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # -------------------------------------------------
    # 1. Raw image
    # -------------------------------------------------
    axes[0].imshow(image, cmap="plasma", interpolation="nearest")
    axes[0].set_title("Raw image")
    axes[0].set_xlabel("x-axis (pixel)")
    axes[0].set_ylabel("y-axis (pixel)")

    # -------------------------------------------------
    # 2. Background region
    # -------------------------------------------------
    axes[1].imshow(image, cmap="plasma", interpolation="nearest")

    # Coordinates of excluded region
    cx, cy = BACKGROUND_CENTER
    r = BACKGROUND_RADIUS

    xmin = cx - r
    xmax = cx + r
    ymin = cy - r
    ymax = cy + r

    # Shade ONLY the excluded region
    axes[1].fill(
        [xmin, xmax, xmax, xmin],
        [ymin, ymin, ymax, ymax],
        color="red",
        alpha=0.35,
    )

    # Border around excluded region
    axes[1].plot(
        [xmin, xmax, xmax, xmin, xmin],
        [ymin, ymin, ymax, ymax, ymin],
        "r-",
        linewidth=2,
    )

    fig.colorbar(
        axes[0].images[0],
        ax=axes,
        label="Camera counts",
    )

    # Background center
    axes[1].plot(
        cx, cy,
        "wo",
        markersize=5,
    )

    axes[1].set_title(
        "Background calculation\n"
        "NORMAL = USED     RED = EXCLUDED"
    )
    axes[1].set_xlabel("x-axis (pixel)")
    axes[1].set_ylabel("y-axis (pixel)")

    fig.suptitle(
        f"Calculated background = {background_value:.3f} counts"
    )

    # fig.tight_layout()

    return fig

def plot_results(images, roi_sets, labels, centers):
    """One figure: shots in columns, views in rows, shared colour bar."""
    view_count = int(PLOT_FULL_IMAGES) + int(PLOT_MOSAICS)

    if view_count == 0:
        return None

    shot_count = len(images)
    plt.rcParams.update({
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
    })
    fig = plt.figure(
        FIGURE_NAME,
        figsize=(8 * shot_count + 1, 4.5 * view_count),
    )
    fig.clear()

    # Reserve a dedicated column for the shared colour bar.
    grid = fig.add_gridspec(
        view_count,
        shot_count + 1,
        width_ratios=[1] * shot_count + [0.045],
        left=0.08,
        right=0.94,
        bottom=0.09,
        top=0.93,
        wspace=0.28,
        hspace=0.32,
    )

    cmap = copy.copy(plt.cm.plasma)
    cmap.set_bad("white")
    norm = Normalize(vmin=VMIN, vmax=VMAX)

    mappable = None

    for column, (image, rois, label) in enumerate(
        zip(images, roi_sets, labels)
    ):
        row = 0

        if PLOT_FULL_IMAGES:
            ax = fig.add_subplot(grid[row, column])

            mappable = ax.imshow(
                image,
                cmap=cmap,
                norm=norm,
                interpolation="nearest",
            )

            # Match the actual 5 x 5 pixel integration regions.
            rectangles = [
                Rectangle(
                    (
                        cx - TRAY + 0.5,
                        cy - TRAY + 0.5,
                    ),
                    2 * TRAY - 1,
                    2 * TRAY - 1,
                )
                for cx, cy in centers
            ]

            ax.add_collection(
                PatchCollection(
                    rectangles,
                    facecolors="none",
                    edgecolors="red",
                    linewidths=0.8,
                )
            )

            height, width = image.shape
            xticks = np.linspace(0, width - 1, 5)
            yticks = np.linspace(0, height - 1, 5)

            ax.set_xticks(xticks)
            ax.set_xticklabels(
                [f"{x * EFFECTIVE_PIXEL_SIZE_UM:.1f}" for x in xticks]
            )

            ax.set_yticks(yticks)
            ax.set_yticklabels(
                [f"{y * EFFECTIVE_PIXEL_SIZE_UM:.1f}" for y in yticks]
            )

            ax.set_xlabel(r"y-axis ($\mu$m)")
            ax.set_ylabel(r"z-axis($\mu$m)")
            ax.set_title(f"Image - {label}")
            row += 1

        if PLOT_MOSAICS:
            ax = fig.add_subplot(grid[row, column])

            mappable = ax.imshow(
                make_roi_mosaic(rois),
                cmap=cmap,
                norm=norm,
                interpolation="nearest",
            )

            ax.set_title(f"Tweezer ROIs - {label}")
            ax.set_xticks([])
            ax.set_yticks([])

    colorbar_ax = fig.add_subplot(grid[:, -1])
    fig.colorbar(
        mappable,
        cax=colorbar_ax,
        label="Background-subtracted camera counts",
    )

    return fig


# ============================================================
# ANALYSIS
# ============================================================

start = time.perf_counter()

centers = np.array(
    [
        (X0 + column * DX, Y0 + row * DY)
        for row in range(NROWS)
        for column in range(NCOLS)
    ],
    dtype=int,
)

# Read shot metadata once.
metadata = data(path)
n_loop = int(metadata["n_loop"])
second_shot = bool(metadata["second_shot"])
camera_roi = str(metadata["Orca_ROI"])

images = []
roi_sets = []
labels = []

with Run(path).open("r+") as shot:
    first_image = load_image(shot, "TweezFluo", n_loop)

    first_mask = background_mask(
        first_image.shape,
        [BACKGROUND_CENTER],
        BACKGROUND_RADIUS,
    )

    first_background_pixels = first_image[first_mask]
    first_background = np.mean(first_background_pixels)

    if PLOT_RAW_IMAGE or PLOT_BACKGROUND_MASK:
            diagnostic_figure = plot_diagnostic_images(
        first_image,
        first_mask,
        centers,
        first_background,
    )

    # Preserve the original result definition for compatibility.
    # This value is approximately zero by construction.
    shot.save_result(
        "background_integral",
        np.mean(first_background_pixels - first_background),
    )

    # Save the actual background level separately.
    shot.save_result("background_mean", first_background)

    # Preserve the original first-image full-frame crop.
    if camera_roi == "full":
        mot_x, mot_y = 23600, 841
        mot_radius = 50

        if (
            mot_x - mot_radius < 0
            or mot_y - mot_radius < 0
            or mot_x + mot_radius > first_image.shape[1]
            or mot_y + mot_radius > first_image.shape[0]
        ):
            raise ValueError("The configured full-frame MOT crop is invalid.")

        first_corrected = (
            first_image[
                mot_y - mot_radius:mot_y + mot_radius,
                mot_x - mot_radius:mot_x + mot_radius,
            ]
            - first_background
        )

        # Centers must be expressed relative to this cropped image.
        # The supplied centers do not fit a 100 x 100 crop, so
        # extract_rois() will report that instead of saving empty sums.

    elif camera_roi in ("mot", "tweez"):
        first_corrected = first_image - first_background

    else:
        raise ValueError(f"Unknown Orca_ROI setting: {camera_roi!r}")

    first_rois = extract_rois(first_corrected, centers)
    first_integrals = first_rois.sum(axis=(1, 2))

    for index, integral in enumerate(first_integrals, start=1):
        shot.save_result(f"tw{index}_integral", integral)

    images.append(first_corrected)
    roi_sets.append(first_rois)
    labels.append("first shot")

    if second_shot:
        second_image = load_image(shot, "second-shot", n_loop)

        if camera_roi == "full":
            raise ValueError(
                "Second-shot analysis with Orca_ROI='full' needs "
                "explicit crop-relative tweezer coordinates."
            )

        if USE_SAME_BACKGROUND_MASK:
            if second_image.shape == first_image.shape:
                second_mask = first_mask
            else:
                second_mask = background_mask(
                    second_image.shape,
                    [BACKGROUND_CENTER],
                    BACKGROUND_RADIUS,
                )
        else:
            # Preserve the original second-shot exclusion regions.
            second_mask = background_mask(
                second_image.shape,
                centers,
                BACKGROUND_RADIUS,
            )

        second_background = np.mean(second_image[second_mask])
        shot.save_result("background_mean_2nd", second_background)

        # Corrected: use the SECOND image for this diagnostic.
        if second_image.shape[0] < 32 or second_image.shape[1] < 32:
            raise ValueError("Second image is too small for the test ROI.")

        test_roi = second_image[29:32, 29:32]
        shot.save_result(
            "background_integral_2nd",
            np.mean(test_roi - second_background),
        )

        second_corrected = second_image - second_background
        second_rois = extract_rois(second_corrected, centers)
        second_integrals = second_rois.sum(axis=(1, 2))

        for index, integral in enumerate(second_integrals, start=1):
            shot.save_result(f"tw{index}_integral_2nd", integral)

        images.append(second_corrected)
        roi_sets.append(second_rois)
        labels.append("second shot")

analysis_finished = time.perf_counter()

# Archive only once, after closing the analysis file handle.
if SAVE_SCRIPT:
    save_script_copy(path)

archive_finished = time.perf_counter()

figure = plot_results(images, roi_sets, labels, centers)

if SAVE_PLOT and figure is not None:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_path = os.path.join(
        os.path.dirname(path),
        f"{timestamp}_tweezer_analysis.png",
    )
    figure.savefig(output_path, dpi=120)

finished = time.perf_counter()

print(
    f"Analysis + result saving: {analysis_finished - start:.3f} s | "
    f"Script archive: {archive_finished - analysis_finished:.3f} s | "
    f"Plot setup/save: {finished - archive_finished:.3f} s | "
    f"Total: {finished - start:.3f} s"
)

# Lyse handles displaying the figure.
# Its subsequent GUI rendering time is not included above.