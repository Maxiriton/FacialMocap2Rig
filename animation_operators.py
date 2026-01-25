import bpy
import csv
import re
import json
from math import floor
from bpy.types import Operator
from mathutils import Vector, Quaternion
from .utils import get_setuped_shape_key_item_by_name


class FACIALM2R_OT_apply_animation(Operator):
    bl_idname = "facialm2r.apply_animation"
    bl_label = "Apply Facial Animation from CSV"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def parse_timecode(self, timecode_re, tc, fps):
        m = timecode_re.match(tc.strip())
        if not m:
            return None
        h, mm, s, f = m.groups()
        h = int(h); mm = int(mm); s = int(s)
        frames = float(f)
        total_seconds = h*3600 + mm*60 + s + (frames / fps)
        frame = int(round(total_seconds * fps))
        return frame

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        scene = context.scene

        armature = context.scene.facialm2r_armature_obj
        if armature is None:
            self.report({'ERROR'}, "No armature in the scene")
            return {'CANCELLED'}

        fps = scene.render.fps / getattr(scene.render, "fps_base", 1.0)
        timecode_re = re.compile(r"(\d+):(\d+):(\d+):([\d\.]+)")

        # read csv
        try:
            with open(self.filepath, newline='', encoding='utf-8') as fh:
                reader = csv.reader(fh)
                header = next(reader)
                # build column index -> name
                cols = [c.strip() for c in header]
                # find timecode column index (should be 0)
                tc_idx = cols.index("Timecode") if "Timecode" in cols else 0

                moved_bones = []

                for row in reader:
                    if not row or len(row) < 1:
                        continue
                    timecode = row[tc_idx]
                    frame = self.parse_timecode(timecode_re, timecode, fps)
                    if frame is None:
                        continue

                    #we need to reset all the bones positions before applying new ones
                    for bone_name in moved_bones:
                        pose_bone = armature.pose.bones.get(bone_name)
                        if pose_bone:
                            pose_bone.location = Vector((0,0,0))
                            pose_bone.rotation_quaternion = Quaternion((1,0,0,0))
                            pose_bone.scale = Vector((1,1,1))

                    # for each column that may be a shapekey name
                    for i, colname in enumerate(cols):
                        if colname in ("Timecode", "BlendShapeCount"):
                            continue

                        item = get_setuped_shape_key_item_by_name(context, colname)
                        if item is None:
                            continue

                        try:
                            val = float(row[i]) * item.multiplier
                            frame_values = json.loads(item.frame_values)
                            frame_values[str(frame)] = val
                            item.frame_values = json.dumps(frame_values)
                        except Exception:
                            continue
                        if val == 0.0:
                            continue

                        bone_transforms = json.loads(item.bone_transforms)
                        for name, transforms in bone_transforms.items():
                            pose_bone = armature.pose.bones.get(name)
                            if pose_bone:
                                pose_bone.location += Vector((0,0,0)).lerp(Vector(transforms['location']), val)
                                pose_bone.rotation_quaternion = pose_bone.rotation_quaternion.slerp(Quaternion(transforms['rotation_quaternion']), min(val, 1.0))
                                pose_bone.scale = pose_bone.scale.lerp(Vector(transforms['scale']), val)
                    
                            # insert keyframes
                            pose_bone.keyframe_insert(data_path="location", frame=frame)
                            pose_bone.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                            pose_bone.keyframe_insert(data_path="scale", frame=frame)

                            if name not in moved_bones:
                                moved_bones.append(name)

                    print(f"Applied motion to bones at {frame}")
                        

                                
        except Exception as e:
            self.report({'ERROR'}, f"Failed to read CSV: {e}")
            return {'CANCELLED'}

        return {'FINISHED'}


### Registration
classes = (
    FACIALM2R_OT_apply_animation,
)

def register():
    for cl in classes:  
        bpy.utils.register_class(cl)

def unregister():
    for cl in reversed(classes):
        bpy.utils.unregister_class(cl)