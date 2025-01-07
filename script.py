import os
import re
import json
import logging
import requests
import shutil
import xml.etree.ElementTree as ET

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
CLDR_REPO_URL = "https://github.com/unicode-org/cldr/archive/refs/tags/release-46.zip"
DATA_FOLDER = "emoji_data"
CLDR_VERSION_FILE = "cldr_version.txt"
GLOBAL_JSON_FILE = "global.json"
LANGUAGE_MAPPING = {
    "am": "am.json",
    "uk": "uk.json",
    "lv": "lv.json",
    "sr_Cyrl": "sr@Cyrl.json",
    "sr_Latn": "sr@latin.json",
    "gu": "gu.json",
    "cs": "cs.json",
    "mk": "mk.json",
    "fa": "fa.json",
    "fi": "fi.json",
    "bs": "bs.json",
    "ru": "ru.json",
    "bn": "bn.json",
    "da": "da.json",
    "sv": "sv.json",
    "pt_PT": "pt_PT.json",
    "zh_Hant": "zh_TW.json",
    "nl": "nl.json",
    "et": "et.json",
    "tr": "tr.json",
    "ar": "ar.json",
    "ml": "ml.json",
    "en_AU": "en_AU.json",
    "ms": "ms.json",
    "it": "it.json",
    "el": "el.json",
    "sw": "sw.json",
    "kab": "kab.json",
    "hu": "hu.json",
    "gl": "gl.json",
    "km": "km.json",
    "en_IN": "en_IN.json",
    "hr": "hr.json",
    "vi": "vi.json",
    "my": "my.json",
    "pt": "pt.json",
    "fr": "fr.json",
    "pl": "pl.json",
    "ko": "ko.json",
    "he": "he.json",
    "th": "th.json",
    "te": "te.json",
    "de_CH": "de_CH.json",
    "ca_ES": "ca_ES.json",
    "es": "es.json",
    "eu": "eu.json",
    "hi": "hi.json",
    "lb": "lb.json",
    "lt": "lt.json",
    "az": "az.json",
    "lo": "lo.json",
    "id": "id.json",
    "en_GB": "en_GB.json",
    "en_CA": "en_CA.json",
    "ka": "ka.json",
    "zh_Hant_HK": "zh_HK.json",
    "sl": "sl.json",
    "ja": "ja.json",
    "ro": "ro.json",
    "bg": "bg.json",
    "mn": "mn.json",
    "de": "de.json",
    "ca": "ca.json",
    "be": "be.json",
    "fr_CA": "fr_CA.json",
    "sk": "sk.json",
    "es_419": "es_419.json",
    "en": "en.json",
    "es_MX": "es_MX.json",
    "zh": "zh.json",
    "sq": "sq.json",
}


# Utility Functions
def generate_shortcode(name):
    """Generate shortcode: replace spaces and symbols with underscores and add colons"""
    if not name:
        return ""
    shortcode = re.sub(r"[\W]+", "_", name.lower()).strip("_")
    return f":{shortcode}:"


def download_cldr(destination):
    """Download the latest CLDR release."""
    logging.info("Downloading CLDR data...")
    response = requests.get(CLDR_REPO_URL, stream=True)
    with open(destination, "wb") as file:
        shutil.copyfileobj(response.raw, file)
    logging.info("Download complete.")


def extract_cldr(zip_path, extract_to):
    """Extract CLDR zip file."""
    logging.info("Extracting CLDR data...")
    shutil.unpack_archive(zip_path, extract_to)
    nested_folder = next((f for f in os.listdir(extract_to) if os.path.isdir(os.path.join(extract_to, f))), None)
    if nested_folder:
        extract_to = os.path.join(extract_to, nested_folder)
    logging.info("Extraction complete.")
    return extract_to


def parse_labels_file(labels_path):
    """Parse labels.txt to map emojis to categories."""
    emoji_categories = {}
    with open(labels_path, encoding="utf-8") as file:
        for line in file:
            if line.startswith("["):
                range_part, category, _ = re.split(r"\s*;\s*", line.strip())
                emojis = []
                if "," in range_part or "-" in range_part:
                    emojis = re.findall(r"\\u[0-9a-fA-F]+", range_part)
                else:
                    emojis = [range_part.strip("[]")]
                for emoji in emojis:
                    emoji_categories[emoji] = category
    return emoji_categories


def parse_annotations(language, input_folder, emoji_categories):
    """Parse annotations for a given language."""
    annotations_file = os.path.join(input_folder, f"annotations/{language}.xml")
    derived_file = os.path.join(input_folder, f"annotationsDerived/{language}.xml")
    emoji_data = {}

    def parse_file(file_path):
        if os.path.exists(file_path):
            tree = ET.parse(file_path)
            root = tree.getroot()
            for elem in root.findall(".//"):
                cp = elem.get("cp")
                if cp:
                    if elem.get("type") == "tts":
                        name = elem.text.strip() if elem.text else ""
                        emoji_data[cp] = {"name": name, "keywords": [], "category": emoji_categories.get(cp, "Unknown")}
                    elif elem.tag == "annotation" and elem.text:
                        keywords = elem.text.split("|")
                        if cp in emoji_data:
                            emoji_data[cp]["keywords"] = [k.strip() for k in keywords]

    parse_file(annotations_file)
    parse_file(derived_file)
    return emoji_data


def update_global_json(output_folder, emoji_data, emoji_categories, previous_global_path):
    """Update global.json with shared metadata and merge emoticons from the previous version."""
    global_file = os.path.join(output_folder, "global.json")
    global_data = {}
    previous_emoticons = {}
    if os.path.exists(previous_global_path):
        with open(previous_global_path, "r", encoding="utf-8") as file:
            previous_data = json.load(file)
            previous_emoticons = {
                cp: entry["emoticons"] for cp, entry in previous_data.items() if entry.get("emoticons")
            }
    for cp, data in emoji_data.items():
        global_data[cp] = {
            "category": emoji_categories.get(cp, "Unknown"),
            "shortcodes": [generate_shortcode(data["name"])] if data["name"] else [],
            "emoticons": previous_emoticons.get(cp, []),
        }
    with open(global_file, "w", encoding="utf-8") as file:
        json.dump(global_data, file, ensure_ascii=False, indent=4)
    logging.info(f"Updated {global_file}")


def update_language_json(language, emoji_data, output_folder):
    """Update language-specific JSON file."""
    output_file = os.path.join(output_folder, LANGUAGE_MAPPING.get(language, f"{language}.json"))
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(emoji_data, file, ensure_ascii=False, indent=4)
    logging.info(f"Updated {output_file}")


def main():
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
    cldr_zip = "cldr.zip"
    cldr_folder = "cldr-release"
    download_cldr(cldr_zip)
    extracted_path = extract_cldr(cldr_zip, cldr_folder)
    labels_path = os.path.join(extracted_path, "common/properties/labels.txt")
    extracted_path = os.path.join(extracted_path, "common")
    emoji_categories = parse_labels_file(labels_path)
    for lang in LANGUAGE_MAPPING.keys():
        logging.info(f"Processing language: {lang}")
        emoji_data = parse_annotations(lang, extracted_path, emoji_categories)
        update_language_json(lang, emoji_data, DATA_FOLDER)
    previous_global_path = GLOBAL_JSON_FILE
    update_global_json(DATA_FOLDER, emoji_data, emoji_categories, previous_global_path)
    os.remove(cldr_zip)
    shutil.rmtree(cldr_folder)


if __name__ == "__main__":
    main()
