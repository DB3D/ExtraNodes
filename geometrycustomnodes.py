# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN, SLU
#
# SPDX-License-Identifier: GPL-2.0-or-later


#NOTE: See https://docs.blender.org/api/blender2.8/bpy.app.handlers.html?highlight=handler#module-bpy.app.handlers 
#      for original notes abouyt this technique


import bpy 

from mathutils import * # Conveniences vars for 'GeometryNodeExtraNodesPythonApi' 
from math import *      # Needed to eval user python expression (cannot import a wildcard within the class).


#Boiler plate functions:


def get_socket_interface_item(ng, idx, in_out='OUTPUT',):
    """return a given socket index as an interface item"""
        
    for itm in ng.interface.items_tree:
        if (itm.in_out == in_out):
            if (itm.position == idx):
                return itm
    
    return None

def get_socket_value(ng, idx, in_out='OUTPUT',):
    """return the value of the given nodegroups output at given socket idx"""
    
    return ng.nodes["Group Output"].inputs[idx].default_value

def set_socket_value(ng, idx, in_out='OUTPUT', value=None,):
    """set the value of the given nodegroups output at given socket idx"""
    
    ng.nodes["Group Output"].inputs[idx].default_value = value 
    
    return None

def set_socket_label(ng, idx, in_out='OUTPUT', label=None,):
    """return the label of the given nodegroups output at given socket idx"""
    
    itm = get_socket_interface_item(ng, idx, in_out=in_out,)
    itm.name = str(label)
                
    return None  

def get_socket_type(ng, idx, in_out='OUTPUT',):
    """return the type of the given nodegroups output at given socket idx"""
    
    itm = get_socket_interface_item(ng, idx, in_out=in_out,)
    return itm.socket_type
    
def set_socket_type(ng, idx, in_out='OUTPUT', socket_type="NodeSocketFloat",):
    """set socket type via bpy.ops.node.tree_socket_change_type() with manual override, context MUST be the geometry node editor"""

    itm = get_socket_interface_item(ng, idx, in_out=in_out,)
    itm.socket_type = socket_type

    return None

def create_socket(ng, in_out='OUTPUT', socket_type="NodeSocketFloat", socket_name="Value",):
    """create a new socket output of given type for given nodegroup"""
    
    return ng.interface.new_socket(socket_name, in_out=in_out, socket_type=socket_type,)

def remove_socket(ng, idx, in_out='OUTPUT',):
    """remove a nodegroup socket output at given index"""
        
    itm = get_socket_interface_item(ng, idx, in_out=in_out,)
    ng.interface.remove(itm)
    
    return None 

def create_new_nodegroup(name, in_sockets={}, out_sockets={},):
    """create new nodegroup with outputs from given dict {"name":"type",}"""

    ng = bpy.data.node_groups.new(name=name, type="GeometryNodeTree")
    
    #create main input/output
    in_node = ng.nodes.new("NodeGroupInput")
    in_node.location.x -= 200
    out_node = ng.nodes.new("NodeGroupOutput")
    out_node.location.x += 200

    #create the sockets
    for socket_name, socket_type in in_sockets.items():
        create_socket(ng, in_out='INPUT', socket_type=socket_type, socket_name=socket_name)
    for socket_name, socket_type in out_sockets.items():
        create_socket(ng, in_out='OUTPUT', socket_type=socket_type, socket_name=socket_name)
        
    return ng


#The custom nodes:


class EXTRANODES_NG_isrenderedview(bpy.types.GeometryNodeCustomGroup):
    """Custom Nodgroup: Evaluate if any viewport is in rendered view mode
    The value is evaluated from depsgraph"""
    
    bl_idname = "GeometryNodeExtraNodesIsRenderedView"
    bl_label = "Is Rendered View"

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
                    "Is Rendered View" : "NodeSocketBool",
                },
            )

        self.node_tree = ng
        self.width = 140
        self.label = self.bl_label

        return None 
    
    def draw_label(self,):
        """node label"""
        
        return self.bl_label

    def draw_buttons(self, context, layout,):
        """node interface drawing"""

        from . __init__ import get_addon_prefs
        
        if (get_addon_prefs().debug):
            box = layout.column()
            box.active = False
            box.template_ID(self, "node_tree")
        
        return None 


