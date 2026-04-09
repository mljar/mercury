import logging
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
from typing import Dict, Iterable, List, Optional

log = logging.getLogger(__name__)

_runtime_url_params: Dict[str, List[str]] = {}


def set_runtime_url_params(params: Optional[Dict[str, Iterable[str]]]) -> None:
    """
    Store URL query params for the current Mercury runtime.

    Expected input shape:
        {
            "name": ["alice"],
            "color": ["red", "blue"],
        }

    Invalid values are ignored silently to keep this helper resilient.
    """
    global _runtime_url_params

    if not params:
        _runtime_url_params = {}
        return

    normalized: Dict[str, List[str]] = {}
    for key, values in params.items():
        if key is None:
            continue

        safe_key = str(key)
        if isinstance(values, (str, bytes)):
            normalized[safe_key] = [str(values)]
            continue

        try:
            normalized[safe_key] = [str(value) for value in values if value is not None]
        except TypeError:
            normalized[safe_key] = [str(values)]

    _runtime_url_params = normalized


def clear_runtime_url_params() -> None:
    """Remove all runtime URL params."""
    global _runtime_url_params
    _runtime_url_params = {}


def get_runtime_url_params() -> Dict[str, List[str]]:
    """Return a copy of currently stored runtime URL params."""
    return {key: list(values) for key, values in _runtime_url_params.items()}


def get_url_param_values(url_key: str) -> List[str]:
    """Return all values for a given URL key."""
    if not url_key:
        return []
    return list(_runtime_url_params.get(url_key, []))


def get_url_param_value(url_key: str) -> Optional[str]:
    """Return the first URL param value for a given key, if present."""
    values = get_url_param_values(url_key)
    if not values:
        return None
    return values[0]


def resolve_text_value(
    value: str = "",
    url_key: str = "",
    warn: bool = True,
) -> str:
    """
    Resolve initial text value using runtime URL params.

    Priority:
    1. first URL param value for ``url_key`` if present
    2. provided ``value``
    """
    if not url_key:
        return value

    url_value = get_url_param_value(url_key)
    if url_value is None:
        return value

    try:
        resolved = str(url_value)
        if not resolved.strip():
            if warn:
                log.warning(
                    "URL param %r is empty. Falling back to widget value.",
                    url_key,
                )
            return value
        return resolved
    except Exception as exc:
        if warn:
            log.warning(
                "Failed to read URL param %r. Falling back to widget value. Error: %s",
                url_key,
                exc,
            )
        return value


def resolve_number_value(
    value: float,
    url_key: str = "",
    min_value: float = 0.0,
    max_value: float = 100.0,
    step: float = 1.0,
    warn: bool = True,
) -> float:
    """
    Resolve initial numeric value using runtime URL params.

    Rules:
    1. empty / missing / invalid URL param -> fallback to ``value``
    2. values below min clamp to ``min_value``
    3. values above max clamp to ``max_value``
    4. in-range values snap to the nearest ``step`` from ``min_value``
    5. ties snap upward
    """
    if not url_key:
        return value

    url_value = get_url_param_value(url_key)
    if url_value is None:
        return value

    if not str(url_value).strip():
        if warn:
            log.warning(
                "URL param %r is empty. Falling back to widget value.",
                url_key,
            )
        return value

    try:
        val_dec = Decimal(str(url_value).strip())
        min_dec = Decimal(str(min_value))
        max_dec = Decimal(str(max_value))
        step_dec = Decimal(str(step))
    except (InvalidOperation, ValueError) as exc:
        if warn:
            log.warning(
                "Failed to parse numeric URL param %r=%r. Falling back to widget value. Error: %s",
                url_key,
                url_value,
                exc,
            )
        return value

    if step_dec <= 0:
        step_dec = Decimal("1")

    if min_dec > max_dec:
        min_dec, max_dec = max_dec, min_dec

    if val_dec <= min_dec:
        return float(min_dec)
    if val_dec >= max_dec:
        return float(max_dec)

    offset = val_dec - min_dec
    quotient_floor = (offset / step_dec).to_integral_value(rounding=ROUND_FLOOR)
    lower = min_dec + quotient_floor * step_dec
    upper = lower + step_dec

    if upper > max_dec:
        upper = max_dec
    if lower < min_dec:
        lower = min_dec

    lower_diff = abs(val_dec - lower)
    upper_diff = abs(upper - val_dec)
    snapped = upper if upper_diff <= lower_diff else lower

    if snapped < min_dec:
        snapped = min_dec
    if snapped > max_dec:
        snapped = max_dec

    return float(snapped)


