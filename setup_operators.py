import bpy
import json
import csv
import re
import mathutils
from pathlib import Path
from bpy.types import Operator
from bpy.props import StringProperty, IntProperty, FloatProperty
from .utils import bone_has_moved, get_shape_key_item_by_name


class FACIALM2R_OT_LoadJSON(Operator):
    """Load JSON file and populate shape key mappings"""
    bl_idname = "facialm2r.load_json"
    bl_label = "Load JSON File"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(
        name="File Path",
        description="Path to the JSON file",
        subtype='FILE_PATH'
    )

    filter_glob: StringProperty(default="*.json", options={'HIDDEN'})

    def execute(self, context): # type: ignore
        if not Path(self.filepath).exists():
            self.report({'ERROR'}, "File not found")
            return {'CANCELLED'}

        scene = context.scene
        scene.facialm2r_shape_keys.clear() # type: ignore

        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
                
                for entry in data:
                    item = scene.facialm2r_shape_keys.add() # type: ignore
                    item.name = entry['name']
                    item.bone_transforms = json.dumps(entry['bone_transforms'])
                    item.is_setuped = entry['is_setuped']

            self.report({'INFO'}, f"Loaded {len(scene.facialm2r_shape_keys)} shape keys from JSON") # type: ignore
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

    def invoke(self, context, event): # type: ignore
        context.window_manager.fileselect_add(self) # type: ignore
        return {'RUNNING_MODAL'}

class FACIALM2R_OT_LoadCSV(Operator):
    """Load CSV file and extract shape key names"""
    bl_idname = "facialm2r.load_csv"
    bl_label = "Load CSV File"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(
        name="File Path",
        description="Path to the CSV file",
        subtype='FILE_PATH'
    )

    filter_glob: StringProperty(default="*.csv", options={'HIDDEN'})

    def execute(self, context): # type: ignore
        if not Path(self.filepath).exists():
            self.report({'ERROR'}, "File not found")
            return {'CANCELLED'}

        scene = context.scene
        scene.facialm2r_shape_keys.clear() # type: ignore

        try:
            with open(self.filepath, 'r') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                
                # Skip non-shape-key columns
                skip_cols = {'Timecode', 'BlendShapeCount'} #TODO move this list to addon preferences, to make it user-configurable.
                
                for header in headers: # type: ignore
                    if header not in skip_cols: 
                        item = scene.facialm2r_shape_keys.add() # type: ignore
                        item.name = header

            self.report({'INFO'}, f"Loaded {len(scene.facialm2r_shape_keys)} shape keys") # type: ignore
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

    def invoke(self, context, event): # type: ignore
        context.window_manager.fileselect_add(self) # type: ignore
        return {'RUNNING_MODAL'}

class FACIALM2R_OT_SetupMultiplier(Operator):
    """Set up multiplier for a shape key"""
    bl_idname = "facialm2r.setup_multiplier"
    bl_label = "Setup Multiplier"
    bl_options = {'REGISTER', 'UNDO'}

    shape_key_name: StringProperty(name="Shape Key Name")
    list_index: IntProperty(name="List Index", default=0)
    multiplier: FloatProperty(name="Multiplier", default=1.0, min=0.0, max=10.0)

    def draw(self, context):
        layout = self.layout
        layout.label(text=f"Shape Key: {self.shape_key_name}") # type: ignore
        layout.prop(self, "multiplier") # type: ignore

    def invoke(self, context, event):
        scene = context.scene
        scene.facialm2r_shape_keys_index = self.list_index # type: ignore
        # prefill from active list item if available
        try:
            item = get_shape_key_item_by_name(context, self.shape_key_name)
            self.multiplier = item.multiplier # type: ignore
        except Exception:
            pass
        return context.window_manager.invoke_props_dialog(self) # type: ignore

    def execute(self, context): # type: ignore
        scene = context.scene
        active_shape_key = scene.facialm2r_shape_keys[scene.facialm2r_shape_keys_index] # type: ignore
        active_shape_key.multiplier = self.multiplier
        self.report({'INFO'}, f"Set multiplier for {self.shape_key_name} to {self.multiplier}")
        return {'FINISHED'}

