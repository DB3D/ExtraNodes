# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN, Andrew Stevenson
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy 

from ..__init__ import get_addon_prefs
from ..utils.str_utils import word_wrap
from ..utils.node_utils import create_new_nodegroup, set_socket_defvalue, get_socket_type, set_socket_type, set_socket_label, get_socket_defvalue

from mathutils import * # Conveniences vars for 'GeometryNodeExtraNodesPythonApi' 
from math import *      # Needed to eval user python expression (cannot import a wildcard within the class).


class NODEBOOSTER_NG_pythonapi(bpy.types.GeometryNodeCustomGroup):
    """Custom Nodgroup: Evaluate a python expression as a single value output.
    The evaluated type can be of type 'float', 'int', 'string', 'object', 'collection', 'material'.
    By default the values will be updated automatically on each on depsgraph post and frame_pre signals"""
    
    bl_idname = "GeometryNodeExtraNodesPythonApi"
    bl_label = "Python Api"

    evaluation_error : bpy.props.BoolProperty(
        default=False,
        )
    socket_type : bpy.props.StringProperty(
        default="NodeSocketBool",
        description="maint output socket type",
        )
    debug_update_counter : bpy.props.IntProperty(
        name="debug counter",
        default=0,
        )

    def update_user_expression(self,context):
        """evaluate user expression and change the socket output type implicitly"""
        self.evaluate_user_expression(implicit_conversion=True)
        return None 
    
    user_expression : bpy.props.StringProperty(
        update=update_user_expression,
        description="type the expression you wish to evaluate right here",
        )

    @classmethod
    def poll(cls, context):
        """mandatory poll"""
        return True

    def init(self, context,):        
        """this fct run when appending the node for the first time"""

        name = f".{self.bl_idname}"
        
        ng = bpy.data.node_groups.get(name)
        if (ng is None):
            ng = create_new_nodegroup(name,
                out_sockets={
                    "Waiting for Input" : "NodeSocketFloat",
                    "Error" : "NodeSocketBool",
                },
            )
         
        ng = ng.copy() #always using a copy of the original ng

        self.node_tree = ng
        self.width = 250
        self.label = self.bl_label

        #mark an update signal so handler fct do not need to loop every single nodegroups
        bpy.context.space_data.node_tree["nodebooster_pythonapi_updateflag"] = True

        return None 

    def copy(self,node,):
        """fct run when dupplicating the node"""
        
        self.node_tree = node.node_tree.copy()
        
        return None 
    
    def update(self):
        """generic update function"""
        
        self.evaluate_user_expression()
        self.debug_update_counter +=1
        
        return None

    def evaluate_user_expression(self, implicit_conversion=False,):
        """evaluate the user string and assign value to output node"""

        ng = self.node_tree

        #check if string is empty first, perhaps user didn't input anything yet 
        if (self.user_expression==""):
            
            set_socket_label(ng,0, label="Waiting for Input" ,)
            set_socket_defvalue(ng,1, value=True,)

            return None
        
        #catch any exception, and report error to node
        try:    
            #convenience variable for user
            D = bpy.data ; C = context = bpy.context ; scene = context.scene

            #convenience execution for user (he can customize this in plugin preference)
            pynode_convenience_exec3 = get_addon_prefs().pynode_convenience_exec3
            if (pynode_convenience_exec3!=""): 
                exec(pynode_convenience_exec3)
            
            #evaluate
            value = eval(self.user_expression)

            #translate to list when possible
            if type(value) in (Vector, Euler, bpy.types.bpy_prop_array, tuple,):
                value = list(value)

            match value:
                    
                case bool():

                    if implicit_conversion and (get_socket_type(ng,0)!="BOOLEAN"):
                        set_socket_type(ng,0, socket_type="NodeSocketBool")
                        self.socket_type = "NodeSocketBool"
                    set_socket_defvalue(ng,0, value=value ,)
                    set_socket_label(ng,0, label=value ,)

                case int():

                    if implicit_conversion and (get_socket_type(ng,0)!="INT"):
                        set_socket_type(ng,0, socket_type="NodeSocketInt")
                        self.socket_type = "NodeSocketInt"
                    set_socket_defvalue(ng,0, value=value ,)
                    set_socket_label(ng,0, label=value ,)

                case float():

                    if implicit_conversion and (get_socket_type(ng,0)!="VALUE"):
                        set_socket_type(ng,0, socket_type="NodeSocketFloat")
                        self.socket_type = "NodeSocketFloat"
                    set_socket_defvalue(ng,0, value=value ,)
                    set_socket_label(ng,0, label=round(value,4) ,)
                
                case list():

                    #evaluate as vector?
                    if (len(value)==3):

                        if implicit_conversion and (get_socket_type(ng,0)!="VECTOR"):
                            set_socket_type(ng,0, socket_type="NodeSocketVector")
                            self.socket_type = "NodeSocketVector"
                        set_socket_defvalue(ng,0, value=value ,)
                        set_socket_label(ng,0, label=[round(n,4) for n in value] ,)
                    
                    #evaluate as color? 
                    elif (len(value)==4):

                        if implicit_conversion and (get_socket_type(ng,0)!="RGBA"):
                            set_socket_type(ng,0, socket_type="NodeSocketColor")
                            self.socket_type = "NodeSocketColor"
                        set_socket_defvalue(ng,0, value=value ,)
                        set_socket_label(ng,0, label=[round(n,4) for n in value] ,)

                    #only vec3 and vec4 are supported
                    else:
                        self.evaluation_error = True
                        raise Exception(f"TypeError: 'List{len(value)}' not supported")

                case str():

                    if implicit_conversion and (get_socket_type(ng,0)!="STRING"):
                        set_socket_type(ng,0, socket_type="NodeSocketString")
                        self.socket_type = "NodeSocketString"
                    set_socket_defvalue(ng,0, value=value ,)
                    set_socket_label(ng,0, label='"'+value+'"' ,)

                case bpy.types.Object():

                    if implicit_conversion and (get_socket_type(ng,0)!="OBJECT"):
                        set_socket_type(ng,0, socket_type="NodeSocketObject")
                        self.socket_type = "NodeSocketObject"
                    set_socket_defvalue(ng,0, value=value,)
                    set_socket_label(ng,0, label=f'D.objects["{value.name}"]',)

                case bpy.types.Collection():

                    if implicit_conversion and (get_socket_type(ng,0)!="COLLECTION"):
                        set_socket_type(ng,0, socket_type="NodeSocketCollection")
                        self.socket_type = "NodeSocketCollection"
                    set_socket_defvalue(ng,0, value=value,)
                    set_socket_label(ng,0, label=f'D.collections["{value.name}"]',)

                case bpy.types.Material():

                    if implicit_conversion and (get_socket_type(ng,0)!="MATERIAL"):
                        set_socket_type(ng,0, socket_type="NodeSocketMaterial")
                        self.socket_type = "NodeSocketMaterial"
                    set_socket_defvalue(ng,0, value=value,)
                    set_socket_label(ng,0, label=f'D.materials["{value.name}"]',)

                case bpy.types.Image():

                    if implicit_conversion and (get_socket_type(ng,0)!="IMAGE"):
                        set_socket_type(ng,0, socket_type="NodeSocketImage")
                        self.socket_type = "NodeSocketImage"
                    set_socket_defvalue(ng,0, value=value,)
                    set_socket_label(ng,0, label=f'D.images["{value.name}"]',)

                case _:
                    self.evaluation_error = True
                    raise Exception(f"TypeError: '{type(value).__name__.title()}' not supported")
            
            #no error, then return False to error prop
            set_socket_defvalue(ng,1, value=False,)

            self.evaluation_error = False
            return get_socket_defvalue(ng,0)

        except Exception as e:

            self.evaluation_error = True 
            print(f"{self.bl_idname} EVALUATION ERROR:\n{e}")

            set_socket_defvalue(ng,1, value=True,)
            set_socket_label(ng,0, label=e,)

        return None
    
    def draw_label(self,):
        """node label"""
        
        return self.bl_label

    def draw_buttons(self, context, layout,):
        """node interface drawing"""
                
        row = layout.row()
        row.alert = self.evaluation_error
        row.prop(self,"user_expression",text="",)

        return None

    def draw_buttons_ext(self, context, layout):
        """draw in the N panel when the node is selected"""
        
        sett_plugin = get_addon_prefs()
        
        col = layout.column(align=True)
        row = col.row(align=True)
        row.alert = self.evaluation_error
        row.prop(self,"user_expression", text="",)

        header, panel = layout.panel("doc_panelid", default_closed=True,)
        header.label(text="Documentation",)
        if (panel):
            word_wrap(layout=panel, alert=False, active=True, max_char='auto',
                char_auto_sidepadding=0.9, context=context, string=self.bl_description,
                )
            panel.operator("wm.url_open", text="Documentation",).url = "www.todo.com"

        header, panel = layout.panel("doc_prefs", default_closed=True,)
        header.label(text="Preferences",)
        if (panel):

            col = panel.column(align=True)
            col.label(text="Namespace Convenience:")
            
            row = col.row(align=True)
            row.enabled = False
            row.prop(sett_plugin,"pynode_convenience_exec1",text="",)
            
            row = col.row(align=True)
            row.enabled = False
            row.prop(sett_plugin,"pynode_convenience_exec2",text="",)
            
            row = col.row(align=True)
            row.prop(sett_plugin,"pynode_convenience_exec3",text="",)
        
            panel.prop(sett_plugin,"pynode_depseval",)
            
            
        header, panel = layout.panel("dev_panelid", default_closed=True,)
        header.label(text="Development",)
        if (panel):
            panel.active = False
                            
            col = panel.column(align=True)
            col.label(text="NodeTree:")
            col.template_ID(self, "node_tree")
            
            col = panel.column(align=True)
            col.label(text="Debugging:")
            row = col.row()
            row.enabled = False
            row.prop(self, "debug_update_counter",)
        
        return None

    @classmethod
    def update_all(cls):
        """search for all nodes of this type and update them"""
        
        for n in [n for ng in bpy.data.node_groups if ('nodebooster_pythonapi_updateflag' in ng) for n in ng.nodes if (n.bl_idname==cls.bl_idname)]:
            n.update()
            
        return None

