from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BugsInPyResultModel(Base):
    __tablename__ = "bugsinpy_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("test_tasks.id"),
        nullable=False,
        index=True,
    )
    project: Mapped[str] = mapped_column(String(100), nullable=False)
    bug_id: Mapped[int] = mapped_column(nullable=False)
    trigger_test: Mapped[str] = mapped_column(String(255), nullable=False)
    buggy_outcome: Mapped[str] = mapped_column(String(20), nullable=False)
    fixed_outcome: Mapped[str] = mapped_column(String(20), nullable=False)
    failure_log: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    suggestion: Mapped[str] = mapped_column(String(255), nullable=False)
    regression_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
