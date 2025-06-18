# recipe-drawer
A simple tool to help you decide what to cook tonight
# README.md
# ---------
# Recipe Drawer CLI

A simple command-line tool to manage and randomize recipes using SQLite.

## Features
- Initialize DB with samples: `init` (`--force` to reset)
- List all recipes: `list`
- Add recipes interactively: `add`
- Delete recipes interactively: `delete`
- Random pick with optional tags and count: `random -t vegetarian -n 2`
- Export grocery list aggregating quantities: `grocery -n 3 -f list.txt`

## Installation
1. Clone the repo and `cd recipe_randomizer`
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
```bash
# Initialize DB with samples
python cli.py init
# Reset and reload samples
python cli.py init --force
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
- **Steps**: comma-separated list of instructions. For example:
  ```
  Mix batter,Cook on griddle,Serve warm
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
Steps: Mix batter,Cook on griddle,Serve warm
Tags: breakfast,vegetarian
Recipe "Pancakes" added.
```

### Deleting Recipes
```bash
python cli.py delete
```
Enter the exact recipe title when prompted to remove it.

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
python cli.py grocery -n 2 -f list.txt
```

Feel free to contribute recipes via the `add` command or by editing the DB directly.
