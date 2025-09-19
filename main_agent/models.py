from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date

class UserDetails(BaseModel):
    name: str = ""
    email: str = ""
    phone_number: str = ""
    passport_nationality: str = ""
    home_address: str = ""

class PersonDetails(BaseModel):
    name: str = ""
    age: Optional[int] = None
    gender: str = ""
    relation_to_user: str = ""

class Preferences(BaseModel):
    travel_theme: List[str] = []
    cuisine_preferences: List[str] = []
    dietary_restrictions: List[str] = []
    interests: List[str] = []
    hotel_type: str = ""
    flight_seat_type: str = ""

class ScheduleItem(BaseModel):
    activity_type: str = ""
    start_time: str = ""
    end_time: str = ""
    description: str = ""
    details: Dict[str, Any] = {}
    booking_status: str = ""

class Day(BaseModel):
    day_number: Optional[int] = None
    date: str = ""
    schedule: List[ScheduleItem] = []

class Itinerary(BaseModel):
    trip_name: str = ""
    origin: str = ""
    destination: str = ""
    start_date: str = ""
    end_date: str = ""
    days: List[Day] = []

class ExpenseBreakdown(BaseModel):
    flights: Optional[float] = None
    hotels: Optional[float] = None
    food: Optional[float] = None
    activities: Optional[float] = None
    transport: Optional[float] = None
    miscellaneous: Optional[float] = None

class Budget(BaseModel):
    total_budget: Optional[float] = None
    currency: str = ""
    expense_breakdown: ExpenseBreakdown = Field(default_factory=ExpenseBreakdown)

class CurrencyExchange(BaseModel):
    from_currency: str = ""
    to_currency: str = ""
    exchange_rate: Optional[float] = None
    last_updated: str = ""

class ItineraryState(BaseModel):
    user_details: UserDetails = Field(default_factory=UserDetails)
    persons_details: List[PersonDetails] = []
    preferences: Preferences = Field(default_factory=Preferences)
    itinerary: Itinerary = Field(default_factory=Itinerary)
    budget: Budget = Field(default_factory=Budget)
    currency_exchange: CurrencyExchange = Field(default_factory=CurrencyExchange)
