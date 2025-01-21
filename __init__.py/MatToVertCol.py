import bpy

# Get the active object
obj = bpy.context.object

# Ensure the object is in the object mode
if bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')

# Ensure the object has a vertex color layer
if not obj.data.vertex_colors:
    obj.data.vertex_colors.new()

# Set the current layer vertex color as active object
vcol_layer = obj.data.vertex_colors.active

# Loop through polygons and assign vertex colors
for poly in obj.data.polygons:
    mat_index = poly.material_index
    material = obj.material_slots[mat_index].material

    #Get the material's base color (Must be Principled BSDF shader)
    if material and material.node_tree:
        base_color = (1,1,1,1)
        for node in material.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                base_color = node.inputs['Base Color'].default_value
                break

        # Assign the base color to the vertex color
        for loop_index in poly.loop_indices:
            vcol_layer.data[loop_index].color = base_color

# Erase the previous material
obj.data.materials.clear()

# Create a new material
new_material = bpy.data.materials.new(name="VCOL Material")
new_material.use_nodes = True
obj.data.materials.append(new_material)

# Get the material's node tree
nodes = new_material.node_tree.nodes
links = new_material.node_tree.links

# Clear all the existing nodes
for node in nodes:
    nodes.remove(node)

# Add Principled BSDF
BSDF_node = nodes.new(type="ShaderNodeBsdfPrincipled")
BSDF_node.location = (0,0)

# Add Attribute Nodes and set the layer to COL
Vert_Node = nodes.new(type="ShaderNodeVertexColor")
Vert_Node.location = (-300, 0)
bpy.data.materials["VCOL Material"].node_tree.nodes["Color Attribute"].layer_name = "Col"

# Add Output Node
M_Out_Node = nodes.new(type="ShaderNodeOutputMaterial")
M_Out_Node.location = (300, 0)

# Connect Nodes
links.new(Vert_Node.outputs["Color"], BSDF_node.inputs["Base Color"])
links.new(BSDF_node.outputs["BSDF"], M_Out_Node.inputs["Surface"])