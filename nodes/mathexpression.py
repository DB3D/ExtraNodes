# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN, Andrew Stevenson
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy 

import re, ast

from ..__init__ import get_addon_prefs
from .boiler import create_new_nodegroup, create_socket, remove_socket


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
    def all_functions_names(cls):
        """get a list of all available functions"""
        r = set()
        for v in cls.__dict__.values():
            if isinstance(v, staticmethod):
                fname = v.__func__.__name__
                if fname.startswith('_'): #ignore internal functions
                    continue
                r.add(fname)
        return r
    
    @classmethod
    def execute_functions(cls, _self, expression=None, node_tree=None, varsockets=None, constsockets=None,):
        """try to execute the functions to arrange the node_tree"""
        
        # Replace the constants or variable with sockets API
        
        # Replace function names to fit namespace
        for fname in cls.all_functions_names():
            if fname in expression:
                expression = expression.replace(fname,f'cls.{fname}')        
        
        # Try to execute the functions:
        try:
            exec(expression)
        except Exception as e:
            _self.error_message = "Error on Execution"
            print(e)
            
        return None            
    
    @staticmethod
    def add(sock1, sock2):
        return None

    @staticmethod
    def subtract(sock1, sock2):
        return None

    @staticmethod
    def mult(sock1, sock2):
        return None

    @staticmethod
    def div(sock1, sock2):
        return None

    @staticmethod
    def exp(sock1, sock2):
        return None

    @staticmethod
    def log(sock1, sock2):
        return None

    @staticmethod
    def sqrt(sock1, sock2):
        return None
    
    @staticmethod
    def invsqrt(sock1, sock2):
        return None
    
    @staticmethod
    def abs(sock1):
        return None
    
    @staticmethod
    def min(sock1, sock2):
        return None
    
    @staticmethod
    def max(sock1, sock2):
        return None
    
    @staticmethod
    def round(sock1):
        return None

    @staticmethod
    def floor(sock1):
        return None

    @staticmethod
    def ceil(sock1):
        return None

    @staticmethod
    def trunc(sock1):
        return None

    @staticmethod
    def sin(sock1):
        return None

    @staticmethod
    def cos(sock1):
        return None
    
    @staticmethod
    def tan(sock1):
        return None


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
    functions_available = NodeSetter.all_functions_names()
    for fname in transformer.functions_used:
        if (fname not in functions_available):
            return Exception(f"'{fname}' Function Not Recognized")
    
    return fctexp


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
        variables, constants = set(), set()
        vareq, consteq = dict(), dict()
        
        # Extract variable and constants from the expression.
        if (self.user_mathexp):
            variables = sorted(set(re.findall(r"\b[a-zA-Z]+\b(?!\s*\()", self.user_mathexp))) #any single letter not followed by '('
            constants = set(re.findall(r"\b\d+(?:\.\d+)?\b", self.user_mathexp)) #any floats or ints
        print("Extracted variables:", variables)
        print("Extracted variables:", constants)
        
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
                vareq[s.name] = s.identifier
                
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
                consteq[const] = con_nod.outputs[0].identifier
        
        # Give it a refresh signal, when we remove/create a lot of sockets, the customnode inputs/outputs needs a kick
        self.update_all()
        
        if (not variables):
            return None
        
        # Transform user expression into pure function expression
        fctexp = mathexpression_to_fctexpression(self.user_mathexp)
        if type(fctexp) is Exception:
            self.error_message = str(fctexp)
            self.debug_fctexp = 'Failed'
            return None
        
        self.debug_fctexp = fctexp
        
        # Execute the function expression to arrange the user nodetree
        NodeSetter.execute_functions(self,
            expression=fctexp,
            node_tree=ng,
            varsockets=vareq,
            constsockets=consteq,
        )

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