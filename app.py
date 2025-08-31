import os
import json
from typing import List, Dict, Any, Tuple
import streamlit as st
from PIL import Image

from utils import (
    load_recipes,
    normalize_ingredients,
    match_recipes,
    filter_recipes,
    scale_servings_text,
    suggest_substitutions_for_list,
    star_rating_widget,
    save_favorite,
    get_user_favorites,
    DIET_OPTIONS,
    DIFFICULTY_OPTIONS,
)

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="Smart Recipe Generator",
    page_icon="🍳",
    layout="wide",
)

# -----------------------------
# Session state init
# -----------------------------
if "ratings" not in st.session_state:
    st.session_state["ratings"] = {}  # {recipe_name: int}
if "favorites" not in st.session_state:
    st.session_state["favorites"] = []  # list of recipe names

# -----------------------------
# Header
# -----------------------------
st.title("🍳 Smart Recipe Generator")
st.caption("Suggests recipes from your ingredients, supports images, filters, and preferences.")

# -----------------------------
# Sidebar Controls
# -----------------------------
with st.sidebar:
    st.header("⚙️ Preferences & Filters")
    diet_pref = st.selectbox("Dietary preference", DIET_OPTIONS, index=0)
    max_time = st.slider("Max cooking time (minutes)", min_value=5, max_value=180, value=45, step=5)
    difficulty = st.selectbox("Difficulty", ["Any"] + DIFFICULTY_OPTIONS, index=0)
    servings = st.number_input("Desired servings", min_value=1, max_value=12, value=2, step=1)

    st.markdown("---")
    st.subheader("📸 Ingredient from Image ")
    img_file = st.file_uploader("Upload a food image (jpg/png)", type=["jpg", "jpeg", "png"])
    detect_btn = st.button("Detect ingredients from image")

# -----------------------------
# Load recipes
# -----------------------------
RECIPES_PATH = os.environ.get("RECIPES_PATH", "recipes.json")
recipes = load_recipes(RECIPES_PATH)

# -----------------------------
# Ingredient input
# -----------------------------
st.subheader("🧺 Ingredients")
default_ing = "tomato, onion, garlic, rice, egg"
ing_text = st.text_input("Type available ingredients (comma-separated):", value=default_ing)

detected_from_image: List[str] = []
if img_file and detect_btn:
    with st.spinner("Analyzing image for ingredients..."):
        try:
            image = Image.open(img_file).convert("RGB")
        except Exception as e:
            st.error(f"Couldn't open image: {e}")
            image = None

        if image is not None:
            # Try local transformers pipeline first, else try HF Inference API, else fallback
            try:
                from transformers import pipeline
                classifier = pipeline("image-classification", model="nateraw/food")
                preds = classifier(image)[:5]
                detected_from_image = [p["label"].lower() for p in preds]
                st.success(f"Detected (local model): {', '.join(detected_from_image)}")
            except Exception as e_local:
                # Optional: HuggingFace Inference API
                import requests
                HF_TOKEN = os.environ.get("hf_rSqveoMyOZqbQCRAQYqIESOTCGFzvJoljKsr")
                if HF_TOKEN:
                    try:
                        API_URL = "https://api-inference.huggingface.co/models/nateraw/food"
                        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
                        import io
                        buffered = io.BytesIO()
                        image.save(buffered, format="PNG")
                        resp = requests.post(API_URL, headers=headers, data=buffered.getvalue(), timeout=30)
                        resp.raise_for_status()
                        outputs = resp.json()
                        # Expect list of dicts with 'label' and 'score'
                        detected_from_image = [o.get("label", "").lower() for o in outputs[:5] if isinstance(o, dict)]
                        if detected_from_image:
                            st.success(f"Detected (HF API): {', '.join(detected_from_image)}")
                        else:
                            st.warning("No labels returned by HF API. Try typing ingredients.")
                    except Exception as e_api:
                        st.warning("Image detection unavailable right now. Please use text input.")
                        st.caption(f"(Local model error: {e_local}; HF API error: {e_api})")
                else:
                    st.warning("Image detection model not available. Set HF_TOKEN env var or rely on text input.")
                    st.caption(f"(Local model error: {e_local})")

