# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
#
# SPDX-License-Identifier: GPL-2.0-or-later


# NOTE How does it works?
# 1- Find the variables or constants with regex
# 2- dynamically remove/create sockets accordingly
# 3- transform the algebric expression into 'function expressions' using 'transform_math_expression'
# 4- execute the function expression with using exec() with the namespace from nex.nodesetter, which will set the nodes in place.

# TODO color of the node header should be blue for converter.. how to do that without hacking in the memory??

#TODO add dynamic output type?
#  - int(a) & all round, floor, ceil, trunc should return int then
#  - bool(a)
#  - sign(a) (to int)
#  - isneg(a) (== boolcompar, will return bool)
#  - ispair(a)
#  - isimpair(a)
#  - ismultiple(a,b)
#  - comparison <>== to bool
# NOTE if we do so, then how can we support other nodetree later on?????
# NOTE perhaps it is best to limit this to float for now. Rename it Float Math Expression?


import bpy

import re, ast

from ..utils.str_utils import match_exact_tokens, replace_exact_tokens, is_float_compatible
from ..utils.node_utils import create_new_nodegroup, create_socket, remove_socket, link_sockets
from ..nex.nodesetter import get_user_functions


DIGITS = '0123456789'
ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

IRRATIONALS = {'π':'3.1415927','𝑒':'2.7182818','φ':'1.6180339',}
MACROS = {'Pi':'π','eNum':'𝑒','Gold':'φ',}
SUPERSCRIPTS = {'⁰':'0', '¹':'1', '²':'2', '³':'3', '⁴':'4', '⁵':'5', '⁶':'6', '⁷':'7', '⁸':'8', '⁹':'9',}

DOCSYMBOLS = {
    '+':{'name':"Addition",'desc':""},
    '-':{'name':"Subtraction.",'desc':"Can be used to negate as well ex: -x"},
    '*':{'name':"Multiplication.",'desc':""},
    '**':{'name':"Power.",'desc':""},
    '²':{'name':"Power Notation.",'desc':"Please note that 2ab² will either be transformed into (ab)**2 or a*((b)**2) depending if you use 'Algebric Notations'."}, #Supported during sanatization
    '/':{'name':"Division.",'desc':""},
    '//':{'name':"FloorDiv.",'desc':""},
    '%':{'name':"Modulo.",'desc':""},
    'π':{'name':"Pi",'desc':"Represented as 3.1415927 float value.\nInvoked using the 'Pi' Macro."}, #Supported during sanatization
    '𝑒':{'name':"EulerNumber.",'desc':"Represented as 2.7182818 float value.\nInvoked using the 'eNum' Macro."}, #Supported during sanatization
    'φ':{'name':"GoldenRation.",'desc':"Represented as 1.6180339 float value.\nInvoked using the 'Gold' Macro."}, #Supported during sanatization
}

#Store the math function used to set the nodetree
USER_FUNCTIONS = get_user_functions(return_types='float')
USER_FNAMES = [f.__name__ for f in USER_FUNCTIONS]


def replace_superscript_exponents(expr: str, algebric_notation:bool=False,) -> str:
    """convert exponent to ** notation
    Example: "2ab²" becomes "2(ab**2) or "2ab²" becomes "2a(b**2)" if alrebric_notation
    """
    
    # Pattern for alphanumeric base followed by superscripts.
    if (algebric_notation):
          pattern_base = r'([A-Za-z0-9π𝑒φ])([⁰¹²³⁴⁵⁶⁷⁸⁹]+)'
    else: pattern_base = r'([A-Za-z0-9π𝑒φ]+)([⁰¹²³⁴⁵⁶⁷⁸⁹]+)'
        
    def repl_base(match):
        base = match.group(1)
        superscripts = match.group(2)
        # Convert each superscript character to its digit equivalent.
        exponent = "".join(SUPERSCRIPTS.get(ch, '') for ch in superscripts)
        # Wrap the base in parentheses and apply the power operator.
        return f"({base}**{exponent})"
    
    # Pattern for a closing parenthesis immediately followed by superscripts.
    pattern_paren = r'(\))([⁰¹²³⁴⁵⁶⁷⁸⁹]+)'
    
    def repl_parenthesis(match):
        closing = match.group(1)
        superscripts = match.group(2)
        exponent = "".join(SUPERSCRIPTS.get(ch, '') for ch in superscripts)
        # Just insert ** before the exponent after the parenthesis.
        return f"){f'**{exponent}'}"
    
    expr = re.sub(pattern_base, repl_base, expr)
    expr = re.sub(pattern_paren, repl_parenthesis, expr)
    return expr


