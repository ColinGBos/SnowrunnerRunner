import json
import re
from pathlib import Path
from typing import Any

import utils
from src.utils import get_modified_file_if_possible


def get_cargo_info(cargo_path, use_initial) -> tuple[str, str, int, int]:
    # print(f"Processing cargo file: {cargo_path}")
    content = get_modified_file_if_possible(cargo_path, use_initial)

    mass_list = re.findall(r'Mass="(\d+)"', content)
    if len(mass_list) > 0:
        file_name = cargo_path.stem
        packed_mass = sum(map(int, mass_list))
        packed_length = int(re.findall(r'CargoLength="(\d+)"', content)[0])
        cargo_type = re.findall(r'CargoType="(\w+)"', content)[0]
        return file_name, cargo_type, packed_mass, packed_length
    return "None", "None", 0, 0


def update_cargos_with_model(cargo_model_path, cargo_dict:dict[str, dict[str, Any]], use_initial) -> dict[str, dict]:
    # print(f"Processing cargo model file: {cargo_model_path}")
    content = get_modified_file_if_possible(cargo_model_path, use_initial)
    mass_list = re.findall(r'Mass="(\d+(?:\.\d+)?)"', content)
    if len(mass_list) > 0:
        unpacked_mass = int(sum(map(float, mass_list)))
        cargo_type_list = re.findall(r'LoadType="(\w+)"', content)
        if len(cargo_type_list) > 0:
            cargo_type = cargo_type_list[0]
            for cargo_name, cargo_data in cargo_dict.items():
                if cargo_data["type"] == cargo_type:
                    cargo_data["unpacked_mass"] = unpacked_mass
    return cargo_dict


def update_cargos_with_type(cargo_type_path: Path, cargo_dict:dict[str, dict[str, Any]], use_initial, ui_dict:dict[str,str]) -> dict[str, dict]:
    content = get_modified_file_if_possible(cargo_type_path, use_initial)
    cargo_type = cargo_type_path.stem
    ui_name_list = re.findall(r'UiName="(\w+)"', content)
    if len(ui_name_list) > 0 and ui_name_list[0] != "":
        for _, cargo_data in cargo_dict.items():
            if cargo_data["type"] == cargo_type:
                cargo_data["name"] = ui_dict[ui_name_list[0]]

    return cargo_dict


def get_all_cargo_data(ui_dict: dict[str, str], use_initial=False, input_folder: str="input") -> dict[str, dict]:

    dlc_folder = Path(utils.root_path, f"{input_folder}/initial/[media]/_dlc")
    cargo_dict: dict[str, dict] = {}

    # contains the packed information (model connected to trailer)
    cargo_path = Path(utils.root_path, f"{input_folder}/initial/[media]/classes/trucks/cargo")
    # contains the ui_name_id, name is the cargo type
    cargo_types_path = Path(utils.root_path, f"{input_folder}/initial/[media]/classes/cargo_types")
    # contains the unpacked information (model not connected to trailer)
    cargo_models_path = Path(utils.root_path, f"{input_folder}/initial/[media]/classes/models")

    for cargo_file_path in dlc_folder.glob(
        "*/classes/trucks/cargo/*.xml", case_sensitive=False
    ):
        cargo_file, cargo_type, packed_mass, packed_length = get_cargo_info(cargo_file_path, use_initial)
        if cargo_type != "None" and cargo_type not in cargo_dict:
            cargo_dict[cargo_type] = {"id":cargo_file_path.stem, "type": cargo_type, "packed_mass": packed_mass, "packed_length": packed_length}

    for cargo_file_path in cargo_path.glob("cargo_*.xml", case_sensitive=False):
        cargo_file, cargo_type, packed_mass, packed_length = get_cargo_info(cargo_file_path, use_initial)
        if cargo_type != "None" and cargo_type not in cargo_dict:
            cargo_dict[cargo_type] = {"id":cargo_file_path.stem, "type": cargo_type, "packed_mass": packed_mass, "packed_length": packed_length}

    for cargo_model_path in dlc_folder.glob(
        "*/classes/models/cargo_*.xml", case_sensitive=False
    ):
        cargo_dict = update_cargos_with_model(cargo_model_path, cargo_dict, use_initial)

    for cargo_model_path in cargo_models_path.glob(
        "*cargo_*.xml", case_sensitive=False
    ):
        cargo_dict = update_cargos_with_model(cargo_model_path, cargo_dict, use_initial)

    for cargo_type_path in dlc_folder.glob(
        "*/classes/cargo_types/Cargo*.xml", case_sensitive=False
    ):
        cargo_dict = update_cargos_with_type(cargo_type_path, cargo_dict, use_initial, ui_dict)

    for cargo_type_path in cargo_types_path.glob("Cargo*.xml", case_sensitive=False):
        cargo_dict = update_cargos_with_type(cargo_type_path, cargo_dict, use_initial, ui_dict)

    return {cargo_name: cargo_data for cargo_name, cargo_data in cargo_dict.items() if "name" in cargo_data}


def process_cargo_data(use_initial_files: bool, ui_dict: dict[str, str], input_folder: str) -> dict:
    data_dict: dict[str, dict] = get_all_cargo_data(ui_dict, use_initial_files, input_folder)
    addition = ""
    if not use_initial_files:
        addition = "_edited"
    with open(f"../reference/info/cargo_data{addition}.json", "w", encoding="utf-8") as f:
        json.dump(data_dict, f, indent=4)
    return data_dict