import utils
from src.utils import get_modified_file_if_possible, write_to_output
import json
import re
from pathlib import Path

from data_process import TruckDataProcessor
from src.models import Cargo


def get_cargo_info(cargo_path, use_initial) -> Cargo | None:
    # print(f"Processing cargo file: {cargo_path}")
    content = get_modified_file_if_possible(cargo_path, use_initial)

    mass_list = re.findall(r'Mass="(\d+)"', content)
    if len(mass_list) > 0:
        packed_mass = sum(map(int, mass_list))
        packed_length = int(re.findall(r'CargoLength="(\d+)"', content)[0])
        cargo_type = re.findall(r'CargoType="(\w+)"', content)[0]
        return Cargo(
            "",
            "",
            cargo_type,
            packed_mass,
            packed_length,
            0,
            str(cargo_path).replace("\\", "/"),
            "",
            0,
            len(mass_list),
        )
    return None


def update_cargos_with_model(cargo_model_path, cargo_list, use_initial) -> list[Cargo]:
    # print(f"Processing cargo model file: {cargo_model_path}")
    content = get_modified_file_if_possible(cargo_model_path, use_initial)
    mass_list = re.findall(r'Mass="(\d+(?:\.\d+)?)"', content)
    if len(mass_list) > 0:
        unpacked_mass = int(sum(map(float, mass_list)))
        cargo_type_list = re.findall(r'LoadType="(\w+)"', content)
        if len(cargo_type_list) > 0:
            cargo_type = cargo_type_list[0]
            if "log" not in cargo_type.lower():
                for cargo in cargo_list:
                    if cargo.cargo_type == cargo_type:
                        cargo.unpacked_mass = unpacked_mass
                        cargo.unpacked_model_file = str(cargo_model_path).replace(
                            "\\", "/"
                        )
                        cargo.unpacked_mass_count = len(mass_list)
    return cargo_list


def update_cargos_with_type(cargo_type_path: Path, cargo_list, use_initial) -> list[Cargo]:
    content = get_modified_file_if_possible(cargo_type_path, use_initial)
    cargo_type = cargo_type_path.stem
    ui_name_list = re.findall(r'UiName="(\w+)"', content)
    if len(ui_name_list) > 0 and ui_name_list[0] != "":
        for cargo in cargo_list:
            if cargo.cargo_type == cargo_type:
                cargo.ui_name = ui_name_list[0]

    return cargo_list


def update_cargo_unpacked_mass(unpacked_model_file, packed_mass, unpacked_mass) -> int:
    final_mass = min(7000.0, max(unpacked_mass, packed_mass))
    content = get_modified_file_if_possible(unpacked_model_file, False)

    mass_list = re.findall(r'Mass="(\d+(?:\.\d+)?)"', content)
    masses = [float(mass) for mass in mass_list]
    current_mass = int(sum(masses))
    max_mass_index = masses.index(max(masses))
    print(
        f"Increase unpacked mass for: {unpacked_model_file} | {current_mass} -> {final_mass}"
    )
    mass_to_add = final_mass - current_mass

    # Use regex to find Mass="number" and replace with buffed value
    modified_content = content.replace(
        f'Mass="{mass_list[max_mass_index]}"',
        f'Mass="{masses[max_mass_index] + mass_to_add}"',
    )

    write_to_output(unpacked_model_file, modified_content)
    return int(final_mass)


def dump_cargo_info(cargo_list: list[Cargo]):
    cargo_to_dump = [
        {
            "cargo_type": cargo.cargo_type,
            "ui_name": cargo.ui_name,
            "name": cargo.name,
            "packed_mass": cargo.packed_mass,
            "packed_length": cargo.packed_length,
            "unpacked_mass": cargo.unpacked_mass,
            "packed_cargo_file": cargo.packed_cargo_file,
            "unpacked_model_file": cargo.unpacked_model_file,
            "unpacked_mass_count": cargo.unpacked_mass_count,
            "packed_mass_count": cargo.packed_mass_count,
            "approx_text_width": cargo.approx_text_width,
        }
        for cargo in cargo_list
    ]

    with open("reference/info/cargo_info.json", "w") as f:
        json.dump(cargo_to_dump, f, indent=4)

    manual_cargo = [
        {
            "cargo_type": cargo.cargo_type,
            "ui_name": cargo.ui_name,
            "name": cargo.name,
            "packed_mass": cargo.packed_mass,
            "packed_length": cargo.packed_length,
            "unpacked_mass": cargo.unpacked_mass,
            "packed_cargo_file": cargo.packed_cargo_file,
            "unpacked_model_file": cargo.unpacked_model_file,
            "unpacked_mass_count": cargo.unpacked_mass_count,
            "packed_mass_count": cargo.packed_mass_count,
            "approx_text_width": cargo.approx_text_width,
        }
        for cargo in cargo_list
        if cargo.unpacked_mass_count > 1
    ]
    with open("reference/info/cargo_to_manually_adjust.json", "w") as f:
        json.dump(manual_cargo, f, indent=4)

    names = {cargo.name: cargo.name for cargo in cargo_list}
    with open("reference/info/cargo_names.json", "w") as f:
        json.dump(names, f, indent=4)


