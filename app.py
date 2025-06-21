import os
import google.generativeai as genai
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
from dotenv import load_dotenv
import logging
import asyncio # Tambahkan ini untuk mengatur kebijakan event loop

# --- PENTING untuk Windows: Setel kebijakan asyncio ke ProactorEventLoop ---
# Ini membantu mencegah 'Event loop is closed' pada Windows saat menggunakan asyncio
# yang mungkin dipicu oleh library gRPC yang digunakan Gemini.
if os.name == 'nt': # 'nt' adalah nama OS untuk Windows
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Konfigurasi logging agar lebih mudah melihat pesan di terminal
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

# Tentukan path absolut untuk direktori root proyek (folder 'Gizi')
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Konfigurasi Flask agar tahu di mana mencari file statis dan template
app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'html'),
            static_folder=BASE_DIR)
CORS(app) # Mengizinkan permintaan dari frontend Anda

# --- KONFIGURASI GEMINI API KEY ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY environment variable not set. "
        "Pastikan Anda memiliki file .env di folder 'Gizi' (root proyek) "
        "dengan isi: GEMINI_API_KEY=YOUR_API_KEY_ANDA_DI_SINI"
    )

genai.configure(api_key=GEMINI_API_KEY)

# --- Inisialisasi Model Gemini ---
# Perhatikan: Tidak perlu 'async' di sini lagi karena kita akan memanggil metode sinkron
model = genai.GenerativeModel('gemini-1.5-flash')

