from __future__ import annotations

from app.pairing.types import PairingFormat


class RoundCountError(ValueError):
    pass


def calculate_swiss_round_count(
    participant_count: int,
    planned_round_count: int,
) -> int:
    validate_pairable_field(participant_count)
    return validate_positive_integer(planned_round_count, "planned round count")


def calculate_round_robin_round_count(participant_count: int) -> int:
    count = validate_pairable_field(participant_count)
    return count - 1 if count % 2 == 0 else count


def calculate_knockout_round_count(participant_count: int) -> int:
    count = validate_pairable_field(participant_count)
    bracket_size = 1 << (count - 1).bit_length()
    return bracket_size.bit_length() - 1


def validate_planned_round_count(
    pairing_format: PairingFormat,
    participant_count: int,
    planned_round_count: int,
) -> int:
    planned = validate_positive_integer(planned_round_count, "planned round count")
    if pairing_format is PairingFormat.SWISS:
        return calculate_swiss_round_count(participant_count, planned)
    calculated = (
        calculate_round_robin_round_count(participant_count)
        if pairing_format is PairingFormat.ROUND_ROBIN
        else calculate_knockout_round_count(participant_count)
    )
    if planned != calculated:
        raise RoundCountError(
            f"{pairing_format.value} requires {calculated} rounds; "
            f"received {planned}.",
        )
    return calculated


def validate_pairable_field(participant_count: int) -> int:
    count = validate_positive_integer(participant_count, "participant count")
    if count < 2:
        raise RoundCountError("Pairing requires at least two participants.")
    return count


def validate_positive_integer(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise RoundCountError(f"{name.capitalize()} must be a positive integer.")
    return value

