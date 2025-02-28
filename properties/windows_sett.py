# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy


class NODEBOOSTER_PR_Window(bpy.types.PropertyGroup):
    """sett_win = bpy.context.window_manager.nodebooster"""
    #Properties in there will always be temporary and reset to their default values on each blender startup

    allow_auto_exec : bpy.props.BoolProperty(
        default=False,
        name="Allow Automatic Executions",
        description="Automatically running a foreign python script is dangerous. Do you know the content of this .blend file? If not, do you trust the authors? When this button is enabled python expressions or scripts from the nodebooster plugin will never execute automatically, you will need to engage with the node properties to trigger an execution",
        )