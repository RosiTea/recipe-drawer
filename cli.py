# cli.py
# ------
import click, json, csv, sys
from pathlib import Path

# Storage drivers
from storage_jsonl import JsonlStorage
# SQLite is optional; import lazily
try:
    from storage_sqlite import SqliteStorage
    HAVE_SQLITE = True
except Exception:
    HAVE_SQLITE = False

from storage import Storage, Recipe

CONTEXT_SETTINGS = dict(help_option_names=['-h','--help'])

def get_store(db: str) -> Storage:
    p = Path(db)
    if p.suffix.lower() == ".jsonl" or p.suffix == "":
        # default to JSONL
        return JsonlStorage(p if p.suffix else p.with_suffix(".jsonl"))
    elif p.suffix.lower() in (".db", ".sqlite", ".sqlite3"):
        if not HAVE_SQLITE:
            raise click.ClickException("SQLite backend not available. Add storage_sqlite.py or use a .jsonl DB.")
        return SqliteStorage(str(p))
    else:
        # Fallback to JSONL
        return JsonlStorage(p)

@click.group(context_settings=CONTEXT_SETTINGS)
@click.option("--db", default="recipes.jsonl", help="Path to DB (.jsonl or .sqlite/.db). Default: recipes.jsonl")
@click.pass_context
def cli(ctx, db):
    """Recipe Drawer CLI (unified storage)."""
    ctx.ensure_object(dict)
    ctx.obj["DB_PATH"] = db
    ctx.obj["STORE"] = get_store(db)

# ---------------------------
# Core commands (storage-backed)
# ---------------------------

@cli.command(name='init')
@click.option('--with-samples', is_flag=True, help='Seed with a few sample recipes')
@click.pass_context
def init_cmd(ctx, with_samples):
    """Initialise an empty database (optionally with samples)."""
    store: Storage = ctx.obj["STORE"]
    if with_samples:
        samples = [
            {
                "title": "Quick Pancakes",
                "ingredients": {"plain flour": "200 g", "milk": "250 ml", "egg": "1", "baking powder": "1 tsp", "salt": "pinch"},
                "steps": ["Whisk dry", "Add wet and whisk", "Rest 5 min", "Cook on medium until bubbles", "Flip and finish"],
                "tags": ["breakfast", "vegetarian"],
            },
            {
                "title": "Spaghetti Aglio e Olio",
                "ingredients": {"spaghetti": "400 g", "garlic": "6 cloves", "olive oil": "80 ml", "red chilli flakes": "1 tsp", "parsley": "small bunch", "salt": "to taste"},
                "steps": ["Cook pasta al dente", "Gently sizzle garlic in oil", "Add chilli", "Toss pasta with oil and pasta water", "Finish with parsley and salt"],
                "tags": ["italian", "quick", "vegan"],
            },
        ]
        store.import_iter(samples)
    store.save()
    click.echo(f"Initialised {ctx.obj['DB_PATH']} {'with samples' if with_samples else ''}.")

@cli.command(name='list')
@click.pass_context
def list_recipes(ctx):
    """List all recipes."""
    store: Storage = ctx.obj["STORE"]
    titles = [r["title"] for r in store.list_recipes()]
    if not titles:
        click.echo("No recipes.")
        return
    click.echo("Recipes:")
    for t in titles:
        click.echo(f"- {t}")

@cli.command(name='add')
@click.option('--title','-t',prompt=True,help='Recipe title')
@click.option('--ingredients','-i',prompt=True,
              help='Comma-separated name:qty pairs (quote the whole field if it includes commas). E.g. "flour:200 g,milk:250 ml"')
@click.option('--steps','-s',prompt=True,
              help='Pipe-separated steps in order, e.g. "Mix|Cook|Serve"')
@click.option('--tags','-g',default='',help='Comma-separated tags (optional)')
@click.option('--servings', default='', help='Servings (optional; free text or integer)')
@click.option('--source-url', default='', help='Source URL (optional)')
@click.pass_context
def add_recipe(ctx, title, ingredients, steps, tags, servings, source_url):
    """Add a new recipe."""
    store: Storage = ctx.obj["STORE"]
    # parse ingredients -> dict
    ing_map = {}
    for chunk in [c for c in ingredients.split(",") if c.strip()]:
        if ":" not in chunk:
            raise click.ClickException(f"Ingredient must be name:qty, got '{chunk}'")
        name, qty = chunk.split(":", 1)
        ing_map[name.strip()] = qty.strip()
    steps_list = [s.strip() for s in steps.split("|") if s.strip()]
    tags_list = [t.strip() for t in tags.split(",") if t.strip()]
    recipe: Recipe = {
        "title": title.strip(),
        "ingredients": ing_map,
        "steps": steps_list,
        "tags": tags_list,
    }
    if servings.strip():
        recipe["servings"] = servings.strip()
    if source_url.strip():
        recipe["source_url"] = source_url.strip()

    if store.get_recipe(recipe["title"]):
        raise click.ClickException(f"Recipe '{recipe['title']}' already exists")
    store.add_recipe(recipe)
    store.save()
    click.echo(f'Added "{recipe["title"]}".')

