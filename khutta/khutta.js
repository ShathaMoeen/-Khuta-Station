/* =====================================================
   KHUTA JAVASCRIPT
===================================================== */

/* =========================
   إعدادات الـ API
   اتركيها فاضية "" لوضع التجربة (بدون سيرفر).
   لما يجهز الـ Backend حطي الرابط، مثال: "https://api.khuta.com"
========================= */

const API_BASE = "http://127.0.0.1:8001";

/* =========================
   NAVBAR ON SCROLL
========================= */

const header = document.getElementById("header");

function scrollHeader() {
    header.classList.toggle("scrolled", window.scrollY > 30);
}

window.addEventListener("scroll", scrollHeader);
scrollHeader();


/* =========================
   DARK / LIGHT MODE
========================= */

const themeBtn = document.getElementById("themeBtn");

if (localStorage.getItem("khuta-theme") === "light") {
    document.body.classList.add("light");
    themeBtn.textContent = "☀";
}

themeBtn.addEventListener("click", function () {
    document.body.classList.toggle("light");
    const isLight = document.body.classList.contains("light");
    localStorage.setItem("khuta-theme", isLight ? "light" : "dark");
    themeBtn.textContent = isLight ? "☀" : "☾";
});


/* =========================
   LANGUAGE BUTTON
========================= */

