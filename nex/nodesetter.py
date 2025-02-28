# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
#
# SPDX-License-Identifier: GPL-2.0-or-later

# NOTE this module gather all kind of math function for sockets
#  when executing these functions, it will create and link new nodes automatically, from sockets to sockets.

# TODO it would be nice that we could support a python float value so we directly set a default value.


import bpy 

import inspect
from functools import partial

from ..utils.node_utils import link_sockets, frame_nodes

sfloat = bpy.types.NodeSocketFloat


NODE_YOFF, NODE_XOFF = 120, 70
_USER_FUNCTIONS = [] #don't import that directly, use get_user_functions, thanks.


def usernamespace(func):
    """decorator to easily store function names on an orderly manner at runtime"""
    _USER_FUNCTIONS.append(func)
    return func

def get_user_functions(fctsubset='float', default_ng=None):
    """get all functions and their names, depending on function types
    optionally, pass the default ng"""

    filtered_functions = []
    match fctsubset:
        case 'float':
            filtered_functions = [f for f in _USER_FUNCTIONS if inspect.signature(f).return_annotation is sfloat]
        case _:
            raise Exception("notSupported")

    # If a default node group argument is provided, use functools.partial to bind it
    if (default_ng):
        filtered_functions = [partial(f, default_ng) for f in filtered_functions]

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


def _floatmath(ng, operation_type:str, val1:sfloat|float=None, val2:sfloat|float=None, val3:sfloat|float=None,) -> sfloat:
    """generic operation for adding a float math node and linking"""

    last = ng.nodes.active
    location = (0,200,)
    if (last):
        location = (last.location.x+last.width+NODE_XOFF, last.location.y-NODE_YOFF,)

    node = ng.nodes.new('ShaderNodeMath')
    node.operation = operation_type
    node.use_clamp = False
    
    node.location = location
    ng.nodes.active = node #Always set the last node active for the final link
    
    values = (val1, val2, val3,)
    for i,val in enumerate(values):
        match val:
            case sfloat(): link_sockets(val, node.inputs[i])
            case float() | int(): node.inputs[i].default_value = val
            case bool(): node.inputs[i].default_value = float(val)
            case None: pass
            case _: raise Exception(f"ArgsTypeError for _floatmath(). Expected parameters in 'Socket', 'float', 'int', 'bool'. Recieved '{type(val).__name__}'")

    return node.outputs[0]

@usernamespace
def add(ng, a:sfloat|float, b:sfloat|float,) -> sfloat:
    """Addition.\nEquivalent to the '+' symbol."""
    return _floatmath(ng,'ADD',a,b)

@usernamespace
def sub(ng, a:sfloat|float, b:sfloat|float,) -> sfloat:
    """Subtraction.\nEquivalent to the '-' symbol."""
    return _floatmath(ng,'SUBTRACT',a,b)

@usernamespace
def mult(ng, a:sfloat|float, b:sfloat|float,) -> sfloat:
    """Multiplications.\nEquivalent to the '*' symbol."""
    return _floatmath(ng,'MULTIPLY',a,b)

@usernamespace
def div(ng, a:sfloat|float, b:sfloat|float,) -> sfloat:
    """Division.\nEquivalent to the '/' symbol."""
    return _floatmath(ng,'DIVIDE',a,b)

@usernamespace
def pow(ng, a:sfloat|float, n:sfloat|float,) -> sfloat:
    """A Power n.\nEquivalent to the 'a**n' and '²' symbol."""
    return _floatmath(ng,'POWER',a,n)

@usernamespace
def log(ng, a:sfloat|float, b:sfloat|float,) -> sfloat:
    """Logarithm A base B."""
    return _floatmath(ng,'LOGARITHM',a,b)

@usernamespace
def sqrt(ng, a:sfloat|float,) -> sfloat:
    """Square Root of A."""
    return _floatmath(ng,'SQRT',a)

@usernamespace
def invsqrt(ng, a:sfloat|float,) -> sfloat:
    """1/ Square Root of A."""
    return _floatmath(ng,'INVERSE_SQRT',a)

