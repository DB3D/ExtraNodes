# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN, Andrew Stevenson
#
# SPDX-License-Identifier: GPL-2.0-or-later


#How does it works?
# 1- Find the variables or constants with regex
# 2- dynamically remove/create sockets accordingly
# 3- transform the algebric expression into 'function expressions' using 'mathexpression_to_fctexpression'
# 4- execute the function expression with 'NodeSetter' using exec(), which will set the nodes in place.


import bpy 

import re, ast
from functools import partial

from ..__init__ import get_addon_prefs
from .boiler import create_new_nodegroup, create_socket, remove_socket, link_sockets, replace_node


def replace_exact_tokens(string, tokens_mapping):
    """replace any token of a given strings with the new values from a given dict mapping"""
    
    def build_token_pattern(tokens):
        def boundary(token):
            # If token is a number (integer or float)
            if re.fullmatch(r'\d+(?:\.\d+)?', token):
                # Use negative lookbehind and lookahead to ensure the token isn't part of a larger number.
                return r'(?<![\d.])' + re.escape(token) + r'(?![\d.])'
            else:
                # For alphabetic tokens, use word boundaries.
                return r'\b' + re.escape(token) + r'\b'
        # Build the overall pattern by joining each token pattern with '|'
        return '|'.join(boundary(token) for token in tokens)

    pattern = build_token_pattern(tokens_mapping.keys())
    
    def repl(match):
        token = match.group(0)
        return tokens_mapping.get(token, token)
    
    return re.sub(pattern, repl, string)


