from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import *

engine = create_engine('sqlite:///itemcatalog.db')
DBSession = sessionmaker(bind=engine)
session = DBSession()

session.add_all([Category(name="Soccer"), Category(name="Basketball"),
                 Category(name="Snowboarding"), Category(name="Skating")])
session.commit()