@usernamespace
def nroot(ng, a:sfloat|float, n:sfloat|float,) -> sfloat:
    """A Root N. a**(1/n.)"""
    _x = div(ng,1,n)
    _r = pow(ng,a,_x)
    frame_nodes(ng, _x.node, _r.node, label='nRoot')
    return _r

@usernamespace
def abs(ng, a:sfloat|float,) -> sfloat:
    """Absolute of A."""
    return _floatmath(ng,'ABSOLUTE',a)

@usernamespace
def neg(ng, a:sfloat|float,) -> sfloat:
    """Negate the value of A.\nEquivalent to the symbol '-x.'"""
    _r = sub(ng,0,a)
    _r.node.name = 'Negate'
    return _r

@usernamespace
def min(ng, a:sfloat|float, b:sfloat|float,) -> sfloat:
    """Minimum between A & B."""
    return _floatmath(ng,'MINIMUM',a,b)

@usernamespace
def smin(ng, a:sfloat|float, b:sfloat|float, dist:sfloat|float,) -> sfloat:
    """Minimum between A & B considering a smoothing distance."""
    return _floatmath(ng,'SMOOTH_MIN',a,b,dist)

@usernamespace
def max(ng, a:sfloat|float, b:sfloat|float,) -> sfloat:
    """Maximum between A & B."""
    return _floatmath(ng,'MAXIMUM',a,b)

@usernamespace
def smax(ng, a:sfloat|float, b:sfloat|float, dist:sfloat|float,) -> sfloat:
    """Maximum between A & B considering a smoothing distance."""
    return _floatmath(ng,'SMOOTH_MAX',a,b,dist)

@usernamespace
def round(ng, a:sfloat|float,) -> sfloat:
    """Round a Float to an Integer."""
    return _floatmath(ng,'ROUND',a)

@usernamespace
def floor(ng, a:sfloat|float,) -> sfloat:
    """Floor a Float to an Integer."""
    return _floatmath(ng,'FLOOR',a)

@usernamespace
def ceil(ng, a:sfloat|float,) -> sfloat:
    """Ceil a Float to an Integer."""
    return _floatmath(ng,'CEIL',a)

@usernamespace
def trunc(ng, a:sfloat|float,) -> sfloat:
    """Trunc a Float to an Integer."""
    return _floatmath(ng,'TRUNC',a)

@usernamespace
def frac(ng, a:sfloat|float,) -> sfloat:
    """Fraction.\nThe fraction part of A."""
    return _floatmath(ng,'FRACT',a)

@usernamespace
def mod(ng, a:sfloat|float, b:sfloat|float,) -> sfloat:
    """Modulo.\nEquivalent to the '%' symbol."""
    return _floatmath(ng,'MODULO',a,b)

@usernamespace
def fmod(ng, a:sfloat|float, b:sfloat|float,) -> sfloat:
    """Floored Modulo."""
    return _floatmath(ng,'FLOORED_MODULO',a,b)

@usernamespace
def wrap(ng, v:sfloat|float, a:sfloat|float, b:sfloat|float,) -> sfloat:
    """Wrap value to Range A B."""
    return _floatmath(ng,'WRAP',v,a,b)

@usernamespace
def snap(ng, v:sfloat|float, i:sfloat|float,) -> sfloat:
    """Snap to Increment."""
    return _floatmath(ng,'SNAP',v,i)

@usernamespace
def pingpong(ng, v:sfloat|float, scale:sfloat|float,) -> sfloat:
    """PingPong. Wrap a value and every other cycles at cycle Scale."""
    return _floatmath(ng,'PINGPONG',v,scale)

@usernamespace
def floordiv(ng, a:sfloat|float, b:sfloat|float,) -> sfloat: #Custom
    """Floor Division.\nEquivalent to the '//' symbol."""
    _x = div(ng,a,b)
    _r = floor(ng,_x)
    frame_nodes(ng, _x.node, _r.node, label='FloorDiv')
    return _r

@usernamespace
def sin(ng, a:sfloat|float,) -> sfloat:
    """The Sine of A."""
    return _floatmath(ng,'SINE',a)

@usernamespace
def cos(ng, a:sfloat|float,) -> sfloat:
    """The Cosine of A."""
    return _floatmath(ng,'COSINE',a)

