# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Noodler",
    "author": "BD3D",
    "version": (1, 0),
    "blender": (2, 93, 0),
    "location": "Node Editor: (Shortcuts, Panel), Addonpreferences",
    "description": "Collection of useful tools/shortcuts for node editors",
    "doc_url": "https://blenderartists.org/t/bd3d-node-plugin/1297740",
    "category": "Node",
}

"""
TODO
    -Find solution for depsgraph & modal operator problem. while in modal, any python api attr set will trigger 
     a depsgraph scene update, making things uncessessary slow. happenning for draw_frame/draw_route/chamfer.
     not sure if possible, prolly hard coded limitation of the python api. 
    -45D lock for draw_route
    -Shift a support for draw_route
    -text node
    -image ref node
    -synchronize image node with active image in img editor
    -proper re-arrange algo -> need socket position api 
    -draw_frame should support framing other frames -> unfortunately frame position api is bad
    -chamfer algo can't detect inputs sockets from nodes right now it's using default directions -> need socket position api 
    -bgl soon deprecated
    -ideally some of these functionality need to be implemented in CPP if the idea get a pass. 

"""

import bpy, blf
import os, sys, numpy
from datetime import datetime
from math import hypot
from mathutils import Vector


#add bl_ui to modules, we'll need to borrow a class later
scr = bpy.utils.system_resource('SCRIPTS')
pth = os.path.join(scr,'startup','bl_ui')
if pth not in sys.path:
    sys.path.append(pth)


from bl_ui.properties_paint_common import BrushPanel


# oooooooooooo                                       .    o8o
# `888'     `8                                     .o8    `"'
#  888         oooo  oooo  ooo. .oo.    .ooooo.  .o888oo oooo   .ooooo.  ooo. .oo.    .oooo.o
#  888oooo8    `888  `888  `888P"Y88b  d88' `"Y8   888   `888  d88' `88b `888P"Y88b  d88(  "8
#  888    "     888   888   888   888  888         888    888  888   888  888   888  `"Y88b.
#  888          888   888   888   888  888   .o8   888 .  888  888   888  888   888  o.  )88b
# o888o         `V88V"V8P' o888o o888o `Y8bod8P'   "888" o888o `Y8bod8P' o888o o888o 8""888P'


def get_active_tree(context):
    """Get nodes from currently edited tree.
    If user is editing a group, space_data.node_tree is still the base level (outside group).
    context.active_node is in the group though, so if space_data.node_tree.nodes.active is not
    the same as context.active_node, the user is in a group.
    source: node_wrangler.py"""

    tree = context.space_data.node_tree
    path = []

    if tree.nodes.active:

        #Check recursively until we find the real active node_tree
        while (tree.nodes.active != context.active_node):
            tree = tree.nodes.active.node_tree
            path.append(tree)
            continue
    
    return tree, path


def get_space_from_mouse(x,y):
    
    areas =  bpy.context.window.screen.areas
    for a in areas:
        if (a.x<x<a.x+a.width) and (a.y<y<a.y+a.height):
            return a.spaces[0]
    return None 


def set_all_node_select(nodes, select_state,):
    for n in nodes:
        n.select = select_state
    return None 


def popup_menu(msgs,title,icon):

    def draw(self, context):
        layout = self.layout
        for msg in msgs:
            layout.label(text=msg)
        return  

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)
    return None 


def ensure_mouse_cursor(context, event,):
    """function needed to get cursor location, source: node_wrangler.py"""

    space = context.space_data
    v2d = context.region.view2d
    tree = space.edit_tree

    # convert mouse position to the View2D for later node placement
    if (context.region.type == "WINDOW"):
          space.cursor_location_from_region(event.mouse_region_x, event.mouse_region_y)
    else: space.cursor_location = tree.view_center

    return None


def get_node_location(node, nodes,):
    """find real location of a node (global space guaranteed)"""
    
    if (node.parent is None):
        return node.location

    x,y = node.location

    while (node.parent is not None):
        x += node.parent.location.x
        y += node.parent.location.y
        node = node.parent
        continue

    return Vector((x,y))


AllFonts = {} 

def blf_add_font(text="Hello World", size=[50,72], position=[2,180], color=[1,1,1,0.1], origin="BOTTOM LEFT", shadow={"blur":3,"color":[0,0,0,0.6],"offset":[2,-2],}):
    """draw fond handler"""

    global AllFonts

    Id = str(len(AllFonts.keys())+1)
    AllFonts[Id]= {"font_id":0, "handler":None,}

    def draw(self, context):
            
        font_id = AllFonts[Id]["font_id"]
    
        #Define X
        if "LEFT" in origin:
            pos_x = position[0]
        elif "RIGHT" in origin:
            pos_x = bpy.context.region.width - position[0]
        #Define Y
        if "BOTTOM" in origin:
            pos_y = position[1]
        elif "TOP" in origin:
            pos_y = bpy.context.region.height - position[1]


        blf.position(font_id, pos_x, pos_y, 0)

        blf.color(font_id, color[0], color[1], color[2], color[3])

        blf.size(font_id, size[0], size[1])

        if shadow is not None:
            blf.enable(font_id, blf.SHADOW)
            blf.shadow(font_id, shadow["blur"], shadow["color"][0], shadow["color"][1], shadow["color"][2], shadow["color"][3])
            blf.shadow_offset(font_id, shadow["offset"][0], shadow["offset"][1])

        blf.draw(font_id, text)

        return None 

    # #try to Load custom font?
    # import os
    # font_path = bpy.path.abspath('//Zeyada.ttf')
    # if os.path.exists(font_path):
    #       AllFonts["font_id"] = blf.load(font_path)
    # else: AllFonts["font_id"] = 0

    #add font handler 
    draw_handler = bpy.types.SpaceNodeEditor.draw_handler_add( draw, (None, None), 'WINDOW', 'POST_PIXEL')
    AllFonts[Id]["handler"] = draw_handler

    return Id


def blf_clear_all_fonts(Id=None):
    """clear all fond appended"""

    global AllFonts

    if (Id is not None): 
        if Id in AllFonts:
            bpy.types.SpaceNodeEditor.draw_handler_remove(AllFonts[Id]["handler"], "WINDOW")
            del AllFonts[Id]
        return None 

    for Id,font in AllFonts.items():
        bpy.types.SpaceNodeEditor.draw_handler_remove(font["handler"], "WINDOW")
    AllFonts.clear()

    return None 


def blf_temporary_msg(text="", size=[], position=[], origin="", color=None, shadow={}, clear_before=True, first_interval=1.0):

    blf_clear_all_fonts()
    Id = blf_add_font(text=text, size=size, position=position, origin=origin, color=color, shadow=shadow)
    def remove_handler_shortly():
        blf_clear_all_fonts(Id)
        return None 
    bpy.app.timers.register(remove_handler_shortly, first_interval=first_interval)

    return None 


def get_dpifac():
    """get user dpi, source: node_wrangler.py"""
    prefs = bpy.context.preferences.system
    return prefs.dpi * prefs.pixel_size / 72


