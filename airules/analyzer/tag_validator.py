"""Tag validation, deduplication, and quality control."""

import re
from typing import Any, Dict, List, Tuple

from .tag_rules import (
    EXCLUSION_RULES,
    LANGUAGE_TAGS,
    MAX_TAGS_PER_PROJECT,
    MIN_TAGS_PER_PROJECT,
    PROJECT_TYPE_TAGS,
    TAG_GROUPS,
    TAG_PRIORITIES,
)


class TagValidator:
    """Validates, cleans, and optimizes tag lists."""

    def __init__(self):
        self.synonym_map = self._build_synonym_map()
        self.invalid_patterns = [
            r"^[0-9]+$",  # Pure numbers
            r"^[^a-zA-Z]",  # Doesn't start with letter
            r"[^a-zA-Z0-9\-_]",  # Contains invalid characters (removed . as it can be problematic)
        ]

    def _build_synonym_map(self) -> Dict[str, str]:
        """Build a map of synonymous tags to their canonical form."""
        return {
            # JavaScript variants
            "js": "javascript",
            "node": "node.js",
            "nodejs": "node.js",
            "react.js": "react",
            "reactjs": "react",
            "vue.js": "vue",
            "vuejs": "vue",
            "angular.js": "angularjs",
            "angularjs": "angular",
            # Python variants
            "py": "python",
            "python3": "python",
            # Database variants
            "postgres": "postgresql",
            "psql": "postgresql",
            "mongo": "mongodb",
            "mysql": "mysql",
            # Testing variants
            "tests": "testing",
            "test": "testing",
            "spec": "testing",
            "unit-test": "unit-tests",
            "integration-test": "integration-tests",
            "e2e-test": "e2e",
            "end-to-end": "e2e",
            # Web variants
            "frontend": "frontend",
            "front-end": "frontend",
            "backend": "backend",
            "back-end": "backend",
            "fullstack": "full-stack",
            "full-stack": "fullstack",
            # Infrastructure variants
            "devops": "devops",
            "dev-ops": "devops",
            "ci": "ci-cd",
            "cd": "ci-cd",
            "continuous-integration": "ci-cd",
            "continuous-deployment": "ci-cd",
            # Style variants
            "css3": "css",
            "html5": "html",
            "sass": "scss",
            # Mobile variants
            "ios": "mobile",
            "android": "mobile",
            "mobile-app": "mobile",
            "native-app": "mobile",
            # API variants
            "api": "rest-api",
            "rest": "rest-api",
            "restful": "rest-api",
            "web-api": "rest-api",
            "graphql-api": "graphql",
            # Architecture variants
            "microservice": "microservices",
            "micro-service": "microservices",
            "monolithic": "monolith",
            # Security variants
            "auth": "authentication",
            "authz": "authorization",
            "security": "security",
        }

    def normalize_tag(self, tag: str) -> str:
        """Normalize a single tag to its canonical form."""
        if not tag:
            return ""

        # Convert to lowercase and strip whitespace
        normalized = tag.lower().strip()

        # Replace spaces with hyphens
        normalized = re.sub(r"\s+", "-", normalized)

        # Remove multiple consecutive hyphens
        normalized = re.sub(r"-+", "-", normalized)

        # Remove leading/trailing hyphens
        normalized = normalized.strip("-")

        # Apply synonym mapping
        if normalized in self.synonym_map:
            normalized = self.synonym_map[normalized]

        return normalized

    def is_valid_tag(self, tag: str) -> bool:
        """Check if a tag is valid according to naming rules."""
        if not tag or len(tag) < 2:
            return False

        # Check against invalid patterns
        for pattern in self.invalid_patterns:
            if re.search(pattern, tag):
                return False

        # Check length constraints
        if len(tag) > 50:  # Too long
            return False

        return True

    def remove_duplicates(self, tags: List[str]) -> List[str]:
        """Remove duplicate tags while preserving order."""
        seen = set()
        result = []

        for tag in tags:
            normalized_tag = self.normalize_tag(tag)
            if (
                normalized_tag
                and normalized_tag not in seen
                and self.is_valid_tag(normalized_tag)
            ):
                seen.add(normalized_tag)
                result.append(normalized_tag)

        return result

    def apply_exclusion_rules(self, tags: List[str]) -> List[str]:
        """Apply exclusion rules to remove conflicting tags."""
        tag_set = set(tags)
        excluded = set()

        for primary_tag, excluded_tags in EXCLUSION_RULES.items():
            if primary_tag in tag_set:
                for excluded_tag in excluded_tags:
                    if excluded_tag in tag_set:
                        excluded.add(excluded_tag)

        return [tag for tag in tags if tag not in excluded]

    def consolidate_groups(self, tags: List[str]) -> List[str]:
        """Consolidate related tags into groups where appropriate."""
        tag_set = set(tags)
        result = list(tags)

        for group_name, group_tags in TAG_GROUPS.items():
            # If we have multiple tags from a group, consider consolidating
            matching_tags = [tag for tag in group_tags if tag in tag_set]

            if len(matching_tags) >= 3:  # If 3+ tags from same group
                # Remove individual tags and add group tag
                for tag in matching_tags:
                    if tag in result:
                        result.remove(tag)

                if group_name not in result:
                    result.append(group_name)

        return result

    def prioritize_tags(
        self, tags: List[str], max_tags: int = MAX_TAGS_PER_PROJECT
    ) -> List[str]:
        """Prioritize and limit tags based on importance."""
        if len(tags) <= max_tags:
            return tags

        # Sort by priority (higher priority first)
        def get_priority(tag: str) -> int:
            return TAG_PRIORITIES.get(tag, 7)  # Default priority

        sorted_tags = sorted(tags, key=get_priority, reverse=True)
        return sorted_tags[:max_tags]

    def validate_tag_list(
        self, tags: List[str], min_tags: int = MIN_TAGS_PER_PROJECT
    ) -> Tuple[List[str], List[str]]:
        """
        Validate an entire tag list and return validated tags and warnings.

        Returns:
            Tuple of (validated_tags, warnings)
        """
        warnings = []

        if not tags:
            warnings.append("No tags provided")
            return [], warnings

        # Normalize and deduplicate
        normalized_tags = self.remove_duplicates(tags)

        if len(normalized_tags) != len(tags):
            warnings.append(
                f"Removed {len(tags) - len(normalized_tags)} duplicate/invalid tags"
            )

        # Apply exclusion rules
        before_exclusion = len(normalized_tags)
        normalized_tags = self.apply_exclusion_rules(normalized_tags)

        if len(normalized_tags) < before_exclusion:
            warnings.append(
                f"Removed {before_exclusion - len(normalized_tags)} conflicting tags"
            )

        # Consolidate groups
        before_consolidation = len(normalized_tags)
        normalized_tags = self.consolidate_groups(normalized_tags)

        if len(normalized_tags) < before_consolidation:
            warnings.append("Consolidated related tags into groups")

        # Prioritize if too many tags
        if len(normalized_tags) > MAX_TAGS_PER_PROJECT:
            warnings.append(f"Limited to {MAX_TAGS_PER_PROJECT} highest priority tags")
            normalized_tags = self.prioritize_tags(normalized_tags)

        # Check minimum requirement
        if len(normalized_tags) < min_tags:
            warnings.append(
                f"Only {len(normalized_tags)} tags generated (minimum {min_tags} recommended)"
            )

        return normalized_tags, warnings

    def suggest_missing_tags(
        self, tags: List[str], project_context: Dict[str, Any]
    ) -> List[str]:
        """Suggest additional tags that might be missing based on context."""
        suggestions = []
        tag_set = set(tags)

        # Check for common patterns
        if "testing" in tag_set and "unit-tests" not in tag_set:
            suggestions.append("unit-tests")

        if "database" in tag_set and not any(
            db in tag_set for db in ["postgresql", "mysql", "mongodb", "sqlite"]
        ):
            suggestions.append("sql")

        if "rest-api" in tag_set and "json" not in tag_set:
            suggestions.append("json")

        if (
            any(web in tag_set for web in ["react", "vue", "angular"])
            and "components" not in tag_set
        ):
            suggestions.append("components")

        if "docker" in tag_set and "containerization" not in tag_set:
            suggestions.append("containerization")

        # Context-based suggestions
        if project_context.get("has_tests", False) and "testing" not in tag_set:
            suggestions.append("testing")

        if project_context.get("is_web_project", False) and not any(
            web in tag_set for web in ["frontend", "backend", "fullstack"]
        ):
            suggestions.append("web-development")

        return [s for s in suggestions if s not in tag_set]

    def calculate_tag_relevance_score(self, tag: str, context: Dict[str, Any]) -> float:
        """Calculate relevance score for a tag given project context."""
        base_score = TAG_PRIORITIES.get(tag, 5) / 10.0  # Normalize to 0-1

        # Boost score based on context
        multiplier = 1.0

        # Framework detection boosts
        if context.get("frameworks", []):
            framework_names = [fw.lower() for fw in context["frameworks"]]
            if tag in framework_names:
                multiplier *= 1.5

        # Language alignment
        if context.get("primary_language"):
            lang = context["primary_language"].lower()
            if tag == lang or tag in LANGUAGE_TAGS.get(lang, []):
                multiplier *= 1.3

        # Project type alignment
        project_type = context.get("project_type")
        if project_type and tag in PROJECT_TYPE_TAGS.get(project_type, []):
            multiplier *= 1.4

        return min(base_score * multiplier, 1.0)

    def generate_tag_report(
        self, original_tags: List[str], final_tags: List[str], warnings: List[str]
    ) -> str:
        """Generate a human-readable report of tag validation process."""
        report = []
        report.append("Tag Validation Report")
        report.append("=" * 22)
        report.append(f"Original tags: {len(original_tags)}")
        report.append(f"Final tags: {len(final_tags)}")
        report.append("")

        if warnings:
            report.append("Warnings:")
            for warning in warnings:
                report.append(f"  - {warning}")
            report.append("")

        report.append("Final tag list:")
        for i, tag in enumerate(final_tags, 1):
            priority = TAG_PRIORITIES.get(tag, 7)
            report.append(f"  {i:2d}. {tag} (priority: {priority})")

        return "\n".join(report)
