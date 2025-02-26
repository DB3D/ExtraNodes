# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy

from ..nex.pytonode import convert_pyvar_to_data
from ..utils.str_utils import word_wrap
from ..utils.node_utils import (
    create_new_nodegroup,
    set_socket_defvalue,
    get_socket_type,
    set_socket_type,
    create_socket,
    remove_socket,
    set_socket_label,
)


class NODEBOOSTER_NG_pythonscript(bpy.types.GeometryNodeCustomGroup):
    """Custom NodeGroup: Executes a Python script from a Blender Text datablock and creates output sockets
    dynamically based on local variables whose names start with 'out_' in the script."""

    #TODO 
    # Could even go harder, and user could call the math expression node within the script to mix with arguments. 
    # Admitting we implement a 'Advanced Math Expression' node that supports Vec/Rot/Matrix ect..
    # Note that if this happens, it would be nicer to have some sort of create_expression_nodetree(mathexpression, modify_node_tree=None, create_node_tree=True,)

    #TODO Optimization: node_utils function should check if value or type isn't already set before setting it.
    #TODO maybe should add a nodebooster panel in text editor for quick execution?

    bl_idname = "GeometryNodeNodeBoosterPythonScript"
    bl_label = "Python Constant Script"

    error_message : bpy.props.StringProperty(
        description="User interface error message"
        )
    debug_evaluation_counter : bpy.props.IntProperty(
        name="Execution Counter",
        default=0
        )
    user_textdata : bpy.props.PointerProperty(
        type=bpy.types.Text,
        name="TextData",
        description="Blender Text datablock to execute",
        poll=lambda self,data: not data.name.startswith('.'),
        update=lambda self, context: self.evaluate_python_script(),
        )
    execute_script : bpy.props.BoolProperty(
        name="Execute",
        description="Click here to execute the script",
        update=lambda self, context: self.evaluate_python_script(),
        )
    execute_at_depsgraph : bpy.props.BoolProperty(
        name="Depsgraph Evaluation",
        description="Synchronize the python values on each depsgraph frame and interaction with the outputs. By toggling your feature, your script will be executed constantly.",
        default=True,
        update=lambda self, context: self.evaluate_python_script(),
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

    def store_text_data_as_frame(self, text):
        """we store the user text data as a frame"""

        ng = self.node_tree

        frame = ng.nodes.get("ScriptStorage")
        if (frame is None):
            frame = ng.nodes.new('NodeFrame')
            frame.name = frame.label = "ScriptStorage"
            frame.width = 500
            frame.height = 1500
            frame.location.x = -750
            frame.label_size = 8

        if (frame.text!=text):
            frame.text = text

        return None

    def evaluate_python_script(self):
        """Execute the Python script from a Blender Text datablock, capture local variables whose names start with "out_",
        and update the node group's output sockets accordingly."""

        ng = self.node_tree
        in_nod, out_nod = ng.nodes["Group Input"], ng.nodes["Group Output"]
        self.debug_evaluation_counter += 1 # potential issue with int limit here? idk how blender handle this
        self.error_message = ''

        #we reset the Error status back to false
        set_socket_label(ng,0, label="NoErrors",)
        set_socket_defvalue(ng,0, value=False,)
        self.error_message = ''
        
        self.store_text_data_as_frame(self.user_textdata)
        
        # Check if a Blender Text datablock has been specified
        if (self.user_textdata is None):
            # if not, remove unused vars sockets
            self.cleanse_outputs()
            # set error to True
            set_socket_label(ng,0, label="EmptyTextError",)
            set_socket_defvalue(ng,0, value=True,)
            return None

        # Execute the script and capture its local variables
        script_vars = {}
        try:
            exec(self.user_textdata.as_string(), {}, script_vars)
        except Exception as e:
            print(f"{self.bl_idname} Execution Exception '{type(e).__name__}':\n{e}")
            # set error to True
            set_socket_label(ng,0, label="ExecutionError",)
            set_socket_defvalue(ng,0, value=True,)
            # Display error
            self.error_message = f"Script Execution Error. {e}"
            return None

        # Filter for variables that start with 'out_'
        out_vars = {k.replace("out_","").replace("_"," "): v for k, v in script_vars.items() if k.startswith("out_") and (k!="out_")}
        if (not out_vars):
            # if not, remove unused vars sockets
            self.cleanse_outputs()
            # set error to True
            set_socket_label(ng,0, label="NoVarFoundError",)
            set_socket_defvalue(ng,0, value=True,)
            # Display error
            self.error_message = f"No 'out_' Variables Found in your Script!"
            return None

        # Transform all py values to values we can use
        # {sockname: sockval, socklbl, socktype}
        out_elems = {}
        try:
            for k,v in out_vars.items():
                out_elems[k] = convert_pyvar_to_data(v)
        except Exception as e:
            print(f"{self.bl_idname} Parsing Exception '{type(e).__name__}':\n   for variable '{k}' | value '{v}' | type '{type(v)}'\n{e}")
            # set error to True
            set_socket_label(ng,0, label="ParsingError",)
            set_socket_defvalue(ng,0, value=True,)
            # Display error
            self.error_message = f"Socket '{k}' {type(e).__name__}. {str(e)}"
            return None

        # Create new sockets depending on vars
        current_vars = [s.name for s in out_nod.inputs]
        for sockname, (_, _, socktype) in out_elems.items():
            if (sockname not in current_vars):
                create_socket(ng, in_out='OUTPUT', socket_type=socktype, socket_name=sockname,)

        # Remove unused vars sockets
        idx_to_del = []
        for idx,socket in enumerate(out_nod.inputs):
            if (socket.name not in out_elems.keys()):
                if ((socket.type!='CUSTOM') and (idx!=0)):
                    idx_to_del.append(idx)
        for idx in reversed(idx_to_del):
            remove_socket(ng, idx, in_out='OUTPUT')

        # Give it a refresh signal, when we remove/create a lot of sockets, the customnode inputs/outputs need a kick
        self.update()

        # Make sure socket types are corresponding to their python evaluated values
        for idx,socket in enumerate(out_nod.inputs):
            if ((socket.type!='CUSTOM') and (idx!=0)):
                _, _, socktype = out_elems[socket.name]
                current_type = get_socket_type(ng, idx, in_out='OUTPUT')
                if (current_type!=socktype):
                    set_socket_type(ng, idx, in_out='OUTPUT', socket_type=socktype,)

        # Assign the values to sockets
        for idx,socket in enumerate(out_nod.inputs):
            if ((socket.type!='CUSTOM') and (idx!=0)):
                sockval, _, _ = out_elems[socket.name]
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
        
        row.prop(self, "execute_at_depsgraph", text="", icon="TEMP",)
        row.prop(self, "execute_script", text="", icon="PLAY", invert_checkbox=self.execute_script,)

        if (is_error):
            col = col.column(align=True)
            word_wrap(layout=col, alert=True, active=True, max_char=self.width/6, string=self.error_message,)

        return None

    @classmethod
    def update_all_instances(cls, from_depsgraph=False,):
        """search for all nodes of this type and update them"""

        all_instances = [n for ng in bpy.data.node_groups for n in ng.nodes if (n.bl_idname==cls.bl_idname)]
        for n in all_instances:
            if (from_depsgraph and not n.execute_at_depsgraph):
                continue
            n.evaluate_python_script()
            continue

        return None