def append_cargo(cargo_list: list[Cargo], cargo: None | Cargo) -> list[Cargo]:
    if cargo is not None:
        for cargo_test in cargo_list:
            if cargo_test.cargo_type == cargo.cargo_type:
                cargo_test.packed_mass = max(cargo_test.packed_mass, cargo.packed_mass)
                return cargo_list
        cargo_list.append(cargo)

    return cargo_list


def cargo_mass_information(requires_change=True, use_initial=False) -> list[Cargo]:

    dlc_folder = Path(utils.root_path,"input/initial/[media]/_dlc")
    cargo_list: list[Cargo] = []

    # contains the packed information (model connected to trailer)
    cargo_path = Path(utils.root_path,"input/initial/[media]/classes/trucks/cargo")
    # contains the ui_name_id, name is the cargo type
    cargo_types_path = Path(utils.root_path,"input/initial/[media]/classes/cargo_types")
    # contains the unpacked information (model not connected to trailer)
    cargo_models_path = Path(utils.root_path,"input/initial/[media]/classes/models")

    for cargo_file_path in dlc_folder.glob(
        "*/classes/trucks/cargo/*.xml", case_sensitive=False
    ):
        cargo = get_cargo_info(cargo_file_path, use_initial)
        cargo_list = append_cargo(cargo_list, cargo)

    for cargo_file_path in cargo_path.glob("cargo_*.xml", case_sensitive=False):
        cargo = get_cargo_info(cargo_file_path, use_initial)
        cargo_list = append_cargo(cargo_list, cargo)

    for cargo_model_path in dlc_folder.glob(
        "*/classes/models/cargo_*.xml", case_sensitive=False
    ):
        cargo_list = update_cargos_with_model(cargo_model_path, cargo_list, use_initial)

    for cargo_model_path in cargo_models_path.glob(
        "*cargo_*.xml", case_sensitive=False
    ):
        cargo_list = update_cargos_with_model(cargo_model_path, cargo_list, use_initial)

    for cargo_type_path in dlc_folder.glob(
        "*/classes/cargo_types/Cargo*.xml", case_sensitive=False
    ):
        cargo_list = update_cargos_with_type(cargo_type_path, cargo_list, use_initial)

    for cargo_type_path in cargo_types_path.glob("Cargo*.xml", case_sensitive=False):
        cargo_list = update_cargos_with_type(cargo_type_path, cargo_list, use_initial)

    if requires_change:
        for cargo in cargo_list:
            if (
                cargo.packed_mass > cargo.unpacked_mass
                and cargo.unpacked_model_file != ""
            ):
                cargo.unpacked_mass = update_cargo_unpacked_mass(
                    Path(cargo.unpacked_model_file),
                    cargo.packed_mass,
                    cargo.unpacked_mass,
                )

    return cargo_list


def update_cargo_names(
    cargo_list: list[Cargo], game_data: TruckDataProcessor
) -> list[Cargo]:
    for ui_ids in game_data.ui_id_list:
        for cargo in cargo_list:
            if cargo.ui_name != "" and cargo.ui_name in ui_ids and "DESC" not in ui_ids:
                unpacked_mass = float(max(cargo.unpacked_mass, 1000) / 1000.0)
                packed_mass = float(max(cargo.packed_mass, 1000) / 1000.0)
                net_mass = round(max(unpacked_mass, packed_mass), 1)
                if "_LOGS_" not in cargo.ui_name:
                    value = f" {net_mass}t|{cargo.packed_length}s"
                else:
                    value = f" {net_mass}t"
                game_data.lang_registry.add_entry(cargo.ui_name, value)
                break

    return cargo_list