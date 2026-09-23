import json
m = json.load(open("manifest.json"))
m["coverage"]["bbox_wgs84"] = [-61.6755, -35.5605, -57.2039, -30.5622]
m["coverage"]["source_route"] = "osm_waterway_river_canal_buffer"
m["tiles"]["vector_layers"] = ["corredor_relevante"]
m["tiles"].pop("layers_note", None)
json.dump(m, open("manifest.json", "w"), indent=2, ensure_ascii=False)
print("Manifest actualizado")
