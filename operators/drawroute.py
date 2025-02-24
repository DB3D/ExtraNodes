# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy

from ..utils.node_utils import get_nearest_node_at_position
from ..utils.draw_utils import ensure_mouse_cursor


def get_next_itm_after_active(itter, active=None, step=1):
    """get the next element from a list after active, loop back to first if last one"""
    assert active in itter
    index = itter.index(active)
    next_index = (index + step) % len(itter)
    return itter[next_index]


class NODEBOOSTER_OT_draw_route(bpy.types.Operator):

    #TODO could propose shift a menu when done just like link operation
    #TODO what if user want to link right to left direction?
    #TODO need to support new panel functionality for nodes, only for latest blender version tho, don't think it was there for 4.2
    
    bl_idname = "nodebooster.draw_route"
    bl_label = "Draw Reroute Pathways"
    bl_options = {'REGISTER'}

    def __init__(self, *args, **kwargs):
        """define modal variables"""
        
        super().__init__(*args, **kwargs)
        
        #We only store blender data here when the operator is active, we should be totally fine!
        self.node_tree = None
        self.init_type = None #Type of the noodle?
        self.init_click = (0,0)
        self.last_click = (0,0)

        #keeps track of reroutes
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
        self.tmp_custom_sock_links = None

        self.footer_active = None #'main|shift'
        self.footer_main = '    |    '.join([ 
            "'Esc' = Cancel",
            "'Enter' = Confirm",
            "'Left-Mouse' = Add Reroute",
            "'Del' = Backstep",
            "'Shift' = Link to Nearest Node",
            "'Ctrl' = Snap",
            "'Mouse-Wheel' = Loop Sockets",
            ])
        self.footer_shift = '    |    '.join([ 
            "'Release Shift' = Cancel",
            "'Enter' or 'Left-Mouse' = Confirm",
            "'Mouse-Wheel' = Loop Sockets",
            ])
        
    @classmethod
    def poll(cls, context):
        return (context.space_data.type=='NODE_EDITOR') and (context.space_data.node_tree is not None)

    def invoke(self, context, event):
        """initialization process"""

        ng = context.space_data.edit_tree
        self.node_tree = ng

        #create new ng? or starting from an active node? 
        if (ng.nodes.active and ng.nodes.active.select):
              self.from_active = ng.nodes.active
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

        #add an initial reroute
        self.add_reroute(context,event)

        #Write status bar
        context.workspace.status_text_set_internal(self.footer_main)
        # context.area.tag_redraw()
        
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
                if (self.wheel_inp is None):
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
        for n in self.node_tree.nodes:
            n.select = False
        rr2.select = True

        return None 

    def backstep(self, context):
        """back to precedent reroute"""

        historycount = len(self.created_rr)
        if (historycount<2):
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
        for n in self.node_tree.nodes:
            n.select = False
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

        # try:

        #make sure message is correct
        if (self.footer_active!='main'):
            context.workspace.status_text_set_internal(self.footer_main)
            self.footer_active = 'main'
        # context.area.tag_redraw()

        #if user is holding shift, that means he want to finalize and connect to input, entering a sub modal state.

        if (event.shift):

            #make sure message is correct
            if (self.footer_active!='shift'):
                context.workspace.status_text_set_internal(self.footer_shift)
                self.footer_active = 'shift'
                # context.area.tag_redraw()
            
            #initiating the shift mode, when user press for the first time
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

            if (self.out_link):
                #remove created link from previous shift loop
                self.node_tree.links.remove(self.out_link)
                self.out_link = None

            #always reset selection
            for n in self.node_tree.nodes:
                n.select = False
            
            #get nearest node
            ensure_mouse_cursor(context, event)                
            nearest = get_nearest_node_at_position(self.node_tree.nodes, context, event,
                position=context.space_data.cursor_location, forbidden=[self.from_active]+self.created_rr,)

            #if switched to a new nearest node:
            if (self.nearest != nearest):
                self.nearest = nearest

                #reset wheel loop
                self.wheel_out = 0

                #if we created new slots in group output, reset
                if (self.gr_out_init_len is not None):
                    #HERE
                    print("111111")
                    # while len(self.node_tree.outputs)>self.gr_out_init_len:
                    #     self.node_tree.outputs.remove(self.node_tree.outputs[-1])
                    # self.gr_out_init_len = None 

            #find available sockets
            availsock = [ i for i,s in enumerate(nearest.inputs) if (s.is_multi_input or len(s.links)==0) and s.enabled]
            socklen = len(availsock)
            if (socklen==0):
                return {'RUNNING_MODAL'}

            #use wheel to loop to other sockets
            match event.type:
                case 'WHEELDOWNMOUSE':
                    self.wheel_out = 0 if (self.wheel_out>=socklen-1) else self.wheel_out+1
                case 'WHEELUPMOUSE':
                    self.wheel_out = socklen-1 if (self.wheel_out<=0) else self.wheel_out-1

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
            if ((nearest.type=="GROUP_OUTPUT") and (self.gr_out_init_len is None)):
                self.gr_out_init_len = len([s for s in nearest.inputs if s.type!="CUSTOM"])

            #create the link
            out_link = self.node_tree.links.new(inp, outp,)

            #detect if we created a new group output by doing this check
            if (out_link!=self.node_tree.links[-1]):
                self.out_link = self.node_tree.links[-1] #forced to do so, creating link to output type is an illusion, two links are created in this special case
            else: self.out_link = out_link

            if (event.type=="RET") or ((event.type=="LEFTMOUSE") and (event.value=="PRESS")):
                
                bpy.ops.ed.undo_push(message="Route Drawing", )
                context.workspace.status_text_set_internal(None)
                return {'FINISHED'}
        
            # context.area.tag_redraw()
            return {'RUNNING_MODAL'}

        #upon quitting shift event?

        elif (event.type=="LEFT_SHIFT" and event.value=="RELEASE"):

            #remove created link
            if (self.out_link):
                self.node_tree.links.remove(self.out_link)
                self.out_link = None
            
            #reset wheel loop
            self.wheel_out = 0

            #if we created new slots in group output, reset
            if (self.gr_out_init_len is not None):
                
                #HERE
                print("222222")
                # while (len(self.node_tree.outputs)>self.gr_out_init_len):
                #     self.node_tree.outputs.remove(self.node_tree.outputs[-1])
                # self.gr_out_init_len = None 

            #restore reroute we removed on shift init
            self.add_reroute(context,event)

            # context.area.tag_redraw()
            return {'RUNNING_MODAL'}

        #switch to new reroute? 

        elif (event.type=="LEFTMOUSE" and event.value=="PRESS"):

            #from active mode with wheelie is only for the first run
            if (self.wheel_inp): 
                self.wheel_inp = None

            self.add_reroute(context,event)
            return {'RUNNING_MODAL'}           
        
        #swap socket of initial node the first node user used

        elif (event.type in {"WHEELUPMOUSE","WHEELDOWNMOUSE"}) and (len(self.created_rr)==1):

            avail_socks = [s for s in self.from_active.outputs if not s.is_unavailable]
            if (not avail_socks):
                return {'RUNNING_MODAL'}

            rr_socket = self.new_rr.inputs[0]
            current_sock = rr_socket.links[0].from_socket

            #loop socket
            direction = 1 if (event.type=='WHEELDOWNMOUSE') else -1
            new_sock = get_next_itm_after_active(avail_socks, active=current_sock, step=direction,)

            #keep in track of the wheel input index
            self.wheel_inp = self.from_active.outputs[:].index(new_sock)

            #we need to remove previous links of cuystom outputs
            if (self.from_active.type=='GROUP_INPUT'):
                for l in rr_socket.links:
                    if (l.from_socket.type!=current_sock and l.from_socket.type=='CUSTOM'):
                        self.node_tree.links.remove(l)
                
            #make the link
            self.node_tree.links.new(new_sock, rr_socket,)
            return {'RUNNING_MODAL'}

        #backstep? 

        elif (event.type in {"BACK_SPACE","DEL"} or (event.type=="Z" and event.ctrl)) and (event.value=="RELEASE"):
            self.backstep(context)
            return {'RUNNING_MODAL'} 

        #accept & finalize? 

        elif (event.type in {"RET","SPACE"}):
            
            #we select all rr we created
            for n in self.created_rr:
                n.select = True 
                
            #just remove last non confirmed reroute
            self.node_tree.nodes.remove(self.new_rr)
            
            bpy.ops.ed.undo_push(message="Route Drawing", )
            context.workspace.status_text_set_internal(None)
            return {'FINISHED'}

        #cancel? 

        if (event.type in {"ESC","RIGHTMOUSE"}):

            #remove all created
            for n in self.created_rr:
                self.node_tree.nodes.remove(n)

            #reset selection to init
            for n in self.node_tree.nodes:
                n.select = False
            
            if (self.from_active):
                self.node_tree.nodes.active = self.from_active
                self.from_active.select = True

            context.workspace.status_text_set_internal(None)
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
    
        # except Exception as e:
        #     print(e)
        #     context.workspace.status_text_set_internal(None)
        #     self.report({'ERROR'},"An Error Occured during DrawRoute modal")
        #     return {'CANCELLED'}
            
        return {'RUNNING_MODAL'}