# --- Fungsi SINKRON untuk Memanggil Gemini API ---
# Fungsi ini tidak lagi 'async' dan memanggil metode sinkron dari model Gemini.
def get_gemini_nutrition_info(item_name, age): # HAPUS 'async'
    """
    Membuat prompt untuk Gemini dan memanggil API untuk mendapatkan informasi nutrisi
    dan penilaian gizi secara SINKRON.
    """
    prompt_text = (
        f"Sebagai ahli gizi yang dapat memberikan estimasi, berikan informasi gizi esensial (Kalori, Protein, Karbohidrat, Lemak, Serat) "
        f"untuk '{item_name}'. "
        f"Jika data spesifik untuk merek atau produk olahan tersebut tidak tersedia, berikan estimasi berdasarkan "
        f"komposisi umum atau kategori produk serupa. "
        f"Kemudian, berikan penilaian singkat apakah kandungan gizi item ini baik, cukup, atau kurang baik "
        f"untuk seseorang dengan usia {age} tahun, berdasarkan Angka Kecukupan Gizi (AKG) umum di Indonesia. "
        f"Sajikan data nutrisi dalam format JSON di bawah kunci 'nutrisi' "
        f"dan penilaian gizi dalam teks singkat di bawah kunci 'penilaian'. "
        f"**Pastikan untuk SELALU memberikan estimasi nilai nutrisi dalam format angka dengan satuan (misal: '150 kcal', '5 g'), "
        f"bukan 'Tidak tersedia', meskipun itu adalah estimasi.** "
        f"Jika suatu nutrisi benar-benar tidak signifikan, berikan nilai '0 g' atau '0 kcal'.\n\n"
        f"Contoh format respons JSON yang diinginkan:\n"
        f'{{"nutrisi": {{"Kalori": "200 kcal", "Protein": "10 g", "Karbohidrat": "30 g", "Lemak": "5 g", "Serat": "3 g"}}, '
        f'"penilaian": "Untuk usia {age} tahun, item ini secara umum baik karena..."}}'
        f"Gunakan bahasa Indonesia."
    )

    try:
        # Panggil metode SINKRON generate_content()
        response = model.generate_content(prompt_text) # HAPUS 'await'
        response_text = response.text.strip()
        logging.info(f"DEBUG Gemini Raw Response for '{item_name}': {response_text[:200]}...")

        # Menghapus blok kode jika ada (misal: ```json ... ```)
        if response_text.startswith("```json") and response_text.endswith("```"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```") and response_text.endswith("```"):
            response_text = response_text[3:-3].strip()
        
        # Jika respons setelah stripping masih kosong atau tidak valid untuk JSON
        if not response_text:
            logging.error(f"DEBUG: Respons Gemini kosong atau hanya whitespace setelah stripping untuk '{item_name}'.")
            return {"error": "Maaf, Gemini tidak dapat memberikan data. Respons kosong.", "debug_response": "Empty response after stripping."}

        try:
            parsed_data = json.loads(response_text)
            return parsed_data
        except json.JSONDecodeError as json_e: # Tangkap error parsing JSON secara spesifik
            logging.error(f"DEBUG: Gagal parsing JSON dari Gemini untuk '{item_name}': {json_e}")
            logging.error(f"DEBUG: Respons JSON yang gagal diparsing: '{response_text}'")
            return {"error": "Maaf, Gemini tidak dapat memberikan data dalam format yang diharapkan. Mohon coba lagi atau gunakan masukan yang lebih spesifik.",
                    "debug_response": response_text}

    except Exception as e: # Tangkap semua jenis error yang mungkin terjadi saat memanggil Gemini
        logging.error(f"Error calling Gemini API for '{item_name}': {e}", exc_info=True)
        return {"error": f"Terjadi kesalahan saat menghubungi layanan gizi eksternal. (Detail: {e})."}

# --- ROUTE UTAMA APLIKASI (juga SINKRON) ---
@app.route('/check_gizi', methods=['POST'])
def check_gizi(): # HAPUS 'async'
    """
    Endpoint Flask yang menerima permintaan dari frontend, memanggil Gemini API untuk makanan dan/atau minuman secara SINKRON,
    dan mengembalikan hasilnya secara gabungan.
    """
    try:
        data = request.json
        food_name = data.get('food', '').strip().lower()
        drink_name = data.get('drink', '').strip().lower()
        age = data.get('age')

        results = {}

        if not isinstance(age, int) or age <= 0:
            return jsonify({"error": "Usia tidak valid. Harap masukkan usia yang benar."}), 400

        # Panggil get_gemini_nutrition_info secara SINKRON
        if food_name:
            food_gemini_result = get_gemini_nutrition_info(food_name, age) # HAPUS 'await'
            if "error" in food_gemini_result:
                results['food_error'] = food_gemini_result['error']
            else:
                results['food'] = {
                    "name": food_name.capitalize(),
                    "nutrients": food_gemini_result.get("nutrisi", {}),
                    "assessment": food_gemini_result.get("penilaian", "Tidak ada penilaian gizi dari Gemini.")
                }
        
        # Panggil get_gemini_nutrition_info secara SINKRON
        if drink_name:
            drink_gemini_result = get_gemini_nutrition_info(drink_name, age) # HAPUS 'await'
            if "error" in drink_gemini_result:
                results['drink_error'] = drink_gemini_result['error']
            else:
                results['drink'] = {
                    "name": drink_name.capitalize(),
                    "nutrients": drink_gemini_result.get("nutrisi", {}),
                    "assessment": drink_gemini_result.get("penilaian", "Tidak ada penilaian gizi dari Gemini.")
                }

        # Jika tidak ada input makanan atau minuman yang valid sama sekali
        if not food_name and not drink_name:
            return jsonify({"error": "Harap masukkan nama makanan atau minuman."}), 400

        results['age'] = age

        return jsonify(results)
    except Exception as route_e:
        logging.error(f"Unhandled error in /check_gizi route: {route_e}", exc_info=True)
        return jsonify({"error": f"Terjadi kesalahan internal pada server: {route_e}"}), 500

# --- ROUTE UNTUK MELAYANI FRONTEND (TIDAK BERUBAH) ---
@app.route('/')
def serve_index():
    """Melayani file index.html dari folder html di root proyek."""
    return send_from_directory(app.template_folder, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """
    Melayani file statis (CSS, JS, dll.) dari subfolder di root proyek.
    (Misal: /css/style.css, /js/script.js)
    """
    # Mengatasi permintaan untuk file di subfolder langsung dari root
    # Contoh: /css/style.css akan dicari di Gizi/css/style.css
    # Contoh: /js/script.js akan dicari di Gizi/js/script.js
    if filename.startswith('static/') or filename.startswith('static/'):
        # Memisahkan path untuk mengirim dari subdirektori yang benar
        directory, file = os.path.split(filename)
        return send_from_directory(os.path.join(app.static_folder, directory), file)
    
    # Jika file ada di root static_folder (misal: kalau ada file langsung di Gizi/)
    return send_from_directory(app.static_folder, filename)
    
# --- MENJALANKAN APLIKASI FLASK ---
if __name__ == '__main__':
    # Untuk menjalankan aplikasi Flask secara sinkron, Anda bisa kembali menggunakan app.run()
    # Pastikan debug=False untuk stabilitas.
    app.run(debug=False, host="0.0.0.0", PORT=int(os.environ.get("PORT", 5000)))