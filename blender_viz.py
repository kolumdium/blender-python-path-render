from a_star import AStar
import os
import ast
from pathlib import Path
import math
import bpy
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, "C:\\Users\\plank\\blender-venv\\lib\\site-packages\\")

# Assuming the script is run from the directory where 'a_star.py' is located
current_dir = os.path.dirname(os.path.realpath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# TODO move this to config file
# TODO remove hard code path
project_folder = r"C:\Users\plank\Documents\git\blender-python-path-render"
project_path = Path(project_folder)
place = "Freiberg"
project_data_path = Path(project_folder, "data", place)

nodes_df = pd.read_csv(project_data_path /
                       "nodes_transformed.csv", index_col="node_id")
adj_list_df = pd.read_csv(
    project_data_path / "adj_list.csv", index_col="node_id")
adj_list_with_weights_df = pd.read_csv(
    project_data_path / "adj_list_with_weights.csv")

adj_list_df['neighbors_indices'] = adj_list_df['neighbors_indices'].apply(
    ast.literal_eval)
adj_list_with_weights_df['neighbors_with_weights'] = adj_list_with_weights_df['neighbors_with_weights'].apply(
    ast.literal_eval)

adj_list_df = adj_list_df.explode('neighbors_indices')
adj_list_df.dropna(subset=['neighbors_indices'], inplace=True)
adj_list_df.reset_index(inplace=True)
edges = list(zip(adj_list_df['node_id'], adj_list_df['neighbors_indices']))

adj_list = {}
for index, row in adj_list_with_weights_df.iterrows():
    node = row['node_id']
    neighbors = {n_id: round(weight, 3) for n_id,
                 weight in row['neighbors_with_weights']}
    adj_list[node] = neighbors

node_render_coordinates = {i: (row['x'], row['y'])
                           for i, row in nodes_df.iterrows()}

node_distance_coordinates = {i: (row['lat'], row['lon'])
                             for i, row in nodes_df.iterrows()}

vertices = np.array(nodes_df[['x', 'y']] * 10)
vertices = np.column_stack((vertices, np.zeros(len(vertices))))
# vertices

# Setup scene for rendering
# Use FFMPEG video format
bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
video_path = Path(project_folder, "videos", place + "-a_star" + ".mp4")
bpy.context.scene.render.filepath = str(video_path)  # Set output path
bpy.context.scene.render.ffmpeg.format = 'MPEG4'
bpy.context.scene.render.ffmpeg.codec = 'H264'
bpy.context.scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
bpy.context.scene.render.fps = 10  # Set frames per second

# new Pencil
gpencil_data = bpy.data.grease_pencils.new("GPencil")
gpencil = bpy.data.objects.new(gpencil_data.name, gpencil_data)
bpy.context.collection.objects.link(gpencil)
glow_fx = gpencil.shader_effects.new('glow', 'FX_GLOW')
glow_fx.samples = 32
glow_fx.size.x = 150.0
glow_fx.size.y = 150.0
glow_fx.opacity = 0.6
gp_layer = gpencil_data.layers.new("base")
gp_frame = gp_layer.frames.new(1)

# color the edges
for edge in edges:
    gp_stroke = gp_frame.strokes.new()
    gp_stroke.line_width = 6
    gp_stroke.start_cap_mode = 'ROUND'
    gp_stroke.end_cap_mode = 'ROUND'
    gp_stroke.points.add(count=2)
    for i, point in enumerate(edge):
        gp_stroke.points[i].co = (
            vertices[point][0], vertices[point][1], vertices[point][2])
        gp_stroke.points[i].vertex_color = (0.2745, 0.4666, 0.4823, 0.2)


# Create one grease pencil object
gpencil_data = bpy.data.grease_pencils.new("GPencil")
gpencil = bpy.data.objects.new(gpencil_data.name, gpencil_data)
bpy.context.collection.objects.link(gpencil)
progress_mat = bpy.data.materials.new(name='Black')
bpy.data.materials.create_gpencil_data(progress_mat)
gpencil.data.materials.append(progress_mat)

# Setup glow effect once
glow_fx = gpencil.shader_effects.new('glow', 'FX_GLOW')
glow_fx.samples = 32
glow_fx.size.x = 150.0
glow_fx.size.y = 150.0
glow_fx.opacity = 0.6

algorithm = AStar(adj_list, node_distance_coordinates)
# source = 50000
source = np.random.choice(nodes_df.index)
# goal = 55084
goal = np.random.choice(nodes_df.index)
algorithm.initialize(source, goal)
algorithm.get_explored_nodes()
source_x, source_y, _ = vertices[source]

# TODO there is propably a more performant way to drawing this.
iteration = 0
frame = 0
nth_iteration = 1
iteration_end = 10000
while algorithm.step():
    # print only every n th iteration
    if iteration % nth_iteration == 0:
        frame += 1
        bpy.context.scene.frame_set(frame)  # Set the current frame

        gp_layer = gpencil_data.layers.new(f"viz_{frame}", set_active=True)
        gp_frame = gp_layer.frames.new(frame)

        max_dist = 0
        result_distances = {}
        explored_nodes = algorithm.get_explored_nodes()

        for node in explored_nodes:
            x_dist = source_x - vertices[node][0]
            y_dist = source_y - vertices[node][1]
            distance = math.sqrt(x_dist ** 2 + y_dist ** 2)
            result_distances[node] = distance
            max_dist = max(max_dist, distance)

        if max_dist == 0:
            max_dist = 1

        # Pre-calculate colors for each node based on distance
        node_colors = {
            node_id: math.sqrt(dist / max_dist) for node_id, dist in result_distances.items()
        }

        # Color and draw strokes for each node based on distance
        for node_id, fac in node_colors.items():
            color = (0.2745 - (0.2745 - 0.1137) * fac, 0.4666 + (0.8588 - 0.4666)
                     * fac, 0.4823 + (0.4862 - 0.4823) * fac, 0.2 + (1.0 - 0.2) * fac)
            for edge in adj_list[node_id].keys():
                # print("stroke")
                gp_stroke = gp_frame.strokes.new()
                gp_stroke.line_width = 8
                gp_stroke.start_cap_mode = 'ROUND'
                gp_stroke.end_cap_mode = 'ROUND'
                gp_stroke.points.add(count=2)
                gp_stroke.points[0].co = (
                    vertices[node_id][0], vertices[node_id][1], vertices[node_id][2] + 0.1)
                gp_stroke.points[0].vertex_color = color
                gp_stroke.points[1].co = (
                    vertices[edge][0], vertices[edge][1], vertices[edge][2] + 0.1)
                gp_stroke.points[1].vertex_color = color

    iteration += 1

    if iteration == 100:
        nth_iteration = 10

    if iteration == 250:
        nth_iteration = 25

    if iteration == 500:
        nth_iteration = 50

    if iteration == 1000:
        nth_iteration = 100

    if iteration > iteration_end:
        break

path = algorithm.reconstruct_path()

# new Pencil
gpencil_data = bpy.data.grease_pencils.new("GPencil")
gpencil = bpy.data.objects.new(gpencil_data.name, gpencil_data)
bpy.context.collection.objects.link(gpencil)

progress_mat = bpy.data.materials.new(name='Green')
bpy.data.materials.create_gpencil_data(progress_mat)
gpencil.data.materials.append(progress_mat)

glow_fx = gpencil.shader_effects.new('glow', 'FX_GLOW')
glow_fx.samples = 32
glow_fx.size.x = 150.0
glow_fx.size.y = 150.0
glow_fx.opacity = 0.6
gp_layer = gpencil_data.layers.new("base")
gp_frame = gp_layer.frames.new(frame)

# Highlight the path in red
for i in range(len(path)-1):
    node_id = path[i]
    next_node_id = path[i+1]

    gp_stroke = gp_frame.strokes.new()
    gp_stroke.line_width = 10
    gp_stroke.start_cap_mode = 'ROUND'
    gp_stroke.end_cap_mode = 'ROUND'
    gp_stroke.points.add(count=2)
    gp_stroke.points[0].co = (vertices[node_id][0],
                              vertices[node_id][1], vertices[node_id][2] + 0.1)
    gp_stroke.points[0].vertex_color = (1, 0, 0, 1)  # red color
    gp_stroke.points[1].co = (
        vertices[next_node_id][0], vertices[next_node_id][1], vertices[next_node_id][2] + 0.1)
    gp_stroke.points[1].vertex_color = (1, 0, 0, 1)  # red color

# Duplicate the path frame for 20 frames
for frame_number in range(1, 20):
    gp_layer.frames.copy(gp_frame)
    frame += 1

# Optionally, set end frame for video output based on iterations
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = frame
camera = bpy.data.objects['Camera']
camera.location = (4, 4, 10)
# TODO set Camera Angle
# camera.rotation_axis_angle = (0,0,0)
print("Job done!")
