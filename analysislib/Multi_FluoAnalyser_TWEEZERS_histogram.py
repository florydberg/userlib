from lyse import *
from pylab import *
import csv
import runmanager
from runmanager.remote import *
import numpy as np
import math
from scipy.optimize import curve_fit, least_squares
from scipy.stats import poisson
import numpy as np
import matplotlib.pyplot as plt
import datetime, time
# import seaborn as sns
import pandas as pd
from scipy.special import erf

ts=time.time()
dt=datetime.datetime.now().date()
dtf = datetime.datetime.now()
show_tweezer_histograms = False


def saturation(dBm):
        Imag_beam_Power=140e-6/28*dBm #W   #TODO: update this value with the measure we have to take

        waist_0=6.667e-3 #m
        I=2*Imag_beam_Power/(np.pi*waist_0**2)
        lambda_laser = 461*1e-9
        delta=0
        Gam=32e6

        h=6.626e-34 #JHz^-1
        c=2.99e8 # m/s

        I_sat = (np.pi* h*c*Gam)/(3*lambda_laser**3) # previous calculation was 67.6
        sat=I*100000//I_sat/100000
        # sat=I/I_sat
        return sat

def data_mean(para, values):
    data1 = {}
    std1 = {}
    stdN = {}
    for ii in set(para):
        indices = [idx for idx, val in enumerate(para) if val == ii]
        aa = [values[idx] for idx in indices]
        data1[ii] = np.mean(aa)
        std1[ii] = np.std(aa)
        stdN[ii] = np.std(aa)/sqrt(len(aa))
    x = sorted(data1.keys())
    y = [data1[key] for key in x]
    e = [std1[key] for key in x]
    eN= [stdN[key] for key in x]
    return x, y, e, eN

def duo_mean(param1, param2, values):
    """
    Computes the mean, standard deviation, and standard error for each combination of param1 and param2 values.

    Args:
        param1: List or array of first parameter values.
        param2: List or array of second parameter values.
        values: List or array of values corresponding to the param1, param2 pairs.

    Returns:
        A dictionary containing:
        - mean_values: Dictionary with (param1, param2) pairs as keys and their mean values as values.
        - std_values: Dictionary with (param1, param2) pairs as keys and their standard deviations as values.
        - error_values: Dictionary with (param1, param2) pairs as keys and their standard errors as values.
    """
    mean_values = {}
    std_values = {}
    error_values = {}
    
    # Ensure that param1, param2, and values are all of the same length
    if len(param1) != len(param2) or len(param1) != len(values):
        raise ValueError("The length of param1, param2, and values must be the same.")

    # Create unique pairs of (param1, param2)
    unique_pairs = set(zip(param1, param2))
    
    for pair in unique_pairs:
        # Step 1: Generate indices where param1 and param2 match the pair
        indices = [idx for idx, val in enumerate(zip(param1, param2)) if val == pair]

        if not indices:
            continue  # Skip if there are no indices for this pair
        
        # Step 2: Extract corresponding values using indices
        try:
            aa = [values[idx] for idx in indices]
        except IndexError as e:
            print(f"IndexError: {e}. Check the length of the values list and the indices.")
            continue
        
        # Step 3: Compute mean, std, and error on mean
        mean_values[pair] = np.mean(aa)
        std_values[pair] = np.std(aa)
        error_values[pair] = np.std(aa) / sqrt(len(aa))
    
    return mean_values, std_values, error_values

def plot_heatmap(mean_values):
    """
    Plots a heatmap from the mean values of (param1, param2) pairs.

    Args:
        mean_values: Dictionary with (param1, param2) pairs as keys and their mean values as values.
    """
    # Step 1: Convert the mean_values dictionary to a DataFrame
    df = pd.DataFrame(list(mean_values.items()), columns=['Params', 'Mean Value'])
    
    # Split the Params tuple into two separate columns: 'param1' and 'param2'
    df['param1'] = df['Params'].apply(lambda x: x[0])
    df['param2'] = df['Params'].apply(lambda x: x[1])
    
    # Step 2: Pivot the DataFrame to create a matrix format
    df_pivot = df.pivot(index='param1', columns='param2', values='Mean Value')

    # Step 3: Plot the heatmap
    plt.figure(figsize=(8, 6))
    sns.heatmap(df_pivot, annot=False, fmt='.0f', cmap="viridis", linewidths=.5, vmin=0, vmax=+2500)
    
    # Add labels and a title
    plt.title("Heatmap of Mean Values across param1 and param2")
    plt.xlabel("param2")
    plt.ylabel("param1")
    
    plt.show()

