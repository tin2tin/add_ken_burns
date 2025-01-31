import bpy
import os
import bpy.utils.previews

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

# Global variable to store custom icons
custom_icons = None

import bpy

def _animated_properties_get(sequence):
    """Returns a list of animated properties for the given sequence."""
    animated_properties = []
    if hasattr(sequence, "volume"):
        animated_properties.append("volume")
    if hasattr(sequence, "blend_alpha"):
        animated_properties.append("blend_alpha")
    # Add other properties if needed (scale_x, scale_y, offset_x, etc.)
    return animated_properties

def remove_keyframes_from_active_strip(context):
    """Removes keyframes and curves from the active strip in the Sequence Editor."""
    scene = context.scene
    animation_data = scene.animation_data
    if animation_data is None:
        return {'CANCELLED'}

    action = animation_data.action
    if action is None:
        return {'CANCELLED'}

    fcurves = action.fcurves
    fcurve_map = {
        curve.data_path: curve
        for curve in fcurves
        if curve.data_path.startswith("sequence_editor.strips_all")
    }

    # Ensure the active strip is the one in focus
    active_strip = context.scene.sequence_editor.active_strip
    if not active_strip:
        return {'CANCELLED'}

    # Iterate over the animated properties of the active strip
    for animated_property in _animated_properties_get(active_strip):
        data_path = active_strip.path_from_id() + "." + animated_property
        curve = fcurve_map.get(data_path)
        
        if curve:
            fcurves.remove(curve)  # Remove the keyframe curve
        
        setattr(active_strip, animated_property, 1.0)  # Reset property value

    active_strip.invalidate_cache('COMPOSITE')  # Update the strip cache

    return {'FINISHED'}



class AddKenBurnsEffect(bpy.types.Operator):
    """Add Ken Burns effect to selected image or movie strips"""
    bl_idname = "sequencer.add_ken_burns_effect"
    bl_label = "Ken Burns Effect"

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

        strips = [strip for strip in bpy.context.selected_editable_sequences if strip.type in ['IMAGE', 'MOVIE', 'TEXT', 'SCENE']]

        for strip in strips:
            if not hasattr(strip, "transform"):
                self.report({'WARNING'}, f"Strip {strip.name} has no transform properties.")
                continue
            old_active = context.scene.sequence_editor.active_strip
            for window in bpy.context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if area.type in {'SEQUENCER','PREVIEW', 'SEQUENCER_PREVIEW'}:
                        graph_editor_found = True
                        with bpy.context.temp_override(window=window, area=area):
                            bpy.ops.sequencer.select_all(action='DESELECT')
            context.scene.sequence_editor.active_strip = strip
            elem = strip.strip_elem_from_frame(frame)  # Get image resolution at current frame

            if not elem:
                #self.report({'WARNING'}, f"Cannot get image resolution for {strip.name}. Falling back to render resolution.")
                
                # Fallback to render resolution if no image resolution is found
                img_width = bpy.context.scene.render.resolution_x
                img_height = bpy.context.scene.render.resolution_y
            else:
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
            
            remove_keyframes_from_active_strip(context)  

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

            graph_editor_found = False
            for window in bpy.context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if area.type == 'GRAPH_EDITOR':
                        graph_editor_found = True
                        with bpy.context.temp_override(window=window, area=area):
                            bpy.ops.graph.select_all(action='SELECT')
                            bpy.ops.graph.interpolation_type(type=interpolation)
            if not graph_editor_found:
                self.report({'INFO'}, "For interpolation to work, the Graph Editor must be visible in the workspace.")
            context.scene.sequence_editor.active_strip = old_active

        return {'FINISHED'}

def update_ken_burns_effect(self, context):
    bpy.ops.sequencer.add_ken_burns_effect()

