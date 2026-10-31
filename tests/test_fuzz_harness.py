# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: FSL-1.1-ALv2
"""Replay the fuzz seed corpus so a broken harness fails ordinary CI."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY))

from fuzz import validation_cards  # noqa: E402

CORPUS = REPOSITORY / "fuzz" / "corpus"


class FuzzHarnessTests(unittest.TestCase):
    def test_seed_corpus(self) -> None:
        seeds = sorted(CORPUS.iterdir())
        self.assertGreater(len(seeds), 0)
        for seed in seeds:
            with self.subTest(seed=seed.name):
                validation_cards.test_one_input(seed.read_bytes())

    def test_a_parser_accepting_the_wrong_id_is_caught(self) -> None:
        metadata = {"id": "other", "synthetic": True, "target_skills": ["a"]}
        with mock.patch.object(validation_cards.validator, "parse_front_matter",
                               return_value=(metadata, "")):
            with self.assertRaisesRegex(AssertionError, "accepted id 'other'"):
                validation_cards.test_one_input(b"x")

    def test_unexpected_parser_errors_escape(self) -> None:
        with mock.patch.object(validation_cards.validator, "parse_front_matter",
                               side_effect=RuntimeError("bug")):
            with self.assertRaisesRegex(RuntimeError, "bug"):
                validation_cards.test_one_input(b"x")


if __name__ == "__main__":
    unittest.main()
