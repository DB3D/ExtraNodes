
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
    "name":"'Missing Inputs' for Geometry-Node",
    "author":"BD3D",
    "description":"There are missing object/collection/collection/Bool/Int input.",
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



##################################################
# CUSTOM NODE
##################################################


class EXTRANODEMISSINGINPUT_NG_object(bpy.types.GeometryNodeCustomGroup):
    
    bl_idname = "GeometryNodeMissingObjectInput"
    bl_label = "Object"

    def pointer_update(self,context):
        """update and implicit conversion when human is writing and press enter"""
        set_socket_value(self.node_tree, 0, value=self.default_value,)
        return None 
    default_value : bpy.props.PointerProperty(type=bpy.types.Object,update=pointer_update)

    @classmethod
    def poll(cls, context): #mandatory with geonode
        return True

    def init(self,context,):        
        """this fct run when appending the node for the first time"""

        name = f".{self.bl_idname}"
        if not name in bpy.data.node_groups.keys():
             ng = create_new_nodegroup(name, sockets={"Object":"NodeSocketObject"},)
        else: ng = bpy.data.node_groups[name].copy()

        self.node_tree = ng
        self.width = 140
        self.label = self.bl_label

        return None 

    def copy(self,node,):
        """fct run when dupplicating the node"""
        self.node_tree = node.node_tree.copy()
        return None 
    
    def update(self):
        """generic update function"""
        return None
    
    #def socket_value_update(self,context):
    #    """dead api, revive me please?"""
    #    return None 
    
    def draw_label(self,):
        """node label"""
        return "Object"

    def draw_buttons(self,context,layout,):
        """node interface drawing"""

        layout.prop(self,"default_value",text="")

        if bpy.context.preferences.addons["extra_node_missing_inputs"].preferences.debug:
            box = layout.column()
            box.active = False
            box.prop(self,"node_tree", text="")

        return None 

class EXTRANODEMISSINGINPUT_NG_collection(bpy.types.GeometryNodeCustomGroup):
    
    bl_idname = "GeometryNodeMissingCollectionInput"
    bl_label = "Collection"

    def pointer_update(self,context):
        """update and implicit conversion when human is writing and press enter"""
        set_socket_value(self.node_tree, 0, value=self.default_value,)
        return None 
    default_value : bpy.props.PointerProperty(type=bpy.types.Collection,update=pointer_update)

    @classmethod
    def poll(cls, context): #mandatory with geonode
        return True

    def init(self,context,):        
        """this fct run when appending the node for the first time"""

        name = f".{self.bl_idname}"
        if not name in bpy.data.node_groups.keys():
             ng = create_new_nodegroup(name, sockets={"Collection":"NodeSocketCollection"},)
        else: ng = bpy.data.node_groups[name].copy()

        self.node_tree = ng
        self.width = 140
        self.label = self.bl_label

        return None 

    def copy(self,node,):
        """fct run when dupplicating the node"""
        self.node_tree = node.node_tree.copy()
        return None 
    
    def update(self):
        """generic update function"""
        return None
    
    #def socket_value_update(self,context):
    #    """dead api, revive me please?"""
    #    return None 
    
    def draw_label(self,):
        """node label"""
        return "Collection"

    def draw_buttons(self,context,layout,):
        """node interface drawing"""

        layout.prop(self,"default_value",text="")

        if bpy.context.preferences.addons["extra_node_missing_inputs"].preferences.debug:
            box = layout.column()
            box.active = False
            box.prop(self,"node_tree", text="")

        return None 


class EXTRANODEMISSINGINPUT_NG_image(bpy.types.GeometryNodeCustomGroup):
    
    bl_idname = "GeometryNodeMissingImageInput"
    bl_label = "Image"

    def pointer_update(self,context):
        """update and implicit conversion when human is writing and press enter"""
        set_socket_value(self.node_tree, 0, value=self.default_value,)
        return None 
    default_value : bpy.props.PointerProperty(type=bpy.types.Image,update=pointer_update)

    @classmethod
    def poll(cls, context): #mandatory with geonode
        return True

    def init(self,context,):        
        """this fct run when appending the node for the first time"""

        name = f".{self.bl_idname}"
        if not name in bpy.data.node_groups.keys():
             ng = create_new_nodegroup(name, sockets={"Image":"NodeSocketImage"},)
        else: ng = bpy.data.node_groups[name].copy()

        self.node_tree = ng
        self.width = 250
        self.label = self.bl_label

        return None 

    def copy(self,node,):
        """fct run when dupplicating the node"""
        self.node_tree = node.node_tree.copy()
        return None 
    
    def update(self):
        """generic update function"""
        return None
    
    def draw_label(self,):
        """node label"""
        return "Image"

    def draw_buttons(self,context,layout,):
        """node interface drawing"""

        #layout.template_image(self, "default_value",self.default_value.path_resolve("users",False),)
        layout.template_ID(self, "default_value", open="image.open", new="image.new")

        if bpy.context.preferences.addons["extra_node_missing_inputs"].preferences.debug:
            box = layout.column()
            box.active = False
            box.prop(self,"node_tree", text="")
        return None 

