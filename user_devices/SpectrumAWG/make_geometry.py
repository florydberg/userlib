import numpy as np
import h5py
from scipy.spatial import Delaunay
import matplotlib.pyplot as plt

def generate_points(pattern, num_points, xy_range=(-200, 200)):
    if pattern == 'triangular':
        side = int(np.ceil(np.sqrt(num_points)))
        x = np.linspace(xy_range[0], xy_range[1], side)
        y = np.linspace(xy_range[0], xy_range[1], side)
        xx, yy = np.meshgrid(x, y)
        xx[1::2] += (x[1] - x[0]) / 2  # Shift alternate rows
        points = np.column_stack([xx.ravel(), yy.ravel()])
        points = points[:num_points]

    elif pattern == 'square':
        side = int(np.ceil(np.sqrt(num_points)))
        x = np.linspace(xy_range[0], xy_range[1], side)
        y = np.linspace(xy_range[0], xy_range[1], side)
        xx, yy = np.meshgrid(x, y)
        points = np.column_stack([xx.ravel(), yy.ravel()])
        points = points[:num_points]

    elif pattern == 'icosahedral':
        indices = np.arange(0, num_points) + 0.5
        phi = np.arccos(1 - 2 * indices / num_points)
        theta = np.pi * (1 + 5**0.5) * indices
        x = np.cos(theta) * np.sin(phi)
        y = np.sin(theta) * np.sin(phi)
        points = np.column_stack([x, y]) * xy_range[1]

    else:
        raise ValueError("Unknown pattern type")
    
    return points

def triangulate_points(points):
    delaunay = Delaunay(points)
    edges = set()
    for simplex in delaunay.simplices:
        edges.update([
            tuple(sorted([simplex[0], simplex[1]])),
            tuple(sorted([simplex[1], simplex[2]])),
            tuple(sorted([simplex[2], simplex[0]])),
        ])
    return np.array(sorted(edges))

def save_to_hdf5(filename, points, edges):
    with h5py.File(filename, 'w') as f:
        f.create_dataset('points', data=points)
        f.create_dataset('num_points', data=np.array([len(points)], dtype=int))
        f.create_dataset('edges', data=edges)

def plot_graph(points, edges, pattern, num_points):
    plt.figure(figsize=(8, 8))
    for edge in edges:
        p1, p2 = points[edge[0]], points[edge[1]]
        plt.plot([p1[0], p2[0]], [p1[1], p2[1]], 'b-')
    plt.scatter(points[:, 0], points[:, 1], color='red', zorder=5)
    plt.title(f"{pattern.capitalize()} pattern with {num_points} points")
    plt.axis('equal')
    plt.grid(True)
    plt.show()

def main():
    pattern = input("Select pattern [triangular/square/icosahedral]: ").strip().lower()
    num_points = int(input("Enter number of points: "))

    points = generate_points(pattern, num_points)
    edges = triangulate_points(points)
    filename = f"{pattern}_{num_points}.h5"
    save_to_hdf5(filename, points, edges)

    print(f"Saved {len(points)} points and {len(edges)} edges to '{filename}'.")
    plot_graph(points, edges, pattern, num_points)

if __name__ == '__main__':
    main()