def save_imag(plt, name):
    picname = name
    tm = datetime.datetime.now()        
    if duo:
        img_name=str(dt) + '_' + tm.strftime("%H") + tm.strftime("%M") + tm.strftime("%S") + '_' +tm.strftime("%f")  + '_' + para1_name + '_' + para2_name
    else:
        img_name=str(dt)  + '_' + tm.strftime("%H") + tm.strftime("%M") + tm.strftime("%S") + '_' +tm.strftime("%f")  + '_' + para1_name
    plt.savefig(two_levels_up+ '/' + img_name +  '_' + picname + ".png")
    print(picname + ' saved')

def Tweezers_scan(value, title):
    plt.figure()  ##################################################################### 
    for jj in range(n_tweezer):
        means_ii=tuple(value.get(str(jj+1)))
        x,y,error,errorN=data_mean(para1_name, means_ii)
        # Subtract offset from x-axis values
        x_adjusted = [2*(xi) for xi in x]
        # plt.errorbar(x, y, yerr=errorN, fmt='--o', ecolor='gray',capsize=5)
        plt.errorbar(x, y, yerr=errorN, fmt='--o', ecolor='black',capsize=5)  #
    plt.rcParams.update({'font.size': 20})
    plt.legend([f'ROI{i}' for i in range(1, n_tweezer + 1)])
    xlabel=str(para1_name)+' ('+str(para1_unit)+')'
    if saving_location:
        xlabel+='\n'+ str(one_level_up)
    # plt.xlabel(xlabel)
    plt.xlabel('Detuning from free space resonance (MHz)')
    #plt.xlabel('time(ms) holdTime_fluoImg')
    plt.title(str(one_level_up))
    plt.ylabel('photons')
    # plt.yscale('log')
    plt.grid(False)
    # plt.xscale('log')
    # plt.ylim(0,1)
    if saving_plots: save_imag(plt, title)  #####################################################################
def plot_individual_tweezer_histograms(
    analyser,
    bins,
):
    """Plot first- and second-shot histograms for all 36 tweezers."""

    fig, axes = plt.subplots(
        6,
        6,
        figsize=(16, 13),
        sharex=True,
        sharey=True,
        constrained_layout=True,
    )

    for tweezer, ax in enumerate(axes.flat, start=1):

        first_values = finite_values(
            analyser[f"tw{tweezer}_integral"]
        )

        second_values = finite_values(
            analyser[f"tw{tweezer}_integral_2nd"]
        )

        # Same filled-bar design as the summed histogram.
        ax.hist(
            [first_values, second_values],
            bins=bins,
            color=["b", "r"],
            histtype="bar",
            fill=True,
            stacked=False,
            alpha=1.0,
            label=["First Shot", "Second Shot"],
        )

        ax.set_title(
            f"Tweezer {tweezer}",
            fontsize=9,
        )

        ax.tick_params(
            axis="both",
            labelsize=7,
        )

    handles, labels = axes.flat[0].get_legend_handles_labels()

    fig.legend(
        handles,
        labels,
        loc="upper right",
    )

    fig.suptitle(
        "First and Second Shot - Individual Tweezers",
        fontsize=14,
    )

    fig.supxlabel("photons")
    fig.supylabel("occurrences")

    return fig
def Tweezers_scan_tot(value, title):
    plt.figure()  ##################################################################### 
    all_y = []
    all_errorN = []    
    
    for jj in range(n_tweezer):
        means_ii=tuple(value.get(str(jj+1)))
        x,y,error,errorN=data_mean(para1_name, means_ii)      
        all_y.append(y)
        all_errorN.append(errorN)

    all_y = np.array(all_y)  
    all_errorN = np.array(all_errorN)
    y_mean = np.mean(all_y, axis=0)  
    errorN_mean = np.sqrt(np.sum(all_errorN**2, axis=0)) / n_tweezer

    # Subtract offset from x-axis values
    x_adjusted = [2*(xi) for xi in x]
    print(x, y, errorN_mean)
    # plt.errorbar(x, y, yerr=errorN, fmt='--o', ecolor='gray',capsize=5)
    plt.errorbar(x, y_mean, yerr=errorN_mean, fmt='-o',mfc='none', mec='black', lw=1, ecolor='black', color='black', capsize=5)  #
    plt.rcParams.update({'font.size': 20})
    # plt.legend(['mean of the 9 ROI'])
    # xlabel=str(para1_name)+' ('+str(para1_unit)+')'
    # if saving_location:
        # xlabel+='\n'+ str(one_level_up)
    # plt.xlabel(xlabel)
    plt.xlabel('Detuning from free space resonance (MHz)')
    #plt.xlabel('time(ms) holdTime_fluoImg')
    plt.title(str(one_level_up))
    plt.ylabel('photons')
    # plt.yscale('log')
    plt.grid(False)
    # plt.xscale('log')
    # plt.ylim(0,1)
    # if saving_plots: save_imag(plt, title)  #####################################################################


