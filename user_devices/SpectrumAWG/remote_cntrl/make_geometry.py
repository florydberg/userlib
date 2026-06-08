import numpy as np
import h5py
import matplotlib.pyplot as plt
import os
# =============================================================================
# POINT GENERATION
# =============================================================================

SAVE_DIRECTORY = r"H:\Andre's Paris Work\SLM\patterns"  # Cambia questo percorso con la directory desiderata

def generate_points(pattern, num_points, xlim, ylim):
    if pattern == 'triangular':
        side = int(np.ceil(np.sqrt(num_points)))

        dx = (xlim[1] - xlim[0]) / side
        dy = dx * np.sqrt(3) / 2

        points = []
        for i in range(side):
            for j in range(side):
                x = xlim[0] + j * dx + (i % 2) * dx / 2
                y = ylim[0] + i * dy
                points.append([x, y])

        points = np.array(points[:num_points])

    elif pattern == 'square':
        side = int(np.ceil(np.sqrt(num_points)))

        x = np.linspace(xlim[0], xlim[1], side)
        y = np.linspace(ylim[0], ylim[1], side)
        xx, yy = np.meshgrid(x, y)

        points = np.column_stack([xx.ravel(), yy.ravel()])
        points = points[:num_points]

    elif pattern == 'icosahedral':
        indices = np.arange(0, num_points) + 0.5
        phi = np.arccos(1 - 2 * indices / num_points)
        theta = np.pi * (1 + 5**0.5) * indices

        x = np.cos(theta) * np.sin(phi)
        y = np.sin(theta) * np.sin(phi)

        points = np.column_stack([x, y])

        # Rescale to xlim / ylim
        points[:, 0] = np.interp(points[:, 0], [-1, 1], [xlim[0], xlim[1]])
        points[:, 1] = np.interp(points[:, 1], [-1, 1], [ylim[0], ylim[1]])

    else:
        raise ValueError("Unknown pattern type")

    return points


# =============================================================================
# EDGE GENERATION (CONTROLLED GRAPH)
# =============================================================================

def build_edges_distance(points, max_dist):
    edges = []
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            dist = np.linalg.norm(points[i] - points[j])
            if dist < max_dist:
                edges.append((i, j))
    return np.array(edges)


def build_grid_edges(points, side):
    edges = []
    for i in range(side):
        for j in range(side):
            idx = i * side + j

            if idx >= len(points):
                continue

            if j < side - 1 and idx + 1 < len(points):
                edges.append((idx, idx + 1))

            if i < side - 1 and idx + side < len(points):
                edges.append((idx, idx + side))

    return np.array(edges)


# =============================================================================
# SAVE
# =============================================================================

def save_to_hdf5(filename, points, edges):
    with h5py.File(filename, 'w') as f:
        f.create_dataset('tweezer_base', data=points)
        f.create_dataset('target_traps', data=points)
        f.create_dataset('target_pattern', data=np.ones(len(points), dtype=bool))
        f.create_dataset('num_points', data=np.array([len(points)], dtype=int))
        f.create_dataset('edges', data=edges)


# =============================================================================
# PLOT
# =============================================================================

def plot_graph(points, edges, pattern, num_points):
    plt.figure(figsize=(8, 8))

    # edges
    for edge in edges:
        p1, p2 = points[edge[0]], points[edge[1]]
        plt.plot([p1[0], p2[0]], [p1[1], p2[1]])

    # points
    plt.scatter(points[:, 0], points[:, 1], zorder=5)

    # indices (VERY useful for debugging)
    for i, (x, y) in enumerate(points):
        plt.text(x, y, str(i), fontsize=8)

    plt.title(f"{pattern.capitalize()} pattern with {num_points} points")
    plt.axis('equal')
    plt.grid(True)
    plt.show()


# =============================================================================
# MAIN
# =============================================================================

def main():
    pattern = input("Select pattern [triangular/square/icosahedral]: ").strip().lower()
    num_points = int(input("Enter number of points: "))

    print("\n⚠️ Use pixel coordinates matching your camera/SLM\n")
    x_min = float(input("Enter x_min (e.g. 0): "))
    x_max = float(input("Enter x_max (e.g. 200): "))
    y_min = float(input("Enter y_min (e.g. 0): "))
    y_max = float(input("Enter y_max (e.g. 200): "))

    xlim = (x_min, x_max)
    ylim = (y_min, y_max)

    points = generate_points(pattern, num_points, xlim, ylim)

    # EDGE STRATEGY
    if pattern == 'square':
        side = int(np.ceil(np.sqrt(num_points)))
        edges = build_grid_edges(points, side)
    else:
        # distance-based (works well for triangular / irregular)
        max_dist = np.linalg.norm(points[1] - points[0]) * 1.5
        edges = build_edges_distance(points, max_dist)

    os.makedirs(SAVE_DIRECTORY, exist_ok=True)

    filename = os.path.join(SAVE_DIRECTORY, f"{pattern}_{num_points}.h5")
    save_to_hdf5(filename, points, edges)


    print(f"\n✅ Saved {len(points)} points and {len(edges)} edges to '{filename}'")

    plot_graph(points, edges, pattern, num_points)


if __name__ == '__main__':
    main()