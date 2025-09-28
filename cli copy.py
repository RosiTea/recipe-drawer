# cli.py
# ------
import click, json, csv
import random as rnd
from models import SessionLocal, init_db, drop_db, add_sample_data, Recipe
from pathlib import Path
from storage_jsonl import JsonlStorage
# from storage_sqlite import SqliteStorage (not implemented yet)

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


def get_store(db: str):
    p = Path(db)
    if p.suffix.lower() == ".jsonl":
        return JsonlStorage(p)
    elif p.suffix.lower() in (".db", ".sqlite", ".sqlite3"):
        return SqliteStorage(str(p))
    else:
        # default to JSONL
        return JsonlStorage(p if p.suffix else p.with_suffix(".jsonl"))


@cli.command(name="import")
@click.option("--db", default="recipes.jsonl", help="Path to DB file (.jsonl or .sqlite)")
@click.option("--fmt", type=click.Choice(["jsonl","json","csv"]), required=True)
@click.option("--file", "infile", type=click.Path(exists=True), required=True)
def import_(db, fmt, infile):
    """Bulk import recipes from a file."""
    store = get_store(db)
    def iter_json():
        with open(infile) as f:
            data = json.load(f)
            for r in data: yield r
    def iter_jsonl():
        with open(infile) as f:
            for line in f: yield json.loads(line)
    def iter_csv():
        # expect: title,ingredients,steps,tags
        # ingredients: "name:qty,name2:qty2"; steps: "step1|step2"; tags: "t1,t2"
        with open(infile, newline="") as f:
            rd = csv.DictReader(f)
            for row in rd:
                recipe = {
                    "title": row["title"].strip(),
                    "ingredients": {kv.split(":")[0].strip(): kv.split(":",1)[1].strip() for kv in row["ingredients"].split(",") if ":" in kv},
                    "steps": [s.strip() for s in row["steps"].split("|") if s.strip()],
                    "tags": [t.strip() for t in row.get("tags","").split(",") if t.strip()],
                }
                yield recipe
    it = {"json": iter_json, "jsonl": iter_jsonl, "csv": iter_csv}[fmt]()
    added = store.import_iter(it)
    store.save()
    click.echo(f"Imported {added} new recipes into {db}")

@cli.command()
@click.option("--db", default="recipes.jsonl")
@click.option("--fmt", type=click.Choice(["jsonl","json"]), default="json")
@click.option("--out", "outfile", type=click.Path(), required=True)
def export(db, fmt, outfile):
    """Export all recipes."""
    store = get_store(db)
    if fmt == "jsonl":
        with open(outfile, "w") as f:
            for r in store.export_iter():
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    else:
        with open(outfile, "w") as f:
            json.dump(list(store.export_iter()), f, ensure_ascii=False, indent=2)
    click.echo(f"Exported to {outfile}")

@cli.command()
@click.option("--db", default="recipes.jsonl")
@click.option("--out", "outfile", type=click.Path(), required=True)
def snapshot(db, outfile):
    """
    Emit a single-file, denormalised JSON snapshot optimised for publishing.
    Structure:
      [{title, tags, ingredients:[{name, amount}], steps:[...]}, ...]
    """
    store = get_store(db)
    pub = []
    for r in store.list_recipes():
        pub.append({
            "title": r["title"],
            "tags": r.get("tags", []),
            "ingredients": [{"name": k, "amount": v} for k, v in r["ingredients"].items()],
            "steps": r["steps"],
        })
    with open(outfile, "w") as f:
        json.dump(pub, f, ensure_ascii=False)
    click.echo(f"Wrote snapshot: {outfile}")

if __name__ == '__main__':
    cli()