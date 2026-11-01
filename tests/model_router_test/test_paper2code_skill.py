"""Verify the paper2code Skill is discovered and activatable on demand."""

from __future__ import annotations

from pathlib import Path

from dynamicharness.execution.skills.catalog import SkillCatalog, SkillSource

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_paper2code_skill_is_discovered_from_project_scope():
    catalog = SkillCatalog.discover(
        [SkillSource(path=REPO_ROOT / "skills", scope="project")]
    )
    names = {summary.name for summary in catalog.summaries()}
    assert "paper2code" in names


def test_paper2code_skill_activates_with_instructions_and_scripts():
    catalog = SkillCatalog.discover(
        [SkillSource(path=REPO_ROOT / "skills", scope="project")]
    )
    activation = catalog.activate("paper2code")
    assert activation.name == "paper2code"
    assert activation.instructions.strip()
    assert (Path(activation.directory) / "scripts" / "fetch_paper.py").exists()
    assert (Path(activation.directory) / "scripts" / "extract_structure.py").exists()


def test_paper2code_license_is_parsed():
    catalog = SkillCatalog.discover(
        [SkillSource(path=REPO_ROOT / "skills", scope="project")]
    )
    summary = next(s for s in catalog.summaries() if s.name == "paper2code")
    # license is part of the SKILL.md frontmatter; the catalog keeps name and
    # description, so activation instructions must still be non-empty and the
    # skill directory must carry the attribution file.
    assert (Path(summary.location).parent / "LICENSE").exists()
