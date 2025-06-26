"""Smart tag generation from project analysis results."""

from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from .data_models import (
    AnalysisResult,
    DeploymentInfo,
    DirectoryInfo,
    FrameworkCategory,
    FrameworkInfo,
    LanguageInfo,
    ProjectType,
    SecurityInfo,
    TestingInfo,
)
from .tag_rules import (
    FRAMEWORK_TAG_MAPPING,
    HIGH_CONFIDENCE_THRESHOLD,
    LANGUAGE_TAGS,
    MAX_TAGS_PER_PROJECT,
    MIN_CONFIDENCE_THRESHOLD,
    MIN_TAGS_PER_PROJECT,
    PROJECT_TYPE_TAGS,
    TAG_PRIORITIES,
)
from .tag_validator import TagValidator


class TagGenerator:
    """Generates intelligent tags from project analysis results."""

    def __init__(self):
        self.validator = TagValidator()
        self.context_analyzers = {
            "testing": self._analyze_testing_context,
            "api": self._analyze_api_context,
            "web": self._analyze_web_context,
            "mobile": self._analyze_mobile_context,
            "data": self._analyze_data_context,
            "security": self._analyze_security_context,
            "deployment": self._analyze_deployment_context,
            "architecture": self._analyze_architecture_context,
        }

    def generate_tags(
        self,
        analysis_result: AnalysisResult,
        framework_info: Optional[List[FrameworkInfo]] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Generate prioritized list of relevant tags from analysis results.

        Args:
            analysis_result: Complete project analysis
            framework_info: Optional additional framework information
            user_preferences: Optional user preferences for tag generation

        Returns:
            List of prioritized, validated tags
        """
        all_frameworks = analysis_result.frameworks or []
        if framework_info:
            all_frameworks.extend(framework_info)

        # Collect tags from different sources
        tag_sources = {
            "frameworks": self._generate_framework_tags(all_frameworks),
            "languages": self._generate_language_tags(analysis_result.languages),
            "project_type": self._generate_project_type_tags(
                analysis_result.project_type
            ),
            "directory": self._generate_directory_tags(analysis_result.directory_info),
            "testing": self._generate_testing_tags(analysis_result.testing_info),
            "security": self._generate_security_tags(analysis_result.security_info),
            "deployment": self._generate_deployment_tags(
                analysis_result.deployment_info
            ),
            "context": self._generate_context_tags(analysis_result),
            "architectural": self._generate_architectural_tags(analysis_result),
        }

        # Apply user preferences
        if user_preferences:
            tag_sources = self._apply_user_preferences(tag_sources, user_preferences)

        # Combine and score all tags
        tag_scores = self._calculate_tag_scores(tag_sources, analysis_result)

        # Generate final prioritized list
        prioritized_tags = self._prioritize_tags(tag_scores, analysis_result)

        # Validate and clean up
        final_tags, warnings = self.validator.validate_tag_list(prioritized_tags)

        # Add suggestions if too few tags
        if len(final_tags) < MIN_TAGS_PER_PROJECT:
            suggestions = self._generate_additional_suggestions(
                analysis_result, final_tags
            )
            final_tags.extend(suggestions[: MIN_TAGS_PER_PROJECT - len(final_tags)])

        return final_tags[:MAX_TAGS_PER_PROJECT]

    def _generate_framework_tags(
        self, frameworks: List[FrameworkInfo]
    ) -> List[Tuple[str, float]]:
        """Generate tags from detected frameworks."""
        tags = []

        for framework in frameworks:
            confidence = framework.confidence

            # Add framework name as tag
            tags.append((framework.name.lower(), confidence))

            # Add pre-associated framework tags
            if framework.tags:
                for tag in framework.tags:
                    tags.append((tag, confidence * 0.9))

            # Add mapped tags from our rules
            framework_key = framework.name.lower()
            if framework_key in FRAMEWORK_TAG_MAPPING:
                for tag in FRAMEWORK_TAG_MAPPING[framework_key]:
                    # Boost confidence for high-confidence frameworks
                    tag_confidence = confidence
                    if confidence > HIGH_CONFIDENCE_THRESHOLD:
                        tag_confidence *= 1.2
                    tags.append((tag, min(tag_confidence, 1.0)))

            # Add category-based tags
            category_tags = self._get_category_tags(framework.category)
            for tag in category_tags:
                tags.append((tag, confidence * 0.8))

        return tags

    def _generate_language_tags(
        self, language_info: LanguageInfo
    ) -> List[Tuple[str, float]]:
        """Generate tags from language information."""
        tags = []

        # Primary language
        if language_info.primary_language != "unknown":
            primary_lang = language_info.primary_language.lower()
            tags.append((primary_lang, 1.0))

            # Add language-specific tags
            if primary_lang in LANGUAGE_TAGS:
                for tag in LANGUAGE_TAGS[primary_lang]:
                    tags.append((tag, 0.9))

        # Secondary languages (based on percentage)
        for lang, percentage in language_info.languages.items():
            if percentage > 0.1:  # More than 10% of codebase
                lang_lower = lang.lower()
                confidence = min(percentage * 2, 1.0)  # Scale percentage to confidence

                tags.append((lang_lower, confidence))

                if lang_lower in LANGUAGE_TAGS:
                    for tag in LANGUAGE_TAGS[lang_lower]:
                        tags.append((tag, confidence * 0.8))

        return tags

    def _generate_project_type_tags(
        self, project_type: ProjectType
    ) -> List[Tuple[str, float]]:
        """Generate tags from project type."""
        tags = []

        if project_type != ProjectType.UNKNOWN:
            # Add project type as tag
            tags.append((project_type.value, 0.95))

            # Add associated tags
            if project_type in PROJECT_TYPE_TAGS:
                for tag in PROJECT_TYPE_TAGS[project_type]:
                    tags.append((tag, 0.9))

        return tags

    def _generate_directory_tags(
        self, directory_info: DirectoryInfo
    ) -> List[Tuple[str, float]]:
        """Generate tags from directory structure."""
        tags = []

        # Standard directory indicators
        directory_indicators = {
            "has_src_dir": ("source-code", 0.8),
            "has_lib_dir": ("library", 0.8),
            "has_tests_dir": ("testing", 0.9),
            "has_docs_dir": ("documentation", 0.8),
            "has_scripts_dir": ("automation", 0.7),
            "has_config_dir": ("configuration", 0.7),
            "has_assets_dir": ("assets", 0.7),
            "has_static_dir": ("static-files", 0.8),
            "has_templates_dir": ("templates", 0.8),
            "has_migrations_dir": ("database", 0.9),
        }

        for attr, (tag, confidence) in directory_indicators.items():
            if getattr(directory_info, attr, False):
                tags.append((tag, confidence))

        # Monorepo detection
        if directory_info.monorepo_packages:
            tags.append(("monorepo", 0.95))
            tags.append(("multi-package", 0.8))

        # Nested projects suggest complexity
        if directory_info.nested_projects:
            tags.append(("multi-project", 0.8))

        return tags

    def _generate_testing_tags(
        self, testing_info: TestingInfo
    ) -> List[Tuple[str, float]]:
        """Generate tags from testing setup."""
        tags = []

        if testing_info.has_unit_tests:
            tags.append(("unit-tests", 0.9))
            tags.append(("testing", 0.9))

        if testing_info.has_integration_tests:
            tags.append(("integration-tests", 0.9))

        if testing_info.has_e2e_tests:
            tags.append(("e2e", 0.9))
            tags.append(("automation", 0.7))

        # Test frameworks
        for framework in testing_info.test_frameworks:
            framework_lower = framework.lower()
            tags.append((framework_lower, 0.8))

            # Map test frameworks to additional tags
            if framework_lower in FRAMEWORK_TAG_MAPPING:
                for tag in FRAMEWORK_TAG_MAPPING[framework_lower]:
                    tags.append((tag, 0.7))

        # Coverage tools suggest quality focus
        if testing_info.test_coverage_tools:
            tags.append(("code-coverage", 0.8))
            tags.append(("quality-assurance", 0.8))

        return tags

    def _generate_security_tags(
        self, security_info: SecurityInfo
    ) -> List[Tuple[str, float]]:
        """Generate tags from security setup."""
        tags = []

        if security_info.has_security_tools:
            tags.append(("security", 0.9))

        if security_info.has_env_files:
            tags.append(("environment-config", 0.8))
            tags.append(("configuration", 0.7))

        if security_info.has_secrets_config:
            tags.append(("secrets-management", 0.9))
            tags.append(("security", 0.8))

        if security_info.has_security_headers:
            tags.append(("web-security", 0.8))

        # Authentication methods
        for auth_method in security_info.authentication_methods:
            auth_lower = auth_method.lower()
            tags.append((auth_lower, 0.8))

            if "oauth" in auth_lower:
                tags.append(("oauth", 0.9))
            elif "jwt" in auth_lower:
                tags.append(("jwt", 0.9))

        return tags

    def _generate_deployment_tags(
        self, deployment_info: DeploymentInfo
    ) -> List[Tuple[str, float]]:
        """Generate tags from deployment setup."""
        tags = []

        if deployment_info.containerized:
            tags.append(("containerization", 0.95))
            tags.append(("docker", 0.9))

        # Container tools
        for tool in deployment_info.container_tools:
            tool_lower = tool.lower()
            tags.append((tool_lower, 0.9))

        # Cloud platforms
        for platform in deployment_info.cloud_platforms:
            platform_lower = platform.lower()
            tags.append((platform_lower, 0.9))
            tags.append(("cloud", 0.8))

        # CI/CD tools
        if deployment_info.ci_cd_tools:
            tags.append(("ci-cd", 0.9))
            for tool in deployment_info.ci_cd_tools:
                tags.append((tool.lower(), 0.8))

        # Infrastructure as Code
        if deployment_info.infrastructure_as_code:
            tags.append(("infrastructure-as-code", 0.9))
            tags.append(("devops", 0.8))

        return tags

    def _generate_context_tags(
        self, analysis_result: AnalysisResult
    ) -> List[Tuple[str, float]]:
        """Generate tags from contextual analysis."""
        tags = []

        # Run specialized context analyzers
        for analyzer_name, analyzer_func in self.context_analyzers.items():
            context_tags = analyzer_func(analysis_result)
            tags.extend(context_tags)

        return tags

    def _generate_architectural_tags(
        self, analysis_result: AnalysisResult
    ) -> List[Tuple[str, float]]:
        """Generate architectural pattern tags."""
        tags = []

        # Microservice indicators
        if analysis_result.is_microservice:
            tags.append(("microservices", 0.95))
            tags.append(("distributed", 0.8))
            tags.append(("scalable", 0.8))

        # Monorepo indicators
        if analysis_result.is_monorepo:
            tags.append(("monorepo", 0.95))
            tags.append(("multi-package", 0.8))

        # API-focused project
        api_frameworks = [
            fw
            for fw in analysis_result.frameworks
            if fw.category in [FrameworkCategory.WEB_FRAMEWORK, FrameworkCategory.API]
        ]
        if api_frameworks and not any(
            fw.category == FrameworkCategory.FRONTEND
            for fw in analysis_result.frameworks
        ):
            tags.append(("api-focused", 0.8))
            tags.append(("backend", 0.9))

        return tags

    def _analyze_testing_context(
        self, analysis_result: AnalysisResult
    ) -> List[Tuple[str, float]]:
        """Analyze testing-related context."""
        tags = []

        # High test coverage suggests TDD/BDD
        if analysis_result.testing_info.test_coverage_tools:
            if (
                analysis_result.testing_info.has_unit_tests
                and analysis_result.testing_info.has_integration_tests
            ):
                tags.append(("comprehensive-testing", 0.8))

        # BDD frameworks
        bdd_indicators = ["cucumber", "behave", "rspec", "jasmine"]
        for framework in analysis_result.testing_info.test_frameworks:
            if any(bdd in framework.lower() for bdd in bdd_indicators):
                tags.append(("bdd", 0.8))
                break

        return tags

    def _analyze_api_context(
        self, analysis_result: AnalysisResult
    ) -> List[Tuple[str, float]]:
        """Analyze API-related context."""
        tags = []

        # REST API indicators
        rest_indicators = ["express", "fastapi", "django-rest", "spring-boot"]
        for framework in analysis_result.frameworks:
            if any(
                indicator in framework.name.lower() for indicator in rest_indicators
            ):
                tags.append(("rest-api", 0.9))
                break

        # GraphQL indicators
        graphql_frameworks = ["apollo", "graphql", "relay"]
        for framework in analysis_result.frameworks:
            if any(gql in framework.name.lower() for gql in graphql_frameworks):
                tags.append(("graphql", 0.9))
                break

        return tags

    def _analyze_web_context(
        self, analysis_result: AnalysisResult
    ) -> List[Tuple[str, float]]:
        """Analyze web development context."""
        tags = []

        # Frontend frameworks
        frontend_frameworks = [
            fw
            for fw in analysis_result.frameworks
            if fw.category == FrameworkCategory.FRONTEND
        ]
        if frontend_frameworks:
            tags.append(("frontend", 0.9))

            # SPA indicators
            spa_frameworks = ["react", "vue", "angular", "svelte"]
            if any(fw.name.lower() in spa_frameworks for fw in frontend_frameworks):
                tags.append(("spa", 0.8))

        # SSR indicators
        ssr_frameworks = ["next.js", "nuxt.js", "sveltekit"]
        if any(fw.name.lower() in ssr_frameworks for fw in analysis_result.frameworks):
            tags.append(("ssr", 0.9))
            tags.append(("full-stack", 0.8))

        return tags

    def _analyze_mobile_context(
        self, analysis_result: AnalysisResult
    ) -> List[Tuple[str, float]]:
        """Analyze mobile development context."""
        tags = []

        mobile_frameworks = ["react-native", "flutter", "ionic", "xamarin"]
        for framework in analysis_result.frameworks:
            if framework.name.lower() in mobile_frameworks:
                tags.append(("cross-platform", 0.8))
                break

        return tags

    def _analyze_data_context(
        self, analysis_result: AnalysisResult
    ) -> List[Tuple[str, float]]:
        """Analyze data processing context."""
        tags = []

        data_frameworks = ["pandas", "numpy", "scikit-learn", "tensorflow", "pytorch"]
        data_count = sum(
            1 for fw in analysis_result.frameworks if fw.name.lower() in data_frameworks
        )

        if data_count >= 2:
            tags.append(("data-science", 0.9))
            tags.append(("analytics", 0.8))

        return tags

    def _analyze_security_context(
        self, analysis_result: AnalysisResult
    ) -> List[Tuple[str, float]]:
        """Analyze security context."""
        tags = []

        if analysis_result.security_info.authentication_methods:
            tags.append(("authentication", 0.9))

        if len(analysis_result.security_info.authentication_methods) > 1:
            tags.append(("multi-auth", 0.8))

        return tags

    def _analyze_deployment_context(
        self, analysis_result: AnalysisResult
    ) -> List[Tuple[str, float]]:
        """Analyze deployment context."""
        tags = []

        if (
            analysis_result.deployment_info.ci_cd_tools
            and analysis_result.deployment_info.containerized
        ):
            tags.append(("modern-deployment", 0.8))
            tags.append(("devops", 0.8))

        return tags

    def _analyze_architecture_context(
        self, analysis_result: AnalysisResult
    ) -> List[Tuple[str, float]]:
        """Analyze architectural patterns."""
        tags = []

        # MVC pattern indicators
        mvc_indicators = ["django", "rails", "spring", "laravel"]
        if any(
            indicator in fw.name.lower()
            for fw in analysis_result.frameworks
            for indicator in mvc_indicators
        ):
            tags.append(("mvc", 0.8))

        return tags

    def _get_category_tags(self, category: FrameworkCategory) -> List[str]:
        """Get relevant tags for a framework category."""
        category_mapping = {
            FrameworkCategory.WEB_FRAMEWORK: ["web-framework", "backend"],
            FrameworkCategory.FRONTEND: ["frontend", "user-interface"],
            FrameworkCategory.DATABASE: ["database", "persistence"],
            FrameworkCategory.TESTING: ["testing", "quality-assurance"],
            FrameworkCategory.BUILD_TOOL: ["build-tools", "automation"],
            FrameworkCategory.DEPLOYMENT: ["deployment", "devops"],
            FrameworkCategory.AUTHENTICATION: ["authentication", "security"],
            FrameworkCategory.API: ["api", "web-services"],
            FrameworkCategory.UI_FRAMEWORK: ["ui-framework", "components"],
            FrameworkCategory.STATE_MANAGEMENT: ["state-management", "data-flow"],
            FrameworkCategory.STYLING: ["styling", "css"],
            FrameworkCategory.CONTAINER: ["containerization", "deployment"],
            FrameworkCategory.CLOUD: ["cloud", "managed-services"],
            FrameworkCategory.CI_CD: ["ci-cd", "automation"],
        }

        return category_mapping.get(category, [])

    def _calculate_tag_scores(
        self,
        tag_sources: Dict[str, List[Tuple[str, float]]],
        analysis_result: AnalysisResult,
    ) -> Dict[str, float]:
        """Calculate weighted scores for all tags."""
        tag_scores: Dict[str, float] = defaultdict(float)

        # Source weights
        source_weights = {
            "frameworks": 1.0,
            "project_type": 0.9,
            "languages": 0.8,
            "testing": 0.7,
            "deployment": 0.7,
            "security": 0.6,
            "directory": 0.5,
            "context": 0.6,
            "architectural": 0.8,
        }

        for source, tags in tag_sources.items():
            weight = source_weights.get(source, 0.5)

            for tag, confidence in tags:
                # Apply source weight and confidence
                score = confidence * weight

                # Apply priority boost
                priority_boost = TAG_PRIORITIES.get(tag, 7) / 10.0
                score *= priority_boost

                # Accumulate scores (tags from multiple sources get higher scores)
                tag_scores[tag] += score

        return dict(tag_scores)

    def _prioritize_tags(
        self, tag_scores: Dict[str, float], analysis_result: AnalysisResult
    ) -> List[str]:
        """Create final prioritized tag list."""
        # Sort by score (descending)
        sorted_tags = sorted(tag_scores.items(), key=lambda x: x[1], reverse=True)

        # Filter out low-confidence tags
        filtered_tags = [
            tag for tag, score in sorted_tags if score >= MIN_CONFIDENCE_THRESHOLD
        ]

        return filtered_tags

    def _apply_user_preferences(
        self,
        tag_sources: Dict[str, List[Tuple[str, float]]],
        user_preferences: Dict[str, Any],
    ) -> Dict[str, List[Tuple[str, float]]]:
        """Apply user preferences to tag generation."""

        # Boost preferred tags
        if "preferred_tags" in user_preferences:
            for preferred in user_preferences["preferred_tags"]:
                for source in tag_sources.values():
                    for i, (tag, confidence) in enumerate(source):
                        if tag == preferred.lower():
                            source[i] = (tag, min(confidence * 1.5, 1.0))

        # Exclude unwanted tags
        if "excluded_tags" in user_preferences:
            excluded = set(tag.lower() for tag in user_preferences["excluded_tags"])
            for source in tag_sources.values():
                source[:] = [(tag, conf) for tag, conf in source if tag not in excluded]

        return tag_sources

    def _generate_additional_suggestions(
        self, analysis_result: AnalysisResult, current_tags: List[str]
    ) -> List[str]:
        """Generate additional tag suggestions when we have too few tags."""
        suggestions = []
        current_set = set(current_tags)

        # Basic fallback tags based on what we know
        if analysis_result.languages.primary_language != "unknown":
            lang = analysis_result.languages.primary_language.lower()
            if lang not in current_set:
                suggestions.append(lang)

        # Add generic project type tags if no specific ones
        if not any(
            tag in current_set
            for tag in ["frontend", "backend", "fullstack", "cli", "library"]
        ):
            if analysis_result.frameworks:
                suggestions.append("development")
            else:
                suggestions.append("project")

        # Add basic quality tags
        if "testing" not in current_set and analysis_result.testing_info.has_unit_tests:
            suggestions.append("testing")

        if (
            "documentation" not in current_set
            and analysis_result.directory_info.has_docs_dir
        ):
            suggestions.append("documentation")

        return suggestions

    def validate_tags(self, tags: List[str]) -> List[str]:
        """Validate and clean a list of tags."""
        validated_tags, _ = self.validator.validate_tag_list(tags)
        return validated_tags

    def get_tag_explanations(
        self, tags: List[str], analysis_result: AnalysisResult
    ) -> Dict[str, str]:
        """Get explanations for why specific tags were generated."""
        explanations = {}

        for tag in tags:
            explanation = []

            # Check if tag is a framework name itself
            framework_names = [fw.name.lower() for fw in analysis_result.frameworks]
            if tag in framework_names:
                explanation.append(f"Detected {tag} framework in project")

            # Check framework mapping
            for framework in analysis_result.frameworks:
                if tag in FRAMEWORK_TAG_MAPPING.get(framework.name.lower(), []):
                    explanation.append(f"Associated with {framework.name} framework")
                    break

            # Check if tag is a language name
            if tag == analysis_result.languages.primary_language.lower():
                explanation.append("Primary programming language")
            elif tag in analysis_result.languages.languages:
                explanation.append("Secondary programming language")

            # Check language mapping
            if tag in LANGUAGE_TAGS.get(
                analysis_result.languages.primary_language.lower(), []
            ):
                explanation.append(
                    f"Related to {analysis_result.languages.primary_language} programming"
                )

            # Check project type
            if tag == analysis_result.project_type.value:
                explanation.append("Matches project type")
            elif tag in PROJECT_TYPE_TAGS.get(analysis_result.project_type, []):
                explanation.append(
                    f"Relevant for {analysis_result.project_type.value} projects"
                )

            # Check directory structure
            if tag == "testing" and analysis_result.directory_info.has_tests_dir:
                explanation.append("Project has test directory structure")
            elif tag == "documentation" and analysis_result.directory_info.has_docs_dir:
                explanation.append("Project has documentation directory")

            # Check testing info
            if (
                tag in ["unit-tests", "integration-tests", "e2e"]
                and analysis_result.testing_info.has_unit_tests
            ):
                explanation.append("Project has comprehensive testing setup")

            # Default explanation
            if not explanation:
                explanation.append("Detected based on project analysis")

            explanations[tag] = "; ".join(explanation)

        return explanations