def get_socket_python_api(node, identifier) -> str:
    """return a python api string that can be executed from a given node and socket identifier"""
    
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


def execute_math_function_expression(customnode=None, expression:str=None, 
    node_tree=None, varsapi:dict=None, constapi:dict=None,) -> None:
    """Execute the functions to arrange the node_tree"""

    # Replace the constants or variable with sockets API
    # ex 'a' will become 'ng.nodes["foo"].outputs[1]'
    api_expression = replace_exact_tokens(expression, {**varsapi, **constapi},)

    # Define the namespace of the execution, and include our functions
    local_vars = {}
    local_vars["ng"] = node_tree
    local_vars.update({f.__name__:f for f in USER_FUNCTIONS})
    
    # we get rid of any blender builtin functions
    global_vars = {"__builtins__": {}}

    try:
        # The user technically has ONLY  access to the 'ng' NodeGroupType variable and to math functions
        # This exec() is therefore security compliant. It will also never execute without an user update signal from string field inputs.
        exec(api_expression, global_vars, local_vars)

    except TypeError as e:
        print(f"TypeError: execute_math_function_expression():\n  {e}\nOriginalExpression:\n  {expression}\nApiExpression:\n  {api_expression}\n")

        #Cook better error message to end user
        e = str(e)
        if ('()' in e):
            fname = e.split('()')[0]
            if ('() missing' in e) and ('required positional argument' in e):
                nbr = e.split('() missing ')[1][0]
                raise Exception(f"Function '{fname}' needs {nbr} more Params")                    
            elif ('() takes' in e) and ('positional argument' in e):
                raise Exception(f"Function '{fname}' recieved Extra Params")
        
        raise Exception("Wrong Arguments Given")
    
    except Exception as e:
        print(f"{type(e).__name__}: execute_math_function_expression():\n  {e}\nOriginalExpression:\n  {expression}\nApiExpression:\n  {api_expression}\n")

        #Cook better error message to end user
        if ("'tuple' object" in str(e)):
            raise Exception("Wrong use of '( , )' Synthax")
        #User really need to have a VERY LONG expression to reach to that point..
        if ('too many nested parentheses' in str(e)):
            raise Exception("Expression too Large")
        
        raise Exception("Error on Execution")
    
    # When executing, the last one created should be the active node, 
    # We still need to connect it to the ng output
    try:
        last = node_tree.nodes.active
        
        #this can only mean one thing, the user only inputed one single variable or constant
        if (last is None):
            if (customnode.elemVar):
                last = node_tree.nodes['Group Input']
            elif (customnode.elemConst):
                for n in node_tree.nodes:
                    if (n.type=='VALUE'):
                        last = n
                        break
            
        out_node = node_tree.nodes['Group Output']
        out_node.location = (last.location.x+last.width+70, last.location.y-120,)
        
        sock1, sock2 = last.outputs[0], out_node.inputs[0]
        link_sockets(sock1, sock2)
        
    except Exception as e:
        print(f"{type(e).__name__} FinalLinkError: execute_math_function_expression():\n  {e}")
        raise Exception("Error on Final Link")
    
    return None     


class FunctionTransformer(ast.NodeTransformer):
    """AST Transformer for converting math expressions into function-call expressions."""

    def __init__(self):
        super().__init__()
        self.functions_used = set()
    
    def visit_BinOp(self, node):
        # First, process child nodes.
        self.generic_visit(node)
        
        # Map ast operators and transform to supported function names
        match node.op:
            case ast.Add():
                func_name = 'add'
            case ast.Sub():
                func_name = 'subtract'
            case ast.Mult():
                func_name = 'mult'
            case ast.Div():
                func_name = 'div'
            case ast.Pow():
                func_name = 'pow'
            case ast.Mod():
                func_name = 'mod'
            case ast.FloorDiv():
                func_name = 'floordiv'
            case _:
                print(f"FunctionTransformer `{node.op}` NotImplementedError")
                raise Exception(f"Operator {node.op} not supported")
        
        self.functions_used.add(func_name)
        
        # Replace binary op with a function call.
        return ast.Call(
            func=ast.Name(id=func_name, ctx=ast.Load()),
            args=[node.left, node.right],
            keywords=[],
        )

    def visit_UnaryOp(self, node):
        # Process child nodes first.
        self.generic_visit(node)
        # Detect unary minus.
        if isinstance(node.op, ast.USub):
            self.functions_used.add('neg')
            # Replace -X with neg(X)
            return ast.Call(
                func=ast.Name(id='neg', ctx=ast.Load()),
                args=[node.operand],
                keywords=[]
            )
        # Otherwise, just return the node unchanged.
        return node

    def visit_Call(self, node):
        # Record called function names.
        if isinstance(node.func, ast.Name):
            self.functions_used.add(node.func.id)
        self.generic_visit(node)
        return node

    def visit_Name(self, node):
        return node

    def visit_Num(self, node):
        return node

    def visit_Constant(self, node):
        return node

    def transform_math_expression(self, math_express: str) -> str:
        """Transforms a math expression into a function-call expression.
        Example: 'x*2 + (3-4/5)/3 + (x+y)**2' becomes 'add(mult(x,2),div(subtract(3,div(4,5)),3),exp(add(x,y),2))'"""
        
        # Use the ast module to visit our equation
        try:
            tree = ast.parse(math_express, mode='eval')
            transformed_node = self.visit(tree.body)
        except Exception as e:
            print(f"FunctionTransformer ParsingError {type(e).__name__}:\n  Expression: `{math_express}`\n{e}")
            raise Exception("Math Expression Not Recognized")
        
        # Ensure all functions used are available valid
        for fname in self.functions_used:
            if fname not in USER_FNAMES:
                print(f"FunctionTransformer NamespaceError:\n  Element '{fname}' not in available functions.\n  Expression: `{math_express}`")
                raise Exception(f"Unknown Function '{fname}'")
        
        # Then transform the ast into a function call sequence
        func_express = str(ast.unparse(transformed_node))
        return func_express


