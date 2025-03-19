import os
from dotenv import load_dotenv

load_dotenv()

user = os.getenv("MATCH_USER_NAME")
password = os.getenv("PASS_WORD")

if __name__ == "__main__":
    print(f"Username: {user}")
    print(f"Password: {password}")