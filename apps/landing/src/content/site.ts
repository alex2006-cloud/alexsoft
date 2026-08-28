export const site = {
  name: "Алексей Осипов",
  shortName: "Осипов",
  role: "ИТ-архитектор ИИ и данных",
  location: "Москва",
  tagline: "Системы, которые выдерживают масштаб банка и скорость продукта",
  summary:
    "Перевожу бизнес-требования в архитектуру AI, данных и интеграций — от концепции и C4 до промышленной эксплуатации, надзора и защиты решений на C-level.",
  years: "11+",
  contacts: {
    email: "alexosipov2006@gmail.com",
    phone: "+7 926 037-11-55",
    phoneHref: "tel:+79260371155",
    telegram: "@Aleks_nxt_lvl",
    telegramHref: "https://t.me/Aleks_nxt_lvl",
    siteLabel: "osipcraft.ru",
    siteHref: "https://osipcraft.ru",
    githubHref: "https://github.com/alex2006-cloud/alexsoft",
  },
  nav: [
    { href: "/#work", label: "Работы" },
    { href: "/#expertise", label: "Экспертиза" },
    { href: "/#lab", label: "Лаборатория" },
    { href: "/#contact", label: "Контакты" },
  ],
  stats: [
    { value: "11+", label: "лет в архитектуре и системах" },
    { value: "10", label: "AI/SaaS-продуктов в одном портфеле" },
    { value: "2 300+", label: "операторов в AI-контуре" },
    { value: "250+ млн ₽", label: "эффект первого квартала" },
  ],
  clients: [
    "Альфа-Банк",
    "ВТБ",
    "Газпром",
    "Норникель",
    "Wildberries",
    "Магнит",
    "Лента",
    "СДЭК",
    "НСПК",
    "Почта Банк",
    "Дом.РФ",
    "Счётная палата РФ",
  ],
  manifesto: [
    {
      title: "Смысл",
      text: "Сначала зачем и для кого. Потом контур: сервисы, данные, интеграции, риски.",
    },
    {
      title: "Форма",
      text: "C4, ADR, NFR, API-контракты. Архитектура, которую можно защитить и собрать.",
    },
    {
      title: "Эффект",
      text: "Сроки, надёжность, деньги. Пилот, который доходит до промышленного контура.",
    },
  ],
} as const;

