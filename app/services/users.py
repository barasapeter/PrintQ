from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.users import UserRepository
from app.schemas.user import UserCreate


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = UserRepository(session)

    async def get(self, user_id: int) -> User | None:
        return await self.repository.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        return await self.repository.get_by_email(email)

    async def create(self, payload: UserCreate) -> User:
        return await self.repository.create(payload)
