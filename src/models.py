class Cargo:
    ui_name_id: str
    ui_name: str
    name: str
    cargo_type: str
    packed_mass: int
    packed_length: int
    unpacked_mass: int
    packed_cargo_file: str
    unpacked_model_file: str
    unpacked_mass_count: int
    packed_mass_count: int
    approx_text_width: int

    def __init__(
        self,
        ui_name_id: str,
        ui_name: str,
        cargo_type: str,
        packed_mass: int,
        packed_length: int,
        unpacked_mass: int,
        packed_cargo_file: str,
        unpacked_model_file: str,
        unpacked_mass_count: int,
        packed_mass_count: int,
        approx_text_width: int = 0,
        name: str = "",
    ):
        self.ui_name_id = ui_name_id
        self.ui_name = ui_name
        self.cargo_type = cargo_type
        self.packed_mass = packed_mass
        self.packed_length = packed_length
        self.unpacked_mass = unpacked_mass
        self.packed_cargo_file = packed_cargo_file
        self.unpacked_model_file = unpacked_model_file
        self.unpacked_mass_count = unpacked_mass_count
        self.packed_mass_count = packed_mass_count
        self.approx_text_width = approx_text_width
        self.name = name


class Adjustment:
    path: str
    from_str: str
    to_str: str
    enable: bool

    def __init__(self, path: str, from_str: str, to_str: str, enable: bool = True):
        self.path = path
        self.from_str = from_str
        self.to_str = to_str