export const work = [
  {
    id: "kamerton",
    kicker: "КамертонТех · с 2025",
    title: "Портфель из 10 AI-продуктов",
    role: "Solution Architect / техлид",
    lead: "Целевая архитектура SaaS, RAG и маркетплейса — от концепции до спецификаций. Совмещал архитектора, руководителя проекта и техлида.",
    metrics: [
      { value: "10", label: "продуктов без архитектурных конфликтов" },
      { value: "−40%", label: "время на согласование за счёт шаблонов" },
    ],
    points: [
      "RAG: Weaviate Cloud, чанкинг, embeddings, retrieval к LLM",
      "Стандарты документации и transition roadmap MVP → B2B/B2C",
      "Ускорение прототипов через Cursor, Copilot и low-code",
    ],
    stack: "C4 · BPMN · RAG · LangChain · Weaviate · REST · Scrum",
    tone: "dark" as const,
  },
  {
    id: "alfa",
    kicker: "Альфа-Банк · 2025–2026",
    title: "ИИ для 2 300 операторов",
    role: "Архитектор AI-решений",
    lead: "Архитектура LLM-сервисов для телемаркетинга и поддержки: CRM, телефония, наблюдаемость и MLOps. Ансамбль ~30 моделей. Защита решений перед управляющим комитетом.",
    metrics: [
      { value: "250+ млн ₽", label: "эффект в первом квартале" },
      { value: "~30 LLM", label: "в рабочем ансамбле" },
      { value: "2 млрд ₽", label: "плановый эффект двух пилотов" },
      { value: "20+", label: "человек в кросс-команде" },
    ],
    points: [
      "NFR: SLI/SLO, latency, доступность и масштаб LLM-контура",
      "MLOps: логирование, версии, A/B, monitoring pipeline",
      "Требования к PostgreSQL, Redis, Kafka, Kubernetes и Grafana",
    ],
    stack:
      "LLM / GenAI · MLOps · Kafka · PostgreSQL · Redis · Kubernetes · Prometheus · Grafana",
    tone: "dark" as const,
  },
  {
    id: "vtb-accelerator",
    kicker: "Т1 · акселератор ВТБ",
    title: "Стартап, который защитили перед топами банка.",
    role: "Архитектор / РП / системный аналитик / вайбкодер",
    lead: "Участвовал в акселераторе стартапов ВТБ от компании Т1: прошёл все этапы согласования и защищал проект перед топ-менеджментом на открытом ИТ-форуме. Внутри стартапа закрывал весь контур ролей — от архитектуры и руководства проектом до системного анализа и вайбкодинга.",
    metrics: [
      { value: "Все этапы", label: "согласования акселератора пройдены" },
      { value: "Топы ВТБ", label: "защита на открытом ИТ-форуме" },
      { value: "4 роли", label: "архитектор, РП, аналитик, вайбкодер" },
    ],
    points: [
      "Сквозной путь акселератора: отбор, согласования, допуск к финальной защите",
      "Публичная защита решения перед топ-менеджментом банка",
      "Один контур ролей: архитектура, РП, системный анализ и вайбкодинг прототипа",
    ],
    stack: "C4 · BPMN · системный анализ · product · Cursor · прототип MVP",
    tone: "light" as const,
  },
  {
    id: "innotech",
    kicker: "Иннотех · 2022–2025",
    title: "Архитектура для лидеров рынка",
    role: "ИТ-архитектор / аналитик AI и Data",
    lead: "AI, данные и интеграции для ВТБ, Газпрома, Wildberries, Ленты, СДЭК, НСПК, Почта Банка, Дом.РФ и Счётной палаты РФ.",
    metrics: [
      { value: "~500 млн ₽", label: "выручка трёх спроектированных проектов" },
      { value: "15 → 5", label: "дней на пакет документации" },
      { value: "30+", label: "защит и архитектурных сессий" },
    ],
    points: [
      "HLD/LLD/ADR, DDD, AS-IS / TO-BE, GAP, ГОСТ 34",
      "Контуры данных: СУБД, DWH, ETL/ELT, BI, качество данных",
      "Полный цикл AI-продукта: CustDev → MVP → защита перед инвесторами",
    ],
    stack: "C4 · UML · BPMN · PostgreSQL · Kafka · RabbitMQ · Redis · Docker · K8s",
    tone: "light" as const,
  },
  {
    id: "erp",
    kicker: "Т1 и БДО · 2017–2022",
    title: "ERP, на котором сходится отчётность.",
    role: "Архитектор ИТ-решений / ведущий консультант SAP",
    lead: "Целевая архитектура SAP S/4HANA и SAP ERP для ВТБ, Магнита, Норникеля и Газпрома: интеграции, миграция, контроль реализации.",
    metrics: [
      { value: "7–10 → 2–3", label: "дней финансовое закрытие" },
      { value: "50 000+", label: "проводок в день в контуре BI" },
      { value: "−40%", label: "ручных процессов в учёте активов" },
    ],
    points: [
      "ВТБ: учёт активов и бюджетирование на SAP S/4HANA",
      "Магнит: единый ERP-контур на 15+ филиалов",
      "Норникель: консолидация legacy; Газпром: ETL и Power BI",
    ],
    stack: "SAP S/4HANA · SAP PI/PO · BPMN · ARIS · SQL · ETL · Power BI",
    tone: "light" as const,
  },
] as const;

export const career = [
  {
    period: "2025 — н.в.",
    company: "КамертонТех",
    role: "Архитектор ИТ-решений / Solution Architect / техлид",
  },
  {
    period: "2025 — 2026",
    company: "Альфа-Банк",
    role: "Архитектор AI-решений",
  },
  {
    period: "2022 — 2025",
    company: "Иннотех",
    role: "ИТ-архитектор / аналитик AI и Data-решений",
  },
  {
    period: "2020 — 2022",
    company: "Т1",
    role: "Архитектор ИТ-решений / ведущий консультант SAP",
  },
  {
    period: "2017 — 2020",
    company: "БДО",
    role: "Архитектор ERP-решений / ведущий консультант SAP",
  },
  {
    period: "2016 — 2017",
    company: "КрасЭко",
    role: "Инженер ПТО: анализ ФХД, SQL, автоматизация в 1С",
  },
  {
    period: "2015 — 2016",
    company: "Победа",
    role: "Инженер-консультант: финмодели, сервисная документация, 1С",
  },
] as const;

