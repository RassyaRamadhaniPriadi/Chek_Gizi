import os
import json
import logging
import asyncio
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai

# --- Windows-specific asyncio policy ---
if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# --- Konfigurasi logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Load environment variables ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY tidak ditemukan. "
        "Pastikan file .env berisi: GEMINI_API_KEY=YOUR_API_KEY"
    )

# --- Konfigurasi Gemini ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- Path folder ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# --- Inisialisasi Flask ---
app = Flask(__name__, template_folder="html", static_folder="static")

CORS(app)

# ============================
# === ROUTE STATIC/INDEX ====
# ============================

@app.route('/')
def serve_index():
    """Melayani halaman utama."""
    logging.info("Serving index.html from / route")
    return send_from_directory(app.template_folder, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Melayani file statis dari root atau subfolder (css/js)."""
    directory, file = os.path.split(filename)
    return send_from_directory(os.path.join(app.static_folder, directory), file)

# ============================
# === ROUTE API: /check_gizi ===
# ============================

@app.route('/check_gizi', methods=['POST'])
def check_gizi():
    """Menerima data makanan/minuman & usia, kirim prompt ke Gemini."""
    try:
        data = request.json
        food_name = data.get('food', '').strip().lower()
        drink_name = data.get('drink', '').strip().lower()
        age = data.get('age')

        if not isinstance(age, int) or age <= 0:
            return jsonify({"error": "Usia tidak valid. Harap masukkan usia yang benar."}), 400

        results = {"age": age}

        if not food_name and not drink_name:
            return jsonify({"error": "Harap masukkan nama makanan atau minuman."}), 400

        if food_name:
            food_result = get_gemini_nutrition_info(food_name, age)
            if "error" in food_result:
                results['food_error'] = food_result['error']
            else:
                results['food'] = {
                    "name": food_name.capitalize(),
                    "nutrients": food_result.get("nutrisi", {}),
                    "assessment": food_result.get("penilaian", "Tidak ada penilaian.")
                }

        if drink_name:
            drink_result = get_gemini_nutrition_info(drink_name, age)
            if "error" in drink_result:
                results['drink_error'] = drink_result['error']
            else:
                results['drink'] = {
                    "name": drink_name.capitalize(),
                    "nutrients": drink_result.get("nutrisi", {}),
                    "assessment": drink_result.get("penilaian", "Tidak ada penilaian.")
                }

        return jsonify(results)

    except Exception as e:
        logging.error("Unhandled error in /check_gizi route", exc_info=True)
        return jsonify({"error": f"Terjadi kesalahan internal: {e}"}), 500

# ================================
# === Fungsi untuk Gemini API ===
# ================================

def get_gemini_nutrition_info(item_name, age):
    """Membuat prompt untuk Gemini & parsing hasilnya ke JSON."""
    prompt = (
        f"Sebagai ahli gizi, berikan estimasi informasi nutrisi untuk '{item_name}' "
        f"dalam format JSON (nutrisi & penilaian) sesuai AKG usia {age}. "
        f"Contoh: {{\"nutrisi\": {{\"Kalori\": \"200 kcal\", \"Protein\": \"10 g\"}}, \"penilaian\": \"Item ini baik untuk...\"}}. "
        f"Gunakan Bahasa Indonesia."
    )

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        if response_text.startswith("```json") and response_text.endswith("```"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```") and response_text.endswith("```"):
            response_text = response_text[3:-3].strip()

        if not response_text:
            return {"error": "Respons kosong dari Gemini.", "debug_response": "Empty response after stripping."}

        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logging.error(f"JSON parsing error: {e}")
            logging.debug(f"Raw response: {response_text}")
            return {"error": "Format respons tidak valid.", "debug_response": response_text}

    except Exception as e:
        logging.error(f"Error calling Gemini: {e}", exc_info=True)
        return {"error": f"Kesalahan saat menghubungi Gemini: {e}"}

# =======================
# === Menjalankan App ===
# =======================

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
