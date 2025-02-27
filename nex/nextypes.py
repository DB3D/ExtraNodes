# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
#
# SPDX-License-Identifier: GPL-2.0-or-later

# TODO better error for user
#  - need better traceback error for NexError so user can at least now the line where it got all wrong.
#  - it's a bit useless to see a Cannot add 'AnonymousVariable' of type.. with type.. 
#    perhaps just don't tell the user varname if we can print the line?

import bpy

import traceback

from ..__init__ import dprint
from ..nex.pytonode import convert_pyvar_to_data
from ..nex import nodesetter as ns
from ..utils.node_utils import (
    create_new_nodegroup,
    set_socket_defvalue,
    get_socket,
    get_socket_type,
    set_socket_type,
    create_socket,
    get_socket_from_socketui,
    remove_socket,
    set_socket_label,
    link_sockets,
    create_constant_input,
)


NEXEQUIVALENCE = {
    #inputs
    'inbool':  'NodeSocketBool',
    'inint':   'NodeSocketInt',
    'infloat': 'NodeSocketFloat',
    'invec':   'NodeSocketVector',
    'incol':   'NodeSocketColor',
    'inquat':  'NodeSocketRotation',
    'inmat':   'NodeSocketMatrix',
    #outputs
    'outbool': 'NodeSocketBool',
    'outint':  'NodeSocketInt',
    'outfloat':'NodeSocketFloat',
    'outvec':  'NodeSocketVector',
    'outcol':  'NodeSocketColor',
    'outquat': 'NodeSocketRotation',
    'outmat':  'NodeSocketMatrix',
    }


class NexError(Exception):
    def __init__(self, message):
        super().__init__(message)


class Nex:
    """parent class of all Nex subclasses"""

    _instance_counter = 0 # - Needed to define nxid, see nxid note.
    node_inst = None      # - the node affiliated with this Nex type
    node_tree = None      # - the node.nodetree affiliated with this Nex type
    nxstype = ''          # - the type of socket the Nex type is using
    nxshort = ''          # - the short name of the nex type (for display reasons)

    def __init__(*args, **kwargs):
        nxsock = None  # - The most important part of a NexType, it's association with an output socket!
        nxvname = None # - The name of the variable, if available. High change the variable will be anonymous. Unsure if it's needed to keep this
        nxid = None    # - In order to not constantly rebuild the nodetree, but still update 
                       # some python evaluated values to the nodetree constants (nodes starting with "C|" in the tree)
                       # we need to have some sort of stable id for our nex Instances.
                       # the problem is that these instances can be anonymous. So here i've decided to identify by instance generation count.

    def __repr__(self):
        return f"<{type(self)}{self.nxid} nxvname='{self.nxvname}'  nxsock=`{self.nxsock}` isoutput={self.nxsock.is_output}' socketnode='{self.nxsock.node.name}''{self.nxsock.node.label}'>"


def create_Nex_constant(node_tree, NexType, nodetype:str, value,):
    """Create a new input node (if not already exist) ensure it's default value, then assign to a NexType & return it."""

    new = NexType(manualdef=True)
    tag = f"{new.nxshort}{new.nxid}"

    # create_constant_input() is smart it will create the node only if it doesn't exist, & ensure (new?) values
    newsock = create_constant_input(node_tree, nodetype, value, tag)

    new.nxsock = newsock
    new.nxvname = 'AnonymousVariable'

    return new

def call_Nex_operand(socketfunction, node_tree, NexType, nxA, nxB):
    """call the socketfunction related to the operand with sockets of our NexTypes, and return a 
    new NexType from the newly formed socket.
    
    Each new node the socketfunctions will create will be tagged, as it is essential that we don't create & 
    link the nodes if there's no need to do so, as a Nex script can be executed very frequently. 
    
    We tag them using the Nex id and types to ensure uniqueness of our values. If a tag already exists, 
    then it means the nodetree structure must still be good"""

    print("call_Nex_operand")

    argtags = f"{nxA.nxshort}{nxA.nxid},{nxB.nxshort}{nxB.nxid}"
    tag = f"F|{NexType.nxshort}.{socketfunction.__name__}({argtags})"

    node = node_tree.nodes.get(tag)
    if (node is None):
        newsock = socketfunction(nxA.nxsock,nxB.nxsock)
        node = newsock.node
        node.name = node.label = tag
    else:
        newsock = node.outputs[0]

    new = NexType(fromsocket=newsock)
    return new