class FACIALM2R_OT_SymmetrizeShapeKey(Operator):
    """Symmetrize recorded transforms for a shape key (LEFT <-> RIGHT)"""
    bl_idname = "facialm2r.symmetrize_shape_key"
    bl_label = "Symmetrize Shape Key"
    bl_options = {'REGISTER', 'UNDO'}

    shape_key_name: StringProperty(name="Shape Key Name")

    def execute(self, context): # type: ignore
        scene = context.scene
        armature_obj = scene.facialm2r_armature_obj # type: ignore
        if not armature_obj or armature_obj.type != 'ARMATURE':
            self.report({'ERROR'}, "No valid armature selected")
            return {'CANCELLED'}
 
        active_shape_key = scene.facialm2r_shape_keys[scene.facialm2r_shape_keys_index] # type: ignore

        name_low = active_shape_key.name.lower()
        if name_low.endswith('left'):
            base = active_shape_key.name[:-4]
            target_name = base + 'Right'
        elif name_low.endswith('right'):
            base = active_shape_key.name[:-5]
            target_name = base + 'Left'
        else:
            self.report({'ERROR'}, "Shape key name must end with LEFT or RIGHT")
            return {'CANCELLED'}

        # find or create target item
        target_shape_key = None
        for it in scene.facialm2r_shape_keys: # type: ignore
            if it.name == target_name:
                target_shape_key = it
                break
        if not target_shape_key:
            self.report({'ERROR'}, f"Target shape key '{target_name}' not found")
            return {'CANCELLED'}

        src_transforms = json.loads(active_shape_key.bone_transforms)
        new_transforms = {}

        # Reflection matrix across central plane X=0 (invert X)
        M = mathutils.Matrix((( -1.0, 0.0, 0.0),
                                (  0.0, 1.0, 0.0),
                                (  0.0, 0.0, 1.0)))

        for bname, t in src_transforms.items():
            # map bone name: mirror .L <-> .R when present, otherwise keep same
            def _flip(m):
                return '.R' if m.group(1) == 'L' else '.L'
            # flip any ".L" or ".R" that is followed by a dot (middle) or end of string
            mapped = re.sub(r'\.([LR])(?=\.|$)', _flip, bname)

            # only apply if mapped bone exists in rig; otherwise skip
            if mapped not in armature_obj.pose.bones:
                continue

            # mirror location (invert X)
            loc = t.get('location', [0.0, 0.0, 0.0])
            mirrored_loc = [-loc[0], loc[1], loc[2]]

            # mirror rotation_quaternion by conjugating rotation matrix with M
            rot = t.get('rotation_quaternion')
            if rot:
                q = mathutils.Quaternion(rot)
                R = q.to_matrix()
                Rm = M @ R @ M
                q_m = Rm.to_quaternion() # type: ignore
                mirrored_rot = [q_m.w, q_m.x, q_m.y, q_m.z]
            else:
                mirrored_rot = t.get('rotation_quaternion', [1.0, 0.0, 0.0, 0.0])

            # copy scale (do not invert scale by default)
            scale = t.get('scale', [1.0, 1.0, 1.0])

            new_transforms[mapped] = {
                'location': mirrored_loc,
                'rotation_quaternion': mirrored_rot,
                'scale': scale
            }

        # save to target item
        target_shape_key.bone_transforms = json.dumps(new_transforms)
        target_shape_key.is_setuped = True

        self.report({'INFO'}, f"Symmetrized '{active_shape_key.name}' -> '{target_shape_key.name}' ({len(new_transforms)} bones)")
        return {'FINISHED'}

class FACIALM2R_OT_RecordPose(Operator):
    """Set armature as active object and enter pose mode"""
    bl_idname = "facialm2r.setup_pose_mode"
    bl_label = "Setup Pose Mode"
    bl_options = {'REGISTER', 'UNDO'}

    shape_key_name: StringProperty(name="Shape Key Name")
    list_index: IntProperty(name="List Index", default=0)

    def execute(self, context): # type: ignore
        scene = context.scene
        armature_obj = scene.facialm2r_armature_obj # type: ignore
        scene.facialm2r_shape_keys_index = self.list_index # type: ignore

        if not armature_obj:
            self.report({'ERROR'}, "No armature selected")
            return {'CANCELLED'}

        if armature_obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Selected object is not an armature")
            return {'CANCELLED'}

        # Set as active object
        context.view_layer.objects.active = armature_obj # type: ignore
        armature_obj.select_set(True)

        # Enter pose mode
        bpy.ops.object.mode_set(mode='POSE')

        scene.facialm2r_is_recording = True # type: ignore
        scene.facialm2r_current_shape_key = self.shape_key_name # type: ignore
        self.report({'INFO'}, f"Ready to record pose for {self.shape_key_name}")
        return {'FINISHED'}

