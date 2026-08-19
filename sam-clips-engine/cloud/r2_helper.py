"""Fetch R2 + ElevenLabs creds from Infisical (universal auth) and expose helpers.

Reuses the proven pattern from .claude/workspace/sam-outliers/outlier_radar.py.
Never prints secret values. Importable: provides infisical_secret(), r2_client(), BUCKET.
"""
import os, sys, json
import requests, urllib3
urllib3.disable_warnings()

PROJECT = "7ba7c8cc-b283-4830-bd04-2d94f48377c1"  # "Claude Secrets Vault"
ENVS = ["dev", "prod", "staging"]
S = requests.Session(); S.verify = False
_TOKEN = None


def _login():
    global _TOKEN
    if _TOKEN:
        return _TOKEN
    cid = os.environ["INFISICAL_UNIVERSAL_AUTH_CLIENT_ID"]
    csec = os.environ["INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET"]
    _TOKEN = S.post("https://app.infisical.com/api/v1/auth/universal-auth/login",
                    data={"clientId": cid, "clientSecret": csec}).json()["accessToken"]
    return _TOKEN


def infisical_secret(key, env="dev", path="/"):
    at = _login()
    r = S.get(f"https://app.infisical.com/api/v3/secrets/raw/{key}"
              f"?workspaceId={PROJECT}&environment={env}&secretPath={path}",
              headers={"Authorization": f"Bearer {at}"})
    if r.status_code != 200:
        return None
    return r.json()["secret"]["secretValue"].strip()


def load_r2_env():
    """Populate os.environ with R2 + ELEVENLABS creds from Infisical (dev env).

    Falls back to leaving unresolved keys unset if Infisical auth isn't available
    (e.g. threads-cloud-engine reads R2 creds straight from the routine env and
    never sets INFISICAL_UNIVERSAL_AUTH_CLIENT_ID) rather than crashing callers
    that already have what they need via plain env vars.
    """
    wanted = ["R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY",
              "R2_BUCKET", "R2_ACCOUNT_ID", "ELEVENLABS_API_KEY", "SUNO_API_KEY",
              "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
    found = {}
    infisical_available = True
    for k in wanted:
        if os.environ.get(k):
            found[k] = "env"
            continue
        if not infisical_available:
            continue
        try:
            v = infisical_secret(k, "dev")
        except KeyError:
            infisical_available = False
            continue
        if v:
            os.environ[k] = v
            found[k] = "infisical"
    return found


def r2_client():
    import boto3
    from botocore.config import Config
    endpoint = os.environ.get("R2_ENDPOINT")
    if not endpoint and os.environ.get("R2_ACCOUNT_ID"):
        endpoint = f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com"
    endpoint = (endpoint or "").strip().strip("<>").strip()
    return boto3.client("s3", endpoint_url=endpoint,
                        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
                        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
                        region_name="auto", config=Config(signature_version="s3v4"))


BUCKET = None


def list_all(prefix=""):
    global BUCKET
    BUCKET = os.environ.get("R2_BUCKET", "verity-video")
    cli = r2_client()
    keys = []
    tok = None
    while True:
        kw = {"Bucket": BUCKET, "Prefix": prefix, "MaxKeys": 1000}
        if tok:
            kw["ContinuationToken"] = tok
        resp = cli.list_objects_v2(**kw)
        for o in resp.get("Contents", []):
            keys.append((o["Key"], o["Size"]))
        if resp.get("IsTruncated"):
            tok = resp.get("NextContinuationToken")
        else:
            break
    return keys


if __name__ == "__main__":
    found = load_r2_env()
    print("creds resolved:", {k: v for k, v in found.items()})
    prefix = sys.argv[1] if len(sys.argv) > 1 else ""
    keys = list_all(prefix)
    print(f"bucket={BUCKET} prefix={prefix!r} -> {len(keys)} objects")
    for k, sz in sorted(keys):
        print(f"  {sz/1e6:9.2f}MB  {k}")
