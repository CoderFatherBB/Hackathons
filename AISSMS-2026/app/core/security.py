from fastapi import Header, HTTPException

def require_role(roles: list[str]):
    def _dep(x_role: str | None = Header(default=None, alias="X-Role")):
        if x_role is None or x_role not in roles:
            raise HTTPException(status_code=403, detail="forbidden")
    return _dep
