# recipe-drawer
A simple tool to help you decide what to cook tonight

## Features
- Initialise a recipe database (JSONL by default, SQLite optional)
- Seed with sample recipes: `init --with-samples`
- List all recipes: `list`
- Add recipes interactively: `add`
- Delete recipes interactively: `delete`
- Pick random recipes with optional tags and count: `random -t vegetarian -n 2`
- Export grocery list aggregating quantities: `grocery --count 3 -o list.txt`
- Bulk import recipes from CSV/JSON/JSONL: `import`
- Export all recipes to JSON/JSONL: `export`
- Create a publishable snapshot: `snapshot`
- Optional: migrate recipes from an existing SQLAlchemy ORM DB: `migrate-from-orm`

## Installation
1. Clone the repo and `cd recipe-drawer`
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
By default, commands operate on `recipes.jsonl`.
You can override with `--db` to use SQLite (`recipes.sqlite`) or another file.
```bash
# Initialize DB with samples
python cli.py init --with-samples
```

### Listing Recipes
```bash
python cli.py list
```

### Adding Recipes
To add a new recipe, run:
```bash
python cli.py add
```
You'll be prompted for:
- **Title**: e.g., `Pancakes`
- **Ingredients**: comma-separated `name:quantity` pairs. For example:
  ```
  flour:200g,milk:250ml,egg:1,sugar:2 tbsp
  ```
- **Steps**: pipe-separated list of instructions. For example:
  ```
  Mix batter|Cook on griddle|Serve warm
  ```
- **Tags** (optional): comma-separated keywords. For example:
  ```
  breakfast,vegetarian
  ```

```bash
# Example interactive session:
$ python cli.py add
Title: Pancakes
Ingredients: flour:200g,milk:250ml,egg:1,sugar:2 tbsp
Steps: Mix batter|Cook on griddle|Serve warm
Tags: breakfast,vegetarian
Recipe "Pancakes" added.
```

### Deleting Recipes
```bash
python cli.py delete
```
Enter the exact recipe title when prompted to remove it. 
You can also use `-t "Exact_recipe_name"` to remove that recipe.

### Random Recipes
```bash
# Single random recipe
python cli.py random
# Filter by tag
python cli.py random -t breakfast
# Two random recipes
python cli.py random -n 2
```

### Grocery List
```bash
# Generate grocery list for all recipes
python cli.py grocery
# For 2 random recipes
python cli.py grocery -count 2 -out list.txt
```

### Bulk Import
You can load many recipes at once from a CSV, JSON, or JSONL file.
CSV format requires headers (`tags`, `servings` and `source_url` are optional):
  ```
  title,ingredients,steps,tags,servings,source_url
  ```
Example row:
  ```csv
  Spinach Egg Omelette,"spinach:250g,eggs:4,salt:1 tsp,pepper:1 tsp","Beat the eggs with salt and pepper|Blench spinach then squeeze dry and cool|Mix egg and spinach|Heat a pan and add oil and mixture - low heat|Roll on pan","breakfast,quick,vegetarian"
  ```
Import into the DB:
```bash
python cli.py import --fmt csv --file recipes.csv
```

### Export
Export all recipes:
```bash
python cli.py export --fmt json --out all_recipes.json
```

### Snapshot
Produce a denormalised JSON file optimised for publishing:
```bash
python cli.py snapshot --out recipes.snapshot.json
```

Help yourself cooking! x