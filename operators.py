import bpy
from bpy_extras.io_utils import ImportHelper

from bpy.props import (IntProperty,
                       BoolProperty,
                       StringProperty,
                       CollectionProperty,
                       PointerProperty)

from bpy.types import (Operator,
                       Panel,
                       PropertyGroup,
                       UIList)
class CUSTOM_OT_list_aware(Operator):
    """An abstract base class, used to store the names of a (Scene) list property used to populate a UI element, and the index of the currently active item in that list. Internal only."""
    list_prop_name: bpy.props.StringProperty(
        name="List Property Name",
        description="The name of the list property to operate on",
        default=""
    )
    
    active_index_prop_name: bpy.props.StringProperty(
        name="Active List Index Property Name",
        description="The name of the (scene) property used to store the index of the active item in the list",
        default=""
    )

    def targets(self, context):
        targets = getattr(context.scene, self.list_prop_name)
        idx = getattr(context.scene, self.active_index_prop_name)
        return (idx, targets)
    

class CUSTOM_OT_actions(CUSTOM_OT_list_aware):
    """Move items up and down, add and remove"""
    bl_idname = "custom.list_action"
    bl_label = "List Actions"
    bl_description = "Move items up and down, add and remove"
    bl_options = {'REGISTER'}

    action: bpy.props.EnumProperty(
        items=(
            ('UP', "Up", ""),
            ('DOWN', "Down", ""),
            ('REMOVE', "Remove", ""),
            ('ADD', "Add", "")))

    def invoke(self, context, event):
        scn = context.scene
        idx, targets = self.get_targets(context)

        try:
            item = targets[idx]
        except IndexError:
            pass
        else:
            if self.action == 'DOWN' and idx < len(targets) - 1:
                item_next = targets[idx+1].name
                targets.move(idx, idx+1)
                index += 1
                info = 'Item "%s" moved to position %d' % (item.name, index + 1)
                self.report({'INFO'}, info)

            elif self.action == 'UP' and idx >= 1:
                item_prev = targets[idx-1].name
                targets.move(idx, idx-1)
                idx -= 1
                info = 'Item "%s" moved to position %d' % (item.name, idx + 1)
                self.report({'INFO'}, info)

            elif self.action == 'REMOVE':
                info = 'Item "%s" removed from list' % (targets[idx].name)
                idx -= 1
                targets.remove(idx)
                self.report({'INFO'}, info)
                
        if self.action == 'ADD':
            if context.object:
                if any(target.name == context.object.name for target in targets):
                    self.report({'INFO'}, 'Item already exists in target list')
                else:
                    item = targets.add()
                    item.name = context.object.name
                    item.obj = context.object
                    idx = len(targets)-1
                    info = '"%s" added to LiveLinkFace targets' % (item.name)
                    self.report({'INFO'}, info)
            else:
                self.report({'INFO'}, "Nothing selected in the Viewport")
        return {"FINISHED"}
    

class CUSTOM_OT_addViewportSelection(CUSTOM_OT_list_aware):
    """Add all items currently selected in the viewport"""
    bl_idname = "custom.add_viewport_selection"
    bl_label = "Add Viewport Selection to List"
    bl_description = "Add all items currently selected in the viewport"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        idx, targets = self.get_targets(context)
        scn = context.scene
        selected_objs = context.selected_objects
        if selected_objs:
            new_objs = []
            for i in selected_objs:
                item = targets.add()
                item.name = i.name
                item.obj = i
                new_objs.append(item.name)
            info = ', '.join(map(str, new_objs))
            self.report({'INFO'}, 'Added: "%s"' % (info))
        else:
            self.report({'INFO'}, "Nothing selected in the Viewport")
        return{'FINISHED'}
    
    
class CUSTOM_OT_printItems(Operator):
    """Print all items and their properties to the console"""
    bl_idname = "custom.print_items"
    bl_label = "Print Items to Console"
    bl_description = "Print all items and their properties to the console"
    bl_options = {'REGISTER', 'UNDO'}
    
    reverse_order: BoolProperty(
        default=False,
        name="Reverse Order")
    
    @classmethod
    def poll(cls, context):
        idx, targets = self.get_targets(context)
        return bool(targets)
    
    def execute(self, context):
        scn = context.scene

        idx, targets = self.get_targets(context)
        if self.reverse_order:
            for i in range(idx, -1, -1):        
                ob = targets[i].obj
                print ("Object:", ob,"-",ob.name, ob.type)
        else:
            for item in targets:
                ob = item.obj
                print ("Object:", ob,"-",ob.name, ob.type)
        return{'FINISHED'}


class CUSTOM_OT_clearList(CUSTOM_OT_list_aware):
    """Clear all items of the list"""
    bl_idname = "custom.clear_list"
    bl_label = "Clear List"
    bl_description = "Clear all items of the list"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        idx, targets = self.get_targets(context)
        return bool(targets)

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)
        
    def execute(self, context):
        idx, targets = self.get_targets(context)
        if bool(targets):
            targets.clear()
            self.report({'INFO'}, "All items removed")
        else:
            self.report({'INFO'}, "Nothing to remove")
        return{'FINISHED'}
    
    
