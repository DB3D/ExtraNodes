# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later


from . camerainfo import NODEBOOSTER_NG_camerainfo
from . isrenderedview import NODEBOOSTER_NG_isrenderedview
from . sequencervolume import NODEBOOSTER_NG_sequencervolume
from . mathexpression import NODEBOOSTER_NG_mathexpression, NODEBOOSTER_OT_bake_mathexpression
from . pythonapi import NODEBOOSTER_NG_pythonapi


#NOTE order will be order of appearance in addmenu
classes = (
    
    NODEBOOSTER_NG_camerainfo,
    NODEBOOSTER_NG_isrenderedview,
    NODEBOOSTER_NG_sequencervolume,
    NODEBOOSTER_NG_mathexpression,
    NODEBOOSTER_OT_bake_mathexpression, 
    NODEBOOSTER_NG_pythonapi,
    
    )
