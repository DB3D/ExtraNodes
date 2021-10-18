
# Copyright (C) 2021 'BD3D DIGITAL DESIGN, SLU'
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


bl_info = {
    "name":"'Sequencer Volume' for Geometry-Node",
    "author":"BD3D",
    "description":"This plugin add an extra node for Geometry-Node that will evaluate the sequencer audio volume",
    "blender":(3,0,0),
    "version": (1,0,0),
    "location":"Node Editor > Geometry Node > Add Menu > Extra",
    "warning":"",
    "tracker_url": "https://devtalk.blender.org/t/extra-nodes-for-geometrynodes/20942",
    "category":"Node",
    }

"""

# About creating GeometryNodeCustomGroup:

>Here are the possibilities: 
    - you can either create a custom interface that interact with a nodegroup
    - or create simple input node, this plugin is only creating input values. all boiler plate below is dedicated to output sockets. 

> if you want to process data, forget about it:
   - currently there's no way to get the value out of a socket, not sure how they could translate field to python.
   - writing simple output value is possible, forget about fields tho.    

> update management is not ideal
   - socket_value_update() function should send us signal when a socket value is being updated, the api is dead for now
   - to update, rely on handlers or msgbus ( https://docs.blender.org/api/blender2.8/bpy.app.handlers.html?highlight=handler#module-bpy.app.handlers )

> socket.type is read only, everything is hardcoded in operators
   - to change socket type, we forced to use operator `bpy.ops.node.tree_socket_change_type(in_out='IN', socket_type='')` + context 'override'. this is far from ideal. 
     this means that changing socket type outside the node editor context is not possible. 

> in order to change the default value of an output, nodegroup.outputs[n].default value won't work use, api is confusing, it is done via the nodegroup.nodes instead: 
    - nodegroup.nodes["Group Output"].inputs[n].default_value  ->see boiler plate functions i wrote below

> Warning `node_groups[x].outputs.new("NodeSocketBool","test")` is tricky, type need to be exact, no warning upon error, will just return none


About this script:

>You will note that there is an extra attention to detail in order to not register handlers twice

>You will note that there is an extra attention in the extension of the Add menu with this new 'Extra' category. 
   In, my opinion all plugin nodes should be in this "Extra" menu. 
   Feel free to reuse the menu registration snippets so all custom node makers can share the 'Extra' menu without confilcts.  

"""

import bpy



##################################################
# BOILER PLATE
##################################################



def get_socket_value(ng, idx):
    return ng.nodes["Group Output"].inputs[idx].default_value

def set_socket_value(ng, idx, value=None,):
    ng.nodes["Group Output"].inputs[idx].default_value = value 
    return ng.nodes["Group Output"].inputs[idx].default_value

def set_socket_label(ng, idx, label=None,):
    ng.outputs[idx].name = str(label) 
    return None  

def get_socket_type(ng, idx):
    return ng.outputs[idx].type

def set_socket_type(ng, idx, socket_type="NodeSocketFloat"):
    """set socket type via bpy.ops.node.tree_socket_change_type() with manual override, context MUST be the geometry node editor"""

    snode = bpy.context.space_data
    if snode is None:
       return None 
            
    #forced to do a ugly override like this... eww
    restore_override = { "node_tree":snode.node_tree, "pin":snode.pin, }
    snode.pin = True 
    snode.node_tree = ng
    ng.active_output = idx
    bpy.ops.node.tree_socket_change_type(in_out='OUT', socket_type=socket_type,) #operator override is best, but which element do we need to override, not sure what the cpp operator need.. 

    #then restore... all this will may some signal to depsgraph
    for api,obj in restore_override.items():
       setattr(snode,api,obj)

    return None

def create_socket(ng, socket_type="NodeSocketFloat", socket_name="Value"):
    socket = ng.outputs.new(socket_type,socket_name)
    return socket

def remove_socket(ng, idx):
    todel = ng.outputs[idx]
    ng.outputs.remove(todel)
    return None 