class AddKenBurnsEffectPanel(bpy.types.Panel):
    """Panel for the Add Ken Burns Effect operator"""
    bl_label = "Ken Burns Effect"
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
    global custom_icons
    custom_icons = bpy.utils.previews.new()

    # Path to the folder containing the icons
    icons_dir = os.path.join(os.path.dirname(__file__), "Icons")

    # Load custom icons
    custom_icons.load("ZOOM_CENTER", os.path.join(icons_dir, "ZOOM_CENTER.svg"), 'IMAGE')
    custom_icons.load("ZOOM_TOP_CENTER", os.path.join(icons_dir, "ZOOM_TOP_CENTER.svg"), 'IMAGE')
    custom_icons.load("ZOOM_BOTTOM_CENTER", os.path.join(icons_dir, "ZOOM_BOTTOM_CENTER.svg"), 'IMAGE')

    custom_icons.load("ZOOM_TOP_LEFT", os.path.join(icons_dir, "ZOOM_TOP_LEFT.svg"), 'IMAGE')
    custom_icons.load("ZOOM_MIDDLE_LEFT", os.path.join(icons_dir, "ZOOM_MIDDLE_LEFT.svg"), 'IMAGE')
    custom_icons.load("ZOOM_BOTTOM_LEFT", os.path.join(icons_dir, "ZOOM_BOTTOM_LEFT.svg"), 'IMAGE')

    custom_icons.load("ZOOM_TOP_RIGHT", os.path.join(icons_dir, "ZOOM_TOP_RIGHT.svg"), 'IMAGE')
    custom_icons.load("ZOOM_MIDDLE_RIGHT", os.path.join(icons_dir, "ZOOM_MIDDLE_RIGHT.svg"), 'IMAGE')
    custom_icons.load("ZOOM_BOTTOM_RIGHT", os.path.join(icons_dir, "ZOOM_BOTTOM_RIGHT.svg"), 'IMAGE')

    bpy.types.Scene.in_value = bpy.props.FloatProperty(name="Scale Start", default=1.0, min=0.0, update=update_ken_burns_effect)
    bpy.types.Scene.out_value = bpy.props.FloatProperty(name="End", default=1.1, min=0.0, update=update_ken_burns_effect)

    bpy.types.Scene.ken_burns_preset = bpy.props.EnumProperty(
        name="Target",
        description="Choose the zoom-in target position",
        items=[
            ('CENTER', "Center", "", custom_icons["ZOOM_CENTER"].icon_id, 0),
            ('TOP_CENTER', "Center Top", "", custom_icons["ZOOM_TOP_CENTER"].icon_id, 1),
            ('BOTTOM_CENTER', "Center Bottom", "", custom_icons["ZOOM_BOTTOM_CENTER"].icon_id, 2),
            ('TOP_LEFT', "Top Left", "Zoom to top left corner", custom_icons["ZOOM_TOP_LEFT"].icon_id, 3),
            ('LEFT_CENTER', "Left Center", "", custom_icons["ZOOM_MIDDLE_LEFT"].icon_id, 4),
            ('BOTTOM_LEFT', "Bottom Left", "Zoom to bottom left corner", custom_icons["ZOOM_BOTTOM_LEFT"].icon_id, 5),
            ('TOP_RIGHT', "Right Top", "Zoom to top right corner", custom_icons["ZOOM_TOP_RIGHT"].icon_id, 6),
            ('RIGHT_CENTER', "Right Center", "", custom_icons["ZOOM_MIDDLE_RIGHT"].icon_id, 7),
            ('BOTTOM_RIGHT', "Right Bottom", "Zoom to bottom right corner", custom_icons["ZOOM_BOTTOM_RIGHT"].icon_id, 8),
        ],
        default='CENTER',
        update=update_ken_burns_effect
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
        default='LINEAR',
        update=update_ken_burns_effect
    )

    bpy.utils.register_class(AddKenBurnsEffect)
    bpy.utils.register_class(AddKenBurnsEffectPanel)

def unregister():
    global custom_icons
    bpy.utils.unregister_class(AddKenBurnsEffect)
    bpy.utils.unregister_class(AddKenBurnsEffectPanel)
    del bpy.types.Scene.in_value
    del bpy.types.Scene.out_value
    del bpy.types.Scene.ken_burns_preset
    del bpy.types.Scene.interpolation

    # Release custom icons
    if custom_icons is not None:
        bpy.utils.previews.remove(custom_icons)
        custom_icons = None

if __name__ == "__main__":
    register()
