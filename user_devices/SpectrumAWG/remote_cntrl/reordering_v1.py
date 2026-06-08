import h5py
import numpy as np
import os
import time
from glob import glob
import matplotlib.pyplot as plt

def find_newest_hdf5(folder):
    hdf5_files = glob(os.path.join(folder, '**', '*.h5'), recursive=True)
    if not hdf5_files:
        return None
    return max(hdf5_files, key=os.path.getmtime)

def read_frame(h5file, frame_idx=-1):
    dataset_path = '/images/Orca_camera/TweezFluo/frame'
    if dataset_path in h5file:
        dataset = h5file[dataset_path]
        if frame_idx < 0:
            frame_idx = dataset.shape[0] - 1
        if 0 <= frame_idx < dataset.shape[0]:
            return dataset[frame_idx]
    return None

def detect_atoms(image, tweezer_positions, threshold=100):
    occupied = []
    for idx, (x, y) in enumerate(tweezer_positions):
        region = image[int(y)-2:int(y)+3, int(x)-2:int(x)+3]
        max_value = region.max()
        atom_present = max_value > threshold
        print(f"Atom in pos {idx} ({x},{y}): {atom_present} (max={max_value:.1f})")
        occupied.append(atom_present)
    return occupied

from collections import deque, defaultdict

def reorder_tweezers(occupied_positions, target_order, tweezer_positions, edges):
    def find_index(pos):
        return np.where((tweezer_positions == pos).all(axis=1))[0][0]

    def build_graph(edges):
        graph = defaultdict(list)
        for i, j in edges:
            graph[i].append(j)
            graph[j].append(i)
        return graph

    def bfs_path(start, goal, graph, occupied_set):
        """Find shortest path avoiding occupied positions, except the goal."""
        queue = deque([(start, [start])])
        visited = set()
        while queue:
            node, path = queue.popleft()
            if node == goal:
                return path
            visited.add(node)
            for neighbor in graph[node]:
                if neighbor not in visited and (neighbor not in occupied_set or neighbor == goal):
                    queue.append((neighbor, path + [neighbor]))
        return None

    def resolve_obstacle(current_idx, target_idx, graph, occupied_set, move_list):
        path = bfs_path(current_idx, target_idx, graph, occupied_set)
        if path is None or len(path) < 2:
            print(f"No path from {current_idx} to {target_idx}")
            return

        for i in range(1, len(path)):
            from_idx = path[i-1]
            to_idx = path[i]
            if to_idx in occupied_set:
                # Move the blocker out of the way first
                empty_neighbors = [n for n in graph[to_idx] if n not in occupied_set]
                if not empty_neighbors:
                    print(f"No space to resolve obstacle at {to_idx}")
                    return
                resolve_obstacle(to_idx, empty_neighbors[0], graph, occupied_set, move_list)
            # Move current atom
            move_label = f"move_{from_idx}_{to_idx}"
            move_list.append(move_label)
            occupied_set.remove(from_idx)
            occupied_set.add(to_idx)

    # Step 1: build index and graph
    graph = build_graph(edges)
    index_map = {tuple(pos): find_index(pos) for pos in tweezer_positions}
    occupied_set = {find_index(pos) for pos in occupied_positions}
    target_indices = [find_index(pos) for pos in target_order[:len(occupied_positions)]]

    # Step 2: compute moves
    move_list = []
    for curr_pos, tgt_idx in zip(occupied_positions, target_indices):
        curr_idx = find_index(curr_pos)
        if curr_idx == tgt_idx:
            continue  # already in place
        resolve_obstacle(curr_idx, tgt_idx, graph, occupied_set, move_list)

    return move_list

# Configurable parameters
data_folder = r'C:\Experiments\Test_AWG_Spectrum_Reorder'
root_folder = r'C:\Users\AndreaFantini\labscript-suite\userlib\labscriptlib\Test_AWG_Spectrum'
last_file = None
last_frame_count = -1

while True:
    print("Waiting for new file...")
    newest_file = find_newest_hdf5(data_folder)

    if newest_file != last_file:
        print(f"Processing file: {newest_file}")
        last_file = newest_file
        last_frame_count = -1

        with h5py.File(newest_file, 'r+') as h5file:
            print("Reading file")
            dataset_path = '/images/Orca_Camera/TweezFluo/frame'

            # Load tweezer positions and edges from geometry file
            try:
                Tweez_pos_name = h5file["/globals/Calibration AWG/geometry_path"].attrs['points']
                Tweez_pos_path = str(root_folder + '/' + Tweez_pos_name)
            except KeyError:
                Tweez_pos_path = str(root_folder + '/square_9.h5')

            with h5py.File(Tweez_pos_path, 'r') as tweez_file:
                tweezer_positions = tweez_file['points'][:]
                if 'edges' in tweez_file:
                    allowed_moves = tweez_file['edges'][:]
                    print("Allowed moves (edges):")
                    for edge in allowed_moves:
                        print(f"  ({edge[0]} <-> {edge[1]})")
                else:
                    print("No 'edges' dataset found in geometry file.")
                    allowed_moves = []

            target_order = sorted(tweezer_positions, key=lambda p: p[0])

            if dataset_path in h5file:
                dataset = h5file[dataset_path]

                frame = dataset
                print(f"Frame shape: {frame.shape}")
                occupied_flags = detect_atoms(frame, tweezer_positions, threshold=250)
                occupied_positions = [pos for pos, occ in zip(tweezer_positions, occupied_flags) if occ]
                occupied_sorted = sorted(occupied_positions, key=lambda p: p[0])

                moves = reorder_tweezers(
                    occupied_sorted, 
                    target_order[:len(occupied_sorted)], 
                    tweezer_positions, 
                    allowed_moves  # ← from the edges dataset
                )
                print(f"Moves: {moves}")
                last_frame_count = -1

                # Save the sequence to the same HDF5 file
                seq_group = h5file.require_group('reordering_sequence')
                move_data = np.array(moves, dtype=h5py.string_dtype())

                if 'moves' in seq_group:
                    del seq_group['moves']
                seq_group.create_dataset('moves', data=move_data)
            else:
                print(f"No dataset found at {dataset_path} in {newest_file}")
        last_file = newest_file
        last_frame_count = -1

    time.sleep(0.5)
