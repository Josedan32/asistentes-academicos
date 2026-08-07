from dataclasses import dataclass

from app.application.identity.ports import PasswordHasher, TokenIssuer, UserRepository
from app.domain.identity.entities import Role, StudentProfile, User
from app.domain.identity.exceptions import EmailAlreadyRegisteredError, InvalidCredentialsError


@dataclass
class RegisterStudent:
    repository: UserRepository
    hasher: PasswordHasher

    async def execute(
        self,
        *,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        document: str,
        program_id: int,
        current_semester: int,
    ) -> User:
        normalized_email = email.strip().lower()
        if await self.repository.find_by_email(normalized_email) is not None:
            raise EmailAlreadyRegisteredError(normalized_email)

        user = User(
            email=normalized_email,
            password_hash=self.hasher.hash(password),
            role=Role.STUDENT,
        )
        profile = StudentProfile(
            user_id=0,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            document=document.strip(),
            program_id=program_id,
            current_semester=current_semester,
        )
        return await self.repository.add(user, profile)


@dataclass
class Authenticate:
    repository: UserRepository
    hasher: PasswordHasher
    issuer: TokenIssuer

    async def execute(self, *, email: str, password: str) -> str:
        user = await self.repository.find_by_email(email.strip().lower())
        if user is None or not self.hasher.verify(password, user.password_hash):
            raise InvalidCredentialsError()
        return self.issuer.issue(subject=str(user.id), role=str(user.role))
