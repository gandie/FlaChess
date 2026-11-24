from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from app.pairing.types import PairingParticipant


def seed_order_key(participant: PairingParticipant) -> tuple[int, int]:
    return participant.seed_position, participant.participant_id


def standings_order_key(
    participant: PairingParticipant,
) -> tuple[Decimal, ...]:
    return (
        -participant.points,
        *(-value for value in participant.ranking_values),
        Decimal(participant.seed_position),
        Decimal(participant.participant_id),
    )


def downward_float_order_key(
    participant: PairingParticipant,
) -> tuple[int, int]:
    return -participant.seed_position, participant.participant_id


def order_by_seed(
    participants: Iterable[PairingParticipant],
) -> tuple[PairingParticipant, ...]:
    return tuple(sorted(participants, key=seed_order_key))


def order_by_standings(
    participants: Iterable[PairingParticipant],
) -> tuple[PairingParticipant, ...]:
    return tuple(sorted(participants, key=standings_order_key))


def order_for_downward_float(
    participants: Iterable[PairingParticipant],
) -> tuple[PairingParticipant, ...]:
    return tuple(sorted(participants, key=downward_float_order_key))

