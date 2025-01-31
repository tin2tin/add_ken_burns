import bpy

# Add-on information
bl_info = {
    "name": "Ken Burns Effect",
    "author": "Tintwotin",
    "version": (1, 6),
    "blender": (3, 00, 0),
    "location": "Sequence Editor > Strip Tools",
    "description": "Add Ken Burns effect to selected image or movie strips",
    "category": "Sequencer"
}

class AddKenBurnsEffect(bpy.types.Operator):
    """Add Ken Burns effect to selected image or movie strips"""
    bl_idname = "sequencer.add_ken_burns_effect"
    bl_label = "Add Ken Burns Effect"

    @classmethod
    def poll(cls, context):
        return context.area.type == 'SEQUENCE_EDITOR'

    def execute(self, context):
        scene = context.scene
        frame = scene.frame_current  # Get the current frame

        in_value = scene.in_value
        out_value = scene.out_value
        interpolation = scene.interpolation
        preset = scene.ken_burns_preset

        strips = [strip for strip in bpy.context.selected_editable_sequences if strip.type in ['IMAGE', 'MOVIE']]

        for strip in strips:
            if not hasattr(strip, "transform"):
                self.report({'WARNING'}, f"Strip {strip.name} has no transform properties.")
                continue

            elem = strip.strip_elem_from_frame(frame)  # Get image resolution at current frame
            if not elem:
                self.report({'WARNING'}, f"Cannot get image resolution for {strip.name}.")
                continue

            img_width, img_height = elem.orig_width, elem.orig_height  # Original image dimensions
            if img_height == 0:
                continue  # Avoid division by zero

            aspect_ratio = img_width / img_height  # Aspect ratio of the image

            # Define zoom target positions (starting from center)
            preset_positions = {
                'CENTER': (0.0, 0.0),  # Center remains at (0, 0)
                'TOP_CENTER': (0.0, 1.0),
                'BOTTOM_CENTER': (0.0, -1.0),
                'LEFT_CENTER': (-1.0, 0.0),
                'RIGHT_CENTER': (1.0, 0.0),
                'TOP_LEFT': (-1.0, 1.0),
                'TOP_RIGHT': (1.0, 1.0),
                'BOTTOM_LEFT': (-1.0, -1.0),
                'BOTTOM_RIGHT': (1.0, -1.0),
            }

            # Calculate normalized coordinates for the selected preset
            target_x, target_y = preset_positions.get(preset, (0.0, 0.0))

            # Offset calculation for alignment of edges
            offset_x = 0.0
            offset_y = 0.0

            # Applying the zoom value
            zoom_factor = out_value / in_value

            if preset == 'TOP_LEFT':
                offset_x = -(img_width * (1 - zoom_factor) / 2)
                offset_y = img_height * (1 - zoom_factor) / 2
            elif preset == 'TOP_RIGHT':
                offset_x = img_width * (1 - zoom_factor) / 2
                offset_y = img_height * (1 - zoom_factor) / 2
            elif preset == 'BOTTOM_LEFT':
                offset_x = -(img_width * (1 - zoom_factor) / 2)
                offset_y = -(img_height * (1 - zoom_factor) / 2)
            elif preset == 'BOTTOM_RIGHT':
                offset_x = img_width * (1 - zoom_factor) / 2
                offset_y = -(img_height * (1 - zoom_factor) / 2)
            elif preset == 'LEFT_CENTER':
                offset_x = -(img_width * (1 - zoom_factor) / 2)
            elif preset == 'RIGHT_CENTER':
                offset_x = img_width * (1 - zoom_factor) / 2
            elif preset == 'CENTER':
                offset_x = 0.0
                offset_y = 0.0
            elif preset == 'TOP_CENTER':
                offset_y = img_height * (1 - zoom_factor) / 2
            elif preset == 'BOTTOM_CENTER':
                offset_y = -(img_height * (1 - zoom_factor) / 2)

            # Apply transformations at start (zoom-in effect)
            transform = strip.transform
            transform.scale_x = in_value
            transform.scale_y = in_value
            transform.offset_x = 0.0  # Start at center
            transform.offset_y = 0.0  # Start at center

            # Remove all keyframes before inserting new ones
            action = bpy.context.scene.animation_data.action
            if action:
                for fcurve in action.fcurves:
                    if "scale_x" in fcurve.data_path or "scale_y" in fcurve.data_path or "offset_x" in fcurve.data_path or "offset_y" in fcurve.data_path:
                        fcurve.keyframe_points.clear()  # Remove all keyframes

            # Insert keyframes for start values
            transform.keyframe_insert(data_path="scale_x", frame=strip.frame_final_start)
            transform.keyframe_insert(data_path="scale_y", frame=strip.frame_final_start)
            transform.keyframe_insert(data_path="offset_x", frame=strip.frame_final_start)
            transform.keyframe_insert(data_path="offset_y", frame=strip.frame_final_start)

            # Apply transformations at end (zoom-out to target position)
            transform.scale_x = out_value
            transform.scale_y = out_value
            transform.offset_x = offset_x
            transform.offset_y = offset_y

            # Insert keyframes for end values
            transform.keyframe_insert(data_path="scale_x", frame=strip.frame_final_end)
            transform.keyframe_insert(data_path="scale_y", frame=strip.frame_final_end)
            transform.keyframe_insert(data_path="offset_x", frame=strip.frame_final_end)
            transform.keyframe_insert(data_path="offset_y", frame=strip.frame_final_end)

            # Select all keyframes in the graph editor
            for window in context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if area.type == 'GRAPH_EDITOR':
                        with context.temp_override(window=window, area=area):
                            bpy.ops.graph.select_all(action='SELECT')
                            bpy.ops.graph.interpolation_type(type=interpolation)

        return {'FINISHED'}

