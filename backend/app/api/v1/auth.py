from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import get_password_hasher, get_token_issuer, get_user_repository
from app.api.v1.schemas import LoginIn, RegisterIn, TokenOut
from app.application.identity.services import Authenticate, RegisterStudent
from app.domain.identity.exceptions import EmailAlreadyRegisteredError, InvalidCredentialsError
from app.infrastructure.persistence.user_repository import SqlAlchemyUserRepository
from app.infrastructure.security.hasher import Argon2Hasher
from app.infrastructure.security.tokens import JwtTokenIssuer

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

UserRepoDep = Annotated[SqlAlchemyUserRepository, Depends(get_user_repository)]
HasherDep = Annotated[Argon2Hasher, Depends(get_password_hasher)]
IssuerDep = Annotated[JwtTokenIssuer, Depends(get_token_issuer)]


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=TokenOut)
async def register(payload: RegisterIn, repository: UserRepoDep, hasher: HasherDep,
                   issuer: IssuerDep) -> TokenOut:
    try:
        user = await RegisterStudent(repository, hasher).execute(
            email=payload.email,
            password=payload.password,
            first_name=payload.first_name,
            last_name=payload.last_name,
            document=payload.document,
            program_id=payload.program_id,
            current_semester=payload.current_semester,
        )
    except EmailAlreadyRegisteredError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        ) from error
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error

    return TokenOut(
        access_token=issuer.issue(subject=str(user.id), role=str(user.role)),
        role=str(user.role),
    )


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn, repository: UserRepoDep, hasher: HasherDep,
                issuer: IssuerDep) -> TokenOut:
    try:
        token = await Authenticate(repository, hasher, issuer).execute(
            email=payload.email, password=payload.password
        )
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        ) from error
    return TokenOut(access_token=token, role=issuer.decode(token)["role"])
