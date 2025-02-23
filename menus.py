# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy 

from .customnodes import classes as nodeclasses


class NODEBOOSTER_MT_addmenu_general(bpy.types.Menu):

    bl_idname = "NODEBOOSTER_MT_addmenu_general"
    bl_label  = "Booster Nodes"

    @classmethod
    def poll(cls, context):
        return (bpy.context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        
        for cls in nodeclasses:
            if ('_NG_' in cls.__name__):
                op = self.layout.operator("node.add_node", text=cls.bl_label,)
                op.type = cls.bl_idname
                op.use_transform = True
        
        return None


def nodebooster_addmenu_append(self, context,):
    
    self.layout.menu("NODEBOOSTER_MT_addmenu_general", text="Booster Nodes",)
    
    return None 


def append_menus():

    menu = bpy.types.NODE_MT_add
    menu.append(nodebooster_addmenu_append)

    return None 


def remove_menus():

    menu = bpy.types.NODE_MT_add
    for f in menu._dyn_ui_initialize().copy():
        if (f.__name__=='nodebooster_addmenu_append'):
            menu.remove(f)
            continue
    
    return None


classes = (
    
    NODEBOOSTER_MT_addmenu_general,
    
    )