const TRANSLATIONS = {

    ar: {
        dir: "rtl",
        navHome: "الرئيسية", navHow: "كيف يعمل؟", navJourney: "رحلتي", navMembership: "بطاقة العضوية",
        heroEyebrow: "الموجّه المكاني التفاعلي",
        h1a: "رحلتك في المعرفة", h1b: "تبدأ من هنا",
        heroText: "تجربة تفاعلية مخصصة تساعدك على التعرف على الإسلام وتعلمه وفق لغتك ومستوى معرفتك.",
        btnStart: "ابدأ رحلتك ←", btnHow: "كيف يعمل النظام؟",
        howEyebrow: "كيف يعمل", howTitle: "كيف يعمل؟",
        howText: "اختر اللغة والمسار، ثم أنشئ بطاقة العضوية. عند ربط قاعدة البيانات ستظهر البيانات على البطاقة تلقائياً.",
        journeyEyebrow: "رحلتي", journeyTitle: "رحلتي",
        language: "اللغة", level: "المستوى",
        Beginner: "مبتدئ", Intermediate: "متوسط", Advanced: "متقدم",
        createCard: "أنشئ بطاقة العضوية",
        membershipEyebrow: "بطاقة العضوية", membershipTitle: "بطاقة العضوية",
        cardEmpty: "لم يتم إنشاء بطاقة بعد.<br>اختر اللغة والمستوى من قسم «رحلتي» ثم اضغط «أنشئ بطاقة العضوية».",
        cardNote: "الـ QR يحتوي بيانات العضوية. عند ربط الـ API / Database يتحدث الـ ID والبطاقة تلقائياً.",
        footContact: "تواصل معنا", footFollow: "تابعنا",
        footAbout: "رحلة تفاعلية في المعرفة، بسيطة وواضحة للجميع.",
        rights: "جميع الحقوق محفوظة."
    },

    ur: {
        dir: "rtl",
        navHome: "ہوم", navHow: "یہ کیسے کام کرتا ہے؟", navJourney: "میرا سفر", navMembership: "رکنیت کارڈ",
        heroEyebrow: "انٹرایکٹو رہنما",
        h1a: "علم کا آپ کا سفر", h1b: "یہیں سے شروع ہوتا ہے",
        heroText: "ایک ذاتی نوعیت کا انٹرایکٹو تجربہ جو آپ کو آپ کی زبان اور علم کی سطح کے مطابق اسلام کو جاننے اور سیکھنے میں مدد دیتا ہے۔",
        btnStart: "اپنا سفر شروع کریں ←", btnHow: "نظام کیسے کام کرتا ہے؟",
        howEyebrow: "یہ کیسے کام کرتا ہے", howTitle: "یہ کیسے کام کرتا ہے؟",
        howText: "زبان اور راستہ منتخب کریں، پھر رکنیت کارڈ بنائیں۔ ڈیٹا بیس سے منسلک ہونے پر ڈیٹا خود بخود کارڈ پر ظاہر ہو جائے گا۔",
        journeyEyebrow: "میرا سفر", journeyTitle: "میرا سفر",
        language: "زبان", level: "سطح",
        Beginner: "ابتدائی", Intermediate: "درمیانی", Advanced: "اعلیٰ",
        createCard: "رکنیت کارڈ بنائیں",
        membershipEyebrow: "رکنیت کارڈ", membershipTitle: "رکنیت کارڈ",
        cardEmpty: "ابھی تک کوئی کارڈ نہیں بنایا گیا۔<br>«میرا سفر» سیکشن سے زبان اور سطح منتخب کریں، پھر «رکنیت کارڈ بنائیں» دبائیں۔",
        cardNote: "QR میں رکنیت کا ڈیٹا ہے۔ API / ڈیٹا بیس سے منسلک ہونے پر ID اور کارڈ خود بخود اپڈیٹ ہو جائیں گے۔",
        footContact: "ہم سے رابطہ کریں", footFollow: "ہمیں فالو کریں",
        footAbout: "علم کا ایک انٹرایکٹو سفر، سادہ اور سب کے لیے واضح۔",
        rights: "جملہ حقوق محفوظ ہیں۔"
    },

    en: {
        dir: "ltr",
        navHome: "Home", navHow: "How it works", navJourney: "My Journey", navMembership: "Membership Card",
        heroEyebrow: "The Interactive Guide",
        h1a: "Your journey in knowledge", h1b: "starts here",
        heroText: "A personalized interactive experience that helps you discover and learn about Islam in your language and at your level.",
        btnStart: "Start your journey →", btnHow: "How does it work?",
        howEyebrow: "HOW IT WORKS", howTitle: "How it works",
        howText: "Choose your language and path, then create your membership card. Once the database is connected, your data will appear on the card automatically.",
        journeyEyebrow: "MY JOURNEY", journeyTitle: "My Journey",
        language: "Language", level: "Level",
        Beginner: "Beginner", Intermediate: "Intermediate", Advanced: "Advanced",
        createCard: "Create membership card",
        membershipEyebrow: "MEMBERSHIP CARD", membershipTitle: "Membership Card",
        cardEmpty: "No card has been created yet.<br>Choose a language and level in “My Journey”, then press “Create membership card”.",
        cardNote: "The QR contains your membership data. Once the API / Database is connected, the ID and card update automatically.",
        footContact: "Contact us", footFollow: "Follow us",
        footAbout: "An interactive journey in knowledge, simple and clear for everyone.",
        rights: "All rights reserved."
    },

    fr: {
        dir: "ltr",
        navHome: "Accueil", navHow: "Comment ça marche", navJourney: "Mon parcours", navMembership: "Carte de membre",
        heroEyebrow: "Le guide interactif",
        h1a: "Votre voyage dans le savoir", h1b: "commence ici",
        heroText: "Une expérience interactive personnalisée qui vous aide à découvrir et à apprendre l'islam selon votre langue et votre niveau.",
        btnStart: "Commencez votre parcours →", btnHow: "Comment ça marche ?",
        howEyebrow: "COMMENT ÇA MARCHE", howTitle: "Comment ça marche",
        howText: "Choisissez votre langue et votre parcours, puis créez votre carte de membre. Une fois la base de données connectée, vos données apparaîtront automatiquement sur la carte.",
        journeyEyebrow: "MON PARCOURS", journeyTitle: "Mon parcours",
        language: "Langue", level: "Niveau",
        Beginner: "Débutant", Intermediate: "Intermédiaire", Advanced: "Avancé",
        createCard: "Créer la carte de membre",
        membershipEyebrow: "CARTE DE MEMBRE", membershipTitle: "Carte de membre",
        cardEmpty: "Aucune carte n'a encore été créée.<br>Choisissez une langue et un niveau dans « Mon parcours », puis appuyez sur « Créer la carte de membre ».",
        cardNote: "Le QR contient les données de votre adhésion. Une fois l'API / la base de données connectée, l'ID et la carte se mettent à jour automatiquement.",
        footContact: "Contactez-nous", footFollow: "Suivez-nous",
        footAbout: "Un voyage interactif dans le savoir, simple et clair pour tous.",
        rights: "Tous droits réservés."
    }
};

/* أسماء اللغات تظهر دائماً بلغتها الأصلية */
const LANG_NAMES = { Arabic: "العربية", Urdu: "اردو", English: "English", French: "Français" };

let currentLang = localStorage.getItem("khuta-lang");
if (!TRANSLATIONS[currentLang]) currentLang = "ar";

let currentMember = null;

function t(key) {
    return TRANSLATIONS[currentLang][key] || key;
}

/* تطبيق اللغة على كل الصفحة */
function applyLanguage(lang) {

    currentLang = lang;
    localStorage.setItem("khuta-lang", lang);

    document.documentElement.lang = lang;
    document.documentElement.dir = TRANSLATIONS[lang].dir;

    document.querySelectorAll("[data-i18n]").forEach(function (el) {
        el.innerHTML = t(el.getAttribute("data-i18n"));
    });

    document.getElementById("langSelect").value = lang;

    /* تحديث نصوص قسم رحلتي بنفس اللغة */
    if (currentMember) renderMembership(currentMember);
}

