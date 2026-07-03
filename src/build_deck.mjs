import {
	buildPptx,
	createDeck,
} from "/data/skills/pptx/scripts/pptx_builder_runtime.mjs"
import { applyRecipeDeckPlan } from "/data/skills/pptx/scripts/slide_recipes.mjs"

const ROOT = "/data/heart-cbr"
const RES = `${ROOT}/results`

const deck = createDeck({ width: 1280, height: 720 })

const slidePlan = [
	{
		recipeId: "cover-image-split",
		content: {
			eyebrow: "Penalaran Komputer \u00b7 SubCPMK-4",
			title: "Case-Based Reasoning",
			subtitle:
				"Diagnosis Penyakit Jantung \u00b7 HEOM Berbobot \u2014 Andika Candra K. \u00b7 Informatika UMM 2025/2026",
			image: { src: `${RES}/fig_cbr_cycle.png`, alt: "Siklus CBR", fit: "contain" },
		},
	},
	{
		recipeId: "image-left-story",
		content: {
			eyebrow: "Metodologi",
			image: { src: `${RES}/fig_cbr_cycle.png`, alt: "Siklus CBR lima tahap", fit: "contain" },
			title: "Siklus Case-Based Reasoning",
			body:
				"Empat tahap inti: Retrieve mengambil kasus mirip lewat similaritas HEOM berbobot, Reuse memungut suara k tetangga, Revise menguji keyakinan, dan Retain menyimpan kasus baru. HEOM menangani atribut numerik dan nominal sekaligus.",
			caption: "Siklus Case-Based Reasoning.",
		},
	},
	{
		recipeId: "process-steps",
		content: {
			eyebrow: "Implementasi & Model",
			title: "Alur Kerja Model CBR",
			subtitle:
				"Python murni tanpa scikit-learn \u00b7 303 kasus \u00b7 13 atribut UCI Cleveland.",
			steps: [
				{ title: "Retrieve", body: "Similaritas HEOM berbobot mengambil k=15 kasus termirip." },
				{ title: "Reuse & Revise", body: "Voting berbobot lalu uji ambang keyakinan diagnosis." },
				{ title: "Retain", body: "Simpan kasus baru yang informatif ke basis kasus." },
			],
		},
	},
	{
		recipeId: "chart-led",
		content: {
			eyebrow: "Hasil & Evaluasi",
			title: "Kinerja Model CBR",
			chart: {
				chartType: "column",
				categories: ["Akurasi", "Presisi", "Recall", "F1-score"],
				series: [
					{ name: "CV 5-fold", values: [75.3, 77.3, 69.2, 72.8], unit: "%" },
					{ name: "Hold-out", values: [73.3, 78.3, 62.1, 69.2], unit: "%" },
				],
				valueAxisTitle: "Skor (%)",
			},
			takeaway:
				"Pembobotan fitur menaikkan akurasi 72.9%\u219279.0%; CV & hold-out konsisten.",
		},
	},
	{
		recipeId: "closing-takeaways",
		content: {
			eyebrow: "Kesimpulan",
			title: "Kesimpulan",
			takeaways: [
				"CBR HEOM berbobot mendiagnosis penyakit jantung akurat dan transparan.",
				"Pembobotan fitur menaikkan akurasi dari 72.9% ke 79.0%.",
				"Keputusan dijelaskan lewat kasus mirip, cocok untuk klinis.",
				"Pengembangan lanjut: data klinis nyata dan seleksi kasus retain.",
			],
		},
	},
]

applyRecipeDeckPlan(deck, slidePlan)

await buildPptx(deck, {
	scenePath: `${ROOT}/build/deck.scene.json`,
	outputPath: `${ROOT}/Presentasi_CBR_Heart_Disease.pptx`,
	reportPath: `${ROOT}/build/deck.build-report.json`,
	previewDir: `${ROOT}/build/deck-preview`,
	layoutDir: `${ROOT}/build/deck-layout`,
})
console.log("DECK_DONE")
