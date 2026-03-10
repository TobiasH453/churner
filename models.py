from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class EmailData(BaseModel):
    """Email data received from n8n"""
    # Required fields (from Claude LLM)
    email_type: Literal["order_confirmation", "shipping_confirmation"]
    order_number: str
    # Routing hint from n8n: "amz_personal" or "amz_business"
    account_type: Optional[str] = None

    # Optional fields
    grand_total: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    recipient: Optional[str] = None
    sender: Optional[str] = None
    timestamp: Optional[str] = None

class OrderDetails(BaseModel):
    """Amazon order details scraped from invoice page"""
    items: List[dict]  # [{"name": "Product", "quantity": 2, "price": "$50"}]
    total_before_cashback: str
    grand_total: str
    cashback_percent: float  # 5.0 or 6.0
    arrival_date: str
    invoice_url: str

class ShippingDetails(BaseModel):
    """Amazon shipping details from tracking page"""
    tracking_number: str
    carrier: str  # "Amazon Logistics", "UPS", etc.
    delivery_date: str
    items: List[dict]  # Item names and quantities

class EBDealResult(BaseModel):
    """Result from electronicsbuyer.gg deal submission"""
    success: bool
    deal_id: Optional[str] = None
    payout_value: float  # Calculated cashout value
    error_message: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    unmatched_items: List[str] = Field(default_factory=list)
    submitted_items: List[str] = Field(default_factory=list)
    payout_captured_items: List[str] = Field(default_factory=list)

class EBTrackingResult(BaseModel):
    """Result from electronicsbuyer.gg tracking submission"""
    success: bool
    tracking_id: Optional[str] = None
    error_message: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)

class AgentResponse(BaseModel):
    """Complete response back to n8n"""
    success: bool
    order_number: str
    email_type: str
    amazon_data: Optional[OrderDetails | ShippingDetails] = None
    eb_result: Optional[EBDealResult | EBTrackingResult] = None
    errors: List[str] = []
    execution_time_seconds: float