@cli.command(name='delete')
@click.option('--title','-t',prompt=True,help='Title of recipe to delete')
@click.pass_context
def delete_recipe(ctx, title):
    """Delete a recipe by title."""
    store: Storage = ctx.obj["STORE"]
    ok = store.delete_recipe(title)
    if ok:
        store.save()
        click.echo(f'Deleted "{title}".')
    else:
        click.echo(f'Recipe "{title}" not found.')

@cli.command(name='random')
@click.option('--tag','-t',multiple=True,help='Filter by tag (repeatable)')
@click.option('--count','-n',default=1,show_default=True,type=int,help='Number of recipes')
@click.pass_context
def random_recipe(ctx, tag, count):
    """Pick random recipe(s)."""
    store: Storage = ctx.obj["STORE"]
    picks = []
    if tag:
        # If multiple tags given, intersect by filtering sequentially
        pool = store.list_recipes()
        for tg in tag:
            pool = [r for r in pool if tg in r.get("tags", [])]
        from random import sample
        picks = sample(pool, k=min(count, len(pool))) if pool else []
    else:
        picks = store.random_recipes(n=count)

    if not picks:
        click.echo("No matching recipes.")
        return

    for r in picks:
        click.echo(f"\nTitle: {r['title']}")
        click.echo('Ingredients:')
        for ing, amt in r.get("ingredients", {}).items():
            click.echo(f"- {amt} {ing}")
        click.echo('Steps:')
        for i, st in enumerate(r.get("steps", []), 1):
            click.echo(f"{i}. {st}")
        if r.get("tags"):
            click.echo("Tags: " + ", ".join(r["tags"]))

@cli.command(name='grocery')
@click.option('--titles', default='', help='Comma-separated list of titles (optional). If omitted, use --count.')
@click.option('--count','-n',default=0,type=int,help='Number of random recipes if --titles not provided')
@click.option('--out','-o',default='grocery.txt',help='Output file')
@click.pass_context
def grocery_cmd(ctx, titles, count, out):
    """Generate a grocery list for selected or random recipes."""
    store: Storage = ctx.obj["STORE"]
    chosen = []
    if titles.strip():
        for t in [x.strip() for x in titles.split(",") if x.strip()]:
            r = store.get_recipe(t)
            if not r:
                raise click.ClickException(f'Recipe "{t}" not found')
            chosen.append(r)
    else:
        if count <= 0:
            raise click.ClickException("Provide --titles or a positive --count")
        chosen = store.random_recipes(n=count)

    lines = store.grocery_list(chosen)
    with open(out, "w", encoding="utf-8") as f:
        for name, amt in lines:
            f.write(f"{name} - {amt}\n")
    click.echo(f"Wrote grocery list to {out}")

# ---------------------------
# Bulk import/export/snapshot
# ---------------------------

