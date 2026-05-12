from collections.abc import Callable
from logging import Logger
from typing import Any

def register_word_tool(
	app: Any,
	logger: Logger,
	word_template: str,
	enable_structured_yaml_mode: bool,
	generate_word_structured: Callable[..., Any],
	generate_word: Callable[..., Any],
) -> None:
	if enable_structured_yaml_mode:
		app.post(
			"/generate_word_structured_yaml",
			summary="Generate Word",
			description=word_template,
			operation_id="generate_word_structured_yaml",
		)(generate_word_structured)
		logger.info("Registered Word endpoint: generate_word_structured_yaml")
		return

	app.post(
		"/generate_word",
		summary="Generate Word",
		description=word_template,
		operation_id="generate_word",
	)(generate_word)
	logger.info("Registered Word endpoint: generate_word")

def register_powerpoint_tool(
	app: Any,
	logger: Logger,
	powerpoint_template: str,
	enable_structured_yaml_mode: bool,
	generate_powerpoint: Callable[..., Any],
	generate_powerpoint_structured: Callable[..., Any],
) -> None:
	if enable_structured_yaml_mode:
		app.post(
			"/generate_powerpoint_structured_yaml",
			summary="Generate PowerPoint",
			description=powerpoint_template,
			operation_id="generate_powerpoint_structured_yaml",
		)(generate_powerpoint_structured)
		logger.info("Registered PowerPoint endpoint: generate_powerpoint_structured_yaml")
		return

	app.post(
		"/generate_powerpoint",
		summary="Generate PowerPoint",
		description=powerpoint_template,
		operation_id="generate_powerpoint",
	)(generate_powerpoint)
	logger.info("Registered PowerPoint endpoint: generate_powerpoint")