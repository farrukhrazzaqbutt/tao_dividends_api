from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime



Base = declarative_base()

class Subnet(Base):
    __tablename__ = "subnets"
    
    id = Column(Integer, primary_key=True)
    netuid = Column(Integer, unique=True, nullable=False)
    name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    dividends = relationship("Dividend", back_populates="subnet")
    operations = relationship("Operation", back_populates="subnet")


class Dividend(Base):
    __tablename__ = "dividends"
    
    id = Column(Integer, primary_key=True)
    subnet_id = Column(Integer, ForeignKey("subnets.id"))
    hotkey = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    subnet = relationship("Subnet", back_populates="dividends")


class Operation(Base):
    __tablename__ = "operations"
    
    id = Column(Integer, primary_key=True)
    subnet_id = Column(Integer, ForeignKey("subnets.id"))
    hotkey = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    sentiment_score = Column(Float)
    operation_type = Column(String(50), nullable=False)  # 'stake' or 'unstake'
    status = Column(String(50), nullable=False)  # 'pending', 'completed', 'failed'
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    subnet = relationship("Subnet", back_populates="operations")

class SentimentAnalysis(Base):
    __tablename__ = "sentiment_analyses"

    id = Column(Integer, primary_key=True, index=True)
    netuid = Column(Integer, index=True)
    sentiment_score = Column(Float)
    tweet_count = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
    source = Column(String)  # 'datura' or 'chutes'