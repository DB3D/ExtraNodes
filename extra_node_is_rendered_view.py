
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
    "name":"'Is Rendered View' for Geometry-Node",
    "author":"BD3D",
    "description":"This plugin add an extra node for Geometry-Node that will check if there is a rendered view active.",
    "blender":(3,0,0),
    "version": (1,0,0),
    "location":"Node Editor > Geometry Node > Add Menu > Extra",
    "warning":"",
    "category":"Node",
    }

"""

About creating GeometryNodeCustomGroup:

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

def create_new_nodegroup(name, sockets={},):
    """create new nodegroup with outputs from given dict {"type":"name",}, make sure given type are correct"""

    ng = bpy.data.node_groups.new(name=name,type="GeometryNodeTree")
    in_node = ng.nodes.new("NodeGroupInput")
    in_node.location.x-=200
    out_node = ng.nodes.new("NodeGroupOutput")
    out_node.location.x+=200

    for socket_type,socket_name in sockets.items():
        create_socket(ng, socket_type=socket_type, socket_name=socket_name)

    return ng

# def import_nodegroup(groupname, source_blend="extra_node_is_rendered_view.blend",):
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



class EXTRANODEISRENDEREDVIEW_NG_is_rendered_view(bpy.types.GeometryNodeCustomGroup):
    
    bl_idname = "GeometryNodeIsRenderedView"
    bl_label = "Is Rendered View"

    debug_update_counter : bpy.props.IntProperty() #visual aid debug 

    @classmethod
    def poll(cls, context): #mandatory with geonode
        return True

    def init(self,context,):        
        """this fct run when appending the node for the first time"""

        name = f".{self.bl_idname}"
        if not name in bpy.data.node_groups.keys():
             ng = create_new_nodegroup(name, sockets={"NodeSocketBool":"Is Rendered View"},)
        else: ng = bpy.data.node_groups[name]

        self.node_tree = ng
        self.width = 140
        self.label = self.bl_label

        return None 

    def copy(self,node,):
        """fct run when dupplicating the node"""
        return None 
    
    def update(self):
        """generic update function"""
        return None
    
    #def socket_value_update(self,context):
    #    """dead api, revive me please?"""
    #    return None 
    
    def draw_label(self,):
        """node label"""
        return "Is Rendered View"

    def draw_buttons(self,context,layout,):
        """node interface drawing"""

        if bpy.context.preferences.addons["extra_node_is_rendered_view"].preferences.debug:
            box = layout.column()
            box.active = False
            box.prop(self,"node_tree", text="")
            box.prop(self,"debug_update_counter", text="update count")

        return None 



##################################################
# MSGBUS UPDATE
##################################################



owner = object()

subscribe_to = (bpy.types.View3DShading, "type")

def all_3d_viewports():
    """return generator of all 3d view space"""

    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if(area.type == 'VIEW_3D'):
                for space in area.spaces:
                    if(space.type == 'VIEW_3D'):
                        yield space

def all_3d_viewports_shading_type():
    """return generator of all shading type str"""

    for space in all_3d_viewports():
        yield space.shading.type

def is_rendered_view():
    """check if is rendered view in a 3d view somewhere"""

    return 'RENDERED' in all_3d_viewports_shading_type()


def msgbus_callback(*args):
    if bpy.context.preferences.addons["extra_node_is_rendered_view"].preferences.debug: print("extra_node_is_rendered_view: msgbus signal")

    ng = bpy.data.node_groups.get(".GeometryNodeIsRenderedView")
    if ng is None: 
        return None

    set_socket_value(ng, 0, value=is_rendered_view(),)

    return None 

def register_handlers(status):
    """register dispatch for handlers"""

    if (status=="register"):

        bpy.msgbus.subscribe_rna(
            key=subscribe_to,
            owner=owner,
            notify=msgbus_callback,
            args=(None,),
            options={"PERSISTENT"},
        )

        return None 

    elif (status=="unregister"):

        bpy.msgbus.clear_by_owner(owner)

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

def extra_geonode_is_rendered_view(self,context,):
    """extend extra menu with new node"""
    op = self.layout.operator("node.add_node",text="Is Rendered View",)
    op.type = "GeometryNodeIsRenderedView"
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
        if "extra_geonode_is_rendered_view" not in [f.__name__ for f in extra_menu._dyn_ui_initialize()]:
            extra_menu.append(extra_geonode_is_rendered_view)

        return None 

    elif (status=="unregister"):

        add_menu = bpy.types.NODE_MT_add
        extra_menu = bpy.types.NODE_MT_category_GEO_EXTRA

        #remove our custom function to extra menu 
        for f in extra_menu._dyn_ui_initialize().copy():
            if (f.__name__=="extra_geonode_is_rendered_view"):
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



class EXTRANODEISRENDEREDVIEW_AddonPref(bpy.types.AddonPreferences):
    """addon_prefs = bpy.context.preferences.addons["extra_node_is_rendered_view"].preferences"""

    bl_idname = "extra_node_is_rendered_view"

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
    
    EXTRANODEISRENDEREDVIEW_AddonPref,
    EXTRANODEISRENDEREDVIEW_NG_is_rendered_view,
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
