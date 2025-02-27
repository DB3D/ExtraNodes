# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy

import re

from ..__init__ import get_addon_prefs
from ..nex.nextypes import NexFactory, NexError
from ..utils.str_utils import word_wrap
from ..utils.node_utils import (
    create_new_nodegroup,
    set_socket_defvalue,
    remove_socket,
    set_socket_label,
)


def transform_nex_script(pyscript:str, nexames:str) -> str:
    """
    Transforms a Nex script by first removing any comments and then replacing type declarations 
    of the form: varname : TYPE = RESTOFTHELINE
    with: varname = TYPE('varname', RESTOFTHELINE)
    """
    
    # Remove comments: delete anything from a '#' to the end of the line.
    script_no_comments = re.sub(r'#.*', '', pyscript)
    
    # Replacement function to inject the constructor call.
    def replacer(match):
        varname, typename, rest = match.groups()
        return f"{varname} = {typename}('{varname}', {rest.strip()})"
    
    pattern = re.compile(rf"\b(\w+)\s*:\s*({'|'.join(nexames)})\s*=\s*(.+)")
    transformed = pattern.sub(replacer, script_no_comments)
    
    return transformed


class NODEBOOSTER_NG_nexinterpreter(bpy.types.GeometryNodeCustomGroup):
    """Custom NodeGroup: Executes a Python script containing 'Nex' language. 'Nex' stands for nodal expression.\
    With Nex, you can efficiently and easily interpret python code into Geometry-Node nodal programming.
    • WIP text about synthax.
    • WIP text about how it works"""

    #TODO Optimization: node_utils function should check if value or type isn't already set before setting it.
    #TODO maybe should add a nodebooster panel in text editor for quick execution?

    bl_idname = "GeometryNodeNodeBoosterNexInterpreter"
    bl_label = "Nex Script (WIP)"

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
        update=lambda self, context: self.interpret_nex_script(build_tree=True),
        )
    execute_script : bpy.props.BoolProperty(
        name="Execute",
        description="Click here to execute the Nex script, the",
        update=lambda self, context: self.interpret_nex_script(build_tree=True),
        )
    execute_at_depsgraph : bpy.props.BoolProperty(
        name="Depsgraph Evaluation",
        description="Synchronize the interpreted python constants (if any) with the outputs values on each depsgraph frame and interaction. By toggling this option, your Nex script will be executed constantly on each interaction you have with blender (note that the internal nodetree will not be constantly rebuilt, press the Play button to do so.).",
        default=False,
        update=lambda self, context: self.interpret_nex_script(build_tree=False),
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

    def cleanse_sockets(self):
        """remove all our outputs"""

        ng = self.node_tree
        in_nod, out_nod = ng.nodes["Group Input"], ng.nodes["Group Output"]

        for sockets, mode in zip((in_nod.outputs, out_nod.inputs),('INPUT','OUTPUT')):

            idx_to_del = []
            for idx,socket in enumerate(sockets):
                if (mode=='OUTPUT' and idx==0):
                    continue #skip error socket
                if (socket.type=='CUSTOM'):
                    continue
                idx_to_del.append(idx)
                continue

            for idx in reversed(idx_to_del):
                remove_socket(ng, idx, in_out=mode,)

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

    def interpret_nex_script(self, build_tree=False,):
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

        #Keepsafe the text data as extra user
        self.store_text_data_as_frame(self.user_textdata)
        
        # Remove all sockets? only for some executions.
        # we don't want the tree to be constantly rebuilt on each frames
        # TODO: this is a bit annoying because the users links will all disapear even if vars don't changes..
        #  maybe it's best to do a prerun of the script and see if the vars are still valid, then then?
        #  and maybe, the VecTypes should NEVER create new sockets, just link them. Hmm. nice idea.
        if (build_tree):
            self.cleanse_sockets()

        # Check if a Blender Text datablock has been specified
        if (self.user_textdata is None):
            # set error to True
            set_socket_label(ng,0, label="EmptyTextError",)
            set_socket_defvalue(ng,0, value=True,)
            return None

        user_script = self.user_textdata.as_string()

        #define all possible Nex types user can toy with
        nexintypes = {
            'infloat': NexFactory(self, 'NexFloat', build_tree=build_tree,),
            # 'inauto': NexFactory(self, 'NexAuto', build_tree=build_tree,), #TODO for later
            }
        nexoutypes = {
            'outbool': NexFactory(self, 'NexOutput', 'NodeSocketBool', build_tree=build_tree,),
            'outint': NexFactory(self, 'NexOutput', 'NodeSocketInt', build_tree=build_tree,),
            'outfloat': NexFactory(self, 'NexOutput', 'NodeSocketFloat', build_tree=build_tree,),
            'outvec': NexFactory(self, 'NexOutput', 'NodeSocketVector', build_tree=build_tree,),
            'outcol': NexFactory(self, 'NexOutput', 'NodeSocketColor', build_tree=build_tree,),
            'outquat': NexFactory(self, 'NexOutput', 'NodeSocketRotation', build_tree=build_tree,),
            'outmat': NexFactory(self, 'NexOutput', 'NodeSocketMatrix', build_tree=build_tree,),
            # 'outauto': NexFactory(self, 'NexOutput', build_tree=build_tree,), #TODO for later
            }
        nextypes = {**nexintypes, **nexoutypes}

        #make sure there are Nex types in the user expression
        if not any(t in user_script for t in nextypes.keys()):
            # set error to True
            set_socket_label(ng,0, label="VoidNexError",)
            set_socket_defvalue(ng,0, value=True,)
            # Display error
            self.error_message = f"No Nex Found in Script." #TODO tell user they can create a template in text editors headers.
            return None

        #also make sure there are Nex outputs types in there..
        if not any(t in user_script for t in nexoutypes.keys()):
            # set error to True
            set_socket_label(ng,0, label="NoOutputError",)
            set_socket_defvalue(ng,0, value=True,)
            # Display error
            self.error_message = f"No Mandatory Nex Outputs in Script." #TODO tell user they can create a template in text editors headers.
            return None
        
        #TODO will need to make sure there are no vars with same names!!!!! will cause Errors.
        # if n...:
        #     # set error to True
        #     set_socket_label(ng,0, label="VarsDoubleError",)
        #     set_socket_defvalue(ng,0, value=True,)
        #     # Display error
        #     self.error_message = f"Bla." #TODO tell user they can create a template in text editors headers.
        #     return None
        
        # replace varname:infloat=REST with varname=infloat('varname',REST) & remove comments
        # much better workflow for artists to use python type indications IMO
        final_script = transform_nex_script(user_script, nextypes.keys(),)
        
        # inject Nex types in user namespace
        # Execute the script and capture its local variables
        exec_namespace = {}
        exec_namespace.update(nextypes)

        #auto type would be nice?
        #TODO exec_namespace['inauto'] = NexFactory(ng,'NexAny')
        #TODO exec_namespace['outauto'] = NexFactory(ng,'NexOutput','Anytype')

        script_vars = {}

        # for debug mode, we execute without try except to catch 'real' errors with more details. 
        # the exception we raise are designed for the users, not for ourselves devs
        if True:#TODO(get_addon_prefs().debug):
            print(f"\n{'-'*50}")
            print("USER EXPRESSION:")
            print('"""\n'+user_script+'\n"""')
            print("TRANSFORMED EXPRESSION:")
            print('"""\n'+final_script+'\n"""')
            print("ERROR(?):")
            exec(final_script, exec_namespace, script_vars)
            return None

        try:
            exec(final_script, exec_namespace, script_vars)
            
        except NexError as e:
            print(f"{self.bl_idname} Nex Execution Exception:\n{e}")
            # set error to True
            set_socket_label(ng,0, label="NexError",)
            set_socket_defvalue(ng,0, value=True,)
            # Display error
            self.error_message = f"{type(e).__name__}. {e}"
            return None
        
        except Exception as e:
            print(f"{self.bl_idname} Python Execution Exception '{type(e).__name__}':\n{e}")
            # set error to True
            set_socket_label(ng,0, label="PythonError",)
            set_socket_defvalue(ng,0, value=True,)
            # Display error
            self.error_message = f"{type(e).__name__}. {e}"
            return None

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
        field.prop(self, "user_textdata", text="", icon="TEXT", placeholder="NexScript.py",)
        
        row.prop(self, "execute_at_depsgraph", text="", icon="TEMP",)
        row.prop(self, "execute_script", text="", icon="PLAY", invert_checkbox=self.execute_script,)

        if (is_error):
            col = col.column(align=True)
            word_wrap(layout=col, alert=True, active=True, max_char=self.width/6, string=self.error_message,)

        return None

    @classmethod
    def update_all_instances(cls, from_depsgraph=False,):
        """search for all nodes of this type and update them"""

        # TODO need to find a solution to feed python values to nex ng constants

        # all_instances = [n for ng in bpy.data.node_groups for n in ng.nodes if (n.bl_idname==cls.bl_idname)]
        # for n in all_instances:
        #     if (from_depsgraph and not n.execute_at_depsgraph):
        #         continue
        #     # n.interpret_nex_script(build_tree=False)
        #     # NOTE we cannot evaluate the nex script as a whole on each depsgraph updates.. 
        #     # We need a more optimized way to deal with this. Recognize the constants we've created and only update thoses. Maybe we need to mark them somehow? in the name
        #     # Hmm idk...
        #     continue

        return None

