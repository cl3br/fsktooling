import unittest

import scripts.copy_participant_files_to_category_folders as cp


class TestCopyParticipantFiles(unittest.TestCase):
    def setUp(self):
        # nothing special needed here; each test sets the file list
        pass

    def test_single_skater_multiple_separators(self):
        # prepare a few variants of the same skater name
        input_file_names_with_ext = [
            "Annabell_STEIN_SP.mp3",
            "STEIN-ANNABELL--_ SP.mp3",
            "Annabell Stein.mp3"
        ]
        participant = {
            "Kategorie-Typ": "S",
            "Segment-Typ": "S",
            "Segment-Abk.": "SP",
            "Vorname": "Annabell",
            "Name": "STEIN",
            "Geburtstag": "2000-01-01",
            "Nation": "XX",
            "Club-Abk.": "YY",
        }
        # with segment filtering only the short‑program file ought to be returned
        res = cp.find_file_name_for_participant(
            participant,
            input_file_names_with_ext,
            find_segment_type=True,
            force_segment_type="",
        )
        self.assertEqual(set(res), {"Annabell_STEIN_SP.mp3", "STEIN-ANNABELL--_ SP.mp3"})

        # if we ignore segments the routine will see all three as matching and report
        # an ambiguous result (order is unspecified)
        res_no_seg = cp.find_file_name_for_participant(
            participant,
            input_file_names_with_ext,
            find_segment_type=False,
            force_segment_type="",
        )
        self.assertEqual(set(res_no_seg), set(input_file_names_with_ext))

    def test_missing_due_to_name_or_segment(self):
        # wrong name and missing segment should both yield no match
        input_file_names_with_ext = ["WrongName_SP.mp3", "Annabell_STEIN.mp3"]
        participant = {
            "Kategorie-Typ": "S",
            "Segment-Typ": "S",
            "Segment-Abk.": "SP",
            "Vorname": "Annabell",
            "Name": "STEIN",
            "Geburtstag": "2000-01-01",
            "Nation": "XX",
            "Club-Abk.": "YY",
        }
        res = cp.find_file_name_for_participant(
            participant,
            input_file_names_with_ext,
            find_segment_type=True,
            force_segment_type="",
        )
        self.assertEqual(res, [])

    def test_couple_full_and_lastname(self):
        # two candidate files, one contains both given+family names, the other just the
        # two family names with a different segment.
        input_file_names_with_ext = [
            "JohnSmithJaneDoe_SP.mp3",
            "SmithDoe_FS.mp3",
        ]
        participant_full = {
            "Kategorie-Typ": "P",
            "Segment-Typ": "S",
            "Segment-Abk.": "SP",
            "Vorname": "John",
            "Name": "Smith",
            "Vorname-Partner": "Jane",
            "Name-Partner": "Doe",
            "Team-Name": "",
            "Nation": "XX",
            "Club-Abk.": "YY",
        }
        res_full = cp.find_file_name_for_participant(
            participant_full,
            input_file_names_with_ext,
            find_segment_type=True,
            force_segment_type="",
        )
        self.assertEqual(res_full, ["JohnSmithJaneDoe_SP.mp3"])

        # ignoring segments returns both names
        res_no_seg = cp.find_file_name_for_participant(
            participant_full,
            input_file_names_with_ext,
            find_segment_type=False,
            force_segment_type="",
        )
        self.assertEqual(set(res_no_seg), set(input_file_names_with_ext))

        # now a file with only family names, free‑skating segment
        participant_full["Segment-Typ"] = "F"
        participant_full["Segment-Abk."] = "FS"
        res_last_only = cp.find_file_name_for_participant(
            participant_full,
            input_file_names_with_ext,
            find_segment_type=True,
            force_segment_type="",
        )
        self.assertEqual(res_last_only, ["SmithDoe_FS.mp3"])

    def test_couple_negative_single_partner(self):
        input_file_names_with_ext = ["JohnSmith_SP.mp3"]
        participant = {
            "Kategorie-Typ": "P",
            "Segment-Typ": "S",
            "Segment-Abk.": "SP",
            "Vorname": "John",
            "Name": "Smith",
            "Vorname-Partner": "Jane",
            "Name-Partner": "Doe",
            "Team-Name": "",
            "Nation": "XX",
            "Club-Abk.": "YY",
        }
        res = cp.find_file_name_for_participant(
            participant,
            input_file_names_with_ext,
            find_segment_type=True,
            force_segment_type="",
        )
        self.assertEqual(res, [])

        input_file_names_with_ext = ["JaneDoe_SP.mp3"]
        res2 = cp.find_file_name_for_participant(
            participant,
            input_file_names_with_ext,
            find_segment_type=True,
            force_segment_type="",
        )
        self.assertEqual(res2, [])

    def test_team_name_matching(self):
        # team category should match on team name only
        input_file_names_with_ext = [
            "Synchronized_Skating_Team_SP.mp3",
            "AnotherTeam_FS.mp3",
        ]
        participant = {
            "Kategorie-Typ": "T",
            "Segment-Typ": "S",
            "Segment-Abk.": "SP",
            "Vorname": "",
            "Name": "",
            "Vorname-Partner": "",
            "Name-Partner": "",
            "Team-Name": "Synchronized Skating Team",
            "Nation": "XX",
            "Club-Abk.": "YY",
        }
        res = cp.find_file_name_for_participant(
            participant,
            input_file_names_with_ext,
            find_segment_type=True,
            force_segment_type="",
        )
        self.assertEqual(res, ["Synchronized_Skating_Team_SP.mp3"])

    def test_team_name_ambiguous_segments(self):
        # team with multiple segment files
        input_file_names_with_ext = [
            "MyTeam_SP.mp3",
            "MyTeam_FS.mp3",
        ]
        participant = {
            "Kategorie-Typ": "T",
            "Segment-Typ": "S",
            "Segment-Abk.": "SP",
            "Vorname": "",
            "Name": "",
            "Vorname-Partner": "",
            "Name-Partner": "",
            "Team-Name": "MyTeam",
            "Nation": "XX",
            "Club-Abk.": "YY",
        }
        res = cp.find_file_name_for_participant(
            participant,
            input_file_names_with_ext,
            find_segment_type=True,
            force_segment_type="",
        )
        self.assertEqual(res, ["MyTeam_SP.mp3"])

    def test_team_name_no_segment_filter(self):
        # without segment filtering, all team files match
        input_file_names_with_ext = [
            "MyTeam_SP.mp3",
            "MyTeam_FS.mp3",
        ]
        participant = {
            "Kategorie-Typ": "T",
            "Segment-Typ": "S",
            "Segment-Abk.": "SP",
            "Vorname": "",
            "Name": "",
            "Vorname-Partner": "",
            "Name-Partner": "",
            "Team-Name": "MyTeam",
            "Nation": "XX",
            "Club-Abk.": "YY",
        }
        res = cp.find_file_name_for_participant(
            participant,
            input_file_names_with_ext,
            find_segment_type=False,
            force_segment_type="",
        )
        self.assertEqual(set(res), set(input_file_names_with_ext))

    def test_team_name_missing(self):
        # team name not found should yield no match
        input_file_names_with_ext = [
            "WrongTeam_SP.mp3",
            "AnotherTeam_FS.mp3",
        ]
        participant = {
            "Kategorie-Typ": "T",
            "Segment-Typ": "S",
            "Segment-Abk.": "SP",
            "Vorname": "",
            "Name": "",
            "Vorname-Partner": "",
            "Name-Partner": "",
            "Team-Name": "MyTeam",
            "Nation": "XX",
            "Club-Abk.": "YY",
        }
        res = cp.find_file_name_for_participant(
            participant,
            input_file_names_with_ext,
            find_segment_type=True,
            force_segment_type="",
        )
        self.assertEqual(res, [])

if __name__ == "__main__":
    unittest.main()