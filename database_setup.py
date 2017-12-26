from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(100))


class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(String(500))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship("Category", back_populates="items")
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {'id': self.id, 'name': self.name,
                'description': self.description,
                'category.id': self.category_id}


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    items = relationship("Item", back_populates="category")
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {'id': self.id, 'name': self.name, }


engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.create_all(engine)
