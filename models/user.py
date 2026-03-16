from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, autoincrement=True,primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index= True)
    username: Mapped[str] = mapped_column(String(100))
    password: Mapped[str] = mapped_column(String(255))
    mobile: Mapped[str] = mapped_column(String(11))

    user_extension: Mapped["UserExtension"] = relationship(back_populates="user", uselist=False) # uselist=False是告诉SQLAlchemy，这个关系只返回一个对象，而不是一个对象列表。
    articles: Mapped[list["Article"]] = relationship(back_populates="author")


class UserExtension(Base):
    __tablename__ = "user_extensions"

    id: Mapped[int] = mapped_column(Integer, autoincrement=True,primary_key=True)
    university: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), unique=True)
    user: Mapped["User"] = relationship(back_populates="user_extension")