class NodeSetter():
    """Set the nodes depending on a given function expression"""
    
    @classmethod
    def get_functions(cls, get_names=False,):
        """get a list of all available functions"""

        r = set()
        
        for v in cls.__dict__.values():
            
            if (not isinstance(v, classmethod)):
                continue
            
            fname = v.__func__.__name__
            
            #ignore internal functions
            if fname.startswith('_'): 
                continue
            if fname in ('get_functions', 'execute_function_expression'):
                continue
            
            if (get_names):
                    r.add(fname)
            else: r.add(v.__func__)
                        
        return r
    
    @classmethod
    def execute_function_expression(cls, expression, node_tree=None, varsapi=None, constapi=None,) -> None | Exception:
        """try to execute the functions to arrange the node_tree"""
        
        # Replace the constants or variable with sockets API
        api_expression = replace_exact_tokens(expression, {**varsapi, **constapi},)
        
        # Define the namespace of the execution, and include our functions
        namespace = {}
        namespace["ng"] = node_tree
        for f in cls.get_functions():
            namespace[f.__name__] = partial(f, cls)
        
        # Try to execute the functions:
        try:
            exec(api_expression, namespace)
            
        except TypeError as e:
            print(f"TypeError:\n  {e}\nOriginalExpression:\n  {expression}\nApiExpression:\n  {api_expression}\n")
            return Exception("Wrong Arguments Given")
        
        except Exception as e:
            print(f"ExecutionError:\n  {e}\nOriginalExpression:\n  {expression}\nApiExpression:\n  {api_expression}\n")
            return Exception("Error on Execution")
        
        # When executing, the last one created should be the active node, 
        # We still need to connect it to the ng output
        try:
            sock1 = node_tree.nodes.active.outputs[0]
            sock2 = node_tree.nodes['Group Output'].inputs[0]
            link_sockets(sock1, sock2)
            
        except Exception as e:
            print(f"FinalLinkError:\n  {e}")
            return Exception("Error on Final Link")
        
        return None            
    
    @classmethod
    def _generic_floatmath(cls, operation_type, sock1, sock2=None, sock3=None,):
        """generic operation for adding a float math node and linking"""
        
        ng = sock1.id_data
        node = ng.nodes.new('ShaderNodeMath')
        node.operation = operation_type
        ng.nodes.active = node
                
        if (sock1):
            link_sockets(sock1, node.inputs[0])
        if (sock2):
            link_sockets(sock2, node.inputs[1])
        if (sock3):
            link_sockets(sock3, node.inputs[2])
            
        return node.outputs[0]
    
    @classmethod
    def add(cls, sock1, sock2):
        return cls._generic_floatmath('ADD', sock1, sock2)

    @classmethod
    def subtract(cls, sock1, sock2):
        return cls._generic_floatmath('SUBTRACT', sock1, sock2)

    @classmethod
    def mult(cls, sock1, sock2):
        return cls._generic_floatmath('MULTIPLY', sock1, sock2)

    @classmethod
    def div(cls, sock1, sock2):
        return cls._generic_floatmath('DIVIDE', sock1, sock2)

    @classmethod
    def exp(cls, sock1, sock2):
        return cls._generic_floatmath('POWER', sock1, sock2)

    @classmethod
    def power(cls, sock1, sock2): #Synonym of 'exp'
        return cls.exp(sock1, sock2)
    
    @classmethod
    def log(cls, sock1, sock2):
        return cls._generic_floatmath('LOGARITHM', sock1, sock2)

    @classmethod
    def sqrt(cls, sock1):
        return cls._generic_floatmath('SQRT', sock1)
    
    @classmethod
    def invsqrt(cls, sock1):
        return cls._generic_floatmath('INVERSE_SQRT', sock1)

    @classmethod
    def abs(cls, sock1):
        return cls._generic_floatmath('ABSOLUTE', sock1)
    
    @classmethod
    def min(cls, sock1, sock2):
        return cls._generic_floatmath('MINIMUM', sock1, sock2)
    
    @classmethod
    def max(cls, sock1, sock2):
        return cls._generic_floatmath('MAXIMUM', sock1, sock2)
    
    @classmethod
    def round(cls, sock1):
        return cls._generic_floatmath('ROUND', sock1)

    @classmethod
    def floor(cls, sock1):
        return cls._generic_floatmath('FLOOR', sock1)

    @classmethod
    def ceil(cls, sock1):
        return cls._generic_floatmath('CEIL', sock1)

    @classmethod
    def trunc(cls, sock1):
        return cls._generic_floatmath('TRUNC', sock1)

    @classmethod
    def sin(cls, sock1):
        return cls._generic_floatmath('SINE', sock1)

    @classmethod
    def cos(cls, sock1):
        return cls._generic_floatmath('COSINE', sock1)
    
    @classmethod
    def tan(cls, sock1):
        return cls._generic_floatmath('TANGENT', sock1)


class FunctionTransformer(ast.NodeTransformer):
    """ast Transformer class for 'mathexpression_to_fctexpression'"""
    
    def __init__(self):
        super().__init__()
        self.functions_used = set()
        
    def visit_BinOp(self, node):
        
        # Process the children nodes first
        self.generic_visit(node)
        
        # Map operators to your function names
        if isinstance(node.op, ast.Add):
            func_name = 'add'
        elif isinstance(node.op, ast.Sub):
            func_name = 'subtract'
        elif isinstance(node.op, ast.Mult):
            func_name = 'mult'
        elif isinstance(node.op, ast.Div):
            func_name = 'div'
        elif isinstance(node.op, ast.Pow):
            func_name = 'exp'
        else:
            raise NotImplementedError(f"Operator {node.op} not supported")

        self.functions_used.add(func_name)
        
        return ast.Call(
            func=ast.Name(id=func_name, ctx=ast.Load()),
            args=[node.left, node.right],
            keywords=[]
        )

    def visit_Call(self, node):
        # If the function is a Name, record it.
        if isinstance(node.func, ast.Name):
            self.functions_used.add(node.func.id)
        # Process any arguments (in case they include binary operations, etc.)
        self.generic_visit(node)
        return node
    
    def visit_Name(self, node):
        return node

    def visit_Num(self, node):
        return node

    def visit_Constant(self, node):
        return node


