# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy

from ..utils.node_utils import replace_node


class NODEBOOSTER_OT_bake_customnode(bpy.types.Operator):
    """Replace the custom node with a nodegroup, preserve values and links"""
    
    bl_idname = "extranode.bake_customnode"
    bl_label = "Bake Custom Node"
    bl_options = {'REGISTER', 'UNDO'}

    nodegroup_name: bpy.props.StringProperty()
    node_name: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return (context.space_data.type=='NODE_EDITOR') and (context.space_data.node_tree is not None)

    def execute(self, context):

        space = context.space_data
        node_tree = space.edit_tree

        old_node = node_tree.nodes.get(self.node_name)
        if (old_node is None):
            self.report({'ERROR'}, "Node with given name not found")
            return {'CANCELLED'}

        node_group = bpy.data.node_groups.get(self.nodegroup_name)
        if (node_group is None):
            self.report({'ERROR'}, "Node group with given name not found")
            return {'CANCELLED'}

        name = None
        if hasattr(old_node,"user_mathexp"):
            name = str(old_node.user_mathexp)
        if hasattr(old_node,"user_textdata"):
            if (old_node.user_textdata):
                name = old_node.user_textdata.name
        
        node_group = node_group.copy()
        node_group.name = f'{node_group.name}.Baked'

        new_node = replace_node(node_tree, old_node, node_group,)
        if (new_node is None):
            self.report({'ERROR'}, "Current NodeTree type not supported")
            return {'FINISHED'}

        if (name):
            new_node.label = name

        self.report({'INFO'}, f"Replaced node '{self.node_name}' with node group '{self.node_name}'")

        return {'FINISHED'}
