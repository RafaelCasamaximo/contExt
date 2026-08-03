from __future__ import annotations

import json
import re
import string
import unittest
from pathlib import Path


TRANSLATIONS_PATH = (
    Path(__file__).resolve().parents[1] / "src" / "context" / "ui" / "translations.json"
)


def flatten(values: dict, prefix: str = "") -> dict[str, str]:
    result = {}
    for key, value in values.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            result.update(flatten(value, full_key))
        else:
            result[full_key] = value
    return result


class TranslationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        translations = json.loads(TRANSLATIONS_PATH.read_text(encoding="utf-8"))
        cls.portuguese = flatten(translations["pt-BR"])
        cls.english = flatten(translations["en"])

    def test_locales_have_the_same_keys(self) -> None:
        self.assertEqual(set(self.portuguese), set(self.english))

    def test_format_placeholders_are_preserved_between_locales(self) -> None:
        formatter = string.Formatter()
        for key in self.portuguese:
            portuguese_fields = {
                field for _, field, _, _ in formatter.parse(self.portuguese[key]) if field
            }
            english_fields = {
                field for _, field, _, _ in formatter.parse(self.english[key]) if field
            }
            self.assertEqual(portuguese_fields, english_fields, key)

    def test_common_unaccented_portuguese_misspellings_are_absent(self) -> None:
        misspellings = {
            "alteracoes",
            "aproximacao",
            "area",
            "configuracoes",
            "diferenca",
            "dimensoes",
            "diretorio",
            "dominio",
            "espacamento",
            "exportacao",
            "extracao",
            "frequencia",
            "geracao",
            "indices",
            "interpolacao",
            "invalido",
            "limiarizacao",
            "mascara",
            "metodo",
            "nao",
            "numero",
            "possivel",
            "regiao",
            "resolucao",
            "simulacao",
            "solucao",
            "visualizacao",
            "voce",
        }
        for key, value in self.portuguese.items():
            words = set(re.findall(r"[A-Za-zÀ-ÿ]+", value.lower()))
            self.assertFalse(words & misspellings, key)


if __name__ == "__main__":
    unittest.main()