def get_node_at_pos(nodes, context, event, position=None, allow_reroute=True, forbidden=None): #TODO could optimize this function by checking if node visible in current user area
    """get mouse near cursor, 
    source: node_wrangler.py"""

    nodes_near_mouse = []
    nodes_under_mouse = []
    target_node = None

    x, y = position

    # Make a list of each corner (and middle of border) for each node.
    # Will be sorted to find nearest point and thus nearest node
    node_points_with_dist = []

    for n in nodes:
        if (n.type == 'FRAME'):  # no point trying to link to a frame node
            continue
        if (not allow_reroute and n.type=="REROUTE"):
            continue
        if (forbidden is not None) and (n in forbidden):
            continue

        locx, locy = get_node_location(n,nodes)
        dimx, dimy = n.dimensions.x/get_dpifac(), n.dimensions.y/get_dpifac()

        node_points_with_dist.append([n, hypot(x - locx, y - locy)])  # Top Left
        node_points_with_dist.append([n, hypot(x - (locx + dimx), y - locy)])  # Top Right
        node_points_with_dist.append([n, hypot(x - locx, y - (locy - dimy))])  # Bottom Left
        node_points_with_dist.append([n, hypot(x - (locx + dimx), y - (locy - dimy))])  # Bottom Right

        node_points_with_dist.append([n, hypot(x - (locx + (dimx / 2)), y - locy)])  # Mid Top
        node_points_with_dist.append([n, hypot(x - (locx + (dimx / 2)), y - (locy - dimy))])  # Mid Bottom
        node_points_with_dist.append([n, hypot(x - locx, y - (locy - (dimy / 2)))])  # Mid Left
        node_points_with_dist.append([n, hypot(x - (locx + dimx), y - (locy - (dimy / 2)))])  # Mid Right

        continue

    nearest_node = sorted(node_points_with_dist, key=lambda k: k[1])[0][0]

    for n in nodes:
        if (n.type == 'FRAME'):  # no point trying to link to a frame node
            continue
        if (not allow_reroute and n.type=="REROUTE"):
            continue
        if (forbidden is not None) and (n in forbidden):
            continue
            
        locx, locy = get_node_location(n,nodes)
        dimx, dimy = n.dimensions.x/get_dpifac(), n.dimensions.y/get_dpifac()

        if (locx <= x <= locx+dimx) and (locy-dimy <= y <= locy):
            nodes_under_mouse.append(n)

        continue

    if (len(nodes_under_mouse)==1):

        if nodes_under_mouse[0] != nearest_node:
              target_node = nodes_under_mouse[0]  # use the node under the mouse if there is one and only one
        else: target_node = nearest_node  # else use the nearest node
    else:
        target_node = nearest_node

    return target_node



# oooooooooo.                                            oooooooooooo
#  `888'   `Y8b                                           `888'     `8
#   888      888 oooo d8b  .oooo.   oooo oooo    ooo       888         oooo d8b  .oooo.   ooo. .oo.  .oo.    .ooooo.
#   888      888 `888""8P `P  )88b   `88. `88.  .8'        888oooo8    `888""8P `P  )88b  `888P"Y88bP"Y88b  d88' `88b
#   888      888  888      .oP"888    `88..]88..8'         888    "     888      .oP"888   888   888   888  888ooo888
#   888     d88'  888     d8(  888     `888'`888'          888          888     d8(  888   888   888   888  888    .o
#  o888bood8P'   d888b    `Y888""8o     `8'  `8'          o888o        d888b    `Y888""8o o888o o888o o888o `Y8bod8P'



def get_nodes_in_frame_box(boxf, nodes, frame_support=True,):
    """search node that can potentially be inside this boxframe created box"""

    for n in nodes:

        #we do not want information on ourselves
        if ((n==boxf) or (n.parent==boxf)):
            continue

        #for now, completely impossible to get a frame location..
        if (n.type=="FRAME"):
            continue

        locx,locy = get_node_location(n,nodes)

        if boxf.location.x <= locx <= (boxf.location.x + boxf.dimensions.x) and \
           boxf.location.y >= locy >= (boxf.location.y - boxf.dimensions.y):
            yield n


class NOODLER_OT_draw_frame(bpy.types.Operator):

    bl_idname = "noodler.draw_frame"
    bl_label = "Draw Frames"
    bl_options = {'REGISTER'}

    def __init__(self): 

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

        ng , _ = get_active_tree(context)
        self.node_tree = ng

        ensure_mouse_cursor(context, event)
        self.old = context.space_data.cursor_location.copy()  

        boxf = ng.nodes.new("NodeFrame")
        self.boxf = boxf 
        boxf.bl_width_min = boxf.bl_height_min = 20
        boxf.width = boxf.height = 0
        boxf.select = False
        boxf.location = self.old

        noodle_scn = context.scene.noodler
        boxf.use_custom_color = noodle_scn.frame_use_custom_color
        boxf.color = noodle_scn.frame_color
        boxf.label = noodle_scn.frame_label
        boxf.label_size = noodle_scn.frame_label_size

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

            set_all_node_select(self.node_tree.nodes,False)
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

        #dybamic selection:

        #enable every 100ms, too slow for python.. 
        if (event.type != 'TIMER'):
            return {'RUNNING_MODAL'}

        #show user a preview off the future node
        set_all_node_select(self.node_tree.nodes,False)
        for n in get_nodes_in_frame_box(self.boxf,self.node_tree.nodes):
            n.select = True
            continue

        return {'RUNNING_MODAL'}

    def cancel(self, context):

        self.node_tree.nodes.remove(self.boxf)
        set_all_node_select(self.node_tree.nodes,False)

        context.area.tag_redraw()
        context.window_manager.event_timer_remove(self.timer)

        return None 


# oooooooooo.                                            ooooooooo.                             .
# `888'   `Y8b                                           `888   `Y88.                         .o8
#  888      888 oooo d8b  .oooo.   oooo oooo    ooo       888   .d88'  .ooooo.  oooo  oooo  .o888oo  .ooooo.
#  888      888 `888""8P `P  )88b   `88. `88.  .8'        888ooo88P'  d88' `88b `888  `888    888   d88' `88b
#  888      888  888      .oP"888    `88..]88..8'         888`88b.    888   888  888   888    888   888ooo888
#  888     d88'  888     d8(  888     `888'`888'          888  `88b.  888   888  888   888    888 . 888    .o
# o888bood8P'   d888b    `Y888""8o     `8'  `8'          o888o  o888o `Y8bod8P'  `V88V"V8P'   "888" `Y8bod8P'


