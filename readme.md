# New Client For Digital Curling

This is a new client for digital curling. It is a work in progress.

## Install requirements.txt
```bash
pip install -r requirements.txt
```

## How to use
In the "src.setting.json" file,  describe the information required for the match, such as the number of ends, simulators to be used, time limits, etc.
(Currently, “fcv1” is the only simulator available, so matches cannot be played on other simulators.)
After completing the settings in setting.json, enter the following command.
```bash
cd src
python match_maker.py
```
The above command should be entered when you want to start a new match.

The match_id will now be stored in match_id.json.
Next, you can configure the players who will play in that match in “src.team0_config.json” and “src.team1_config.json”. In addition, when playing with the same settings as in the tournament, you can set
```md
"use_default_config": true
``` 
If you want to create a unique team,

```md
"use_default_config": flase
``` 

After the above settings are in place, connect the client to the server by entering the following command

```bash
python sample0.py
```

When another terminal is opened and another client also connects to the server, the match begins.

```bash
cd src
python sample1.py
```