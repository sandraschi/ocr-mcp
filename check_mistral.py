import os
import sys
from dotenv import load_dotenv


def check_env():
    load_dotenv()
    key = os.getenv("MISTRAL_API_KEY")
    if key:
        print(f"MISTRAL_API_KEY is SET (Length: {len(key)})")
        print(f"Key preview: {key[:4]}...")
    else:
        print("MISTRAL_API_KEY is NOT SET")


if __name__ == "__main__":
    check_env()
