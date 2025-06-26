"""Service layer for rules generation."""

from datetime import datetime
from typing import List, Optional, Protocol, Tuple

from .api_clients import AIClientFactory
from .config import get_config
from .exceptions import APIError, ConfigurationError
from .file_operations import ContentProcessor, FileManager
from .ui import ConsoleManager, Spinner
from .venv_check import in_virtualenv


class RulesGeneratorProtocol(Protocol):
    """Protocol for rules generator implementations."""

    def generate_rules(
        self,
        lang: str,
        tool: str,
        tag: str,
        model: str,
        research_summary: Optional[str] = None,
    ) -> str:
        """Generate rules for a specific tool and tag."""
        ...

    def validate_rules(self, content: str, review_model: str) -> str:
        """Validate and refine generated rules."""
        ...


class ResearchService:
    """Service for performing research using Perplexity."""

    def __init__(self):
        self.client_factory = AIClientFactory()

    def research_topic(self, lang: str, tag: str) -> str:
        """Perform research on a specific topic."""
        prompt = (
            f"Your goal is to provide rulesets for AI coding assistants in a '{lang}' project using '{tag}'. "
            "Focus the best rulesets on Github for similar projects and return only the best industry standard "
            "best practices in the correct format."
        )

        try:
            client = self.client_factory.get_research_client()
            return client.generate_completion(prompt)
        except Exception as e:
            raise APIError(f"Research failed: {e}")


class RulesGeneratorService:
    """Service for generating and validating rules."""

    def __init__(self):
        self.client_factory = AIClientFactory()
        self.content_processor = ContentProcessor()

    def generate_rules(
        self,
        lang: str,
        tool: str,
        tag: str,
        model: str,
        research_summary: Optional[str] = None,
    ) -> str:
        """Generate coding assistant rules using the appropriate AI API."""
        today = datetime.now().strftime("%Y-%m-%d")

        prompt_sections = [
            f"Generate a set of rules for the AI coding assistant '{tool}' for a '{lang}' project.",
            "Use best practices and industry standard rulesets with clarity and proper formatting.",
            "Keep the rules concise and to the point.",
            f"The rules should focus on the topic: '{tag}'.",
            f"The current date is {today}. The rules should be modern and reflect the latest standards.",
            "",
            "IMPORTANT: Use strong enforcement language for critical rules:",
            "- Use **MUST** for absolutely required practices that cannot be violated",
            "- Use **ALWAYS** for practices that should be consistently followed",
            "- Use **MANDATORY** for non-negotiable requirements",
            "- Use **NEVER** for practices that should be completely avoided",
            "- Use **REQUIRED** for essential components or steps",
            "- Use 'should' or 'recommended' for best practices that are preferred but not critical",
            "",
            "The output should be a markdown file, containing only the rules, without any additional explanations or preamble.",
            "Start the file with a title that includes the language and tag.",
            "Format rules with clear hierarchy using markdown headers and bullet points.",
        ]

        if research_summary:
            prompt_sections.extend(
                [
                    "\n--- RESEARCH SUMMARY ---\n",
                    research_summary,
                    "\n--- END RESEARCH SUMMARY ---\n",
                    "Based on the research summary above, generate the rules file.",
                ]
            )

        prompt = "\n".join(prompt_sections)

        try:
            client = self.client_factory.get_client(model)
            return client.generate_completion(prompt, model)
        except Exception as e:
            raise APIError(f"Rules generation failed: {e}")

    def validate_rules(self, content: str, review_model: str) -> str:
        """Validate and refine the generated rules."""
        today = datetime.now().strftime("%Y-%m-%d")
        review_prompt = (
            f"Please review and refine the following AI coding assistant rules. "
            f"Ensure they are clear, concise, and follow best practices and industry standards as of {today}. "
            f"IMPORTANT: Maintain and strengthen enforcement language where appropriate:\n"
            f"- Keep **MUST**, **ALWAYS**, **MANDATORY**, **NEVER**, **REQUIRED** for critical rules\n"
            f"- Use 'should' or 'recommended' for best practices that are preferred but not critical\n"
            f"- Ensure the language clearly indicates the severity and importance of each rule\n"
            f"Return only the refined markdown content, without any preamble.\n\n---\n\n{content}"
        )

        try:
            client = self.client_factory.get_client(review_model)
            return client.generate_completion(review_prompt, review_model)
        except Exception as e:
            raise APIError(f"Rules validation failed: {e}")