class NOODLER_OT_draw_route(bpy.types.Operator):

    bl_idname = "noodler.draw_route"
    bl_label = "Draw Reroute Noodle Easily with Shortcut."
    bl_options = {'REGISTER'}

    def __init__(self): 

        self.node_tree = None
        self.init_type = None #Type of the noodle?
        self.init_click = (0,0)
        self.last_click = (0,0)
            
        #"rr"" stands for reroute
        self.old_rr = None 
        self.new_rr = None
        self.created_rr = []

        #wheeling upon active 
        self.from_active = None #if node is active, then we do not create an new reroute to begin with but we use active output and wheel shortcut
        self.wheel_inp = None #if from_active, then we can use wheelie input shortcut before first click to switch outputs easily

        #shift mode 
        self.wheel_out = 0
        self.out_link = None 
        self.nearest = None
        #keep track of if we created inputs on GROUP_OUTPUT type
        self.gr_out_init_len = None

    @classmethod
    def poll(cls, context):
        return (context.space_data.type=='NODE_EDITOR') and (context.space_data.node_tree is not None)

    def bfl_message(self, mode="add"):

        if mode=="add":
              shadow = {"blur":5,"color":[0,0,0,1],"offset":[1,-1],} ; color = [0.9,0.9,0.9,0.9] ; origin = "BOTTOM LEFT" ; size = [25,45]
              blf_add_font(text="[SHFT] Link to node", size=size, position=[20,190], origin=origin, color=color, shadow=shadow)
              blf_add_font(text="[CTRL] Snapping", size=size, position=[20,160], origin=origin, color=color, shadow=shadow)
              blf_add_font(text="[DEL] Backstep", size=size, position=[20,130], origin=origin, color=color, shadow=shadow)
              blf_add_font(text="[LEFTMOUSE] Add reroute/Confirm link", size=size, position=[20,100], origin=origin, color=color, shadow=shadow)
              blf_add_font(text="[ENTER] Confirm reroute", size=size, position=[20,70], origin=origin, color=color, shadow=shadow)
              blf_add_font(text="[MOUSEWHEEL] Loop Sockets", size=size, position=[20,40], origin=origin, color=color, shadow=shadow)
        else: blf_clear_all_fonts(Id=None)

        bpy.context.area.tag_redraw()

        return None 

    def invoke(self, context, event):
        """initialization process"""

        ng , _ = get_active_tree(context)
        nodes = ng.nodes
        self.node_tree = ng

        #create new ng? or starting from an active node? 
        if (nodes.active and nodes.active.select):
              self.from_active = nodes.active
        else: self.from_active = None 

        #do not support frames
        if (self.from_active is not None): 
            if (self.from_active.type=="FRAME"):
                return {'FINISHED'}
            if (len(self.from_active.outputs)==0):
                return {'FINISHED'}

        #store init mouse location
        ensure_mouse_cursor(context, event)
        self.init_click = context.space_data.cursor_location.copy()  

        self.add_reroute(context,event)

        self.bfl_message()

        #start modal 
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def add_reroute(self,context,event):
        """create new/old reroute, or cycle old with new"""

        rr1 = rr2 = None 
        ng = self.node_tree

        #get mouse location
        ensure_mouse_cursor(context, event)
        click_loc = context.space_data.cursor_location.copy()  

        #write initial node/link 

        if (self.old_rr is None):

            #if self.old_rr is None this mean that this is the first time we are running! upon pressing shortcut key
            if (self.from_active is not None):
                    
                #initialize wheelie
                if self.wheel_inp is None:
                    self.wheel_inp = 0

                active_node = self.from_active
                self.old_rr = "Not None"
                outp = active_node.outputs[self.wheel_inp]
                self.init_type = outp.type

                self.last_click = self.from_active.location.copy()
            else:

                #if user didn't selected a node, create an initial reroute
                rr1 = ng.nodes.new("NodeReroute")
                rr1.select = True
                rr1.location = click_loc
                self.old_rr = rr1 
                self.created_rr.append(rr1) #keep track of reroute created 
                outp = rr1.outputs[0]
                self.init_type = outp.type

                self.last_click = rr1.location.copy()

        else: 
            #otherwise old is now new and we switch cycle
            rr1 = self.old_rr = self.new_rr
            outp = rr1.outputs[0]

            self.last_click = rr1.location.copy()

        #register internal click

        rr2 = ng.nodes.new("NodeReroute")
        rr2.select = True
        rr2.location = click_loc
        self.new_rr = rr2 
        self.created_rr.append(rr2) #keep track of reroute created 
        inp = rr2.inputs[0]

        #keep track of reroute created 
        if (rr2 not in self.created_rr):
            self.created_rr.append(rr2)

        #link the two sockets
        ng.links.new(outp,inp)

        #reset selection for visual cue
        set_all_node_select(self.node_tree.nodes,False)
        rr2.select = True

        return None 

    def backstep(self, context):
        """back to precedent reroute"""

        historycount = len(self.created_rr)
        if historycount<2:
            return None 
        
        #remove last 
        last = self.created_rr[-1]
        self.node_tree.nodes.remove(last)
        self.created_rr.remove(last)
        
        #redefine old/new properties & last click position
        self.old_rr = self.created_rr[-2] if (historycount!=2) else self.created_rr[-1]
        self.last_click = self.old_rr.location
        self.new_rr = self.created_rr[-1]

        #reset gui
        set_all_node_select(self.node_tree.nodes,False)
        self.new_rr.select = True

        #if backstep to the init beginning:
        if (len(self.created_rr)==1):

            #cursor back to init 
            self.last_click = self.init_click

            #re-enable wheelie if from active
            if (self.from_active is not None):
                self.wheel_inp = 0
        
        return None 

    def modal(self, context, event):     
        """main state machine"""

        context.area.tag_redraw()

        #if user is holding shift, that means he want to finalize and connect to input, entering a sub modal state.

        if event.shift:

            #initiating the shift mode
            if (event.type=="LEFT_SHIFT" and event.value=="PRESS"):
                #in this sub modal, we do not want reroute anymore, so we'll remove the latest one created upon entering
                if (self.from_active is not None) and (len(self.created_rr)==1):
                    #this can be tricky if we only have one, if from_active we can use the stored input
                    last = self.created_rr[-1]
                    self.node_tree.nodes.remove(last)
                    self.created_rr.remove(last)
                    self.new_rr = self.old_rr = None
                    self.last_click = self.init_click
                else:
                    self.backstep(context)

            if self.out_link:
                #remove created link from previous shift loop
                self.node_tree.links.remove(self.out_link)
                self.out_link = None

            #always reset selection
            set_all_node_select(self.node_tree.nodes,False)

            #get nearest node
            ensure_mouse_cursor(context, event)                
            nearest = get_node_at_pos(self.node_tree.nodes, context, event, position=context.space_data.cursor_location, forbidden=[self.from_active]+self.created_rr,)

            #if switched to a new nearest node:
            if self.nearest != nearest:
                self.nearest = nearest

                #reset wheel loop
                self.wheel_out = 0

                #if we created new slots in group output, reset
                if (self.gr_out_init_len is not None):
                    while len(self.node_tree.outputs)>self.gr_out_init_len:
                        self.node_tree.outputs.remove(self.node_tree.outputs[-1])
                    self.gr_out_init_len = None 

            #find available sockets
            availsock = [ i for i,s in enumerate(nearest.inputs) if (s.is_multi_input or len(s.links)==0) and s.enabled]
            socklen = len(availsock)
            if (socklen==0):
                return {'RUNNING_MODAL'}

            #use wheel to loop to other sockets
            if (event.type=="WHEELDOWNMOUSE"): self.wheel_out = 0 if (self.wheel_out>=socklen-1) else self.wheel_out+1
            elif (event.type=="WHEELUPMOUSE"): self.wheel_out = socklen-1 if (self.wheel_out<=0) else self.wheel_out-1

            #reset selection for visual cue
            self.node_tree.nodes.active = nearest
            nearest.select = True

            #find out sockets
            outp = nearest.inputs[availsock[self.wheel_out]]
            #find input socket, depends if user using initially reroute or active
            if (self.new_rr is not None):
                  inp = self.new_rr.outputs[0] 
            else: inp = self.from_active.outputs[self.wheel_inp]

            #keep track if we created new sockets of an GROUP_OUTPUT type
            if (nearest.type=="GROUP_OUTPUT"):
                if self.gr_out_init_len is None:
                    self.gr_out_init_len = len([s for s in nearest.inputs if s.type!="CUSTOM"])

            #create the link
            out_link = self.node_tree.links.new(inp, outp,)

            #detect if we created a new group output by doing this check
            if (out_link!=self.node_tree.links[-1]):
                  self.out_link = self.node_tree.links[-1] #forced to do so, creating link to output type is an illusion, two links are created in this special case
            else: self.out_link = out_link

            if (event.type=="RET") or ((event.type=="LEFTMOUSE") and (event.value=="PRESS")):

                bpy.ops.ed.undo_push(message="Route Drawing", )
                self.bfl_message(mode="clear")

                return {'FINISHED'}
           
            context.area.tag_redraw()
            return {'RUNNING_MODAL'}

        #upon quitting shift event?

        elif (event.type=="LEFT_SHIFT" and event.value=="RELEASE"):

            #remove created link
            if self.out_link:
                self.node_tree.links.remove(self.out_link)
                self.out_link = None
            
            #reset wheel loop
            self.wheel_out = 0

            #if we created new slots in group output, reset
            if (self.gr_out_init_len is not None):
                while len(self.node_tree.outputs)>self.gr_out_init_len:
                    self.node_tree.outputs.remove(self.node_tree.outputs[-1])
                self.gr_out_init_len = None 

            #restore reroute we removed on shift init
            self.add_reroute(context,event)

            context.area.tag_redraw()
            return {'RUNNING_MODAL'}

        #switch to new reroute? 

        elif (event.type=="LEFTMOUSE") and (event.value=="PRESS"):
                
            #from active mode with wheelie is only for the first run
            if self.wheel_inp: 
                self.wheel_inp = None

            self.add_reroute(context,event)
            return {'RUNNING_MODAL'}           
        
        #from active on init? then we can switch socket output with mouse wheel 

        elif (event.type in ("WHEELUPMOUSE","WHEELDOWNMOUSE")) and (len(self.created_rr)==1):

            socklen = len(self.from_active.outputs)
            if (socklen==0):
                return {'RUNNING_MODAL'}

            if (event.type=="WHEELDOWNMOUSE"): self.wheel_inp = 0 if (self.wheel_inp>=socklen-1) else self.wheel_inp+1
            elif (event.type=="WHEELUPMOUSE"): self.wheel_inp = socklen-1 if (self.wheel_inp<=0) else self.wheel_inp-1

            self.node_tree.links.new(self.from_active.outputs[self.wheel_inp], self.new_rr.inputs[0],)
            return {'RUNNING_MODAL'}    

        #backstep? 

        elif (event.type in ("BACK_SPACE","DEL") or (event.type=="Z" and event.ctrl)) and (event.value=="RELEASE"):
            self.backstep(context)
            return {'RUNNING_MODAL'} 

        #accept & finalize? 

        elif event.type in ("RET","SPACE"):

            for n in self.created_rr:
                n.select = True 

            self.node_tree.nodes.remove(self.new_rr) #just remove last non confirmed reroute
            bpy.ops.ed.undo_push(message="Route Drawing", )
            self.bfl_message(mode="clear")

            return {'FINISHED'}

        #cancel? 

        if event.type in ("ESC","RIGHTMOUSE"):

            #remove all created
            for n in self.created_rr:
                self.node_tree.nodes.remove(n)

            #reset selection to init
            set_all_node_select(self.node_tree.nodes,False)
            if self.from_active:
                self.node_tree.nodes.active = self.from_active
                self.from_active.select = True

            self.bfl_message(mode="clear")

            return {'CANCELLED'}

        #or move newest reroute 
        ensure_mouse_cursor(context, event)
        cursor = context.space_data.cursor_location

        #special ctrl key for 90d snap
        if (event.ctrl):   
            #y constraint? 
            if abs(self.last_click.x-cursor.x)<abs(self.last_click.y-cursor.y):
                  cursor.x = self.last_click.x
            else: cursor.y = self.last_click.y

        rr = self.new_rr
        rr.location = cursor

        return {'RUNNING_MODAL'}


