import json



def main():
    file_types = ["addon", "truck", "engine", "wheel", "gearbox", "trailer"]
    for f_type in file_types:
        with open(f"reference/info/table_columns/{f_type}_columns_new.json", "r") as file:
            new_col_dict = {}
            col_dict = json.load(file)
            for col, entry in col_dict.items():
                if "min_color" in entry["con_format"]:
                    entry["con_format"]["min_color"] = "#7EC86F"
                    entry["con_format"]["max_color"] = "#D57575"
                    entry["con_format"]["mid_color"] = "#ffffff"
                    entry["con_format"]["type"] = "3_color_scale"


                new_col_dict[col] = {"name":entry["name"], "num_format":entry["num_format"], "con_format":entry["con_format"]}

            with open(f"reference/info/table_columns/{f_type}_columns_new.json", "w") as f:
                json.dump(new_col_dict, f, indent=4)




if __name__ == "__main__":
    main()