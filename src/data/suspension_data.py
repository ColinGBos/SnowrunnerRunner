import json

from lxml import etree  # ty:ignore[unresolved-import]
from pathlib import Path

import utils
from src.utils import (
    get_modified_file_if_possible,
)


def update_suspension_data_with_truck_data(truck_dict, suspension_dict) -> dict[str, dict]:
    for _, suspension_data in suspension_dict.items():
        suspension_file:str = suspension_data["suspension_file"]
        truck_names_for_suspension: list[str] = []
        for _, truck_data in truck_dict.items():
            if suspension_file in truck_data["suspension_type"]:
                truck_names_for_suspension.append(truck_data["name"])
        if len(truck_names_for_suspension) == 1:
            suspension_data["truck"] = truck_names_for_suspension[0]
        else:
            suspension_data["truck"] = ", ".join(truck_names_for_suspension)
    return suspension_dict


def get_suspension_data(file_path, use_initial_files, ui_dict: dict[str, str]) -> dict[str, dict]:
    suspension_file = file_path.stem
    rets: dict[str, dict] = {}
    contents = get_modified_file_if_possible(file_path, use_initial_files)

    parser = etree.XMLParser(recover=True)
    wrapped_xml_data = f"<fake_root>{contents}</fake_root>"
    root = etree.fromstring(wrapped_xml_data, parser=parser)
    suspension_variants = root.find("SuspensionSetVariants")
    if suspension_variants is None:
        print(f"Suspension variants not found in {file_path}")
    else:
        for sus_set in suspension_variants.findall("SuspensionSet"):
            suspension_data: dict = {}
            suspension_id = sus_set.get("Name")
            damage_capacity = sus_set.get("DamageCapacity")
            if damage_capacity is not None:
                suspension_data["damage_capacity"] = int(damage_capacity)
            suspension_data["suspension_file"] = suspension_file
            crit_damage_threshold = sus_set.get("CriticalDamageThreshold")
            if crit_damage_threshold is not None:
                suspension_data["critical_damage_threshold"] = float(crit_damage_threshold)
            suspension_data["id"] = suspension_id
            suspension_data["ui_desc_id"] = (
                sus_set.find("GameData").find("UiDesc").get("UiDesc")
            )
            ui_name = sus_set.find("GameData").find("UiDesc").get("UiName")
            if ui_name in ui_dict:
                suspension_data["name"] = ui_dict[ui_name]
            else:
                suspension_data["name"] = sus_set.find("GameData").find("UiDesc").get("UiName")
            suspension_data["active"] = (
                sus_set.get("DeviationDelta") is not None
            )
            suspension_data["price"] = sus_set.find("GameData").get("Price")
            suspension_data["requires_exploration"] = sus_set.find("GameData").get("UnlockByExploration").lower() == "true"
            for sus in sus_set.findall("Suspension"):
                wheel_type = sus.get("WheelType")
                if wheel_type.lower() != "middle":
                    max_height = float(sus.get("Height"))
                    suspension_data[f"{wheel_type}_height"] = max_height
                    suspension_data[f"{wheel_type}_strength"] = float(sus.get("Strength"))
                    damping = sus.get("Damping")
                    if damping is not None:
                        suspension_data[f"{wheel_type}_damping"] = float(damping)
                    dev_delta = sus.get("DeviationMax")
                    if dev_delta is not None:
                        suspension_data[f"{wheel_type}_dev_delta"] = float(dev_delta)
                        max_height = max_height+float(dev_delta)
                    suspension_data[f"{wheel_type}_max_height"] = max_height

            rets[f"{suspension_file}-{suspension_id}"] = suspension_data

    return rets


def get_all_suspension_data(use_initial_files, ui_dict: dict[str, str], input_folder: str) -> dict[str, dict]:
    all_suspension_dict: dict[str, dict] = {}
    suspension_folder = Path(utils.root_path, f"{input_folder}/initial/[media]/classes/suspensions")
    mod_folder = Path(utils.root_path, "input/mods")
    dlc_folder = Path(utils.root_path, f"{input_folder}/initial/[media]/_dlc")

    # Iterate through all XML files in the folder
    for file_path in suspension_folder.glob("*.xml"):
        all_suspension_dict.update(get_suspension_data(file_path, use_initial_files, ui_dict))

    for file_path in mod_folder.glob("*/classes/suspensions/*.xml"):
        all_suspension_dict.update(get_suspension_data(file_path, True, ui_dict))

    for file_path in dlc_folder.glob(
        "dlc_*/classes/suspensions/*.xml", case_sensitive=False
    ):
        all_suspension_dict.update(get_suspension_data(file_path, use_initial_files, ui_dict))
    return all_suspension_dict


def process_suspension_data(use_initial_files, ui_dict: dict[str, str], input_folder: str):
    data_dict: dict[str, dict] = get_all_suspension_data(use_initial_files, ui_dict, input_folder)
    addition = ""
    if not use_initial_files:
        addition = "_edited"
    with open(f"../reference/info/suspension_data{addition}.json", "w", encoding="utf-8") as f:
        json.dump(data_dict, f, indent=4)
    return data_dict



