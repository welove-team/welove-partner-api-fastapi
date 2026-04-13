from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response

from app.middleware.verify_request import encrypt_jwe, verify_request
from app.models import VerifyMemberRequest, VerifyMemberResponse

router = APIRouter()

# 교인 데이터 타입
type MemberData = dict[str, bool | str | None]

# ─────────────────────────────────────────────────────────────
# TODO: 아래 더미 데이터를 실제 교적 DB 조회 로직으로 교체하세요.
#
# 교적 DB 연동 예시 (SQLAlchemy):
#   member = db.query(Member).filter(
#       Member.phone == body.phoneNumber,
#       Member.name == body.name
#   ).first()
# ─────────────────────────────────────────────────────────────
MEMBERS: dict[str, MemberData] = {
    "01012345678": {"name": "김철수", "leadership": True,  "community": "갈렙공동체",    "group": "3목장"},
    "01098765432": {"name": "이영희", "leadership": False, "community": "여호수아공동체", "group": "1목장"},
    "01011112222": {"name": "박민수", "leadership": False, "community": None,            "group": None   },
}


@router.post(
    "/verify-member",
    dependencies=[Depends(verify_request)],
)
async def verify_member(request: Request) -> Response:
    """
    POST /verify-member

    welove 서버가 사용자의 교회 소속을 확인하기 위해 호출합니다.
    Basic Auth 검증 후, JWE 암호화된 요청 본문을 복호화하여 처리합니다.

    Request body: JWE compact serialization (평문 JSON: { phoneNumber: str, name: str })
    Response:     JWE compact serialization (평문 JSON: { leadership: bool, community: str | None, group: str | None })
    Content-Type: application/jose
    """
    # 복호화된 body에서 요청 데이터 파싱
    decrypted = request.state.decrypted_body
    try:
        body = VerifyMemberRequest(**decrypted)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail={"error": "INVALID_REQUEST", "message": "요청 본문의 형식이 올바르지 않습니다."},
        )

    # ─────────────────────────────────────────────────────────────
    # TODO: 여기에 교회 교적 DB 조회 로직을 구현하세요.
    #       현재는 테스트용 더미 데이터를 사용합니다.
    # ─────────────────────────────────────────────────────────────
    member = MEMBERS.get(body.phoneNumber)

    if not member or member["name"] != body.name:
        raise HTTPException(
            status_code=404,
            detail={"error": "MEMBER_NOT_FOUND", "message": "교인 정보를 찾을 수 없습니다."},
        )

    result = VerifyMemberResponse(
        leadership=bool(member["leadership"]),
        community=member["community"],  # type: ignore[arg-type]
        group=member["group"],          # type: ignore[arg-type]
    )

    # 응답을 JWE로 암호화
    jwe_token = encrypt_jwe(result.model_dump(), request.state.jwe_key)

    return Response(
        content=jwe_token,
        media_type="application/jose",
    )
