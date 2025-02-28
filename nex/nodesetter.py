# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
#
# SPDX-License-Identifier: GPL-2.0-or-later

# NOTE this module gather all kind of math function for sockets
#  when executing these functions, it will create and link new nodes automatically, from sockets to sockets.
#  the 'update_if_exists' parameter will only update potential default values of existing nodes.


import bpy 

import inspect
from functools import partial

from ..utils.node_utils import link_sockets, frame_nodes


SkFloat = bpy.types.NodeSocketFloat

NODE_YOFF, NODE_XOFF = 120, 70
_USER_FUNCTIONS = [] #don't import that directly, use get_user_functions, thanks.

class InvalidTypePassedToSocket(Exception):
    def __init__(self, message):
        super().__init__(message)


def usernamespace(func):
    """decorator to easily store function names on an orderly manner at runtime"""
    _USER_FUNCTIONS.append(func)
    return func

def get_user_functions(fctsubset='float', default_ng=None):
    """get all functions and their names, depending on function types
    optionally, pass the default ng. The 'update_if_exists' functionality of the functions will be disabled"""

    filtered_functions = []
    match fctsubset:
        case 'float':
            filtered_functions = [f for f in _USER_FUNCTIONS if inspect.signature(f).return_annotation is SkFloat]
        case _:
            raise Exception("notSupported")

    # If a default node group argument is provided, use functools.partial to bind it
    if (default_ng):
        filtered_functions = [partial(f, default_ng, update_if_exists='') for f in filtered_functions]

    return filtered_functions

def generate_documentation(fctsubset='float'):
    """generate doc about function subset for user, we are collecting function name and arguments"""

    r = {}
    for f in get_user_functions(fctsubset=fctsubset):

        fargs = list(f.__code__.co_varnames[:f.__code__.co_argcount])
        if ('ng' in fargs):
            fargs.remove('ng')
        fstr = f'{f.__name__}({", ".join(fargs)})'

        r[f.__name__] = {'repr':fstr, 'doc':f.__doc__,}
        continue

    return r


# 88b 88  dP"Yb  8888b.  888888 .dP"Y8     .dP"Y8 888888 888888 888888 888888 88""Yb     888888  dP""b8 888888 .dP"Y8 
# 88Yb88 dP   Yb  8I  Yb 88__   `Ybo."     `Ybo." 88__     88     88   88__   88__dP     88__   dP   `"   88   `Ybo." 
# 88 Y88 Yb   dP  8I  dY 88""   o.`Y8b     o.`Y8b 88""     88     88   88""   88"Yb      88""   Yb        88   o.`Y8b 
# 88  Y8  YbodP  8888Y"  888888 8bodP'     8bodP' 888888   88     88   888888 88  Yb     88      YboodP   88   8bodP' 


def _floatmath(ng, operation_type:str, val1:SkFloat|float=None, val2:SkFloat|float=None, val3:SkFloat|float=None, update_if_exists:str='',) -> SkFloat:
    """generic operation for adding a float math node and linking.
    if 'update_if_exists' is passed the function shall only but update values of existing node, not adding new nodes"""

    node = None
    args = (val1, val2, val3,)
    needs_linking = False

    if (update_if_exists):
        node = ng.nodes.get(update_if_exists)

    if (node is None):
        last = ng.nodes.active
        if (last):
              location = (last.location.x+last.width+NODE_XOFF, last.location.y-NODE_YOFF,)
        else: location = (0,200,)
        node = ng.nodes.new('ShaderNodeMath')
        node.operation = operation_type
        node.use_clamp = False
        node.location = location
        ng.nodes.active = node #Always set the last node active for the final link
        needs_linking = True
    
    for i,val in enumerate(args):
        match val:
            case SkFloat():
                if needs_linking:
                    link_sockets(val, node.inputs[i])
            case float() | int():
                node.inputs[i].default_value = val
            case bool():
                node.inputs[i].default_value = float(val)
            case None:
                pass
            case _:
                raise InvalidTypePassedToSocket(f"ArgsTypeError for _floatmath(). Expected parameters in 'Socket', 'float', 'int', 'bool'. Recieved '{type(val).__name__}'")

    return node.outputs[0]