@usernamespace
def tan(ng, a:sfloat|float,) -> sfloat:
    """The Tangent of A."""
    return _floatmath(ng,'TANGENT',a)

@usernamespace
def asin(ng, a:sfloat|float,) -> sfloat:
    """The Arcsine of A."""
    return _floatmath(ng,'ARCSINE',a)

@usernamespace
def acos(ng, a:sfloat|float,) -> sfloat:
    """The Arccosine of A."""
    return _floatmath(ng,'ARCCOSINE',a)

@usernamespace
def atan(ng, a:sfloat|float,) -> sfloat:
    """The Arctangent of A."""
    return _floatmath(ng,'ARCTANGENT',a)

@usernamespace
def hsin(ng, a:sfloat|float,) -> sfloat:
    """The Hyperbolic Sine of A."""
    return _floatmath(ng,'SINH',a)

@usernamespace
def hcos(ng, a:sfloat|float,) -> sfloat:
    """The Hyperbolic Cosine of A."""
    return _floatmath(ng,'COSH',a)

@usernamespace
def htan(ng, a:sfloat|float,) -> sfloat:
    """The Hyperbolic Tangent of A."""
    return _floatmath(ng,'TANH',a)

@usernamespace
def rad(ng, a:sfloat|float,) -> sfloat:
    """Convert from Degrees to Radians."""
    return _floatmath(ng,'RADIANS',a)

@usernamespace
def deg(ng, a:sfloat|float,) -> sfloat:
    """Convert from Radians to Degrees."""
    return _floatmath(ng,'DEGREES',a)

def _mix(ng, data_type:str, val1:sfloat|float=None, val2:sfloat|float=None, val3:sfloat|float=None,) -> sfloat:
    """generic operation for adding a mix node and linking"""

    last = ng.nodes.active
    location = (0,200,)
    if (last):
        location = (last.location.x+last.width+NODE_XOFF, last.location.y-NODE_YOFF,)

    node = ng.nodes.new('ShaderNodeMix')
    node.data_type = data_type
    node.clamp_factor = False

    node.location = location
    ng.nodes.active = node #Always set the last node active for the final link

    # Need to choose socket depending on node data_type (hidden sockets)
    indexes = None
    match data_type:
        case 'FLOAT':
            indexes = (0,2,3)
        case _:
            raise Exception("Integration Needed")

    for i,val in zip(indexes,(val1,val2,val3)):    
        match val:
            case sfloat(): link_sockets(val, node.inputs[i])
            case float() | int(): node.inputs[i].default_value = val
            case bool(): node.inputs[i].default_value = float(val)
            case None: pass
            case _: raise Exception(f"ArgsTypeError for _mix(). Expected parameters in 'Socket', 'float', 'int', 'bool'. Recieved '{type(val).__name__}'")

    return node.outputs[0]

@usernamespace
def lerp(ng, f:sfloat|float, a:sfloat|float, b:sfloat|float,) -> sfloat:
    """Mix.\nLinear Interpolation of value A and B from given factor."""
    return _mix(ng,'FLOAT',f,a,b)

@usernamespace
def mix(ng, f:sfloat|float, a:sfloat|float, b:sfloat|float,) -> sfloat: 
    """Alternative notation to lerp() function."""
    return lerp(ng,f,a,b)

def _floatclamp(ng, clamp_type:str, val1:sfloat|float=None, val2:sfloat|float=None, val3:sfloat|float=None,) -> sfloat:
    """generic operation for adding a mix node and linking"""

    last = ng.nodes.active
    location = (0,200,)
    if (last):
        location = (last.location.x+last.width+NODE_XOFF, last.location.y-NODE_YOFF,)

    node = ng.nodes.new('ShaderNodeClamp')
    node.clamp_type = clamp_type

    node.location = location
    ng.nodes.active = node #Always set the last node active for the final link
    
    values = (val1, val2, val3,)
    for i,val in enumerate(values):   
        match val:
            case sfloat(): link_sockets(val, node.inputs[i])
            case float() | int(): node.inputs[i].default_value = val
            case bool(): node.inputs[i].default_value = float(val)
            case None: pass
            case _: raise Exception(f"ArgsTypeError for _floatclamp(). Expected parameters in 'Socket', 'float', 'int', 'bool'. Recieved '{type(val).__name__}'")

    return node.outputs[0]

