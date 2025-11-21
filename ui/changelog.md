# Changelog

## v0.4.1
- converter
    - fix log output if club abbreviation is missing
    - add code of category (RSC) in participants.csv
- misc
    - update officials for season 25/26
    - update to Python 3.13

## v0.4.0
- converter
    - accept more category types: ISU category names or ODF/RSC abbreviations
    - accept custom category levels by specifying alphabetic category name with a maximum of 6 letters
    - couples can participate in multiple categories
    - support for solo dance starting from FSM 1.8.9 ("solo" must be part of the category name)
    - convert couples with unkwown ids (e.g. 888888 or 999999)
    - custom clubs can be added via a custom club csv file (`masterData/csv/club*.csv`)
- UI
    - add PPC converter
    - show log messages for all frames
    - make log messages copyable
    - advanced log options (clear log, show debug messages)
    - add port option for data base connection in result extraction
- misc
    - update clubs and officials for season 24/25
    - crop flags for website to a common width
    - update to Python 3.12
- bugfixes:
    - always use specified file name for result extraction
    - properly update data base drop down menus for result extraction

## v0.3.2
- bugfixes:
    - read clubs from masterData with umlaut
    - nation for official corrected
    - add missing official
    - create output folder if not existing

## v0.3.1
- skip athletes with incomplete name or result
- print location of extracted file
- remove debug messages from log
- bugfixes:
    - fix extracting people from database without ID
    - do not extract LEV data to club column
    - remove team id if incomplete

## v0.3.0
- add UI for extracting competition results from FSM MySQL database
- update masterData for DEU officials and clubs
- ignore rows in Meldeformular if no name is given
- bugfixes:
    - copy flags to correct fsm folder
    - fix nation for M. Derpa

## v0.2.3
- add flags for website
- change default category to advanced novice
- create empty pdf files for detailed judges scores
- generate csv file with all participants
- accept dates from excel as strings dd.mm.yyyy or dd.mm.yy
- bugfixes
    - split categories junior and jugend
    - copy flags to FSM directory
    - strip all data from excel cells
    - export for couples and teams

## v0.2.2
- fix gender for officials in master data ODF file
- add license

## v0.2.1
- add master data ODF file with all DEU officials
- convert officials from input xlsx file
- data from formulas can be read from input xlsx file
- LEV abbreviation can be used as club (e.g. for officials)
- bug fixes

## v0.2.0
- compatible with FSM >= 1.6.8
- all athletes can be added to a category
- incompatible change in ODF format
    - RSC string changed (category level names)
    - category number is included in RSC string
- non-ISU categories are assigned to senior
- basic novice and intermediate novice categories can be added 
    - use category name as heuristic

## v0.1.0
- initial version
