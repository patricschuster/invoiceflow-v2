from sqlalchemy import Column, Integer, String, Text
from app.database import Base


class Setting(Base):
    """Key/value configuration settings stored in DB"""

    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Setting {self.key}>"