class NODEBOOSTER_NG_mathexpression(bpy.types.GeometryNodeCustomGroup):
    """Custom Nodgroup: Evaluate a float math equation.
    • The sockets are limited to Float types. Consider this node a 'Float Math Expression' node.
    • Please See the 'NodeBooster > Active Node > Glossary' panel to see all functions and notation available and their descriptions.
    • If you wish to bake this node into a nodegroup, a bake operator is available in the 'NodeBooster > Active Node' panel.
    • Under the hood, on each string field edit, the expression will be sanarized, then transformed into functions that will be executed to create a nodetree, see the breakdown of the process in the 'NodeBooster > Active Node > Development' panel."""

    bl_idname = "GeometryNodeNodeBoosterMathExpression"
    bl_label = "Math Expression"

    error_message : bpy.props.StringProperty()
    debug_sanatized : bpy.props.StringProperty()
    debug_fctexp : bpy.props.StringProperty()

    def update_signal(self,context):
        """evaluate user expression and change the sockets implicitly"""
        self.apply_math_expression()
        return None 
    
    user_mathexp : bpy.props.StringProperty(
        default="",
        name="Expression",
        update=update_signal,
        description="type your math expression right here",
    )
    use_algrebric_multiplication : bpy.props.BoolProperty(
        default=False,
        name="Algebric Notation",
        update=update_signal,
        description="Algebric Notation.\nAutomatically consider notation such as '2ab' as '2*a*b'",
    )
    use_macros : bpy.props.BoolProperty(
        default=False,
        name="Recognize Macros",
        update=update_signal,
        description="Recognize Macros.\nAutomatically recognize the strings 'Pi' 'eNum' 'Gold' and replace them with their unicode symbols.",
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

        return None 

    def copy(self,node,):
        """fct run when dupplicating the node"""
        
        self.node_tree = node.node_tree.copy()
        
        return None 
    
    def update(self):
        """generic update function"""
                
        return None
    
    def sanatize_math_expression(self, expression) -> str:
        """ensure the user expression is correct, sanatized it, and collect its element"""

        authorized_symbols = ALPHABET + DIGITS + '/*-+%.,()'
        
        # Remove white spaces char
        expression = expression.replace(' ','')
        expression = expression.replace('	','')
                
        # Sanatize ² Notations
        for char in expression:
            if char in SUPERSCRIPTS.keys():
                expression = replace_superscript_exponents(expression,
                    algebric_notation=self.use_algrebric_multiplication,
                    )
                break 
        
        # Support for Irrational unicode char
        mached = match_exact_tokens(expression, IRRATIONALS.keys())
        if any(mached):
            expression = replace_exact_tokens(expression, IRRATIONALS)
        
        # Gather lists of expression component outside of operand and some synthax elements
        elemTotal = expression
        for char in '/*-+%,()':
            elemTotal = elemTotal.replace(char,'|')
        self.elemTotal = set(e for e in elemTotal.split('|') if e!='')
        
        # Implicit multiplication on parentheses? Need to add '*(' or ')*' then
        match self.use_algrebric_multiplication:
            
            # Is any vars right next to any parentheses? ex: a(ab)²c
            case True:
                for e in self.elemTotal:
                    if (e not in USER_FNAMES):
                        if match_exact_tokens(expression,f'{e}('):
                            expression = replace_exact_tokens(expression,{f'{e}(':f'{e}*('})
                        if match_exact_tokens(expression,f'){e}'):
                            expression = replace_exact_tokens(expression,{f'){e}':f')*{e}'})
            
            # At least Support for implicit math operation on parentheses (ex: '*(' '2(a+b)' or '2.59(c²)')
            case False:
                expression = re.sub(r"(\d+(?:\.\d+)?)(\()", r"\1*\2", expression)
        
        # Gather and sort our expression elements
        # they can be either variables, constants, functions, or unrecognized
        self.elemFct = set()
        self.elemConst = set()
        self.elemVar = set()
        self.elemComp = set()

        match self.use_algrebric_multiplication:

            case True:
                for e in self.elemTotal:
                    
                    #we have a function
                    if (e in USER_FNAMES):
                        if f'{e}(' in expression:
                            self.elemFct.add(e)
                            continue
                    
                    #we have float or int?
                    if (e.replace('.','').isdigit()):
                        if (not is_float_compatible(e)):
                            raise Exception(f"Unrecognized Float '{e}'")
                        self.elemConst.add(e)
                        continue
                    
                    #we have a single char alphabetical variable a,x,E ect..
                    if (len(e)==1 and (e in ALPHABET)):
                        self.elemVar.add(e)
                        continue
                    
                    #check if user varnames is ok
                    for c in list(e):
                        if (c not in list(authorized_symbols) + list(IRRATIONALS.keys())):
                            raise Exception(f"Unauthorized Symbol '{c}'")
                            
                    # Then it means we have a composite element (ex 2ab)
                    self.elemComp.add(e)
                    
                    # Separate our composite into a list of int/float with single alphabetical char
                    # ex 24abc1.5 to [24,a,b,c,1.5]
                    esplit = [m for match in re.finditer(r'(\d+\.\d+|\d+)|([a-zA-Z])', e) for m in match.groups() if m]

                    # Store the float or int const elems of the composite
                    for esub in esplit:
                        if (esub.replace('.','').isdigit()):
                            self.elemConst.add(esub)
                        elif (esub.isalpha() and len(esub)==1):
                            self.elemVar.add(esub)
                        else:
                            msg = f"Unknown Element '{esub}' of Composite '{e}'"
                            print(f"Exception: sanatize_math_expression():\n{msg}")
                            raise Exception(msg)
                            
                    # Insert inplicit multiplications
                    expression = replace_exact_tokens(expression,{e:'*'.join(esplit)})
                    continue
                
            case False:
                for e in self.elemTotal:

                    #we have a function
                    if (e in USER_FNAMES):
                        if f'{e}(' in expression:
                            self.elemFct.add(e)
                            continue

                    #we have float or int?
                    if (e.replace('.','').isdigit()):
                        if (not is_float_compatible(e)):
                            raise Exception(f"Unrecognized Float '{e}'")
                        self.elemConst.add(e)
                        continue

                    #we have a variable (ex 'ab' or 'x')
                    if all(c in ALPHABET for c in list(e)):
                        if (e in USER_FNAMES):
                            raise Exception(f"Variable '{e}' is Taken")
                        self.elemVar.add(e)
                        continue

                    #check for bad symbols
                    for c in list(e):
                        if (c not in list(authorized_symbols) + list(IRRATIONALS.keys())):
                            raise Exception(f"Unauthorized Symbol '{c}'")

                    #unauthorized variable? technically, it's unrecognized
                    raise Exception(f"Unauthorized Variable '{e}'")
        
        #Order our variable alphabetically
        self.elemVar = sorted(self.elemVar)

        # Ensure user is using correct symbols #NOTE we do that 3 times already tho.. reperitive.
        for char in expression:
            if (char not in authorized_symbols):
                raise Exception(f"Unauthorized Symbol '{char}'")
        
        return expression
    
    def apply_macros_to_math_expression(self, expression) -> str:
        """Replace macros such as 'Pi' 'eNum' or else..  by their values"""
        
        modified_expression = None
        
        for k,v in MACROS.items():
            if (k in expression):
                if (modified_expression is None):
                    modified_expression = expression
                modified_expression = modified_expression.replace(k,v)
            
        return modified_expression
    
    def store_equation_as_frame(self, text):
        """we store the user text data as a frame"""

        ng = self.node_tree

        frame = ng.nodes.get("EquationStorage")
        if (frame is None):
            frame = ng.nodes.new('NodeFrame')
            frame.name = "EquationStorage"
            frame.width = 750
            frame.height = 50
            frame.location.x = -1000
            frame.label_size = 20

        if (frame.label!=text):
            frame.label = text

        return None

    def apply_math_expression(self) -> None:
        """transform the math expression into sockets and nodes arrangements"""
        
        # Support for automatically replacing uer symbols
        if (self.use_macros):
            newexp = self.apply_macros_to_math_expression(self.user_mathexp)
            if (newexp is not None):
                self.user_mathexp = newexp
                # We just sent an update signal by modifying self.user_mathexp
                # let's stop here then, the function will restart shortly and we don't have a recu error.
                return None
        
        ng = self.node_tree 
        in_nod, out_nod = ng.nodes["Group Input"], ng.nodes["Group Output"]
        
        # Reset error message
        self.error_message = self.debug_sanatized = self.debug_fctexp = ""
        
        # Keepsafe the math expression within the group
        self.store_equation_as_frame(self.user_mathexp)
        
        # First we make sure the user expression is correct
        try:
            rval = self.sanatize_math_expression(self.user_mathexp)
        except Exception as e:
            self.error_message = str(e)
            self.debug_sanatized = 'Failed'
            return None
        
        # Define the result of sanatize_math_expression
        sanatized_expr = self.debug_sanatized = rval
        elemVar, elemConst = self.elemVar, self.elemConst
        
        # Clear node tree
        for node in list(ng.nodes).copy():
            if (node.name not in {"Group Input", "Group Output", "EquationStorage",}):
                ng.nodes.remove(node)
                
        # Create new sockets depending on vars
        if (elemVar):
            current_vars = [s.name for s in in_nod.outputs]
            for var in elemVar:
                if (var not in current_vars):
                    create_socket(ng, in_out='INPUT', socket_type="NodeSocketFloat", socket_name=var,)
        
        # Remove unused vars sockets
        idx_to_del = []
        for idx,socket in enumerate(in_nod.outputs):
            if ((socket.type!='CUSTOM') and (socket.name not in elemVar)):
                idx_to_del.append(idx)
        for idx in reversed(idx_to_del):
            remove_socket(ng, idx, in_out='INPUT')
        
        # Let's collect equivalence between varnames/const and the pythonAPI
        vareq, consteq = dict(), dict()
        
        # Fill equivalence dict with it's socket eq
        if (elemVar):
            for s in in_nod.outputs:
                if (s.name in elemVar):
                    vareq[s.name] = get_socket_python_api(in_nod, s.identifier)
                
        # Add input for constant right below the vars group input
        if (elemConst):
            xloc, yloc = in_nod.location.x, in_nod.location.y-330
            for const in elemConst:
                con_nod = ng.nodes.new('ShaderNodeValue')
                con_nod.outputs[0].default_value = float(const)
                con_nod.name = const
                con_nod.label = const
                con_nod.location.x = xloc
                con_nod.location.y = yloc
                yloc -= 90
                # Also fill const to socket equivalence dict
                consteq[const] = get_socket_python_api(con_nod, con_nod.outputs[0].identifier)
        
        # Give it a refresh signal, when we remove/create a lot of sockets, the customnode inputs/outputs need a kick
        self.update()
        
        # if we don't have any elements to work with, quit
        if not (elemVar or elemConst):
            return None
        
        # Transform user expression into pure function expression
        try:
            transformer = FunctionTransformer()
            fctexp = transformer.transform_math_expression(sanatized_expr)
        except Exception as e:
            self.error_message = str(e)
            self.debug_fctexp = 'Failed'
            return None
        
        self.debug_fctexp = fctexp
        
        # Execute the function expression to arrange the user nodetree
        try:
            execute_math_function_expression(
                customnode=self, expression=fctexp, node_tree=ng, varsapi=vareq, constapi=consteq,
                )
        except Exception as e:
            self.error_message = str(e)
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
        field.prop(self, "user_mathexp", placeholder="(a + sin(b)/c)²", text="",)
        
        opt = row.row(align=True)
        opt.scale_x = 0.35
        opt.prop(self, "use_algrebric_multiplication", text="ab", toggle=True, )
        
        opt = row.row(align=True)
        opt.scale_x = 0.3
        opt.prop(self, "use_macros", text="π", toggle=True, )
        
        if (is_error):
            lbl = col.row()
            lbl.alert = is_error
            lbl.label(text=self.error_message)
        
        layout.separator(factor=0.75)
        
        return None
    
    @classmethod
    def update_all_instances(cls, from_depsgraph=False,):
        """search for all nodes of this type and update them"""

        return None
