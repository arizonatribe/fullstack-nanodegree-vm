import sys
import datetime
from sqlalchemy import Column, ForeignKey, Integer, DateTime, String, Text

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship

from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
  __tablename__ = 'user'
  id = Column(Integer, primary_key = True)
  name = Column(String(80), nullable = False)
  email = Column(String(50), nullable = False)
  picture = Column(Text)

class Restaurant(Base):
  __tablename__ = 'restaurant'
  id = Column(Integer, primary_key = True)
  name = Column(String(80), nullable = False)
  user_id = Column(Integer, ForeignKey('user.id'))
  user = relationship(User)
  created_date = Column(DateTime, default=datetime.datetime.utcnow)
  updated_date = Column(DateTime, default=datetime.datetime.utcnow)

  @property
  def serialize(self):
    #Returns object data in serializable format
    return {
      'name': self.name,
      'id': self.id,
      'user_id': self.user_id
    }

class MenuItem(Base):
  __tablename__ = 'menu_item'
  id = Column(Integer, primary_key = True)
  name = Column(String(80), nullable = False)
  course = Column(String(250))
  description = Column(String(250))
  price = Column(String(8))
  restaurant_id = Column(Integer, ForeignKey('restaurant.id'))
  restaurant = relationship(Restaurant)
  picture = Column(Text, nullable = True)
  user_id = Column(Integer, ForeignKey('user.id'))
  user = relationship(User)
  created_date = Column(DateTime, default=datetime.datetime.utcnow)
  updated_date = Column(DateTime, default=datetime.datetime.utcnow)

  @property
  def serialize(self):
    #Returns object data in serializable format
    return {
      'name': self.name,
      'description': self.description,
      'id': self.id,
      'price': self.price,
      'course': self.course,
      'user_id': self.user_id
    }
engine = create_engine('sqlite:///restaurantmenuwithusers.db')

Base.metadata.create_all(engine)