def create_new_nodegroup(name, sockets={}):
    """create new nodegroup with outputs from given dict {"name":"type",}, make sure given type are correct"""

    ng = bpy.data.node_groups.new(name=name, type="GeometryNodeTree")
    in_node = ng.nodes.new("NodeGroupInput")
    in_node.location.x -= 200
    out_node = ng.nodes.new("NodeGroupOutput")
    out_node.location.x += 200

    for socket_name, socket_type in sockets.items():
        create_socket(ng, socket_type=socket_type, socket_name=socket_name)

    return ng

# def import_nodegroup(groupname, source_blend="extra_node_sequencer_volume.blend",):
#     """import an existing nodegroup"""

#     import os 

#     python_path = os.path.dirname(os.path.realpath(__file__))
#     lib_file = os.path.join(python_path,source_blend)

#     with bpy.data.libraries.load(lib_file,link=False) as (data_from,data_to):
#        data_to.node_groups.append(groupname)
#     group = bpy.data.node_groups[groupname]
#     group.use_fake_user = True

#     return group



##################################################
# CUSTOM NODE
##################################################



class EXTRANODESEQUENCERVOLUME_NG_sequencer_volume(bpy.types.GeometryNodeCustomGroup):
    
    bl_idname = "GeometryNodeSequencerVolume"
    bl_label = "Sequencer Volume"

    debug_update_counter : bpy.props.IntProperty() #visual aid debug 

    frame_delay : bpy.props.IntProperty()

    @classmethod
    def poll(cls, context): #mandatory with geonode
        return True

    def init(self,context,):        
        """this fct run when appending the node for the first time"""

        name = f".{self.bl_idname}"
        if not name in bpy.data.node_groups.keys():
             ng = create_new_nodegroup(name, sockets={"Volume":"NodeSocketFloat"},)
        else: ng = bpy.data.node_groups[name].copy()

        self.node_tree = ng
        self.width = 150
        self.label = self.bl_label

        #mark an update signal so handler fct do not need to loop every single nodegroups
        bpy.context.space_data.node_tree["extra_node_sequencer_volume_update_needed"] = True

        return None 

    def copy(self,node,):
        """fct run when dupplicating the node"""
        self.node_tree = node.node_tree.copy()
        return None 
    
    def update(self):
        """generic update function"""
        
        ng = self.node_tree

        frame = None 
        if self.frame_delay:
            frame = bpy.context.scene.frame_current + self.frame_delay

        value = self.evaluate_sequencer_volume(frame=frame)
        set_socket_value(ng,0, value=float(value) ,)

        self.debug_update_counter +=1
        return None

    def evaluate_sequencer_volume(self,frame=None):
        """evaluate the sequencer volume source
        this node was possible thanks to tintwotin
        source : https://github.com/snuq/VSEQF/blob/3ac717e1fa8c7371ec40503428bc2d0d004f0b35/vseqf.py#L142"""

        #TODO, ideally we need to also sample volume from few frame before or after, so user can create a smoothing falloff of some sort, 
        #      that's what 'frame_delay' is for, but unfortunately this function is incomplete, frame can only be None in order to work
        #      right now i do not have the strength to do it, you'll need to check for 'fades.get_fade_curve(bpy.context, sequence, create=False)' from the github link above

        total = 0

        if bpy.context.scene.sequence_editor is None:
            return 0
        
        sequences = bpy.context.scene.sequence_editor.sequences_all
        depsgraph = bpy.context.evaluated_depsgraph_get()
        
        if frame is None:
              frame = bpy.context.scene.frame_current
              evaluate_volume = False
        else: evaluate_volume = True

        fps = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base

        for sequence in sequences:

            if (sequence.type=="SOUND" and sequence.frame_final_start<frame and sequence.frame_final_end>frame and not sequence.mute):
               
                time_from = (frame - 1 - sequence.frame_start) / fps
                time_to = (frame - sequence.frame_start) / fps

                audio = sequence.sound.evaluated_get(depsgraph).factory

                chunk = audio.limit(time_from, time_to).data()
                #sometimes the chunks cannot be read properly, try to read 2 frames instead
                if (len(chunk)==0):
                    time_from_temp = (frame - 2 - sequence.frame_start) / fps
                    chunk = audio.limit(time_from_temp, time_to).data()
                #chunk still couldnt be read... just give up :\
                if (len(chunk)==0):
                    average = 0

                else:
                    cmax = abs(chunk.max())
                    cmin = abs(chunk.min())
                    if cmax > cmin:
                          average = cmax
                    else: average = cmin

                if evaluate_volume:
                    fcurve = fades.get_fade_curve(bpy.context, sequence, create=False) #->fades still need support, check Github source 
                    if fcurve:
                          volume = fcurve.evaluate(frame)
                    else: volume = sequence.volume
                else:
                    volume = sequence.volume

                total = total + (average * volume)
            
            continue 

        return total
    
    #def socket_value_update(self,context):
    #    """dead api, revive me please?"""
    #    return None 
    
    def draw_label(self,):
        """node label"""
        return "Sequencer Volume"

    def draw_buttons(self,context,layout,):
        """node interface drawing"""

        ng = self.node_tree

        #layout.prop(self,"frame_delay",text="Frame Delay")

        if bpy.context.preferences.addons["extra_node_sequencer_volume"].preferences.debug:
            box = layout.column()
            box.active = False
            box.prop(self,"node_tree", text="")
            box.prop(self,"debug_update_counter", text="update count")

        return None 



