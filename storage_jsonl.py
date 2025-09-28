# storage_jsonl.py
import json, random
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterable, Tuple
from storage import Storage, Recipe, GroceryLine

def _norm_title(t: str) -> str:
    return t.strip().lower()

class JsonlStorage(Storage):
    def __init__(self, path: Path):
        self.path = path
        self._recipes: List[Recipe] = []
        if path.exists():
            with path.open(encoding="utf-8") as f:
                self._recipes = [json.loads(line) for line in f if line.strip()]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            for r in self._recipes:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def list_recipes(self) -> List[Recipe]:
        return list(self._recipes)

    def get_recipe(self, title: str) -> Optional[Recipe]:
        t = _norm_title(title)
        return next((r for r in self._recipes if _norm_title(r["title"]) == t), None)

    def add_recipe(self, recipe: Recipe) -> None:
        if self.get_recipe(recipe["title"]):
            raise ValueError(f"Recipe with title '{recipe['title']}' already exists")
        # Normalise shape
        recipe.setdefault("tags", [])
        recipe.setdefault("steps", [])
        recipe.setdefault("ingredients", {})
        self._recipes.append(recipe)

    def delete_recipe(self, title: str) -> bool:
        before = len(self._recipes)
        self._recipes = [r for r in self._recipes if _norm_title(r["title"]) != _norm_title(title)]
        return len(self._recipes) < before

    def random_recipes(self, n=1, tag=None) -> List[Recipe]:
        pool = self._recipes if not tag else [r for r in self._recipes if tag in r.get("tags", [])]
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
                self.add_recipe(r)
                c += 1
        return c

    def export_iter(self) -> Iterable[Recipe]:
        yield from self._recipes