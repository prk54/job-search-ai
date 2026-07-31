import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Table, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from job_search.core.config import APP_DIR

DB_PATH = APP_DIR / "state.db"
Base = declarative_base()

class DBProfile(Base):
    __tablename__ = "profiles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String)
    phone = Column(String)
    location = Column(String)
    linkedin = Column(String)
    github = Column(String)
    portfolio = Column(String)
    raw_profile_json = Column(String) # JSON backup string
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DBCompany(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    api_slug = Column(String)
    api_type = Column(String) # greenhouse, lever, ashby, null
    careers_url = Column(String)
    tc_range = Column(String, default="Varies")
    tier = Column(Integer, default=2) # 1, 2, 3, practice
    notes = Column(String)
    is_discovered = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Ensure slug+type is unique to prevent duplicate crawlers
    __table_args__ = (
        UniqueConstraint('api_slug', 'api_type', name='_company_api_uc'),
    )

class DBApplication(Base):
    __tablename__ = "applications"
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    role_title = Column(String, nullable=False)
    jd_url = Column(String, unique=True, nullable=False)
    jd_text = Column(String)
    fit_rating = Column(String, default="Medium") # High, Medium, Low
    fit_score = Column(Integer, default=50) # 0-100 score
    applied_date = Column(DateTime)
    status = Column(String, default="Wishlist") # Wishlist, Applied, Interviewing, Offer, Rejected
    tailored_resume_path = Column(String)
    tailored_cover_path = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    company = relationship("DBCompany", backref="applications")

# Session management
engine = create_engine(f"sqlite:///{DB_PATH}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Create database tables if they do not exist"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Context manager database session helper"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
