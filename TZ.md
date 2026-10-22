# TEXNIK TOPSHIRIQ (ТЗ)
**Loyiha nomi:** Jismoniy shaxslar uchun kredit skoringi (Application-skoring) ma'lumotlar vitrinasini loyihalash, target yig'ish va portfel muammolarini tahlil qilish

---

## 1. Umumiy ma'lumotlar va biznes-kontekst
- **Buyurtmachi:** Bankning chakana kreditlash departamenti (Kredit mahsuloti egasi).
- **Biznes muammo:** Kredit portfelida muddati o'tgan qarzdorlik (просрочка) o'sgan. Eskirgan skoring siyosati (`score_v1` va `approved_by_old_policy`) yomon mijozlar oqimini ushlab qololmayapti.
- **Loyiha maqsadi:** Yangi Application-skoring modelini o'qitishdan oldingi to'liq Data Science / Data Engineering bosqichini bajarish: ma'lumotlar bazasini audit qilish, maqsadli o'zgaruvchini (`target`) shakllantirish, kechikish o'sishi sabablarini aniqlash, vaqt bo'yicha sizib chiqishsiz (*Point-in-Time*) fichalar vitrinasini yig'ish hamda modelni tekshirish va iqtisodiy baholash sxemasini ishlab chiqish.

---

## 2. Dastlabki ma'lumotlar manbai
- **Ma'lumotlar bazasi:** PostgreSQL (`academy_db`), `public` sxemasi, `scoring_` prefiksli 17 ta jadval.
- **Baza yuklangan sana (snapshot date):** `2025-05-31`.
- **Muhim cheklov:** Baza shoshilinch yuklangan bo'lib, uning ichida ishchi jadvallar bilan birga eskirgan nusxalar, bekaplar, kesilgan namunalar va kelajakdagi ma'lumotlarni o'z ichiga olgan (*Data Leakage*) tayyor vitrinalar mavjud.

---

## 3. Bajarilishi shart bo'lgan funktsional talablar (Bosqichlar)

