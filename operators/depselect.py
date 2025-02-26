# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy

from ..utils.draw_utils import ensure_mouse_cursor
from ..utils.node_utils import get_nearest_node_at_position


def get_dependecies(node, context, mode="upstream|downstream", parent=False):
    """return list of all nodes downstream or upsteam"""

    NODELIST = []

    #determine vars used in recur fct
    is_upstream = (mode=="upstream")
    sockets_api = "outputs" if is_upstream else "inputs"
    link_api = "to_node" if is_upstream else "from_node"

    def recur_node(node):
        """gather node in nodelist by recursion"""

        #add note to list 
        NODELIST.append(node)

        #frame?
        if (parent and node.parent):
            if (node.parent not in NODELIST):
                NODELIST.append(node.parent)

        #get sockets 
        sockets = getattr(node,sockets_api)
        if not len(sockets):
            return None 

        #check all outputs
        for socket in sockets:
            for link in socket.links:
                nextnode = getattr(link,link_api)
                if nextnode not in NODELIST:
                    recur_node(nextnode)
                continue
            continue

        return None 

    recur_node(node)

    return NODELIST


class NODEBOOSTER_OT_dependency_select(bpy.types.Operator):

    bl_idname = "nodebooster.dependency_select"
    bl_label = "Select Dependencies"
    bl_options = {'REGISTER', 'UNDO'}

    mode : bpy.props.EnumProperty(
        name="Mode",
        default="downstream",
        items=[
            ("downstream","Downstream","",),
            ("upstream","Upstream","",),
            ],
        )
    repsel : bpy.props.BoolProperty(
        default=True,
        name="Replace Selection",
        )
    frame : bpy.props.BoolProperty(
        default=False,
        name="Include Frames",
        )

    @classmethod
    def poll(cls, context):
        return (context.space_data.type=='NODE_EDITOR') and (context.space_data.node_tree is not None)

    def invoke(self, context, event):

        ng = context.space_data.edit_tree
        
        ensure_mouse_cursor(context, event)
        node = get_nearest_node_at_position(ng.nodes, context, event, position=context.space_data.cursor_location)
        if node is None:
            return {"CANCELLED"}

        if (self.repsel):
            bpy.ops.node.select_all(action="DESELECT")

        deps = get_dependecies(node, context, mode=self.mode, parent=self.frame)
        for n in deps:
            n.select = True

        return {"CANCELLED"}
