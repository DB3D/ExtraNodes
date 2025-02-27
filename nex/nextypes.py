# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy

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

    _instance_counter = 0 #Needed to define nxid
    node_inst = None
    node_tree = None
    nxstype = ''
    nxstui = '' #Shorter version of nxstype

    def __init__(*args, **kwargs):
        nxsock = None
        nxvname = None
        nxid = None # NOTE What are nex id? well, in order to not constantly rebuild the nodetree, but still update 
                    # some python evaluated values to the nodetree constants (nodes starting with "C|" in the tree)
                    # we need to have some sort of stable id for our nex Instances.
                    # the problem is that these instances can be anonymous. So here i've decided to identify by instance generation count.

        # NOTE we store node_tree and socket blender objects in there. Storing blender object in pyvar is dangerous.
        # HOWEVER we never re-use the initialized class outside of blender context so its totally fine!

    def __repr__(self):
        return f"<{type(self)}{self.nxid} nxstui={self.nxstui} nxvname='{self.nxvname}'  nxsock=`{self.nxsock}` isoutput={self.nxsock.is_output}' socketnode='{self.nxsock.node.name}''{self.nxsock.node.label}'>"



def NexFactory(customnode_instance, gen_classname:str, gen_socket_type:str='', build_tree:bool=False,):
    """return a nex type, which is simply an overloaded type that automatically arrange links sokets together
    enable `build_tree` if you wish to only update constants of the node_tree and not rebuild it!"""

    #TODO implement build_tree... see 'OPTIMIZATION_TODO'
    
    class NexFloat(Nex):
        
        _instance_counter = 0
        node_inst = customnode_instance
        node_tree = node_inst.node_tree
        nxstype = 'NodeSocketFloat'
        nxstui = nxstype.replace("NodeSocket","")

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

            match value:

                # reassignation.. x = a
                case NexFloat():
                    print("is copy?:", value)
                    nxob = value
                    self.nxsock = nxob.nxsock
                    self.nxvname = 'AnonymousVariableCopy'

                # initial creation by assignation, we need to create a socket type
                case int() | float() | bool():
                    
                    assert varname!='', "Development Error! NexInput Initialization should always define a varname"
                    outsock = get_socket(self.node_tree, in_out='INPUT', socket_name=varname,)
                    
                    if (value is not None):
                        value = float(value)
                        set_socket_defvalue(self.node_tree, socket=outsock, node=self.node_inst, value=value, in_out='INPUT')

                    self.nxsock = outsock
                    self.nxvname = varname

                # wrong initialization?
                case _:
                    if issubclass(type(value), Nex):
                        raise NexError(f"'{varname}' invalid type assignation.\nCannot assign '{value.nxstui}' to '{self.nxstui}'")
                    raise NexError(f"'{varname}' invalid type assignation.\nCannot assign '{type(value)}' to '{self.nxstui}'")

            print(f'DEBUG: {type(self).__name__}.__init__({value}). Instance:',self)
            return None

        # Additions

        def __add__(self, other):
            
            # define each add builtin behaviors depending on other arg type.
            # would be nicer to overload.. singledispatchmethod won't work from this Factory context
            match other:

                case NexFloat():
                    # did we already created this operation? check with nodeid if it is the case
                    nodeid = f'F|Nf.add(Nf{self.nxid},Nf{other.nxid})'
                    node = self.node_tree.nodes.get(nodeid)
                    if (node is None):
                        newsock = ns.add(self.nxsock,other.nxsock)
                        node = newsock.node
                        node.name = node.label = nodeid
                    socket = node.outputs[0]
                    return NexFloat(fromsocket=socket,)

                case int() | float() | bool(): 
                    # did we already created the input node constant? 
                    # if yes we need to update value. create_constant_input() will do that
                    newnex = NexFloat(manualdef=True)
                    nodeid = f'{type(self).__name__}{newnex.nxid}'
                    newsock = create_constant_input(self.node_tree, 'ShaderNodeValue', float(other), nodeid,), #will create input of name f'C|{shortype}|{identifier}'
                    newnex.nxsock = newsock
                    newnex.nxvname = 'AnonymousVariable'

                case _:
                    #TODO would be nice to catch the line number in error message..
                    raise NexError(f"Unsupported add operaton for '{self.nxvname}' of type '{self.nxstui}' and {other} of type '{type(other)}'.")

            return None

        def __radd__(self, other):
            """a+b == b+a, we should be fine"""
            return self.__add__(other)


    class NexOutput(Nex):
        """A nex output is just a simple linking operation. We only assign to an output.
        After assinging the final output not a lot of other operations are possible"""

        node_inst = customnode_instance
        node_tree = node_inst.node_tree
        nxstype = gen_socket_type
        nxstui = nxstype.replace("NodeSocket","")

        def __init__(self, varname='', value=0.0):

            assert varname!='', "Development Error! NexOutput should always define a varname"
            self.nxvname = varname

            outsock = get_socket(self.node_tree, in_out='OUTPUT', socket_name=varname,)

            # we link another nextype
            if issubclass(type(value), Nex):
                nxob = value
                l = link_sockets(nxob.nxsock, outsock)
                # we might need to send a refresh signal before checking is_valid property?? if it works, it works
                if (not l.is_valid):
                    raise NexError(f"'{varname}' invalid type assignation.\nCannot assign '{nxob.nxstui}' to '{self.nxstui}'")

            # or we simply output a default python constant value
            else:
                value, _, socktype = convert_pyvar_to_data(value)
                try:
                    set_socket_defvalue(self.node_tree, value=value, socket=outsock, in_out='OUTPUT',)
                except Exception as e:
                    print(f"NexOutput set_socket_defvalue() Errror:\n{type(e).__name__}\n{e}")
                    raise NexError(f"'{varname}' invalid type assignation.\nCannot assign '{socktype}' to '{self.nxstui}'")

    # return the class
    ReturnClass = locals().get(gen_classname)
    if (ReturnClass is None):
        raise Exception(f"Type '{gen_classname}' not supported")

    return ReturnClass