
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
    "name":"'Python Api' for Geometry-Node",
    "author":"BD3D",
    "description":"This plugin add an extra node for Geometry-Node that will evaluate python data, use 'Auto Evaluation' to automatically re-evaluate the python eval() snippets",
    "blender":(3,0,0),
    "version": (1,0,0),
    "location":"Node Editor > Geometry Node > Add Menu > Extra",
    "warning":"",
    "tracker_url": "https://devtalk.blender.org/t/extra-nodes-for-geometrynodes/20942",
    "category":"Node",
    }

"""

At the moment of writing this note, there are really limitations/walls when creating GeometryNodeCustomGroup:

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

# def import_nodegroup(groupname, source_blend="extra_node_python_api.blend",):
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



#convenience import, needed for string evaluation
from mathutils import * ; from math import *

class EXTRANODEPYTHONAPI_NG_python_api(bpy.types.GeometryNodeCustomGroup):
    
    bl_idname = "GeometryNodePythonApi"
    bl_label = "Python Api"

    error : bpy.props.BoolProperty(default=False,)
    socket_type : bpy.props.StringProperty(default="NodeSocketBool")
    debug_update_counter : bpy.props.IntProperty() #visual aid debug 

    def api_str_update(self,context):
        """update and implicit conversion when human is writing and press enter"""
        self.evaluate_api(implicit_conversion=True)
        return None 
    api_str : bpy.props.StringProperty(update=api_str_update,)

    @classmethod
    def poll(cls, context): #mandatory with geonode
        return True

    def init(self,context,):        
        """this fct run when appending the node for the first time"""

        name = f".{self.bl_idname}"
        if not name in bpy.data.node_groups.keys():
              ng = create_new_nodegroup(name, sockets={"Waiting for Input":"NodeSocketFloat","Error":"NodeSocketBool"},)
        else: ng = bpy.data.node_groups[name].copy()

        self.node_tree = ng
        self.label = self.bl_label
        self.width = 250

        #mark an update signal so handler fct do not need to loop every single nodegroups
        bpy.context.space_data.node_tree["extra_node_python_api_update_needed"] = True

        return None 

    def copy(self,node,):
        """fct run when dupplicating the node"""
        self.node_tree = node.node_tree.copy()
        return None 
    
    def update(self):
        """generic update function"""
        
        self.evaluate_api()

        self.debug_update_counter +=1
        return None

    def evaluate_api(self, implicit_conversion=False):
        """function that will evaluate the pointer and assign value to output node"""

        ng = self.node_tree

        #check if string is empty first, perhaps user didn't input anything yet 
        if (self.api_str==""):

            set_socket_value(ng,1, value=True,)
            set_socket_label(ng,0, label="Waiting for Input" ,)

            return None
        
        #catch any exception, and report error to node
        try:    
            #convenience variable 
            D = bpy.data ; C = context = bpy.context ; scene = context.scene

            #convenience execution
            convenience_exec3 = bpy.context.preferences.addons["extra_node_python_api"].preferences.convenience_exec3
            if (convenience_exec3!=""): 
                exec(bpy.context.preferences.addons["extra_node_python_api"].preferences.convenience_exec3)
            
            #evaluate
            value = eval(self.api_str)

            #translate to list when possible
            if type(value) in (Vector, Euler, bpy.types.bpy_prop_array, tuple,):
                value = list(value)

            #get the value type 
            type_val = type(value)

            #evaluate as bool?
            if (type_val is bool):

                if implicit_conversion and (get_socket_type(ng,0)!="BOOLEAN"):
                    set_socket_type(ng,0, socket_type="NodeSocketBool") ; self.socket_type="NodeSocketBool"
                v=set_socket_value(ng,0, value=value ,)
                set_socket_label(ng,0, label=v ,)

            #evaluate as int?
            elif (type_val is int):

                if implicit_conversion and (get_socket_type(ng,0)!="INT"):
                    set_socket_type(ng,0, socket_type="NodeSocketInt") ; self.socket_type="NodeSocketInt"
                v=set_socket_value(ng,0, value=value ,)
                set_socket_label(ng,0, label=v ,)

            #float?
            elif (type_val is float):

                if implicit_conversion and (get_socket_type(ng,0)!="VALUE"):
                    set_socket_type(ng,0, socket_type="NodeSocketFloat") ; self.socket_type="NodeSocketFloat"
                v=set_socket_value(ng,0, value=value ,)
                set_socket_label(ng,0, label=round(v,4) ,)
            
            #vector/color?
            elif (type_val is list):

                #evaluate as vector?
                if (len(value)==3):

                    if implicit_conversion and (get_socket_type(ng,0)!="VECTOR"):
                        set_socket_type(ng,0, socket_type="NodeSocketVector") ; self.socket_type="NodeSocketVector"
                    v=set_socket_value(ng,0, value=value ,)
                    set_socket_label(ng,0, label=[round(n,4) for n in v] ,)
                
                #evaluate as color? 
                elif (len(value)==4):

                    if implicit_conversion and (get_socket_type(ng,0)!="RGBA"):
                        set_socket_type(ng,0, socket_type="NodeSocketColor") ; self.socket_type="NodeSocketColor"
                    v=set_socket_value(ng,0, value=value ,)
                    set_socket_label(ng,0, label=[round(n,4) for n in v] ,)

                #only vec3 and vec4 are supported
                else:
                    self.error = True
                    raise Exception(f"TypeError: 'List{len(value)}' not supported")

            #string?
            elif (type_val is str):

                if implicit_conversion and (get_socket_type(ng,0)!="STRING"):
                    set_socket_type(ng,0, socket_type="NodeSocketString") ; self.socket_type="NodeSocketString"
                v=set_socket_value(ng,0, value=value ,)
                set_socket_label(ng,0, label='"'+v+'"' ,)

            #object type?
            elif (type_val is bpy.types.Object):

                if implicit_conversion and (get_socket_type(ng,0)!="OBJECT"):
                    set_socket_type(ng,0, socket_type="NodeSocketObject") ; self.socket_type="NodeSocketObject"
                v=set_socket_value(ng,0, value=value,)
                set_socket_label(ng,0, label=f'D.objects["{v.name}"]',)

            #collection type? 
            elif (type_val is bpy.types.Collection):

                if implicit_conversion and (get_socket_type(ng,0)!="COLLECTION"):
                    set_socket_type(ng,0, socket_type="NodeSocketCollection") ; self.socket_type="NodeSocketCollection"
                v=set_socket_value(ng,0, value=value,)
                set_socket_label(ng,0, label=f'D.collections["{v.name}"]',)

            #material type? 
            elif (type_val is bpy.types.Material):

                if implicit_conversion and (get_socket_type(ng,0)!="MATERIAL"):
                    set_socket_type(ng,0, socket_type="NodeSocketMaterial") ; self.socket_type="NodeSocketMaterial"
                v=set_socket_value(ng,0, value=value,)
                set_socket_label(ng,0, label=f'D.materials["{v.name}"]',)

            #image type?
            elif (type_val is bpy.types.Image):

                if implicit_conversion and (get_socket_type(ng,0)!="IMAGE"):
                    set_socket_type(ng,0, socket_type="NodeSocketImage") ; self.socket_type="NodeSocketImage"
                v=set_socket_value(ng,0, value=value,)
                set_socket_label(ng,0, label=f'D.images["{v.name}"]',)

            # #texture type? well how about we have the sample texture node back ;-)
            # elif (type_val is bpy.types.Texture): #-> well, annoying because it give us subtype, how to check if type given is a texture then? check parent class with python? 
            #
            #     if implicit_conversion and (get_socket_type(ng,0)!="TEXTURE"):
            #         set_socket_type(ng,0, socket_type="NodeSocketTexture")
            #     v=set_socket_value(ng,0, value=value,)
            #     set_socket_label(ng,0, label=f'D.textures["{value.name}"]',)

            #unsusupported type
            else:
                self.error = True
                raise Exception(f"TypeError: '{type_val.__name__.title()}' not supported")
            
            #no error, then return False to error prop
            set_socket_value(ng,1, value=False,)

            self.error = False
            return get_socket_value(ng,0)

        except Exception as e:

            self.error = True 
            print(f"GeometryNodePythonApi >>> {e}")

            set_socket_value(ng,1, value=True,)
            set_socket_label(ng,0, label=e ,)

        return None
    
    #def socket_value_update(self,context):
    #    """dead api, revive me please?"""
    #    return None 
    
    def draw_label(self,):
        """node label"""
        return "Python Api"

    def draw_buttons(self,context,layout,):
        """node interface drawing"""

        ng = self.node_tree

        row = layout.row()
        row.alert = self.error
        row.prop(self,"api_str",text="",)

        if bpy.context.preferences.addons["extra_node_python_api"].preferences.debug:
            box = layout.column()
            box.active = False
            box.prop(self,"node_tree", text="")
            box.prop(self,"debug_update_counter", text="update count")

        return None 



##################################################
# HANDLER UPDATE
##################################################



@bpy.app.handlers.persistent
def extra_node_python_api_depsgraph(scene,desp): #used for Api node, if allowed!
    """update on depsgraph change"""
    if bpy.context.preferences.addons["extra_node_python_api"].preferences.debug: print("extra_node_python_api: depsgraph signal")

    #automatic update for Python Api only if allowed 
    if not bpy.context.preferences.addons["extra_node_python_api"].preferences.auto_evaluate_py:
        return None 

    #search for nodes all over data and update
    for n in [n for ng in bpy.data.node_groups if ("extra_node_python_api_update_needed" in ng) for n in ng.nodes if (n.bl_idname=="GeometryNodePythonApi")]:
        n.update()

    return None

@bpy.app.handlers.persistent
def extra_node_python_api_frame_pre(scene,desp): #used for Volume and Api Node!
    """update on frame change"""
    if bpy.context.preferences.addons["extra_node_python_api"].preferences.debug: print("extra_node_python_api: frame_pre signal")

    #automatic update for Python Api only if allowed 
    if not bpy.context.preferences.addons["extra_node_python_api"].preferences.auto_evaluate_py:
        return None 

    #search for nodes all over data and update
    for n in [n for ng in bpy.data.node_groups if ("extra_node_python_api_update_needed" in ng) for n in ng.nodes if (n.bl_idname=="GeometryNodePythonApi")]:
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
        if "extra_node_python_api_depsgraph" not in all_handler_names:
            bpy.app.handlers.depsgraph_update_post.append(extra_node_python_api_depsgraph)

        #frame_change
        if "extra_node_python_api_frame_pre" not in all_handler_names:
            bpy.app.handlers.frame_change_pre.append(extra_node_python_api_frame_pre)
            
        #render
        # if extra_node_python_api_render_pre not in all_handlers():
        #     bpy.app.handlers.render_pre.append(extra_node_python_api_render_pre)
        # if extra_node_python_api_render_post not in all_handlers():
        #     bpy.app.handlers.render_post.append(extra_node_python_api_render_post)

        #blend open 
        # if extra_node_python_api_load_post not in all_handlers():
        #     bpy.app.handlers.load_post.append(extra_node_python_api_load_post)

        return None 

    elif (status=="unregister"):

        for h in all_handlers():

            #depsgraph
            if(h.__name__=="extra_node_python_api_depsgraph"):
                bpy.app.handlers.depsgraph_update_post.remove(h)

            #frame_change
            if(h.__name__=="extra_node_python_api_frame_pre"):
                bpy.app.handlers.frame_change_pre.remove(h)

            # #render 
            # if(h==extra_node_python_api_render_pre):
            #     bpy.app.handlers.render_pre.remove(h)
            # if(h==extra_node_python_api_render_post):
            #     bpy.app.handlers.render_post.remove(h)

            # #blend open 
            # if(h==extra_node_python_api_load_post):
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

def extra_node_python_api(self,context,):
    """extend extra menu with new node"""
    op = self.layout.operator("node.add_node",text="Python Api",)
    op.type = "GeometryNodePythonApi"
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
        if "extra_node_python_api" not in [f.__name__ for f in extra_menu._dyn_ui_initialize()]:
            extra_menu.append(extra_node_python_api)

        return None 

    elif (status=="unregister"):

        add_menu = bpy.types.NODE_MT_add
        extra_menu = bpy.types.NODE_MT_category_GEO_EXTRA

        #remove our custom function to extra menu 
        for f in extra_menu._dyn_ui_initialize().copy():
            if (f.__name__=="extra_node_python_api"):
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



class EXTRANODEPYTHONAPI_AddonPref(bpy.types.AddonPreferences):
    """addon_prefs = bpy.context.preferences.addons["extra_node_python_api"].preferences"""

    bl_idname = "extra_node_python_api"

    debug : bpy.props.BoolProperty(default=False)
    auto_evaluate_py : bpy.props.BoolProperty(default=True)
    convenience_exec1 : bpy.props.StringProperty(default="rom mathutils import * ; from math import *") #fake
    convenience_exec2 : bpy.props.StringProperty(default="D = bpy.data ; C = context = bpy.context ; scene = context.scene") #fake
    convenience_exec3 : bpy.props.StringProperty(default="")

    #drawing part in ui module
    def draw(self,context):
        layout = self.layout

        box = layout.box()

        box.prop(self,"auto_evaluate_py",text="Auto Evaluation",)
        box.prop(self,"debug",text="Debug Mode",)

        convenience = box.column(align=True)
        convenience.label(text="Convenience Execution:")
        cexec = convenience.row() ; cexec.enabled = False
        cexec.prop(self,"convenience_exec1",text="",)
        cexec = convenience.row() ; cexec.enabled = False
        cexec.prop(self,"convenience_exec2",text="",)
        cexec = convenience.row() ; cexec.active = False
        cexec.prop(self,"convenience_exec3",text="",)

        return None 



##################################################
# INIT REGISTRATION 
##################################################



classes = [
    
    EXTRANODEPYTHONAPI_AddonPref,
    EXTRANODEPYTHONAPI_NG_python_api,
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
