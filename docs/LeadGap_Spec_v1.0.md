# LeadGap Spec v1.0 — CatalogFix AI Outreach

**Версия:** 1.0
**Дата:** 2026-09-22
**Владелец:** CatalogFix AI
**Статус:** готово к внедрению в LeadGap
**Язык первой волны:** EN
**Голос:** we / CatalogFix AI

---

## 1. Назначение

LeadGap собирает лиды для cold outreach CatalogFix AI в три ICP-сегмента. Спека описывает:

- схему вывода (main + reserve),
- правила валидации и фильтрации,
- формулу scoring,
- правила генерации персонализации,
- структуру `batch_manifest.json`,
- чек-лист перед отправкой.

Принцип, который важнее всех остальных: **ничего не выдумано, ничего не угадано**. Если факт нельзя проверить по URL — он не попадает в лид. Это то же правило, что и в самом CatalogFix.

---

## 2. ICP и сегменты

| Сегмент | Код | Описание |
|---|---|---|
| Shopify / commerce agency | `shopify_commerce_agency` | Shopify, Shopify Plus, BigCommerce, headless commerce |
| PIM / MDM integrator | `pim_mdm_integrator` | Akeneo, Pimcore, Plytix, Salsify, inRiver, custom PIM |
| PL/CEE/DE SMB agency | `pl_cee_de_smb_agency` | Небольшие e-com агентства в Польше, CEE, Германии |

Приоритет ICP: №1 — агентства (повторяемая боль, платят за инструменты, считают в часах биллинга). №2 — интернет-магазины с большим числом поставщиков. №3 — поставщики/производители (тут чаще managed service, а не self-serve).

---

## 3. Фильтр включения / исключения

### 3.1. Жёсткие исключения

Компания не попадает в выборку, если основной профиль:

- `generic web design`
- `branding only`
- `SEO only`
- `one-person freelancer without e-commerce evidence`
- `dropshipping course`
- `marketing agency without catalog/product-data work`

### 3.2. Правило «2 из 5»

Компания включается только при наличии **минимум 2 сигналов из 5**:

1. Shopify / BigCommerce / headless commerce
2. Akeneo / Pimcore / Plytix / PIM / MDM
3. migration / replatforming / catalog onboarding
4. работа с большим ассортиментом или marketplace/e-commerce clients
5. явная работа с product feeds, ERP, PIM, supplier data

### 3.3. Пороги первой волны

```text
fit_score       >= 75
evidence_score  >= 70
evidence_age    <= 90 дней
email_conf      >= 0.8 (если work_email задан)
language_ok     = "en"
exclude_reason  = null
```

### 3.4. Формула priority_score

```text
priority_score = floor(0.5 * fit_score + 0.5 * evidence_score)
```

Обоснование: при близком fit выше поднимается тот, у кого сейчас горит (свежее доказательство), а не тот, у кого красивее стек.

---

## 4. Decision-maker mapping

| Размер команды | Приоритетная роль |
|---|---|
| до 15 | Founder / Co-founder / Owner |
| 15–50 | Founder **или** Head of E-commerce / Delivery / Operations |
| 50–200 | PIM Lead / Solutions Architect / Head of Commerce / Digital Commerce Director |
| PIM integrator (любой размер) | PIM Lead / Solution Architect (не CEO) |

---

## 5. Scoring rubric

### 5.1. fit_score (0–100)

| Компонент | Макс | Правило |
|---|---|---|
| Совпадение стека | 30 | Shopify/BigCommerce/headless = 30; Akeneo/Pimcore/Plytix = 30; оба = 30; смежное = 15; нет = 0 |
| Сила catalog_workflow_signal | 25 | явные product feeds / supplier data / ERP = 25; косвенные = 15; слабые = 5 |
| Partner badge | 15 | официальный партнёр = 15; упоминание = 8; нет = 0 |
| Соответствие размеру | 15 | внутри целевого диапазона = 15; на границе = 8; вне = 0 |
| Подтверждение ICP-подтипа | 15 | есть кейсы/клиенты в нише = 15; намёки = 8; нет = 0 |

### 5.2. evidence_score (0–100)

| Компонент | Макс | Правило |
|---|---|---|
| Свежесть | 40 | <30 дней = 40; 30–60 = 30; 60–90 = 20; >90 = 0 |
| Специфичность | 30 | названный клиент/кейс = 30; названная роль в найме = 25; конкретный пост = 15; общее = 5 |
| Проверяемость | 30 | первоисточник (их сайт, LinkedIn) = 30; вторичный (пресса, агрегатор) = 15 |

### 5.3. Иерархия recent_evidence

