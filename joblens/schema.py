from typing import Literal

from pydantic import BaseModel


class JobPosting(BaseModel):
    work_mode: Literal["remote", "hybrid", "onsite", "unspecified"]
    company: str
    location: str | None
    salary_min: int | None
    salary_max: int | None
    salary_currency: str | None
    required_skills: list[str]
    discipline: Literal["frontend", "backend", "fullstack"]