@cli.command(name="import")
@click.option("--fmt", type=click.Choice(["jsonl","json","csv"]), required=True)
@click.option("--file", "infile", type=click.Path(exists=True), required=True)
@click.pass_context
def import_cmd(ctx, fmt, infile):
    """Bulk import recipes from a file."""
    store: Storage = ctx.obj["STORE"]

    def iter_json():
        with open(infile, encoding="utf-8") as f:
            data = json.load(f)
            for r in data:
                yield _coerce_recipe(r)

    def iter_jsonl():
        with open(infile, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield _coerce_recipe(json.loads(line))

    def iter_csv():
        # CSV header: title,ingredients,steps,tags,(optional)servings,(optional)source_url
        with open(infile, newline="", encoding="utf-8") as f:
            rd = csv.DictReader(f)
            required = {"title", "ingredients", "steps"}
            missing = required - set(h.strip().lower() for h in rd.fieldnames or [])
            if missing:
                raise click.ClickException(f"CSV missing columns: {', '.join(sorted(missing))}")
            for row in rd:
                recipe = {
                    "title": row["title"].strip(),
                    "ingredients": {
                        kv.split(":", 1)[0].strip(): kv.split(":", 1)[1].strip()
                        for kv in row["ingredients"].split(",") if ":" in kv
                    } if row.get("ingredients") else {},
                    "steps": [s.strip() for s in row["steps"].split("|") if s.strip()] if row.get("steps") else [],
                    "tags": [t.strip() for t in (row.get("tags") or "").split(",") if t.strip()],
                }
                if row.get("servings"):
                    recipe["servings"] = row["servings"].strip()
                if row.get("source_url"):
                    recipe["source_url"] = row["source_url"].strip()
                yield recipe

    source = {"json": iter_json, "jsonl": iter_jsonl, "csv": iter_csv}[fmt]()
    added = store.import_iter(source)
    store.save()
    click.echo(f"Imported {added} new recipes into {ctx.obj['DB_PATH']}")

def _coerce_recipe(r: dict) -> Recipe:
    """Coerce arbitrary dict (json/jsonl) into our recipe shape."""
    r = {**r}
    r["title"] = r["title"].strip()
    r["ingredients"] = r.get("ingredients", {})
    r["steps"] = r.get("steps", [])
    r["tags"] = r.get("tags", [])
    return r

@cli.command(name='export')
@click.option("--fmt", type=click.Choice(["jsonl","json"]), default="json")
@click.option("--out", "outfile", type=click.Path(), required=True)
@click.pass_context
def export_cmd(ctx, fmt, outfile):
    """Export all recipes."""
    store: Storage = ctx.obj["STORE"]
    if fmt == "jsonl":
        with open(outfile, "w", encoding="utf-8") as f:
            for r in store.export_iter():
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    else:
        with open(outfile, "w", encoding="utf-8") as f:
            json.dump(list(store.export_iter()), f, ensure_ascii=False, indent=2)
    click.echo(f"Exported to {outfile}")

@cli.command(name='snapshot')
@click.option("--out", "outfile", type=click.Path(), required=True)
@click.pass_context
def snapshot_cmd(ctx, outfile):
    """
    Emit a single-file, denormalised JSON snapshot for publishing:
    [{title, tags, ingredients:[{name, amount}], steps:[...]}, ...]
    """
    store: Storage = ctx.obj["STORE"]
    pub = []
    for r in store.list_recipes():
        pub.append({
            "title": r["title"],
            "tags": r.get("tags", []),
            "ingredients": [{"name": k, "amount": v} for k, v in r.get("ingredients", {}).items()],
            "steps": r.get("steps", []),
        })
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(pub, f, ensure_ascii=False)
    click.echo(f"Wrote snapshot: {outfile}")

# ---------------------------
# Optional: migrate from legacy ORM DB to storage
# ---------------------------

@cli.command(name='migrate-from-orm')
@click.option('--module', default='models', help='Python module that defines SessionLocal and Recipe (default: models)')
@click.pass_context
def migrate_from_orm(ctx, module):
    """Migrate all recipes from an existing SQLAlchemy ORM DB into the current storage."""
    store: Storage = ctx.obj["STORE"]
    try:
        orm = __import__(module, fromlist=['SessionLocal', 'Recipe'])
        SessionLocal = getattr(orm, 'SessionLocal')
        RecipeModel = getattr(orm, 'Recipe')
    except Exception as e:
        raise click.ClickException(f"Could not import ORM module '{module}': {e}")

    session = SessionLocal()
    added = 0
    try:
        rows = session.query(RecipeModel).all()
        for row in rows:
            title = (row.title or '').strip()
            if not title:
                continue
            if store.get_recipe(title):
                continue
            # Map ORM shape -> storage
            # Assuming ORM uses: ingredients as list of {"name","quantity"}, steps as list[str], tags as list[str]
            ing = {}
            for item in (row.ingredients or []):
                name = item.get("name", "").strip()
                qty = item.get("quantity", "").strip()
                if name:
                    ing[name] = qty
            r = {
                "title": title,
                "ingredients": ing,
                "steps": list(row.steps or []),
                "tags": list(row.tags or []),
            }
            store.add_recipe(r)
            added += 1
        store.save()
    finally:
        session.close()
    click.echo(f"Migrated {added} recipe(s) from ORM into {ctx.obj['DB_PATH']}")

if __name__ == '__main__':
    cli()
