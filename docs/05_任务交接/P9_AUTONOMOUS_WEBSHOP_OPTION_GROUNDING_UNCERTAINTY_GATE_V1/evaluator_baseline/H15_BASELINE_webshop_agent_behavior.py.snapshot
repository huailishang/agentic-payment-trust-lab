from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple


_WORD_RE = re.compile(r"[a-z0-9]+(?:[.-][a-z0-9]+)*")
_ASIN_RE = re.compile(r"^[a-z0-9]{10}$", re.IGNORECASE)
_PRICE_RE = re.compile(r"(?<![a-z0-9])\$?([0-9]+(?:\.[0-9]+)?)")
_BUDGET_RE = re.compile(
    r"(?:under|below|less\s+than|lower\s+than|price\s+lower\s+than)\s*\$?([0-9]+(?:\.[0-9]+)?)",
    re.IGNORECASE,
)

_STOP_WORDS = {
    "a",
    "also",
    "am",
    "an",
    "and",
    "are",
    "be",
    "but",
    "dollar",
    "dollars",
    "everyday",
    "for",
    "friendly",
    "hello",
    "i",
    "im",
    "in",
    "instruction",
    "is",
    "looking",
    "need",
    "some",
    "that",
    "lower",
    "me",
    "of",
    "pair",
    "please",
    "price",
    "size",
    "than",
    "the",
    "to",
    "under",
    "want",
    "with",
}

_STRUCTURAL_CLICKABLES = {
    "back to search",
    "buy now",
    "description",
    "features",
    "next >",
    "< prev",
    "prev",
    "reviews",
    "search",
}

_SIZE_WORDS = {
    "small",
    "medium",
    "large",
    "xsmall",
    "xlarge",
    "xxsmall",
    "xxlarge",
    "xxxlarge",
}

_CARDINAL_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}

_MEASUREMENT_UNIT_ALIASES = {
    "cm": "cm",
    "mm": "mm",
    "m": "m",
    "inch": "in",
    "inches": "in",
    "in": "in",
    "ounce": "oz",
    "ounces": "oz",
    "oz": "oz",
    "ml": "ml",
    "liter": "l",
    "liters": "l",
    "litre": "l",
    "litres": "l",
    "l": "l",
    "gram": "g",
    "grams": "g",
    "g": "g",
    "kg": "kg",
}


@dataclass(frozen=True)
class AgentPolicyInput:
    instruction_text: str
    observation: str
    available_actions: Dict[str, object]
    step_index: int
    previous_actions: Sequence[str]


@dataclass(frozen=True)
class AgentPolicyDecision:
    action: Optional[str]
    reason_summary: str
    stop: bool = False


def choose_webshop_action(state: AgentPolicyInput) -> AgentPolicyDecision:
    clickables = _clickables(state.available_actions)
    previous = tuple(str(action).strip().lower() for action in state.previous_actions)

    option = _instruction_option(clickables, state.instruction_text, previous)
    if option is not None:
        return AgentPolicyDecision(
            action="click[{}]".format(option),
            reason_summary="select an explicitly requested visible option",
        )

    if _contains_clickable(clickables, "buy now"):
        return AgentPolicyDecision(
            action=None,
            reason_summary="requested product state reached; stop before purchase",
            stop=True,
        )

    asins = [item for item in clickables if _ASIN_RE.fullmatch(item)]
    if asins:
        chosen = _choose_result(
            asins=asins,
            observation=state.observation,
            instruction=state.instruction_text,
        )
        return AgentPolicyDecision(
            action="click[{}]".format(chosen),
            reason_summary="open the visible result with the strongest instruction match",
        )

    has_search_bar = bool(state.available_actions.get("has_search_bar"))
    already_searched = any(action.startswith("search[") for action in previous)
    if has_search_bar and not already_searched:
        query = _search_query(state.instruction_text)
        if not query:
            return AgentPolicyDecision(
                action=None,
                reason_summary="instruction does not provide usable local search terms",
                stop=True,
            )
        return AgentPolicyDecision(
            action="search[{}]".format(query),
            reason_summary="search using terms derived from the user instruction",
        )

    next_page = _matching_clickable(clickables, "next >")
    if next_page is not None:
        return AgentPolicyDecision(
            action="click[{}]".format(next_page),
            reason_summary="inspect the next visible result page",
        )

    return AgentPolicyDecision(
        action=None,
        reason_summary="no safe progress action remains",
        stop=True,
    )