class FACIALM2R_OT_FinishRecord(Operator):
    """Store bone transforms for the current shape key"""
    bl_idname = "facialm2r.finish_record"
    bl_label = "Finish Recording"
    bl_options = {'REGISTER', 'UNDO'}

    shape_key_name: StringProperty(name="Shape Key Name")

    def execute(self, context): # type: ignore
        scene = context.scene
        armature_obj = scene.facialm2r_armature_obj # type: ignore

        if not armature_obj or armature_obj.type != 'ARMATURE':
            self.report({'ERROR'}, "No valid armature selected")
            return {'CANCELLED'}

        # Collect bone transforms
        bone_transforms = {}
        for pose_bone in armature_obj.pose.bones:
            if bone_has_moved(pose_bone):
                bone_transforms[pose_bone.name] = {
                    'location': list(pose_bone.location),
                    'rotation_quaternion': list(pose_bone.rotation_quaternion),
                    'scale': list(pose_bone.scale)
                }
            else:
                print(f"Skipping bone {pose_bone.name} with default transforms")

        # Find and update the shape key mapping
        for item in scene.facialm2r_shape_keys: # type: ignore
            if item.name == self.shape_key_name:
                item.bone_transforms = json.dumps(bone_transforms)
                item.is_setuped = True
                break

        scene.facialm2r_is_recording = False # type: ignore
        scene.facialm2r_current_shape_key = "" # type: ignore
        self.report({'INFO'}, f"Saved transforms for {self.shape_key_name}")
        return {'FINISHED'}
    
class FACIALM2R_OT_ExportJSON(Operator):
    """Export shape key mappings to JSON file"""
    bl_idname = "facialm2r.export_json"
    bl_label = "Export to JSON"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(
        name="File Path",
        description="Path to save the JSON file",
        subtype='FILE_PATH'
    )

    filter_glob: StringProperty(default="*.json", options={'HIDDEN'})

    def execute(self, context): # type: ignore
        scene = context.scene
        data = []

        for item in scene.facialm2r_shape_keys: # type: ignore
            data.append({
                'name': item.name,
                'bone_transforms': json.loads(item.bone_transforms),
                'is_setuped': item.is_setuped,
                'frame_values': json.loads(item.frame_values)
            })

        try:
            with open(self.filepath, 'w') as f:
                json.dump(data, f, indent=2)
            self.report({'INFO'}, f"Exported {len(data)} shape keys")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

    def invoke(self, context, event): # type: ignore
        context.window_manager.fileselect_add(self) # type: ignore
        return {'RUNNING_MODAL'}

#TODO add a checkup operator to validate that all shape keys have recorded poses.

def on_shape_key_index_changed(self, context):
    """Callback when shape key index changes"""
    current_item = context.scene.facialm2r_shape_keys[context.scene.facialm2r_shape_keys_index]
    armature_obj = context.scene.facialm2r_armature_obj
    if not armature_obj or armature_obj.type != 'ARMATURE':
        return
    # Reset to rest pose
    for pose_bone in armature_obj.pose.bones:
        pose_bone.location = (0, 0, 0)
        pose_bone.rotation_quaternion = (1,0, 0, 0)
        pose_bone.scale = (1, 1, 1)
    if current_item.is_setuped:
        # Apply stored transforms
        bone_transforms = json.loads(current_item.bone_transforms)
        for name, transforms in bone_transforms.items():
            pose_bone = armature_obj.pose.bones.get(name)
            if pose_bone:
                pose_bone.location = transforms['location']
                pose_bone.rotation_quaternion = transforms['rotation_quaternion']
                pose_bone.scale = transforms['scale']
    
### Registration
classes = (
    FACIALM2R_OT_LoadJSON,
    FACIALM2R_OT_LoadCSV,
    FACIALM2R_OT_RecordPose,
    FACIALM2R_OT_FinishRecord,
    FACIALM2R_OT_ExportJSON,
    FACIALM2R_OT_SymmetrizeShapeKey,
    FACIALM2R_OT_SetupMultiplier
)

def register():
    for cl in classes:  
        bpy.utils.register_class(cl)

def unregister():
    for cl in reversed(classes):
        bpy.utils.unregister_class(cl)