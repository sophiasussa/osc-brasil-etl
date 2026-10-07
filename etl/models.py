from datetime import date

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    Double,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class LegalNature(Base):
    __tablename__ = "legal_natures"

    code: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    organizations: Mapped[list["Organization"]] = relationship(
        back_populates="legal_nature",
    )


class Municipality(Base):
    __tablename__ = "municipalities"

    code: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str | None] = mapped_column(
        String(150),
    )

    uf: Mapped[str | None] = mapped_column(
        String(2),
    )

    organizations: Mapped[list["Organization"]] = relationship(
        back_populates="municipality",
    )


class ActivityArea(Base):
    __tablename__ = "activity_areas"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
    )

    organizations: Mapped[list["OrganizationArea"]] = relationship(
        back_populates="area",
    )

    subareas: Mapped[list["ActivitySubarea"]] = relationship(
        back_populates="area",
    )


class ActivitySubarea(Base):
    __tablename__ = "activity_subareas"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    area_id: Mapped[int] = mapped_column(
        ForeignKey(
            "activity_areas.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    area: Mapped["ActivityArea"] = relationship(
        back_populates="subareas",
    )

    organizations: Mapped[list["OrganizationSubarea"]] = relationship(
        back_populates="subarea",
    )

    __table_args__ = (
        UniqueConstraint(
            "area_id",
            "name",
            name="uq_activity_subarea_area_name",
        ),
    )


class Cnae(Base):
    __tablename__ = "cnaes"

    code: Mapped[str] = mapped_column(
        String(10),
        primary_key=True,
    )

    name: Mapped[str | None] = mapped_column(
        String(255),
    )

    organizations: Mapped[list["OrganizationCnae"]] = relationship(
        back_populates="cnae",
    )


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    cnpj: Mapped[str] = mapped_column(
        String(14),
        nullable=False,
        unique=True,
    )

    legal_name: Mapped[str | None] = mapped_column(
        String(255),
    )

    trade_name: Mapped[str | None] = mapped_column(
        String(255),
    )

    legal_nature_code: Mapped[int | None] = mapped_column(
        ForeignKey("legal_natures.code"),
    )

    matrix_or_branch: Mapped[str | None] = mapped_column(
        String(20),
    )

    registration_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    removed_from_mosc: Mapped[bool | None] = mapped_column(
        Boolean,
    )

    foundation_date: Mapped[date | None] = mapped_column(
        Date,
    )

    closing_date: Mapped[date | None] = mapped_column(
        Date,
    )

    closing_year: Mapped[int | None] = mapped_column(
        Integer,
    )

    address: Mapped[str | None] = mapped_column(
        Text,
    )

    municipality_code: Mapped[int | None] = mapped_column(
        ForeignKey("municipalities.code"),
    )

    latitude: Mapped[float | None] = mapped_column(
        Double,
    )

    longitude: Mapped[float | None] = mapped_column(
        Double,
    )

    legal_nature: Mapped["LegalNature | None"] = relationship(
        back_populates="organizations",
    )

    municipality: Mapped["Municipality | None"] = relationship(
        back_populates="organizations",
    )

    areas: Mapped[list["OrganizationArea"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    subareas: Mapped[list["OrganizationSubarea"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    cnaes: Mapped[list["OrganizationCnae"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "registration_status IN "
            "('ACTIVE', 'INAPT', 'CLOSED_OR_NULL', 'SUSPENDED')",
            name="chk_registration_status",
        ),
        CheckConstraint(
            "matrix_or_branch IN "
            "('HEADQUARTERS', 'BRANCH', 'UNKNOWN')",
            name="chk_matrix_or_branch",
        ),
    )


class OrganizationArea(Base):
    __tablename__ = "organization_areas"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey(
            "organizations.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    area_id: Mapped[int] = mapped_column(
        ForeignKey(
            "activity_areas.id",
            ondelete="RESTRICT",
        ),
        primary_key=True,
    )

    organization: Mapped["Organization"] = relationship(
        back_populates="areas",
    )

    area: Mapped["ActivityArea"] = relationship(
        back_populates="organizations",
    )


class OrganizationSubarea(Base):
    __tablename__ = "organization_subareas"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey(
            "organizations.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    subarea_id: Mapped[int] = mapped_column(
        ForeignKey(
            "activity_subareas.id",
            ondelete="RESTRICT",
        ),
        primary_key=True,
    )

    organization: Mapped["Organization"] = relationship(
        back_populates="subareas",
    )

    subarea: Mapped["ActivitySubarea"] = relationship(
        back_populates="organizations",
    )


class OrganizationCnae(Base):
    __tablename__ = "organization_cnaes"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey(
            "organizations.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    cnae_code: Mapped[str] = mapped_column(
        ForeignKey(
            "cnaes.code",
            ondelete="RESTRICT",
        ),
        primary_key=True,
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    organization: Mapped["Organization"] = relationship(
        back_populates="cnaes",
    )

    cnae: Mapped["Cnae"] = relationship(
        back_populates="organizations",
    )


Index(
    "uq_organization_primary_cnae",
    OrganizationCnae.organization_id,
    unique=True,
    postgresql_where=OrganizationCnae.is_primary.is_(True),
)
