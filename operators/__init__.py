# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy

from .drawroute import NODEBOOSTER_OT_draw_route
from .bakemath import NODEBOOSTER_OT_bake_mathexpression
from .purge import NODEBOOSTER_OT_node_purge_unused
from .favorites import NODEBOOSTER_OT_favorite_add, NODEBOOSTER_OT_favorite_loop
from .depselect import NODEBOOSTER_OT_dependency_select
from .drawframes import NODEBOOSTER_OT_draw_frame
from .chamfer import NODEBOOSTER_OT_chamfer
from .palette import NODEBOOSTER_OT_setcolor, NODEBOOSTER_OT_palette_reset_color, NODEBOOSTER_OT_initalize_palette
from .codetemplates import NODEBOOSTER_OT_text_templates

classes = (

    NODEBOOSTER_OT_draw_route,
    NODEBOOSTER_OT_bake_mathexpression,
    NODEBOOSTER_OT_node_purge_unused,
    NODEBOOSTER_OT_favorite_add,
    NODEBOOSTER_OT_favorite_loop,
    NODEBOOSTER_OT_dependency_select,
    NODEBOOSTER_OT_draw_frame,
    NODEBOOSTER_OT_chamfer,
    NODEBOOSTER_OT_setcolor,
    NODEBOOSTER_OT_palette_reset_color,
    NODEBOOSTER_OT_initalize_palette,
    NODEBOOSTER_OT_text_templates,

    )


ADDON_KEYMAPS = []

KMI_DEFS = (

    # Operator.bl_idname,                         Key,         Action,  Ctrl,  Shift, Alt,   props(name,value)                         Name,                      Icon,                  Enable
    ( NODEBOOSTER_OT_draw_route.bl_idname,        "E",         "PRESS", False, False, False, (),                                       "Draw Route",              "TRACKING",            True, ),
    ( NODEBOOSTER_OT_favorite_add.bl_idname,      "Y",         "PRESS", True,  False, False, (),                                       "Add Favorite",            "SOLO_OFF",            True, ),
    ( NODEBOOSTER_OT_favorite_loop.bl_idname,     "Y",         "PRESS", False, False, False, (),                                       "Loop Favorites",          "SOLO_OFF",            True, ),
    ( NODEBOOSTER_OT_draw_frame.bl_idname,        "J",         "PRESS", False, False, False, (),                                       "Draw Frame",              "ALIGN_TOP",           True, ),
    ( NODEBOOSTER_OT_chamfer.bl_idname,           "B",         "PRESS", True,  False, False, (),                                       "Reroute Chamfer",         "MOD_BEVEL",           True, ),
    ( NODEBOOSTER_OT_dependency_select.bl_idname, "LEFTMOUSE", "PRESS", True,  False, False, (("mode","downstream"),("repsel",True )), "Select Downstream",       "RESTRICT_SELECT_OFF", True, ),
    ( NODEBOOSTER_OT_dependency_select.bl_idname, "LEFTMOUSE", "PRESS", True,  True,  False, (("mode","downstream"),("repsel",False)), "Select Downstream (Add)", "RESTRICT_SELECT_OFF", True, ),
    ( NODEBOOSTER_OT_dependency_select.bl_idname, "LEFTMOUSE", "PRESS", True,  False, True,  (("mode","upstream"),  ("repsel",True )), "Select Upsteam",          "RESTRICT_SELECT_OFF", True, ),
    ( NODEBOOSTER_OT_dependency_select.bl_idname, "LEFTMOUSE", "PRESS", True,  True,  True,  (("mode","upstream"),  ("repsel",False)), "Select Upsteam (Add)",    "RESTRICT_SELECT_OFF", True, ),

    )


def load_operators_keymaps():

    #TODO, ideally we need to save these keys on addonprefs somehow, it will reset per blender sessions.
    
    ADDON_KEYMAPS.clear()

    kc = bpy.context.window_manager.keyconfigs.addon
    if (not kc):
        return None

    km = kc.keymaps.new(name="Node Editor", space_type='NODE_EDITOR',)
    for (identifier, key, action, ctrl, shift, alt, props, name, icon, enable) in KMI_DEFS:
        kmi = km.keymap_items.new(identifier, key, action, ctrl=ctrl, shift=shift, alt=alt,)
        kmi.active = enable
        if (props):
            for prop, value in props:
                setattr(kmi.properties, prop, value)
        ADDON_KEYMAPS.append((km, kmi, name, icon))

    return None
            
def unload_operators_keymaps():

    for km, kmi, _, _ in ADDON_KEYMAPS:
        km.keymap_items.remove(kmi)
    ADDON_KEYMAPS.clear()

    return None
