from __future__ import annotations

from decimal import Decimal

from app.pairing.types import (
    Color,
    ColorAllocationContext,
    ColorAssignment,
    PairingFormat,
    PairingParticipant,
)


class ColorAllocationError(ValueError):
    pass


def allocate_colors(
    first: PairingParticipant,
    second: PairingParticipant,
    context: ColorAllocationContext,
) -> ColorAssignment:
    validate_context(first, second, context)
    if (
        context.pairing_format is PairingFormat.SWISS
        and context.round_number == 1
    ):
        return allocate_first_swiss_round(first, second, context.pair_number)
    candidates = (
        ColorAssignment(first.participant_id, second.participant_id),
        ColorAssignment(second.participant_id, first.participant_id),
    )
    by_id = {
        first.participant_id: first,
        second.participant_id: second,
    }
    return min(
        candidates,
        key=lambda assignment: allocation_order_key(assignment, by_id),
    )


def allocate_first_swiss_round(
    first: PairingParticipant,
    second: PairingParticipant,
    pair_number: int,
) -> ColorAssignment:
    higher_seed = min(
        (first, second),
        key=lambda participant: (
            participant.seed_position,
            participant.participant_id,
        ),
    )
    lower_seed = second if higher_seed is first else first
    white, black = (
        (higher_seed, lower_seed)
        if pair_number % 2
        else (lower_seed, higher_seed)
    )
    return ColorAssignment(white.participant_id, black.participant_id)


def allocation_order_key(
    assignment: ColorAssignment,
    participants_by_id: dict[int, PairingParticipant],
) -> tuple[int, Decimal, int, int]:
    white = participants_by_id[assignment.white_participant_id]
    black = participants_by_id[assignment.black_participant_id]
    streak_violations = int(_creates_third_streak(white, Color.WHITE))
    streak_violations += int(_creates_third_streak(black, Color.BLACK))
    imbalance = abs(_balance_after(white, Color.WHITE))
    imbalance += abs(_balance_after(black, Color.BLACK))
    return (
        streak_violations,
        Decimal(imbalance),
        white.seed_position,
        white.participant_id,
    )


def validate_context(
    first: PairingParticipant,
    second: PairingParticipant,
    context: ColorAllocationContext,
) -> None:
    if first.participant_id == second.participant_id:
        raise ColorAllocationError("A participant cannot be paired with itself.")
    if context.round_number <= 0 or context.pair_number <= 0:
        raise ColorAllocationError("Round and pair numbers must be positive.")


def _creates_third_streak(
    participant: PairingParticipant,
    color: Color,
) -> bool:
    return (
        len(participant.color_history) >= 2
        and participant.color_history[-1] is color
        and participant.color_history[-2] is color
    )


def _balance_after(participant: PairingParticipant, color: Color) -> int:
    balance = sum(
        1 if prior_color is Color.WHITE else -1
        for prior_color in participant.color_history
    )
    return balance + (1 if color is Color.WHITE else -1)

