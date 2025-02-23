# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy

from datetime import datetime

from ..utils.node_utils import get_node_absolute_location
from ..utils.draw_utils import ensure_mouse_cursor


def get_nodes_in_frame_box(boxf, nodes, frame_support=True,):
    """search node that can potentially be inside this boxframe created box"""

    for n in nodes:

        #we do not want information on ourselves
        if ((n==boxf) or (n.parent==boxf)):
            continue

        #for now, completely impossible to get a frame location..
        if (n.type=="FRAME"):
            continue

        locx,locy = get_node_absolute_location(n)

        if boxf.location.x <= locx <= (boxf.location.x + boxf.dimensions.x) and \
           boxf.location.y >= locy >= (boxf.location.y - boxf.dimensions.y):
            yield n


class NODEBOOSTER_OT_draw_frame(bpy.types.Operator):
    """modal operator to easily draw frames by keep pressing the J key"""
    
    #TODO would be nice to also support add frames to frames
    
    bl_idname = "nodebooster.draw_frame"
    bl_label = "Draw Frames"
    bl_options = {'REGISTER'}

    def __init__(self, *args, **kwargs):
        """get var user selection"""
        
        super().__init__(*args, **kwargs)
        
        self.node_tree = None
        self.boxf = None
        self.old = (0,0)
        self.timer = None 
        self.init_time = None
        self.selframerate = 0.350 #selection refreshrate in s, const

    @classmethod
    def poll(cls, context):
        return (context.space_data.type=='NODE_EDITOR') and (context.space_data.node_tree is not None)

    def invoke(self, context, event):

        ng = context.space_data.edit_tree
        self.node_tree = ng

        ensure_mouse_cursor(context, event)
        self.old = context.space_data.cursor_location.copy()  

        boxf = ng.nodes.new("NodeFrame")
        self.boxf = boxf 
        boxf.bl_width_min = boxf.bl_height_min = 20
        boxf.width = boxf.height = 0
        boxf.select = False
        boxf.location = self.old

        sett_scene = context.scene.nodebooster
        boxf.use_custom_color = sett_scene.frame_use_custom_color
        boxf.color = sett_scene.frame_color
        boxf.label = sett_scene.frame_label
        boxf.label_size = sett_scene.frame_label_size

        #start timer, needed to regulate a function refresh rate
        self.timer = context.window_manager.event_timer_add(self.selframerate, window=context.window)
        self.init_time = datetime.now()

        #start modal 
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):     

        context.area.tag_redraw()

        #if user confirm:
        if ((event.value=="RELEASE") or (event.type=="LEFTMOUSE")):
                    
            #if box is too small, just cancel
            if (self.boxf.dimensions.x <30 and self.boxf.dimensions.y <30):
                self.cancel(context)
                return {'CANCELLED'}

            nodes = list(get_nodes_in_frame_box(self.boxf,self.node_tree.nodes))

            if (len(nodes)==0):
                return {'FINISHED'}
        
            for n in nodes:
                n.parent = self.boxf
                continue

            for n in nodes:
                n.select = False

            self.node_tree.nodes.active = self.boxf
            self.boxf.select = True

            context.area.tag_redraw()
            context.window_manager.event_timer_remove(self.timer)

            return {'FINISHED'}

        #if user cancel:

        elif event.type in ("ESC","RIGHTMOUSE"):
            self.cancel(context)
            return {'CANCELLED'}

        #only start if user is pressing a bit longer
        time_diff = datetime.now()-self.init_time
        if time_diff.total_seconds()<0.150:
            return {'RUNNING_MODAL'}

        #else, adjust frame location/width/height:
    
        #else recalculate position & frame dimensions
        ensure_mouse_cursor(context, event)
        new = context.space_data.cursor_location
        old = self.old

        #new y above init y
        if (old.y<=new.y):
              self.boxf.location.y = new.y
              self.boxf.height = (new.y-old.y)
        else: self.boxf.height = (old.y-new.y)

        #same principle as above for width
        if (old.x>=new.x):
              self.boxf.location.x = new.x
              self.boxf.width = (old.x-new.x)
        else: self.boxf.width = (new.x-old.x)

        #dynamic selection:

        #enable every 100ms, too slow for python.. 
        if (event.type != 'TIMER'):
            return {'RUNNING_MODAL'}

        #show user a preview off the future node by selecting them
        for n in self.node_tree.nodes:
            n.select = False
        for n in get_nodes_in_frame_box(self.boxf,self.node_tree.nodes):
            n.select = True
            continue

        return {'RUNNING_MODAL'}

    def cancel(self, context):

        self.node_tree.nodes.remove(self.boxf)
        
        for n in self.node_tree.nodes:
            n.select = False

        context.area.tag_redraw()
        context.window_manager.event_timer_remove(self.timer)

        return None 