#   .oooooo.   oooo                                     .o88o.
#  d8P'  `Y8b  `888                                     888 `"
# 888           888 .oo.    .oooo.   ooo. .oo.  .oo.   o888oo   .ooooo.  oooo d8b
# 888           888P"Y88b  `P  )88b  `888P"Y88bP"Y88b   888    d88' `88b `888""8P
# 888           888   888   .oP"888   888   888   888   888    888ooo888  888
# `88b    ooo   888   888  d8(  888   888   888   888   888    888    .o  888
#  `Y8bood8P'  o888o o888o `Y888""8o o888o o888o o888o o888o   `Y8bod8P' d888b


def get_rr_links_info(n,mode):
    """get links information from given node, we do all this because we can't store socket object directly, too dangerous, cause bug as object pointer change in memory often"""

    links_info=[]
    is_input = (mode=="IN")

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


def restore_links(n,ng,links_info,mode):
    """restore links from given info list"""

    is_input = (mode=="IN")

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


class NOODLER_OT_chamfer(bpy.types.Operator): 

    #not sure how real bevel algo works, but this is a naive approach, creating new vert, new edges and moving location from origin point
    #note that local/global space can be problematic. here we are only working in local space, if parent. 

    bl_idname = "noodler.chamfer"
    bl_label = "Reroute Chamfer"
    bl_options = {'REGISTER'}

    def __init__(self): 

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
        loc_init_global = get_node_location(n, ng.nodes).copy() 
        #get chamfer direction from
        if (from_sock.node.type=="REROUTE"):
              Chamf.fromvec = get_node_location(from_sock.node, ng.nodes) - loc_init_global
              Chamf.fromvec.normalize()
        else: Chamf.fromvec = Vector((-1,0))
        #get chamfer direction to
        if (to_sock.node.type=="REROUTE"):
              Chamf.tovec = get_node_location(to_sock.node, ng.nodes) - loc_init_global
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

        ng , _ = get_active_tree(context)
        self.node_tree = ng

        #get initial mouse position
        ensure_mouse_cursor(context, event)
        self.init_click = context.space_data.cursor_location.copy()  

        selected = [n for n in ng.nodes if n.select and (n.type=="REROUTE") and not ((len(n.inputs[0].links)==0) or (len(n.outputs[0].links)==0))]
        if (len(selected)==0):
            return {'FINISHED'}

        #save state to data later
        for n in selected: 
            self.init_state[n.name]={"location":n.location.copy(),"IN":get_rr_links_info(n,"IN"),"OUT":get_rr_links_info(n,"OUT")}

        #set selection
        set_all_node_select(self.node_tree.nodes,False)

        #set up chamfer
        for n in selected:
            self.chamfer_setup(n)

        #start modal 
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):     

        context.area.tag_redraw()

        #if user confirm:

        if (event.type in ("LEFTMOUSE","RET","SPACE")):
            bpy.ops.ed.undo_push(message="Reroute Chamfer", )
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
                restore_links(n, self.node_tree, v["IN"], "IN")
                restore_links(n, self.node_tree, v["OUT"], "OUT")
                continue

            context.area.tag_redraw()
            return {'CANCELLED'}

        #else move position of all chamfer items
        
        #get distance data from cursor
        ensure_mouse_cursor(context, event)
        distance = numpy.linalg.norm(context.space_data.cursor_location - self.init_click)
            
        #move chamfer vertex
        for Chamf in self.chamfer_data:
            self.node_tree.nodes.get(Chamf.init_rr).location = Chamf.init_loc_local + ( Chamf.tovec * distance ) #need global to local
            self.node_tree.nodes.get(Chamf.added_rr).location = Chamf.init_loc_local + ( Chamf.fromvec * distance ) #need global to local
            continue

        return {'RUNNING_MODAL'}


# oooooooooo.                                                    .o8
# `888'   `Y8b                                                  "888
#  888      888  .ooooo.  oo.ooooo.   .ooooo.  ooo. .oo.    .oooo888   .ooooo.  ooo. .oo.    .ooooo.  oooo    ooo
#  888      888 d88' `88b  888' `88b d88' `88b `888P"Y88b  d88' `888  d88' `88b `888P"Y88b  d88' `"Y8  `88.  .8'
#  888      888 888ooo888  888   888 888ooo888  888   888  888   888  888ooo888  888   888  888         `88..8'
#  888     d88' 888    .o  888   888 888    .o  888   888  888   888  888    .o  888   888  888   .o8    `888'
# o888bood8P'   `Y8bod8P'  888bod8P' `Y8bod8P' o888o o888o `Y8bod88P" `Y8bod8P' o888o o888o `Y8bod8P'     .8'
#                          888                                                                        .o..P'
#                         o888o                                                                       `Y8P'



def get_dependecies(node, context, mode="upstream or downstream", parent=False):
    """return list of all nodes downstream or upsteam"""

    #determine vars used in recur fct
    is_upstream = (mode=="upstream")
    sockets_api = "outputs" if is_upstream else "inputs"
    link_api = "to_node" if is_upstream else "from_node"
    nodelist = []

    def recur_node(node):
        """gather node in nodelist by recursion"""

        #add note to list 
        nodelist.append(node)

        #frame?
        if (parent and node.parent):
            if (node.parent not in nodelist):
                nodelist.append(node.parent)

        #get sockets 
        sockets = getattr(node,sockets_api)
        if not len(sockets):
            return None 

        #check all outputs
        for socket in sockets:
            for link in socket.links:
                nextnode = getattr(link,link_api)
                if nextnode not in nodelist:
                    recur_node(nextnode)
                continue
            continue
        
        return None 

    recur_node(node)

    return nodelist