class AddKenBurnsEffectPanel(bpy.types.Panel):
    """Panel for the Add Ken Burns Effect operator"""
    bl_label = "Add Ken Burns Effect"
    bl_idname = "SCENE_PT_add_ken_burns_effect"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Strip Tools'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        col = layout.column(align=True)
        col.prop(context.scene, "in_value")
        col.prop(context.scene, "out_value")
        layout.prop(context.scene, "ken_burns_preset")  # Position Preset

        row = layout.row()
        row.prop(context.scene, "interpolation", text="Interpolation")
        layout.operator("sequencer.add_ken_burns_effect", text="Add Ken Burns Effect")

def register():
    bpy.types.Scene.in_value = bpy.props.FloatProperty(name="Scale In", default=1.0, min=0.0)
    bpy.types.Scene.out_value = bpy.props.FloatProperty(name="Out", default=1.1, min=0.0)

    bpy.types.Scene.ken_burns_preset = bpy.props.EnumProperty(
        name="Target",
        description="Choose the zoom-in target position",
        items=[
            ('CENTER', "Center", "", 'ANCHOR_CENTER', 0),
            ('TOP_CENTER', "Center Top", "", 'ANCHOR_TOP', 1),
            ('BOTTOM_CENTER', "Center Bottom", "", 'ANCHOR_BOTTOM', 2),
            ('LEFT_CENTER', "Left Center", "", 'ANCHOR_LEFT', 3),
            ('RIGHT_CENTER', "Right Center", "", 'ANCHOR_RIGHT', 4),
            ('TOP_LEFT', "Top Left", "Zoom to top left corner", 'TRIA_TOPLEFT', 5),
            ('TOP_RIGHT', "Top Right", "Zoom to top right corner", 'TRIA_TOPRIGHT', 6),
            ('BOTTOM_LEFT', "Bottom Left", "Zoom to bottom left corner", 'TRIA_BOTTOMLEFT', 7),
            ('BOTTOM_RIGHT', "Bottom Right", "Zoom to bottom right corner", 'TRIA_BOTTOMRIGHT', 8),
        ],
        default='CENTER'
    )

    bpy.types.Scene.interpolation = bpy.props.EnumProperty(
        name="Interpolation Type",
        description="Choose the interpolation type for keyframes",
        items=[
            ('CONSTANT', "Constant", "No interpolation", 'IPO_CONSTANT', 0),
            ('LINEAR', "Linear", "Smooth linear transition", 'IPO_LINEAR', 1),
            ('BEZIER', "Bezier", "Smooth bezier curve", 'IPO_BEZIER', 2),
            ('SINE', "Sine", "Sine wave easing", 'IPO_SINE', 3),
            ('QUAD', "Quadratic", "Quadratic easing", 'IPO_QUAD', 4),
            ('CUBIC', "Cubic", "Cubic easing", 'IPO_CUBIC', 5),
            ('QUART', "Quartic", "Quartic easing", 'IPO_QUART', 6),
            ('QUINT', "Quintic", "Quintic easing", 'IPO_QUINT', 7),
            ('EXPO', "Exponential", "Exponential easing", 'IPO_EXPO', 8),
            ('CIRC', "Circular", "Circular easing", 'IPO_CIRC', 9),
            ('BACK', "Back", "Overshoot easing", 'IPO_BACK', 10),
            ('BOUNCE', "Bounce", "Bouncing easing", 'IPO_BOUNCE', 11),
            ('ELASTIC', "Elastic", "Elastic easing", 'IPO_ELASTIC', 12),
        ],
        default='LINEAR'
    )

    bpy.utils.register_class(AddKenBurnsEffect)
    bpy.utils.register_class(AddKenBurnsEffectPanel)

def unregister():
    bpy.utils.unregister_class(AddKenBurnsEffect)
    bpy.utils.unregister_class(AddKenBurnsEffectPanel)
    del bpy.types.Scene.in_value
    del bpy.types.Scene.out_value
    del bpy.types.Scene.ken_burns_preset
    del bpy.types.Scene.interpolation

if __name__ == "__main__":
    register()