1. Вакансия с упоминанием PIM / Akeneo / catalog migration / supplier data — **сильнейший сигнал**, потому что про будущую боль.
2. Именованный кейс на сайте с датой.
3. Пост decision-maker’а в LinkedIn про каталог/PIM/поставщиков.
4. Пресс-релиз или партнёрское объявление.
5. Клиентские логотипы на сайте — **самый слабый**, только в reserve.

Правило: если выпадает только уровень 5 — лид идёт в reserve, не в первую волну.

---

## 6. Основная schema — `leadgap-lead.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://catalogfix.ai/schemas/leadgap-lead.json",
  "title": "LeadGap Lead — CatalogFix outreach",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "company_name", "website", "country", "segment", "subtype",
    "decision_maker_name", "decision_maker_role", "linkedin_url",
    "recent_evidence", "evidence_type", "evidence_url", "evidence_date",
    "personalization_hook", "relevance_reason", "catalog_workflow_signal",
    "likely_pain", "recommended_angle", "recommended_offer", "first_line",
    "fit_score", "evidence_score", "priority_score",
    "excluded_signals", "language_ok", "source_urls"
  ],
  "properties": {
    "company_name": { "type": "string", "minLength": 2, "maxLength": 120 },
    "website": { "type": "string", "format": "uri", "pattern": "^https?://" },
    "country": { "type": "string", "pattern": "^[A-Z]{2}$" },
    "city": { "type": ["string", "null"], "maxLength": 80 },
    "employee_range": {
      "type": "string",
      "enum": ["1-10", "11-15", "16-50", "51-200", "201-500", "500+"]
    },
    "segment": {
      "type": "string",
      "enum": ["shopify_commerce_agency", "pim_mdm_integrator", "pl_cee_de_smb_agency"]
    },
    "subtype": { "type": "string", "maxLength": 80 },
    "commerce_stack": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["Shopify", "Shopify Plus", "BigCommerce", "headless", "Magento", "WooCommerce", "commercetools", "other"]
      },
      "uniqueItems": true
    },
    "pim_stack": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["Akeneo", "Pimcore", "Plytix", "Salsify", "inRiver", "custom", "other"]
      },
      "uniqueItems": true
    },
    "partner_badges": {
      "type": "array",
      "items": { "type": "string", "maxLength": 80 },
      "uniqueItems": true
    },
    "decision_maker_name": { "type": "string", "minLength": 2, "maxLength": 120 },
    "decision_maker_role": { "type": "string", "minLength": 2, "maxLength": 120 },
    "linkedin_url": {
      "type": "string",
      "format": "uri",
      "pattern": "^https://([a-z]{2,3}\\.)?linkedin\\.com/"
    },
    "work_email": { "type": ["string", "null"], "format": "email" },
    "email_confidence": { "type": ["number", "null"], "minimum": 0, "maximum": 1 },
    "recent_evidence": { "type": "string", "minLength": 20, "maxLength": 500 },
    "evidence_type": {
      "type": "string",
      "enum": ["case_study", "job_posting", "linkedin_post", "press", "partner_page", "client_logo"]
    },
    "evidence_url": { "type": "string", "format": "uri" },
    "evidence_date": { "type": "string", "format": "date" },
    "personalization_hook": { "type": "string", "minLength": 30, "maxLength": 300 },
    "relevance_reason": { "type": "string", "minLength": 30, "maxLength": 400 },
    "catalog_workflow_signal": { "type": "string", "minLength": 20, "maxLength": 300 },
    "likely_pain": { "type": "string", "minLength": 20, "maxLength": 300 },
    "recommended_angle": {
      "type": "string",
      "enum": ["shopify_onboarding", "staging_before_pim", "supplier_normalization", "catalog_migration", "ongoing_supplier_intake"]
    },
    "recommended_offer": {
      "type": "string",
      "enum": ["actor_self_serve", "managed_service", "pilot_engagement"]
    },
    "first_line": { "type": "string", "minLength": 20, "maxLength": 200 },
    "fit_score": { "type": "integer", "minimum": 0, "maximum": 100 },
    "evidence_score": { "type": "integer", "minimum": 0, "maximum": 100 },
    "priority_score": { "type": "integer", "minimum": 0, "maximum": 100 },
    "excluded_signals": {
      "type": "array",
      "items": { "type": "string", "maxLength": 120 },
      "minItems": 0
    },
    "language_ok": { "type": "string", "enum": ["en", "pl", "de", "mixed"] },
    "source_urls": {
      "type": "array",
      "items": { "type": "string", "format": "uri" },
      "minItems": 1,
      "uniqueItems": true
    },
    "exclude_reason": { "type": ["string", "null"], "maxLength": 200 },
    "human_pass_notes": { "type": ["string", "null"], "maxLength": 500 }
  }
}
```

---

## 7. Reserve schema — `leadgap-reserve.json`

Лёгкая схема для кандидатов, отсеянных до прохождения порогов. Смысл: не терять кандидатов и видеть, **где именно** фильтр режет.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://catalogfix.ai/schemas/leadgap-reserve.json",
  "title": "LeadGap Reserve Lead",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "company_name", "website", "segment", "exclude_reason", "exclude_stage"
  ],
  "properties": {
    "company_name": { "type": "string", "minLength": 2, "maxLength": 120 },
    "website": { "type": "string", "format": "uri" },
    "country": { "type": ["string", "null"], "pattern": "^[A-Z]{2}$" },
    "segment": {
      "type": "string",
      "enum": ["shopify_commerce_agency", "pim_mdm_integrator", "pl_cee_de_smb_agency", "unknown"]
    },
    "exclude_stage": {
      "type": "string",
      "enum": [
        "pre_filter",
        "no_decision_maker",
        "no_recent_evidence",
        "low_fit_score",
        "low_evidence_score",
        "language_mismatch",
        "manual_exclude"
      ]
    },
    "exclude_reason": { "type": "string", "minLength": 10, "maxLength": 300 },
    "fit_score": { "type": ["integer", "null"], "minimum": 0, "maximum": 100 },
    "evidence_score": { "type": ["integer", "null"], "minimum": 0, "maximum": 100 },
    "recent_evidence": { "type": ["string", "null"], "maxLength": 500 },
    "evidence_date": { "type": ["string", "null"], "format": "date" },
    "decision_maker_name": { "type": ["string", "null"], "maxLength": 120 },
    "decision_maker_role": { "type": ["string", "null"], "maxLength": 120 },
    "source_urls": {
      "type": "array",
      "items": { "type": "string", "format": "uri" },
      "minItems": 0
    }
  }
}
```

