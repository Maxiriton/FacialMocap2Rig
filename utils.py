import bpy

def get_setuped_shape_key_item_by_name(context, name):
    """Retrieve shape key property item by name"""
    for item in context.scene.facialm2r_shape_keys:
        if item.name == name and item.is_setuped:
            return item
    return None

def get_shape_key_item_by_name(context, name):
    """Retrieve shape key property item by name"""
    for item in bpy.context.scene.facialm2r_shape_keys:
        if item.name == name:
            return item
    return None

def bone_has_moved(pose_bone):
    """Check if a bone has moved from its rest position"""
    #TODO: we assume the rest position is loc (0,0,0), rot (1,0,0,0), scale (1,1,1), which may not always be true, we should compare the value to the bone's rest pose
    loc_moved = pose_bone.location.length > 1e-6
    rot_moved = pose_bone.rotation_quaternion.w  - 1 > 1e-6 or any(abs(x) > 1e-6 for x in pose_bone.rotation_quaternion[1:])
    scale_moved = any(abs(s - 1) > 1e-6 for s in pose_bone.scale)
    return loc_moved or rot_moved or scale_moved