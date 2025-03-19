from pydantic import BaseModel, Json
from typing import List
from enum import Enum


class MatchModel(BaseModel):
    """To get match_id from server"""
    time_limit: int
    extra_end_time_limit: int
    standard_end_count: int
    match_name: str


class ScoreModel(BaseModel):
    first_team_score: List[int]
    second_team_score: List[int]


class PhysicalSimulatorModel(BaseModel):
    simulator_name: str


class TournamentModel(BaseModel):
    tournament_name: str


class ShotInfoModel(BaseModel):
    translation_velocity: float
    angular_velocity_sign: int
    angular_velocity: float | None
    shot_angle: float


class StateModel(BaseModel):
    end_number: int
    shot_number: int
    total_shot_number: int


class StoneCoordinates(BaseModel):
    stone_data: Json


class MatchNameModel(str, Enum):
    team0 = "team0"         # team0 is first attacker team at the first end
    team1 = "team1"         # team1 is sencond attacker team at the first end


class PlayerModel(BaseModel):
    max_velocity: float
    shot_dispersion_rate: float
    player_name: str


class TeamModel(BaseModel):
    use_default_config: bool
    team_name: str                  # your team name
    match_team_name: MatchNameModel = MatchNameModel.team1  # team0 or team1
    player1: PlayerModel
    player2: PlayerModel
    player3: PlayerModel
    player4: PlayerModel


class ClientDataModel(BaseModel):
    tournament: TournamentModel
    simulator: PhysicalSimulatorModel
    time_limit: int
    extra_end_time_limit: int
    standard_end_count: int
    match_name: str



