# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy

from .pythonapi import convert_pyvar_to_data
from ..utils.str_utils import word_wrap
from ..utils.node_utils import (
    create_new_nodegroup,
    set_socket_defvalue,
    get_socket_type,
    set_socket_type,
    create_socket,
    remove_socket,
)


class NODEBOOSTER_NG_pythonscript(bpy.types.GeometryNodeCustomGroup):
    """Custom NodeGroup: Executes a Python script from a Blender Text datablock and creates output sockets
    dynamically based on local variables whose names start with 'out_' in the script."""

    #TODO 
    # Could even go harder, and user could call the math expression node within the script to mix with arguments. 
    # Admitting we implement a 'Advanced Math Expression' node that supports Vec/Rot/Matrix ect..
    # Note that if this happens, it would be nicer to have some sort of create_expression_nodetree(mathexpression, modify_node_tree=None, create_node_tree=True,)

    bl_idname = "GeometryNodeNodeBoosterPythonScript"
    bl_label = "Python Constants"

    error_message : bpy.props.StringProperty(
        description="User interface error message"
        )
    debug_evaluation_counter : bpy.props.IntProperty(
        name="debug counter",
        default=0
        )
    user_textdata : bpy.props.PointerProperty(
        type=bpy.types.Text,
        update=lambda self, context: self.evaluate_python_script(),
        name="TextData",
        description="Blender Text datablock to execute",
        )
    launch_script : bpy.props.BoolProperty(
        update=lambda self, context: self.evaluate_python_script(),
        name="Execute",
        description="Click here to execute the script",
        )

    def init(self, context):
        """Called when the node is first added."""

        name = f".{self.bl_idname}"

        ng = bpy.data.node_groups.get(name)
        if (ng is None):
            ng = create_new_nodegroup(name,
                out_sockets={
                    "Error" : "NodeSocketBool",
                },
            )

        ng = ng.copy() #always using a copy of the original ng

        self.node_tree = ng
        self.width = 200
        self.label = self.bl_label

        return None

    def copy(self,node,):
        """fct run when dupplicating the node"""

        self.node_tree = node.node_tree.copy()

        return None 

    def update(self):
        """generic update function"""

        return None

    def cleanse_outputs(self):
        """remove all our outputs"""

        ng = self.node_tree
        out_nod = ng.nodes["Group Output"]

        idx_to_del = []
        for idx,socket in enumerate(out_nod.inputs):
            if ((socket.type!='CUSTOM') and (idx!=0)):
                idx_to_del.append(idx)
                
        for idx in reversed(idx_to_del):
            remove_socket(ng, idx, in_out='OUTPUT')

        return None

    def evaluate_python_script(self):
        """Execute the Python script from a Blender Text datablock, capture local variables whose names start with "out_",
        and update the node group's output sockets accordingly."""

        ng = self.node_tree
        in_nod, out_nod = ng.nodes["Group Input"], ng.nodes["Group Output"]
        self.debug_evaluation_counter += 1
        self.error_message = ''

        # Check if a Blender Text datablock has been specified
        if (self.user_textdata is None):
            # if not, remove unused vars sockets
            self.cleanse_outputs()
            # set error to True
            set_socket_defvalue(ng,0, value=True,)
            return None

        # set error status back to False
        set_socket_defvalue(ng,0, value=False,)

        # Execute the script and capture its local variables
        script_vars = {}
        try:
            exec(self.user_textdata.as_string(), {}, script_vars)
        except Exception as e:
            print(f"{self.bl_idname} Exception:\n{e}")
            # set error to True
            set_socket_defvalue(ng,0, value=True,)
            # Display error
            self.error_message = f'An Error Occured on Script Execution\n{e}'
            return None

        # Filter for variables that start with 'out_'
        out_vars = {k.replace("out_","").replace("_"," "): v for k, v in script_vars.items() if k.startswith("out_") and (k!="out_")}
        if (not out_vars):
            # if not, remove unused vars sockets
            self.cleanse_outputs()
            # set error to True
            set_socket_defvalue(ng,0, value=True,)
            # Display error
            self.error_message = f"No Variables Starting with 'out_' Found in your Script!"
            return None

        # Transform all py values to values we can use
        try:
            # sockname: sockval, socklbl, socktype
            out_vars = {k:convert_pyvar_to_data(v) for k,v in out_vars.items()}
        except Exception as e:
            print(f"{self.bl_idname} Exception:\n{e}")
            # set error to True
            set_socket_defvalue(ng,0, value=True,)
            # Display error
            self.error_message =type(e).__name__ +"\n"+ str(e)
            return None

        # Create new sockets depending on vars
        current_vars = [s.name for s in out_nod.inputs]
        for sockname, (_, socklbl, socktype) in out_vars.items():
            if (sockname not in current_vars):
                create_socket(ng, in_out='OUTPUT', socket_type=socktype, socket_name=sockname,)

        # Remove unused vars sockets
        idx_to_del = []
        for idx,socket in enumerate(out_nod.inputs):
            if (socket.name not in out_vars.keys()):
                if ((socket.type!='CUSTOM') and (idx!=0)):
                    idx_to_del.append(idx)
        for idx in reversed(idx_to_del):
            remove_socket(ng, idx, in_out='OUTPUT')

        # Give it a refresh signal, when we remove/create a lot of sockets, the customnode inputs/outputs needs a kick
        self.update()

        # Make sure socket types are corresponding to their python evaluated values
        for idx,socket in enumerate(out_nod.inputs):
            if ((socket.type!='CUSTOM') and (idx!=0)):
                _, _, socktype = out_vars[socket.name]
                current_type = get_socket_type(ng, idx, in_out='OUTPUT')
                if (current_type!=socktype):
                    set_socket_type(ng, idx, in_out='OUTPUT', socket_type=socktype,)

        # Assign the values to sockets
        for idx,socket in enumerate(out_nod.inputs):
            if ((socket.type!='CUSTOM') and (idx!=0)):
                sockval, _, _ = out_vars[socket.name]
                set_socket_defvalue(ng, idx, value=sockval,)
                
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
        field.prop(self, "user_textdata", text="", icon="TEXT", placeholder="MyScript",)
        
        row.prop(self, "launch_script", text="", icon="PLAY", invert_checkbox=self.launch_script,)

        if (is_error):
            col = col.column(align=True)
            word_wrap(layout=col, alert=True, active=True, max_char=self.width/6, string=self.error_message,)

        return None

    @classmethod
    def update_all(cls):
        """search for all nodes of this type and update them"""

        for n in [n for ng in bpy.data.node_groups for n in ng.nodes if (n.bl_idname==cls.bl_idname)]:
            n.evaluate_python_script()

        return None

