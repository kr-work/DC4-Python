import asyncio
import json
import logging
import pathlib
from datetime import datetime
from uuid import UUID
from uuid6 import uuid7

import aiohttp
import numpy as np
import requests
from aiohttp import BasicAuth
from requests.auth import HTTPBasicAuth
from sseclient import SSEClient

from dcclient.load_secrets import user, password
from dcclient.receive_database import (
    CoordinateDataSchema,
    ScoreSchema,
    StateSchema,
)
from dcclient.send_database import (
    ClientDataModel,
    MatchModel,
    MatchNameModel,
    PhysicalSimulatorModel,
    PlayerModel,
    ScoreModel,
    ShotInfoModel,
    StateModel,
    TeamModel,
    TournamentModel,
)

TEAM_INFO_URL = "http://localhost:10000/store_team_config"
SHOT_INFO_URL = "http://localhost:10000/receive_shot_info"
RECEIVE_STATE_URL = "http://localhost:10000/receive_state_info"

# ログファイルの保存先ディレクトリを指定
par_dir = pathlib.Path(__file__).parents[1]
log_dir = par_dir / "logs"

current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file_name = f"dc3_5_{current_time}.log"
log_file_path = log_dir / log_file_name


class DCClient:
    def __init__(self, log_level: int = logging.INFO, match_team_name: MatchNameModel = MatchNameModel.team1):
        self.logger = logging.getLogger("DC_Client")
        self.logger.propagate = False
        self.logger.setLevel(log_level)

        formatter = logging.Formatter(
            "%(asctime)s, %(name)s : %(levelname)s - %(message)s"
        )
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8", mode="w")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        st_handler = logging.StreamHandler()
        st_handler.setFormatter(formatter)
        self.logger.addHandler(st_handler)

        self.match_team_name = match_team_name
        self.logger.debug(f"user: {user}, password: {password}")

    async def send_team_info(self, match_id: UUID, team_info: TeamModel):
        async with aiohttp.ClientSession(auth=BasicAuth(login=user, password=password)) as session:
            async with session.post(
                url=TEAM_INFO_URL,
                params={"match_id": match_id,
                        "expected_match_team_name": self.match_team_name.value},
                json=team_info.model_dump(),
            ) as response:
                if response.status == 200:
                    self.logger.info("Team information successfully sent.")
                    self.match_team_name = await response.json()
                    print(f"team_name: {self.match_team_name}")
                elif response.status == 401:
                    self.logger.error(f"response: {response}")
                    self.logger.error("Unauthorized access. Please check your credentials.")
                else:
                    self.logger.error("Failed to send team information.")

    async def send_shot_info(self, match_id: UUID, shot_info: ShotInfoModel):
        requests.post(
            url=SHOT_INFO_URL,
            params={"match_id": match_id, "shot_info": shot_info.model_dump_json()},
            auth=HTTPBasicAuth(username=user, password=password),
        )

    async def receive_state_data(self, match_id: UUID):
        response = requests.get(
            url=RECEIVE_STATE_URL,
            params=match_id,
            auth=HTTPBasicAuth(username=user, password=password),
        )
        state_data = SSEClient(response)

        state_data = await asyncio.wait_for(self.websocket.recv(), timeout=50.0)
        state_data = json.loads(state_data)

        stone_coordinate_data = state_data.get("stone_coordinate", {}).get(
            "stone_coordinate_data"
        )
        if isinstance(stone_coordinate_data, dict):
            for team, coords in stone_coordinate_data.items():
                stone_coordinate_data[team] = [
                    CoordinateDataSchema(**coord) for coord in coords
                ]

        # Convert score to the appropriate format
        score_data = state_data.get("score", {})
        if isinstance(score_data, dict):
            state_data["score"] = ScoreSchema(**score_data)
        # self.logger.info(f"state_data.stone_coordinate: {state_data.stone_coordinate}")

        self.state_data = StateSchema(**state_data)
        # self.logger.info(f"Received state_data: {self.state_data}")

    async def send_shot_info(
        self,
        translation_velocity: float,
        angular_velocity_sign: int,
        shot_angle: float,
        angular_velocity=np.pi / 2,
    ):
        shot_info = ShotInfoModel(
            translation_velocity=translation_velocity,
            angular_velocity_sign=angular_velocity_sign,
            angular_velocity=angular_velocity,
            shot_angle=shot_angle,
        )
        if self.websocket.state == websockets.protocol.State.OPEN:
            await self.websocket.send(shot_info.model_dump_json())
        else:
            self.logger.error("WebSocket connection is closed. Cannot send shot_info.")

    def get_end_number(self):
        return self.state_data.end_number

    def get_shot_number(self):
        return self.state_data.total_shot_number

    def get_score(self):
        score = self.state_data.score
        return score.first_team_score, score.second_team_score

    def get_next_team(self):
        return self.state_data.next_shot_team

    def get_winner_team(self):
        winner_team = self.state_data.winner_team
        return winner_team

    def get_stone_coordinates(self):
        # Access the nested data properly from the StoneCoordinateSchema instance
        stone_coordinate_data = self.state_data.stone_coordinate.stone_coordinate_data
        # Extract coordinates for each team
        team0_stone_coordinate = stone_coordinate_data.get("team0", [])
        team1_stone_coordinate = stone_coordinate_data.get("team1", [])
        team0_coordinates = [(coord.x, coord.y) for coord in team0_stone_coordinate]
        team1_coordinates = [(coord.x, coord.y) for coord in team1_stone_coordinate]
        return team0_coordinates, team1_coordinates


async def main():
    client = WebsocketClient()
    with open("match_id.json", "r") as f:
        match_id = json.load(f)
    client.logger.info(f"match_id: {match_id}")
    with open("team1_config.json", "r") as f:
        data = json.load(f)
    client_data = TeamModel(**data)
    # match_id = requests.get(f"{URL}/get_match_id", json=data).json()
    # logging.info(f"match_id: {match_id}")

    # team_name = asyncio.run(client.initialize(match_id))
    # logging.info(f"team_name: {team_name}")

    team_name = await client.initialize(match_id, 1, client_data)

    # Start match
    while True:
        # Receive state data
        await client.receive_state_data()

        if (winner_team := client.get_winner_team()) is not None:
            client.logger.info(f"Winner: {winner_team}")
            break

        next_shot_team = client.get_next_team()
        client.logger.info(f"next_shot_team: {next_shot_team}")

        if next_shot_team == team_name:
            translation_velocity = 2.371
            angular_velocity_sign = -1
            angular_velocity = np.pi / 2
            shot_angle = 91.7
            await client.send_shot_info(
                translation_velocity,
                angular_velocity_sign,
                angular_velocity,
                shot_angle,
            )

    await client.disconnect_websocket()


if __name__ == "__main__":
    asyncio.run(main())
