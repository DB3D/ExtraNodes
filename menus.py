# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN, SLU
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy 


class EXTRANODES_MT_addmenu_general(bpy.types.Menu):

    bl_idname = "EXTRANODES_MT_addmenu_general"
    bl_label  = "Extra Nodes"

    @classmethod
    def poll(cls, context):
        return (bpy.context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        
        from . geometrycustomnodes import EXTRANODES_NG_camerainfo, EXTRANODES_NG_isrenderedview, EXTRANODES_NG_sequencervolume, EXTRANODES_NG_pythonapi
        
        for cls in (EXTRANODES_NG_camerainfo, EXTRANODES_NG_isrenderedview, EXTRANODES_NG_sequencervolume, EXTRANODES_NG_pythonapi,):
            op = self.layout.operator("node.add_node", text=cls.bl_label,)
            op.type = cls.bl_idname
            op.use_transform = True
        
        return None


def extranodes_addmenu_append(self, context,):
    
    self.layout.menu("EXTRANODES_MT_addmenu_general", text="Extra Nodes",)
    
    return None 


def append_menus():

    menu = bpy.types.NODE_MT_add
    menu.append(extranodes_addmenu_append)

    return None 


def remove_menus():

    menu = bpy.types.NODE_MT_add
    for f in menu._dyn_ui_initialize().copy():
        if (f.__name__=='extranodes_addmenu_append'):
            menu.remove(f)
            continue
    
    return None


classes = (
    
    EXTRANODES_MT_addmenu_general,
    
    )