### 1-bosqich. Masalaning qo'yilishi (Постановка задачи)
Quyidagi 5 ta savolga aniq va asoslangan yozma javob berish:
1. **Bankning qaysi qarori o'zgaradi?** (Ariza bo'yicha ma'qullash/rad etish, kredit limiti, foiz stavkasi).
2. **Qanday hodisa va qaysi gorizontda bashorat qilinadi?** (`bad` hodisasi ta'rifi va kuzatuv oynasi).
3. **Qaror qaysi populyatsiyada qo'llaniladi?** (Kiruvchi arizalar: bankning amaldagi ETB mijozlari va yangi NTB mijozlar; o'qitish va qo'llash populyatsiyasi farqi).
4. **Qaror qabul qilish paytida (`decision_date`) qaysi ma'lumotlar mavjud?**
5. **Biznes natijani qaysi mezon asosida qabul qiladi?** (DS-metrikalar va biznes/iqtisodiy ko'rsatkichlar).

---

### 2-bosqich. Ma'lumotlar razvedkasi va auditi (Разведка данных)
1. Barcha 17 ta `scoring_*` jadvalini inventarizatsiya qilish: mohiyati, birlamchi kaliti, qatorlar soni va sanalar diapazoni.
2. **Arizalar tahlili:** Qancha ariza ma'qullangan (`approved` — 11 277 ta) va rad etilgan (`rejected` — 6 723 ta), rad etilganlar haqida qanday ma'lumotlar borligini tekshirish.
3. **Kuzatuv oynasi (Right Censoring):** Qaysi shartnomalarda kuzatuv oynasi `2025-05-31` sanasigacha hali yopilmaganini aniqlash.
4. **Data Leakage (kelajakdan ma'lumot sizib chiqishi) nazorati:** Qaror sanasidan (`decision_date`) keyin paydo bo'ladigan ustunlar va jadvallarni (`scoring_applications_full`, `scoring_collection_actions`, `scoring_bureau_loans`dagi joriy statuslar) aniqlash.
5. **Dublikat va axlat jadvallarni saralash:** Eskirgan va bekap jadvallarni (`scoring_clients_old`, `scoring_payments_backup`, `scoring_txn_sample`, `scoring_temp`) asosiy jadvallar bilan solishtirib, brakka chiqarish.
6. **Karta tranzaksiyalari qamrovi:** Nega karta tranzaksiyalari faqat bir qism mijozlarda (ETB — 8 000 mijoz) borligi va yangi mijozlarda (NTB — 5 437 mijoz) yo'qligini asoslash.
7. **Yakuniy artefakt:** Barcha 17 ta jadval bo'yicha *«Manba | Kalit | Paydo bo'lish vaqti | Fichaga qo'shish mumkinmi / Sababi»* yakuniy jadvalini tuzish.

---

### 3-bosqich. Target yig'ish (Сбор таргета — asosiy qism)
1. `scoring_payments` va `scoring_contracts` jadvallari asosida har bir to'lov bo'yicha kechikish kunlarini (**DPD — Days Past Due**) `2025-05-31` holatiga hisoblash.
2. **`bad` (`target = 1`) qoidasini asoslash:** Kredit berilgandan keyingi **dastlabki 6 ta rejaviy to'lov (`installment_no <= 6`, 6 oy)** ichida **DPD >= 60 kun** kechikishga chiqish.
3. **Chegara holatlarini (Edge cases) qayta ishlash:**
   - Rad etilgan arizalar (`rejected` — shartnoma yo'q);
   - Kuzatuv oynasi yopilmagan yangi shartnomalar (`2024-11` – `2025-04`);
   - To'lov grafigi hali shakllanmagan eng yangi shartnomalar (39 ta).
4. **Yakuniy artefakt:** `application_id, client_id, decision_date, target` ustunlaridan iborat `df_target` datafreymi (8 367 ta yetilgan shartnoma, Bad Rate = 17.44%) va berilish oylari (kogortalar) bo'yicha `bad` ulushi jadvali.

---

### 4-bosqich. Muammo diagnostikasi va tahlili (Анализ проблемы)
Kamida 3 ta tekshiruvni SQL/Python orqali bajarish:
1. **Kogortalar bo'yicha dinamika:** Muddati o'tgan qarzdorlik haqiqatan o'sganmi va qaysi oydan boshlangan? (`2024-06` oyidan boshlab `bad` ulushi 14.61% dan 22.91% gacha, oktyabrda 28.01% gacha sakraganini va NTB mijozlar ta'sirini ko'rsatish).
2. **Selection Bias (Tanlanma siljishi):** Ma'qullangan (`approved`) va rad etilgan (`rejected`) arizalarni qaror sanasigacha ma'lum bo'lgan belgilar bo'yicha solishtirish hamda eski siyosat (`approved_by_old_policy`) tanlanmani qanchalik siljitganini baholash.
3. **Anketa anomaliyalari:** `declared_income_uzs` (daromad) va `employment_months` (ish staji — 1 402 ta `NULL` yoki 7.79% bo'shliq) ustunlaridagi anomaliyalarni va ularning defoltga ta'sirini tekshirish.

---

### 5-bosqich. Fichalar vitrinasini yig'ish (Feature Engineering)
Faqat `decision_date` sanasigacha ma'lum bo'lgan ma'lumotlardan foydalanib fichalar yig'ish:
1. **Anketa va mijoz profili:** so'ralgan summa, muddat, e'lon qilingan daromad, ish staji, `is_emp_missing` flagi, PTI (oylik yuklama), mijoz segmenti (ETB/NTB), yoshi.
2. **Kredit byurosi (BKI):** `snapshot_date <= decision_date` sharti bilan *as-of join* orqali olingan oxirgi `bureau_score_asof`, joriy qarz, faol kreditlar soni va oxirgi 90/180 kundagi BKI so'rovlari soni (`scoring_bureau_inquiries`).
3. **Karta xatti-harakati (3–6 oy oldin):** `txn_ts < decision_date` sharti bilan 3 va 6 oylik oborotlar, tushgan oylik ish haqi (`salary_in`), rad etilgan tranzaksiyalar ulushi (`decline_rate_6m`), naqd pul yechish ulushi (`cash_out_share_6m`) va qaror sanasigacha ochilgan disputlar (`opened_date < decision_date`).
4. **Daromad verifikatsiyasi:** Anketadagi daromad karta orqali tushgan `salary_in` bilan tasdiqlanishini tekshirish va tasdiqlanmagan daromadlarda defolt yuqoriligini isbotlash.
5. **Tuzoq ustunlar (Leakage traps):** Metrikani sun'iy oshirib yuboradigan, lekin qaror paytida mavjud bo'lmagan kamida 2 ta (loyihada 5 ta) tuzoq ustunni topish va ularning target bilan soxta korrelyatsiyasini ko'rsatish.

---

### 6-bosqich. Tekshiruv sxemasi va qaror iqtisodiyoti (Схема проверки)
Modelni o'qitmasdan, uni baholash arxitekturasini yozish:
1. **Vaqt bo'yicha bo'lish (Out-of-Time split):** Tasodifiy bo'lish (`random split`) o'rniga aniq sanalar bo'yicha `Train` (`2023-06..2024-05`), `Val OOT-1` (`2024-06..2024-07`), `Test OOT-2` (`2024-08..2024-10`) va `PSI Monitoring` (`2024-11..2025-04`) davrlarini belgilash.
2. **Metrikalar tizimi:** Ranjirlash sifati uchun (ROC-AUC, Gini, PR-AUC, KS, PSI) va biznes qarori iqtisodiyoti uchun (Approval Rate, Bad Rate, NPV/Expected Profit) metrikalarni asoslash.
3. **Ikki turdagi xatoning puldagi narxi:** O'rtacha shartnoma (11.66 mln so'm, 13.55 oy, 31.03% stavka) misolida:
   - **I tur xatosi (FN — `bad` mijozni ma'qullash):** o'rtacha **~8.68 mln so'm** to'g'ridan-to'g'ri zarar (LGD ~ 68.5%);
   - **II tur xatosi (FP — `good` mijozni rad etish):** o'rtacha **~2.35 mln so'm** yo'qotilgan foiz daromadi (~1.41 mln so'm sof oqim);
   - Zararsizlik chegarasi (PD_cutoff ~ 14-21%) hisob-kitobi.

---

## 4. Qabul qilish mezonlari va topshiriladigan natijalar (Deliverables)
1. **Jupyter Notebook (`week_scoring_dataset.ipynb`):** Barcha 6 ta qadam kodi, SQL-so'rovlari, jadvallari va yozma asosnomalari bilan xatosiz ishga tushirilgan holatda.
2. **Xavfsizlik:** Baza login va parollari kod ichida ochiq yozilmasligi, `.env` fayli orqali o'qilishi va `.gitignore`ga kiritilishi shart.
3. **Hujjatlashtirish (`README.md` va `requirements.txt`):** GitHub repozitoriysida loyiha tavsifi va asosiy natijalar xulosasi.
