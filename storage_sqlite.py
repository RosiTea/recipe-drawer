# storage_sqlite.py
import json, sqlite3, random
from typing import List, Dict, Any, Optional, Iterable, Tuple
from storage import Storage, Recipe, GroceryLine

DDL = """
CREATE TABLE IF NOT EXISTS recipes(
  id INTEGER PRIMARY KEY,
  title TEXT UNIQUE NOT NULL,
  steps_json TEXT NOT NULL,
  ingredients_json TEXT NOT NULL,
  tags_json TEXT NOT NULL,
  servings TEXT,
  source_url TEXT
);
"""

def _row_to_recipe(row) -> Recipe:
    _, title, steps, ings, tags, servings, url = row
    r: Recipe = {
        "title": title,
        "steps": json.loads(steps),
        "ingredients": json.loads(ings),
        "tags": json.loads(tags),
    }
    if servings is not None: r["servings"] = servings
    if url: r["source_url"] = url
    return r

class SqliteStorage(Storage):
    def __init__(self, path: str):
        self.con = sqlite3.connect(path)
        self.con.execute(DDL)

    def save(self) -> None:
        self.con.commit()

    def list_recipes(self) -> List[Recipe]:
        cur = self.con.execute("SELECT * FROM recipes ORDER BY title")
        return [_row_to_recipe(r) for r in cur.fetchall()]

    def get_recipe(self, title: str) -> Optional[Recipe]:
        cur = self.con.execute("SELECT * FROM recipes WHERE lower(title)=lower(?)", (title.strip(),))
        row = cur.fetchone()
        return _row_to_recipe(row) if row else None

    def add_recipe(self, r: Recipe) -> None:
        r = {**r}  # shallow copy
        r.setdefault("tags", [])
        r.setdefault("steps", [])
        r.setdefault("ingredients", {})
        self.con.execute(
            "INSERT INTO recipes(title,steps_json,ingredients_json,tags_json,servings,source_url) VALUES (?,?,?,?,?,?)",
            (
                r["title"],
                json.dumps(r["steps"], ensure_ascii=False),
                json.dumps(r["ingredients"], ensure_ascii=False),
                json.dumps(r["tags"], ensure_ascii=False),
                str(r.get("servings")) if r.get("servings") is not None else None,
                r.get("source_url"),
            ),
        )

    def delete_recipe(self, title: str) -> bool:
        cur = self.con.execute("DELETE FROM recipes WHERE lower(title)=lower(?)", (title.strip(),))
        return cur.rowcount > 0

    def random_recipes(self, n=1, tag=None) -> List[Recipe]:
        if tag:
            cur = self.con.execute("SELECT * FROM recipes")
            pool = [_row_to_recipe(r) for r in cur.fetchall() if tag in json.loads(r[4])]
        else:
            cur = self.con.execute("SELECT * FROM recipes")
            pool = [_row_to_recipe(r) for r in cur.fetchall()]
        if not pool:
            return []
        return random.sample(pool, k=min(n, len(pool)))

    def grocery_list(self, recipes: List[Recipe]) -> List[GroceryLine]:
        lines: List[GroceryLine] = []
        for r in recipes:
            for ing, amt in r.get("ingredients", {}).items():
                lines.append((ing, amt))
        return lines

    def import_iter(self, recipes: Iterable[Recipe]) -> int:
        c = 0
        for r in recipes:
            if not self.get_recipe(r["title"]):
                self.add_recipe(r); c += 1
        return c

    def export_iter(self) -> Iterable[Recipe]:
        for r in self.list_recipes():
            yield r
