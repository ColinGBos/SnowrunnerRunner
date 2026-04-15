import json

from lxml import etree  # ty:ignore[unresolved-import]
from pathlib import Path

import utils
from src.utils import (
    get_modified_file_if_possible,
)


def update_wheel_data_with_truck_data(truck_dict, wheel_dict) -> dict[str, dict]:
    for _, wheel_data in wheel_dict.items():
        wheel_file:str = wheel_data["file"]
        truck_names_for_wheel: list[str] = []
        for _, truck_data in truck_dict.items():
            if wheel_file in truck_data["wheel_types"]:
                truck_names_for_wheel.append(truck_data["name"])
        if len(truck_names_for_wheel) == 1:
            wheel_data["Name"] = f"{wheel_data['Name']} ({truck_names_for_wheel[0]})"
    return wheel_dict


def get_wheel_data(
    file_path: Path, use_initial_files: bool, wheel_template_dict: dict, ui_dict: dict[str, str]
) -> dict[str, dict]:
    rets: dict[str, dict] = {}
    wheel_file = file_path.stem
    contents = get_modified_file_if_possible(file_path, use_initial_files)
    if "_parent" in contents:
        return rets
    parser = etree.XMLParser(recover=True)
    wrapped_xml_data = f"<fake_root>{contents}</fake_root>"
    root = etree.fromstring(wrapped_xml_data, parser=parser)

    template_data = {}

    mass: int = 0
    radius_offset: float = 0
    soft_force_scale: float = 0
    body_friction: float = 0
    asphalt_friction: float = 0
    substance_friction: float = 0

    templates = root.find("_templates")
    if templates is not None:
        tire_templates = templates.find("TruckTire")
        if tire_templates is not None:
            for child in tire_templates:
                wheel_material_template = child.tag
                if child.get("_template") is not None:
                    mass = wheel_template_dict["TruckTire"][child.get("_template")][
                        "Mass"
                    ]
                else:
                    if child.get("Mass") is not None:
                        mass = int(child.get("Mass"))
                softness_element = child.find("WheelSoftness")
                if softness_element is not None:
                    s_type = softness_element.get("_template")
                    if s_type is not None:
                        radius_offset = wheel_template_dict["WheelSoftness"][s_type][
                            "RadiusOffset"
                        ]
                        soft_force_scale = wheel_template_dict["WheelSoftness"][s_type][
                            "SoftForceScale"
                        ]

                friction_element = child.find("WheelFriction")
                if friction_element is not None:
                    f_type = friction_element.get("_template")
                    if f_type is not None:
                        body_friction = wheel_template_dict["WheelFriction"][f_type][
                            "BodyFriction"
                        ]
                        asphalt_friction = wheel_template_dict["WheelFriction"][f_type][
                            "BodyFrictionAsphalt"
                        ]
                        substance_friction = wheel_template_dict["WheelFriction"][
                            f_type
                        ]["SubstanceFriction"]

                template_data[wheel_material_template] = {
                    "Material": wheel_material_template,
                    "Mass": mass,
                    "RadiusOffset": radius_offset,
                    "SoftForceScale": soft_force_scale,
                    "BodyFriction": body_friction,
                    "BodyFrictionAsphalt": asphalt_friction,
                    "SubstanceFriction": substance_friction,
                }

    truck_wheels = root.find("TruckWheels")
    if truck_wheels is None:
        return rets
    damage_capacity = truck_wheels.get("DamageCapacity")
    if damage_capacity is not None:
        damage_capacity = int(truck_wheels.get("DamageCapacity"))
    else:
        damage_capacity = 0
    width = float(truck_wheels.get("Width"))
    width_rear = truck_wheels.get("WidthRear")
    if width_rear is not None:
        width_rear = float(truck_wheels.get("WidthRear"))
    else:
        width_rear = width
    for truck_tire in truck_wheels.find("TruckTires").findall("TruckTire"):
        tire_data: dict = {"file": wheel_file, "full_file": str(file_path.relative_to(utils.root_path))}
        if "_template" in truck_tire.attrib:
            if truck_tire.attrib["_template"] in template_data:
                tire_data.update(template_data[truck_tire.attrib["_template"]])

        tire_data["Mass"] = mass
        tire_data["DamageCapacity"] = damage_capacity
        tire_data["Width"] = width
        tire_data["WidthRear"] = width_rear

        wheel_friction = truck_tire.find("WheelFriction")
        if wheel_friction is not None:
            f_type = wheel_friction.get("_template")
            if f_type is not None:
                tire_data["BodyFriction"] = wheel_template_dict["WheelFriction"][
                    f_type
                ]["BodyFriction"]
                tire_data["BodyFrictionAsphalt"] = wheel_template_dict["WheelFriction"][
                    f_type
                ]["BodyFrictionAsphalt"]
                tire_data["SubstanceFriction"] = wheel_template_dict["WheelFriction"][
                    f_type
                ]["SubstanceFriction"]
        if wheel_friction is not None:
            if "BodyFriction" in wheel_friction.attrib:
                tire_data["BodyFriction"] = float(wheel_friction.attrib["BodyFriction"])
            if "BodyFrictionAsphalt" in wheel_friction.attrib:
                tire_data["BodyFrictionAsphalt"] = float(
                    wheel_friction.attrib["BodyFrictionAsphalt"]
                )
            if "SubstanceFriction" in wheel_friction.attrib:
                tire_data["SubstanceFriction"] = float(
                    wheel_friction.attrib["SubstanceFriction"]
                )

        tire_data["Price"] = float(truck_tire.find("GameData").get("Price"))
        if truck_tire.find("GameData").find("UiDesc") is not None:
            name_id = truck_tire.find("GameData").find("UiDesc").get("UiName")
            tire_data["name_id"] = name_id
            desc_id = truck_tire.find("GameData").find("UiDesc").get("UiDesc")
            tire_data["desc_id"] = desc_id
            if name_id in ui_dict:
                tire_data["Name"] = ui_dict[name_id]
            else:
                tire_data["Name"] = name_id
                print(f"No name for {name_id}")
        if "BodyFriction" not in tire_data:
            print(f"No friction for {wheel_file}-{truck_tire.get('Name')}")
        elif tire_data["BodyFriction"] == 0:
            print(f"Body friction for {wheel_file}-{truck_tire.get('Name')} is 0")
        if (
            "Name" in tire_data
            and tire_data["Name"] != ""
            and "Material" in tire_data
            and tire_data["Material"] != ""
        ):
            rets[f"{wheel_file}-{truck_tire.get('Name')}"] = tire_data

    return rets