class EXTRANODES_NG_camerainfo(bpy.types.GeometryNodeCustomGroup):

    bl_idname = "GeometryNodeExtraNodesCameraInfo"
    bl_label = "Camera info"

    use_scene_cam: bpy.props.BoolProperty(
        default=True,
        )

    def camera_obj_poll(self, obj):
        return obj.type == 'CAMERA'
    
    camera_obj: bpy.props.PointerProperty(
        type=bpy.types.Object,
        poll=camera_obj_poll,
        )

    @classmethod
    def poll(cls, context):
        """mandatory poll"""
        return True

    def init(self, context):
        """this fct run when appending the node for the first time"""

        name = f".{self.bl_idname}"

        ng = bpy.data.node_groups.get(name)
        if (ng is None):
            ng = create_new_nodegroup(name,
                out_sockets={
                    "Camera Object" : "NodeSocketObject",
                    "Field of View" : "NodeSocketFloat",
                    "Shift X" : "NodeSocketFloat",
                    "Shift Y" : "NodeSocketFloat",
                    "Clip Start" : "NodeSocketFloat",
                    "Clip End" : "NodeSocketFloat",
                    "Resolution X" : "NodeSocketInt",
                    "Resolution Y" : "NodeSocketInt",
                },
            )
         
        ng = ng.copy() #always using a copy of the original ng
        
        self.node_tree = ng
        self.label = self.bl_label

        return None

    def copy(self, node):
        """fct run when dupplicating the node"""
        
        self.node_tree = node.node_tree.copy()
        
        return None

    def update(self):
        """generic update function"""

        scene = bpy.context.scene
        cam_obj = scene.camera if (self.use_scene_cam) else self.camera_obj
        set_socket_value(self.node_tree, 0, cam_obj)
        
        if (cam_obj and cam_obj.data):
            set_socket_value(self.node_tree, 1, cam_obj.data.angle)
            set_socket_value(self.node_tree, 2, cam_obj.data.shift_x)
            set_socket_value(self.node_tree, 3, cam_obj.data.shift_y)
            set_socket_value(self.node_tree, 4, cam_obj.data.clip_start)
            set_socket_value(self.node_tree, 5, cam_obj.data.clip_end)
            set_socket_value(self.node_tree, 6, scene.render.resolution_x)
            set_socket_value(self.node_tree, 7, scene.render.resolution_y)

        return None

    def draw_label(self,):
        """node label"""
        
        return self.bl_label

    def draw_buttons(self, context, layout):
        """node interface drawing"""

        from . __init__ import get_addon_prefs
        
        row = layout.row(align=True)
        sub = row.row(align=True)
        sub.active = not self.use_scene_cam
        
        if (self.use_scene_cam):
            sub.prop(bpy.context.scene, "camera", text="", icon="CAMERA_DATA")
        else:
            sub.prop(self, "camera_obj", text="", icon="CAMERA_DATA")
        
        row.prop(self, "use_scene_cam", text="", icon="SCENE_DATA")

        if (get_addon_prefs().debug):
            box = layout.column()
            box.active = False
            box.template_ID(self, "node_tree")

        return None

    @classmethod
    def update_all(cls):
        """search for all nodes of this type and update them"""
        
        for n in [n for ng in bpy.data.node_groups for n in ng.nodes if (n.bl_idname==cls.bl_idname)]:
            n.update()
            
        return None 


