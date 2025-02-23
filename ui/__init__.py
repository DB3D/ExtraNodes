# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later


from .menus import NODEBOOSTER_MT_addmenu_general, append_menus, remove_menus


classes = (
    
    NODEBOOSTER_MT_addmenu_general
)


def load_ui():

    append_menus()

    return None


def unload_ui():

    remove_menus()

    return None
