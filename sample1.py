import json
import asyncio
import numpy as np
import logging
import time

from dc_client import WebsocketClient
from send_database import TeamModel


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
        total_shot_number = client.get_shot_number()
        client.logger.info(f"client.get_shot_number(): {total_shot_number}")
        if total_shot_number < 16:

            next_shot_team = client.get_next_team()
            client.logger.info(f"next_shot_team: {next_shot_team}")

            # team0_coordinates, team1_coordinates = client.get_stone_coordinates()
            # print(f"team0_coordinates: {team0_coordinates}")
            # print(f"team1_coordinates: {team1_coordinates}")
            time.sleep(1)

            if next_shot_team == team_name:
                client.logger.info("my turn")
                translation_velocity = 2.371
                angular_velocity_sign = -1
                # angular_velocity = np.pi / 2
                shot_angle = 91.7
                await client.send_shot_info(
                    translation_velocity,
                    angular_velocity_sign,
                    shot_angle,
                    # angular_velocity,
                )
                client.logger.info("my turn end")

        elif total_shot_number == 16:
            if (winner_team := client.get_winner_team()) is not None:
                client.logger.info(f"Winner: {winner_team}")
                if winner_team == client.team_name:
                    print("You won")
                else:
                    print("You lost")
                break

    await client.disconnect_websocket()


if __name__ == "__main__":
    asyncio.run(main())
