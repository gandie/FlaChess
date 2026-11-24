from pydantic import BaseModel, Field


class PlayerSummary(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class TournamentParticipantRegistration(BaseModel):
    player_id: int = Field(gt=0)


class TournamentParticipantSummary(BaseModel):
    registration_id: int
    player_id: int
    player_name: str

    model_config = {"from_attributes": True}