class EXTRANODEMISSINGINPUT_NG_int(bpy.types.GeometryNodeCustomGroup):
    
    bl_idname = "GeometryNodeMissingIntInput"
    bl_label = "Integer"

    def pointer_update(self,context):
        """update and implicit conversion when human is writing and press enter"""
        set_socket_value(self.node_tree, 0, value=self.default_value,)
        set_socket_label(self.node_tree, 0, label=str(self.default_value),)
        return None 
    default_value : bpy.props.IntProperty(update=pointer_update)

    @classmethod
    def poll(cls, context): #mandatory with geonode
        return True

    def init(self,context,):        
        """this fct run when appending the node for the first time"""

        name = f".{self.bl_idname}"
        if not name in bpy.data.node_groups.keys():
              ng = create_new_nodegroup(name, sockets={"Integer":"NodeSocketInt"},)
        else: ng = bpy.data.node_groups[name].copy()

        self.node_tree = ng
        self.width = 140
        self.label = self.bl_label

        return None 

    def copy(self,node,):
        """fct run when dupplicating the node"""
        self.node_tree = node.node_tree.copy()
        return None 
    
    def update(self):
        """generic update function"""
        return None
    
    def draw_label(self,):
        """node label"""
        return "Integer"

    def draw_buttons(self,context,layout,):
        """node interface drawing"""

        layout.prop(self,"default_value",text="")

        if bpy.context.preferences.addons["extra_node_missing_inputs"].preferences.debug:
            box = layout.column()
            box.active = False
            box.prop(self,"node_tree", text="")

        return None 

class EXTRANODEMISSINGINPUT_NG_bool(bpy.types.GeometryNodeCustomGroup):
    
    bl_idname = "GeometryNodeMissingBoolInput"
    bl_label = "Boolean"

    def pointer_update(self,context):
        """update and implicit conversion when human is writing and press enter"""
        set_socket_value(self.node_tree, 0, value=self.default_value,)
        set_socket_label(self.node_tree, 0, label=str(self.default_value),)
        return None 
    default_value : bpy.props.BoolProperty(update=pointer_update)

    @classmethod
    def poll(cls, context): #mandatory with geonode
        return True

    def init(self,context,):        
        """this fct run when appending the node for the first time"""

        name = f".{self.bl_idname}"
        if not name in bpy.data.node_groups.keys():
             ng = create_new_nodegroup(name, sockets={"Boolean":"NodeSocketBool"},)
        else: ng = bpy.data.node_groups[name].copy()

        self.node_tree = ng
        self.width = 140
        self.label = self.bl_label

        return None 

    def copy(self,node,):
        """fct run when dupplicating the node"""
        self.node_tree = node.node_tree.copy()
        return None 
    
    def update(self):
        """generic update function"""
        return None
    
    def draw_label(self,):
        """node label"""
        return "Boolean"

    def draw_buttons(self,context,layout,):
        """node interface drawing"""

        layout.prop(self,"default_value",text="Boolean")

        if bpy.context.preferences.addons["extra_node_missing_inputs"].preferences.debug:
            box = layout.column()
            box.active = False
            box.prop(self,"node_tree", text="")

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

def extra_geonode_missing_inputs(self,context,):
    """extend extra menu with new node"""

    op = self.layout.operator("node.add_node",text="Boolean",)
    op.type = "GeometryNodeMissingBoolInput"
    op.use_transform = True

    op = self.layout.operator("node.add_node",text="Integer",)
    op.type = "GeometryNodeMissingIntInput"
    op.use_transform = True

    op = self.layout.operator("node.add_node",text="Object",)
    op.type = "GeometryNodeMissingObjectInput"
    op.use_transform = True

    op = self.layout.operator("node.add_node",text="Collection",)
    op.type = "GeometryNodeMissingCollectionInput"
    op.use_transform = True

    op = self.layout.operator("node.add_node",text="Image",)
    op.type = "GeometryNodeMissingImageInput"
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
        if "extra_geonode_missing_inputs" not in [f.__name__ for f in extra_menu._dyn_ui_initialize()]:
            extra_menu.append(extra_geonode_missing_inputs)

        return None 

    elif (status=="unregister"):

        add_menu = bpy.types.NODE_MT_add
        extra_menu = bpy.types.NODE_MT_category_GEO_EXTRA

        #remove our custom function to extra menu 
        for f in extra_menu._dyn_ui_initialize().copy():
            if (f.__name__=="extra_geonode_missing_inputs"):
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



class EXTRANODEMISSINGINPUT_AddonPref(bpy.types.AddonPreferences):
    """addon_prefs = bpy.context.preferences.addons["extra_node_missing_inputs"].preferences"""

    bl_idname = "extra_node_missing_inputs"

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
    
    EXTRANODEMISSINGINPUT_AddonPref,
    EXTRANODEMISSINGINPUT_NG_bool,
    EXTRANODEMISSINGINPUT_NG_int,
    EXTRANODEMISSINGINPUT_NG_object,
    EXTRANODEMISSINGINPUT_NG_collection,
    EXTRANODEMISSINGINPUT_NG_image,

]


def register():

    #classes
    for cls in classes:
        bpy.utils.register_class(cls)
            
    #extend add menu
    register_menus("register")
    
    return None


def unregister():
            
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
