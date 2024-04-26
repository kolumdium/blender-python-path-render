import osmnx as ox
import numpy as np
import pandas as pd
from pathlib import Path


def make_adj_list(G):
    indices = {node: idx for idx, node in enumerate(G.nodes())}
    adj_list_with_weights = {}
    adj_list = {}
    for node in G.nodes:
        neighbors_and_weights = [(indices[neighbor], data.get(0, {}).get('length', None))
                                 for neighbor, data in G[node].items() if 'length' in data.get(0, {})]
        neighbors = [indices[neighbor] for neighbor in G[node]]

        # Store in dictionaries
        adj_list_with_weights[node] = neighbors_and_weights
        adj_list[node] = neighbors

    # Convert dictionaries to DataFrame
    df_adj_list = pd.DataFrame(list(adj_list.items()), columns=[
        'node_id', 'neighbors_indices'])
    df_adj_list_with_weights = pd.DataFrame(list(
        adj_list_with_weights.items()), columns=['node_id', 'neighbors_with_weights'])

    # Convert node index to index from indices dictionary
    df_adj_list['node_id'] = df_adj_list['node_id'].map(indices)
    df_adj_list_with_weights['node_id'] = df_adj_list_with_weights['node_id'].map(
        indices)

    return df_adj_list, df_adj_list_with_weights


def add_blender_coordinates(nodes):
    minx, miny, maxx, maxy = nodes.total_bounds
    viz_scale = maxy - miny
    minx, miny, maxx, maxy = minx + 90, miny + 90, maxx + 90, maxy + 90
    minx, miny, maxx, maxy

    c = 0.0001120378  # TODO: Find a way to calculate this value; I got this from another project
    angle_rad = np.abs(nodes['y']) * np.deg2rad(1)
    x_scale_factor = np.sqrt(1 - (np.abs(nodes['y']) / 90) ** 2)
    y_scale_factor = (1 + c * (np.cos(2 * angle_rad) - 1)) / np.cos(angle_rad)

    nodes['new_x'] = (((nodes['x'] + 90) - minx) * x_scale_factor) / viz_scale
    nodes['new_y'] = ((((nodes['y'] + 90) - miny) * y_scale_factor) /
                      viz_scale) * (1 - (nodes['y'] / 900))

    return nodes


def export_blender_coordinates(nodes, output_folder):
    export = nodes[['new_x', 'new_y', "x", "y"]]
    export.reset_index(inplace=True)
    # Reset index twice to get node_id and not osm_id
    export.reset_index(inplace=True)
    export.columns = ['node_id', 'osm_id', 'x', 'y', "lon", "lat"]
    export_path = Path(output_folder, "nodes_transformed.csv")
    export.to_csv(export_path, columns=[
        'node_id', 'osm_id', 'x', 'y', "lon", "lat"], index=False)


def export_adj_list(df_adj_list, df_adj_list_with_weights, output_folder):
    export_path = Path(output_folder, "adj_list.csv")
    export_path_with_weights = Path(output_folder, "adj_list_with_weights.csv")
    df_adj_list.to_csv(export_path, index=False)
    df_adj_list_with_weights.to_csv(
        export_path_with_weights, index=False)


def graph_to_blender_files(G, output_folder=""):
    nodes = ox.graph_to_gdfs(G, edges=False)
    nodes = add_blender_coordinates(nodes)
    print("Exporting Blender Coordinates...")
    export_blender_coordinates(nodes, output_folder=output_folder)
    print("Creating adjacency list...")
    df_adj_list, df_adj_list_with_weights = make_adj_list(G)
    print("Exporting adjacency list...")
    export_adj_list(df_adj_list=df_adj_list,
                    df_adj_list_with_weights=df_adj_list_with_weights, output_folder=output_folder)


if __name__ == '__main__':
    print("Exporting files...")
    place = 'Freiberg, Sachsen'
    G = ox.graph_from_place(place, network_type='drive')
    print("Graph loaded successfully")
    output_folder = Path("data", place.split(",")[0])
    if not output_folder.exists():
        output_folder.mkdir(parents=True)
    graph_to_blender_files(G, output_folder=output_folder)
    print("Files exported successfully")
