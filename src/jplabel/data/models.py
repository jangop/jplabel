from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass

class StampedBase(DeclarativeBase):
    created: Mapped[datetime] = mapped_column(server_default=func.now())
    updated: Mapped[datetime] = mapped_column(
        server_default=func.now(), server_onupdate=func.now()
    )

class User(StampedBase):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False, unique=True)

class Image(StampedBase):
    __tablename__ = "image"
    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(nullable=False, unique=True)

    labelings: Mapped[list[Labeling]] = relationship("Labeling")

class Label(StampedBase):
    __tablename__ = "label"
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(nullable=False, unique=True)

class Labeling(StampedBase):
    __tablename__ = "labeling"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    user: Mapped[User] = relationship("User")
    image_id: Mapped[int] = mapped_column(
        ForeignKey("image.id", ondelete="CASCADE"), nullable=False
    )
    image: Mapped[Image] = relationship("Image", back_populates="labelings")
    label_id: Mapped[int] = mapped_column(
        ForeignKey("label.id", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[Label] = relationship("Label")