class EXTRANODES_NG_sequencervolume(bpy.types.GeometryNodeCustomGroup):
    
    bl_idname = "GeometryNodeExtraNodesSequencerVolume"
    bl_label = "Sequencer Volume"

    # frame_delay : bpy.props.IntProperty()

    @classmethod
    def poll(cls, context):
        """mandatory poll"""
        return True

    def init(self,context,):        
        """this fct run when appending the node for the first time"""

        name = f".{self.bl_idname}"

        ng = bpy.data.node_groups.get(name)
        if (ng is None):
            ng = create_new_nodegroup(name,
                out_sockets={
                    "Volume" : "NodeSocketFloat",
                },
            )
            
        ng = ng.copy() #always using a copy of the original ng
         
        self.node_tree = ng
        self.width = 150
        self.label = self.bl_label

        return None 

    def copy(self,node,):
        """fct run when dupplicating the node"""
        
        self.node_tree = node.node_tree.copy()
        
        return None 
    
    def update(self):
        """generic update function"""
        
        ng = self.node_tree
        
        # for later?
        # frame = None 
        # if (self.frame_delay):
        #     frame = bpy.context.scene.frame_current + self.frame_delay

        set_socket_value(ng,0,
            value=self.evaluate_sequencer_volume(),
            )

        return None

    def evaluate_sequencer_volume(self, frame=None,):
        """evaluate the sequencer volume source
        this node was possible thanks to tintwotin https://github.com/snuq/VSEQF/blob/3ac717e1fa8c7371ec40503428bc2d0d004f0b35/vseqf.py#L142"""

        #TODO ideally we need to also sample volume from few frame before or after, so user can create a smoothing falloff of some sort, 
        #     that's what 'frame_delay' is for, but unfortunately this function is incomplete, frame can only be None in order to work
        #     right now i do not have the strength to do it, you'll need to check for 'fades.get_fade_curve(bpy.context, sequence, create=False)' from the github link above

        scene = bpy.context.scene
        if (scene.sequence_editor is None):
            return 0
        
        totvolume = 0
        sequences = scene.sequence_editor.sequences_all
        depsgraph = bpy.context.evaluated_depsgraph_get()
        
        if (frame is None):
              frame = scene.frame_current
              evaluate_volume = False
        else: evaluate_volume = True

        fps = scene.render.fps / scene.render.fps_base

        for sequence in sequences:

            if ((sequence.type=='SOUND') and (sequence.frame_final_start<frame) 
                and (sequence.frame_final_end>frame) and (not sequence.mute)):
               
                time_from = (frame - 1 - sequence.frame_start) / fps
                time_to = (frame - sequence.frame_start) / fps

                audio = sequence.sound.evaluated_get(depsgraph).factory
                chunk = audio.limit(time_from, time_to).data()
                
                #sometimes the chunks cannot be read properly, try to read 2 frames instead
                if (len(chunk)==0):
                    time_from_temp = (frame - 2 - sequence.frame_start) / fps
                    chunk = audio.limit(time_from_temp, time_to).data()
                    
                #chunk still couldnt be read...
                if (len(chunk)==0):
                    average = 0

                else:
                    cmax, cmin = abs(chunk.max()), abs(chunk.min())
                    average = cmax if (cmax > cmin) else cmin

                if evaluate_volume:
                    # TODO: for later? get fade curve https://github.com/snuq/VSEQF/blob/8487c256db536eb2e9288a16248fe394d06dfb74/fades.py#L57
                    # fcurve = get_fade_curve(bpy.context, sequence, create=False)
                    # if (fcurve):
                    #       volume = fcurve.evaluate(frame)
                    # else: volume = sequence.volume
                    volume = 0
                else:
                    volume = sequence.volume

                totvolume += (average * volume)
            
            continue 

        return float(totvolume)
    
    def draw_label(self,):
        """node label"""
        
        return self.bl_label

    def draw_buttons(self,context,layout,):
        """node interface drawing"""

        from . __init__ import get_addon_prefs
        
        #for later?
        #layout.prop(self,"frame_delay",text="Frame Delay")

        if (get_addon_prefs().debug):
            box = layout.column()
            box.active = False
            box.template_ID(self, "node_tree")

        return None 

    @classmethod
    def update_all(cls):
        """search for all nodes of this type and update them"""

        for n in [n for ng in bpy.data.node_groups for n in ng.nodes if (n.bl_idname==cls.bl_idname)]:
            n.update()

        return None


