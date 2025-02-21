# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN, Andrew Stevenson
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy 

import re, ast
from functools import partial

from ..__init__ import get_addon_prefs
from .boiler import create_new_nodegroup, create_socket, remove_socket, link_sockets


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


def replace_exact_tokens(expr, tokens_mapping):
    # Build a regex pattern that matches any of the tokens with the proper boundaries.
    pattern = build_token_pattern(tokens_mapping.keys())
    
    def repl(match):
        token = match.group(0)
        return tokens_mapping.get(token, token)
    
    return re.sub(pattern, repl, expr)


class NodeSetter():
    """Set the nodes depending on a given function expression"""
    
    @classmethod
    def all_functions(cls, get_names=False,):
        """get a list of all available functions"""

        r = set()
        
        for v in cls.__dict__.values():
            
            if (not isinstance(v, classmethod)):
                continue
            
            fname = v.__func__.__name__
            
            #ignore internal functions
            if fname.startswith('_'): 
                continue
            if fname in ('all_functions', 'execute_function_expression'):
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
        for f in cls.all_functions():
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
        
        return None            
    
    @classmethod
    def _generic_floatmath(cls, operation_type, sock1, sock2=None, sock3=None,):
        """generic operation for adding a float math node and linking"""
        
        ng = sock1.id_data
        node = ng.nodes.new('ShaderNodeMath')
        node.operation = operation_type
        
        print("--->",ng, operation_type, sock1, sock2, sock3)
        
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
            
    # First we format the expression a little
    if ('²' in mathexp):
        mathexp = mathexp.replace('²','**2')
    if ('³' in mathexp):
        mathexp = mathexp.replace('³','**3')

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
    functions_available = NodeSetter.all_functions(get_names=True)
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
    """Custom Nodgroup: Evaluate a python expression as a single value output
    the evaluated type can be a float, int, string, object. By default the values will be updated on depsgraph"""
    
    #TODO later support multi type operation with blender with int/vector/bool operator?  and other math operation, 
    #     - right now we only support the float math node.. we could support these other nodes
    #     - all vars could start with 'v' 'f' 'i' 'b'
    #     - could procedurally change sockets input/outputs depending on type
    #     - however, there will be a lot of checks required to see if the user is using valid types.. quite annoying. Perhaps could be done by checking 'is_valid'
    
    #TODO what if user use a function with wrong number of arguments?
    
    #TODO would be nice to have some sort of operator within the node interface that bake the node into a nodegroup.
    
    bl_idname = "GeometryNodeExtraMathExpression"
    bl_label = "Math Expression"

    error_message : bpy.props.StringProperty()
    debug_fctexp : bpy.props.StringProperty()
    
    def update_user_mathexp(self,context):
        """evaluate user expression and change the sockets implicitly"""
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
        
    def generate_expression(self):
        """transform the math expression into sockets and nodes arrangements"""
        
        #reset error message
        self.error_message = ""
        self.debug_fctexp = "No Init"
        
        ng = self.node_tree 
        in_nod, out_nod = ng.nodes["Group Input"], ng.nodes["Group Output"]
        variables, constants = set(), set() #List of variable or constant represented as str
        vareq, consteq = dict(), dict() #Equivalence from the str collected above to python API
        
        # Extract variable and constants from the expression.
        if (self.user_mathexp):
            variables = sorted(set(re.findall(r"\b[a-zA-Z]+\b(?!\s*\()", self.user_mathexp))) #any single letter not followed by '('
            constants = set(re.findall(r"\b\d+(?:\.\d+)?\b", self.user_mathexp)) #any floats or ints
        print("Extracted variables:", variables)
        print("Extracted constants:", constants)
        
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
        fctexp = mathexpression_to_fctexpression(self.user_mathexp)
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
        col.alert = bool(self.error_message)
        col.prop(self,"user_mathexp", text="",)
        
        if (self.error_message):
            col.label(text=self.error_message)

        if (get_addon_prefs().debug):
            box = layout.column()
            box.active = False
            box.template_ID(self, "node_tree")
            box.prop(self, "debug_fctexp", text="",)

        return None

    @classmethod
    def update_all(cls):
        """search for all nodes of this type and update them"""
        
        for n in [n for ng in bpy.data.node_groups for n in ng.nodes if (n.bl_idname==cls.bl_idname)]:
            n.update()
            
        return None 