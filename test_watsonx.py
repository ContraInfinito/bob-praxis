"""
Praxis — watsonx.ai connectivity smoke test
Sends one prompt to Granite and prints the response.
If this runs cleanly, watsonx.ai is ready for the hackathon.
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load .env file from the same directory
load_dotenv()

API_KEY = os.getenv("WATSONX_API_KEY")
PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")
ENDPOINT_URL = os.getenv("WATSONX_ENDPOINT_URL", "https://us-south.ml.cloud.ibm.com")

# Hard-fail if any value is missing — better than a cryptic 401 later
missing = [k for k, v in {
    "WATSONX_API_KEY": API_KEY,
    "WATSONX_PROJECT_ID": PROJECT_ID,
    "WATSONX_ENDPOINT_URL": ENDPOINT_URL,
}.items() if not v]
if missing:
    sys.exit(f"Missing env vars: {missing}. Set them in .env and retry.")


def get_iam_token(api_key: str) -> str:
    """Exchange the IBM Cloud API key for a short-lived IAM access token."""
    resp = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": api_key,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def call_granite(token: str, prompt: str) -> str:
    """Send a prompt to a Granite model via the watsonx.ai text generation API."""
    url = f"{ENDPOINT_URL}/ml/v1/text/generation?version=2023-05-29"
    payload = {
        "input": prompt,
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": 100,
            "min_new_tokens": 1,
            "repetition_penalty": 1.0,
        },
        "model_id": "ibm/granite-3-8b-instruct",
        "project_id": PROJECT_ID,
    }
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json=payload,
        timeout=60,
    )
    if not resp.ok:
        print(f"  DEBUG: watsonx response status = {resp.status_code}")
        print(f"  DEBUG: watsonx response body = {resp.text}")
    resp.raise_for_status()
    return resp.json()["results"][0]["generated_text"]


if __name__ == "__main__":
    print("Step 1: Requesting IAM token...")
    token = get_iam_token(API_KEY)
    print("IAM token acquired")

    print("Step 2: Calling Granite with a one-line prompt...")
    prompt = "In one sentence, what is the practical application of theory?"
    result = call_granite(token, prompt)
    print(f"Granite responded:\n\n{result}\n")

    print("watsonx.ai is ready. Proceed to Phase 0.")