---

## 8. Правила валидации поверх схем

Применяются LeadGap **после** генерации и **до** попадания лида в первую волну:

```text
1.  fit_score >= 75  AND  evidence_score >= 70
2.  recent_evidence не старше 90 дней от today
3.  evidence_type != "client_logo" для первой волны
4.  personalization_hook НЕ содержит паттернов:
      - "I saw that {company} works with"
      - "impressive portfolio" / "love your work"
      - "your website mentions"
5.  first_line не пересекается >60% по токенам с other first_line
    в этой же партии
6.  email_confidence >= 0.8, если work_email задан; иначе work_email = null
7.  language_ok = "en" для первой волны
8.  exclude_reason = null для допущенных к отправке
```

Правило №5 — самое пропускаемое. Если первые строки двух писем в одной волне структурно одинаковые, получатель это заметит, если сравнивает с коллегой или партнёром.

---

## 9. Правила генерации `personalization_hook`

**Запрещено:**

- Пересказ homepage или About.
- «I saw you work with X» без конкретики.
- Общая похвала («impressive portfolio», «love your work»).
- Любая фраза, которая подошла бы 100 другим компаниям без изменений.
- Событие старше 90 дней без пометки, почему оно всё ещё релевантно.

**Обязательно:** hook должен содержать то, что **нельзя узнать со страницы «О нас»** — вакансию, кейс клиента, пост, партнёрский статус.

### Примеры (плохо / хорошо)

**Плохо:**
> «I saw that you work with Shopify and help brands grow online.»

**Хорошо:**
> «Saw your Q3 case study on migrating a 12k-SKU catalog to Shopify Plus — the note about supplier data arriving in three different formats is exactly the problem we built CatalogFix for.»

**Плохо:**
> «Impressive portfolio of e-commerce clients.»

**Хорошо:**
> «Noticed you're hiring a PIM Specialist with Akeneo experience — in most agencies that role inherits the messiest part: normalizing supplier catalogs before they hit the PIM.»

**Плохо:**
> «Your site mentions you specialize in replatforming projects.»

**Хорошо:**
> «Your LinkedIn post last week about onboarding three new suppliers in a month — that's the exact moment CatalogFix saves the most time, before the data hits your PIM.»

**Тест на валидность:** если hook можно поставить в письмо другой компании из списка без изменений, кроме имени — вернуть на доработку.

---

## 10. `batch_manifest.json`

