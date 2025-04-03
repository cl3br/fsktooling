Tooling for figure skating events.

# Overview
Most tooling is based on the "DEU Meldeformular". Conversion is done from xlsx to csv.
The 3 main parts of the form will be exported to separate csv files:
- info header
- categories
- people (athletes and officials)

After extracting the information into csv files, they could be merged and further processed to retreive the actual discipline participants.

# Features / Scripts
1. Convert from "DEUMeldeformular" to
    - participant csv files
    - ODF xml files that can be read by the judging system FS manager (GUI available)
    - empty PDF files for all detailed segment results
2. Get participant starting order from a FS manager SQL database
3. Copy participant files from plain folder structure to category / segment folder structure and sort with starting order
4. Merge PDF files
5. Create mp3 playlists
6. Convert DEU clubs and nations to XML

# Development
## Requirements

1. Install [python](https://www.python.org/downloads/)
    - python >= 3.4

2. Install addinional python packages

    ```pip install -r requirements.txt```

    or
 
    ```install_requirements.bat```

## Getting started
1. Register fsklib as a local editable python package. E.g. on windows:

    ```ínstall_editable_fsklib.bat```

2. Run scripts:

    ```python scripts/xxx.py```

## Deploy GUI
On Windows run:

```cd ui && package.bat```

## Contribution
- Create new branch from `master` branch
- Do your changes
- Open PR against `master`
- Squash merge with PR title following [conventional commits](https://www.conventionalcommits.org/)
