bl_info = {
    "name": "MatToVertCol",
    "description": "Converts all selected objects' materials into vertex colors and merges them into one material",
    "author": "Nafis Widihasmoro",
    "version": (0, 5),
    "blender": (4, 2, 5),
    "location": "View3D > Sidebar > MatToVertCol",
    "category": "Object",
}

import bpy

class OBJECT_PT_MatToVertColPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_mat_to_vert_col"
    bl_label = "Material to Vertex Color"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MatToVertCol'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Display the "Delete Previous Material" property
        layout.prop(scene, "delete_previous_material", text="Delete Previous Materials")
        layout.prop(scene, "new_material_name", text="New Material Name")
        layout.operator("object.mat_to_vert_col", text="Convert Materials to Vertex Colors")

class OBJECT_OT_MatToVertColOperator(bpy.types.Operator):
    """Converts materials to vertex colors for selected objects"""
    bl_idname = "object.mat_to_vert_col"
    bl_label = "Convert"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        selected_objects = context.selected_objects

        if not selected_objects:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}

        new_material_name = scene.new_material_name if scene.new_material_name else "VCOL_Material"

        for obj in selected_objects:
            if obj.type != 'MESH':
                continue

            # Ensure the object is in object mode
            if obj.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')

            # Ensure the object has a vertex color layer
            if not obj.data.vertex_colors:
                obj.data.vertex_colors.new(name="Col")

            vcol_layer = obj.data.vertex_colors["Col"]

            # Loop through polygons and assign vertex colors
            for poly in obj.data.polygons:
                mat_index = poly.material_index
                material = obj.material_slots[mat_index].material if mat_index < len(obj.material_slots) else None

                # Get the material's base color (assuming Principled BSDF shader)
                base_color = (1, 1, 1, 1)
                if material and material.node_tree:
                    for node in material.node_tree.nodes:
                        if node.type == 'BSDF_PRINCIPLED':
                            base_color = node.inputs['Base Color'].default_value
                            break

                # Assign the base color to the vertex color
                for loop_index in poly.loop_indices:
                    vcol_layer.data[loop_index].color = base_color

            # Optionally delete the previous materials
            if scene.delete_previous_material:
                obj.data.materials.clear()

            # Always add a new material with vertex color as input
            new_material = bpy.data.materials.new(name=new_material_name)
            new_material.use_nodes = True
            obj.data.materials.append(new_material)

            nodes = new_material.node_tree.nodes
            links = new_material.node_tree.links

            # Clear all nodes and set up new ones
            for node in nodes:
                nodes.remove(node)

            vert_col_node = nodes.new(type="ShaderNodeVertexColor")
            vert_col_node.location = (-300, 0)
            vert_col_node.layer_name = "Col"

            bsdf_node = nodes.new(type="ShaderNodeBsdfPrincipled")
            bsdf_node.location = (0, 0)

            output_node = nodes.new(type="ShaderNodeOutputMaterial")
            output_node.location = (300, 0)

            links.new(vert_col_node.outputs["Color"], bsdf_node.inputs["Base Color"])
            links.new(bsdf_node.outputs["BSDF"], output_node.inputs["Surface"])

        self.report({'INFO'}, f"Materials converted to vertex colors with new material: {new_material_name}")
        return {'FINISHED'}

# Registering and unregistering the classes
def menu_func(self, context):
    self.layout.operator(OBJECT_OT_MatToVertColOperator.bl_idname)

def register():
    bpy.utils.register_class(OBJECT_PT_MatToVertColPanel)
    bpy.utils.register_class(OBJECT_OT_MatToVertColOperator)

    # Add a BoolProperty to the scene for user control
    bpy.types.Scene.delete_previous_material = bpy.props.BoolProperty(
        name="Delete Previous Materials",
        description="Delete existing materials after converting to vertex colors",
        default=True
    )

    # Add a StringProperty for renaming the new material
    bpy.types.Scene.new_material_name = bpy.props.StringProperty(
        name="New Material Name",
        description="Name of the new material created",
        default="VCOL_Material"
    )

    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    bpy.utils.unregister_class(OBJECT_PT_MatToVertColPanel)
    bpy.utils.unregister_class(OBJECT_OT_MatToVertColOperator)

    del bpy.types.Scene.delete_previous_material
    del bpy.types.Scene.new_material_name

    bpy.types.VIEW3D_MT_object.remove(menu_func)

if __name__ == "__main__":
    register()