```json
{
  "run_id": "lg-2026-09-22-01",
  "date": "2026-09-22",
  "target_segments": {
    "shopify_commerce_agency": 4,
    "pim_mdm_integrator": 4,
    "pl_cee_de_smb_agency": 4
  },
  "thresholds_applied": {
    "fit_score_min": 75,
    "evidence_score_min": 70,
    "evidence_max_age_days": 90,
    "email_confidence_min": 0.8,
    "language_ok": "en",
    "priority_formula": "0.5*fit + 0.5*evidence"
  },
  "totals": {
    "candidates_raw": 0,
    "passed_pre_filter": 0,
    "passed_thresholds": 0,
    "reserve_count": 0
  },
  "segment_distribution_passed": {
    "shopify_commerce_agency": 0,
    "pim_mdm_integrator": 0,
    "pl_cee_de_smb_agency": 0
  },
  "exclusion_reasons_histogram": {
    "pre_filter": 0,
    "no_decision_maker": 0,
    "no_recent_evidence": 0,
    "low_fit_score": 0,
    "low_evidence_score": 0,
    "language_mismatch": 0,
    "manual_exclude": 0
  },
  "source_mix": {
    "linkedin": 0,
    "clutch": 0,
    "shopify_partners": 0,
    "apify_store": 0,
    "other": 0
  },
  "email_coverage": {
    "with_confident_email": 0,
    "without_email": 0
  },
  "notes": ""
}
```

Ключевые поля для калибровки:

- `exclusion_reasons_histogram` — если 70% отсева на `no_recent_evidence`, менять источники, а не ослаблять порог. Если на `pre_filter` — значит поисковые запросы ловят не тех.
- `email_coverage` — сразу видно, сколько лидов пойдёт по email, а сколько требует альтернативного канала (LinkedIn DM, форма на сайте).
- `source_mix` — какой источник даёт лучший signal-to-noise, куда смещать бюджет поиска в следующей волне.

---

## 11. Правила заполнения: чего ожидать

Честные ориентиры, чтобы не было сюрпризов после первого прогона:

| Поле | Ожидаемый fill rate |
|---|---|
| `work_email` с `email_confidence >= 0.8` | 50–70% |
| `recent_evidence` уровня 1–3 | 40–60% |
| `personalization_hook` | только для прошедших оба порога |

Остальные лиды попадают в `reserve.jsonl` — это **нормальный результат**, не «плохой прогон».

---

## 12. Human pass — чек-лист перед отправкой

Для первых 6–8 из партии в 12:

1. Открыть `evidence_url`, убедиться, что факт реален и дата свежая.
2. Проверить, что decision-maker всё ещё в компании (LinkedIn активен, не «ex-»).
3. Домен email совпадает с доменом компании.
4. Нет свежих негативных сигналов: сокращения, закрытие агентства, скандал.
5. `first_line` не совпадает с шаблоном другого лида в этой же партии.

Пятый пункт — самый пропускаемый. Если две первые строки в одной волне структурно одинаковые — вернуть на доработку.

---

## 13. План запуска

```text
1. Прогон LeadGap на 12 кандидатах:
   4 shopify_commerce_agency
   4 pim_mdm_integrator
   4 pl_cee_de_smb_agency

2. Проверить batch_manifest:
   - histogram отсева
   - email_coverage
   - source_mix

3. Human pass на 6–8 лидах.

4. Отправка (secondary домен, разбивка 3–4 в день).

5. Через 3 дня — смотрим reply rate, калибруем.

6. Следующие 10–12 лидов — только после калибровки.
```

---

## 14. Связанные артефакты

- **Privacy / public-facing:** ✅ закрыто. Формулировка для onboarding:
  > Customer catalog inputs and run outputs remain in the customer's Apify run storage. CatalogFix does not automatically receive access to customer runs. Users can explicitly share a run for support if needed.

- **Sample pack:** готовится. Три proof point:
  1. Реальный 32-страничный image-only PDF case (RapidOCR).
  2. Маленький XLSX/CSV controlled demo.
  3. Technical-datasheet refusal — сильный differentiator.

- **Outbound домен:** secondary, не основной. Прогрев 7–10 дней до первой волны.

---

## 15. Definition of done

- [ ] Схемы валидны, интегрированы в LeadGap.
- [ ] `batch_manifest.json` генерируется автоматически.
- [ ] `reserve.jsonl` пишется параллельно, отдельной schema.
- [ ] Первая волна = 12 кандидатов, отправка = 6–8.
- [ ] Reply handling (три ветки: yes / not now / in-house) заготовлен до первого ответа.
- [ ] Secondary домен прогрет.
- [ ] Sample pack собран.

---

**Конец v1.0.** Следующий шаг — прогон на 12 лидах. Если после прогона histogram покажет перекос в одну стадию отсева — возвращаемся в разделы 3, 5 и 8, калибруем, выпускаем v1.1.
