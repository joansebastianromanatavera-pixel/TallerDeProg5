"""CRUD endpoints for gym members (5 endpoints)."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from gymflow.api.deps import get_db
from gymflow.api.schemas import ErrorOut, MemberCreate, MemberOut, MemberUpdate
from gymflow.models import Socio

router = APIRouter(prefix="/api/v1/members", tags=["Members"])

DbSession = Annotated[Session, Depends(get_db)]

# English API field -> Spanish ORM attribute
_FIELD_MAP = {"name": "nombre", "email": "email", "phone": "telefono", "active": "activo"}
_REQUIRED_FIELDS = {"name", "email", "active"}

_NOT_FOUND = {404: {"model": ErrorOut, "description": "Member not found."}}
_CONFLICT = {409: {"model": ErrorOut, "description": "Another member already uses this email."}}
_INVALID = {422: {"model": ErrorOut, "description": "Invalid request body or parameters."}}


def _get_member_or_404(db: Session, member_id: int) -> Socio:
    member = db.get(Socio, member_id)
    if member is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Member with id {member_id} was not found.")
    return member


def _ensure_email_available(db: Session, email: str, exclude_id: int | None = None) -> None:
    query = select(Socio.id).where(Socio.email == email)
    if exclude_id is not None:
        query = query.where(Socio.id != exclude_id)
    if db.scalar(query) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"A member with email '{email}' already exists.")


@router.post(
    "",
    response_model=MemberOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a member",
    description="Registers a new gym member. The email must be unique; the registration date is set automatically.",
    responses={201: {"description": "Member created."}, **_CONFLICT, **_INVALID},
)
def create_member(payload: MemberCreate, db: DbSession) -> Socio:
    email = payload.email.lower()
    _ensure_email_available(db, email)
    member = Socio(nombre=payload.name, email=email, telefono=payload.phone, activo=payload.active)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.get(
    "",
    response_model=list[MemberOut],
    summary="List members",
    description="Returns a paginated list of members ordered by id. Use `skip` and `limit` to paginate.",
    responses={200: {"description": "List of members."}, **_INVALID},
)
def list_members(
    db: DbSession,
    skip: Annotated[int, Query(ge=0, description="Number of records to skip.")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum number of records to return.")] = 20,
) -> list[Socio]:
    return list(db.scalars(select(Socio).order_by(Socio.id).offset(skip).limit(limit)))


@router.get(
    "/{member_id}",
    response_model=MemberOut,
    summary="Get a member",
    description="Returns a single member by its id.",
    responses={200: {"description": "Member found."}, **_NOT_FOUND, **_INVALID},
)
def get_member(member_id: int, db: DbSession) -> Socio:
    return _get_member_or_404(db, member_id)


@router.put(
    "/{member_id}",
    response_model=MemberOut,
    summary="Update a member",
    description="Updates the fields sent in the body. Fields that are not sent keep their current value.",
    responses={200: {"description": "Member updated."}, **_NOT_FOUND, **_CONFLICT, **_INVALID},
)
def update_member(member_id: int, payload: MemberUpdate, db: DbSession) -> Socio:
    member = _get_member_or_404(db, member_id)
    changes: dict[str, Any] = payload.model_dump(exclude_unset=True)
    if changes.get("email"):
        changes["email"] = changes["email"].lower()
        _ensure_email_available(db, changes["email"], exclude_id=member_id)
    for field, value in changes.items():
        if value is None and field in _REQUIRED_FIELDS:
            continue  # required columns cannot be cleared
        setattr(member, _FIELD_MAP[field], value)
    db.commit()
    db.refresh(member)
    return member


@router.delete(
    "/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a member",
    description="Deletes a member together with their memberships and routines.",
    responses={204: {"description": "Member deleted."}, **_NOT_FOUND, **_INVALID},
)
def delete_member(member_id: int, db: DbSession) -> Response:
    member = _get_member_or_404(db, member_id)
    db.delete(member)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
