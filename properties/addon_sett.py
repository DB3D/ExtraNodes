# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy 


class NODEBOOSTER_AddonPref(bpy.types.AddonPreferences):
    
    from .. import __package__ as base_package
    bl_idname = base_package
    
    debug : bpy.props.BoolProperty(
        name="Debug Mode",
        default=False,
        )
    debug_depsgraph : bpy.props.BoolProperty(
        name="Depsgraph Debug",
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
    #not exposed
    ui_word_wrap_max_char_factor : bpy.props.FloatProperty(
        default=1.0,
        soft_min=0.3,
        soft_max=3,
        description="ui 'word_wrap' layout funciton, max characters per lines",
        )
    ui_word_wrap_y : bpy.props.FloatProperty(
        default=0.8,
        soft_min=0.1,
        soft_max=3,
        description="ui 'word_wrap' layout funciton, max height of the lines",
        )
    
    def draw(self,context):
        
        layout = self.layout
        
        layout.prop(self,"debug",)
        layout.prop(self,"debug_depsgraph",)
        
        return None
