# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
#
# SPDX-License-Identifier: GPL-2.0-or-later


#TODO ideas for later
#  - Share nodes between ShaderEditor/Compositor as well? Would be nice to introduce BaseClass then..
#  - MathExpression node could have a big brother supporting plenty of other datatype, not only floats.. 
#    Vectors, Rotation, Comparison, Matrix ect.. Auto socket type swap as well
#  - Sequencer volume could use some options for sampling a specific time. Perhaps sampling other elements of the sound?
#  - Other node ideas from user feedback?
#  - Maybe copy some nodewrangler functionality such as quick mix so user don't rely on both plugins and swap to Booster ;-)
#  - for custom nodes could use blender new message system to display an error message on header perhaps?

#TODO
#  - copy/pasting a node with ctrlc/v is not working 

#NOTE You might stumble into this crash when hot-reloading (enable/disable) the plugin on blender 4.2/4.2
#     https://projects.blender.org/blender/blender/issues/134669 Has been fixed in 4.4. Only impacts developers hotreloading.

import bpy


def get_addon_prefs():
    """get preferences path from base_package, __package__ path change from submodules"""
    return bpy.context.preferences.addons[__package__].preferences

def isdebug():
    return get_addon_prefs().debug

def dprint(thing):
    if isdebug():
        print(thing)

def cleanse_modules():
    """remove all plugin modules from sys.modules for a clean uninstall (dev hotreload solution)"""
    # See https://devtalk.blender.org/t/plugin-hot-reload-by-cleaning-sys-modules/20040 fore more details.

    import sys

    all_modules = sys.modules
    all_modules = dict(sorted(all_modules.items(),key= lambda x:x[0])) #sort them

    for k,v in all_modules.items():
        if k.startswith(__package__):
            del sys.modules[k]

    return None


def get_addon_classes(revert=False):
    """gather all classes of this plugin that have to be reg/unreg"""

    from .properties import classes as sett_classes
    from .operators import classes as ope_classes
    from .customnodes import classes as nodes_classes
    from .ui import classes as ui_classes

    classes = sett_classes + ope_classes + nodes_classes + ui_classes

    if (revert):
        return reversed(classes)

    return classes


def register():
    """main addon register"""

    from .resources import load_icons
    load_icons() 
    
    #register every single addon classes here
    for cls in get_addon_classes():
        bpy.utils.register_class(cls)

    from .properties import load_properties
    load_properties()

    from .handlers import load_handlers    
    load_handlers()

    from .ui import load_ui
    load_ui()

    from .operators import load_operators_keymaps
    load_operators_keymaps()
    

    return None


def unregister():
    """main addon un-register"""

    from .operators import unload_operators_keymaps
    unload_operators_keymaps()

    from .ui import unload_ui
    unload_ui()

    from .handlers import unload_handlers  
    unload_handlers()

    from .properties import unload_properties
    unload_properties()

    #unregister every single addon classes here
    for cls in get_addon_classes(revert=True):
        bpy.utils.unregister_class(cls)

    from .resources import unload_icons
    unload_icons() 

    cleanse_modules()

    return None
