This repo is used to update the emojis data used in Odoo from [CLDR (The Unicode Common Locale Data Repository)](https://github.com/unicode-org/cldr/tree/release-46) following the steps below.

## Steps
1. Open your terminal and run the following commands
```bash
git clone git@github.com:MohammedBasioni/cldr-emojis-updater.git
cd cldr-emojis-updater/
```
2. Copy `{community_path}/addons/web/static/src/core/emoji_picker/emoji_data/global.json` file to the current directory and accept overwriting.
> [!IMPORTANT]
> Skip this step if you don't have this file yet.
```bash
cp -i {community_path}/addons/web/static/src/core/emoji_picker/emoji_data/global.json ./
```
3. Run the script
```bash
python3 script.py
```
4. A directory with the name `emoji_data` will be visiable with the new files from CLDR. Update the files in the directory `{community_path}/addons/web/static/src/core/emoji_picker/emoji_data/` with the new files.

5. Voila!


> [!NOTE] 
> You may want to update `LANGUAGE_MAPPING` in `script.py` if there are new supported languages in Odoo. 
