# Changelog

## v0.3.3
- update clubs and officials for season 24/25
- crop flags for website to a common width
- convert couples with unkwown ids
- make log messages copyable
- update to Python 3.12
- bugfixes:
    - always use specified file name for result extraction

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
