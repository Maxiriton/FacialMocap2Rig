# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

#type: ignore

import bpy
import json
from bpy.props import StringProperty, CollectionProperty
from bpy.types import PropertyGroup


from . import setup_operators
from . import animation_operators
from . import ui


bl_info = {
    "name": "FacialMocap2Rigify",
    "author": "Henri Hebeisen",
    "description": "",
    "blender": (5, 0, 1),
    "version": (0, 0, 1),
    "location": "",
    "warning": "",
    "category": "Generic",
}

class ShapeKeyMapping(PropertyGroup):
    """Property group to store shape key mapping data"""
    name: StringProperty(name="Shape Key Name")
    bone_transforms: StringProperty(name="Bone Transforms", default="{}")
    is_setuped: bpy.props.BoolProperty(name="Is Recorded", default=False)
    frame_values: StringProperty(name="Frame Values", default="{}")
    current_value: bpy.props.FloatProperty(name="Current Value", default=0.0, min=0.0, max=1.0)
    multiplier: bpy.props.FloatProperty(name="Multiplier", default=1.0, min=0.0, max=10.0)

def register_shape_key_properties():
    """Register scene properties"""
    bpy.types.Scene.facialm2r_shape_keys = CollectionProperty(
        type=ShapeKeyMapping,
        name="Shape Keys"
    )
    bpy.types.Scene.facialm2r_shape_keys_index = bpy.props.IntProperty(
        name="Shape Keys Index",
        default=0,
        update=setup_operators.on_shape_key_index_changed
    )
    bpy.types.Scene.facialm2r_armature_obj = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Armature",
        description="Rigify armature to record poses"
    )
    bpy.types.Scene.facialm2r_is_recording = bpy.props.BoolProperty(
        name="Is Recording",
        default=False
    )
    bpy.types.Scene.facialm2r_current_shape_key = bpy.props.StringProperty(
        name="Current Shape Key",
        default=""
    )

def update_shape_keys_values(scene):
    """Update shape keys values based on current frame"""
    frame = scene.frame_current
    for item in scene.facialm2r_shape_keys:
        if item.is_setuped:
            frame_values = json.loads(item.frame_values)
            value = frame_values.get(str(frame), 0.0)
            item.current_value = value


def unregister_shape_key_properties():
    """Unregister scene properties"""
    del bpy.types.Scene.facialm2r_current_shape_key
    del bpy.types.Scene.facialm2r_is_recording
    del bpy.types.Scene.facialm2r_shape_keys
    del bpy.types.Scene.facialm2r_shape_keys_index
    del bpy.types.Scene.facialm2r_armature_obj

classes = (
    ShapeKeyMapping,
)

addon_modules = (
    setup_operators,
    animation_operators,
    ui,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    for mod in addon_modules:
        mod.register()
    register_shape_key_properties()
    bpy.app.handlers.frame_change_post.append(update_shape_keys_values)

def unregister():
    # bpy.app.handlers.frame_change_pre.clear()
    bpy.app.handlers.frame_change_post.remove(update_shape_keys_values)
    unregister_shape_key_properties()
    for mod in reversed(addon_modules):
        mod.unregister()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()