##################################################
# HANDLER UPDATE
##################################################



@bpy.app.handlers.persistent
def extra_node_sequencer_volume_frame_pre(scene,desp): #used for Volume and Api Node!
    """update on frame change"""
    if bpy.context.preferences.addons["extra_node_sequencer_volume"].preferences.debug: print("extra_node_sequencer_volume: frame_pre signal")

    #search for nodes all over data and update
    for n in [n for ng in bpy.data.node_groups if ("extra_node_sequencer_volume_update_needed" in ng) for n in ng.nodes if (n.bl_idname=="GeometryNodeSequencerVolume")]:
        n.update()

    return None


def all_handlers(name=False):
    """return a list of handler stored in .blend""" 

    return_list = []
    for oh in bpy.app.handlers:
        try:
            for h in oh:
                return_list.append(h)
        except: pass
    return return_list

def register_handlers(status):
    """register dispatch for handlers"""

    if (status=="register"):

        all_handler_names = [h.__name__ for h in all_handlers()]

        #depsgraph
        # if "extra_node_sequencer_volume_depsgraph" not in all_handler_names:
        #     bpy.app.handlers.depsgraph_update_post.append(extra_node_sequencer_volume_depsgraph)

        #frame_change
        if "extra_node_sequencer_volume_frame_pre" not in all_handler_names:
            bpy.app.handlers.frame_change_pre.append(extra_node_sequencer_volume_frame_pre)
            
        #render
        # if extra_node_sequencer_volume_render_pre not in all_handlers():
        #     bpy.app.handlers.render_pre.append(extra_node_sequencer_volume_render_pre)
        # if extra_node_sequencer_volume_render_post not in all_handlers():
        #     bpy.app.handlers.render_post.append(extra_node_sequencer_volume_render_post)

        #blend open 
        # if extra_node_sequencer_volume_load_post not in all_handlers():
        #     bpy.app.handlers.load_post.append(extra_node_sequencer_volume_load_post)

        return None 

    elif (status=="unregister"):

        for h in all_handlers():

            #depsgraph
            # if(h.__name__=="extra_node_sequencer_volume_depsgraph"):
            #     bpy.app.handlers.depsgraph_update_post.remove(h)

            #frame_change
            if(h.__name__=="extra_node_sequencer_volume_frame_pre"):
                bpy.app.handlers.frame_change_pre.remove(h)

            # #render 
            # if(h==extra_node_sequencer_volume_render_pre):
            #     bpy.app.handlers.render_pre.remove(h)
            # if(h==extra_node_sequencer_volume_render_post):
            #     bpy.app.handlers.render_post.remove(h)

            # #blend open 
            # if(h==extra_node_sequencer_volume_load_post):
            #     bpy.app.handlers.load_post.remove(h)

    return None 



