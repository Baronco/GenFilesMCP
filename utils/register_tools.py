from collections.abc import Callable
from logging import Logger
from typing import Any

def register_word_tool(
	app: Any,
	logger: Logger,
	word_template: str,
	enable_word_element_filling: bool,
	generate_word_structured: Callable[..., Any],
	generate_word: Callable[..., Any],
) -> None:
	if enable_word_element_filling:
		app.post(
			"/generate_word_structured",
			summary="Generate Word",
			description=word_template,
			operation_id="generate_word_structured",
		)(generate_word_structured)
		logger.info("Registered Word endpoint: generate_word_structured")
		return

	app.post(
		"/generate_word",
		summary="Generate Word",
		description=word_template,
		operation_id="generate_word",
	)(generate_word)
	logger.info("Registered Word endpoint: generate_word")
