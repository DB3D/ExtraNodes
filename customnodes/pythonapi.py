# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy 

from ..__init__ import get_addon_prefs
from ..utils.str_utils import word_wrap
from ..utils.node_utils import create_new_nodegroup, set_socket_defvalue, get_socket_type, set_socket_type, set_socket_label, get_socket_defvalue

from mathutils import * ; from math import * # Conveniences vars! Needed to evaluate the user python expression. 
                                             # Must be done in global space, wild cards not supported within classes.


class NODEBOOSTER_NG_pythonapi(bpy.types.GeometryNodeCustomGroup):
    """Custom Nodgroup: Evaluate a python expression as a single value output.
    The evaluated type can be of type 'float', 'int', 'string', 'object', 'collection', 'material'.
    By default the values will be updated automatically on each on depsgraph post and frame_pre signals"""

    #TODO we could expand this functionality and let user select a python script datablock.
    # the script could automatically recognize some vars from the execution namespace and output them?
    # ex: the user define some global variables starting with 'NODEOUTPUT_' and they become output values automatically.
    # ...
    # Could even go harder, and user could call the math expression node within the script to mix with arguments. 
    # Admitting we implement a 'Advanced Math Expression' node that supports Vec/Rot/Matrix ect..
    # Note that if this happens, it would be nicer to have some sort of create_expression_nodetree(mathexpression, modify_node_tree=None, create_node_tree=True,)

    bl_idname = "GeometryNodeNodeBoosterPythonApi"
    bl_label = "Python Api"

    error_message : bpy.props.StringProperty(
        description="user interface error message",
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
        sett_plugin = get_addon_prefs()

        #check if string is empty first, perhaps user didn't input anything yet 
        if (self.user_expression==""):
            set_socket_label(ng,0, label="Waiting for Input" ,)
            set_socket_defvalue(ng,1, value=True,)
            return None

        #we reset the Error status back to false
        set_socket_defvalue(ng,1, value=False,)
        self.error_message = ""

        try:
            #NOTE, maybe the execution need to check for some sort of blender checks before allowing execution?
            # a little like the driver python expression, there's a global setting for that. Unsure if it's needed.

            namespace = {}
            namespace["bpy"] = bpy
            namespace["D"] = bpy.data
            namespace["C"] = bpy.context
            namespace["context"] = bpy.context
            namespace["scene"] = bpy.context.scene
            namespace.update(vars(__import__('mathutils')))
            namespace.update(vars(__import__('math')))

            #convenience execution for user (he can customize this in plugin preference)
            # NOTE Need sanatization layer here? Hmm
            if (sett_plugin.pynode_namespace1!=""): exec(sett_plugin.pynode_namespace1, {}, namespace,)
            if (sett_plugin.pynode_namespace2!=""): exec(sett_plugin.pynode_namespace2, {}, namespace,)
            if (sett_plugin.pynode_namespace3!=""): exec(sett_plugin.pynode_namespace3, {}, namespace,)

            #evaluated exprtession
            evalexp = eval(self.user_expression, {}, namespace,)

            #translate to list when possible
            if type(evalexp) in (Vector, Euler, bpy.types.bpy_prop_array, tuple,):
                evalexp = list(evalexp)

            match evalexp:

                # TODO could support Quaternion rotation & Matrix evaluation???
                # Would be quite nice to directly execute matrix math code in there..
                
                # TODO could support numpy as well? Hmm.

                case bool():

                    if implicit_conversion and (get_socket_type(ng,0)!="BOOLEAN"):
                        set_socket_type(ng,0, socket_type="NodeSocketBool")
                        self.socket_type = "NodeSocketBool"
                    set_socket_defvalue(ng,0, value=evalexp ,)
                    set_socket_label(ng,0, label=evalexp ,)

                case int():

                    if implicit_conversion and (get_socket_type(ng,0)!="INT"):
                        set_socket_type(ng,0, socket_type="NodeSocketInt")
                        self.socket_type = "NodeSocketInt"
                    set_socket_defvalue(ng,0, value=evalexp ,)
                    set_socket_label(ng,0, label=evalexp ,)

                case float():

                    if implicit_conversion and (get_socket_type(ng,0)!="VALUE"):
                        set_socket_type(ng,0, socket_type="NodeSocketFloat")
                        self.socket_type = "NodeSocketFloat"
                    set_socket_defvalue(ng,0, value=evalexp ,)
                    set_socket_label(ng,0, label=round(evalexp,4) ,)
                
                case list():

                    #evaluate as vector?
                    if (len(evalexp)==3):

                        if implicit_conversion and (get_socket_type(ng,0)!="VECTOR"):
                            set_socket_type(ng,0, socket_type="NodeSocketVector")
                            self.socket_type = "NodeSocketVector"
                        set_socket_defvalue(ng,0, value=evalexp ,)
                        set_socket_label(ng,0, label=[round(n,4) for n in evalexp] ,)
                    
                    #evaluate as color? 
                    elif (len(evalexp)==4):

                        if implicit_conversion and (get_socket_type(ng,0)!="RGBA"):
                            set_socket_type(ng,0, socket_type="NodeSocketColor")
                            self.socket_type = "NodeSocketColor"
                        set_socket_defvalue(ng,0, value=evalexp ,)
                        set_socket_label(ng,0, label=[round(n,4) for n in evalexp] ,)

                    #only vec3 and vec4 are supported
                    else:
                        self.evaluation_error = True
                        raise Exception(f"TypeError: 'List{len(evalexp)}' not supported")

                case str():

                    if implicit_conversion and (get_socket_type(ng,0)!="STRING"):
                        set_socket_type(ng,0, socket_type="NodeSocketString")
                        self.socket_type = "NodeSocketString"
                    set_socket_defvalue(ng,0, value=evalexp ,)
                    set_socket_label(ng,0, label='"'+evalexp+'"' ,)

                case bpy.types.Object():

                    if implicit_conversion and (get_socket_type(ng,0)!="OBJECT"):
                        set_socket_type(ng,0, socket_type="NodeSocketObject")
                        self.socket_type = "NodeSocketObject"
                    set_socket_defvalue(ng,0, value=evalexp,)
                    set_socket_label(ng,0, label=f'D.objects["{evalexp.name}"]',)

                case bpy.types.Collection():

                    if implicit_conversion and (get_socket_type(ng,0)!="COLLECTION"):
                        set_socket_type(ng,0, socket_type="NodeSocketCollection")
                        self.socket_type = "NodeSocketCollection"
                    set_socket_defvalue(ng,0, value=evalexp,)
                    set_socket_label(ng,0, label=f'D.collections["{evalexp.name}"]',)

                case bpy.types.Material():

                    if implicit_conversion and (get_socket_type(ng,0)!="MATERIAL"):
                        set_socket_type(ng,0, socket_type="NodeSocketMaterial")
                        self.socket_type = "NodeSocketMaterial"
                    set_socket_defvalue(ng,0, value=evalexp,)
                    set_socket_label(ng,0, label=f'D.materials["{evalexp.name}"]',)

                case bpy.types.Image():

                    if implicit_conversion and (get_socket_type(ng,0)!="IMAGE"):
                        set_socket_type(ng,0, socket_type="NodeSocketImage")
                        self.socket_type = "NodeSocketImage"
                    set_socket_defvalue(ng,0, value=evalexp,)
                    set_socket_label(ng,0, label=f'D.images["{evalexp.name}"]',)

                case _:
                    raise TypeError(f"'{type(evalexp).__name__.title()}' not supported")

            return get_socket_defvalue(ng,0)

        except Exception as e:

            print(f"{self.bl_idname}: Exception:\n{e}")

            #display error to user
            self.error_message = str(e)
            set_socket_label(ng,0, label=type(e).__name__,)

            #set error socket output to True
            set_socket_defvalue(ng,1, value=True,)

        return None

    def draw_label(self,):
        """node label"""

        return self.bl_label

    def draw_buttons(self, context, layout,):
        """node interface drawing"""

        is_error = bool(self.error_message)

        col = layout.column(align=True)
        row = col.row(align=True)

        field = row.row(align=True)
        field.alert = is_error
        field.prop(self, "user_expression", placeholder="C.object.name", text="",)

        if (is_error):
            lbl = col.row()
            lbl.alert = is_error
            lbl.label(text=self.error_message)

        return None

    @classmethod
    def update_all(cls):
        """search for all nodes of this type and update them"""

        for n in [n for ng in bpy.data.node_groups for n in ng.nodes if (n.bl_idname==cls.bl_idname)]:
            n.update()

        return None