class EXTRANODES_NG_pythonapi(bpy.types.GeometryNodeCustomGroup):
    """Custom Nodgroup: Evaluate a python expression as a single value output
    the evaluated type can be a float, int, string, object. By default the values will be updated on depsgraph"""
    
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
        bpy.context.space_data.node_tree["extranodes_pythonapi_updateflag"] = True

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

        from . __init__ import get_addon_prefs
        ng = self.node_tree

        #check if string is empty first, perhaps user didn't input anything yet 
        if (self.user_expression==""):

            set_socket_value(ng,1, value=True,)
            set_socket_label(ng,0, label="Waiting for Input" ,)

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
                    set_socket_value(ng,0, value=value ,)
                    set_socket_label(ng,0, label=value ,)

                case int():

                    if implicit_conversion and (get_socket_type(ng,0)!="INT"):
                        set_socket_type(ng,0, socket_type="NodeSocketInt")
                        self.socket_type = "NodeSocketInt"
                    set_socket_value(ng,0, value=value ,)
                    set_socket_label(ng,0, label=value ,)

                case float():

                    if implicit_conversion and (get_socket_type(ng,0)!="VALUE"):
                        set_socket_type(ng,0, socket_type="NodeSocketFloat")
                        self.socket_type = "NodeSocketFloat"
                    set_socket_value(ng,0, value=value ,)
                    set_socket_label(ng,0, label=round(value,4) ,)
                
                case list():

                    #evaluate as vector?
                    if (len(value)==3):

                        if implicit_conversion and (get_socket_type(ng,0)!="VECTOR"):
                            set_socket_type(ng,0, socket_type="NodeSocketVector")
                            self.socket_type = "NodeSocketVector"
                        set_socket_value(ng,0, value=value ,)
                        set_socket_label(ng,0, label=[round(n,4) for n in value] ,)
                    
                    #evaluate as color? 
                    elif (len(value)==4):

                        if implicit_conversion and (get_socket_type(ng,0)!="RGBA"):
                            set_socket_type(ng,0, socket_type="NodeSocketColor")
                            self.socket_type = "NodeSocketColor"
                        set_socket_value(ng,0, value=value ,)
                        set_socket_label(ng,0, label=[round(n,4) for n in value] ,)

                    #only vec3 and vec4 are supported
                    else:
                        self.evaluation_error = True
                        raise Exception(f"TypeError: 'List{len(value)}' not supported")

                case str():

                    if implicit_conversion and (get_socket_type(ng,0)!="STRING"):
                        set_socket_type(ng,0, socket_type="NodeSocketString")
                        self.socket_type = "NodeSocketString"
                    set_socket_value(ng,0, value=value ,)
                    set_socket_label(ng,0, label='"'+value+'"' ,)

                case bpy.types.Object():

                    if implicit_conversion and (get_socket_type(ng,0)!="OBJECT"):
                        set_socket_type(ng,0, socket_type="NodeSocketObject")
                        self.socket_type = "NodeSocketObject"
                    set_socket_value(ng,0, value=value,)
                    set_socket_label(ng,0, label=f'D.objects["{value.name}"]',)

                case bpy.types.Collection():

                    if implicit_conversion and (get_socket_type(ng,0)!="COLLECTION"):
                        set_socket_type(ng,0, socket_type="NodeSocketCollection")
                        self.socket_type = "NodeSocketCollection"
                    set_socket_value(ng,0, value=value,)
                    set_socket_label(ng,0, label=f'D.collections["{value.name}"]',)

                case bpy.types.Material():

                    if implicit_conversion and (get_socket_type(ng,0)!="MATERIAL"):
                        set_socket_type(ng,0, socket_type="NodeSocketMaterial")
                        self.socket_type = "NodeSocketMaterial"
                    set_socket_value(ng,0, value=value,)
                    set_socket_label(ng,0, label=f'D.materials["{value.name}"]',)

                case bpy.types.Image():

                    if implicit_conversion and (get_socket_type(ng,0)!="IMAGE"):
                        set_socket_type(ng,0, socket_type="NodeSocketImage")
                        self.socket_type = "NodeSocketImage"
                    set_socket_value(ng,0, value=value,)
                    set_socket_label(ng,0, label=f'D.images["{value.name}"]',)

                case _:
                    self.evaluation_error = True
                    raise Exception(f"TypeError: '{type(value).__name__.title()}' not supported")
            
            #no error, then return False to error prop
            set_socket_value(ng,1, value=False,)

            self.evaluation_error = False
            return get_socket_value(ng,0)

        except Exception as e:

            self.evaluation_error = True 
            print(f"{self.bl_idname} EVALUATION ERROR:\n{e}")

            set_socket_value(ng,1, value=True,)
            set_socket_label(ng,0, label=e,)

        return None
    
    def draw_label(self,):
        """node label"""
        
        return self.bl_label

    def draw_buttons(self, context, layout,):
        """node interface drawing"""
        
        from . __init__ import get_addon_prefs
        
        row = layout.row()
        row.alert = self.evaluation_error
        row.prop(self,"user_expression",text="",)

        if (get_addon_prefs().debug):
            box = layout.column()
            box.active = False
            box.template_ID(self, "node_tree")
            box.prop(self, "debug_update_counter", text="update count")

        return None

    @classmethod
    def update_all(cls):
        """search for all nodes of this type and update them"""
        
        for n in [n for ng in bpy.data.node_groups if ('extranodes_pythonapi_updateflag' in ng) for n in ng.nodes if (n.bl_idname==cls.bl_idname)]:
            n.update()
            
        return None


