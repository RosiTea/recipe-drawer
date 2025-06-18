# models.py
# ---------
import json
from sqlalchemy import Column, Integer, String, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Recipe(Base):
    __tablename__ = 'recipes'
    id = Column(Integer, primary_key=True)
    title = Column(String, unique=True, nullable=False)
    ingredients = Column(JSON, nullable=False)
    steps = Column(JSON, nullable=False)
    tags = Column(JSON, nullable=True)

engine = create_engine('sqlite:///recipes.db')
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Create database tables."""
    Base.metadata.create_all(engine)


def drop_db():
    """Drop all database tables."""
    Base.metadata.drop_all(engine)


def add_sample_data():
    """Insert sample recipes if they don't already exist."""
    session = SessionLocal()
    # Define sample recipes
    sample = [
        {
            'title': 'Spaghetti Aglio e Olio',
            'ingredients': [
                {'name': 'spaghetti', 'quantity': '200g'},
                {'name': 'garlic', 'quantity': '3 cloves'},
                {'name': 'olive oil', 'quantity': '2 tbsp'},
                {'name': 'chili flakes', 'quantity': '1 tsp'}
            ],
            'steps': ['Boil pasta', 'Saute garlic', 'Toss together'],
            'tags': ['italian', 'vegetarian']
        },
        {
            'title': 'Quick Pancakes',
            'ingredients': [
                {'name': 'flour', 'quantity': '200g'},
                {'name': 'milk', 'quantity': '250ml'},
                {'name': 'egg', 'quantity': '1'},
                {'name': 'baking powder', 'quantity': '1 tsp'},
                {'name': 'sugar', 'quantity': '2 tbsp'}
            ],
            'steps': ['Mix ingredients', 'Cook on griddle'],
            'tags': ['breakfast', 'vegetarian']
        },
        {
            'title': 'Chicken Salad',
            'ingredients': [
                {'name': 'chicken breast', 'quantity': '200g'},
                {'name': 'lettuce', 'quantity': '1 head'},
                {'name': 'tomato', 'quantity': '2'},
                {'name': 'cucumber', 'quantity': '1'},
                {'name': 'olive oil', 'quantity': '1 tbsp'}
            ],
            'steps': ['Cook chicken', 'Chop veggies', 'Toss together', 'Dress salad'],
            'tags': ['lunch', 'gluten-free']
        }
    ]
    # refresh samples
    for data in sample:
        existing = session.query(Recipe).filter_by(title=data['title']).first()
        if existing:
            session.delete(existing)
    session.commit()
    for data in sample:
        session.add(Recipe(**data))
    session.commit()
    session.close()