##################################################
# EXTEND MENU  
##################################################



#extra menu

def extra_geonode_menu(self,context,):
    """extend NODE_MT_add with new extra menu"""
    self.layout.menu("NODE_MT_category_GEO_EXTRA",text="Extra",)
    return None 

class NODE_MT_category_GEO_EXTRA(bpy.types.Menu):

    bl_idname = "NODE_MT_category_GEO_EXTRA"
    bl_label  = ""

    @classmethod
    def poll(cls, context):
        return (bpy.context.space_data.tree_type == "GeometryNodeTree")

    def draw(self, context):
        return None

#extra menu extension 

def extra_geonode_sequencer_volume(self,context,):
    """extend extra menu with new node"""
    op = self.layout.operator("node.add_node",text="Sequencer Volume",)
    op.type = "GeometryNodeSequencerVolume"
    op.use_transform = True

#register

def register_menus(status):
    """register extra menu, if not already, append item, if not already"""

    if (status=="register"):

        #register new extra menu class if not exists already, perhaps another plugin already implemented it 
        if "NODE_MT_category_GEO_EXTRA" not in  bpy.types.__dir__():
            bpy.utils.register_class(NODE_MT_category_GEO_EXTRA)

        #extend add menu with extra menu if not already, _dyn_ui_initialize() will get appended drawing functions of a menu
        add_menu = bpy.types.NODE_MT_add
        if "extra_geonode_menu" not in [f.__name__ for f in add_menu._dyn_ui_initialize()]:
            add_menu.append(extra_geonode_menu)

        #extend extra menu with our custom nodes if not already
        extra_menu = bpy.types.NODE_MT_category_GEO_EXTRA
        if "extra_geonode_sequencer_volume" not in [f.__name__ for f in extra_menu._dyn_ui_initialize()]:
            extra_menu.append(extra_geonode_sequencer_volume)

        return None 

    elif (status=="unregister"):

        add_menu = bpy.types.NODE_MT_add
        extra_menu = bpy.types.NODE_MT_category_GEO_EXTRA

        #remove our custom function to extra menu 
        for f in extra_menu._dyn_ui_initialize().copy():
            if (f.__name__=="extra_geonode_sequencer_volume"):
                extra_menu.remove(f)

        #if extra menu is empty 
        if len(extra_menu._dyn_ui_initialize())==1:

            #remove our extra menu item draw fct add menu  
            for f in add_menu._dyn_ui_initialize().copy():
                if (f.__name__=="extra_geonode_menu"):
                    add_menu.remove(f)

            #unregister extra menu 
            bpy.utils.unregister_class(extra_menu)

    return None 



##################################################
# PROPERTIES & PREFS 
##################################################



class EXTRANODESEQUENCERVOLUME_AddonPref(bpy.types.AddonPreferences):
    """addon_prefs = bpy.context.preferences.addons["extra_node_sequencer_volume"].preferences"""

    bl_idname = "extra_node_sequencer_volume"

    debug : bpy.props.BoolProperty(default=False)

    #drawing part in ui module
    def draw(self,context):
        layout = self.layout

        box = layout.box()
        box.prop(self,"debug",text="Debug Mode",)

        return None 



##################################################
# INIT REGISTRATION 
##################################################



classes = [
    
    EXTRANODESEQUENCERVOLUME_AddonPref,
    EXTRANODESEQUENCERVOLUME_NG_sequencer_volume,
]


def register():

    #classes
    for cls in classes:
        bpy.utils.register_class(cls)
            
    #extend add menu
    register_menus("register")

    #handlers
    register_handlers("register")
    
    return None


def unregister():
        
    #handlers
    register_handlers("unregister")
    
    #extend add menu
    register_menus("unregister")

    #classes
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    return None


if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()
