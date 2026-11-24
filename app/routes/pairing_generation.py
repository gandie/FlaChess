from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.pairing.generation import (
    PairingPreview,
    generate_next_round,
    preview_next_round,
)
from app.pairing.generation_state import (
    PairingGenerationConflict,
    PairingGenerationError,
    PairingGenerationNotFound,
)
from app.pairing.types import PairingFormat, PlannedOutcomeType
from app.pairing_generation_schemas import (
    PairingConfirmationCommand,
    PairingGameRead,
    PairingOutcomeRead,
    PairingPlanRead,
    PairingSeedRead,
)

router = APIRouter()


def pairing_error(error: PairingGenerationError) -> HTTPException:
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    if isinstance(error, PairingGenerationConflict):
        status_code = status.HTTP_409_CONFLICT
    if isinstance(error, PairingGenerationNotFound):
        status_code = status.HTTP_404_NOT_FOUND
    return HTTPException(status_code=status_code, detail=str(error))


def pairing_policy_labels(pairing_format: PairingFormat) -> list[str]:
    if pairing_format is PairingFormat.ROUND_ROBIN:
        return [
            "stored_seed_order",
            "single_round_robin",
            "fixed_member_schedule",
            "balanced_colors",
        ]
    if pairing_format is PairingFormat.SWISS:
        return [
            "stored_seed_order",
            "fide_dutch_score_groups",
            "repeat_opponent_avoidance",
            "controlled_downward_float",
            "one_swiss_bye_max",
            "balanced_colors",
        ]
    return [
        "stored_seed_order",
        "standard_seeded_bracket",
        "decisive_predecessor_advancement",
        "balanced_colors",
    ]


def pairing_warnings(preview: PairingPreview) -> list[str]:
    warnings: list[str] = []
    for outcome in preview.plan.outcomes:
        if outcome.outcome_type is not PlannedOutcomeType.BYE:
            warnings.append(
                f"Participant {outcome.participant_id} is marked "
                f"{outcome.outcome_type.value}.",
            )
            continue
        if preview.pairing_format is PairingFormat.SWISS:
            warnings.append(
                f"Participant {outcome.participant_id} receives a one-point Swiss bye.",
            )
        else:
            warnings.append(
                f"Participant {outcome.participant_id} receives a structural "
                f"{preview.pairing_format.value} bye without an awarded score.",
            )
    return warnings


def pairing_response(
    preview: PairingPreview,
    round_id: int | None = None,
) -> PairingPlanRead:
    return PairingPlanRead(
        section_id=preview.section_id,
        round_id=round_id,
        target_round=preview.plan.round_number,
        format=preview.pairing_format,
        planned_round_count=preview.planned_round_count,
        calculated_round_count=preview.calculated_round_count,
        games=[
            PairingGameRead(
                white_participant_id=game.white_participant_id,
                black_participant_id=game.black_participant_id,
            )
            for game in preview.plan.games
        ],
        outcomes=[
            PairingOutcomeRead(
                participant_id=outcome.participant_id,
                outcome_type=outcome.outcome_type,
                score_awarded=outcome.score_awarded,
            )
            for outcome in preview.plan.outcomes
        ],
        seed_order=[
            PairingSeedRead(
                participant_id=participant.participant_id,
                seed_position=participant.seed_position,
            )
            for participant in preview.seed_order
        ],
        policy_labels=pairing_policy_labels(preview.pairing_format),
        warnings=pairing_warnings(preview),
    )


@router.get(
    "/tournament-sections/{section_id}/pairing/preview",
    response_model=PairingPlanRead,
    tags=["Tournament Sections"],
)
async def preview_pairing(
    section_id: int,
    session: AsyncSession = Depends(get_session),
) -> PairingPlanRead:
    try:
        preview = await preview_next_round(section_id, session)
    except PairingGenerationError as error:
        raise pairing_error(error) from error
    return pairing_response(preview)


@router.post(
    "/tournament-sections/{section_id}/pairing/confirm",
    response_model=PairingPlanRead,
    tags=["Tournament Sections"],
)
async def confirm_pairing(
    section_id: int,
    payload: PairingConfirmationCommand,
    session: AsyncSession = Depends(get_session),
) -> PairingPlanRead:
    try:
        preview = await preview_next_round(
            section_id,
            session,
            payload.expected_round_number,
        )
        generated = await generate_next_round(
            section_id,
            session,
            payload.expected_round_number,
        )
    except PairingGenerationError as error:
        raise pairing_error(error) from error
    return pairing_response(
        replace(preview, plan=generated.plan),
        generated.round.id,
    )
from dataclasses import replace

