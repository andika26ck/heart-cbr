# Case-Based Reasoning untuk Diagnosis Penyakit Jantung

Implementasi **Case-Based Reasoning (CBR)** dengan similaritas **HEOM berbobot** untuk
mendiagnosis penyakit jantung, beserta artikel ilmiah (format JOIV) dan presentasi.
Seluruh mesin CBR, fungsi similaritas, pembobotan fitur, dan metrik evaluasi
ditulis **dari nol dengan Python murni** (tanpa scikit-learn) agar setiap langkah
perhitungan dapat ditelusuri dan direplikasi.

Tugas: **SubCPMK-4 – Penalaran Komputer**, Program Studi Informatika,
Universitas Muhammadiyah Malang, Semester Genap 2025/2026.

---

## Ringkasan Hasil

| Metrik      | Validasi Silang (5-fold) | Hold-out (20%) |
| ----------- | ------------------------ | -------------- |
| Akurasi     | 75.3% (±3.6%)            | 73.3%          |
| Presisi     | 77.3%                    | 78.3%          |
| Recall      | 69.2%                    | 62.1%          |
| F1-score    | 72.8%                    | 69.2%          |

- Jumlah tetangga optimal **k = 15** (dipilih via validasi silang).
- **Studi ablasi:** pembobotan fitur menaikkan akurasi dari **72.9% → 79.0%**.
- Fitur paling berpengaruh: `ca`, `oldpeak`, `cp`.

---

## Struktur Repository

```
heart-cbr/
├─ README.md
├─ requirements.txt
├─ data/
│  └─ heart_disease.csv          # dataset (skema UCI Cleveland, 303 baris)
├─ src/
│  ├─ generate_dataset.py        # membangkitkan dataset skema UCI Cleveland
│  ├─ cbr.py                     # mesin CBR: HEOM, bobot, retrieve/reuse/revise/retain
│  ├─ run_experiment.py          # pelatihan, penyetelan k, CV, ablasi, simpan metrik+grafik
│  ├─ make_cbr_diagram.py        # membuat diagram siklus CBR
│  ├─ build_article.py           # membangun artikel .docx (format JOIV)
│  └─ build_deck.mjs             # membangun presentasi .pptx (5 slide)
├─ results/
│  ├─ metrics.json               # seluruh metrik hasil eksperimen
│  └─ fig_*.png                  # grafik (distribusi kelas, seleksi k, confusion matrix, dll)
├─ Artikel_JOIV_CBR_Heart_Disease.docx
└─ Presentasi_CBR_Heart_Disease.pptx
```

---

## Prasyarat

- Python 3.10 atau lebih baru
- (Opsional) Node.js 18+ hanya jika ingin membangun ulang presentasi `.pptx`

Pasang dependensi:

```bash
pip install -r requirements.txt
```

---

## Cara Menjalankan (Replikasi)

```bash
# 1. Siapkan dataset (menghasilkan data/heart_disease.csv)
python src/generate_dataset.py

# 2. Jalankan eksperimen lengkap
#    (penyetelan k, validasi silang 5-fold, hold-out, studi ablasi)
#    -> menyimpan results/metrics.json dan seluruh grafik results/fig_*.png
python src/run_experiment.py

# 3. (Opsional) Bangun ulang artikel ilmiah .docx
python src/build_article.py
```

Seluruh angka pada artikel dan presentasi dibaca langsung dari
`results/metrics.json`, sehingga hasil selalu konsisten dengan eksperimen.
Seed acak ditetapkan (`seed=42` untuk data, `seed=7` untuk eksperimen) agar
hasil dapat direproduksi persis.

---

## Menggunakan Data Nyata

Pipeline ini kompatibel dengan dataset **UCI Heart Disease (Cleveland)** asli.
Untuk memakainya, cukup ganti `data/heart_disease.csv` dengan berkas nyata yang
memiliki kolom sama, lalu jalankan ulang `src/run_experiment.py` (lewati langkah
1). Skema kolom:

```
age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal, target
```

`target` = 0 (sehat) atau 1 (sakit).

> Catatan: dataset yang disertakan dibangkitkan mengikuti skema, rentang nilai,
> dan hubungan antar-fitur UCI Cleveland karena keterbatasan akses unduhan pada
> lingkungan pengembangan. Struktur kode tidak berubah untuk data nyata.

---

## Detail Metodologi Singkat

1. **Retrieve** — similaritas HEOM: jarak overlap untuk atribut nominal dan
   selisih ternormalisasi (z-score) untuk atribut numerik, ditimbang bobot fitur.
2. **Reuse** — pemungutan suara k tetangga terdekat berbobot similaritas.
3. **Revise** — pemeriksaan ambang keyakinan hasil diagnosis.
4. **Retain** — penyimpanan kasus baru yang informatif ke basis kasus.

---

## Lisensi

Ditujukan untuk keperluan akademik (tugas kuliah).
