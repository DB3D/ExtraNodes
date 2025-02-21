# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN
#
# SPDX-License-Identifier: GPL-2.0-or-later


from . camerainfo import EXTRANODES_NG_camerainfo
from . isrenderedview import EXTRANODES_NG_isrenderedview
from . sequencervolume import EXTRANODES_NG_sequencervolume
from . mathexpression import EXTRANODES_NG_mathexpression
from . pythonapi import EXTRANODES_NG_pythonapi


#NOTE order will be order of appearance in addmenu
classes = (
    
    EXTRANODES_NG_camerainfo,
    EXTRANODES_NG_isrenderedview,
    EXTRANODES_NG_sequencervolume,
    EXTRANODES_NG_mathexpression,
    EXTRANODES_NG_pythonapi,
    
    )
