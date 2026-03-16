from sqlalchemy import Integer, String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import Base


class Article(Base):
    __tablename__ = "article"

    id: Mapped[ int] = mapped_column(Integer, primary_key=True, autoincrement= True)
    title: Mapped[ str] = mapped_column(String(255))
    content: Mapped[ str] = mapped_column(Text)
    author_id: Mapped[ int] = mapped_column(Integer, ForeignKey("user.id"))
    author: Mapped[ "User"] = relationship(back_populates="articles")

    tags: Mapped[ list["Tag"]] = relationship(
        "Tag",
        back_populates="articles",
        secondary="article_tag")


class Tag(Base):
    __tablename__ = "tag"

    id: Mapped[ int] = mapped_column(Integer, primary_key=True, autoincrement= True)
    name: Mapped[ str] = mapped_column(String(255))
    articles: Mapped[ list["Article"]] = relationship(
        "Article",
        back_populates="tags",
        secondary="article_tag")

class ArticleTag(Base):
    __tablename__ = "article_tag"

    article_id: Mapped[ int] = mapped_column(Integer, ForeignKey("article.id"), primary_key=True)
    tag_id: Mapped[ int] = mapped_column(Integer, ForeignKey("tag.id"), primary_key=True)