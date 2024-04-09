import unicodedata


# remove spaces, dashes, dots, commas and underscores in strings to make them comparable
def normalize_string(s: str):
    translation_table = str.maketrans("", "", " -_.,")

    # normalize unicode characters, remove characters, lowercase, ä -> ae, ö -> oe, ü -> ue
    return (
        unicodedata.normalize("NFC", unicodedata.normalize("NFD", s))
        .translate(translation_table)
        .casefold()
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
    )