def Tweezers_scan_duo(values, title):
    values=tuple(values)
    mean_values, std_values, error_values = duo_mean(parameter2, parameter1, values)
    plot_heatmap(mean_values)

    plt.ylabel(str(para2_name)+ ' ('+str(para2_unit)+')')
    xlabel=str(para1_name)+' ('+str(para1_unit)+')'
    if saving_location:
        xlabel+='\n' + str(one_level_up)
    plt.xlabel(xlabel)
    plt.title(title)

    print("Heatmap data saved to heatmap_data.csv")

    if saving_plots: save_imag(plt, title)  #####################################################################

def calculate_mean_images(paths):
    """
    Calculate two separate mean raw images over all shots
    currently present in the Lyse dataframe.

    First mean:
        TweezFluo

    Second mean:
        second-shot
    """

    first_sum = None
    second_sum = None

    first_count = 0
    second_count = 0

    for file_path in paths:

        try:
            with Run(file_path).open("r") as shot:

                # ==================================================
                # FIRST SHOT
                # ==================================================

                try:
                    image = shot.get_image(
                        "Orca_Camera",
                        "TweezFluo",
                        "frame",
                    )

                    image = np.asarray(image, dtype=np.float64)

                    # If there are multiple frames, average them
                    if image.ndim == 3:
                        image = np.mean(image, axis=0)

                    if image.ndim != 2:
                        raise ValueError(
                            f"Unexpected FIRST image shape: {image.shape}"
                        )

                    if first_sum is None:
                        first_sum = np.zeros_like(
                            image,
                            dtype=np.float64,
                        )

                    if image.shape == first_sum.shape:
                        first_sum += image
                        first_count += 1

                except Exception as exc:
                    print(
                        f"FIRST image not available in {file_path}: {exc}"
                    )

                # ==================================================
                # SECOND SHOT
                # ==================================================

                try:
                    image = shot.get_image(
                        "Orca_Camera",
                        "second-shot",
                        "frame",
                    )

                    image = np.asarray(image, dtype=np.float64)

                    # If there are multiple frames, average them
                    if image.ndim == 3:
                        image = np.mean(image, axis=0)

                    if image.ndim != 2:
                        raise ValueError(
                            f"Unexpected SECOND image shape: {image.shape}"
                        )

                    if second_sum is None:
                        second_sum = np.zeros_like(
                            image,
                            dtype=np.float64,
                        )

                    if image.shape == second_sum.shape:
                        second_sum += image
                        second_count += 1

                except Exception as exc:
                    print(
                        f"SECOND image not available in {file_path}: {exc}"
                    )

        except Exception as exc:
            print(
                f"Could not open {file_path}: {exc}"
            )

    # ==============================================================
    # Calculate the two independent means
    # ==============================================================

    mean_first = None
    mean_second = None

    if first_count > 0:
        mean_first = (
            first_sum / first_count
        )

    if second_count > 0:
        mean_second = (
            second_sum / second_count
        )

    print()
    print(
        f"Mean FIRST image: {first_count} shots"
    )
    print(
        f"Mean SECOND image: {second_count} shots"
    )

    return (
        mean_first,
        mean_second,
        first_count,
        second_count,
    )


