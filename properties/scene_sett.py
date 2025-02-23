# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy


class NODEBOOSTER_PR_scene(bpy.types.PropertyGroup): 
    """sett_scene = bpy.context.scene.nodebooster"""

    #custom properties for the frame node operator
    frame_use_custom_color: bpy.props.BoolProperty(
        default=False,
        name="Frame Color")
    frame_color: bpy.props.FloatVectorProperty(
        default=(0,0,0),
        subtype="COLOR",
        name="Color",
        )
    frame_sync_color: bpy.props.BoolProperty(
        default=True,
        name="Sync Color",
        description="Synchronize with palette",
        )
    frame_label: bpy.props.StringProperty(
        default=" ",
        name="Label",
        )
    frame_label_size: bpy.props.IntProperty(
        default=16,min=0,
        name="Label Size",
        )

    # palette_prop: bpy.props.FloatVectorProperty(
    #     default=(0,0,0),
    #     subtype='COLOR',
    #     name="Color",
    #     update=palette_prop_upd,
    #     )

    # search_keywords: bpy.props.StringProperty(
    #     default=" ",
    #     name="Keywords",
    #     update=search_upd,
    #     )
    # search_center: bpy.props.BoolProperty(
    #     default=True,
    #     name="Recenter View",
    #     update=search_upd,
    #     )
    # search_labels: bpy.props.BoolProperty(
    #     default=True,
    #     name="Label",
    #     update=search_upd,
    #     )
    # search_types: bpy.props.BoolProperty(
    #     default=True,
    #     name="Type",
    #     update=search_upd,
    #     )
    # search_names: bpy.props.BoolProperty(
    #     default=False,
    #     name="Internal Name",
    #     update=search_upd,
    #     )
    # search_socket_names: bpy.props.BoolProperty(
    #     default=False,
    #     name="Socket Names",
    #     update=search_upd,
    #     )
    # search_socket_types: bpy.props.BoolProperty(
    #     default=False,
    #     name="Socket Types",
    #     update=search_upd,
    #     )
    # search_input_only: bpy.props.BoolProperty(
    #     default=False,
    #     name="Input Only",
    #     update=search_upd,
    #     )
    # search_frame_only: bpy.props.BoolProperty(
    #     default=False,
    #     name="Frame Only",
    #     update=search_upd,
    #     )
    
    # search_found: bpy.props.IntProperty(
    #     default=0,
    #     )

    favorite_index : bpy.props.IntProperty(
        default=0,
        description="prop used to take track the the current user favorite",
        )