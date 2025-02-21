# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy 


class EXTRANODES_AddonPref(bpy.types.AddonPreferences):
    
    from . import __package__ as base_package
    bl_idname = base_package
    
    debug : bpy.props.BoolProperty(
        name="Debug Mode",
        default=False,
        )
    pynode_depseval : bpy.props.BoolProperty(
        name="Auto Evaluate",
        description="Automatically evaluate these nodes python expression on every depsgraph update signal",
        default=True,
        )
    pynode_convenience_exec1 : bpy.props.StringProperty(
        default="from mathutils import * ; from math import *",
        description="this text is informal and read only",
        )
    pynode_convenience_exec2 : bpy.props.StringProperty(
        default="D = bpy.data ; C = context = bpy.context ; scene = context.scene",
        description="this text is informal and read only",
        )
    pynode_convenience_exec3 : bpy.props.StringProperty(
        default="",
        )

    def draw(self,context):
        
        layout = self.layout

        layout.box().label(text="Python Api Node:")
        
        layout.prop(self,"pynode_depseval",)

        col = layout.column(align=True)
        col.label(text="Convenience Variables")
        col.separator()
        
        row = col.row(align=True)
        row.enabled = False
        row.prop(self,"pynode_convenience_exec1",text="",)
        
        row = col.row(align=True)
        row.enabled = False
        row.prop(self,"pynode_convenience_exec2",text="",)
        
        row = col.row(align=True)
        row.active = False
        row.prop(self,"pynode_convenience_exec3",text="",)

        layout.box().label(text="Developers:")
        
        layout.prop(self,"debug",)
        
        return None


classes = (
    
    EXTRANODES_AddonPref,
    
    )
