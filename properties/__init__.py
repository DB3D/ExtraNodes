# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy

from .addon_sett import NODEBOOSTER_AddonPref
from .scene_sett import NODEBOOSTER_PR_scene

classes = (

    NODEBOOSTER_AddonPref,
    NODEBOOSTER_PR_scene,

    )


def load_properties():

    bpy.types.Scene.nodebooster = bpy.props.PointerProperty(type=NODEBOOSTER_PR_scene)

    return None

def unload_properties():

    del bpy.types.Scene.nodebooster 

    return None