# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy

from .bakemath import NODEBOOSTER_OT_bake_mathexpression
from .purge import NOODLER_OT_node_purge_unused
from .favorites import NODEBOOSTER_OT_favorite_add, NODEBOOSTER_OT_favorite_loop
from .depselect import NODEBOOSTER_OT_dependency_select

classes = (

    NODEBOOSTER_OT_bake_mathexpression,
    NOODLER_OT_node_purge_unused,
    NODEBOOSTER_OT_favorite_add,
    NODEBOOSTER_OT_favorite_loop,
    NODEBOOSTER_OT_dependency_select,

    )



KMI_DEFS = (

    # Operator.bl_idname,                         Key,         Action,  Ctrl,  Shift, Alt,   props(name,value)                         Name,                      Icon,        Enable
    ( NODEBOOSTER_OT_favorite_add.bl_idname,      "Y",         "PRESS", True,  False, False, (),                                       "Add Favorite",            "SOLO_OFF",  True, ),
    ( NODEBOOSTER_OT_favorite_loop.bl_idname,     "Y",         "PRESS", False, False, False, (),                                       "Loop Favorites",          "SOLO_OFF",  True, ),
    ( NODEBOOSTER_OT_dependency_select.bl_idname, "LEFTMOUSE", "PRESS", True,  False, False, (("mode","downstream"),("repsel",True )), "Select Downstream",       "BACK",      True, ),
    ( NODEBOOSTER_OT_dependency_select.bl_idname, "LEFTMOUSE", "PRESS", True,  True,  False, (("mode","downstream"),("repsel",False)), "Select Downstream (Add)", "BACK",      True, ),
    ( NODEBOOSTER_OT_dependency_select.bl_idname, "LEFTMOUSE", "PRESS", True,  False, True,  (("mode","upstream"),  ("repsel",True )), "Select Upsteam",          "FORWARD",   True, ),
    ( NODEBOOSTER_OT_dependency_select.bl_idname, "LEFTMOUSE", "PRESS", True,  True,  True,  (("mode","upstream"),  ("repsel",False)), "Select Upsteam (Add)",    "FORWARD",   True, ),
    # ( NOODLER_OT_draw_route.bl_idname,        "V",         "PRESS", False, False, False, (),                                       "Operator: Draw Route",              "TRACKING",  True,  ),
    # ( NOODLER_OT_draw_frame.bl_idname,        "J",         "PRESS", False, False, False, (),                                       "Operator: Draw Frame",              "ALIGN_TOP", True,  ),
    # ( NOODLER_OT_chamfer.bl_idname,           "B",         "PRESS", True,  False, False, (),                                       "Operator: Reroute Chamfer",         "MOD_BEVEL", True,  ),

    )

ADDON_KEYMAPS = []


def load_operators_keymaps():
    
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
    