import h5py
import numpy as np
import os
import time
from glob import glob
import numpy as np
# from remote_cntrl.spectrum_card_interface import SpectrumCardInterface
# from remote_cntrl.spectrum_card_waveform_generation_tool import SpectrumCardWaveformTool
import time
import matplotlib.pyplot as plt
import SpectrumCard

def find_newest_hdf5(folder):
    hdf5_files = glob(os.path.join(folder, '*.h5'))
    if not hdf5_files:
        return None
    return max(hdf5_files, key=os.path.getmtime)

def read_frame(h5file, frame_idx=-1):
    dataset_path = '/images/Orca_camera/TweezFluo/frame'
    if dataset_path in h5file:
        dataset = h5file[dataset_path]
        if frame_idx < 0:
            frame_idx = dataset.shape[0] - 1
        if frame_idx >= 0 and frame_idx < dataset.shape[0]:
            return dataset[frame_idx]
    return None


def detect_atoms(image, tweezer_positions, threshold=100):
    occupied = []
    for x, y in tweezer_positions:
        region = image[int(y)-2:int(y)+3, int(x)-2:int(x)+3]
        atom_present = region.mean() > threshold
        occupied.append(atom_present)
    return occupied

def reorder_tweezers(occupied_positions, target_order):
    moves = []
    for current_pos, target_pos in zip(occupied_positions, target_order):
        if not np.allclose(current_pos, target_pos):
            moves.append({'from': current_pos, 'to': target_pos})
    return moves

# Configurable parameters
data_folder = './data'  # Change this to your folder
tweezer_positions = [(100, 200), (150, 200), (200, 200), (250, 200)]  # Example positions
target_order = sorted(tweezer_positions, key=lambda p: p[0])  # Example target order by x

# Watcher loop (example)
last_frame_count = -1
#############################################################

# awg = SpectrumAWG('awg', device_path="/dev/spcm0")

while True:
    try:
        AWG = SpectrumCard.SpectrumCard("/dev/spcm0",timeout=1)
        AWG.open()

        # spectrum_card = SpectrumCardInterface()
        # spectrum_card.ch1_enabled = True
        # spectrum_card.ch2_enabled = True
        # spectrum_card.setupCard()
        # spectrum_card.startReplay()
        # spectrum_card.closeCard()
    except Exception as e:
        print(f"Error setting up Spectrum Card: {e}")
    time.sleep(3)  # Wait before checking for new files

while False:
    newest_file = find_newest_hdf5(data_folder)
    if newest_file is None:
        print("No HDF5 files found.")
        time.sleep(1)
        continue

    with h5py.File(newest_file, 'r') as h5file:
        dataset_path = '/images/Orca_camera/TweezFluo/frame'
        if dataset_path in h5file:
            dataset = h5file[dataset_path]
            current_frame_count = dataset.shape[0]
            if current_frame_count > last_frame_count:
                for idx in range(last_frame_count + 1, current_frame_count):
                    frame = dataset[idx]
                    occupied_flags = detect_atoms(frame, tweezer_positions, threshold=120)
                    occupied_positions = [pos for pos, occ in zip(tweezer_positions, occupied_flags) if occ]
                    occupied_sorted = sorted(occupied_positions, key=lambda p: p[0])
                    moves = reorder_tweezers(occupied_sorted, target_order[:len(occupied_sorted)])
                    print(f"Frame {idx}: Moves: {moves}")
                last_frame_count = current_frame_count - 1
    time.sleep(0.5)  # Adjust the polling interval as needed
