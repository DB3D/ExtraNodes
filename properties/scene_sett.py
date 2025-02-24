# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy

from ..operators.search import search_upd
from ..operators.palette import palette_active_upd


class NODEBOOSTER_PR_scene(bpy.types.PropertyGroup): 
    """sett_scene = bpy.context.scene.nodebooster"""

    frame_use_custom_color : bpy.props.BoolProperty(
        default=False,
        name="Frame Color")
    frame_color : bpy.props.FloatVectorProperty(
        default=(0,0,0),
        subtype="COLOR",
        name="Color",
        min=0,
        max=1,
        )
    frame_sync_color : bpy.props.BoolProperty(
        default=True,
        name="Sync Color",
        description="Synchronize with palette",
        )
    frame_label : bpy.props.StringProperty(
        default=" ",
        name="Label",
        )
    frame_label_size : bpy.props.IntProperty(
        default=16,min=0,
        name="Label Size",
        )

    palette_active : bpy.props.FloatVectorProperty(
        default=(0,0,0),
        subtype='COLOR',
        name="Color",
        min=0,
        max=1,
        update=palette_active_upd,
        )
    palette_old : bpy.props.FloatVectorProperty(
        default=(0,0,0),
        subtype='COLOR',
        name="Color",
        min=0,
        max=1,
        )
    palette_older : bpy.props.FloatVectorProperty(
        default=(0,0,0),
        subtype='COLOR',
        name="Color",
        min=0,
        max=1,
        )

    search_keywords : bpy.props.StringProperty(
        default=" ",
        name="Keywords",
        update=search_upd,
        )
    search_center : bpy.props.BoolProperty(
        default=True,
        name="Recenter View",
        update=search_upd,
        )
    search_labels : bpy.props.BoolProperty(
        default=True,
        name="Label",
        update=search_upd,
        )
    search_types : bpy.props.BoolProperty(
        default=True,
        name="Type",
        update=search_upd,
        )
    search_names : bpy.props.BoolProperty(
        default=False,
        name="Internal Name",
        update=search_upd,
        )
    search_socket_names : bpy.props.BoolProperty(
        default=False,
        name="Socket Names",
        update=search_upd,
        )
    search_socket_types : bpy.props.BoolProperty(
        default=False,
        name="Socket Types",
        update=search_upd,
        )
    search_input_only : bpy.props.BoolProperty(
        default=False,
        name="Input Nodes Only",
        update=search_upd,
        )
    search_frame_only : bpy.props.BoolProperty(
        default=False,
        name="Frame Only",
        update=search_upd,
        )
    search_found : bpy.props.IntProperty(
        default=0,
        )

    favorite_index  : bpy.props.IntProperty(
        default=0,
        description="prop used to take track the the current user favorite",
        )