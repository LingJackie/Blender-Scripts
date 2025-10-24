import bpy
import itertools

'''
This blender script merges all combos of objects in Blender into one object per combination.
For example if the objects are named top0, top1, bottom0, bottom1, bottom2, legs0, legs1,
the script will create objects like top0_bottom0_legs0, top0_bottom0_legs1, top0_bottom1_legs0, etc.
'''

# Define categories and options
categories = {
    "top": [0, 1,2],
    "bottom": [0, 1, 2, 3],
    "legs": [0, 1],
   
}

collection_name = "MeshParts"
output_collection = "MergedModels"

# Ensure output collection exists
if output_collection not in bpy.data.collections:
    bpy.data.collections.new(output_collection)
    bpy.context.scene.collection.children.link(bpy.data.collections[output_collection])

# Cartesian product of all options
combinations = list(itertools.product(*categories.values()))

for combo in combinations:
    combo_dict = dict(zip(categories.keys(), combo))
    combo_name = "_".join([f"{k}{v}" for k, v in combo_dict.items()])

    # Find and duplicate objects
    objects_to_merge = []
    for k, v in combo_dict.items():
        obj_name = f"{k}{v}"
        obj = bpy.data.collections[collection_name].objects.get(obj_name)
        if obj:
            dup = obj.copy()
            dup.data = obj.data.copy()
            bpy.data.collections[output_collection].objects.link(dup)
            objects_to_merge.append(dup)

    # Join objects
    if objects_to_merge:
        bpy.context.view_layer.objects.active = objects_to_merge[0]
        for obj in objects_to_merge:
            obj.select_set(True)
        bpy.ops.object.join()
        merged = bpy.context.active_object
        merged.name = combo_name
        merged.select_set(False)