export const expertise = [
  {
    title: "Искусственный интеллект",
    items: [
      "Архитектура LLM и GenAI-сервисов",
      "RAG: чанкинг, embeddings, retrieval",
      "MLOps, A/B, качество ответов",
      "Prompt engineering, ReAct, guardrails",
      "LangChain, Weaviate, ансамбли моделей",
    ],
  },
  {
    title: "Данные",
    items: [
      "PostgreSQL, Redis, MongoDB",
      "DWH / КХД, ETL/ELT, витрины",
      "Kafka, RabbitMQ, Tarantool",
      "Качество данных и модели данных",
      "BI: Metabase, Power BI, Grafana",
    ],
  },
  {
    title: "Интеграции и платформа",
    items: [
      "REST, OpenAPI, SOAP, XML/XSD",
      "Микросервисы и API-контракты",
      "Docker, Kubernetes",
      "SAP PI/PO, enterprise-шины",
      "Prometheus, Grafana, Kibana",
    ],
  },
  {
    title: "Архитектурное управление",
    items: [
      "C4, UML, ArchiMate, BPMN, DDD",
      "ADR, HLD/LLD, AS-IS / TO-BE",
      "NFR: SLO, latency, масштаб",
      "Agile/Scrum, бэклог, ревью",
      "Защита решений перед C-level",
    ],
  },
] as const;

export const lab = {
  title: "Личная лаборатория",
  name: "alexsoft",
  subtitle: "Personal Ecosystem Lab",
  lead: "Площадка, где архитектура становится работающими сервисами: витрина, продукты, данные и AI-шлюз — в одном контуре.",
  products: [
    {
      name: "Игры",
      blurb: "Мини-продукты, чтобы быстро проверить UX, контур данных и выкладку.",
      status: "Скоро",
    },
    {
      name: "RAG",
      blurb: "Поиск и ответы по собственной базе знаний. Живое демо retrieval-контура.",
      status: "Скоро",
    },
    {
      name: "AI Gateway",
      blurb: "Единый шлюз агентов: посты, проверки, ответы в каналы — без второго стека.",
      status: "Скоро",
    },
  ],
} as const;

export const credentials = {
  education:
    "Самарский государственный технический университет, 2015. Инженер-технолог. Офицер запаса, лейтенант.",
  languages: "Русский — родной. Английский — B2.",
  awards: ["Лидеры России — 2017, 2019"],
  certificates: [
    {
      title: "Интеграция бизнес-процессов",
      issuer: "SAP SE",
      year: "2022",
    },
    {
      title: "SAP S/4HANA для специалистов по финансовому учету",
      issuer: "SAP SE",
      year: "2021",
    },
  ],
  courses: [
    {
      title: "Развитие управленческих навыков",
      issuer: "Т1 Цифровая академия",
      year: "2024",
    },
    {
      title: "1С: Основы менеджмента",
      issuer: "1С",
      year: "2023",
    },
    {
      title: "Excel. Полезные навыки работы, о которых не знают профи",
      issuer: "Нетология",
      year: "2022",
    },
    {
      title: "Введение в SQL и работу с базой данных",
      issuer: "Нетология",
      year: "2022",
    },
    {
      title: "Основы программирования и баз данных",
      issuer: "МГТУ им. Н.Э. Баумана. Учебно-научный центр «Специалист»",
      year: "2020",
    },
    {
      title: "Бухгалтерский учет. Теория и практика.",
      issuer: "МГТУ им. Н.Э. Баумана. Учебно-научный центр «Специалист»",
      year: "2019",
    },
    {
      title: "Тренинг для тренеров",
      issuer: "BDO Unicon",
      year: "2018",
    },
  ],
} as const;
