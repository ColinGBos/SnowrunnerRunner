import os
from typing import Literal
from pathlib import Path
import re

from lxml import etree  # ty:ignore[unresolved-import]


def write_to_output(file_path, file_data: str, encoding="utf-8"):
    output_file_path = str(file_path).replace("input", "output", 1)
    directory = os.path.dirname(output_file_path)
    os.makedirs(directory, exist_ok=True)
    with open(Path(output_file_path), "w", encoding=encoding) as file:
        file.write(file_data)


def get_modified_file_if_possible(file_path, use_initial_files) -> str:
    output_file_path = str(file_path).replace("input", "output", 1)
    if not use_initial_files and os.path.exists(output_file_path) and os.path.isfile(output_file_path):
        with open(Path(output_file_path), "r", encoding="utf-8") as file:
            return file.read()
    else:
        with open(file_path, "r") as file:
            return file.read()


def find_regex_in(
    contents: str, search_constant, search_type: Literal["str", "float", "int"]
) -> str | int | float | None:
    mode = r"(\w+)"
    if search_type == "float":
        mode = r"(\d+(?:\.\d+)?)"
    elif search_type == "int":
        mode = r"(\d+)"
    result_list = re.findall(rf'{search_constant}"{mode}"', contents)
    if len(result_list) > 0:
        result = str(result_list[0])
        if search_type == "float":
            result = float(result)
        elif search_type == "int":
            result = int(result)
        return result
    return None


def find_sum_of_regex(
    contents: str, search_constant, search_type: Literal["float", "int"]
) -> int | float | None:
    mode = r"(\d+(?:\.\d+)?)"
    if search_type == "int":
        mode = r"(\d+)"
    result_list = re.findall(rf'{search_constant}"{mode}"', contents)
    if len(result_list) > 0:
        float_list = [float(item) for item in result_list]
        sum_of_floats = sum(float_list)
        if search_type == "int":
            sum_of_floats = int(sum_of_floats)
        return sum_of_floats
    return None


def xml_result(
    contents,
    needs_wrapping,
    param_chain: list[str],
    return_type: Literal["str", "float", "int", "bool"],
) -> str | int | float | bool | None:
    parser = etree.XMLParser(recover=True)
    if needs_wrapping:
        wrapped_xml_data = f"<fake_root>{contents}</fake_root>"
        root = etree.fromstring(wrapped_xml_data, parser=parser)
    else:
        root = etree.fromstring(contents, parser=parser)

    element = root.find(param_chain[0])
    if element is not None:
        for i in range(1, len(param_chain)):
            if element is not None:
                if i == len(param_chain) - 1:
                    value = element.get(param_chain[i])
                    if value is not None:
                        if return_type == "float":
                            return float(value)
                        elif return_type == "int":
                            return int(value)
                        elif return_type == "bool":
                            return value.lower() == "true"
                        return value
                else:
                    element = element.find(param_chain[i])
    return None


def xml_result_list(
    contents,
    needs_wrapping,
    param_chain: list[str],
    return_type: Literal["str", "float", "int"],
) -> list[str | int | float | bool] | None:
    parser = etree.XMLParser(recover=True)
    if needs_wrapping:
        wrapped_xml_data = f"<fake_root>{contents}</fake_root>"
        root = etree.fromstring(wrapped_xml_data, parser=parser)
    else:
        root = etree.fromstring(contents, parser=parser)

    element = root.find(param_chain[0])
    if element is not None:
        for i in range(1, len(param_chain) - 1):
            if element is not None:
                if i == len(param_chain) - 2:
                    elements = element.findall(param_chain[i])
                    if elements is not None:
                        values = []
                        for final_e in elements:
                            if return_type == "float":
                                value = float(final_e.get(param_chain[-1]))
                            elif return_type == "int":
                                value = int(final_e.get(param_chain[-1]))
                            else:
                                value = str(final_e.get(param_chain[-1]))
                            if value not in values:
                                values.append(value)
                        return values
                else:
                    element = element.find(param_chain[i])
    return None


def xml_result_count(
    contents,
    needs_wrapping,
    param_chain: list[str]
) -> int | None:
    parser = etree.XMLParser(recover=True)
    if needs_wrapping:
        wrapped_xml_data = f"<fake_root>{contents}</fake_root>"
        root = etree.fromstring(wrapped_xml_data, parser=parser)
    else:
        root = etree.fromstring(contents, parser=parser)

    element = root.find(param_chain[0])
    if element is not None:
        for i in range(1, len(param_chain)):
            if element is not None:
                if i == len(param_chain) - 1:
                    return len(element.findall(param_chain[i]))
                else:
                    element = element.find(param_chain[i])
    return None