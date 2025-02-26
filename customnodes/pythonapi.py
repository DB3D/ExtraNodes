# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy 

from ..__init__ import get_addon_prefs
from ..nex.pytonode import convert_pyvar_to_data
from ..utils.node_utils import (
    create_new_nodegroup,
    set_socket_defvalue,
    set_socket_type,
    set_socket_label,
)

class NODEBOOSTER_NG_pythonapi(bpy.types.GeometryNodeCustomGroup):
    """Custom Nodgroup: Evaluate a python expression as a single value output.
    • The evaluated values can be of type 'float', 'int', 'Vector', 'Color', 'Quaternion', 'Matrix', 'String', 'Object', 'Collection', 'Material' & 'list/tuple/set' up to len 16"""

    #TODO Optimization: node_utils function should check if value or type isn't already set before setting it.
    
    bl_idname = "GeometryNodeNodeBoosterPythonApi"
    bl_label = "Python Expression"

    error_message : bpy.props.StringProperty(
        description="user interface error message",
        )
    debug_evaluation_counter : bpy.props.IntProperty(
        name="Execution Counter",
        default=0,
        )
    user_pyapiexp : bpy.props.StringProperty(
        update=lambda self, context: self.evaluate_python_expression(define_socketype=True),
        description="type the expression you wish to evaluate right here",
        )
    execute_at_depsgraph : bpy.props.BoolProperty(
        name="Depsgraph Evaluation",
        description="Synchronize the python values with the outputs values on each depsgraph frame and interaction. By toggling this option, your script will be executed constantly.",
        default=True,
        update=lambda self, context: self.evaluate_python_expression(),
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
        self.debug_evaluation_counter += 1 # potential issue with int limit here? idk how blender handle this

        #we reset the Error status back to false
        set_socket_label(ng,1, label="NoErrors",)
        set_socket_defvalue(ng,1, value=False,)
        self.error_message = ''
        
        #check if string is empty first, perhaps user didn't input anything yet 
        if (self.user_pyapiexp==""):
            set_socket_label(ng,0, label="Waiting for Input" ,)
            set_socket_label(ng,1, label="EmptyFieldError",)
            set_socket_defvalue(ng,1, value=True,)
            return None

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
            
        #NOTE, maybe the execution need to check for some sort of blender checks before allowing execution?
        # a little like the driver python expression, there's a global setting for that. Unsure if it's needed.
        
        #convenience namespace execution for user
        # NOTE Need sanatization layer here? Hmmmm. Maybe we can forbid access to the os module?
        # but well, the whole concept of this node is to execute python lines of code..
        try:
            if (sett_plugin.node_pyapi_namespace1!=""): exec(sett_plugin.node_pyapi_namespace1, {}, namespace,)
            if (sett_plugin.node_pyapi_namespace2!=""): exec(sett_plugin.node_pyapi_namespace2, {}, namespace,)
            if (sett_plugin.node_pyapi_namespace3!=""): exec(sett_plugin.node_pyapi_namespace3, {}, namespace,)
        except Exception as e:
            print(f"{self.bl_idname} UserNameSpace Exception '{type(e).__name__}':\n{e}")

            #display error to user
            self.error_message = str(e)
            set_socket_label(ng,0, label=type(e).__name__,)
            set_socket_label(ng,1, label="NameSpaceError",)
            set_socket_defvalue(ng,1, value=True,)
            return None

        #evaluated the user expression
        try:
            evaluated_pyvalue = eval(to_evaluate, {}, namespace,)
        except Exception as e:
            print(f"{self.bl_idname} Evaluation Exception '{type(e).__name__}':\n{e}")

            msg = str(e)
            if ("name 'self' is not defined" in msg):
                msg = "'self' not Available in this Context."

            #display error to user
            self.error_message = msg
            set_socket_label(ng,0, label=type(e).__name__,)
            set_socket_label(ng,1, label="ExecutionError",)
            set_socket_defvalue(ng,1, value=True,)
            return None

        #python to actual values we can use
        try:
            set_value, set_label, socktype = convert_pyvar_to_data(evaluated_pyvalue)
        except Exception as e:
            print(f"{self.bl_idname} Parsing Exception '{type(e).__name__}':\n{e}")

            #display error to user
            self.error_message = str(e)
            set_socket_label(ng,0, label=type(e).__name__,)
            set_socket_label(ng,1, label="ParsingError",)
            set_socket_defvalue(ng,1, value=True,)
            return None
    
        #set values
        if (define_socketype):
            set_socket_type(ng,0, socket_type=socktype,)
        set_socket_label(ng,0, label=set_label ,)
        set_socket_defvalue(ng,0, value=set_value ,)

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

        row.prop(self, "execute_at_depsgraph", text="", icon="TEMP",)
        
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
    def update_all_instances(cls, from_depsgraph=False,):
        """search for all nodes of this type and update them"""

        all_instances = [n for ng in bpy.data.node_groups for n in ng.nodes if (n.bl_idname==cls.bl_idname)]
        for n in all_instances:
            if (from_depsgraph and not n.execute_at_depsgraph):
                continue
            n.evaluate_python_expression()
            continue

        return None