def _clickables(available_actions: Dict[str, object]) -> List[str]:
    raw = available_actions.get("clickables", [])
    if not isinstance(raw, (list, tuple)):
        return []
    return [str(item) for item in raw if str(item).strip()]


def _contains_clickable(clickables: Sequence[str], expected: str) -> bool:
    expected_lower = expected.lower()
    return any(item.lower() == expected_lower for item in clickables)


def _matching_clickable(clickables: Sequence[str], expected: str) -> Optional[str]:
    expected_lower = expected.lower()
    for item in clickables:
        if item.lower() == expected_lower:
            return item
    return None


def _instruction_option(
    clickables: Sequence[str],
    instruction: str,
    previous_actions: Sequence[str],
) -> Optional[str]:
    instruction_phrase = _normalised_phrase(instruction)
    instruction_tokens = set(_basic_words(instruction))
    used = set(previous_actions)
    prior_option_tokens = []
    consumed_instruction_roots = set()
    prior_numeric_option = False
    prior_lexical_option = False
    for previous_action in previous_actions:
        match = re.fullmatch(r"click\[(.+)\]", str(previous_action).strip(), re.IGNORECASE)
        if match is None:
            continue
        previous_value = match.group(1)
        if previous_value.lower() in _STRUCTURAL_CLICKABLES or (
            _ASIN_RE.fullmatch(previous_value) and _dimension_signature(previous_value) is None
        ):
            continue
        tokens = _basic_words(previous_value)
        if tokens:
            prior_option_tokens.append(set(tokens))
            kind = _option_semantic_kind(previous_value)
            if kind == "numeric":
                prior_numeric_option = True
            elif kind == "lexical":
                prior_lexical_option = True
            consumed_instruction_roots.update(
                _matched_instruction_roots(tokens, instruction_tokens)
            )

    candidates: List[Tuple[int, int, str]] = []
    for position, item in enumerate(clickables):
        lowered = item.lower()
        if lowered in _STRUCTURAL_CLICKABLES or (
            _ASIN_RE.fullmatch(item) and _dimension_signature(item) is None
        ):
            continue
        action = "click[{}]".format(item).lower()
        if action in used:
            continue
        item_tokens = _basic_words(item)
        if not item_tokens:
            continue

        item_phrase = " ".join(item_tokens)
        exact_phrase = _contains_token_phrase(instruction_phrase, item_phrase)
        numeric_led = any(token[0].isdigit() for token in item_tokens if token)
        item_kind = _option_semantic_kind(item)
        item_token_set = set(item_tokens)
        if prior_numeric_option and item_kind == "numeric":
            continue
        if any(item_token_set.intersection(previous) for previous in prior_option_tokens):
            continue
        if numeric_led:
            exact_phrase = _numeric_option_matches_instruction(instruction, item)

        matched_chars = 0
        matched_tokens = 0
        matched_roots = set()
        if not numeric_led:
            matched_roots = _matched_instruction_roots(item_tokens, instruction_tokens)
            if matched_roots.intersection(consumed_instruction_roots):
                continue
            for token in item_tokens:
                best = 0
                for requested in matched_roots:
                    if token == requested:
                        best = max(best, len(token))
                    elif len(requested) >= 3 and token.startswith(requested):
                        best = max(best, len(requested))
                    elif len(token) >= 3 and requested.startswith(token):
                        best = max(best, len(token))
                if best:
                    matched_tokens += 1
                    matched_chars += best

            # After one free-text option has already satisfied a requested attribute,
            # do not drift into another merely fuzzy free-text label. Exact requested
            # labels and distinct size/numeric groups remain eligible.
            if prior_lexical_option and item_kind == "lexical" and not exact_phrase:
                continue

        if not exact_phrase and matched_tokens == 0:
            continue

        # Rank by explicit phrase match first, then by how much of the visible option
        # is grounded in the instruction, and finally by specificity. This supports
        # visible label variants without embedding task-specific option truth.
        coverage = int(1000 * matched_tokens / max(1, len(item_tokens)))
        score = (10000 if exact_phrase else 0) + coverage + matched_chars * 10 + len(lowered)
        candidates.append((score, position, item))

    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][2]