class EXTRANODES_NG_mathexpression(bpy.types.GeometryNodeCustomGroup):
    """Custom Nodgroup: Evaluate a python expression as a single value output
    the evaluated type can be a float, int, string, object. By default the values will be updated on depsgraph"""
    
    bl_idname = "GeometryNodeExtraMathExpression"
    bl_label = "Math Expression"

    def update_user_mathexp(self,context):
        """evaluate user expression and change the socket output type implicitly"""
        self.generate_expression()
        return None 
    
    user_mathexp : bpy.props.StringProperty(
        default="a + b + c",
        update=update_user_mathexp,
        description="type your math expression right here",
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
                in_sockets={
                    "a" : "NodeSocketFloat",
                    "b" : "NodeSocketFloat",
                    "c" : "NodeSocketFloat",                    
                },
                out_sockets={
                    "Result" : "NodeSocketFloat",
                },
            )
         
        ng = ng.copy() #always using a copy of the original ng

        self.node_tree = ng
        self.width = 250
        self.label = self.bl_label

        #mark an update signal so handler fct do not need to loop every single nodegroups
        bpy.context.space_data.node_tree["extranodes_pythonapi_updateflag"] = True

        return None 

    def copy(self,node,):
        """fct run when dupplicating the node"""
        
        self.node_tree = node.node_tree.copy()
        
        return None 
    
    def update(self):
        """generic update function"""
        
        self.generate_expression()
        
        return None
    
    def generate_expression(self):
        """
        Evaluate the user math expression in self.user_mathexp and rebuild the node tree
        for a Geometry Nodes math expression. This function:
        1. Clears all nodes except Group Input and Group Output.
        2. Extracts variable names from the expression.
        3. Creates input sockets on the Group Input node for each variable.
        4. Parses the expression (using Python’s ast) and recursively creates math and value nodes.
        5. Connects the final node’s output to the first input of the Group Output.
        """
        import re, ast
        
        ng = self.node_tree  # The node group.
        
        group_input = ng.nodes.get("Group Input")
        group_output = ng.nodes.get("Group Output")
        if not group_input or not group_output:
            print("ERROR: generate_expression(): Group Input or Output are gone")
            return None
        
        #Extract variable names from the expression.
        FUNCS = {"sin", "cos", "tan", "log", "exp", "sqrt"}
        variables = set()
        expr = self.user_mathexp
        if (expr):
            # Simple regex to extract words starting with a letter or underscore.
            variables = set(re.findall(r"(?<!\d)\b[a-zA-Z_]\w*\b", expr))
            # Filter out common math functions (adjust as needed).
            for func in FUNCS:
                variables.discard(func)
        
        print("Extracted variables:", variables)
        
        # Clear node tree (except Group Input and Group Output).
        for node in list(ng.nodes):
            if node.type not in {'GROUP_INPUT', 'GROUP_OUTPUT'}:
                ng.nodes.remove(node)
                
        # create or remove input socket dynamically
        for var in variables:
            if (var not in group_input.outputs):
                create_socket(ng, in_out='INPUT', socket_type="NodeSocketFloat", socket_name=var,)

        idx_to_del = []
        for idx,socket in enumerate(group_input.outputs):
            if ((socket.type!='CUSTOM') and (socket.name not in variables)):
                idx_to_del.append(idx)
        print(idx_to_del)
        for idx in reversed(idx_to_del):
            remove_socket(ng, idx+1, in_out='INPUT') #WHY+1???
                
        if (not variables):
            return None 
        
        return None
        
        # --- Step 4: Parse the expression and create nodes.
        try:
            expr_ast = ast.parse(expr, mode='eval')
        except Exception as e:
            print("Error parsing expression:", e)
            return None

        def build_math_nodes(node_ast):
            """
            Recursively build nodes from an AST node.
            Returns the created node.
            """
            # For a binary operation, create a math node.
            if isinstance(node_ast, ast.BinOp):
                left_node = build_math_nodes(node_ast.left)
                right_node = build_math_nodes(node_ast.right)
                
                # Create a new math node.
                math_node = ng.nodes.new("GeometryNodeMath")
                # Position it relative to children (for clarity).
                math_node.location = (left_node.location[0] + 200, left_node.location[1])
                
                # Map AST operator to math node operation.
                if isinstance(node_ast.op, ast.Add):
                    math_node.operation = 'ADD'
                elif isinstance(node_ast.op, ast.Sub):
                    math_node.operation = 'SUBTRACT'
                elif isinstance(node_ast.op, ast.Mult):
                    math_node.operation = 'MULTIPLY'
                elif isinstance(node_ast.op, ast.Div):
                    math_node.operation = 'DIVIDE'
                else:
                    raise ValueError("Unsupported operator: " + str(node_ast.op))
                
                # Link the left and right nodes to the math node's inputs.
                # (Assuming math_node.inputs[0] and inputs[1] are the two inputs.)
                ng.links.new(left_node.outputs[0], math_node.inputs[0])
                ng.links.new(right_node.outputs[0], math_node.inputs[1])
                
                return math_node
            
            # For a constant value, create a value node.
            elif isinstance(node_ast, ast.Constant):
                value_node = ng.nodes.new("GeometryNodeValue")
                value_node.outputs[0].default_value = node_ast.n
                return value_node
            
            # For a variable name, return the corresponding Group Input output.
            elif isinstance(node_ast, ast.Name):
                var_name = node_ast.id
                # Find the socket on the group input.
                sock = group_input.outputs.get(var_name)
                if not sock:
                    raise ValueError("Variable not found: " + var_name)
                # For linking purposes, we use the group input node's output.
                # In Blender, you can link directly from the Group Input.
                return group_input
            
            else:
                raise ValueError("Unsupported AST node type: " + str(type(node_ast)))
        
        try:
            result_node = build_math_nodes(expr_ast.body)
        except Exception as e:
            print("Error building math nodes:", e)
            return None

        # --- Step 5: Connect the result to the Group Output node.
        # Assume that the Group Output node's first input is intended for the final result.
        if group_output.inputs:
            ng.links.new(result_node.outputs[0], group_output.inputs[0])
            print("Successfully connected the result to Group Output.")
        else:
            print("Group Output has no input sockets to connect to.")
        
        return None

    def draw_label(self,):
        """node label"""
        
        return self.bl_label

    def draw_buttons(self, context, layout,):
        """node interface drawing"""
        
        from . __init__ import get_addon_prefs
        
        row = layout.row()
        row.prop(self,"user_mathexp",text="",)

        if (get_addon_prefs().debug):
            box = layout.column()
            box.active = False
            box.template_ID(self, "node_tree")

        return None

    @classmethod
    def update_all(cls):
        """search for all nodes of this type and update them"""
        
        # for n in [n for ng in bpy.data.node_groups if ('extranodes_pythonapi_updateflag' in ng) for n in ng.nodes if (n.bl_idname==cls.bl_idname)]:
        #     n.update()
            
        return None 


classes = (
    
    EXTRANODES_NG_camerainfo,
    EXTRANODES_NG_isrenderedview,
    EXTRANODES_NG_sequencervolume,
    EXTRANODES_NG_mathexpression,
    EXTRANODES_NG_pythonapi,
    
    )