@usernamespace
def add(ng, a:SkFloat|float, b:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Addition.\nEquivalent to the '+' symbol."""
    return _floatmath(ng,'ADD',a,b, update_if_exists=update_if_exists,)

@usernamespace
def sub(ng, a:SkFloat|float, b:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Subtraction.\nEquivalent to the '-' symbol."""
    return _floatmath(ng,'SUBTRACT',a,b, update_if_exists=update_if_exists,)

@usernamespace
def mult(ng, a:SkFloat|float, b:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Multiplications.\nEquivalent to the '*' symbol."""
    return _floatmath(ng,'MULTIPLY',a,b, update_if_exists=update_if_exists,)

@usernamespace
def div(ng, a:SkFloat|float, b:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Division.\nEquivalent to the '/' symbol."""
    return _floatmath(ng,'DIVIDE',a,b, update_if_exists=update_if_exists,)

@usernamespace
def pow(ng, a:SkFloat|float, n:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """A Power n.\nEquivalent to the 'a**n' and '²' symbol."""
    return _floatmath(ng,'POWER',a,n, update_if_exists=update_if_exists,)

@usernamespace
def log(ng, a:SkFloat|float, b:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Logarithm A base B."""
    return _floatmath(ng,'LOGARITHM',a,b, update_if_exists=update_if_exists,)

@usernamespace
def sqrt(ng, a:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Square Root of A."""
    return _floatmath(ng,'SQRT',a, update_if_exists=update_if_exists,)

@usernamespace
def invsqrt(ng, a:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """1/ Square Root of A."""
    return _floatmath(ng,'INVERSE_SQRT',a, update_if_exists=update_if_exists,)

@usernamespace
def nroot(ng, a:SkFloat|float, n:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """A Root N. a**(1/n.)"""
    
    if (update_if_exists): #this function is created multiple nodes so we need multiple tag
          _x = div(ng,1,n, update_if_exists=f"{update_if_exists}|inner",)
    else: _x = div(ng,1,n,)

    _r = pow(ng,a,_x, update_if_exists=update_if_exists,)
    frame_nodes(ng, _x.node, _r.node, label='nRoot',)
    return _r

@usernamespace
def abs(ng, a:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Absolute of A."""
    return _floatmath(ng,'ABSOLUTE',a, update_if_exists=update_if_exists,)

@usernamespace
def neg(ng, a:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Negate the value of A.\nEquivalent to the symbol '-x.'"""
    _r = sub(ng,0,a, update_if_exists=update_if_exists,)
    frame_nodes(ng, _r.node, label='Negate',)
    return _r

@usernamespace
def min(ng, a:SkFloat|float, b:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Minimum between A & B."""
    return _floatmath(ng,'MINIMUM',a,b, update_if_exists=update_if_exists,)

@usernamespace
def smin(ng, a:SkFloat|float, b:SkFloat|float, dist:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Minimum between A & B considering a smoothing distance."""
    return _floatmath(ng,'SMOOTH_MIN',a,b,dist, update_if_exists=update_if_exists,)

@usernamespace
def max(ng, a:SkFloat|float, b:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Maximum between A & B."""
    return _floatmath(ng,'MAXIMUM',a,b, update_if_exists=update_if_exists,)

@usernamespace
def smax(ng, a:SkFloat|float, b:SkFloat|float, dist:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Maximum between A & B considering a smoothing distance."""
    return _floatmath(ng,'SMOOTH_MAX',a,b,dist, update_if_exists=update_if_exists,)

@usernamespace
def round(ng, a:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Round a Float to an Integer."""
    return _floatmath(ng,'ROUND',a, update_if_exists=update_if_exists,)

@usernamespace
def floor(ng, a:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Floor a Float to an Integer."""
    return _floatmath(ng,'FLOOR',a, update_if_exists=update_if_exists,)

@usernamespace
def ceil(ng, a:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Ceil a Float to an Integer."""
    return _floatmath(ng,'CEIL',a, update_if_exists=update_if_exists,)

@usernamespace
def trunc(ng, a:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Trunc a Float to an Integer."""
    return _floatmath(ng,'TRUNC',a, update_if_exists=update_if_exists,)

@usernamespace
def frac(ng, a:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Fraction.\nThe fraction part of A."""
    return _floatmath(ng,'FRACT',a, update_if_exists=update_if_exists,)

@usernamespace
def mod(ng, a:SkFloat|float, b:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Modulo.\nEquivalent to the '%' symbol."""
    return _floatmath(ng,'MODULO',a,b, update_if_exists=update_if_exists,)

@usernamespace
def fmod(ng, a:SkFloat|float, b:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Floored Modulo."""
    return _floatmath(ng,'FLOORED_MODULO',a,b, update_if_exists=update_if_exists,)

@usernamespace
def wrap(ng, v:SkFloat|float, a:SkFloat|float, b:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Wrap value to Range A B."""
    return _floatmath(ng,'WRAP',v,a,b, update_if_exists=update_if_exists,)

@usernamespace
def snap(ng, v:SkFloat|float, i:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Snap to Increment."""
    return _floatmath(ng,'SNAP',v,i, update_if_exists=update_if_exists,)

@usernamespace
def pingpong(ng, v:SkFloat|float, scale:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """PingPong. Wrap a value and every other cycles at cycle Scale."""
    return _floatmath(ng,'PINGPONG',v,scale, update_if_exists=update_if_exists,)

@usernamespace
def floordiv(ng, a:SkFloat|float, b:SkFloat|float, update_if_exists:str='',) -> SkFloat: #Custom
    """Floor Division.\nEquivalent to the '//' symbol."""

    if (update_if_exists): #this function is created multiple nodes so we need multiple tag
          _x = div(ng,a,b,update_if_exists=f"{update_if_exists}|inner",)
    else: _x = div(ng,a,b)

    _r = floor(ng,_x)
    frame_nodes(ng, _x.node, _r.node, label='FloorDiv',)
    return _r

@usernamespace
def sin(ng, a:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """The Sine of A."""
    return _floatmath(ng,'SINE',a, update_if_exists=update_if_exists,)

@usernamespace
def cos(ng, a:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """The Cosine of A."""
    return _floatmath(ng,'COSINE',a, update_if_exists=update_if_exists,)

@usernamespace
def tan(ng, a:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """The Tangent of A."""
    return _floatmath(ng,'TANGENT',a, update_if_exists=update_if_exists,)

@usernamespace
def asin(ng, a:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """The Arcsine of A."""
    return _floatmath(ng,'ARCSINE',a, update_if_exists=update_if_exists,)

@usernamespace
def acos(ng, a:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """The Arccosine of A."""
    return _floatmath(ng,'ARCCOSINE',a, update_if_exists=update_if_exists,)

@usernamespace
def atan(ng, a:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """The Arctangent of A."""
    return _floatmath(ng,'ARCTANGENT',a, update_if_exists=update_if_exists,)

@usernamespace
def hsin(ng, a:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """The Hyperbolic Sine of A."""
    return _floatmath(ng,'SINH',a, update_if_exists=update_if_exists,)

@usernamespace
def hcos(ng, a:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """The Hyperbolic Cosine of A."""
    return _floatmath(ng,'COSH',a, update_if_exists=update_if_exists,)

@usernamespace
def htan(ng, a:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """The Hyperbolic Tangent of A."""
    return _floatmath(ng,'TANH',a, update_if_exists=update_if_exists,)

@usernamespace
def rad(ng, a:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Convert from Degrees to Radians."""
    return _floatmath(ng,'RADIANS',a, update_if_exists=update_if_exists,)

@usernamespace
def deg(ng, a:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Convert from Radians to Degrees."""
    return _floatmath(ng,'DEGREES',a, update_if_exists=update_if_exists,)

def _mix(ng, data_type:str, val1:SkFloat|float=None, val2:SkFloat|float=None, val3:SkFloat|float=None, update_if_exists:str='',) -> SkFloat:
    """generic operation for adding a mix node and linking.
    if 'update_if_exists' is passed the function shall only but update values of existing node, not adding new nodes"""

    node = None
    args = (val1, val2, val3,)
    needs_linking = False

    if (update_if_exists):
        node = ng.nodes.get(update_if_exists)

    if (node is None):
        last = ng.nodes.active
        if (last):
              location = (last.location.x+last.width+NODE_XOFF, last.location.y-NODE_YOFF,)
        else: location = (0,200,)
        node = ng.nodes.new('ShaderNodeMix')
        node.data_type = data_type
        node.clamp_factor = False
        node.location = location
        ng.nodes.active = node #Always set the last node active for the final link
        needs_linking = True

    # Need to choose socket depending on node data_type (hidden sockets)
    indexes = None
    match data_type:
        case 'FLOAT':
            indexes = (0,2,3)
        case _:
            raise Exception("Integration Needed")

    for i,val in zip(indexes,args):    
        match val:
            case SkFloat():
                if needs_linking:
                    link_sockets(val, node.inputs[i])
            case float() | int():
                node.inputs[i].default_value = val
            case bool():
                node.inputs[i].default_value = float(val)
            case None:
                pass
            case _:
                raise InvalidTypePassedToSocket(f"ArgsTypeError for _mix(). Expected parameters in 'Socket', 'float', 'int', 'bool'. Recieved '{type(val).__name__}'")

    return node.outputs[0]

@usernamespace
def lerp(ng, f:SkFloat|float, a:SkFloat|float, b:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Mix.\nLinear Interpolation of value A and B from given factor."""
    return _mix(ng,'FLOAT',f,a,b)

@usernamespace
def mix(ng, f:SkFloat|float, a:SkFloat|float, b:SkFloat|float, update_if_exists:str='',) -> SkFloat: 
    """Alternative notation to lerp() function."""
    return lerp(ng,f,a,b)

def _floatclamp(ng, clamp_type:str, val1:SkFloat|float=None, val2:SkFloat|float=None, val3:SkFloat|float=None, update_if_exists:str='',) -> SkFloat:
    """generic operation for adding a mix node and linking"""

    node = None
    args = (val1, val2, val3,)
    needs_linking = False

    if (update_if_exists):
        node = ng.nodes.get(update_if_exists)

    if (node is None):
        last = ng.nodes.active
        if (last):
              location = (last.location.x+last.width+NODE_XOFF, last.location.y-NODE_YOFF,)
        else: location = (0,200,)
        node = ng.nodes.new('ShaderNodeClamp')
        node.clamp_type = clamp_type
        node.location = location
        ng.nodes.active = node #Always set the last node active for the final link
        needs_linking = True

    for i,val in enumerate(args):
        match val:
            case SkFloat():
                if needs_linking:
                    link_sockets(val, node.inputs[i])
            case float() | int():
                node.inputs[i].default_value = val
            case bool():
                node.inputs[i].default_value = float(val)
            case None:
                pass
            case _:
                raise InvalidTypePassedToSocket(f"ArgsTypeError for _floatclamp(). Expected parameters in 'Socket', 'float', 'int', 'bool'. Recieved '{type(val).__name__}'")

    return node.outputs[0]

@usernamespace
def clamp(ng, v:SkFloat|float, a:SkFloat|float, b:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Clamp value between min an max."""
    return _floatclamp(ng,'MINMAX',v,a,b)

@usernamespace
def clampr(ng, v:SkFloat|float, a:SkFloat|float, b:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Clamp value between auto-defined min/max."""
    return _floatclamp(ng,'RANGE',v,a,b)

def _maprange(ng, data_type:str, interpolation_type:str, val1:SkFloat|float=None, val2:SkFloat|float=None, val3:SkFloat|float=None,
    val4:SkFloat|float=None, val5:SkFloat|float=None, val6:SkFloat|float=None, update_if_exists:str='',) -> SkFloat:
    """generic operation for adding a remap node and linking"""

    node = None
    args = (val1, val2, val3, val4, val5, val6,)
    needs_linking = False

    if (update_if_exists):
        node = ng.nodes.get(update_if_exists)

    if (node is None):
        last = ng.nodes.active
        if (last):
              location = (last.location.x+last.width+NODE_XOFF, last.location.y-NODE_YOFF,)
        else: location = (0,200,)
        node = ng.nodes.new('ShaderNodeMapRange')
        node.data_type = data_type
        node.interpolation_type = interpolation_type
        node.clamp = False
        node.location = location
        ng.nodes.active = node #Always set the last node active for the final link
        needs_linking = True

    for i,val in enumerate(args):
        match val:
            case SkFloat():
                if needs_linking:
                    link_sockets(val, node.inputs[i])
            case float() | int():
                node.inputs[i].default_value = val
            case bool():
                node.inputs[i].default_value = float(val)
            case None:
                pass
            case _:
                raise InvalidTypePassedToSocket(f"ArgsTypeError for _maprange(). Expected parameters in 'Socket', 'float', 'int', 'bool'. Recieved '{type(val).__name__}'")

    return node.outputs[0]

@usernamespace
def map(ng, val:SkFloat|float, a:SkFloat|float, b:SkFloat|float, x:SkFloat|float, y:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Map Range.\nRemap a value from a fiven A,B range to a X,Y range."""
    return _maprange(ng,'FLOAT','LINEAR',val,a,b,x,y)

@usernamespace
def mapst(ng, val:SkFloat|float, a:SkFloat|float, b:SkFloat|float, x:SkFloat|float, y:SkFloat|float, step:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Map Range (Stepped).\nRemap a value from a fiven A,B range to a X,Y range with step."""
    return _maprange(ng,'FLOAT','STEPPED',val,a,b,x,y,step)

@usernamespace
def mapsmo(ng, val:SkFloat|float, a:SkFloat|float, b:SkFloat|float, x:SkFloat|float, y:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Map Range (Smooth).\nRemap a value from a fiven A,B range to a X,Y range."""
    return _maprange(ng,'FLOAT','SMOOTHSTEP',val,a,b,x,y)

@usernamespace
def mapsmoo(ng, val:SkFloat|float, a:SkFloat|float, b:SkFloat|float, x:SkFloat|float, y:SkFloat|float, update_if_exists:str='',) -> SkFloat:
    """Map Range (Smoother).\nRemap a value from a fiven A,B range to a X,Y range."""
    return _maprange(ng,'FLOAT','SMOOTHERSTEP',val,a,b,x,y)

#TODO support comparison functions
# def equal(a:SkFloat|float, b:SkFloat|float,)
# def notequal(a:SkFloat|float, b:SkFloat|float,)
# def aequal(a:SkFloat|float, b:SkFloat|float, threshold:SkFloat|float,)
# def anotequal(a:SkFloat|float, b:SkFloat|float, threshold:SkFloat|float,)
# def issmaller(a:SkFloat|float, b:SkFloat|float,)
# def isasmaller(a:SkFloat|float, b:SkFloat|float, threshold:SkFloat|float,)
# def isbigger(a:SkFloat|float, b:SkFloat|float,)
# def isabigger(a:SkFloat|float, b:SkFloat|float, threshold:SkFloat|float,)
# def isbetween(a:SkFloat|float, x:SkFloat|float, y:SkFloat|float,)
# def isabetween(a:SkFloat|float, x:SkFloat|float, y:SkFloat|float, threshold:SkFloat|float,)
# def isbetweeneq(a:SkFloat|float, x:SkFloat|float, y:SkFloat|float,)
