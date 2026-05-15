"""
Praxis watsonx.ai Granite integration module.

Wraps the IBM watsonx.ai text generation API for Granite model inference.
Handles IAM token exchange and caching for the duration of one CLI run.
"""

import os
import sys
import requests
from dotenv import load_dotenv


# Module-level state: cached IAM token for the duration of one CLI run
_iam_token: str | None = None
_api_key: str = ""
_project_id: str = ""
_endpoint_url: str = ""


def _load_credentials() -> tuple[str, str, str]:
    """
    Load watsonx.ai credentials from environment variables.
    
    Loads .env file on first call and caches credentials for subsequent calls.
    
    Returns:
        Tuple of (api_key, project_id, endpoint_url)
        
    Raises:
        RuntimeError: If required credentials are missing
    """
    global _api_key, _project_id, _endpoint_url
    
    # Load credentials only once
    if not _api_key:
        load_dotenv()
        
        api_key_env = os.getenv("WATSONX_API_KEY")
        project_id_env = os.getenv("WATSONX_PROJECT_ID")
        
        # Validate required credentials
        if not api_key_env:
            raise RuntimeError(
                "Missing required environment variable: WATSONX_API_KEY. "
                "Set it in your .env file."
            )
        
        if not project_id_env:
            raise RuntimeError(
                "Missing required environment variable: WATSONX_PROJECT_ID. "
                "Set it in your .env file."
            )
        
        _api_key = api_key_env
        _project_id = project_id_env
        _endpoint_url = os.getenv("WATSONX_ENDPOINT_URL") or "https://us-south.ml.cloud.ibm.com"
    
    return _api_key, _project_id, _endpoint_url


def _get_iam_token(api_key: str) -> str:
    """
    Exchange an IBM Cloud API key for a short-lived IAM access token.
    
    Args:
        api_key: IBM Cloud API key
        
    Returns:
        IAM access token (valid for ~1 hour)
        
    Raises:
        requests.HTTPError: If token exchange fails
    """
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


def _ensure_token() -> str:
    """
    Ensure we have a valid IAM token, fetching one if needed.
    
    Caches the token in module-level state for reuse within one CLI run.
    
    Returns:
        IAM access token
        
    Raises:
        RuntimeError: If credentials are missing
        requests.HTTPError: If token exchange fails
    """
    global _iam_token
    
    if _iam_token is None:
        api_key, _, _ = _load_credentials()
        _iam_token = _get_iam_token(api_key)
    
    return _iam_token


def generate(prompt: str, max_tokens: int = 500) -> str:
    """
    Generate text using IBM watsonx.ai Granite model.
    
    Uses the Granite 3 8B Instruct model with greedy decoding. Caches IAM
    token for the duration of the CLI run (no expiry checking needed for
    short-lived processes).
    
    Args:
        prompt: Input text prompt for the model
        max_tokens: Maximum number of tokens to generate (default: 500)
        
    Returns:
        Generated text from the model
        
    Raises:
        RuntimeError: If credentials are missing
        requests.HTTPError: If the API request fails
    """
    # Ensure we have credentials and a token
    token = _ensure_token()
    _, project_id, endpoint_url = _load_credentials()
    
    # Build the API request
    url = f"{endpoint_url}/ml/v1/text/generation?version=2023-05-29"
    payload = {
        "input": prompt,
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": max_tokens,
            "min_new_tokens": 1,
            "repetition_penalty": 1.0,
        },
        "model_id": "ibm/granite-3-8b-instruct",
        "project_id": project_id,
    }
    
    # Make the request
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
    
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        # Include response body in error for debuggability
        error_body = ""
        try:
            error_body = resp.text
        except:
            pass
        raise requests.HTTPError(
            f"Granite API request failed: {e}\nResponse body: {error_body}"
        ) from e
    
    # Extract and return generated text
    return resp.json()["results"][0]["generated_text"]


if __name__ == "__main__":
    # Self-test: verify Granite connectivity
    try:
        response = generate("Reply with the single word: ready.", max_tokens=10)
        print(f"Granite responded: {response}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

# Made with Bob
