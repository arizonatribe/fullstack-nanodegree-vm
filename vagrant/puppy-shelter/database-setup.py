import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, SmallInteger, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

Base = declarative_base()

class Shelter(Base):
  __tablename__ = 'shelter'

  id = Column(Integer, primary_key=True)
  name = Column(String(256), nullable=False)
  address = Column(String(256), nullable=False)
  city = Column(String(256), nullable=False)
  state = Column(String(2), nullable=False)
  email = Column(String(100))

class Puppy(Base):
  __tablename__ = 'puppy'

  id = Column(Integer, primary_key=True)
  name = Column(String(256), nullable=False)
  date_of_birth = Column(Date)
  breed = Column(String(256), nullable=False)
  gender = Column(String(1), nullable=False)
  weight = Column(SmallInteger, nullable=False)

  shelter_id = Column(Integer, ForeignKey('shelter.id'))

engine = create_engine('sqlite:///puppies.db')
Base.metadata.create_all(engine)
