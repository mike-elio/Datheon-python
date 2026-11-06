"""The output contracts; all keys are required, unknown facts are null."""

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Text = Annotated[str, Field(min_length=1)]
Number = Annotated[float, Field(allow_inf_nan=False)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class LineItem(StrictModel):
    description: Text
    quantity: Number | None
    unit_price: Number | None
    amount: Number | None


class Invoice(StrictModel):
    document_type: Literal["invoice"]
    invoice_number: Text | None
    vendor: Text | None
    customer: Text | None
    issue_date: date | None
    due_date: date | None
    currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")] | None
    items: list[LineItem]
    subtotal: Number | None
    tax: Number | None
    total: Number | None
    warnings: list[Text]


class Experience(StrictModel):
    company: Text | None
    title: Text | None
    start: Text | None
    end: Text | None
    highlights: list[Text]


class Education(StrictModel):
    institution: Text | None
    degree: Text | None
    graduation: Text | None


class Resume(StrictModel):
    document_type: Literal["resume"]
    name: Text | None
    email: Text | None
    phone: Text | None
    location: Text | None
    summary: Text | None
    skills: list[Text]
    experience: list[Experience]
    education: list[Education]
    languages: list[Text]
    warnings: list[Text]


SCHEMAS = {"invoice": Invoice, "resume": Resume}
