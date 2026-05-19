from typing import Literal, Optional
from pydantic import BaseModel, Field


class Party(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None


class PaymentDetails(BaseModel):
    bank: Optional[str] = None
    account_name: Optional[str] = None
    account_number: Optional[str] = None


class LineItem(BaseModel):
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total: Optional[float] = None


class Invoice(BaseModel):
    document_type: Literal["invoice", "claim_form", "other"] = "invoice"
    invoice_number: Optional[str] = None
    policy_number: Optional[str] = None
    incident_date: Optional[str] = Field(None, description="ISO YYYY-MM-DD, claim forms only")
    issue_date: Optional[str] = Field(None, description="ISO 8601 YYYY-MM-DD")
    due_date: Optional[str] = Field(None, description="ISO 8601 YYYY-MM-DD")
    currency: Optional[str] = None
    issued_to: Party = Party()
    pay_to: PaymentDetails = PaymentDetails()
    line_items: list[LineItem] = []
    subtotal: Optional[float] = None
    tax_rate: Optional[float] = Field(None, description="Percent, e.g. 10 for 10%")
    tax_amount: Optional[float] = None
    total: Optional[float] = None
    missing_fields: list[str] = []


class WordBox(BaseModel):
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    page: int


class PageSize(BaseModel):
    page: int
    width: float
    height: float


class ExtractionResponse(BaseModel):
    invoice: Invoice
    raw_text: str
    mode: str
    model: Optional[str] = None
    pdf_base64: Optional[str] = None
    word_boxes: list[WordBox] = []
    pages: list[PageSize] = []


class Classification(BaseModel):
    category: str
    category_label: str
    priority: Literal["high", "medium", "low"]
    route_to: str
    confidence: float
    reason: str
    suggested_actions: list[str] = []
    detected_language: Optional[str] = None


class ClassificationResponse(BaseModel):
    classification: Classification
    mode: str
    model: Optional[str] = None


class ClassificationRequest(BaseModel):
    text: str