def _search_query(instruction: str) -> str:
    terms = _significant_terms(instruction)
    return " ".join(terms[:12])


def _significant_terms(instruction: str) -> List[str]:
    result: List[str] = []
    seen = set()
    for token in _words(instruction):
        token = _canonical_term(token)
        if token in _STOP_WORDS or token.isdigit() or len(token) < 3:
            continue
        if token not in seen:
            seen.add(token)
            result.append(token)
    return result


def _canonical_term(token: str) -> str:
    token = str(token).lower()
    aliases = {
        "mens": "men",
        "men's": "men",
        "womens": "women",
        "women's": "women",
        "soles": "sole",
    }
    return aliases.get(token, token)


def _words(text: str) -> List[str]:
    return _WORD_RE.findall(str(text).lower())


def _basic_words(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", str(text).lower())


def _normalised_phrase(text: str) -> str:
    return " ".join(_basic_words(text))


def _matched_instruction_roots(
    option_tokens: Sequence[str], instruction_tokens: Sequence[str]
) -> set:
    matched = set()
    for token in option_tokens:
        for requested in instruction_tokens:
            if token == requested:
                matched.add(requested)
            elif len(requested) >= 3 and token.startswith(requested):
                matched.add(requested)
            elif len(token) >= 3 and requested.startswith(token):
                matched.add(requested)
    return matched


def _contains_token_phrase(haystack: str, needle: str) -> bool:
    if not needle:
        return False
    return (" " + needle + " ") in (" " + haystack + " ")


def _contains_raw_option(instruction: str, option: str) -> bool:
    pattern = r"(?<![a-z0-9.]){}(?![a-z0-9.])".format(re.escape(str(option).lower()))
    return re.search(pattern, str(instruction).lower()) is not None


def _option_semantic_kind(value: str) -> str:
    tokens = _basic_words(value)
    compact = "".join(tokens)
    if any(token in _SIZE_WORDS for token in tokens) or compact in _SIZE_WORDS:
        return "size"
    if _dimension_signature(value) is not None:
        return "dimension"
    if _count_amount(value) is not None:
        return "count"
    if _measurement_pairs(value):
        return "measurement"
    if any(token and token[0].isdigit() for token in tokens):
        return "numeric"
    return "lexical"


def _canonical_number_text(value: str) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value).lower()
    if number.is_integer():
        return str(int(number))
    return ("{:.8f}".format(number)).rstrip("0").rstrip(".")


def _canonical_measurement_unit(value: str) -> str:
    return _MEASUREMENT_UNIT_ALIASES.get(str(value).lower(), str(value).lower())


def _dimension_signature(text: str) -> Optional[Tuple[str, ...]]:
    match = re.search(
        r"(?<![a-z0-9])([0-9]+(?:\.[0-9]+)?)\s*[x×]\s*"
        r"([0-9]+(?:\.[0-9]+)?)(?:\s*[x×]\s*([0-9]+(?:\.[0-9]+)?))?\s*"
        r"(cm|mm|m|inch|inches|in)(?![a-z])",
        str(text).lower(),
    )
    if match is None:
        return None
    dimensions = [
        _canonical_number_text(value)
        for value in match.groups()[:3]
        if value is not None
    ]
    dimensions.append(_canonical_measurement_unit(match.group(4)))
    return tuple(dimensions)


