import json

from lxml import etree  # ty:ignore[unresolved-import]
from pathlib import Path

import utils
from src.utils import (
    get_modified_file_if_possible,
)



def get_engine_data(file_path: Path, ui_dict:dict[str,str], use_initial_files: bool) -> dict[str, dict]:
    rets: dict[str, dict] = {}
    engine_file = file_path.stem
    contents = get_modified_file_if_possible(file_path, use_initial_files)

    parser = etree.XMLParser(recover=True)
    wrapped_xml_data = f"<fake_root>{contents}</fake_root>"
    root = etree.fromstring(wrapped_xml_data, parser=parser)
    engine_variants = root.find("EngineVariants")
    if engine_variants is None:
        print(f"Engine variants not found in {file_path}")
    else:
        for engine in engine_variants.findall("Engine"):
            engine_data: dict = {}
            engine_id = engine.get("Name")
            engine_data["id"] = engine_id
            engine_data["ui_desc_id"] = engine.find("GameData").find("UiDesc").get("UiDesc")
            engine_data["engine_file"] = engine_file
            torque = int(engine.get("Torque"))
            engine_data["torque"] = torque
            engine_data["critical_damage_threshold"] = float(engine.get("CriticalDamageThreshold"))
            engine_data["damage_capacity"] = int(engine.get("DamageCapacity"))
            fuel_consumption = float(engine.get("FuelConsumption"))
            engine_data["fuel_consumption"] = fuel_consumption
            engine_data["torque_efficiency"] = round(float(torque/fuel_consumption/1000.0),1)
            engine_data["price"] = int(engine.find("GameData").get("Price"))
            engine_ui_name = engine.find("GameData").find("UiDesc").get("UiName")
            if engine_ui_name in ui_dict:
                engine_data["name"] = ui_dict[engine_ui_name]
            else:
                engine_data["name"] = engine_ui_name
            # engine_data["name"] = get_ui_dict_result(engine.find("GameData").find("UiDesc").get("UiName"))

            rets[f"{engine_file}-{engine_id}"] = engine_data

    return rets


def get_all_engine_data(use_initial_files: bool, ui_dict:dict[str,str]) -> dict[str, dict]:
    all_engine_data: dict[str, dict] = {}
    engine_folder = Path(utils.root_path, "input/initial/[media]/classes/engines")
    dlc_folder = Path(utils.root_path, "input/initial/[media]/_dlc")

    # Iterate through all XML files in the folder
    for file_path in engine_folder.glob("*.xml"):
        all_engine_data.update(get_engine_data(file_path, ui_dict, use_initial_files))

    for file_path in dlc_folder.glob(
        "dlc_*/classes/engines/*.xml", case_sensitive=False
    ):
        all_engine_data.update(get_engine_data(file_path,ui_dict, use_initial_files))

    return all_engine_data


def process_engine_data(use_initial_files: bool, ui_dict:dict[str,str]) -> dict[str, dict]:
    engine_dict: dict[str, dict] = get_all_engine_data(use_initial_files, ui_dict)
    addition = ""
    if not use_initial_files:
        addition = "_edited"
    with open(f"../reference/info/engine_data{addition}.json", "w", encoding="utf-8") as f:
        json.dump(engine_dict, f, indent=4)
    return engine_dict


def update_engine_data_with_truck_data(truck_dict: dict[str, dict], engine_dict: dict[str, dict]) -> dict[str, dict]:
    for engine_id, engine_data in engine_dict.items():
        trucks = []
        for truck_id, truck_data in truck_dict.items():
            if engine_data["engine_file"] in truck_data["engine_types"]:
                trucks.append(truck_data["name"])

        engine_dict[engine_id]["trucks"] = ", ".join(trucks)
    return engine_dict