class CUSTOM_OT_removeDuplicates(CUSTOM_OT_list_aware):
    """Remove all duplicates"""
    bl_idname = "custom.remove_duplicates"
    bl_label = "Remove Duplicates"
    bl_description = "Remove all duplicates"
    bl_options = {'INTERNAL'}

    def find_duplicates(self, context):
        """find all duplicates by name"""
        idx, targets = self.get_targets(context)
        name_lookup = {}
        for c, i in enumerate(targets):
            name_lookup.setdefault(i.obj.name, []).append(c)
        duplicates = set()
        for name, indices in name_lookup.items():
            for i in indices[1:]:
                duplicates.add(i)
        return sorted(list(duplicates))
        
    @classmethod
    def poll(cls, context):
        idx, targets = self.get_targets(context)
        return bool(targets)
        
    def execute(self, context):
        scn = context.scene
        idx, targets = self.get_targets(context)
        removed_items = []
        # Reverse the list before removing the items
        for i in self.find_duplicates(context)[::-1]:
            targets.remove(i)
            removed_items.append(i)
        if removed_items:
            idx = len(targets)-1
            info = ', '.join(map(str, removed_items))
            self.report({'INFO'}, "Removed indices: %s" % (info))
        else:
            self.report({'INFO'}, "No duplicates")
        return{'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)
    
    
class CUSTOM_OT_selectItems(CUSTOM_OT_list_aware):
    """Select Items in the Viewport"""
    bl_idname = "custom.select_items"
    bl_label = "Select Item(s) in Viewport"
    bl_description = "Select Items in the Viewport"
    bl_options = {'REGISTER', 'UNDO'}

    select_all = BoolProperty(
        default=False,
        name="Select all Items of List",
        options={'SKIP_SAVE'})
        
    @classmethod
    def poll(cls, context):
        idx, targets = self.get_targets(context)
        return bool(targets)
    
    def execute(self, context):
        scn = context.scene

        idx, targets = self.get_targets(context)
        
        try:
            item = targets[idx]
        except IndexError:
            self.report({'INFO'}, "Nothing selected in the list")
            return{'CANCELLED'}
                   
        obj_error = False
        bpy.ops.object.select_all(action='DESELECT')
        if not self.select_all:
            name = targets[idx].obj.name
            obj = scn.objects.get(name, None)
            if not obj: 
                obj_error = True
            else:
                obj.select_set(True)
                info = '"%s" selected in Vieport' % (obj.name)
        else:
            selected_items = []
            unique_objs = set([i.obj.name for i in targets])
            for i in unique_objs:
                obj = scn.objects.get(i, None)
                if obj:
                    obj.select_set(True)
                    selected_items.append(obj.name)
            
            if not selected_items: 
                obj_error = True
            else:
                missing_items = unique_objs.difference(selected_items)
                if not missing_items:
                    info = '"%s" selected in Viewport' \
                        % (', '.join(map(str, selected_items)))
                else:
                    info = 'Missing items: "%s"' \
                        % (', '.join(map(str, missing_items)))
        if obj_error: 
            info = "Nothing to select, object removed from scene"
        self.report({'INFO'}, info)    
        return{'FINISHED'}


class CUSTOM_OT_deleteObject(CUSTOM_OT_list_aware):
    """Delete object from scene"""
    bl_idname = "custom.delete_object"
    bl_label = "Remove Object from Scene"
    bl_description = "Remove object from scene"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):

        targets = getattr(context.scene, self.list_prop_name)
        return bool(context.scene.ll_targets)

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)
        
    def execute(self, context):
        idx, targets = self.get_targets(context)
        scn = context.scene

        selected_objs = context.selected_objects
        try:
            item = targets[idx]
        except IndexError:
            pass
        else:        
            ob = scn.objects.get(item.obj.name)
            if not ob:
                self.report({'INFO'}, "No object of that name found in scene")
                return {"CANCELLED"}
            else:
                bpy.ops.object.select_all(action='DESELECT')
                ob.select_set(True)
                bpy.ops.object.delete()
                
            info = ' Item "%s" removed from Scene' % (len(selected_objs))
            idx -= 1
            targets.remove(idx)
            self.report({'INFO'}, info)
        return{'FINISHED'}
    
    
class CUSTOM_UL_items(UIList):
   
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        obj = item.obj
        custom_icon = "OUTLINER_OB_%s" % obj.type
        layout.prop(obj, "name", text="", emboss=False, translate=False, icon=custom_icon)
            
    def invoke(self, context, event):
        pass   

__all__ = ['CUSTOM_UL_items', 'CUSTOM_OL_deleteObject', 'CUSTOM_OT_selectItems', 'CUSTOM_OT_removeDuplicates', 'CUSTOM_OT_clearList', 'CUSTOM_OT_printItems', 'CUSTOM_OT_addViewportSelection', 'CUSTOM_OT_actions' ]

