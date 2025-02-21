# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy, sys


def get_addon_prefs():
    """get preferences path from base_package, __package__ path change from submodules"""
    return bpy.context.preferences.addons[__package__].preferences


def cleanse_modules():
    """remove all plugin modules from sys.modules for a clean uninstall"""
    #https://devtalk.blender.org/t/plugin-hot-reload-by-cleaning-sys-modules/20040
    
    all_modules = sys.modules
    all_modules = dict(sorted(all_modules.items(),key= lambda x:x[0])) #sort them
    
    for k,v in all_modules.items():
        if k.startswith(__package__):
            del sys.modules[k]

    return None


def get_addon_classes():
    """gather all classes of this plugin that have to be reg/unreg"""
    
    from .addonprefs import classes as addonpref_classes
    from .nodes import classes as nodes_classes
    from .menus import classes as menus_classes
    
    return addonpref_classes + nodes_classes + menus_classes


def register():
    """main addon register"""

    for cls in get_addon_classes():
        bpy.utils.register_class(cls)
    
    from .handlers import register_handlers_and_msgbus    
    register_handlers_and_msgbus()
    
    from .menus import append_menus
    append_menus()
    
    return None


def unregister():
    """main addon un-register"""

    from .menus import remove_menus
    remove_menus()
    
    from .handlers import unregister_handlers_and_msgbus  
    unregister_handlers_and_msgbus()
    
    for cls in reversed(get_addon_classes()):
        bpy.utils.unregister_class(cls)
    
    cleanse_modules()
    
    return None
