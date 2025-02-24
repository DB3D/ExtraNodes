# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy 

from ..__init__ import get_addon_prefs
from ..utils.str_utils import word_wrap
from ..utils.node_utils import create_new_nodegroup, set_socket_defvalue


def all_3d_viewports():
    """return generator of all 3d view space"""
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if (area.type == 'VIEW_3D'):
                for space in area.spaces:
                    if (space.type == 'VIEW_3D'):
                        yield space


def all_3d_viewports_shading_type():
    """return generator of all shading type str"""
    for space in all_3d_viewports():
        yield space.shading.type


def is_rendered_view():
    """check if is rendered view in a 3d view somewhere"""
    return 'RENDERED' in all_3d_viewports_shading_type()


class NODEBOOSTER_NG_isrenderedview(bpy.types.GeometryNodeCustomGroup):
    """Custom Nodgroup: Evaluate if any 3Dviewport is in rendered view mode.
    The value is evaluated from depsgraph post update signals"""
    
    bl_idname = "GeometryNodeNodeBoosterIsRenderedView"
    bl_label = "Is Rendered View"

    @classmethod
    def poll(cls, context):
        """mandatory poll"""
        return True

    def init(self, context,):        
        """this fct run when appending the node for the first time"""

        name = f".{self.bl_idname}"

        ng = bpy.data.node_groups.get(name)
        if (ng is None):
            ng = create_new_nodegroup(name, 
                out_sockets={
                    "Is Rendered View" : "NodeSocketBool",
                },
            )

        self.node_tree = ng
        self.label = self.bl_label

        set_socket_defvalue(ng, 0, value=is_rendered_view(),)
        return None 

    def update(self):
        """generic update function"""

        return None
    
    def draw_label(self,):
        """node label"""
        
        return self.bl_label

    def draw_buttons(self, context, layout,):
        """node interface drawing"""
        
        return None 
    
    @classmethod
    def update_all(cls):
        """search for all nodes of this type and update them"""
        
        name = f".{cls.bl_idname}"
        
        #actually there's only one instance of this node nodetree
        ng = bpy.data.node_groups.get(name)
        if (ng):
            set_socket_defvalue(ng, 0, value=is_rendered_view(),)
            
        return None
    