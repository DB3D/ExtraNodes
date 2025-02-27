# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
#
# SPDX-License-Identifier: GPL-2.0-or-later


import bpy


class NODEBOOSTER_OT_text_templates(bpy.types.Operator):
    bl_idname = "text.text_templates"
    bl_label = "Nex Example"
    bl_description = "Create a new text template with predefined content"

    def execute(self, context):

        text_block = bpy.data.texts.new(name="My Template")

        text_block.clear()
        text_block.write("this\nis\nMy \nText\n")
        self.report({'INFO'}, "My Template created!")

        return {'FINISHED'}