class NOODLER_OT_dependency_select(bpy.types.Operator):

    bl_idname = "noodler.dependency_select"
    bl_label = "Select Dependencies With Shortcut"
    bl_options = {'REGISTER', 'UNDO'}

    mode : bpy.props.EnumProperty(default="downstream",items=[("downstream","Downstream","",),("upstream","Upstream","",),], name="Mode") 
    repsel : bpy.props.BoolProperty(default=True, name="Replace Selection")
    frame : bpy.props.BoolProperty(default=False, name="Include Frames")

    @classmethod
    def poll(cls, context):
        return (context.space_data.type=='NODE_EDITOR') and (context.space_data.node_tree is not None)

    def invoke(self, context, event):

        ng , _ = get_active_tree(context)
        ensure_mouse_cursor(context, event)
        node = get_node_at_pos(ng.nodes, context, event, position=context.space_data.cursor_location)
        if node is None:
            return {"CANCELLED"}

        if self.repsel:
            bpy.ops.node.select_all(action="DESELECT")

        deps = get_dependecies(node, context, mode=self.mode, parent=self.frame)
        for n in deps:
            n.select = True

        return {"CANCELLED"}


# ooooooooo.
# `888   `Y88.
#  888   .d88' oooo  oooo  oooo d8b  .oooooooo  .ooooo.
#  888ooo88P'  `888  `888  `888""8P 888' `88b  d88' `88b
#  888          888   888   888     888   888  888ooo888
#  888          888   888   888     `88bod8P'  888    .o
# o888o         `V88V"V8P' d888b    `8oooooo.  `Y8bod8P'
#                                   d"     YD
#                                   "Y88888P'


# def is_node_used(node):
#     """check if node is reaching output"""
            
#     found_output = False
    
#     def recur_node(n):

#         #reached destination? 
#         if (n.type == "GROUP_OUTPUT"):
#             nonlocal found_output
#             found_output = True
#             return 

#         #else continue parcour
#         for out in n.outputs:
#             for link in out.links:
#                 recur_node(link.to_node)

#         return None 
        
#     recur_node(node)

#     return found_output


# def purge_unused_nodes(node_group, delete_muted=True, delete_reroute=True, delete_frame=True):
#     """delete all unused nodes"""
        
#     for n in list(node_group.nodes):
#         #deselct all
#         n.select = False
#         #delete if muted?
#         if (delete_muted==True and n.mute==True):  
#             n.select = True
#             continue 
#         #delete if reroute?
#         if (delete_reroute==True and n.type=="REROUTE"):
#             n.select = True
#             continue               
#         #don't delete if frame?
#         if (delete_frame==False and n.type=="FRAME"):
#             continue 
#         #delete if unconnected
#         if not is_node_used(n):
#             node_group.nodes.remove(n)
#         continue 

#     if delete_muted or delete_reroute:
#         bpy.ops.node.delete_reconnect()
        
#     return None 


# def re_arrange_nodes(node_group, Xmultiplier=1):
#     """re-arrange node by sorting them in X location, (could improve)"""

#     nodes = { n.location.x:n for n in node_group.nodes }
#     nodes = { k:nodes[k] for k in sorted(nodes) }

#     for i,n in enumerate(nodes.values()):
#         n.location.x = i*200*Xmultiplier
#         n.width = 150

#     return None 


# class NOODLER_OT_node_purge_unused(bpy.types.Operator): #context from node editor only

#     bl_idname      = "noodler.node_purge_unused"
#     bl_label       = "Purge Unused Nodes"
#     bl_description = ""
#     bl_options     = {'REGISTER', 'UNDO'}

#     delete_frame   : bpy.props.BoolProperty(default=True, name="Remove Frame(s)",)
#     delete_muted   : bpy.props.BoolProperty(default=True, name="Remove Muted Node(s)",)
#     delete_reroute : bpy.props.BoolProperty(default=True, name="Remove Reroute(s)",)

#     re_arrange : bpy.props.BoolProperty(default=False, name="Re-Arrange Nodes",)
#     re_arrange_fake : bpy.props.BoolProperty(default=False, name="Re-Arrange (not possible with frames)",)

#     def execute(self, context):
#         node_group = context.space_data.node_tree

#         purge_unused_nodes(
#             node_group, 
#             delete_muted=self.delete_muted,
#             delete_reroute=self.delete_reroute,
#             delete_frame=self.delete_frame,
#             )

#         if (self.re_arrange and self.delete_frame):
#             re_arrange_nodes(node_group)

#         return {'FINISHED'}

#     def invoke(self, context, event):
#         return bpy.context.window_manager.invoke_props_dialog(self)

#     def draw(self, context):
#         layout = self.layout 
        
#         #Remove
#         layout.prop(self, "delete_muted")
#         layout.prop(self, "delete_reroute")
#         layout.prop(self, "delete_frame")
        
#         #Re-Arrange
#         if self.delete_frame==True:    
#             layout.prop(self, "re_arrange")
#         else: 
#             re = layout.row()
#             re.enabled = False
#             re.prop(self, "re_arrange_fake")

#         return None 


# ooooo                 .                       .o88o.
# `888'               .o8                       888 `"
#  888  ooo. .oo.   .o888oo  .ooooo.  oooo d8b o888oo   .oooo.    .ooooo.   .ooooo.
#  888  `888P"Y88b    888   d88' `88b `888""8P  888    `P  )88b  d88' `"Y8 d88' `88b
#  888   888   888    888   888ooo888  888      888     .oP"888  888       888ooo888
#  888   888   888    888 . 888    .o  888      888    d8(  888  888   .o8 888    .o
# o888o o888o o888o   "888" `Y8bod8P' d888b    o888o   `Y888""8o `Y8bod8P' `Y8bod8P'


# class NOODLER_PT_tool_search(bpy.types.Panel):

#     bl_idname = "NOODLER_PT_tool_search"
#     bl_label = "Node Search"
#     bl_category = "Noolder"
#     bl_space_type = "NODE_EDITOR"
#     bl_region_type = "UI"

#     def draw(self, context):

#         layout = self.layout
#         noodle_scn = context.scene.noodler
            
#         row = layout.row(align=True)
#         row.prop(noodle_scn,"search_keywords",text="",icon="VIEWZOOM")
#         row.prop(noodle_scn,"search_center",text="",icon="ZOOM_ALL")

#         layout.label(text="Search Filters:")

#         layout.use_property_split = True

#         layout.prop(noodle_scn,"search_labels")
#         layout.prop(noodle_scn,"search_types")
#         layout.prop(noodle_scn,"search_socket_names")
#         layout.prop(noodle_scn,"search_socket_types")
#         layout.prop(noodle_scn,"search_names")
#         layout.prop(noodle_scn,"search_input_only")
#         layout.prop(noodle_scn,"search_frame_only")

#         s = layout.column()
#         s.label(text=f"Found {noodle_scn.search_found} Element(s)")
    
#         return None 


# class NOODLER_PT_tool_color_palette(bpy.types.Panel,BrushPanel):
#     #palette api is a bit bad, it is operatiors designed for unified paint tools
#     #so we are hijacking the context for us then.

#     bl_idname = "NOODLER_PT_tool_color_palette"
#     bl_label = "Assign Palette"
#     bl_category = "Noolder"
#     bl_space_type = "NODE_EDITOR"
#     bl_region_type = "UI"

#     @classmethod
#     def poll(cls, context):
#         return True

#     def draw(self, context):

