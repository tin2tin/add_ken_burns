import bpy

# Add-on information
bl_info = {
    "name": "Ken Burns Effect",
    "author": "Tintwotin",
    "version": (1, 0),
    "blender": (3, 00, 0),
    "location": "Sequence Editor > Strip Tools",
    "description": "Add Ken Burns effect to selected image or movie strips",
    "warning": "",
    "wiki_url": "",
    "category": "Sequencer"
}

class AddKenBurnsEffect(bpy.types.Operator):
    """Add Ken Burns effect to selected image or movie strips"""
    bl_idname = "sequencer.add_ken_burns_effect"
    bl_label = "Add Ken Burns Effect"
    
    in_value: bpy.props.FloatProperty(name="In Value", default=1.0, min=0.0)
    out_value: bpy.props.FloatProperty(name="Out Value", default=1.1, min=0.0)
    
    @classmethod
    def poll(cls, context):
        return context.area.type == 'SEQUENCE_EDITOR'

    def execute(self, context):
        strips = [strip for strip in bpy.context.selected_editable_sequences if strip.type in ['IMAGE', 'MOVIE']]
        
        for strip in strips:
            # Insert keyframes for start and end offset
            strip.transform.scale_x = self.in_value
            strip.transform.scale_y = self.in_value
            strip.transform.keyframe_insert(data_path="scale_x", frame=strip.frame_final_start)
            strip.transform.keyframe_insert(data_path="scale_y", frame=strip.frame_final_start)
            
            strip.transform.scale_x = self.out_value
            strip.transform.scale_y = self.out_value
            strip.transform.keyframe_insert(data_path="scale_x", frame=strip.frame_final_end)
            strip.transform.keyframe_insert(data_path="scale_y", frame=strip.frame_final_end)

            # Set interpolation to "VECTOR" for smoother motion
            for window in context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if area.type == 'GRAPH_EDITOR':
                        with context.temp_override(window=window, area=area):
                            bpy.ops.graph.handle_type(type='VECTOR')
                        break

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
        layout.prop(context.scene, "in_value")
        layout.prop(context.scene, "out_value")
        layout.operator("sequencer.add_ken_burns_effect", text="Add Ken Burns Effect")

def register():
    bpy.types.Scene.in_value = bpy.props.FloatProperty(name="In Value", default=1.0, min=0.0)
    bpy.types.Scene.out_value = bpy.props.FloatProperty(name="Out Value", default=1.1, min=0.0)
    
    bpy.utils.register_class(AddKenBurnsEffect)
    bpy.utils.register_class(AddKenBurnsEffectPanel)

def unregister():
    bpy.utils.unregister_class(AddKenBurnsEffect)
    bpy.utils.unregister_class(AddKenBurnsEffectPanel)
    del bpy.types.Scene.in_value
    del bpy.types.Scene.out_value

if __name__ == "__main__":
    register()
