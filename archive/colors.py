# import json
# from pathlib import Path
# import xml.etree.ElementTree as ET
#
#
# def get_split_color(c_str_1:str) -> dict[str,float]:
#     c_str = c_str_1.replace("g","").replace(" ","").replace("(","").replace(")","").strip()
#     splits = c_str.split(";")
#     return {
#         "r":float(splits[0]),
#         "g":float(splits[1]),
#         "b":float(splits[2]),
#     }
#
#
# def main():
#     colours = []
#     with open(Path("reference/colours_to_add.json"), "r") as f:
#         colours = json.load(f)
#
#     tree = ET.parse("input/initial/[media]/classes/customization_presets/customization_preset.xml")
#     root = tree.getroot()
#
#     # with open(Path("input/initial/[media]/classes/customization_presets/customization_preset.xml"), "r") as f:
#     #     xml_data = f.read()
#     # root = ET.fromstring(xml_data)
#     for truck in root.findall("Truck"):
#         name = truck.attrib["Name"]
#         ids: list[int] = []
#         existing_colours:list[dict] = []
#         for preset in truck.findall("CustomizationPreset"):
#             colour_id = int(preset.attrib["Id"])
#             ids.append(colour_id)
#             c_str_1 = preset.attrib["TintColor1"]
#             c_str_2 = preset.attrib["TintColor2"]
#             c_str_3 = preset.attrib["TintColor3"]
#             if c_str_1 != c_str_2 and c_str_2 != c_str_3 and c_str_1 != c_str_3:
#                 color_1: dict[str, float] = get_split_color(c_str_1)
#                 color_2: dict[str, float] = get_split_color(c_str_2)
#                 color_3: dict[str, float] = get_split_color(c_str_3)
#                 existing_colours.append({"1": color_1, "2": color_2, "3": color_3})
#
#         max_id = max(ids)+1
#         for colour in colours:
#             if colour["vehicle"] != name and {"1": colour["1"], "2": colour["2"], "3": colour["3"]} not in existing_colours:
#                 print(f"Adding {colour['vehicle']} with id {max_id}")
#                 ET.SubElement(
#                     truck,
#                     "CustomizationPreset",
#                     Id=str(max_id),
#                     TintColor1=f"g({int(colour['1']['r'])}; {int(colour['1']['g'])}; {int(colour['1']['b'])})",
#                     TintColor2=f"g({int(colour['2']['r'])}; {int(colour['2']['g'])}; {int(colour['2']['b'])})",
#                     TintColor3=f"g({int(colour['3']['r'])}; {int(colour['3']['g'])}; {int(colour['3']['b'])})",
#                     MaterialOverrideName="skin_00",
#                 )
#                 max_id += 1
#     ET.indent(tree)
#     tree.write(Path("input/initial/[media]/classes/customization_presets/customization_preset.xml"), encoding='utf-8')
#
#
#
#
# if __name__ == "__main__":
#     main()