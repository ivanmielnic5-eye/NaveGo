import json
m = json.load(open("manifest.json"))
# Bbox real del MBTiles (cobertura efectiva)
m["coverage"]["bbox_wgs84"] = [-61.095695, -34.968970, -57.941380, -31.216923]
json.dump(m, open("manifest.json", "w"), indent=2, ensure_ascii=False)
print("bbox_wgs84 -> cobertura real del MBTiles")
