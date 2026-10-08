# Copyright (©) 2026, Vladimir Baykov. All rights reserved.
# Color palettes for light and dark themes used by GUI windows

LIGHT = {
    "bg": "#F0F0F0",
    "btn": "#E0E0E0",
    "btn_hover": "#F5D060",
    "main_bg": "#F5C542",
    "main_fg": "#000000",
    "fg": "#000000",
    "pause_fg": "#CC2020",
    "highlight_fg": "#CC6600",
    "entry_bg": "#FFFFFF",
    "entry_fg": "#000000",
    "tree_bg": "#FFFFFF",
    "tree_fg": "#000000",
    "select_bg": "#3399FF",
    "select_fg": "#FFFFFF",
    "field_bg": "#E8E8E8",
    "trough": "#D0D0D0",
}

DARK = {
    "bg": "#303030",
    "btn": "#505050",
    "btn_hover": "#F5D060",
    "main_bg": "#F5C542",
    "main_fg": "#000000",
    "fg": "#FFFFFF",
    "pause_fg": "#FF2020",
    "highlight_fg": "#FF8000",
    "entry_bg": "#404040",
    "entry_fg": "#FFFFFF",
    "tree_bg": "#404040",
    "tree_fg": "#FFFFFF",
    "select_bg": "#5A5A5A",
    "select_fg": "#FFFFFF",
    "field_bg": "#383838",
    "trough": "#202020",
}


# Return the palette dict for the given theme flag
def get_palette(dark: bool) -> dict:
    return DARK if dark else LIGHT