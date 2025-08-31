from __future__ import annotations
import os, json, re
from typing import List, Dict, Any, Tuple

# Constant options
DIET_OPTIONS = ["None", "Vegetarian", "Vegan", "Gluten-Free", "Pescatarian", "Keto"]
DIFFICULTY_OPTIONS = ["Easy", "Medium", "Hard"]

# Simple substitution dictionary (extend as needed)
SUBSTITUTIONS = {
    "butter": ["ghee", "olive oil"],
    "milk": ["almond milk", "oat milk", "soy milk"],
    "egg": ["tofu", "chia egg", "flax egg"],
    "yogurt": ["coconut yogurt"],
    "cream": ["evaporated milk", "coconut cream"],
    "chicken": ["tofu", "paneer", "chickpeas"],
    "paneer": ["tofu", "halloumi"],
    "rice": ["quinoa", "millets"],
    "wheat flour": ["gluten-free flour blend"],
    "soy sauce": ["tamari", "coconut aminos"],
    "cheese": ["nutritional yeast"],
    "mayonnaise": ["hung curd", "greek yogurt"],
    "tomato": ["canned tomato", "tomato puree"],
    "onion": ["shallots", "spring onion"],
    "garlic": ["garlic powder"],
    "buttermilk": ["milk + lemon juice"],
}

def load_recipes(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"recipes file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Normalize minor fields
    for r in data:
        r["ingredients"] = [i.lower().strip() for i in r.get("ingredients", [])]
        r["diet"] = r.get("diet", "None")
        r["difficulty"] = r.get("difficulty", "Easy")
        r["time"] = int(r.get("time", 20))
        r["servings"] = int(r.get("servings", 2))
    return data

def normalize_ingredients(text: str) -> List[str]:
    if not text:
        return []
    parts = re.split(r"[,\n]+", text.lower())
    clean = [p.strip() for p in parts if p.strip()]
    return list(dict.fromkeys(clean))  # dedupe preserve order

def _overlap_score(user: List[str], recipe_ing: List[str]) -> Tuple[int, int, float]:
    suser = set(user)
    srec = set(recipe_ing)
    matches = len(suser & srec)
    missing = len(srec - suser)
    # Weighted score: prioritize matches, small penalty for missing
    score = matches - 0.35 * missing
    return matches, missing, score

def match_recipes(user_ingredients: List[str], recipes: List[Dict[str, Any]], diet_pref: str="None") -> List[Tuple[float, Dict[str, Any]]]:
    ranked = []
    for r in recipes:
        # diet filter early if requested
        if diet_pref != "None" and r.get("diet") != diet_pref:
            continue
        matches, missing, score = _overlap_score(user_ingredients, r["ingredients"])
        if matches == 0:
            continue
        ranked.append((score, r))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return ranked

def filter_recipes(recipes: List[Dict[str, Any]], max_time: int=60, difficulty: str|None=None, diet_pref: str="None") -> List[Dict[str, Any]]:
    out = []
    for r in recipes:
        if r["time"] > max_time:
            continue
        if difficulty and r["difficulty"] != difficulty:
            continue
        if diet_pref != "None" and r.get("diet") != diet_pref:
            continue
        out.append(r)
    return out

def scale_servings_text(step: str, base_servings: int, target_servings: int) -> str:
    # Very simple scaling hint appended to steps (human-readable)
    if base_servings == target_servings:
        return step
    return f"{step} _(scale x{target_servings/base_servings:.1f})_"

def suggest_substitutions_for_list(missing: List[str]) -> Dict[str, List[str]]:
    out = {}
    for item in missing:
        if item in SUBSTITUTIONS:
            out[item] = SUBSTITUTIONS[item]
    return out

def star_rating_widget(recipe_name: str):
    import streamlit as st
    # 1..5 stars selection using radio
    current = st.session_state["ratings"].get(recipe_name, 0)
    rating = st.radio("Rate this recipe", options=[0,1,2,3,4,5], index=current, horizontal=True, key=f"rate_{recipe_name}")
    st.session_state["ratings"][recipe_name] = rating

def save_favorite(recipe_name: str):
    import streamlit as st
    if recipe_name not in st.session_state["favorites"]:
        st.session_state["favorites"].append(recipe_name)

def get_user_favorites() -> List[str]:
    import streamlit as st
    return st.session_state.get("favorites", [])
