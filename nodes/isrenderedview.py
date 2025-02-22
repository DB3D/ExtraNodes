# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy 

from ..__init__ import get_addon_prefs
from .boiler import create_new_nodegroup


class EXTRANODES_NG_isrenderedview(bpy.types.GeometryNodeCustomGroup):
    """Custom Nodgroup: Evaluate if any 3Dviewport is in rendered view mode.
    The value is evaluated from depsgraph post update signals"""
    
    bl_idname = "GeometryNodeExtraNodesIsRenderedView"
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
        self.width = 140
        self.label = self.bl_label

        return None 
    
    def draw_label(self,):
        """node label"""
        
        return self.bl_label

    def draw_buttons(self, context, layout,):
        """node interface drawing"""
        
        return None 

    def draw_buttons_ext(self, context, layout):
        """draw in the N panel when the node is selected"""
        
        col = layout.column(align=True)
        col.label(text="NodeTree:")
        col.template_ID(self, "node_tree")
        
        return None