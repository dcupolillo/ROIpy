""" Created on Mon Aug 14 16:19:42 2023
    @author: dcupolillo """


class Palette:

    def __init__(self) -> None:
        """
        Define color attributes

        Returns
        -------
        None.

        """

        self.black = Color('#181c21')
        self.dark = Color('#1c2128')
        self.d_dark = Color('#22272e')
        self.light = Color('#aab3b9')
        self.green = Color('#347d39')
        self.d_green = Color('#4bb452')
        self.white = Color('#f8fcfb')
        self.blue = Color('#3d82ee')
        self.d_blue = Color('#96d0ff')
        self.red = Color('#d57059')
        self.orange = Color('#f69d50')
        self.hovering = Color('#373e47')
        self.magenta = Color('#c711a4')
        self.pink = Color('#dcbdfb')
        self.disabled = Color('#2a3139')
        self.gray = Color('#e5e5e5')

    def __getattr__(self,
                    name: str):
        return self.__dict__[f"_{name}"]

    def __setattr__(self,
                    name: str,
                    value: str):
        self.__dict__[f"_{name}"] = value

    def __repr__(self):

        color_strings = [None] * len(vars(self).items())

        for n, (attribute, color) in enumerate(vars(self).items()):

            color_hex = color.hex
            rgb = color.rgb
            attribute_name = attribute.lstrip('_')
            color_strings[n] = (f"\033[38;2;{rgb[0]};"
                                f"{rgb[1]};{rgb[2]}m{attribute_name}:"
                                f" {color_hex},{rgb}\033[0m")

        return '\n'.join(color_strings)


class Color:

    def __init__(self,
                 color: str) -> None:
        """
        Color object representation.

        Parameters
        ----------
        color : str
            Hex code for the color

        Returns
        -------
        None

        """

        self.hex = color
        self.rgb = self.hex_to_rgb(color)

    def __repr__(self):

        hex_color_str = (f"\033[38;2;{self.rgb[0]};{self.rgb[1]};"
                         f"{self.rgb[2]}m{self.hex}\033[0m")
        rgb_str = (f"RGB: \033[38;2;{self.rgb[0]};{self.rgb[1]};"
                   f".{self.rgb[2]}m{self.rgb}\033[0m")
        return f"Hex: {hex_color_str}, {rgb_str}"

    def hex_to_rgb(self,
                   color: str) -> tuple:

        value = color.lstrip('#')
        lv = len(value)

        return tuple(int(value[i:i + lv // 3], 16)
                     for i in range(0, lv, lv // 3))


dim = Palette()
