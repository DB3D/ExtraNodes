# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy 

from ..customnodes import classes as NODECUSTOMCLS


class NODEBOOSTER_MT_addmenu_general(bpy.types.Menu):

    bl_idname = "NODEBOOSTER_MT_addmenu_general"
    bl_label  = "Booster Nodes"

    @classmethod
    def poll(cls, context):
        return (bpy.context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):

        for cls in NODECUSTOMCLS:
            if ('_NG_' in cls.__name__):
                op = self.layout.operator("node.add_node", text=cls.bl_label,)
                op.type = cls.bl_idname
                op.use_transform = True

        return None


def nodebooster_addmenu_append(self, context,):

    self.layout.menu("NODEBOOSTER_MT_addmenu_general", text="Booster Nodes",)

    return None 

def nodebooster_nodemenu_append(self, context):

    layout = self.layout 
    layout.separator()
    layout.operator("nodebooster.node_purge_unused", text="Purge Unused Nodes",)

    return None


def append_menus():

    bpy.types.NODE_MT_add.append(nodebooster_addmenu_append)
    bpy.types.NODE_MT_node.append(nodebooster_nodemenu_append)

    return None

def remove_menus():

    #remove menus by name, in case there was a problem at unreg
    menus = (bpy.types.NODE_MT_add, bpy.types.NODE_MT_node,)
    for menu in menus:
        for f in menu._dyn_ui_initialize().copy():
            if (f.__name__=='nodebooster_addmenu_append'):
                menu.remove(f)
            if (f.__name__=='nodebooster_nodemenu_append'):
                menu.remove(f)

    return None