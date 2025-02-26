# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy 

from ..__init__ import get_addon_prefs
from ..utils.node_utils import (
    create_new_nodegroup,
    set_socket_defvalue,
    set_socket_type,
    set_socket_label,
)

from mathutils import Color, Euler, Matrix, Quaternion, Vector
from collections import namedtuple
RGBAColor = namedtuple('RGBAColor', ['r','g','b','a'])


def convert_pyvar_to_data(py_variable):
    """Convert a given python variable into data we can use to create and assign sockets"""
    #TODO do we want to support numpy as well? or else?
    
    value = py_variable
    
    #we sanatize out possible types depending on their length
    matrix_special_label = ''
    if (type(value) in {tuple, list, set, Vector, Euler, bpy.types.bpy_prop_array}):

        value = list(value)
        n = len(value)

        if (n == 1):
            value = float(value[0])

        elif (n <= 3):
            value = Vector(value + [0.0]*(3 - n))

        elif (n == 4):
            value = RGBAColor(*value)

        elif (4 < n <= 16):
            if (n < 16):
                matrix_special_label = f'List[{len(value)}]'
                nulmatrix = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                value.extend(nulmatrix[len(value):])
            value =  Matrix([value[i*4:(i+1)*4] for i in range(4)])

        else:
            raise TypeError(f"'{type(value).__name__.title()}' of len {n} not supported")

    match value:

        case bool():
            repr_label = str(value)
            socket_type = 'NodeSocketBool'

        case int():
            repr_label = str(value)
            socket_type = 'NodeSocketInt'

        case float():
            repr_label = str(round(value,4))
            socket_type = 'NodeSocketFloat'

        case str():
            repr_label = '"'+value+'"'
            socket_type = 'NodeSocketString'

        case Vector():
            repr_label = str(tuple(round(n,4) for n in value))
            socket_type = 'NodeSocketVector'

        case Color():
            value = RGBAColor(*value,1) #add alpha channel
            repr_label = str(tuple(round(n,4) for n in value))
            socket_type = 'NodeSocketColor'
            
        case RGBAColor():
            repr_label = str(tuple(round(n,4) for n in value))
            socket_type = 'NodeSocketColor'

        case Quaternion():
            repr_label = str(tuple(round(n,4) for n in value))
            socket_type = 'NodeSocketRotation'

        case Matrix():
            repr_label = "MatrixValue" if (not matrix_special_label) else matrix_special_label
            socket_type = 'NodeSocketMatrix'

        case bpy.types.Object():
            repr_label = f'D.objects["{value.name}"]'
            socket_type = 'NodeSocketObject'

        case bpy.types.Collection():
            repr_label = f'D.collections["{value.name}"]'
            socket_type = 'NodeSocketCollection'

        case bpy.types.Material():
            repr_label = f'D.materials["{value.name}"]'
            socket_type = 'NodeSocketMaterial'

        case bpy.types.Image():
            repr_label = f'D.images["{value.name}"]'
            socket_type = 'NodeSocketImage'

        case _:
            raise TypeError(f"'{type(value).__name__.title()}' not supported")
    
    return value, repr_label, socket_type


class NODEBOOSTER_NG_pythonapi(bpy.types.GeometryNodeCustomGroup):
    """Custom Nodgroup: Evaluate a python expression as a single value output.
    The evaluated type can be of type 'float', 'int', 'string', 'object', 'collection', 'material'.
    By default the values will be updated automatically on each on depsgraph post and frame_pre signals"""

    bl_idname = "GeometryNodeNodeBoosterPythonApi"
    bl_label = "Python Constant"

    error_message : bpy.props.StringProperty(
        description="user interface error message",
        )
    debug_evaluation_counter : bpy.props.IntProperty(
        name="debug counter",
        default=0,
        )
    user_pyapiexp : bpy.props.StringProperty(
        update=lambda self, context: self.evaluate_python_expression(define_socketype=True),
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
        self.error_message = ''
        
        #check if string is empty first, perhaps user didn't input anything yet 
        if (self.user_pyapiexp==""):
            set_socket_label(ng,0, label="Waiting for Input" ,)
            set_socket_defvalue(ng,1, value=True,)
            return None

        #we reset the Error status back to false
        set_socket_defvalue(ng,1, value=False,)

        try:
            #NOTE, maybe the execution need to check for some sort of blender checks before allowing execution?
            # a little like the driver python expression, there's a global setting for that. Unsure if it's needed.

            to_evaluate = self.user_pyapiexp

            #support for macros
            if ('#frame' in to_evaluate):
                to_evaluate = to_evaluate.replace('#frame','scene.frame_current')

            #define user namespace
            namespace = {}
            namespace["bpy"] = bpy
            namespace["D"] = bpy.data
            namespace["C"] = bpy.context
            namespace["context"] = bpy.context
            namespace["scene"] = bpy.context.scene
            namespace.update(vars(__import__('mathutils')))
            namespace.update(vars(__import__('math')))

            #'self' as object using this node? only if valid and not ambiguous
            node_obj_users = self.get_objects_from_node_instance()
            if (len(node_obj_users)==1):
                namespace["self"] = list(node_obj_users)[0]

            #convenience namespace execution for user
            # NOTE Need sanatization layer here? Hmmmm. Maybe we can forbid access to the os module?
            # but well, the whole concept of this node is to execute python lines of code..
            if (sett_plugin.node_pyapi_namespace1!=""): exec(sett_plugin.node_pyapi_namespace1, {}, namespace,)
            if (sett_plugin.node_pyapi_namespace2!=""): exec(sett_plugin.node_pyapi_namespace2, {}, namespace,)
            if (sett_plugin.node_pyapi_namespace3!=""): exec(sett_plugin.node_pyapi_namespace3, {}, namespace,)

            #evaluated exprtession
            evaluated_pyvalue = eval(to_evaluate, {}, namespace,)

            #python to actual values we can use
            set_value, set_label, socktype = convert_pyvar_to_data(evaluated_pyvalue)

            #set values
            if (define_socketype):
                set_socket_type(ng,0, socket_type=socktype,)
                #HERE maybe we can simply check type and replace if not
            set_socket_label(ng,0, label=set_label ,)
            set_socket_defvalue(ng,0, value=set_value ,)            

            return None

        except Exception as e:
            print(f"{self.bl_idname} Exception:\n{e}")

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