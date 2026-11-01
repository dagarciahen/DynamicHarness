"""Platform tool metadata; imports no executable tools."""

from dynamicharness.tools.catalog_types import ToolSpec, _spec


def tool_specs() -> tuple[ToolSpec, ...]:
    return (
        _spec(
            "loom_retrieve_context",
            "dynamicharness.tools.context.retrieve_context",
            "context",
            "Retrieve original content behind a ContextRef.",
            "context",
            fixed_arg_names=("ref", "query", "offset", "limit"),
            is_read_only=True,
            max_result_chars=None,
            output_kind="text",
            owner="platform",
            provider="DynamicHarness",
            capability="loom_retrieve_context",
            operation="platform",
        ),
        _spec(
            "skill",
            "dynamicharness.tools.skills.skill_tool",
            "skills",
            "Load a specialized Skill when its description matches the current task.",
            "skills",
            fixed_arg_names=("name",),
            is_read_only=True,
            max_result_chars=20000,
            output_kind="text",
            owner="platform",
            provider="DynamicHarness",
            capability="skill",
            operation="platform",
        ),
    )
