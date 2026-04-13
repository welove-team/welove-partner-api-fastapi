import base64
import hmac
import json
import os
from typing import Annotated

from fastapi import Header, HTTPException, Request
from jwcrypto import jwe, jwk


def key_from_secret(secret_key: str) -> jwk.JWK:
    """Secret Key(ASCII 32바이트)를 그대로 32바이트 JWK로 변환합니다.

    welove가 발급하는 Secret Key는 정확히 32바이트 문자열이며,
    별도 해싱/변환 없이 그대로 대칭키로 사용합니다.
    """
    key_bytes = secret_key.encode("utf-8")
    if len(key_bytes) != 32:
        raise ValueError(f"Secret Key는 정확히 32바이트여야 합니다. (현재 {len(key_bytes)}바이트)")
    return jwk.JWK(kty="oct", k=base64.urlsafe_b64encode(key_bytes).decode().rstrip("="))


def decrypt_jwe(token: str, key: jwk.JWK) -> dict:
    """JWE compact serialization 토큰을 복호화하여 JSON 딕셔너리로 반환합니다."""
    jweobj = jwe.JWE()
    jweobj.deserialize(token)
    jweobj.decrypt(key)
    return json.loads(jweobj.payload.decode())


def encrypt_jwe(data: dict, key: jwk.JWK) -> str:
    """딕셔너리를 JWE compact serialization으로 암호화합니다. (alg=dir, enc=A256GCM)"""
    payload = json.dumps(data, ensure_ascii=False).encode()
    protected = {"alg": "dir", "enc": "A256GCM"}
    jweobj = jwe.JWE(payload, json.dumps(protected))
    jweobj.add_recipient(key)
    return jweobj.serialize(compact=True)


async def verify_request(
    request: Request,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> None:
    """
    welove 서버 요청 검증 의존성 함수

    두 가지를 순서대로 처리합니다:
    1. API Key 검증 — `X-API-Key` 헤더로 파트너 포털에서 발급받은 API Key 확인
    2. JWE 복호화 — 요청 본문(JWE compact serialization)을 Secret Key로 복호화해 request.state에 저장

    Secret Key는 헤더로 전송되지 않고, 오직 JWE 암복호화 키로만 사용됩니다.
    """
    # 1. API Key 검증
    expected_api_key = os.environ.get("WELOVE_API_KEY", "")
    if not x_api_key or not expected_api_key or not hmac.compare_digest(x_api_key, expected_api_key):
        raise HTTPException(
            status_code=401,
            detail={"error": "UNAUTHORIZED", "message": "X-API-Key 헤더가 없거나 올바르지 않습니다."},
        )

    # 2. JWE 복호화
    body_bytes = await request.body()
    if not body_bytes:
        raise HTTPException(
            status_code=400,
            detail={"error": "DECRYPTION_FAILED", "message": "요청 본문이 비어 있습니다."},
        )

    secret_key = os.environ.get("WELOVE_SECRET", "")
    try:
        key = key_from_secret(secret_key)
        decrypted = decrypt_jwe(body_bytes.decode("utf-8"), key)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail={"error": "DECRYPTION_FAILED", "message": "JWE 복호화에 실패했습니다."},
        )

    # 복호화된 body와 JWK를 request.state에 저장
    request.state.decrypted_body = decrypted
    request.state.jwe_key = key
