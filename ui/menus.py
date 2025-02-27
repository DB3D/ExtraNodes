# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy 

import os

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


class NODEBOOSTER_MT_textemplate(bpy.types.Menu):

    bl_idname = "NODEBOOSTER_MT_textemplate"
    bl_label  = "Booster Nodes"

    def draw(self, context):

        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        external_dir = os.path.join(parent_dir, "external")
        
        file_path = os.path.join(external_dir, "NexSimpleExample.py")
        layout = self.layout 
        layout.separator()
        op = layout.operator("nodebooster.import_template", text=os.path.basename(file_path),)
        op.filepath = file_path

        return None

def nodebooster_templatemenu_append(self, context):
    
    layout = self.layout 
    layout.separator()
    layout.menu("NODEBOOSTER_MT_textemplate", text="Booster Scripts",)

    return None


MENUS = [
    bpy.types.NODE_MT_add,
    bpy.types.NODE_MT_node,
    bpy.types.TEXT_MT_templates,
    ]


DRAWFUNCS = [
    nodebooster_addmenu_append,
    nodebooster_nodemenu_append,
    nodebooster_templatemenu_append,
    ]


def append_menus():

    for menu, fct in zip(MENUS,DRAWFUNCS):
        menu.append(fct)

    return None

def remove_menus():

    for menu in MENUS:
        for f in menu._dyn_ui_initialize().copy():
            if (f in DRAWFUNCS):
                menu.remove(f)

    return None