class GenerationPipelineService:
    """Orchestrates the complete rules generation pipeline."""

    def __init__(self, console: ConsoleManager, file_manager: FileManager):
        self.console = console
        self.file_manager = file_manager
        self.research_service = ResearchService()
        self.rules_generator = RulesGeneratorService()
        self.content_processor = ContentProcessor()

    def run_pipeline(
        self,
        tool: str,
        primary_model: str,
        research: bool,
        review_model: Optional[str],
        dry_run: bool,
        yes: bool,
        project_path: str,
        lang: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> None:
        """Run the complete generation pipeline."""
        self._validate_environment()

        # Get configuration
        current_lang, current_tags = self._get_configuration(lang, tags)

        # Process each tag
        has_errors = False
        for tag_item in current_tags:
            try:
                self._process_single_tag(
                    tag_item,
                    current_lang,
                    tool,
                    primary_model,
                    research,
                    review_model,
                    dry_run,
                    yes,
                    project_path,
                )
            except Exception as e:
                self.console.print_error(f"✗ ERROR processing tag '{tag_item}': {e}")
                has_errors = True

        if has_errors:
            raise APIError("Pipeline completed with errors")

    def _validate_environment(self) -> None:
        """Validate that the environment is properly set up."""
        if not in_virtualenv():
            raise ConfigurationError(
                "This command must be run in a virtual environment."
            )

    def _get_configuration(
        self, lang: Optional[str], tags: Optional[str]
    ) -> Tuple[str, List[str]]:
        """Get language and tags from parameters or configuration."""
        # Get language - either from parameter, config, or default
        current_lang = lang
        current_tags = []

        # Try to get from configuration if not provided
        if not current_lang or not tags:
            try:
                config = get_config()
                if not current_lang:
                    current_lang = config.get("settings", "language", fallback="python")
                if not tags:
                    current_tags_str = config.get(
                        "settings", "tags", fallback="general"
                    )
                    current_tags = [tag.strip() for tag in current_tags_str.split(",")]
            except FileNotFoundError:
                # If no config file and no lang provided, require at least lang
                if not current_lang:
                    raise ConfigurationError(
                        "No .rules4rc file found and no --lang provided. "
                        "Please run 'rules4 init' first or provide --lang parameter."
                    )
                # Use default tag if no config and no tags provided
                if not tags:
                    current_tags = ["general"]

        # If tags were provided via parameter, use those
        if tags:
            current_tags = [tag.strip() for tag in tags.split(",")]

        # Ensure we have at least one tag
        if not current_tags:
            current_tags = ["general"]

        return current_lang, current_tags

    def _process_single_tag(
        self,
        tag: str,
        lang: str,
        tool: str,
        primary_model: str,
        research: bool,
        review_model: Optional[str],
        dry_run: bool,
        yes: bool,
        project_path: str,
    ) -> None:
        """Process a single tag through the generation pipeline."""
        # Research phase
        research_summary = None
        if research:
            with Spinner(f"Researching '{tag}' with Perplexity"):
                research_summary = self.research_service.research_topic(lang, tag)

        # Generation phase
        with Spinner(f"Generating rules for '{tag}'"):
            rules_content = self.rules_generator.generate_rules(
                lang, tool, tag, primary_model, research_summary
            )

            if review_model:
                rules_content = self.rules_generator.validate_rules(
                    rules_content, review_model
                )

        # Clean and write content
        rules_content = self.content_processor.clean_rules_content(rules_content)
        filepath = self.file_manager.get_rules_filepath(tool, lang, tag, project_path)
        self.file_manager.write_rules_file(filepath, rules_content, dry_run, yes, tool)