#         layout = self.layout
#         noodle_scn = context.scene.noodler
#         settings = context.tool_settings.vertex_paint
#         unified = context.tool_settings.unified_paint_settings

#         if settings is None: 
#             col = layout.column()
#             col.active = False
#             col.scale_y = 0.8
#             col.label(text="Please go in vertex-paint to")
#             col.label(text="initiate the palette API.")
#             return None 
        
#         layout.template_ID(settings, "palette", new="palette.new")

#         if settings.palette:
#             row = layout.row(align=True)
#             colo = row.row(align=True)
#             colo.prop(unified,"color",text="")
#             colo.prop(noodle_scn,"palette_prop",text="")

#             row.operator("noodler.reset_color",text="",icon="LOOP_BACK",)
#             layout.template_palette(settings, "palette", color=True,)

#         return None 


# class NOODLER_PT_tool_frame(bpy.types.Panel):

#     bl_idname = "NOODLER_PT_tool_frame"
#     bl_label = "Draw Frame"
#     bl_category = "Noolder"
#     bl_space_type = "NODE_EDITOR"
#     bl_region_type = "UI"

#     def draw(self, context):

#         layout = self.layout
#         noodle_scn = context.scene.noodler
        
#         layout.use_property_split = True

#         layout.prop(noodle_scn,"frame_label")
#         layout.prop(noodle_scn,"frame_label_size")

#         layout.prop(noodle_scn,"frame_use_custom_color")
#         col = layout.column()
#         col.prop(noodle_scn,"frame_sync_color")
#         col.active = noodle_scn.frame_use_custom_color
#         col.prop(noodle_scn,"frame_color")
        
#         return None 


class NOODLER_PF_node_framer(bpy.types.AddonPreferences):
    bl_idname = __name__

    def draw(self, context):

        layout = self.layout

        kc = bpy.context.window_manager.keyconfigs.addon

        #draw shortcuts items:
        for km, kmi, name, icon in addon_keymaps:
            #tweaked snippets from `rna_keymap_ui.py`

            col = layout.column(align=True)

            row = col.box().row()
            row.label(text=name, icon=icon,)
            row.prop(kmi,"active",text="",emboss=False,)

            if not kmi.active:
                continue

            box = col.box()
            split = box.split(factor=0.4)
            sub = split.row()

            if km.is_modal:
                  sub.prop(kmi, "propvalue", text="")
            else: sub.prop(kmi, "idname", text="")

            if kmi.map_type not in {'TEXTINPUT', 'TIMER'}:

                sub = split.column()
                subrow = sub.row(align=True)

                if (kmi.map_type=='KEYBOARD'):

                    subrow.prop(kmi, "type", text="", event=True)
                    subrow.prop(kmi, "value", text="")
                    subrow_repeat = subrow.row(align=True)
                    subrow_repeat.active = kmi.value in {'ANY', 'PRESS'}
                    subrow_repeat.prop(kmi, "repeat", text="Repeat", toggle=True)

                elif kmi.map_type in {'MOUSE', 'NDOF'}:

                    subrow.prop(kmi, "type", text="")
                    subrow.prop(kmi, "value", text="")

                subrow = box.row()
                mainkey = subrow.row()
                mainkey.scale_x = 1.3
                mainkey.separator(factor=0.2)
                #subrow.prop(kmi, "any", text="Any",) #what's the use of this? 
                mainkey.prop(kmi, "shift", text="",icon="EVENT_SHIFT")
                mainkey.prop(kmi, "ctrl", text="",icon="EVENT_CTRL")
                mainkey.prop(kmi, "alt", text="",icon="EVENT_ALT")
                mainkey.prop(kmi, "oskey", text="",icon="EVENT_OS")

                keymod = subrow.row(align=True)
                keymod.alignment = "RIGHT"
                keymod.scale_x = 2
                keymod.label(text="KeyMod:")
                keymod.prop(kmi, "key_modifier", text="", event=True)

            # Operator properties
            box.template_keymap_item_properties(kmi)

            # Modal key maps attached to this operator
            if not km.is_modal:
                kmm = kc.keymaps.find_modal(kmi.idname)
                if kmm:
                    draw_km(addon_keymaps, kc, kmm, None, layout, level + 1)
                    layout.context_pointer_set("keymap", km)

            continue
        
        return None 


# class NOODLER_PT_shortcuts_memo(bpy.types.Panel):

#     bl_idname = "NOODLER_PT_shortcuts_memo"
#     bl_label = "Default Shortcuts"
#     bl_category = "Noolder"
#     bl_space_type = "NODE_EDITOR"
#     bl_region_type = "UI"

#     def draw(self, context):

#         layout = self.layout
        
#         lbl = layout.column()
            
#         row = lbl.row()
#         row.separator(factor=0.5)
#         rol = row.column()
#         rol.scale_y = 0.9

#         ro = rol.column(align=True)
#         ro.label(text="Loop Favorites:")
#         ro.box().label(text="Y")
        
#         rol.separator()

#         ro = rol.column(align=True)
#         ro.label(text="Add Favorite:")
#         ro.box().label(text="CTRL+Y")
            
#         rol.separator()

#         ro = rol.column(align=True)
#         ro.label(text="Draw Reroute:")
#         ro.box().label(text="V")
        
#         rol.separator()

#         ro = rol.column(align=True)
#         ro.label(text="Draw Frame:")
#         ro.box().label(text="PRESS J")
        
#         rol.separator()

#         ro = rol.column(align=True)
#         ro.label(text="Reroute Chamfer:")
#         ro.box().label(text="CTRL+B")
        
#         rol.separator()

#         ro = rol.column(align=True)
#         ro.label(text="Select Downstream:")
#         ro.box().label(text="CTRL+LEFTMOUSE")
        
#         rol.separator()

#         ro = rol.column(align=True)
#         ro.label(text="Select Upstream:")
#         ro.box().label(text="CTRL+ALT+LEFTMOUSE")

#         rol.separator()

#         ro = rol.column(align=True)
#         ro.label(text="Purge Unused Nodes in Header")

#         return None 


# ooooooooo.             oooo                .       .
# `888   `Y88.           `888              .o8     .o8
#  888   .d88'  .oooo.    888   .ooooo.  .o888oo .o888oo  .ooooo.
#  888ooo88P'  `P  )88b   888  d88' `88b   888     888   d88' `88b
#  888          .oP"888   888  888ooo888   888     888   888ooo888
#  888         d8(  888   888  888    .o   888 .   888 . 888    .o
# o888o        `Y888""8o o888o `Y8bod8P'   "888"   "888" `Y8bod8P'


#color palette api is completely broken, it only works with paint tools..
#we need to check if context is node editor and and find active nodetree from msgbus function.. 
#the problem is that context is not accessible from message bus, the following code is a workaround

mouse_coord = (0,0) 

class NOODLER_OT_get_mouse_location(bpy.types.Operator):

    bl_idname = "noodler.get_mouse_location"
    bl_label = ""
    bl_options = {'REGISTER'}

    def invoke(self, context, event): #How about we have bpy.context.event instead of this workaround ? hu? 

        global mouse_coord
        mouse_coord = event.mouse_x,event.mouse_y

        return {'FINISHED'}


class NOODLER_OT_reset_color(bpy.types.Operator, ):

    bl_idname = "noodler.reset_color"
    bl_label = "Reset Color"
    bl_description = "Reset Color"
        
    def execute(self, context, ):
        
        ng , _ = get_active_tree(context)
        for n in ng.nodes:
            if n.select:
                n.use_custom_color = False

        return {'FINISHED'}