def plot_mean_images(
    mean_first,
    mean_second,
    first_count,
    second_count,
):
    """
    Plot FIRST and SECOND mean images in a separate figure.
    """

    available = []

    if mean_first is not None:
        available.append(
            (
                mean_first,
                f"Mean FIRST shot\n({first_count} shots)",
            )
        )

    if mean_second is not None:
        available.append(
            (
                mean_second,
                f"Mean SECOND shot\n({second_count} shots)",
            )
        )

    if not available:
        print("No images available for mean image.")
        return None

    fig, axes = plt.subplots(
        1,
        len(available),
        figsize=(8 * len(available), 7),
        squeeze=False,
    )

    axes = axes.ravel()

    for ax, (image, title) in zip(
        axes,
        available,
    ):

        im = ax.imshow(
            image,
            cmap="plasma",
            origin="upper",
            interpolation="nearest",
        )

        ax.set_title(title)
        ax.set_xlabel("x pixel")
        ax.set_ylabel("y pixel")

        fig.colorbar(
        im,
        ax=ax,
        label="Raw camera counts",
    )

    fig.suptitle(
        "Mean raw images"
    )

    # Do not use tight_layout() here:
    # it is incompatible with the colorbar
    # in this Matplotlib layout engine.
    fig.subplots_adjust(
        top=0.88,
        bottom=0.10,
        left=0.07,
        right=0.92,
        wspace=0.25,
    )

    return fig

    return fig

################################### 
################################### 

duo=0
saturation_conversion=False
saving_plots=True
saving_location=True
n_tweezer=36
saving_data=True
second_shot = 1
MEAN_IMAGE = False


para1_name='ImagingFluo_SetPoint' #'n_shot'
para1_unit='ms'    #'s' 
if duo:
    para2_name='FluoImgPulse_Dt'
    para2_unit='ms'
