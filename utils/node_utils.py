# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy 


def get_socket_interface_item(ng, idx, in_out='OUTPUT',):
    """return a given socket index as an interface item, either find the socket by it's index, name or socketidentifier"""
    
    #first we need to retrieve the socket identifier from index
    identifier = None
    sockets = ng.nodes["Group Output"].inputs if (in_out=='OUTPUT') else ng.nodes["Group Input"].outputs
    for i,s in enumerate(sockets):
        if (i==idx):
            identifier = s.identifier
            break
    
    if (identifier is None):
        raise Exception("ERROR: get_socket_interface_item(): couldn't retrieve socket identifier..")
    
    #then we retrieve thesocket interface item from identifier
    sockui = None
    findgen = [itm for itm in ng.interface.items_tree
               if hasattr(itm,'identifier') and (itm.identifier == identifier)]
    if len(findgen):
        sockui = findgen[0]
        
    if (sockui is None):
        raise Exception("ERROR: get_socket_interface_item(): couldn't retrieve socket interface item..")
    
    return sockui


def get_socket_defvalue(ng, idx, in_out='OUTPUT',):
    """return the value of the given nodegroups output at given socket idx"""
    
    match in_out:
        case 'OUTPUT':
            return ng.nodes["Group Output"].inputs[idx].default_value
        case 'INPUT':
            return ng.nodes["Group Input"].outputs[idx].default_value
        case _:
            raise Exception("get_socket_defvalue(): in_out arg not valid")

     
def set_socket_defvalue(ng, idx, in_out='OUTPUT', value=None,):
    """set the value of the given nodegroups output at given socket idx"""
    
    match in_out:
        case 'OUTPUT':
            ng.nodes["Group Output"].inputs[idx].default_value = value 
        case 'INPUT':
            ng.nodes["Group Input"].outputs[idx].default_value = value 
        case _:
            raise Exception("get_socket_defvalue(): in_out arg not valid")
        
    return None


def set_socket_label(ng, idx, in_out='OUTPUT', label=None,):
    """return the label of the given nodegroups output at given socket idx"""
    
    itm = get_socket_interface_item(ng, idx, in_out=in_out,)
    itm.name = str(label)
                
    return None  


def get_socket_type(ng, idx, in_out='OUTPUT',):
    """return the type of the given nodegroups output at given socket idx"""
    
    itm = get_socket_interface_item(ng, idx, in_out=in_out,)
    return itm.socket_type


def set_socket_type(ng, idx, in_out='OUTPUT', socket_type="NodeSocketFloat",):
    """set socket type via bpy.ops.node.tree_socket_change_type() with manual override, context MUST be the geometry node editor"""

    itm = get_socket_interface_item(ng, idx, in_out=in_out,)
    itm.socket_type = socket_type

    return None


def create_socket(ng, in_out='OUTPUT', socket_type="NodeSocketFloat", socket_name="Value",):
    """create a new socket output of given type for given nodegroup"""
    
    return ng.interface.new_socket(socket_name, in_out=in_out, socket_type=socket_type,)


def remove_socket(ng, idx, in_out='OUTPUT',):
    """remove a nodegroup socket output at given index"""
        
    itm = get_socket_interface_item(ng, idx, in_out=in_out,)
    ng.interface.remove(itm)
    
    return None 


def create_new_nodegroup(name, in_sockets={}, out_sockets={},):
    """create new nodegroup with outputs from given dict {"name":"type",}"""

    ng = bpy.data.node_groups.new(name=name, type='GeometryNodeTree',)
    
    #create main input/output
    in_node = ng.nodes.new('NodeGroupInput')
    in_node.location.x -= 200
    out_node = ng.nodes.new('NodeGroupOutput')
    out_node.location.x += 200

    #create the sockets
    for socket_name, socket_type in in_sockets.items():
        create_socket(ng, in_out='INPUT', socket_type=socket_type, socket_name=socket_name,)
    for socket_name, socket_type in out_sockets.items():
        create_socket(ng, in_out='OUTPUT', socket_type=socket_type, socket_name=socket_name,)
        
    return ng

def link_sockets(socket1, socket2):
    """link two nodes together in a nodetree"""

    ng = socket1.id_data
    return ng.links.new(socket1, socket2)


def replace_node(node_tree, old_node, node_group):
    """Replace an existing node with a new Node Group node (assuming same socket structure)"""
    
    # Save old node properties.
    old_node_width = float(old_node.width)
    old_node_location = old_node.location.copy()
    
    # For inputs, store default values and the linked from_socket (if exists)
    old_inputs_defaults = [getattr(sock, 'default_value', None) for sock in old_node.inputs]
    old_inputs_links = [sock.links[0].from_socket if sock.links else None for sock in old_node.inputs]
    
    # For outputs, store the linked to_socket (if exists)
    old_outputs_links = [sock.links[0].to_socket if sock.links else None for sock in old_node.outputs]
    
    # Delete the old node.
    node_tree.nodes.remove(old_node)
    
    # Determine the appropriate node type for a node group.
    if node_tree.bl_idname == "ShaderNodeTree":
        new_node_type = "ShaderNodeGroup"
    elif node_tree.bl_idname == "CompositorNodeTree":
        new_node_type = "CompositorNodeGroup"
    elif node_tree.bl_idname == "GeometryNodeTree":
        new_node_type = "GeometryNodeGroup"
    else:
        new_node_type = "ShaderNodeGroup"  # Fallback if unknown.
    
    # Create the new node group node.
    new_node = node_tree.nodes.new(new_node_type)
    new_node.location = old_node_location
    new_node.width = old_node_width
    
    # Assign the provided node group.
    new_node.node_tree = node_group

    # Re-apply default values to new node inputs (if available).
    for i, sock in enumerate(new_node.inputs):
        if i < len(old_inputs_defaults) and old_inputs_defaults[i] is not None:
            try:
                sock.default_value = old_inputs_defaults[i]
            except Exception as e:
                print(f"Warning: Could not copy default for input '{sock.name}': {e}")
    
    # Re-create input links.
    for i, sock in enumerate(new_node.inputs):
        if i < len(old_inputs_links) and old_inputs_links[i] is not None:
            try:
                node_tree.links.new(old_inputs_links[i], sock)
            except Exception as e:
                print(f"Warning: Could not re-link input '{sock.name}': {e}")
    
    # Re-create output links.
    for i, sock in enumerate(new_node.outputs):
        if i < len(old_outputs_links) and old_outputs_links[i] is not None:
            try:
                node_tree.links.new(sock, old_outputs_links[i])
            except Exception as e:
                print(f"Warning: Could not re-link output '{sock.name}': {e}")
    
    return new_node


def frame_nodes(node_tree, *nodes, label="Frame",):
    """Create a Frame node in the given node_tree and parent the specified nodes to it."""

    frame = node_tree.nodes.new("NodeFrame")
    frame.label = label
    
    for node in nodes:
        node.parent = frame
    
    return frame