def mathexpression_to_fctexpression(mathexp:str) -> str | Exception:
    """transform a math algebric expression into a funciton expression
    ex: 'x*2 + (3 - 4/5)/3 + (x+y)**2' will become 'add(mult(x,2),div(subtract(3,div(4,5)),3),exp(add(x,y),2))'"""

    # Parse the expression.
    try:
        tree = ast.parse(mathexp, mode='eval')
    except Exception as e:
        print(e)
        return Exception("Math Expression Not Recognized")

    # Transform the AST.
    transformer = FunctionTransformer()
    try:
        astvisited = transformer.visit(tree.body)
    except Exception as e:
        print(e)
        return Exception("Math Expression Not Recognized")
    
    # Convert the transformed AST back to source code.
    fctexp = str(ast.unparse(astvisited))
    
    # Return both the transformed expression and the sorted list of functions used.
    functions_available = NodeSetter.get_functions(get_names=True)
    for fname in transformer.functions_used:
        if (fname not in functions_available):
            return Exception(f"'{fname}' Function Not Recognized")
    
    return fctexp


def get_socket_python_api(node, identifier) -> str:
    
    idx = None
    in_out_api = "inputs"
    for sockets in (node.inputs, node.outputs):
        for i,s in enumerate(sockets):
            if (hasattr(s,'identifier') and (s.identifier==identifier)):
                idx = i
                if (s.is_output):
                    in_out_api = "outputs"
                break
    
    assert idx is not None, 'ERROR: get_socket_python_api(): Did not find socket idx..'
    
    return f"ng.nodes['{node.name}'].{in_out_api}[{idx}]"


