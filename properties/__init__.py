# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy

from .addon_sett import NODEBOOSTER_AddonPref
from .scene_sett import NODEBOOSTER_PR_scene
from .windows_sett import NODEBOOSTER_PR_Window


classes = (

    NODEBOOSTER_AddonPref,
    NODEBOOSTER_PR_scene,
    NODEBOOSTER_PR_Window,

    )


def load_properties():

    bpy.types.Scene.nodebooster = bpy.props.PointerProperty(type=NODEBOOSTER_PR_scene)
    bpy.types.WindowManager.nodebooster = bpy.props.PointerProperty(type=NODEBOOSTER_PR_Window)

    return None

def unload_properties():

    del bpy.types.Scene.nodebooster
    del bpy.types.WindowManager.nodebooster

    return None