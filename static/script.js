document.addEventListener('DOMContentLoaded', () => {
    const foodNameInput = document.getElementById('foodName');
    const drinkNameInput = document.getElementById('drinkName');
    const userAgeInput = document.getElementById('userAge');
    const checkGiziBtn = document.getElementById('checkGiziBtn');
    const loadingSection = document.getElementById('loadingSection');
    const resultsSection = document.getElementById('resultsSection');
    const resultsContent = document.getElementById('resultsContent');

    // --- Data Fakta Gizi Acak (Fitur Baru) ---
    const nutritionFacts = [
        "Tahukah Kamu? Konsumsi air yang cukup sangat penting untuk menjaga fungsi tubuh dan metabolisme!",
        "Tahukah Kamu? Serat dari buah dan sayur membantu pencernaan dan menjaga kadar gula darah stabil.",
        "Tahukah Kamu? Protein tidak hanya membangun otot, tapi juga penting untuk enzim dan hormon tubuh!",
        "Tahukah Kamu? Lemak sehat seperti dari alpukat dan kacang-kacangan esensial untuk otak dan penyerapan vitamin.",
        "Tahukah Kamu? Vitamin C, yang banyak di jeruk, adalah antioksidan kuat untuk kekebalan tubuh.",
        "Tahukah Kamu? Kurangi gula tambahan, karena dapat meningkatkan risiko penyakit kronis.",
        "Tahukah Kamu? Sarapan adalah kunci untuk memulai metabolisme Anda di pagi hari!",
        "Tahukah Kamu? Tidur yang cukup sama pentingnya dengan nutrisi untuk kesehatan optimal.",
        "Tahukah Kamu? Warna-warni di piring Anda berarti lebih banyak nutrisi dan antioksidan berbeda!",
        "Tahukah Kamu? Kalsium dari susu atau sayuran hijau penting untuk tulang yang kuat sepanjang hidup."
    ];

    // Fungsi untuk menampilkan fakta gizi acak saat halaman dimuat
    function displayRandomNutritionFact() {
        const randomIndex = Math.floor(Math.random() * nutritionFacts.length);
        const fact = nutritionFacts[randomIndex];
        // Buat elemen untuk menampilkan fakta, atau update elemen yang ada jika mau
        // Untuk saat ini, kita bisa menampilkannya di konsol atau di tempat lain jika ada elemen UI khusus.
        // Sebagai contoh, kita bisa menampilkannya di bagian deskripsi awal atau di footer.
        // Untuk demo ini, mari kita ubah placeholder hasil analisis menjadi fakta acak saat pertama kali.
        resultsContent.innerHTML = `<p class="placeholder-message">${fact}</p>`;
    }

    displayRandomNutritionFact(); // Panggil saat halaman dimuat

    // --- Fungsi Tampilan UI ---
    function showLoading() {
        resultsContent.innerHTML = ''; // Hapus hasil sebelumnya
        resultsSection.style.display = 'none'; // Sembunyikan area hasil
        loadingSection.style.display = 'block'; // Tampilkan spinner loading
        checkGiziBtn.disabled = true; // Nonaktifkan tombol saat loading
    }

    function hideLoading() {
        loadingSection.style.display = 'none'; // Sembunyikan spinner loading
        resultsSection.style.display = 'block'; // Tampilkan area hasil kembali
        checkGiziBtn.disabled = false; // Aktifkan kembali tombol
    }

    function displayResults(data) {
        let html = '';

        if (data.food_error) {
            html += `<div class="error-message">Gagal menganalisis Makanan: ${data.food_error}</div>`;
        } else if (data.food) {
            html += `
                <div class="nutrition-result">
                    <h3>Analisis Makanan: ${data.food.name}</h3>
                    <div class="nutrients">
                        <p><strong>Kalori:</strong> ${data.food.nutrients.Kalori || 'Tidak tersedia'}</p>
                        <p><strong>Protein:</strong> ${data.food.nutrients.Protein || 'Tidak tersedia'}</p>
                        <p><strong>Karbohidrat:</strong> ${data.food.nutrients.Karbohidrat || 'Tidak tersedia'}</p>
                        <p><strong>Lemak:</strong> ${data.food.nutrients.Lemak || 'Tidak tersedia'}</p>
                        <p><strong>Serat:</strong> ${data.food.nutrients.Serat || 'Tidak tersedia'}</p>
                    </div>
                    <div class="assessment">
                        <p><strong>Penilaian Gizi:</strong> ${data.food.assessment || 'Tidak ada penilaian.'}</p>
                    </div>
                </div>
            `;
        }

        if (data.drink_error) {
            html += `<div class="error-message">Gagal menganalisis Minuman: ${data.drink_error}</div>`;
        } else if (data.drink) {
            html += `
                <div class="nutrition-result">
                    <h3>Analisis Minuman: ${data.drink.name}</h3>
                    <div class="nutrients">
                        <p><strong>Kalori:</strong> ${data.drink.nutrients.Kalori || 'Tidak tersedia'}</p>
                        <p><strong>Protein:</strong> ${data.drink.nutrients.Protein || 'Tidak tersedia'}</p>
                        <p><strong>Karbohidrat:</strong> ${data.drink.nutrients.Karbohidrat || 'Tidak tersedia'}</p>
                        <p><strong>Lemak:</strong> ${data.drink.nutrients.Lemak || 'Tidak tersedia'}</p>
                        <p><strong>Serat:</strong> ${data.drink.nutrients.Serat || 'Tidak tersedia'}</p>
                    </div>
                    <div class="assessment">
                        <p><strong>Penilaian Gizi:</strong> ${data.drink.assessment || 'Tidak ada penilaian.'}</p>
                    </div>
                </div>
            `;
        }

        if (!data.food && !data.drink && !data.food_error && !data.drink_error) {
            html = `<p class="placeholder-message">Tidak ada hasil yang tersedia. Pastikan Anda memasukkan nama makanan atau minuman.</p>`;
        } else if (data.error) { // Tangani error dari server (misal: usia tidak valid)
             html = `<div class="error-message">${data.error}</div>`;
        }

        resultsContent.innerHTML = html;
        hideLoading();
    }

    // --- Validasi Input Frontend (Fitur Baru) ---
    function validateInputs(food, drink, age) {
        if (!food && !drink) {
            alert('Mohon masukkan nama makanan atau minuman untuk dianalisis.');
            return false;
        }
        if (!age || isNaN(age) || parseInt(age) <= 0) {
            alert('Mohon masukkan usia yang valid (angka positif).');
            return false;
        }
        return true;
    }

    // --- Event Listener untuk Tombol Analisis ---
    checkGiziBtn.addEventListener('click', async () => {
        const foodName = foodNameInput.value.trim();
        const drinkName = drinkNameInput.value.trim();
        const userAge = parseInt(userAgeInput.value.trim());

        if (!validateInputs(foodName, drinkName, userAge)) {
            return; // Hentikan proses jika validasi gagal
        }

        showLoading(); // Tampilkan spinner

        try {
            const response = await fetch('http://127.0.0.1:5000/check_gizi', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ food: foodName, drink: drinkName, age: userAge })
            });

            const data = await response.json();
            displayResults(data);

        } catch (error) {
            console.error('Error during fetch:', error);
            resultsContent.innerHTML = `<div class="error-message">Terjadi kesalahan koneksi. Mohon coba lagi.</div>`;
            hideLoading();
        }
    });
});