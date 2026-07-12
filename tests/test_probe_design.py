#!/usr/bin/env python3
"""Deterministic checks for the position control and selector shortcut."""

from __future__ import annotations

import unittest

from analysis.run_probes import (
    Family,
    POSITIONS,
    TIERS,
    assemble,
    deterministic_code_extract,
    exact_entity_sentences,
    extract_query_entity,
    filler_sentences,
    query_entity_select,
)


class PositionControlTests(unittest.TestCase):
    def test_competitor_final_index_is_invariant_across_target_positions(self) -> None:
        for tier, _tokens, family_count, _seconds in TIERS:
            for family_index in range(family_count):
                family = Family(family_index)
                filler = filler_sentences(family, tier, "irr", 80)
                needle, competitor = family.clauses("para")
                indices = []
                for depth in POSITIONS.values():
                    document = assemble(
                        filler, needle, competitor, depth, family.distractor_depth
                    )
                    indices.append(document.index(competitor))
                self.assertEqual(len(set(indices)), 1, (tier, family_index, indices))


class ExactEntityDiagnosticTests(unittest.TestCase):
    def setUp(self) -> None:
        self.question = (
            "What is the renewal code required to extend the contract with Meridian?"
        )
        self.answer = "Meridian's master supply agreement carries renewal identifier BC-321."
        self.decoy = (
            "The renewal code required to extend the contract with Halvern is DX-654."
        )

    def test_exact_generated_form_selects_and_extracts_without_model(self) -> None:
        document = [self.decoy, self.answer]
        self.assertEqual(extract_query_entity(self.question), "Meridian")
        self.assertEqual(exact_entity_sentences(document, self.question), [self.answer])
        self.assertEqual(deterministic_code_extract(document, self.question), "BC-321")

    def test_alias_is_rejected(self) -> None:
        question = self.question.replace("Meridian?", "Meridian Holdings?")
        self.assertIsNone(extract_query_entity(question))
        self.assertIsNone(deterministic_code_extract([self.answer], question))

    def test_pronoun_is_rejected(self) -> None:
        question = self.question.replace("Meridian", "it")
        self.assertIsNone(extract_query_entity(question))
        self.assertIsNone(deterministic_code_extract([self.answer], question))

    def test_repeated_entity_is_ambiguous(self) -> None:
        second = "Meridian's archived rider carries registry entry FG-777."
        self.assertIsNone(exact_entity_sentences([self.answer, second], self.question))
        self.assertIsNone(deterministic_code_extract([self.answer, second], self.question))

    def test_ambiguous_sentence_with_two_codes_is_rejected(self) -> None:
        sentence = "Meridian lists renewal identifiers BC-321 and FG-777."
        self.assertIsNone(deterministic_code_extract([sentence], self.question))

    def test_missing_entity_uses_keyword_fallback(self) -> None:
        selected = query_entity_select([self.decoy], self.question)
        self.assertEqual(selected, [self.decoy])
        self.assertIsNone(deterministic_code_extract([self.decoy], self.question))

    def test_unseen_question_form_is_rejected(self) -> None:
        question = "Which identifier renews Meridian's agreement?"
        self.assertIsNone(extract_query_entity(question))
        self.assertIsNone(deterministic_code_extract([self.answer], question))


if __name__ == "__main__":
    unittest.main()