class EXTRANODES_NG_mathexpression(bpy.types.GeometryNodeCustomGroup):
    """Custom Nodgroup: Evaluate a math expression using the float math node.
    Under the hood, the expression will be sanarized, the transformed into functions that will be executed to create a new nodetree.
    The nodetree will be recomposed on each expression keystrokes"""
    
    #TODO later support multi type operation with blender with int/vector/bool operator?  and other math operation, 
    #     - right now we only support the float math node.. we could support these other nodes
    #     - all vars could start with 'v' 'f' 'i' 'b' to designate their types?
    #     - could procedurally change sockets input/outputs depending on type
    #     - however, there will be a lot of checks required to see if the user is using valid types.. quite annoying. Perhaps could be done by checking 'is_valid'
    #     Or maybe create a separate 'ComplexMath' node and keep this simple one?
    
    #TODO what if user use a function with wrong number of arguments?
    #TODO support more math symbols? https://en.wikipedia.org/wiki/Glossary_of_mathematical_symbols
        
    bl_idname = "GeometryNodeExtraMathExpression"
    bl_label = "Math Expression"

    error_message : bpy.props.StringProperty()
    debug_sanatized : bpy.props.StringProperty()
    debug_fctexp : bpy.props.StringProperty()
    
    def update_user_mathexp(self,context):
        """evaluate user expression and change the sockets implicitly"""
        self.apply_expression()
        return None 
    
    user_mathexp : bpy.props.StringProperty(
        default="a + b + c",
        name="Expression",
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
                out_sockets={
                    "Result" : "NodeSocketFloat",
                },
            )
         
        ng = ng.copy() #always using a copy of the original ng

        self.node_tree = ng
        self.width = 250
        self.label = self.bl_label

        #initialize default expression
        self.user_mathexp = self.user_mathexp

        return None 

    def copy(self,node,):
        """fct run when dupplicating the node"""
        
        self.node_tree = node.node_tree.copy()
        
        return None 
    
    def update(self):
        """generic update function"""
                
        return None
    
    def sanatize_expression(self, expression) -> str | Exception:
        """ensure the user expression is correct, sanatized it"""
        
        # First we format some symbols
        expression = expression.replace(' ','')
        expression = expression.replace('^','**')
        expression = expression.replace('²','**2')
        expression = expression.replace('³','**3')
        
        # Make a list of authorized symbols
        authorized_symbols = '/*-+.,()'
        authorized_symbols += ''.join(chr(c) for c in range(ord('a'), ord('z') + 1)) #alphabet
        authorized_symbols += ''.join(chr(c).upper() for c in range(ord('a'), ord('z') + 1)) #alphabet upper
        authorized_symbols += ''.join(chr(c) for c in range(ord('0'), ord('9') + 1)) #numbers
        
        # Ensure user is using correct symbols
        for char in expression:
            if (char not in authorized_symbols):
                return Exception(f"Unrecorgnized Symbol '{char}'")
        
        # Ensure user is using correct functions
        functions_available = NodeSetter.get_functions(get_names=True)
        user_functions = set(re.findall(r"\b[a-zA-Z]+(?=\()", expression))
        for fname in user_functions:
            if (fname not in functions_available):
                return Exception(f"Unrecorgnized Function '{fname}'")
        
        # Support for implicit math operation on variables (ex 2a, 0.5a)
        expression = re.sub(r"(\d+(?:\.\d+)?)([A-Za-z])", r"\1*\2", expression)
        
        # Disregard user variable that are mixing numbers and alphabets (ex 2a a1)
        invalid_args = re.findall(r"\b(?=[A-Za-z0-9]*[A-Za-z])(?=[A-Za-z0-9]*\d)[A-Za-z0-9]+\b", expression)
        if (invalid_args):
            for inva in invalid_args:
                return Exception(f"Invalid Variable '{inva}'")
        
        # Support for implicit math operation on parentheses (ex 2(a+b) or 2.59(c²))
        expression = re.sub(r"(\d+(?:\.\d+)?)(\()", r"\1*\2", expression)
        
        return expression
    
    def apply_expression(self) -> None:
        """transform the math expression into sockets and nodes arrangements"""
        
        # Reset error message
        self.error_message = self.debug_sanatized = self.debug_fctexp = ""
        
        # First we make sure the user expression is correct
        rval = self.sanatize_expression(self.user_mathexp)
        if (type(rval) is Exception):
            self.error_message = str(rval)
            self.debug_sanatized = 'Failed'
            return None
        
        sanatized_expr = self.debug_sanatized = rval
    
        ng = self.node_tree 
        in_nod, out_nod = ng.nodes["Group Input"], ng.nodes["Group Output"]
        variables, constants = set(), set() #List of variable or constant represented as str
        vareq, consteq = dict(), dict() #Equivalence from the str collected above to python API
        
        # Extract variable and constants from the expression.
        if (sanatized_expr):
            variables = sorted(set(re.findall(r"\b[a-zA-Z]+\b(?!\s*\()", sanatized_expr))) #any series of letter not followed by '('
            constants = set(re.findall(r"\b\d+(?:\.\d+)?\b", sanatized_expr)) #any floats or ints
        
        # Make sure the user variables aren't function names.
        functions_available = NodeSetter.get_functions(get_names=True)
        for var in variables:
            if (var in functions_available):
                self.error_message = f"Variable '{var}' is Taken"
                self.debug_fctexp = 'Failed'
                return None
        
        # Clear node tree
        for node in list(ng.nodes):
            if node.type not in {'GROUP_INPUT', 'GROUP_OUTPUT'}:
                ng.nodes.remove(node)
                
        # Create new sockets depending on vars
        if (variables):
            current_vars = [s.name for s in in_nod.outputs]
            for var in variables:
                if (var not in current_vars):
                    create_socket(ng, in_out='INPUT', socket_type="NodeSocketFloat", socket_name=var,)
        
        # Remove unused vars sockets
        idx_to_del = []
        for idx,socket in enumerate(in_nod.outputs):
            if ((socket.type!='CUSTOM') and (socket.name not in variables)):
                idx_to_del.append(idx)
        for idx in reversed(idx_to_del):
            remove_socket(ng, idx, in_out='INPUT')
        
        # Fill equivalence dict with it's socket eq
        if (variables):
            for s in in_nod.outputs:
                if (s.name in variables):
                    vareq[s.name] = get_socket_python_api(in_nod, s.identifier)
                
        # Add input for constant right below the vars group input
        if (constants):
            xloc, yloc = in_nod.location.x, in_nod.location.y
            xloc -= 175
            for const in constants:
                con_nod = ng.nodes.new('ShaderNodeValue')
                con_nod.outputs[0].default_value = float(const)
                con_nod.name = const
                con_nod.label = const
                con_nod.location.x = xloc
                con_nod.location.y = yloc
                yloc -= 90
                # Also fill const to socket equivalence dict
                consteq[const] = get_socket_python_api(con_nod, con_nod.outputs[0].identifier)
        
        # Give it a refresh signal, when we remove/create a lot of sockets, the customnode inputs/outputs needs a kick
        self.update_all()
        
        if (not variables):
            return None
        
        # Transform user expression into pure function expression
        fctexp = mathexpression_to_fctexpression(sanatized_expr)
        if (type(fctexp) is Exception):
            self.error_message = str(fctexp)
            self.debug_fctexp = 'Failed'
            return None
        
        self.debug_fctexp = fctexp
        
        # Execute the function expression to arrange the user nodetree
        rval = NodeSetter.execute_function_expression(fctexp,
            node_tree=ng, varsapi=vareq, constapi=consteq,
            )
        if (type(rval) is Exception):
            self.error_message = str(rval)
            return None
        
        return None

    def draw_label(self,):
        """node label"""
        
        return self.bl_label

    def draw_buttons(self, context, layout,):
        """node interface drawing"""
                
        col = layout.column(align=True)
        
        row = col.row(align=True)
        row.alert = bool(self.error_message)
        row.prop(self,"user_mathexp", text="",)
        op = row.operator("extranode.bake_mathexpression", text="", icon="CURRENT_FILE",)
        op.nodegroup_name = self.node_tree.name
        op.node_name = self.name
        
        if (self.error_message):
            col.label(text=self.error_message)

        if (get_addon_prefs().debug):
            box = layout.box()
            box.label(text='Debug')
            box.separator(type='LINE', factor=0.5,)
            box.template_ID(self, "node_tree")
            
            col = box.column(align=True)
            col.scale_y = 0.9
            col.label(text="SanatizedExp:")
            col.prop(self, "debug_sanatized", text="",)

            col = box.column(align=True)
            col.scale_y = 0.9
            col.label(text="FunctionExp:")
            col.prop(self, "debug_fctexp", text="",)

        return None

    @classmethod
    def update_all(cls):
        """search for all nodes of this type and update them"""
        
        for n in [n for ng in bpy.data.node_groups for n in ng.nodes if (n.bl_idname==cls.bl_idname)]:
            n.update()
            
        return None


