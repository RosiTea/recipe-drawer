# cli.py
# ------
import click
import random as rnd
from models import SessionLocal, init_db, drop_db, add_sample_data, Recipe

@click.group(context_settings=dict(help_option_names=['-h','--help']))
def cli():
    """Recipe Drawer CLI: Manage and randomize recipes."""
    pass

@cli.command()
@click.option('--force','-f',is_flag=True,help='Drop DB before init (fresh samples)')
def init(force):
    """Initialize the database and load sample recipes."""
    if force:
        drop_db()
        click.echo('Dropped existing database.')
    init_db()
    add_sample_data()
    click.echo('Initialized database with sample recipes.')

@cli.command(name='list')
def list_recipes():
    """List all recipe titles."""
    session = SessionLocal()
    titles = session.query(Recipe.title).all()
    click.echo('Recipes:')
    for (t,) in titles:
        click.echo(f'- {t}')
    session.close()

@cli.command(name='add')
@click.option('--title','-t',prompt=True,help='Recipe title')
@click.option('--ingredients','-i',prompt=True,
              help='Comma-separated list of name:quantity pairs, e.g. "flour:200g,milk:250ml"')
@click.option('--steps','-s',prompt=True,
              help='Comma-separated list of steps in order')
@click.option('--tags','-g',prompt=True,default='',
              help='Comma-separated tags (optional)')
def add_recipe(title, ingredients, steps, tags):
    """Add a new recipe to the database."""
    session = SessionLocal()
    # parse ingredients into dicts
    ingr_list = []
    for item in ingredients.split(','):
        name, qty = item.split(':')
        ingr_list.append({'name':name.strip(),'quantity':qty.strip()})
    # parse steps
    steps_list = [st.strip() for st in steps.split(',')]
    # parse tags
    tags_list = [tg.strip() for tg in tags.split(',')] if tags else []
    # create and commit
    new = Recipe(title=title, ingredients=ingr_list, steps=steps_list, tags=tags_list)
    session.add(new)
    session.commit()
    click.echo(f'Recipe "{title}" added.')
    session.close()

@cli.command(name='delete')  # CHANGED: new delete command
@click.option('--title','-t',prompt=True,help='Title of recipe to delete')
def delete_recipe(title):
    """Delete a recipe by its title."""
    session = SessionLocal()
    recipe = session.query(Recipe).filter_by(title=title).first()
    if not recipe:
        click.echo(f'Recipe "{title}" not found.')
    else:
        session.delete(recipe)
        session.commit()
        click.echo(f'Recipe "{title}" deleted.')
    session.close()

@cli.command(name='random')
@click.option('--tag','-t',multiple=True,help='Filter by tags')
@click.option('--count','-n',default=1,show_default=True,type=int,
              help='Number of recipes')
def random_recipe(tag,count):
    """Pick random recipe(s), optionally by tag."""
    session = SessionLocal()
    allr = session.query(Recipe).all()
    if tag:
        allr = [r for r in allr if all(t in (r.tags or []) for t in tag)]
    if not allr:
        click.echo('No recipes found.')
        return
    pick = rnd.sample(allr, k=min(count, len(allr)))
    for r in pick:
        click.echo(f"\nTitle: {r.title}")
        click.echo('Ingredients:')
        for ing in r.ingredients:
            click.echo(f"- {ing['quantity']} {ing['name']}")
        click.echo('Steps:')
        for i, st in enumerate(r.steps, 1):
            click.echo(f"{i}. {st}")

@cli.command()
@click.option('--file','-f',default='grocery.txt',help='Output file')
@click.option('--count','-n',default=None,type=int,help='Number of recipes')
def grocery(file,count):
    """Generate grocery list for recipe(s)."""
    session = SessionLocal()
    rs = session.query(Recipe).all()
    if count:
        rs = rnd.sample(rs, k=min(count, len(rs)))
    agg = {}
    for r in rs:
        for ing in r.ingredients:
            agg.setdefault(ing['name'], []).append(ing['quantity'])
    with open(file, 'w') as f:
        for name, qs in agg.items():
            f.write(f"{name} - {', '.join(qs)}\n")
    click.echo(f'Grocery list written to {file}')

if __name__ == '__main__':
    cli()