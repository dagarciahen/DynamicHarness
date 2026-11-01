"""Verify the general-programming Skill is discovered and routable."""

from __future__ import annotations

from pathlib import Path

from dynamicharness.execution.skills.catalog import SkillCatalog, SkillSource

REPO_ROOT = Path(__file__).resolve().parents[2]


def _catalog():
    return SkillCatalog.discover(
        [SkillSource(path=REPO_ROOT / "skills", scope="project")]
    )


def test_general_programming_skill_is_discovered():
    names = {summary.name for summary in _catalog().summaries()}
    assert "general-programming" in names


def test_general_programming_skill_activates_with_references():
    activation = _catalog().activate("general-programming")
    assert activation.name == "general-programming"
    assert activation.instructions.strip()
    directory = Path(activation.directory)
    assert (directory / "references" / "understanding.md").exists()
    assert (directory / "references" / "testing.md").exists()
    assert (directory / "references" / "verification.md").exists()


def test_general_programming_skill_is_model_agnostic():
    instructions = _catalog().activate("general-programming").instructions
    # The skill must not hard-code a model or provider; routing belongs to the harness.
    assert "never selects a model" in instructions
    assert "config/model_router.yaml" in instructions