def get_wheel_template_info(use_initial_files: bool) -> dict:
    file_path = Path("input/initial/[media]/_templates/trucks.xml")
    contents = get_modified_file_if_possible(file_path, use_initial_files)

    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(contents, parser=parser)

    ret_dict: dict = {}
    wheel_softness_dict = {}
    wheel_softness = root.find("WheelSoftness")
    for child in wheel_softness:
        if child is not None:
            wheel_softness_dict[child.tag] = {
                "RadiusOffset": float(child.get("RadiusOffset")),
                "SoftForceScale": float(child.get("SoftForceScale")),
            }
    ret_dict["WheelSoftness"] = wheel_softness_dict

    wheel_friction_dict = {}
    wheel_friction = root.find("WheelFriction")
    for child in wheel_friction:
        if child is not None:
            wheel_friction_dict[child.tag] = {
                "BodyFriction": float(child.get("BodyFriction")),
                "BodyFrictionAsphalt": float(child.get("BodyFrictionAsphalt")),
                "SubstanceFriction": float(child.get("SubstanceFriction")),
                "UiName": child.get("UiName"),
            }
    ret_dict["WheelFriction"] = wheel_friction_dict

    truck_wheel_dict = {}
    truck_wheel = root.find("TruckWheel")
    for child in truck_wheel:
        if child is not None:
            truck_wheel_dict[child.tag] = {
                "Mass": int(child.get("Mass")),
            }
    ret_dict["TruckWheel"] = truck_wheel_dict

    truck_tire_dict = {}
    truck_tire = root.find("TruckTire")
    for child in truck_tire:
        if child is not None:
            truck_tire_dict[child.tag] = {
                "Mass": int(child.get("Mass")),
            }
    ret_dict["TruckTire"] = truck_tire_dict

    return ret_dict


def get_all_wheel_data(use_initial_files, ui_dict: dict[str, str]):
    all_wheel_data: dict[str, dict] = {}
    gearbox_folder = Path(utils.root_path, "input/initial/[media]/classes/wheels")
    dlc_folder = Path(utils.root_path, "input/initial/[media]/_dlc")

    wheel_template_dict = get_wheel_template_info(use_initial_files)
    addition = ""
    if not use_initial_files:
        addition = "_edited"
    with open(
        f"../reference/info/wheel_template_data{addition}.json", "w", encoding="utf-8"
    ) as f:
        json.dump(wheel_template_dict, f, indent=4)

    # Iterate through all XML files in the folder
    for file_path in gearbox_folder.glob("*.xml"):
        all_wheel_data.update(
            get_wheel_data(file_path, use_initial_files, wheel_template_dict, ui_dict)
        )

    for file_path in dlc_folder.glob(
        "dlc_*/classes/wheels/*.xml", case_sensitive=False
    ):
        all_wheel_data.update(
            get_wheel_data(file_path, use_initial_files, wheel_template_dict, ui_dict)
        )

    return all_wheel_data


def process_wheel_data(use_initial_files, ui_dict: dict[str, str]) -> dict[str, dict]:
    wheel_dict: dict[str, dict] = get_all_wheel_data(use_initial_files, ui_dict)
    addition = ""
    if not use_initial_files:
        addition = "_edited"
    with open(f"../reference/info/wheel_data{addition}.json", "w", encoding="utf-8") as f:
        json.dump(wheel_dict, f, indent=4)
    return wheel_dict



