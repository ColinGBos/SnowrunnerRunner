import json
from pathlib import Path
import xlsxwriter
import polars as pl

from src.data.addon_data import process_addon_data
from src.data.cargo_data import process_cargo_data
from src.data.engine_data import process_engine_data, update_engine_data_with_truck_data
from src.data.gearbox_data import process_gearbox_data, update_gearbox_data_with_truck_data
from src.data.suspension_data import (
    process_suspension_data,
    update_suspension_data_with_truck_data,
)
from src.data.trailer_data import process_trailer_data
from src.data.truck_data import process_truck_data, update_trucks_with_cargo_slots
from src.data.wheel_data import process_wheel_data, update_wheel_data_with_truck_data
from src.lang_handler import LangRegistry


class TruckDataProcessor:
    def __init__(self, use_initial_files: bool = False):
        self.lang_registry = LangRegistry(Path("../input/initial/[strings]/strings_english.str"))
        self.ui_dict: dict[str, str] = self.lang_registry.entries
        self.ui_id_list: list[str] = list(self.ui_dict.keys())
        self.engine_dict: dict = process_engine_data(use_initial_files, self.ui_dict)
        self.gearbox_dict: dict = process_gearbox_data(use_initial_files, self.ui_dict)
        self.wheel_dict: dict = process_wheel_data(use_initial_files, self.ui_dict)
        self.suspension_dict: dict = process_suspension_data(use_initial_files, self.ui_dict)
        self.truck_data: dict = process_truck_data(
            self.engine_dict, self.gearbox_dict, self.wheel_dict,self.suspension_dict, self.ui_dict,use_initial_files
        )
        self.wheel_dict: dict = update_wheel_data_with_truck_data(self.truck_data, self.wheel_dict)
        self.engine_dict: dict = update_engine_data_with_truck_data(self.truck_data, self.engine_dict)
        self.gearbox_dict: dict = update_gearbox_data_with_truck_data(self.truck_data, self.gearbox_dict)
        self.suspension_dict: dict = update_suspension_data_with_truck_data(
            self.truck_data, self.suspension_dict
        )
        self.addon_dict:dict = process_addon_data(use_initial_files, self.truck_data, self.ui_dict)
        self.truck_data = update_trucks_with_cargo_slots(truck_data=self.truck_data, addon_data=self.addon_dict)
        self.trailer_dict:dict = process_trailer_data(use_initial_files, self.ui_dict)
        self.cargo_dict:dict = process_cargo_data(use_initial_files, self.ui_dict)
        self.is_initial_files = use_initial_files

    def get_dicts(self)-> dict[str,dict]:
        return {
            "truck": self.truck_data,
            "engine": self.engine_dict,
            "gearbox": self.gearbox_dict,
            "suspension": self.suspension_dict,
            "wheel": self.wheel_dict,
            "addon": self.addon_dict,
            "trailer": self.trailer_dict,
            "cargo": self.cargo_dict,
        }


def get_english_names() -> dict[str,str]:
    registry = LangRegistry(Path("../input/initial/[strings]/strings_english.str"))
    return registry.entries


def output_data(data_set: TruckDataProcessor, use_initial_files: bool) -> None:
    if use_initial_files:
        name = "../reference/info/data_initial.xlsx"
    else:
        name = "../reference/info/data_edited.xlsx"

    workbook: xlsxwriter.Workbook
    with xlsxwriter.Workbook(name) as workbook:
        for name, data in data_set.get_dicts().items():
            df = pl.DataFrame(list(data.values()))
            df_columns = df.columns
            dict_columns:dict[str, dict] = {}
            with open(f"../reference/info/table_columns/{name}_columns_new.json", "r", encoding="utf-8") as f:
                dict_columns = json.load(f)
            con_formats = {}
            num_formats = {}
            for col, val in dict_columns.items():
                if val["con_format"] != {}:
                    con_formats[col] = val["con_format"]
                if val["num_format"] != {}:
                    num_formats[col] = val["num_format"]

            for column in df_columns:
                if column not in dict_columns:
                    print(f"Warning: {name} does not have column {column} in columns.json.")
            col_names = list(dict_columns.keys())
            print(col_names)
            df = df.select(col_names)
            df.write_excel(workbook=workbook, worksheet=name, autofit=True,table_style="Table Style Medium 6", float_precision=2, conditional_formats=con_formats, column_formats=num_formats)
            if name == "gearbox":
                ws = workbook.get_worksheet_by_name("gearbox")
                if ws is not None:
                    ws.conditional_format(0,col_names.index("g1_f"),df.height+1, col_names.index("g8_f"), {
                        "type": "2_color_scale",
                        "max_color": "#D57575",
                        "min_color": "#ffffff",
                        "min_value": 0.0,
                        "max_value": 3.0,
                    })
                    ws.conditional_format(0,col_names.index("g1_v"),df.height+1, col_names.index("g8_v"), {
                        "type": "2_color_scale",
                        "max_color": "#7EC86F",
                        "min_color": "#ffffff",
                        "min_value": 0.0,
                        "max_value": 20.0,
                    })
            ws = workbook.get_worksheet_by_name(name)
            if ws is not None:
                ws.freeze_panes(1, 1)


def process_all_data(use_initial_files):
    game_data = TruckDataProcessor(use_initial_files)
    output_data(game_data, use_initial_files)


def main():
    process_all_data(use_initial_files=True)
    process_all_data(use_initial_files=False)


if __name__ == "__main__":
    main()
