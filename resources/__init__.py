# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy
import bpy.utils.previews

import os 


PREVIEWS_ICONS = {} #Our custom "W_" Icons are stored here
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def get_previews_from_directory(directory, extension=".png", previews=None,):
    """install previews with bpy.utils.preview, will try to search for all image file inside given directory"""

    if (previews is None):
        previews = bpy.utils.previews.new()

    for f in os.listdir(directory):
        if (f.endswith(extension)):

            icon_name = f[:-len(extension)]
            path = os.path.abspath(os.path.join(directory, f))

            if (not os.path.isfile(path)):
                print(f"ERROR: get_previews_from_directory(): File not found: {path}")  # Debugging aid
                continue
            try:
                previews.load(icon_name, path, "IMAGE")
            except Exception as e:
                print(f"ERROR: get_previews_from_directory(): loading icon {icon_name} from '{path}':\n{e}")
                continue

        continue 

    return previews 

def remove_previews(previews):
    """remove previews wuth bpy.utils.preview"""

    bpy.utils.previews.remove(previews)
    previews.clear()

    return None


def cust_icon(str_value):

    if (str_value.startswith("W_")):
        global PREVIEWS_ICONS
        if (str_value in PREVIEWS_ICONS):
            return PREVIEWS_ICONS[str_value].icon_id
        return 1

    return 0


def load_icons():

    global PREVIEWS_ICONS
    print(CURRENT_DIR)
    PREVIEWS_ICONS = get_previews_from_directory(CURRENT_DIR, extension=".png",)

    return None 

def unload_icons():

    global PREVIEWS_ICONS
    remove_previews(PREVIEWS_ICONS)

    return None 