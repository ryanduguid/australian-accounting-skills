"""Shared strict YAML loading for the validator and the test suite."""

from __future__ import annotations

import yaml


def unique_key_safe_loader(
    error: type[Exception],
    *,
    field_noun: str,
    keys_noun: str,
) -> type[yaml.SafeLoader]:
    """Build a SafeLoader subclass that rejects aliases and duplicate keys.

    ``error`` carries each caller's expected exception type and the nouns
    carry its message wording, so the rejection behaviour cannot drift
    between callers again.
    """

    class UniqueKeySafeLoader(yaml.SafeLoader):
        """Safe YAML loader that rejects aliases and duplicate mapping keys."""

        def compose_node(self, parent: object, index: object) -> yaml.nodes.Node:
            if self.check_event(yaml.events.AliasEvent):
                raise error("YAML aliases are not permitted")
            return super().compose_node(parent, index)

        def construct_mapping(
            self,
            node: yaml.nodes.MappingNode,
            deep: bool = False,
        ) -> dict[object, object]:
            mapping: dict[object, object] = {}
            for key_node, value_node in node.value:
                key = self.construct_object(key_node, deep=deep)
                try:
                    duplicate = key in mapping
                except TypeError as key_error:
                    raise error(f"{keys_noun} must be scalar") from key_error
                if duplicate:
                    raise error(f"duplicate {field_noun}: {key!r}")
                mapping[key] = self.construct_object(value_node, deep=deep)
            return mapping

    return UniqueKeySafeLoader
