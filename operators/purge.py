# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy 


def is_node_used(node):
    """check if node is reaching output"""
            
    found_output = False
    
    def recur_node(n):

        #reached destination? 
        if (n.type == "GROUP_OUTPUT"):
            nonlocal found_output
            found_output = True
            return 

        #else continue parcour
        for out in n.outputs:
            for link in out.links:
                recur_node(link.to_node)

        return None 
        
    recur_node(node)

    return found_output


def purge_unused_nodes(node_group, delete_muted=True, delete_reroute=True, delete_frame=True):
    """delete all unused nodes, using 'ops.node.delete_reconnect' operator"""
        
    for n in list(node_group.nodes):
        
        #deselct all
        n.select = False
        
        #delete if muted?
        if (delete_muted==True and n.mute==True):  
            n.select = True
            continue 
        
        #delete if reroute?
        if (delete_reroute==True and n.type=="REROUTE"):
            n.select = True
            continue         
              
        #don't delete if frame?
        if (delete_frame==False and n.type=="FRAME"):
            continue 
        
        #delete if unconnected
        if not is_node_used(n):
            node_group.nodes.remove(n)
            
        continue 

    if (delete_muted or delete_reroute):
        bpy.ops.node.delete_reconnect()
        
    return None 


def re_arrange_nodes(node_group, Xmultiplier=1):
    """re-arrange node by sorting them in X location, (could improve)"""

    nodes = { n.location.x:n for n in node_group.nodes }
    nodes = { k:nodes[k] for k in sorted(nodes) }

    for i,n in enumerate(nodes.values()):
        n.location.x = i*200*Xmultiplier
        n.width = 150

    return None 


class NODEBOOSTER_OT_node_purge_unused(bpy.types.Operator):

    bl_idname      = "nodebooster.node_purge_unused"
    bl_label       = "Purge Unused Nodes"
    bl_description = ""
    bl_options     = {'REGISTER','UNDO',}

    delete_frame : bpy.props.BoolProperty(
        default=True,
        name="Remove Frame(s)",
        )
    delete_muted : bpy.props.BoolProperty(
        default=True,
        name="Remove Muted Node(s)",
        )
    delete_reroute : bpy.props.BoolProperty(
        default=True,
        name="Remove Reroute(s)",
        )

    re_arrange : bpy.props.BoolProperty(
        default=False,
        name="Re-Arrange Nodes",
        )
    re_arrange_fake : bpy.props.BoolProperty(
        default=False,
        name="Re-Arrange (not possible with frames)",
        )

    @classmethod
    def poll(cls, context):
        return (context.space_data.type=='NODE_EDITOR') and (context.space_data.node_tree is not None)

    def execute(self, context):
        node_group = context.space_data.node_tree

        purge_unused_nodes(
            node_group, 
            delete_muted=self.delete_muted,
            delete_reroute=self.delete_reroute,
            delete_frame=self.delete_frame,
            )

        if (self.re_arrange and self.delete_frame):
            re_arrange_nodes(node_group)

        return {'FINISHED'}

    def invoke(self, context, event):
        return bpy.context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout 
        
        layout.prop(self, "delete_muted")
        layout.prop(self, "delete_reroute")
        layout.prop(self, "delete_frame")
        
        match self.delete_frame:
            case True:
                layout.prop(self, "re_arrange")
            case False:
                re = layout.row()
                re.enabled = False
                re.prop(self, "re_arrange_fake")

        return None 