# Merge text + detected ingredients
user_ingredients = normalize_ingredients(ing_text)
user_ingredients += [x for x in detected_from_image if x not in user_ingredients]

# Show current ingredients
if user_ingredients:
    st.write("**Using ingredients:**", ", ".join(sorted(set(user_ingredients))))

# -----------------------------
# Substitutions (preview)
# -----------------------------
with st.expander("🔁 See suggested substitutions for your ingredients"):
    subs = suggest_substitutions_for_list(user_ingredients)
    if subs:
        for need, options in subs.items():
            st.write(f"- **{need}** ➜ {', '.join(options)}")
    else:
        st.info("No substitutions suggested yet. Add more common pantry items to see tips.")

# -----------------------------
# Matching & Filtering
# -----------------------------
st.subheader("🍽️ Recipe Suggestions")
matched = match_recipes(user_ingredients, recipes, diet_pref=diet_pref)
filtered = filter_recipes(
    [r for _, r in matched],
    max_time=max_time,
    difficulty=None if difficulty == "Any" else difficulty,
    diet_pref=diet_pref,
)

if not filtered:
    st.warning("No recipes matched your inputs and filters. Try relaxing filters or adding more ingredients.")
else:
    # Show top 10
    for recipe in filtered[:10]:
        with st.container(border=True):
            cols = st.columns([3, 1])
            with cols[0]:
                st.markdown(f"### {recipe['name']}")
                meta = f"⏱️ {recipe['time']} min · 🎯 {recipe['difficulty']} · 🥗 {recipe['diet']}"
                st.caption(meta)

                if recipe.get("image"):
                    st.image(recipe["image"], use_column_width=True)

                st.markdown("**Ingredients:** " + ", ".join(recipe["ingredients"]))
                st.markdown("**Steps:**")
                for i, step in enumerate(recipe["steps"], 1):
                    st.markdown(f"{i}. {scale_servings_text(step, recipe.get('servings', 2), servings)}")

                nut = recipe.get("nutrition", {})
                if nut:
                    st.markdown(f"**Nutrition (per serving):** {nut.get('calories','?')} kcal · "
                                f"Protein {nut.get('protein','?')} g")

                # Rating
                star_rating_widget(recipe["name"])

                # Favorites
                fav_col1, fav_col2 = st.columns(2)
                with fav_col1:
                    if st.button("⭐ Save to Favorites", key=f"fav_{recipe['name']}"):
                        save_favorite(recipe['name'])
                        st.toast("Saved to favorites!")
                with fav_col2:
                    st.caption("Your rating and favorites persist during this session.")

            with cols[1]:
                st.markdown("**Missing & Subs**")
                missing = [ing for ing in recipe["ingredients"] if ing not in user_ingredients]
                if missing:
                    st.write(", ".join(missing))
                    # Simple substitution ideas
                    rec_subs = suggest_substitutions_for_list(missing)
                    if rec_subs:
                        st.markdown("**Try instead:**")
                        for need, options in rec_subs.items():
                            st.write(f"- {need}: {', '.join(options)}")
                else:
                    st.success("You have all ingredients!")

# -----------------------------
# Favorites Page
# -----------------------------
with st.expander("⭐ Your Favorites"):
    favs = get_user_favorites()
    if favs:
        st.write(", ".join(favs))
    else:
        st.info("No favorites yet. Click 'Save to Favorites' on a recipe to add it.")

# -----------------------------
# Footer
# -----------------------------
st.markdown("---")
st.caption("Built with Streamlit • Image ingredient detection via transformers or HuggingFace Inference API • ")
