from sqlmodel import Field, Session, SQLModel, create_engine
from datetime import datetime
from pydantic import BaseModel

sqlite_file_name = 'modbus.db'
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

class Relay(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    relay_port: int = Field(default=None, unique=True)
    relay_hz: str = Field(default=None, max_length=100, index=True)
    status: bool = Field(default=False)
    created: datetime | None = Field(default_factory=datetime.now, nullable=False)
    

class Report(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    startTime: datetime = Field(default_factory=datetime.now, nullable=False)
    frequencies: str = Field(default=None, nullable=False)
    deadline: float | None = Field(default=None, nullable=True)
    endTime: datetime | None = Field(default=None, nullable=True)

class Item(BaseModel):
    ports: list
    dedline: float
    token: str

class Token(BaseModel):
    token: str

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    
def get_session():
    with Session(engine) as session:
        yield session

