# mybot/database/models/auction.py
import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    BigInteger,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    UniqueConstraint,
    Enum,
)
from sqlalchemy.sql import func
from database.base import Base

class AuctionStatus(enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    ENDED = "ended"
    CANCELLED = "cancelled"

class Auction(Base):
    """Real-time auction system."""
    
    __tablename__ = "auctions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    prize_description = Column(Text, nullable=False)
    initial_price = Column(Integer, nullable=False)
    current_highest_bid = Column(Integer, default=0)
    highest_bidder_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    winner_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    status = Column(Enum(AuctionStatus), default=AuctionStatus.PENDING)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    ended_at = Column(DateTime, nullable=True)
    min_bid_increment = Column(Integer, default=10)
    max_participants = Column(Integer, nullable=True)
    auto_extend_minutes = Column(Integer, default=5)


class Bid(Base):
    """Individual bids in auctions."""
    
    __tablename__ = "bids"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    auction_id = Column(Integer, ForeignKey("auctions.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    is_winning = Column(Boolean, default=False)
    
    __table_args__ = (
        UniqueConstraint("auction_id", "user_id", "amount", name="uix_auction_user_bid"),
    )


class AuctionParticipant(Base):
    """Track users participating in auctions for notifications."""
    
    __tablename__ = "auction_participants"
    
    auction_id = Column(Integer, ForeignKey("auctions.id"), primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    joined_at = Column(DateTime, default=func.now())
    notifications_enabled = Column(Boolean, default=True)
    last_notified_at = Column(DateTime, nullable=True)