document.getElementById("langSelect").addEventListener("change", function (e) {
    applyLanguage(e.target.value);
});

const STORAGE_KEY = "khuta-member";


/* =========================
   RENDER MEMBERSHIP CARD
   تُستدعى بعد إنشاء البطاقة أو عند تحديث البيانات من الـ API
========================= */

function renderMembership(member) {

    currentMember = member;

    /* إظهار البطاقة وإخفاء رسالة "لم يتم إنشاء بطاقة" */
    document.getElementById("cardEmpty").hidden = true;
    document.getElementById("memberCard").hidden = false;

    /* بيانات البطاقة (الـ ID يتحدث من الداتابيس) */
    document.getElementById("memberId").textContent = member.id;
    document.getElementById("memberLanguage").textContent = member.language;
    document.getElementById("memberPath").textContent = member.path;

    /* قسم رحلتي */
    document.getElementById("journeyLanguage").textContent =
        LANG_NAMES[member.language] || member.language;
    document.getElementById("journeyLevel").textContent =
        TRANSLATIONS[currentLang][member.path] || member.path;

    /* QR */
    const qrContainer = document.getElementById("qrcode");
    qrContainer.innerHTML = "";

    const qrData = JSON.stringify({
        membershipId: member.id,
        language: member.language,
        path: member.path,
        privacy: "Anonymous (Zero Personal Data)"
    });

    if (window.QRCode) {
        new QRCode(qrContainer, {
            text: qrData,
            width: 90,
            height: 90,
            colorDark: "#111111",
            colorLight: "#ffffff",
            correctLevel: QRCode.CorrectLevel.M
        });
    }
}


/* =========================
   DATABASE / API
========================= */

/* رقم تجريبي محلي (يُستخدم فقط إذا ما فيه API) */
function makeLocalId() {
    const next = (parseInt(localStorage.getItem("khuta-counter") || "0", 10) || 0) + 1;
    localStorage.setItem("khuta-counter", String(next));
    return "KHT-" + String(next).padStart(6, "0");
}

/*
   إنشاء عضوية جديدة.
   الـ API المتوقع:
   POST {API_BASE}/api/members   body: { language, path }
   يرجّع JSON: { id: "KHT-000123", language, path }
*/
async function createMember(language, path) {

    if (API_BASE) {
        try {
            const response = await fetch(API_BASE + "/api/members", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ language, path })
            });

            if (response.ok) {
                const data = await response.json();
                return {
                    id: data.id,
                    language: data.language || language,
                    path: data.path || path
                };
            }
        } catch (e) {
            /* إذا فشل الاتصال نكمل بالوضع التجريبي */
        }
    }

    return { id: makeLocalId(), language, path };
}

/*
   تحديث بيانات العضوية من الداتابيس (يحدّث الـ ID وباقي البيانات).
   GET {API_BASE}/api/members/:id
*/
async function loadMember(memberId) {

    if (!API_BASE) return null;

    try {
        const response = await fetch(API_BASE + "/api/members/" + encodeURIComponent(memberId));
        if (!response.ok) return null;

        const member = await response.json();
        localStorage.setItem(STORAGE_KEY, JSON.stringify(member));
        renderMembership(member);
        return member;

    } catch (e) {
        return null;
    }
}


/* =========================
   CREATE CARD (زر "أنشئ بطاقة العضوية")
========================= */

document.getElementById("journeyForm").addEventListener("submit", async function (e) {

    e.preventDefault();

    const btn = document.getElementById("createBtn");
    const language = document.getElementById("languageSelect").value;
    const path = document.getElementById("levelSelect").value;

    btn.disabled = true;

    const member = await createMember(language, path);

    localStorage.setItem(STORAGE_KEY, JSON.stringify(member));
    renderMembership(member);

    btn.disabled = false;

    /* ننقل الشخص لقسم بطاقة العضوية عشان تظهر له */
    document.getElementById("membership").scrollIntoView({ behavior: "smooth" });
});


/* =========================
   RESTORE SAVED CARD
   إذا سبق وأنشأ بطاقة، تظهر له مرة ثانية ويتحدث الـ ID من الداتابيس
========================= */

/* تطبيق اللغة المحفوظة (أو العربية) على الصفحة عند التحميل */
applyLanguage(currentLang);

(function restore() {
    let saved = null;

    try {
        saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
    } catch (e) {}

    if (saved && saved.id) {
        renderMembership(saved);
        loadMember(saved.id);
    }
})();


/* =========================
   COPYRIGHT YEAR
========================= */

document.getElementById("year").textContent = new Date().getFullYear();