def resolve_select_value(
    value: str = "",
    url_key: str = "",
    choices: Optional[List[str]] = None,
    warn: bool = True,
) -> str:
    """
    Resolve initial select value using runtime URL params.

    Rules:
    1. missing / empty URL param -> fallback to ``value``
    2. URL value must exactly match one of ``choices``
    3. invalid URL value -> fallback to ``value``
    """
    if not url_key:
        return value

    url_value = get_url_param_value(url_key)
    if url_value is None:
        return value

    resolved = str(url_value)
    if not resolved.strip():
        if warn:
            log.warning(
                "URL param %r is empty. Falling back to widget value.",
                url_key,
            )
        return value

    available_choices = choices or []
    lowered_to_choices: Dict[str, List[str]] = {}
    for choice in available_choices:
        lowered_to_choices.setdefault(choice.lower(), []).append(choice)

    matches = lowered_to_choices.get(resolved.lower(), [])
    if len(matches) == 1:
        return matches[0]

    if len(matches) > 1:
        if warn:
            log.warning(
                "URL param %r=%r matches multiple widget choices case-insensitively. Falling back to widget value.",
                url_key,
                resolved,
            )
        return value

    if resolved not in available_choices:
        if warn:
            log.warning(
                "URL param %r=%r is not present in widget choices. Falling back to widget value.",
                url_key,
                resolved,
            )
        return value
    return resolved


def resolve_multiselect_value(
    value: Optional[List[str]] = None,
    url_key: str = "",
    choices: Optional[List[str]] = None,
    warn: bool = True,
) -> List[str]:
    """
    Resolve initial multiselect value using runtime URL params.

    Rules:
    1. read all values for ``url_key``
    2. ignore empty values
    3. keep only values present in ``choices``
    4. if at least one valid value remains, it wins over ``value``
    5. otherwise fall back to ``value``
    """
    fallback = list(value or [])
    if not url_key:
        return fallback

    raw_values = get_url_param_values(url_key)
    if not raw_values:
        return fallback

    available_choices = choices or []
    lowered_to_choices: Dict[str, List[str]] = {}
    for choice in available_choices:
        lowered_to_choices.setdefault(choice.lower(), []).append(choice)

    non_empty_values = [str(v) for v in raw_values if str(v).strip()]
    valid_values: List[str] = []
    for raw_value in non_empty_values:
        matches = lowered_to_choices.get(raw_value.lower(), [])
        if len(matches) == 1:
            valid_values.append(matches[0])
        elif len(matches) > 1 and warn:
            log.warning(
                "URL param %r=%r matches multiple widget choices case-insensitively. Ignoring this value.",
                url_key,
                raw_value,
            )

    if valid_values:
        deduplicated_values = list(dict.fromkeys(valid_values))
        return deduplicated_values

    if warn:
        log.warning(
            "URL params for %r do not contain any valid widget choices. Falling back to widget value.",
            url_key,
        )
    return fallback


def resolve_integer_value(
    value: int,
    url_key: str = "",
    min_value: int = 0,
    max_value: int = 100,
    warn: bool = True,
) -> int:
    """
    Resolve initial integer value using runtime URL params.

    Rules:
    1. missing / empty / invalid URL param -> fallback to ``value``
    2. only integer strings are accepted
    3. values below min clamp to ``min_value``
    4. values above max clamp to ``max_value``
    """
    if not url_key:
        return value

    url_value = get_url_param_value(url_key)
    if url_value is None:
        return value

    resolved = str(url_value).strip()
    if not resolved:
        if warn:
            log.warning(
                "URL param %r is empty. Falling back to widget value.",
                url_key,
            )
        return value

    if resolved[0] in {"+", "-"}:
        digits = resolved[1:]
    else:
        digits = resolved

    if not digits.isdigit():
        if warn:
            log.warning(
                "URL param %r=%r is not a valid integer. Falling back to widget value.",
                url_key,
                resolved,
            )
        return value

    parsed = int(resolved)
    if parsed < min_value:
        return min_value
    if parsed > max_value:
        return max_value
    return parsed


def resolve_boolean_value(
    value: bool,
    url_key: str = "",
    warn: bool = True,
) -> bool:
    """
    Resolve initial boolean value using runtime URL params.

    Rules:
    1. missing / empty / invalid URL param -> fallback to ``value``
    2. only ``true`` and ``false`` are accepted (case-insensitive)
    """
    if not url_key:
        return value

    url_value = get_url_param_value(url_key)
    if url_value is None:
        return value

    resolved = str(url_value).strip().lower()
    if not resolved:
        if warn:
            log.warning(
                "URL param %r is empty. Falling back to widget value.",
                url_key,
            )
        return value

    if resolved == "true":
        return True
    if resolved == "false":
        return False

    if warn:
        log.warning(
            "URL param %r=%r is not a valid boolean. Falling back to widget value.",
            url_key,
            url_value,
        )
    return value