def _measurement_pairs(text: str) -> set:
    pairs = set()
    pattern = re.compile(
        r"(?<![a-z0-9])([0-9]+(?:\.[0-9]+)?)\s*"
        r"(cm|mm|m|inch|inches|in|ounce|ounces|oz|ml|liter|liters|litre|litres|l|gram|grams|g|kg)"
        r"(?![a-z])",
        re.IGNORECASE,
    )
    for match in pattern.finditer(str(text)):
        pairs.add(
            (
                _canonical_number_text(match.group(1)),
                _canonical_measurement_unit(match.group(2)),
            )
        )
    return pairs


def _count_amount(text: str) -> Optional[int]:
    match = re.search(
        r"(?<![a-z0-9])([0-9]+)\s*(?:pcs?|pieces?|count)(?![a-z])",
        str(text).lower(),
    )
    if match is None:
        return None
    return int(match.group(1))


def _requested_cardinal_amounts(instruction: str) -> set:
    amounts = set()
    for token in _basic_words(instruction):
        if token in _CARDINAL_WORDS:
            amounts.add(_CARDINAL_WORDS[token])
    for match in re.finditer(
        r"(?<![a-z0-9])([0-9]+)\s*(?:pcs?|pieces?|count)(?![a-z])",
        str(instruction).lower(),
    ):
        amounts.add(int(match.group(1)))
    return amounts


def _numeric_option_matches_instruction(instruction: str, option: str) -> bool:
    if _contains_raw_option(instruction, option):
        return True

    option_dimension = _dimension_signature(option)
    if option_dimension is not None:
        return option_dimension == _dimension_signature(instruction)

    compact_instruction = re.sub(r"[^a-z0-9]+", "", str(instruction).lower())
    compact_option = re.sub(r"[^a-z0-9]+", "", str(option).lower())
    if len(compact_option) >= 3 and compact_option in compact_instruction:
        return True

    option_measurements = _measurement_pairs(option)
    if option_measurements:
        return bool(option_measurements.intersection(_measurement_pairs(instruction)))

    option_count = _count_amount(option)
    if option_count is not None:
        return option_count in _requested_cardinal_amounts(instruction)

    return False


def _budget(instruction: str) -> Optional[float]:
    match = _BUDGET_RE.search(instruction)
    if match is None:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _normalise_match_token(token: str) -> str:
    lowered = str(token).lower()
    if lowered == "mens":
        return "men"
    if len(lowered) > 4 and lowered.endswith("s") and not lowered.endswith("ss"):
        return lowered[:-1]
    return lowered


def _choose_result(asins: Sequence[str], observation: str, instruction: str) -> str:
    parts = [part.strip() for part in str(observation).split("[SEP]")]
    instruction_terms = {
        _normalise_match_token(term) for term in _significant_terms(instruction)
    }
    budget = _budget(instruction)
    scored: List[Tuple[float, int, str]] = []

    lower_parts = [part.lower() for part in parts]
    for position, asin in enumerate(asins):
        try:
            part_index = lower_parts.index(asin.lower())
        except ValueError:
            title = ""
            price_text = ""
        else:
            title = parts[part_index + 1] if part_index + 1 < len(parts) else ""
            price_text = parts[part_index + 2] if part_index + 2 < len(parts) else ""

        title_terms = {
            _normalise_match_token(token)
            for token in _basic_words(title)
            if len(token) >= 3 and token not in _STOP_WORDS
        }
        overlap = len(instruction_terms.intersection(title_terms))
        precision = float(overlap) / max(1, len(title_terms))
        score = float(overlap * 10) + precision * 10.0

        if budget is not None:
            price = _first_price(price_text)
            if price is not None:
                score += 3.0 if price <= budget else -1000.0

        scored.append((score, -position, asin))

    scored.sort(reverse=True)
    return scored[0][2]


def _first_price(text: str) -> Optional[float]:
    for match in _PRICE_RE.finditer(text):
        try:
            return float(match.group(1))
        except ValueError:
            continue
    return None