@usernamespace
def clamp(ng, v:sfloat|float, a:sfloat|float, b:sfloat|float,) -> sfloat:
    """Clamp value between min an max."""
    return _floatclamp(ng,'MINMAX',v,a,b)

@usernamespace
def clampr(ng, v:sfloat|float, a:sfloat|float, b:sfloat|float,) -> sfloat:
    """Clamp value between auto-defined min/max."""
    return _floatclamp(ng,'RANGE',v,a,b)

def _maprange(ng, data_type:str, interpolation_type:str, val1:sfloat|float=None, val2:sfloat|float=None, val3:sfloat|float=None, val4:sfloat|float=None, val5:sfloat|float=None, val6:sfloat|float=None,) -> sfloat:
    """generic operation for adding a remap node and linking"""

    last = ng.nodes.active
    location = (0,200,)
    if (last):
        location = (last.location.x+last.width+NODE_XOFF, last.location.y-NODE_YOFF,)

    node = ng.nodes.new('ShaderNodeMapRange')
    node.data_type = data_type
    node.interpolation_type = interpolation_type
    node.clamp = False

    node.location = location
    ng.nodes.active = node #Always set the last node active for the final link

    values = (val1, val2, val3, val4, val5, val6,)
    for i,val in enumerate(values):
        match val:
            case sfloat(): link_sockets(val, node.inputs[i])
            case float() | int(): node.inputs[i].default_value = val
            case bool(): node.inputs[i].default_value = float(val)
            case None: pass
            case _: raise Exception(f"ArgsTypeError for _maprange(). Expected parameters in 'Socket', 'float', 'int', 'bool'. Recieved '{type(val).__name__}'")

    return node.outputs[0]

@usernamespace
def map(ng, val:sfloat|float, a:sfloat|float, b:sfloat|float, x:sfloat|float, y:sfloat|float,) -> sfloat:
    """Map Range.\nRemap a value from a fiven A,B range to a X,Y range."""
    return _maprange(ng,'FLOAT','LINEAR',val,a,b,x,y)

@usernamespace
def mapst(ng, val:sfloat|float, a:sfloat|float, b:sfloat|float, x:sfloat|float, y:sfloat|float, step:sfloat|float,) -> sfloat:
    """Map Range (Stepped).\nRemap a value from a fiven A,B range to a X,Y range with step."""
    return _maprange(ng,'FLOAT','STEPPED',val,a,b,x,y,step)

@usernamespace
def mapsmo(ng, val:sfloat|float, a:sfloat|float, b:sfloat|float, x:sfloat|float, y:sfloat|float,) -> sfloat:
    """Map Range (Smooth).\nRemap a value from a fiven A,B range to a X,Y range."""
    return _maprange(ng,'FLOAT','SMOOTHSTEP',val,a,b,x,y)

@usernamespace
def mapsmoo(ng, val:sfloat|float, a:sfloat|float, b:sfloat|float, x:sfloat|float, y:sfloat|float,) -> sfloat:
    """Map Range (Smoother).\nRemap a value from a fiven A,B range to a X,Y range."""
    return _maprange(ng,'FLOAT','SMOOTHERSTEP',val,a,b,x,y)

#TODO support comparison functions
# def equal(a:sfloat|float, b:sfloat|float,)
# def notequal(a:sfloat|float, b:sfloat|float,)
# def aequal(a:sfloat|float, b:sfloat|float, threshold:sfloat|float,)
# def anotequal(a:sfloat|float, b:sfloat|float, threshold:sfloat|float,)
# def issmaller(a:sfloat|float, b:sfloat|float,)
# def isasmaller(a:sfloat|float, b:sfloat|float, threshold:sfloat|float,)
# def isbigger(a:sfloat|float, b:sfloat|float,)
# def isabigger(a:sfloat|float, b:sfloat|float, threshold:sfloat|float,)
# def isbetween(a:sfloat|float, x:sfloat|float, y:sfloat|float,)
# def isabetween(a:sfloat|float, x:sfloat|float, y:sfloat|float, threshold:sfloat|float,)
# def isbetweeneq(a:sfloat|float, x:sfloat|float, y:sfloat|float,)