class EXTRANODES_OT_bake_mathexpression(bpy.types.Operator):
    """Replace a node with a Node Group node, preserving defaults and links"""
    
    bl_idname = "extranode.bake_mathexpression"
    bl_label = "Replace Node with Node Group"
    bl_options = {'REGISTER', 'UNDO'}

    nodegroup_name: bpy.props.StringProperty()
    node_name: bpy.props.StringProperty()

    def execute(self, context):
        
        space = context.space_data
        if not space or not hasattr(space, "edit_tree") or space.edit_tree is None:
            self.report({'ERROR'}, "No active node tree found")
            return {'CANCELLED'}
        node_tree = space.edit_tree

        old_node = node_tree.nodes.get(self.node_name)
        if (old_node is None):
            self.report({'ERROR'}, "Node with given name not found")
            return {'CANCELLED'}

        node_group = bpy.data.node_groups.get(self.nodegroup_name)
        if (node_group is None):
            self.report({'ERROR'}, "Node group with given name not found")
            return {'CANCELLED'}

        node_group = node_group.copy()
        node_group.name = f'{node_group.name}.Baked'
        
        replace_node(node_tree, old_node, node_group,)
        self.report({'INFO'}, f"Replaced node '{self.node_name}' with node group '{self.node_name}'")
        
        return {'FINISHED'}

