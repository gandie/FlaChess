from app.admin_views.rounds import (
    GameAdmin,
    RoundParticipantAdmin,
    TournamentRoundAdmin,
)
from app.admin_views.sections import (
    SectionParticipantAdmin,
    SectionTiebreakAdmin,
)
from app.admin_views.standings import (
    SectionStandingAdmin,
    SectionStandingValueAdmin,
)
from app.admin_views.structure import (
    PlayerAdmin,
    TournamentAdmin,
    TournamentParticipantAdmin,
    TournamentPhaseAdmin,
    TournamentSectionAdmin,
)

__all__ = [
    "GameAdmin",
    "PlayerAdmin",
    "RoundParticipantAdmin",
    "SectionParticipantAdmin",
    "SectionStandingAdmin",
    "SectionStandingValueAdmin",
    "SectionTiebreakAdmin",
    "TournamentAdmin",
    "TournamentParticipantAdmin",
    "TournamentPhaseAdmin",
    "TournamentRoundAdmin",
    "TournamentSectionAdmin",
]