def palette_callback(*args):
    """execute this function everytime user is clicking on a palette color""" 
    #bpy.ops.noodler.reset_color()

    bpy.ops.noodler.get_mouse_location(('INVOKE_DEFAULT'))
    global mouse_coord

    space = get_space_from_mouse(mouse_coord[0], mouse_coord[1])
    if (space is None) or (space.type!="NODE_EDITOR"):
        return None 

    if not bpy.context.scene.tool_settings.unified_paint_settings.use_unified_color:
        bpy.context.scene.tool_settings.unified_paint_settings.use_unified_color = True 
    palette_color = bpy.context.tool_settings.unified_paint_settings.color

    noodle_scn = bpy.context.scene.noodler
    noodle_scn.palette_prop = list(palette_color)[:3]
    if noodle_scn.frame_sync_color:
        noodle_scn.frame_color = list(palette_color)[:3]

    ng = space.node_tree
    for n in ng.nodes:
        if n.select:
            n.use_custom_color=True
            n.color = palette_color

    return None 


def palette_prop_upd(self, context):

    if context.space_data is None:
        return None 
        
    ng , _ = get_active_tree(context)
    for n in ng.nodes:
        if n.select:
            if not n.use_custom_color:
                n.use_custom_color = True
            n.color = self.palette_prop

    return None 


@bpy.app.handlers.persistent
def noodler_load_post(scene,desp): 
    
    print(f"noodler_load_post")
    
    bpy.msgbus.subscribe_rna(
        key=bpy.types.PaletteColor,#get notified when active color change
        owner=palette_msgbus_owner,
        notify=palette_callback,
        args=(bpy.context,),
        options={"PERSISTENT"},
        )

    return None


# oooooooooooo                                           o8o      .
# `888'     `8                                           `"'    .o8
#  888          .oooo.   oooo    ooo  .ooooo.  oooo d8b oooo  .o888oo  .ooooo.
#  888oooo8    `P  )88b   `88.  .8'  d88' `88b `888""8P `888    888   d88' `88b
#  888    "     .oP"888    `88..8'   888   888  888      888    888   888ooo888
#  888         d8(  888     `888'    888   888  888      888    888 . 888    .o
# o888o        `Y888""8o     `8'     `Y8bod8P' d888b    o888o   "888" `Y8bod8P'

#\u2605=★


# def get_favorites(nodes, index=None):

#     favs = []

#     for n in nodes:
#         if n.name.startswith("★"):
#             favs.append(n)
#         continue

#     def namesort(elem):
#         return elem.name
#     favs.sort(key=namesort)

#     if (index is not None):
#         for i,n in enumerate(favs):
#             if (i==index):
#                 return n
#         return None 

#     return favs


# def favorite_index_upd(self, context):

#     ng , _ = get_active_tree(context)

#     n = get_favorites(ng.nodes, index=self.favorite_index)
#     if n is None:
#         return None 

#     set_all_node_select(ng.nodes, False,)
#     n.select = True 

#     override = bpy.context.copy()
#     override["area"] = context.area
#     override["space"] = context.area.spaces[0]
#     override["region"] = context.area.regions[3]
#     bpy.ops.node.view_selected((override))
        
#     return None


# class NOODLER_OT_favorite_add(bpy.types.Operator):

#     bl_idname      = "noodler.favorite_add"
#     bl_label       = "Add favorites reroute"
#     bl_description = "Add favorites reroute"

#     def invoke(self, context, event):

#         ng = context.space_data.node_tree
#         noodle_scn = context.scene.noodler

#         idx = 1
#         name = f"★{idx:02}"
#         while name in [n.name for n in ng.nodes]:
#             idx +=1
#             name = f"★{idx:02}"

#         if (idx>50):
#             popup_menu([f"You reached {idx-1} favorites.","Sorry mate. It's for your own good.",],"Congratulation!","FUND")
#             return {"FINISHED"}

#         sh = ng.nodes.new("NodeReroute")
#         sh.name = sh.label = name
#         sh.inputs[0].display_shape = "SQUARE"
#         #hide? 
#         #sh.inputs[0].enabled = False 
#         ensure_mouse_cursor(context, event)
#         sh.location = context.space_data.cursor_location

#         blf_temporary_msg(text=f"Added Favorite '{sh.label}'", size=[25,45], position=[20,20], origin="BOTTOM LEFT", color=[0.9,0.9,0.9,0.9], shadow={"blur":3,"color":[0,0,0,0.4],"offset":[2,-2],})
#         context.area.tag_redraw()

#         return {"FINISHED"}


# class NOODLER_OT_favorite_loop(bpy.types.Operator):

#     bl_idname      = "short.favorite_loop"
#     bl_label       = "Loop over favorites"
#     bl_description = "Loop over favorites"

#     def execute(self, context):

#         ng = context.space_data.node_tree
#         noodle_scn = context.scene.noodler

#         favs = get_favorites(ng.nodes)
#         favs_len = len(favs)

#         if (favs_len==0):

#             blf_temporary_msg(text=f"No Favorites Found", size=[25,45], position=[20,20], origin="BOTTOM LEFT", color=[0.9,0.9,0.9,0.9], shadow={"blur":3,"color":[0,0,0,0.4],"offset":[2,-2],})
#             context.area.tag_redraw()

#             return {"FINISHED"}

#         index = noodle_scn.favorite_index
#         if noodle_scn.favorite_index>=(favs_len-1):
#               noodle_scn.favorite_index = 0
#         else: noodle_scn.favorite_index += 1

#         sh = get_favorites(ng.nodes, index=noodle_scn.favorite_index)
#         ng.nodes.active = sh 

#         blf_temporary_msg(text=f"Looping to Favorite '{sh.label}'", size=[25,45], position=[20,20], origin="BOTTOM LEFT", color=[0.9,0.9,0.9,0.9], shadow={"blur":3,"color":[0,0,0,0.4],"offset":[2,-2],})
#         context.area.tag_redraw()

#         return {"FINISHED"}


#  .oooooo..o                                        oooo
# d8P'    `Y8                                        `888
# Y88bo.       .ooooo.   .oooo.   oooo d8b  .ooooo.   888 .oo.
#  `"Y8888o.  d88' `88b `P  )88b  `888""8P d88' `"Y8  888P"Y88b
#      `"Y88b 888ooo888  .oP"888   888     888        888   888
# oo     .d8P 888    .o d8(  888   888     888   .o8  888   888
# 8""88888P'  `Y8bod8P' `Y888""8o d888b    `Y8bod8P' o888o o888o


def search_upd(self, context):
    """search in context nodetree for nodes"""

    ng , _ = get_active_tree(context)

    keywords = self.search_keywords.lower().replace(","," ").split(" ")
    keywords = set(keywords)

    def is_matching(keywords,terms):
        matches = []
        for k in keywords:
            for t in terms:
                matches.append(k in t)
        return any(matches) 

    found = []
    for n in ng.nodes:
        terms = []

        if self.search_labels:
            name = n.label.lower()
            if not name:
                name = n.bl_label.lower()
            terms += name.split(" ")

        if self.search_types:
            terms += n.type.lower().split(" ")

        if self.search_names:
            name = n.name + " " + n.bl_idname
            terms += name.replace("_"," ").lower().split(" ")

        if self.search_socket_names:
            for s in [*list(n.inputs),*list(n.outputs)]:
                name = s.name.lower() 
                if name not in terms:
                    terms += name.split(" ")

        if self.search_socket_types:
            for s in [*list(n.inputs),*list(n.outputs)]:
                name = s.type.lower() 
                if name not in terms:
                    terms += name.split(" ")

        if not is_matching(keywords,terms):
            continue

        found.append(n)

        continue

    set_all_node_select(ng.nodes, False,)

    self.search_found = len(found)
    if (self.search_found==0):
        return None

    if self.search_input_only:
        for n in found.copy():
            if (len(n.inputs)==0 and (n.type!="FRAME")):
                continue
            found.remove(n)
            continue

    if self.search_frame_only:
        for n in found.copy():
            if (n.type!="FRAME"):
                found.remove(n)
            continue

    for n in found:
        n.select = True 

    if self.search_center:

        #from prop update,need some context override

        override = bpy.context.copy()
        override["area"] = context.area
        override["space"] = context.area.spaces[0]
        override["region"] = context.area.regions[3]
        bpy.ops.node.view_selected((override))
    
    return None


