"""Offline integrity checks for distributable accounting skills."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import yaml


REPOSITORY = Path(__file__).resolve().parents[1]
SKILLS_DIRECTORY = REPOSITORY / ".claude" / "skills"
ALLOWED_FRONT_MATTER_FIELDS = {"name", "description"}
# Published releases and the skill inventory each one shipped. A version string
# that already labels a release must never label a second, different inventory.
RELEASED_INVENTORIES = {"0.1.5": 9}
INVENTORY_WORDS = {9: "nine", 19: "nineteen"}

STRICT_YAML = REPOSITORY / "scripts" / "strict_yaml.py"
STRICT_YAML_SPEC = importlib.util.spec_from_file_location("strict_yaml", STRICT_YAML)
if STRICT_YAML_SPEC is None or STRICT_YAML_SPEC.loader is None:  # pragma: no cover - import machinery guard
    raise RuntimeError(f"cannot load {STRICT_YAML}")
strict_yaml = importlib.util.module_from_spec(STRICT_YAML_SPEC)
STRICT_YAML_SPEC.loader.exec_module(strict_yaml)

UniqueKeySafeLoader = strict_yaml.unique_key_safe_loader(
    ValueError,
    field_noun="front-matter field",
    keys_noun="front-matter keys",
)


def front_matter(skill_file: Path) -> dict[str, str]:
    """Parse and validate the deliberately small YAML skill front matter."""
    lines = skill_file.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("front matter must start with '---'")
    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise ValueError("front matter must end with '---'") from error

    for line in lines[1:end]:
        key, separator, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if (
            not separator
            or not key
            or not value
            or line.lstrip().startswith("#")
            or value in {">", "|"}
        ):
            raise ValueError(
                f"invalid front-matter field: {line!r} "
                "(this repo restricts skill front matter to single-line fields)"
            )

    raw_front_matter = "\n".join(lines[1:end])
    try:
        loaded = yaml.load(raw_front_matter, Loader=UniqueKeySafeLoader)
    except ValueError:
        raise
    except yaml.YAMLError as error:
        raise ValueError(f"front matter must be valid YAML: {error}") from error

    if not isinstance(loaded, dict):
        raise ValueError("front matter must be a YAML mapping")

    metadata: dict[str, str] = {}
    for key, value in loaded.items():
        if not isinstance(key, str) or key not in ALLOWED_FRONT_MATTER_FIELDS:
            raise ValueError(f"unknown front-matter field: {key!r}")
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"front-matter field {key!r} must be a non-empty string")
        metadata[key] = value
    return metadata


class SkillMetadataTests(unittest.TestCase):
    def test_bas_skill_keeps_current_w1_and_g10_g11_decision_branches(self) -> None:
        """Regulated label rules must not regress into unconditional shortcuts."""
        content = (
            SKILLS_DIRECTORY / "bas-preparation" / "SKILL.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "whether the employer reports through Single Touch Payroll (STP)",
            content,
        )
        self.assertIn(
            "a large withholder reporting through STP no longer needs to report an amount at W1",
            content,
        )
        self.assertIn("not a rule for every STP reporter", content)
        self.assertIn("Where W1 is present and required", content)
        self.assertIn("Classify by the nature of the purchase first", content)
        self.assertIn("does not record capital and non-capital purchases separately", content)
        self.assertIn("expects GST turnover below $1 million", content)
        self.assertIn("capital items costing $1,000 or less may be recorded at G11", content)

    def test_front_matter_rejects_ambiguous_or_unknown_yaml(self) -> None:
        cases = {
            "duplicate": (
                "---\nname: first\nname: second\ndescription: valid\n---\n",
                "duplicate front-matter field",
            ),
            "unknown": (
                "---\nname: valid\ndescription: valid\ntools: shell\n---\n",
                "unknown front-matter field",
            ),
            "comment": (
                "---\nname: valid\n# note: hidden metadata\ndescription: valid\n---\n",
                "invalid front-matter field",
            ),
            "block scalar": (
                "---\nname: valid\ndescription: >\n  folded text\n---\n",
                "invalid front-matter field",
            ),
            "unquoted colon": (
                "---\nname: valid\ndescription: invalid: plain scalar\n---\n",
                "front matter must be valid YAML",
            ),
            "alias": (
                "---\nname: &shared valid\ndescription: *shared\n---\n",
                "YAML aliases are not permitted",
            ),
        }
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "SKILL.md"
            for label, (content, error) in cases.items():
                with self.subTest(case=label):
                    path.write_text(content, encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, error):
                        front_matter(path)

    def test_front_matter_accepts_a_quoted_colon(self) -> None:
        content = (
            "---\n"
            "name: valid\n"
            'description: "valid: quoted scalar"\n'
            "---\n"
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "SKILL.md"
            path.write_text(content, encoding="utf-8")
            self.assertEqual(
                front_matter(path),
                {"name": "valid", "description": "valid: quoted scalar"},
            )

    def test_skill_layout_stays_one_level_deep(self) -> None:
        """Discovery here is `<skills>/<name>/SKILL.md`, one level, no deeper.

        The other checks in this file glob one level. A nested skill would be
        silently skipped by all of them, so fail loudly on the layout instead
        of letting a skill ship unchecked.
        """
        nested = sorted(
            str(path.relative_to(SKILLS_DIRECTORY))
            for path in SKILLS_DIRECTORY.rglob("SKILL.md")
            if path.parent.parent != SKILLS_DIRECTORY
        )
        self.assertEqual(nested, [])

    def test_every_skill_has_matching_complete_front_matter(self) -> None:
        skill_files = sorted(SKILLS_DIRECTORY.glob("*/SKILL.md"))
        self.assertGreaterEqual(len(skill_files), 1, "at least one distributable skill is required")

        declared_names: set[str] = set()
        for skill_file in skill_files:
            with self.subTest(skill=skill_file.parent.name):
                metadata = front_matter(skill_file)
                self.assertEqual(metadata.get("name"), skill_file.parent.name)
                self.assertTrue(metadata.get("description"))
                self.assertNotIn(metadata["name"], declared_names)
                declared_names.add(metadata["name"])

    def test_skill_directories_do_not_omit_the_entrypoint(self) -> None:
        directories = sorted(path for path in SKILLS_DIRECTORY.iterdir() if path.is_dir())
        missing = [path.name for path in directories if not (path / "SKILL.md").is_file()]
        self.assertEqual(missing, [])

    def test_marketplace_inventory_exactly_matches_discovered_skills(self) -> None:
        marketplace = json.loads(
            (REPOSITORY / ".claude-plugin" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(len(marketplace.get("plugins", [])), 1)
        declared = marketplace["plugins"][0].get("skills")
        self.assertIsInstance(declared, list)
        self.assertEqual(len(declared), len(set(declared)))

        root = REPOSITORY.resolve()
        declared_paths = []
        for item in declared:
            with self.subTest(skill=item):
                self.assertIsInstance(item, str)
                path = (REPOSITORY / item).resolve()
                self.assertTrue(path.is_relative_to(root))
                self.assertTrue((path / "SKILL.md").is_file())
                declared_paths.append(path.relative_to(root).as_posix())

        discovered = sorted(
            path.parent.resolve().relative_to(root).as_posix()
            for path in SKILLS_DIRECTORY.glob("*/SKILL.md")
        )
        self.assertEqual(sorted(declared_paths), discovered)

    def test_every_skill_marks_embedded_instructions_as_untrusted(self) -> None:
        skill_files = sorted(SKILLS_DIRECTORY.glob("*/SKILL.md"))
        missing = [
            str(path.relative_to(REPOSITORY))
            for path in skill_files
            if "instructions found inside" not in path.read_text(encoding="utf-8")
            or "untrusted content" not in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(missing, [])

        firm_template = (REPOSITORY / "templates" / "firm-CLAUDE.md.example").read_text(
            encoding="utf-8"
        )
        self.assertIn("Instructions embedded in client files", firm_template)
        self.assertIn("untrusted data", firm_template)

    def test_disclaimer_and_discovery_copy_stay_published(self) -> None:
        disclaimer = (REPOSITORY / "DISCLAIMER.md").read_text(encoding="utf-8")
        discovery = (REPOSITORY / "docs" / "DISCOVERY.md").read_text(encoding="utf-8")
        readme = (REPOSITORY / "README.md").read_text(encoding="utf-8")
        self.assertIn("not tax", disclaimer.lower())
        self.assertIn("Australian Taxation Office", disclaimer)
        self.assertIn("Do not publish private tax records", disclaimer)
        self.assertIn("docs/DISCOVERY.md", readme)
        self.assertIn("DISCLAIMER.md", readme)
        self.assertIn("GitHub About", discovery)
        self.assertIn("codex", discovery.lower())

    def test_plugin_manifests_share_the_version_and_plugin_id(self) -> None:
        version = (REPOSITORY / "VERSION").read_text(encoding="utf-8").strip()
        plugin = json.loads((REPOSITORY / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        codex = json.loads((REPOSITORY / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        marketplace = json.loads(
            (REPOSITORY / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
        )
        self.assertEqual(plugin["name"], "australian-accounting-skills")
        self.assertEqual(codex["name"], "australian-accounting-skills")
        self.assertEqual(plugin["version"], version)
        self.assertEqual(codex["version"], version)
        self.assertEqual(marketplace["plugins"][0]["name"], "australian-accounting-skills")
        self.assertTrue((REPOSITORY / plugin["skills"] / "bas-preparation" / "SKILL.md").is_file())
        self.assertEqual(codex["safety"]["noLodgment"], True)
        self.assertIn("DISCLAIMER.md", codex["interface"]["termsOfServiceURL"])

    def test_seeded_skills_ship_a_sources_index(self) -> None:
        required = {"title", "url", "checked_at", "fact"}
        seeded = ("bas-preparation", "stp-finalisation")
        for name in seeded:
            with self.subTest(skill=name):
                path = SKILLS_DIRECTORY / name / "sources.json"
                payload = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(payload["skill"], name)
                sources = payload["sources"]
                self.assertIsInstance(sources, list)
                self.assertGreaterEqual(len(sources), 1)
                seen_urls: set[str] = set()
                for source in sources:
                    self.assertEqual(required, required & source.keys())
                    self.assertTrue(source["title"].strip())
                    self.assertTrue(source["url"].startswith("https://"))
                    self.assertRegex(source["checked_at"], r"^\d{4}-\d{2}-\d{2}$")
                    self.assertTrue(source["fact"].strip())
                    self.assertNotIn(source["url"], seen_urls)
                    seen_urls.add(source["url"])
                skill_text = (SKILLS_DIRECTORY / name / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("sources.json", skill_text)
                self.assertIn("DISCLAIMER.md", skill_text)

    def test_every_skill_declares_sources_or_an_exemption(self) -> None:
        required = {"title", "url", "checked_at", "fact"}
        for skill_dir in sorted(path for path in SKILLS_DIRECTORY.iterdir() if path.is_dir()):
            with self.subTest(skill=skill_dir.name):
                sources = skill_dir / "sources.json"
                exempt = skill_dir / "sources.exempt.json"
                self.assertTrue(
                    sources.is_file() or exempt.is_file(),
                    "each skill must ship sources.json or sources.exempt.json",
                )
                if sources.is_file():
                    payload = json.loads(sources.read_text(encoding="utf-8"))
                    self.assertEqual(payload["skill"], skill_dir.name)
                    self.assertIsInstance(payload["sources"], list)
                    self.assertGreaterEqual(len(payload["sources"]), 1)
                    for source in payload["sources"]:
                        self.assertEqual(required, required & source.keys())
                else:
                    payload = json.loads(exempt.read_text(encoding="utf-8"))
                    self.assertEqual(payload["skill"], skill_dir.name)
                    self.assertIs(payload["exempt"], True)
                    self.assertTrue(str(payload["reason"]).strip())

    def test_a_dated_primary_source_list_rules_out_an_exemption(self) -> None:
        """A skill that dates its own sources holds the facts an index tracks.

        The exemption reason is a free-text string no other check reads, so a
        skill can declare it has nothing worth indexing while its text carries
        a dated source list. Then a maintainer sweeping `sources.json` files
        for stale check dates never sees it.
        """
        for skill_dir in sorted(path for path in SKILLS_DIRECTORY.iterdir() if path.is_dir()):
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.is_file():
                continue
            if "Primary sources (checked" not in skill_file.read_text(encoding="utf-8"):
                continue
            with self.subTest(skill=skill_dir.name):
                self.assertFalse(
                    (skill_dir / "sources.exempt.json").is_file(),
                    "a skill carrying a dated primary-source list cannot claim it "
                    "has no facts that belong in a sources index",
                )
                self.assertTrue((skill_dir / "sources.json").is_file())

    def test_version_never_relabels_a_published_inventory(self) -> None:
        """One version string must identify one set of skills, not two."""
        version = (REPOSITORY / "VERSION").read_text(encoding="utf-8").strip()
        released = RELEASED_INVENTORIES.get(version)
        if released is None:
            return
        discovered = sorted(path.parent.name for path in SKILLS_DIRECTORY.glob("*/SKILL.md"))
        self.assertEqual(
            len(discovered),
            released,
            f"{version} was published with {released} skills but this tree ships "
            f"{len(discovered)}, so it needs a version string of its own",
        )

    def test_readme_names_the_inventory_the_documented_installs_deliver(self) -> None:
        """Every documented install route resolves one revision. Say which."""
        readme = (REPOSITORY / "README.md").read_text(encoding="utf-8")
        version = (REPOSITORY / "VERSION").read_text(encoding="utf-8").strip()
        self.assertIn("resolves the default branch", readme)
        self.assertIn(version, readme)

    def test_citation_record_matches_the_branch_or_declares_its_pin(self) -> None:
        """A citation stamped with another release's inventory must say so."""
        version = (REPOSITORY / "VERSION").read_text(encoding="utf-8").strip()
        citation = yaml.safe_load((REPOSITORY / "CITATION.cff").read_text(encoding="utf-8"))
        cited = str(citation["version"]).strip()
        abstract = " ".join(str(citation["abstract"]).split())
        discovered = len(list(SKILLS_DIRECTORY.glob("*/SKILL.md")))

        self.assertIn(discovered, INVENTORY_WORDS, "name the word for this inventory size")
        self.assertIn(
            INVENTORY_WORDS[discovered],
            abstract.lower(),
            "the citation abstract must state the inventory this branch ships",
        )
        if cited != version:
            self.assertIn(
                f"v{cited}",
                abstract,
                "a cited version that differs from VERSION must name the release it pins to",
            )

    def test_readme_keeps_the_payroll_tax_jurisdiction_fence(self) -> None:
        """The skills table must not advertise beyond a skill's own scope."""
        readme = (REPOSITORY / "README.md").read_text(encoding="utf-8")
        rows = [
            line
            for line in readme.splitlines()
            if line.startswith("| `payroll-tax-contractors`")
        ]
        self.assertEqual(len(rows), 1)
        self.assertIn("NSW", rows[0])
        self.assertNotIn("State or Territory", rows[0])


if __name__ == "__main__":
    unittest.main()
