# Smart Recipe Generator 🍳

A Streamlit app that suggests recipes based on available ingredients (typed or detected from an image).  
Includes recipe matching, filters (time, difficulty, diet), serving size hints, ratings, favorites, and basic nutrition info.

## ✨ Features
- Ingredient input via **text** and optional **image detection**
- **Recipe matching** by ingredient overlap (+ substitution tips)
- **Filters:** difficulty, max cooking time, dietary preference
- **Serving size** scaling hints
- **Favorites** and **star ratings** (in-session)
- **Predefined database**: 20+ recipes with steps and nutrition
- **Mobile-responsive** Streamlit UI
- **Deployment-ready**

## 🧠 Ingredient Recognition from Images
Two ways (both optional):
1. **Local transformers** model: `nateraw/food` (auto-downloaded when available)
2. **Hugging Face Inference API**: set env var `HF_TOKEN`

If models are unavailable, the app gracefully **falls back** to text input.

## 🚀 Quickstart

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 🌐 Deploy (Streamlit Cloud)
1. Push these files to GitHub.
2. On Streamlit Cloud, create a new app from your repo.
3. (Optional) Add `HF_TOKEN` as a **secret** if you want image detection via API.

## ⚙️ Files
- `app.py` — main Streamlit app
- `utils.py` — matching, filters, substitutions, ratings/favorites helpers
- `recipes.json` — 20+ sample recipes with nutrition
- `requirements.txt` — dependencies
- `README.md` — docs

## 🧪 Recipe Matching Logic (Summary)
- Score = matches - 0.35 × missing
- Filter by time ≤ slider, difficulty, and diet preference
- Show top results with missing-ingredient substitutions

## 🧰 Error Handling & UX
- Try/except around image detection with clear fallbacks
- Loading spinner during image analysis
- Toasts for favorites
- Session-persistent ratings/favorites

## 📄 License
For educational/demo use.