# ooooooooo.
# `888   `Y88.
#  888   .d88' oooo d8b  .ooooo.  oo.ooooo.   .oooo.o
#  888ooo88P'  `888""8P d88' `88b  888' `88b d88(  "8
#  888          888     888   888  888   888 `"Y88b.
#  888          888     888   888  888   888 o.  )88b
# o888o        d888b    `Y8bod8P'  888bod8P' 8""888P'
#                                  888
#                                 o888o


# class NOODLER_PR_scene(bpy.types.PropertyGroup): 
#     """noodle_scn = bpy.context.scene.noodler"""

#     frame_use_custom_color: bpy.props.BoolProperty(default=False,name="Frame Color")
#     frame_color: bpy.props.FloatVectorProperty(default=(0,0,0),subtype="COLOR",name="Color")
#     frame_sync_color: bpy.props.BoolProperty(default=True,name="Sync Color",description="Synchronize with palette") 
#     frame_label: bpy.props.StringProperty(default=" ",name="Label")
#     frame_label_size: bpy.props.IntProperty(default=16,min=0,name="Label Size")

#     palette_prop: bpy.props.FloatVectorProperty(default=(0,0,0),subtype="COLOR",name="Color",update=palette_prop_upd)

#     search_keywords: bpy.props.StringProperty(default=" ",name="Keywords",update=search_upd)
#     search_center: bpy.props.BoolProperty(default=True,name="Recenter View",update=search_upd) 
#     search_labels: bpy.props.BoolProperty(default=True,name="Label",update=search_upd)
#     search_types: bpy.props.BoolProperty(default=True,name="Type",update=search_upd)
#     search_names: bpy.props.BoolProperty(default=False,name="Internal Name",update=search_upd)
#     search_socket_names: bpy.props.BoolProperty(default=False,name="Socket Names",update=search_upd)
#     search_socket_types: bpy.props.BoolProperty(default=False,name="Socket Types",update=search_upd)
#     search_input_only: bpy.props.BoolProperty(default=False,name="Input Only",update=search_upd)
#     search_frame_only: bpy.props.BoolProperty(default=False,name="Frame Only",update=search_upd)
#     search_found: bpy.props.IntProperty(default=0)

#     favorite_index : bpy.props.IntProperty(default=0,update=favorite_index_upd,)


# ooooooooo.                         o8o               .
# `888   `Y88.                       `"'             .o8
#  888   .d88'  .ooooo.   .oooooooo oooo   .oooo.o .o888oo  .ooooo.  oooo d8b
#  888ooo88P'  d88' `88b 888' `88b  `888  d88(  "8   888   d88' `88b `888""8P
#  888`88b.    888ooo888 888   888   888  `"Y88b.    888   888ooo888  888
#  888  `88b.  888    .o `88bod8P'   888  o.  )88b   888 . 888    .o  888
# o888o  o888o `Y8bod8P' `8oooooo.  o888o 8""888P'   "888" `Y8bod8P' d888b
#                        d"     YD
#                        "Y88888P'


palette_msgbus_owner = object()

addon_keymaps = []

# entry: (identifier, key, action, CTRL, SHIFT, ALT, props, name, icon, enable) props: ( (property name, property value), )

kmi_defs = ( 
    ( NOODLER_OT_draw_route.bl_idname,        "V",         "PRESS", False, False, False, (),                                       "Operator: Draw Route",              "TRACKING",  True,  ),
    ( NOODLER_OT_draw_frame.bl_idname,        "J",         "PRESS", False, False, False, (),                                       "Operator: Draw Frame",              "ALIGN_TOP", True,  ),
    ( NOODLER_OT_chamfer.bl_idname,           "B",         "PRESS", True,  False, False, (),                                       "Operator: Reroute Chamfer",         "MOD_BEVEL", True,  ),
    ( NOODLER_OT_favorite_loop.bl_idname,     "Y",         "PRESS", False, False, False, (),                                       "Operator: Loop Favorites",          "SOLO_OFF",  True,  ),
    ( NOODLER_OT_favorite_add.bl_idname,      "Y",         "PRESS", True,  False, False, (),                                       "Operator: Add Favorite",            "SOLO_OFF",  True,  ),
    ( NOODLER_OT_dependency_select.bl_idname, "LEFTMOUSE", "PRESS", True,  False, False, (("mode","downstream"),("repsel",True )), "Operator: Select Downstream",       "BACK",      True,  ),
    ( NOODLER_OT_dependency_select.bl_idname, "LEFTMOUSE", "PRESS", True,  True,  False, (("mode","downstream"),("repsel",False)), "Operator: Select Downstream (Add)", "BACK",      False, ),
    ( NOODLER_OT_dependency_select.bl_idname, "LEFTMOUSE", "PRESS", True,  False, True,  (("mode","upstream"),  ("repsel",True )), "Operator: Select Upsteam",          "FORWARD",   True,  ),
    ( NOODLER_OT_dependency_select.bl_idname, "LEFTMOUSE", "PRESS", True,  True,  True,  (("mode","upstream"),  ("repsel",False)), "Operator: Select Upsteam (Add)",    "FORWARD",   False, ),
    )

classes = (
    NOODLER_PF_node_framer,

    NOODLER_PT_tool_search,
    NOODLER_PT_tool_color_palette,
    NOODLER_PT_tool_frame,
    NOODLER_PT_shortcuts_memo,

    NOODLER_PR_scene,

    NOODLER_OT_get_mouse_location,
    NOODLER_OT_reset_color,

    NOODLER_OT_draw_route,
    NOODLER_OT_draw_frame,
    NOODLER_OT_chamfer,

    NOODLER_OT_favorite_add,
    NOODLER_OT_favorite_loop,

    NOODLER_OT_dependency_select,

    NOODLER_OT_node_purge_unused,
    )


# def node_purge_unused_menu(self, context):
#     """extend menu"""
    
#     layout = self.layout 
#     layout.separator()
#     layout.operator("noodler.node_purge_unused", text="Purge Unused Nodes",)

#     return None


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    #extend header menu
    bpy.types.NODE_MT_node.append(node_purge_unused_menu)

    #properties
    bpy.types.Scene.noodler = bpy.props.PointerProperty(type=NOODLER_PR_scene)

    #color palette update
    bpy.msgbus.subscribe_rna(
        key=bpy.types.PaletteColor,#get notified when active color change
        owner=palette_msgbus_owner,
        notify=palette_callback,
        args=(bpy.context,),
        options={"PERSISTENT"},
        )

    #load post update for palette msgbus, unfortunately, not so 'persistent'
    bpy.app.handlers.load_post.append(noodler_load_post)

    #keymaps
    addon_keymaps.clear()
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="Node Editor", space_type="NODE_EDITOR")
        for (identifier, key, action, CTRL, SHIFT, ALT, props, name, icon, enable) in kmi_defs:
            kmi = km.keymap_items.new(identifier, key, action, ctrl=CTRL, shift=SHIFT, alt=ALT)
            kmi.active = enable
            if props:
                for prop, value in props:
                    setattr(kmi.properties, prop, value)
            addon_keymaps.append((km, kmi, name, icon))


def unregister():

    #keymaps
    for km, kmi, _, _ in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    #remove handler 
    bpy.app.handlers.load_post.remove(noodler_load_post)
    
    #color palette update
    bpy.msgbus.clear_by_owner(palette_msgbus_owner)

    #properties 
    del bpy.types.Scene.noodler 

    #extend header menu 
    bpy.types.NODE_MT_node.remove(node_purge_unused_menu)

    #classes
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()