################################### 
###################################
try:
    import os

    df = data()
    if df.empty:
        raise ValueError("No shots available in lyse.")

    paths = df["filepath"]
    FluoAnalyser = df["FluoAnalyser_tweez"]

    one_level_up = os.path.dirname(str(paths.iloc[-1]))
    two_levels_up = os.path.dirname(one_level_up)

    # ---------------- Settings ----------------
    nbin = 50

    threshold_first = 200
    upper_threshold_first = 800

    threshold_second = 200
    upper_threshold_second = 800
    # ------------------------------------------

    def finite_values(values):
        values = np.asarray(values, dtype=float).ravel()
        return values[np.isfinite(values)]

    # Extract all tweezers together.
    # Separate arrays prevent the second image overwriting the first.
    first_columns = [
        f"tw{i}_integral"
        for i in range(1, n_tweezer + 1)
    ]

    first_photons = finite_values(
        FluoAnalyser[first_columns].to_numpy()
    )
    first_background = finite_values(
        FluoAnalyser["background_integral"].to_numpy()
    )

    images = [
        (
            "First Shot",
            first_photons,
            first_background,
            threshold_first,
            upper_threshold_first,
        )
    ]

    if second_shot:
        second_columns = [
            f"tw{i}_integral_2nd"
            for i in range(1, n_tweezer + 1)
        ]

        second_photons = finite_values(
            FluoAnalyser[second_columns].to_numpy()
        )
        second_background = finite_values(
            FluoAnalyser["background_integral_2nd"].to_numpy()
        )
        # ============================================================
        # SURVIVAL PROBABILITY
        # ============================================================

        total_atoms_first = 0
        total_survived = 0

        for ii in range(1, n_tweezer + 1):

            first = np.asarray(
                FluoAnalyser[f"tw{ii}_integral"],
                dtype=float
            )

            second = np.asarray(
                FluoAnalyser[f"tw{ii}_integral_2nd"],
                dtype=float
            )

            # Consider only shots where both measurements exist
            valid = np.isfinite(first) & np.isfinite(second)

            first = first[valid]
            second = second[valid]

            # Atom present if counts > threshold
            atom_first = first > threshold_first
            atom_second = second > threshold_second

            total_atoms_first += np.sum(atom_first)
            total_survived += np.sum(atom_first & atom_second)

        if total_atoms_first > 0:
            survival_probability = total_survived / total_atoms_first
        else:
            survival_probability = np.nan

        print(f"Survival probability = {survival_probability:.4f}")

        images.append(
            (
                "Second Shot",
                second_photons,
                second_background,
                threshold_second,
                upper_threshold_second,
            )
        )

    # Shared bins make first and second images directly comparable.
    arrays = [
        values
        for _, photons, background, _, _ in images
        for values in (photons, background)
        if values.size
    ]

    if not arrays:
        raise ValueError("No finite histogram values available.")

    lower_edge = min(values.min() for values in arrays)
    upper_edge = max(values.max() for values in arrays)

    if lower_edge == upper_edge:
        lower_edge -= 0.5
        upper_edge += 0.5

    bins = np.linspace(lower_edge, upper_edge, nbin + 1)
    bin_centers = (bins[:-1] + bins[1:]) / 2

    # ONE figure only; no individual ROI figures.
    fig = plt.figure(1, figsize=(16, 7))
    fig.clear()

    axes = fig.subplots(
        1,
        len(images),
        sharex=True,
        squeeze=False,
    )[0]

    csv_rows = []

    for ax, (
        label,
        photons,
        background,
        threshold,
        upper_threshold,
    ) in zip(axes, images):

        # Your original histogram style: solid blue and red bars.
        counts, _, _ = ax.hist(
            [background, photons],
            bins=bins,
            color=["b", "r"],
            histtype="bar",
            fill=True,
            stacked=False,
            alpha=1.0,
            label=["BG", "Atoms"],
        )

        ax.set_title(
            f"{label.lower()} - all {n_tweezer} tweezers",
            fontsize=14,
        )
        ax.set_xlabel("photons")
        ax.set_ylabel("occurrences")
        ax.legend()

        selected = photons[
            (photons > threshold) &
            (photons < upper_threshold)
        ]
        below = photons[photons <= threshold]

        fraction = (
            selected.size / photons.size
            if photons.size else np.nan
        )

        mean_above = selected.mean() if selected.size else np.nan
        std_above = selected.std() if selected.size else np.nan
        mean_below = below.mean() if below.size else np.nan
        std_below = below.std() if below.size else np.nan

        # Retain your framed statistics boxes.
        annotations = [
            (
                0.65,
                f"Above Threshold: {fraction:.2%}",
            ),
            (
                0.53,
                f"Mean Above: {mean_above:.2f}\n"
                f"Std Above: {std_above:.2f}",
            ),
            (
                0.36,
                f"Mean Below: {mean_below:.2f}\n"
                f"Std Below: {std_below:.2f}",
            ),
            (
            0.20,
            f"Survival: {survival_probability:.2%}",
            ),
        ]

        for y, text in annotations:
            ax.text(
                0.95,
                y,
                text,
                transform=ax.transAxes,
                fontsize=12,
                ha="right",
                va="top",
                bbox=dict(
                    boxstyle="round,pad=0.3",
                    edgecolor="black",
                    facecolor="white",
                ),
            )

        if saving_data:
            for source, source_counts in zip(
                ["BG", "Atoms"], counts
            ):
                csv_rows.extend(
                    [
                        f"Full Array - {label}",
                        center,
                        int(count),
                        source,
                    ]
                    for center, count in zip(
                        bin_centers, source_counts
                    )
                )

    if saving_location:
        fig.suptitle(one_level_up, fontsize=12)
        fig.tight_layout(rect=(0, 0, 1, 0.94))
    else:
        fig.tight_layout()

    # Save both histograms together with one CSV write.
    list_name = (
        datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S_%f")
        + "_" + para1_name
    )
    if duo:
        list_name += "_" + para2_name

    if saving_data:
        histogram_data_csv = os.path.join(
            one_level_up,
            list_name + "_histogram_data.csv",
        )

        with open(
            histogram_data_csv, "w", newline=""
        ) as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(
                ["Histogram Type", "Bin Center", "Counts", "Source"]
            )
            writer.writerows(csv_rows)

        with open(
            os.path.join(two_levels_up, list_name + "_shots.csv"),
            "w",
            newline="",
        ) as csvfile:
            csv.writer(csvfile).writerows([path] for path in paths)

        print("Histogram data saved to:", histogram_data_csv)

    if saving_plots:
        fig.savefig(
            os.path.join(
                two_levels_up,
                list_name + "_total_histograms.png",
            )
        )

    if show_tweezer_histograms and second_shot:
        
        tweezer_histogram_figure = (
            plot_individual_tweezer_histograms(
                analyser=FluoAnalyser,
                bins=bins,
            )
        )

        if saving_plots:
            tweezer_histogram_figure.savefig(
                os.path.join(
                    two_levels_up,
                    list_name + "_36_tweezer_histograms.png",
                ),
                dpi=200,
            )

    plt.show()


    if MEAN_IMAGE:
    
        (
            mean_first,
            mean_second,
            first_count,
            second_count,
        ) = calculate_mean_images(paths)

        mean_image_figure = plot_mean_images(
            mean_first,
            mean_second,
            first_count,
            second_count,
        )

        if mean_image_figure is not None:

            if saving_plots:
                mean_image_figure.savefig(
                    os.path.join(
                        two_levels_up,
                        list_name + "_mean_images.png",
                    ),
                    dpi=200,
                    bbox_inches="tight",
                )

            mean_image_figure.show()

    plt.show()

    

except Exception as e:
    import traceback
    print("ERROR:", e)
    traceback.print_exc()