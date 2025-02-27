# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy

import os 


class NODEBOOSTER_OT_text_templates(bpy.types.Operator):
    
    bl_idname = "nodebooster.import_template"
    bl_label = "Code Example"
    bl_description = "Import example code"

    filepath : bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):

        if not os.path.isfile(self.filepath):
            self.report({'ERROR'}, f"File not found: {self.filepath}")
            return {'CANCELLED'}

        dataname = os.path.basename(self.filepath)

        with open(self.filepath, "r", encoding="utf-8") as file:
            file_content = file.read()

        text_block = bpy.data.texts.new(name=dataname)
        text_block.write(file_content)
        context.space_data.text = text_block

        self.report({'INFO'}, f"Imported '{dataname}' into Blender text editor")

        return {'FINISHED'}