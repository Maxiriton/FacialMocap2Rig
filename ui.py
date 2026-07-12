#type: ignore
import bpy
from bpy.types import Panel, UIList

class FACIALM2R_PT_SetupPanel(Panel):
    """Setup UI panel in 3D view"""
    bl_label = "Facial Mocap 2 Rigify Setup"
    bl_idname = "FACIALM2R_PT_setup_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "FacialMocap2Rigify"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        layout.label(text="Shape Key Setup")
        row = layout.row()
        row.split(factor=0.5)
        row.operator("facialm2r.load_json", text="Load Existing setup from JSON File")
        row.operator("facialm2r.load_csv", text="Create new setup from CSV File")

        layout.prop_search(
            scene, "facialm2r_armature_obj",
            scene, "objects",
            text="Armature",
        )

        layout.label(text="Shape Keys")
        layout.template_list(
            "FACIALM2R_UL_ShapeKeys", "shape_keys",
            scene, "facialm2r_shape_keys",
            scene, "facialm2r_shape_keys_index"
        )

        layout.label(text="Symmetrize Shape Keys")
        row = layout.row()
        row.split(factor=0.5)
        row.operator("facialm2r.symmetrize_shape_key", text="Symmetrize Shape Keys")

        layout.operator("facialm2r.export_json", text="Export Current Setup to JSON File")


class FACIALM2R_PT_AnimationPanel(Panel):
    """Animation UI panel in 3D view"""
    bl_label = "Facial Mocap 2 Rigify Animation"
    bl_idname = "FACIALM2R_PT_animation_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "FacialMocap2Rigify"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop_search(
            scene, "facialm2r_armature_obj",
            scene, "objects",
            text="Armature",
        )
        
        layout.label(text="Record animation from CSV")
        layout.operator("facialm2r.apply_animation", text="Apply Animation from CSV File")

        layout.label(text="Shape Keys")
        layout.template_list(
            "FACIALM2R_UL_ShapeKeysAnimation", "shape_keys",
            scene, "facialm2r_shape_keys",
            scene, "facialm2r_shape_keys_index"
        )


class FACIALM2R_UL_ShapeKeys(UIList):
    """UI List for shape keys setuping and recording"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index): # type: ignore
        row = layout.row(align=True)
        if context.scene.facialm2r_is_recording and context.scene.facialm2r_current_shape_key != item.name:
            row.enabled = False

        split = row.split(factor=0.5)
        c = split.column()
        if item.is_setuped:
            c.label(text=item.name, icon='CHECKMARK')
        else:
            c.label(text=item.name, icon='DECORATE')
        
        split = split.split(factor=0.7)
        c = split.column()
        if context.scene.facialm2r_is_recording and context.scene.facialm2r_current_shape_key == item.name:
            c.operator(
            "facialm2r.finish_record",
            text="Finish Recording",
            icon='REC'
            ).shape_key_name = item.name
        else:
            op = c.operator(
            "facialm2r.setup_pose_mode",
            text="Record Pose" if not item.is_setuped else "Update Record Pose",
            icon='ARMATURE_DATA'
            )
            op.list_index = index
            op.shape_key_name = item.name
    
        c = split.column()  
        text = "" if item.multiplier == 1.0 else f"{item.multiplier:.1f}"
        icon = 'PRESET_NEW' if item.multiplier == 1.0 else 'X'
        op = c.operator(
            "facialm2r.setup_multiplier",
            text=text,
            icon=icon
        )
        op.shape_key_name = item.name
        op.list_index = index


class FACIALM2R_UL_ShapeKeysAnimation(UIList):
    """UI List for shape keys animation playback"""

    slider: bpy.props.FloatProperty(name = "Toto", default = 0.0, min = 0.0, max = 1.0)

    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index): # type: ignore
        row = layout.row(align=True)
        if not item.is_setuped:
            row.enabled = False
        split = row.split(factor=0.5)
        icon = 'CHECKMARK' if item.is_setuped else 'DECORATE'
        split.label(text=item.name, icon=icon)

        split = split.split(factor=0.8)
        c = split.column()
        c.prop(item, "current_value", text="", slider=True)
        c = split.column()
        text = "" if item.multiplier == 1.0 else f"x {item.multiplier:.1f}"
        c.label(text=text)

### Registration
classes = (
    FACIALM2R_PT_SetupPanel,
    FACIALM2R_PT_AnimationPanel,
    FACIALM2R_UL_ShapeKeys,
    FACIALM2R_UL_ShapeKeysAnimation
)

def register():
    for cl in classes:  
        bpy.utils.register_class(cl)

def unregister():
    for cl in reversed(classes):
        bpy.utils.unregister_class(cl)