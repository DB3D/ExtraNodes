# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy 

from ..__init__ import get_addon_prefs
from ..utils.node_utils import create_new_nodegroup, set_socket_defvalue, set_socket_type, set_socket_label

from mathutils import * ; from math import * # Conveniences vars! Needed to evaluate the user python expression. 
                                             # Must be done in global space, wild cards not supported within classes.

from collections import namedtuple
RGBAColor = namedtuple('RGBAColor', ['r','g','b','a'])


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
    debug_evaluation_counter : bpy.props.IntProperty(
        name="debug counter",
        default=0,
        )

    def update_signal(self,context):
        """evaluate user expression and change the socket output type implicitly"""
        self.evaluate_python_expression(define_socketype=True)
        return None 

    user_pyapiexp : bpy.props.StringProperty(
        update=update_signal,
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

        return None

    def evaluate_python_expression(self, define_socketype=False,):
        """evaluate the user string and assign value to output node"""

        ng = self.node_tree
        sett_plugin = get_addon_prefs()
        self.debug_evaluation_counter += 1

        #check if string is empty first, perhaps user didn't input anything yet 
        if (self.user_pyapiexp==""):
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

            #recognize self as object using this node? only if valid and not ambiguous
            node_obj_users = self.get_objects_from_node_instance()
            if (len(node_obj_users)==1):
                namespace["self"] = list(node_obj_users)[0]

            #convenience execution for user (he can customize this in plugin preference)
            # NOTE Need sanatization layer here? Hmm
            if (sett_plugin.pynode_namespace1!=""): exec(sett_plugin.pynode_namespace1, {}, namespace,)
            if (sett_plugin.pynode_namespace2!=""): exec(sett_plugin.pynode_namespace2, {}, namespace,)
            if (sett_plugin.pynode_namespace3!=""): exec(sett_plugin.pynode_namespace3, {}, namespace,)

            #evaluated exprtession
            evalexp = eval(self.user_pyapiexp, {}, namespace,)

            #we sanatize out possible types depending on their length
            matrix_special_label = ''
            if (type(evalexp) in {tuple, list, set, Vector, Euler, bpy.types.bpy_prop_array}):

                evalexp = list(evalexp)
                n = len(evalexp)

                if (n == 1):
                    evalexp = float(evalexp[0])

                elif (n <= 3):
                    evalexp = Vector(evalexp + [0.0]*(3 - n))

                elif (n == 4):
                    evalexp = RGBAColor(*evalexp)

                elif (4 < n <= 16):
                    if (n < 16):
                        matrix_special_label = f'List[{len(evalexp)}]'
                        nulmatrix = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                        evalexp.extend(nulmatrix[len(evalexp):])
                    evalexp =  Matrix([evalexp[i*4:(i+1)*4] for i in range(4)])

                else:
                    raise TypeError(f"'{type(evalexp).__name__.title()}' of len {n} not supported")

            #gather the value, label and type we need to set
            set_type = set_value = set_label = None
            match evalexp:

                case bool():
                    set_value = evalexp
                    set_label = str(evalexp)
                    set_type = 'NodeSocketBool'

                case int():
                    set_value = evalexp
                    set_label = str(evalexp)
                    set_type = 'NodeSocketInt'

                case float():
                    set_value = evalexp
                    set_label = str(round(evalexp,4))
                    set_type = 'NodeSocketFloat'
                
                case str():
                    set_value = evalexp
                    set_label = '"'+evalexp+'"'
                    set_type = 'NodeSocketString'

                case Vector():
                    set_value = evalexp
                    set_label = str(tuple(round(n,4) for n in evalexp))
                    set_type = 'NodeSocketVector'
                    
                case RGBAColor():
                    set_value = evalexp
                    set_label = str(tuple(round(n,4) for n in evalexp))
                    set_type = 'NodeSocketColor'

                case Quaternion():
                    set_value = evalexp
                    set_label = str(tuple(round(n,4) for n in evalexp))
                    set_type = 'NodeSocketRotation'
                    
                case Matrix():
                    set_value = evalexp
                    set_label = "MatrixValue" if (not matrix_special_label) else matrix_special_label
                    set_type = 'NodeSocketMatrix'
                    
                case bpy.types.Object():
                    set_value = evalexp
                    set_label = f'D.objects["{evalexp.name}"]'
                    set_type = 'NodeSocketObject'

                case bpy.types.Collection():
                    set_value = evalexp
                    set_label = f'D.collections["{evalexp.name}"]'
                    set_type = 'NodeSocketCollection'

                case bpy.types.Material():
                    set_value = evalexp
                    set_label = f'D.materials["{evalexp.name}"]'
                    set_type = 'NodeSocketMaterial'

                case bpy.types.Image():
                    set_value = evalexp
                    set_label = f'D.images["{evalexp.name}"]'
                    set_type = 'NodeSocketImage'

                case _:
                    raise TypeError(f"'{type(evalexp).__name__.title()}' not supported")

                # case .. TODO could support numpy types as well? Hmm..

            #set the values!
            
            if (define_socketype):
                if (set_type is not None):
                    set_socket_type(ng,0, socket_type=set_type,)

            if (set_label is not None):
                set_socket_label(ng,0, label=set_label ,)

            if (set_value is not None):
                set_socket_defvalue(ng,0, value=set_value ,)            

            return None

        except Exception as e:

            print(f"{self.bl_idname}: Exception:\n{e}")

            msg = str(e)
            if ("name 'self' is not defined" in msg):
                msg = "'self' is not Available in this Context"

            #display error to user
            self.error_message = msg
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
        field.prop(self, "user_pyapiexp", placeholder="C.object.name", text="",)

        if (is_error):
            lbl = col.row()
            lbl.alert = is_error
            lbl.label(text=self.error_message)

        return None

    def get_objects_from_node_instance(self,):
        """Return a list of objects using the given GeometryNodeTree."""
        
        #NOTE could support recur nodegroups perhaps? altho it will cause ambiguity..
        users = set()
        for o in bpy.data.objects:
            for m in o.modifiers:
                if (m.type=='NODES' and m.node_group):
                    for n in m.node_group.nodes:
                        if (n==self):
                            users.add(o)
        return users

    @classmethod
    def update_all(cls):
        """search for all nodes of this type and update them"""

        for n in [n for ng in bpy.data.node_groups for n in ng.nodes if (n.bl_idname==cls.bl_idname)]:
            n.evaluate_python_expression()

        return None