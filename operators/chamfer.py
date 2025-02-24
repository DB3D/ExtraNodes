# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy

import numpy
from mathutils import Vector

from ..utils.node_utils import get_node_absolute_location
from ..utils.draw_utils import ensure_mouse_cursor


def get_rr_links_info(n,mode):
    """get links information from given node, we do all this because we can't store socket object directly, too dangerous, cause bug as object pointer change in memory often"""

    links_info=[]
    is_input = (mode=='IN')

    sockets = n.inputs[0] if is_input else n.outputs[0]
    for i,l in enumerate(sockets.links):
        s = l.from_socket if is_input else l.to_socket
        dn = s.node

        #retrieve socket index
        sidx = None #should never be none
        nsocks = dn.outputs if is_input else dn.inputs
        for sidx,sout in enumerate(nsocks):
            if (sout==s):
                break 

        info = (dn.name,s.name,sidx)
        links_info.append(info) 
        continue

    return links_info


def restore_links_to_original(n,ng,links_info,mode):
    """restore links from given info list"""

    is_input = (mode=='IN')

    for elem in links_info:
        
        nn, _, sidx = elem
        dn = ng.nodes.get(nn)
        s = dn.outputs[sidx] if is_input else dn.inputs[sidx]
        
        args = (s, n.inputs[0]) if is_input else (n.outputs[0], s,)
        ng.links.new(*args)

        continue

    return None 


class ChamferItem():

    init_rr = "" #Initial Reroute Node. Storing names to avoid crash
    init_loc_local = (0,0) #Initial Local Location Vector.
    added_rr = "" #all added reroute, aka the reroute added before init rr. Storing names to avoid crash
    fromvec = (0,0) #downstream chamfer direction Vector
    tovec = (0,0) #upstream chamfer direction  Vector


class NODEBOOSTER_OT_chamfer(bpy.types.Operator): 

    #NOTE not sure how real bevel algo works, but this is a 'naive' approach, we create a new vert, new edges 
    # and moving their location from the origin origin point
    #NOTE that local/global space can be problematic. Here we are only working in local space, if parent. 

    bl_idname = "nodebooster.chamfer"
    bl_label = "Reroute Chamfer"
    bl_options = {'REGISTER'}

    def __init__(self, *args, **kwargs):
        
        super().__init__(*args, **kwargs)
        
        #We only store blender data here when the operator is active, we should be totally fine!
        self.node_tree = None
        self.init_click = (0,0)
        self.chamfer_data = []
        self.init_state = {}

    @classmethod
    def poll(cls, context):
        return (context.space_data.type=='NODE_EDITOR') and (context.space_data.node_tree is not None)

    def chamfer_setup(self, n):

        ng = self.node_tree

        Chamf = ChamferItem() #Using custom class may cause crashes? i had one... perhaps it would be best to switch to nested lists or dicts?  
        Chamf.init_rr = n.name     #we are storing objects directly and their adress may change 

        #get initial node location
        Chamf.init_loc_local = n.location.copy() 

        left_link = n.inputs[0].links[0]
        from_sock = left_link.from_socket
        right_link = n.outputs[0].links[0]
        to_sock = right_link.to_socket

        #get chamfer directions, in global space
        loc_init_global = get_node_absolute_location(n).copy() 
        #get chamfer direction from
        if (from_sock.node.type == 'REROUTE'):
              Chamf.fromvec = get_node_absolute_location(from_sock.node) - loc_init_global
              Chamf.fromvec.normalize()
        else: Chamf.fromvec = Vector((-1,0))
        #get chamfer direction to
        if (to_sock.node.type == 'REROUTE'):
              Chamf.tovec = get_node_absolute_location(to_sock.node) - loc_init_global
              Chamf.tovec.normalize()
        else: Chamf.tovec = Vector((1,0))

        #add new reroute 
        rra = ng.nodes.new("NodeReroute")
        rra.location = n.location
        rra.parent = n.parent
        Chamf.added_rr = rra.name

        #remove old link 
        ng.links.remove(left_link)
        #add new links
        ng.links.new(from_sock, rra.inputs[0],)
        ng.links.new(rra.outputs[0], n.inputs[0],)

        #set selection visual cue 
        n.select = rra.select = True 

        self.chamfer_data.append(Chamf)
        return None

    def invoke(self, context, event):

        ng = context.space_data.edit_tree
        self.node_tree = ng

        #get initial mouse position
        ensure_mouse_cursor(context, event)
        self.init_click = context.space_data.cursor_location.copy()  

        selected = [n for n in ng.nodes if n.select and (n.type=='REROUTE') \
         and not ((len(n.inputs[0].links)==0) or (len(n.outputs[0].links)==0))]
        
        if (len(selected)==0):
            return {'FINISHED'}

        #save state to data later
        for n in selected: 
            self.init_state[n.name]={
                "location":n.location.copy(),
                "IN":get_rr_links_info(n,"IN"),
                "OUT":get_rr_links_info(n,"OUT"),
                }

        #set selection
        for n in self.node_tree.nodes:
            n.select = False

        #set up chamfer
        for n in selected:
            self.chamfer_setup(n)

        #Write status bar
        context.workspace.status_text_set_internal("Confirm:   'Enter' 'Space' 'Left-Click'     |     Cancel:   'Right-Click' 'Esc'")
        
        #start modal 
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):     

        try:
            # context.area.tag_redraw()

            #if user confirm:
            if (event.type in ("LEFTMOUSE","RET","SPACE")):
                bpy.ops.ed.undo_push(message="Reroute Chamfer", )
                context.workspace.status_text_set_internal(None)
                return {'FINISHED'}

            #if user cancel:
            elif event.type in ("ESC","RIGHTMOUSE"):
                
                #remove all newly created items
                for Chamfer in self.chamfer_data:
                    self.node_tree.nodes.remove(self.node_tree.nodes.get(Chamfer.added_rr))

                #restore init state
                for k,v in self.init_state.items():
                    n = self.node_tree.nodes[k]
                    n.location = v["location"]
                    restore_links_to_original(n, self.node_tree, v["IN"], "IN")
                    restore_links_to_original(n, self.node_tree, v["OUT"], "OUT")
                    continue
                
                context.workspace.status_text_set_internal(None)
                # context.area.tag_redraw()
                return {'CANCELLED'}

            #else move position of all chamfer items
            
            #get distance data from cursor
            ensure_mouse_cursor(context, event)
            distance = numpy.linalg.norm(context.space_data.cursor_location - self.init_click)
                
            #move chamfer vertex
            for Chamf in self.chamfer_data:
                #need global to local
                self.node_tree.nodes.get(Chamf.init_rr).location = Chamf.init_loc_local + ( Chamf.tovec * distance )
                self.node_tree.nodes.get(Chamf.added_rr).location = Chamf.init_loc_local + ( Chamf.fromvec * distance )
                continue

        except Exception as e:
            print(e)
            context.workspace.status_text_set_internal(None)
            self.report({'ERROR'},"An Error Occured during Chamfer modal")
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}