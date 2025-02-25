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

    bl_idname = "GeometryNodeNodeBoosterPythonApi"
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

        #catch any exception, and report error to node
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
                    self.evaluation_error = True
                    raise Exception(f"TypeError: '{type(evalexp).__name__.title()}' not supported")

            #no error, then return False to error output socket
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
        #icon = 'ERROR' if self.evaluation_error else 'SCRIPT'
        row.prop(self, "user_expression", placeholder="C.object.name", text="",) #icon=icon,) # Use an icon for the text field?

        return None

    @classmethod
    def update_all(cls):
        """search for all nodes of this type and update them"""

        for n in [n for ng in bpy.data.node_groups for n in ng.nodes if (n.bl_idname==cls.bl_idname)]:
            n.update()

        return None