def NexFactory(factor_customnode_instance, factory_classname:str, factory_outsocktype:str='',):
    """return a nex type, which is simply an overloaded custom type that automatically arrange links and nodes and
    set default values. The nextypes will/should only build the nodetree and links when neccessary"""

    class NexFloat(Nex):
        
        _instance_counter = 0
        node_inst = factor_customnode_instance
        node_tree = node_inst.node_tree
        nxstype = 'NodeSocketFloat'
        nxshort = 'Nf'

        def __init__(self, varname='', value=None, fromsocket=None, manualdef=False):

            #create a stable identifier for our NexObject
            self.nxid = NexFloat._instance_counter
            NexFloat._instance_counter += 1

            #on some occation we might want to first initialize this new python object, and define it later (ot get the id)
            if (manualdef):
                return None

            #initialize from a socket?
            if (fromsocket is not None):
                self.nxsock = fromsocket
                self.nxvname = 'AnonymousVariable'
                return None
            
            # Now, define different initialization depending on given value type
            # NOTE we are relying on string name for robustness. Stumble into an issue where 
            # `match value: case NexOutput():` didn't work. Probably because of runtime initialization of 
            # checking a type that didn't already exist yet. Unsure how to solve this problem. Easier to use names for now.

            type_name = type(value).__name__
            match type_name: 

                # a:infloat = anotherinfloat
                case 'NexFloat':
                    raise NexError(f"Invalid use of Inputs. Cannot assign 'NexInput' to 'NexInput'.")

                # is user toying with  output? output cannot be reused in any way..
                case 'NexOutput':
                    raise NexError(f"Invalid use of Outputs. Cannot assign 'NexOutput' to 'NexInput'.")

                # initial creation by assignation, we need to create a socket type
                case 'int'|'float'|'bool':

                    assert varname!='', "NexInput Initialization should always define a varname"
                    outsock = get_socket(self.node_tree, in_out='INPUT', socket_name=varname,)

                    if (value is not None):
                        value = float(value)
                        set_socket_defvalue(self.node_tree, socket=outsock, node=self.node_inst, value=value, in_out='INPUT')

                    self.nxsock = outsock
                    self.nxvname = varname

                # wrong initialization?
                case _:
                    raise NexError(f"NexTypeError. Cannot assign var '{varname}' of type '{type(value).__name__}' to 'NexFloat'.")

            print(f'DEBUG: {type(self).__name__}.__init__({value}). Instance:',self)
            return None

        # Additions

        def __add__(self, other):

            # define each add builtin behaviors depending on other arg type.
            # for each types, we define operation members a &, b

            type_name = type(other).__name__
            match type_name:

                case 'NexFloat':
                    a = self
                    b = other
                    socketfunction = ns.add

                case 'int'|'float'|'bool': 
                    a = self
                    b = create_Nex_constant(self.node_tree, NexFloat, 'ShaderNodeValue',  float(other),)
                    socketfunction = ns.add

                case _:
                    raise NexError(f"NexTypeError. Cannot add '{self.nxvname}' of type 'NexFloat' to '{type(other).__name__}'.")

            c = call_Nex_operand(socketfunction, self.node_tree, NexFloat, a, b)
            return c

        def __radd__(self, other):
            """a+b == b+a, we should be fine"""
            return self.__add__(other)


    class NexOutput(Nex):
        """A nex output is just a simple linking operation. We only assign to an output.
        After assinging the final output not a lot of other operations are possible"""

        _instance_counter = 0
        node_inst = factor_customnode_instance
        node_tree = node_inst.node_tree
        nxstype = factory_outsocktype
        nxshort = 'Nout'
        
        outsubtype = nxstype.replace("NodeSocket","")

        def __init__(self, varname='', value=0.0):

            assert varname!='', "NexOutput Initialization should always define a varname"
            self.nxvname = varname

            # create a stable identifier for our NexObject
            self.nxid = NexOutput._instance_counter
            NexOutput._instance_counter += 1

            # add a socket to this object
            outsock = get_socket(self.node_tree, in_out='OUTPUT', socket_name=varname,)
            self.nxsock = outsock

            type_name = type(value).__name__
            match type_name:

                # is user toying with  output? output cannot be reused in any way..
                case 'NexOutput':
                    raise NexError(f"Invalid use of Outputs. Cannot assign 'NexOutput' to 'NexOutput'.")

                # we link another nextype
                case _ if ('Nex' in type_name):
                    l = link_sockets(value.nxsock, outsock)
                    # we might need to send a refresh signal before checking is_valid property?? if it works, it works
                    if (not l.is_valid):
                        raise NexError(f"NexTypeError. Cannot assign var '{varname}' of type '{type(value).__name__}' to 'NexOutput' of subtype '{self.outsubtype}'.")

                # or we simply output a default python constant value
                case _:
                    newval, _, socktype = convert_pyvar_to_data(value)
                    # just do a try except to see if the var assignment to python is working.. easier.
                    try:
                        set_socket_defvalue(self.node_tree, value=newval, socket=outsock, in_out='OUTPUT',)
                    except Exception as e:
                        raise NexError(f"NexTypeError. Cannot assign var '{varname}' of type '{type(value).__name__}' to 'NexOutput' of subtype '{self.outsubtype}'.")

    
    # return the class
    ReturnClass = locals().get(factory_classname)
    if (ReturnClass is None):
        raise Exception(f"Type '{factory_classname}' not supported")

    return ReturnClass