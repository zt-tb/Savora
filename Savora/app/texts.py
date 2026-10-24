from .ui import LINE, em

Z, SEARCH, EYE, PERSON = em("zap"), em("search"), em("eye"), em("person")
CAL, CLOCK, WARN, MEDAL = em("calendar"), em("clock"), em("warning"), em("medal")
TROPHY, HEART, THOUGHT, MAIL = em("trophy"), em("heart"), em("thought"), em("mail")
BIN, FORB, PLUS, SHIELD = em("bin"), em("forbidden"), em("plus"), em("shield")
COMET, IRAQ, KEY, ROBOT = em("comet"), em("iraq"), em("key"), em("robot")

TEXTS = {
    "ar": {
        "welcome": (f"{HEART} <b>أهلاً {{name}}</b> {IRAQ}\n{LINE}\n"
                    f"{Z} حمّل أي محتوى من تيليجرام بضغطة وحدة\n"
                    f"{EYE} منشورات · ستوريات · ألبومات · قنوات خاصة\n"
                    f"{LINE}\n{TROPHY} حسابك: <b>{{plan}}</b>\n{CAL} رصيدك: {{quota}}\n{LINE}\n"
                    f"{THOUGHT} أرسل الرابط الآن وأنا أتكفّل بالباقي{{nudge}}"),
        "quota_meter": "{meter} <b>{left}/{total}</b>",
        "quota_locked": "🔒 <b>تتجدد بعد {wait}</b>",
        "nudge_left": f"\n\n{MEDAL} <i>VIP = تحميل بلا حدود وبلا انتظار · من {{per_day}}⭐ لليوم</i>",
        "nudge_locked": f"\n\n{COMET} <b>لا تنتظر!</b> VIP يفتح لك التحميل فوراً · من {{per_day}}⭐ لليوم",
        "upgrade_btn": "⚡ تخطَّ الانتظار — VIP",
        "plan_free": "عادي",
        "plan_vip": "VIP 👑",
        "left_unlimited": "∞ غير محدود",
        "download_btn": "⬇️ ابدأ التحميل",
        "vip_status_btn": "👑 حالة الحساب",
        "vip_sub_btn": "💎 الترقية المميزة",
        "change_lang_btn": "🌍 اللغة",
        "share_earn_btn": "👑 اربح VIP",
        "contact_btn": "✉️ تواصل",
        "my_id_btn": "🆔 معرفي",
        "admin_panel_btn": "🔐 لوحة التحكم",
        "back_btn": "🔙 رجوع",
        "send_link": (f"{Z} <b>جاهز للتحميل</b>\n{LINE}\n"
                      f"{THOUGHT} أرسل رابط المنشور أو الستوري — تقدر ترسل عدة روابط بنفس الرسالة."),
        "invalid_link": f"{WARN} <b>رابط غير مدعوم</b>\nأرسل رابط منشور أو ستوري من تيليجرام فقط (<code>t.me/…</code>).",
        "select_language": f"{PERSON} <b>اختر اللغة</b>",
        "language_changed": f"{TROPHY} تم تغيير اللغة.",
        "error": f"{WARN} <b>صار خطأ غير متوقع</b>\nجرّب مرة ثانية بعد قليل.",
        "you_are_banned": f"{FORB} <b>أنت محظور</b> من استخدام هذا البوت.",
        "maintenance": (f"{SHIELD} <b>البوت بصيانة مؤقتة</b>\n{LINE}\n"
                        f"نرجع لك قريباً — شكراً لصبرك {HEART}"),
        "my_id_info": f"{KEY} <b>معرّفك</b>\n{LINE}\nالأيدي: <code>{{}}</code>\nاليوزر: @{{}}",
        "my_id_no_username": f"{KEY} <b>معرّفك</b>\n{LINE}\nالأيدي: <code>{{}}</code>\nاليوزر: بدون",
        "vip_active_status": (f"{MEDAL} <b>حساب VIP فعّال</b>\n{LINE}\n"
                              f"{CLOCK} المتبقي: <b>{{remaining}}</b>\n{Z} تحميل بلا حدود + أولوية بالطابور"),
        "vip_inactive_status": (f"{PERSON} <b>حساب عادي</b>\n{LINE}\n"
                                f"{CAL} رصيدك: {{quota}}\n{MEDAL} ارتقِ إلى VIP للتحميل بلا حدود وبلا انتظار"),
        "share_earn_vip_active": f"{MEDAL} عندك VIP مفعّل حالياً.",

        "card_queued": (f"{CLOCK} <b>طلبك بالطابور</b>\n{LINE}\n"
                        f"{COMET} ترتيبك: <b>{{pos}}</b> من <b>{{total}}</b>\n"
                        f"{EYE} الروابط: <b>{{n}}</b>\n{Z} يبدأ تلقائياً أول ما يجي دورك{{hint}}"),
        "queue_vip_hint": f"\n\n{MEDAL} <i>مشتركو VIP يتقدمون على الجميع بالطابور</i>",
        "card_fetching": f"{SEARCH} <b>جاري فحص الرابط…</b>{{step}}\n{LINE}\nنتأكد من المحتوى ونجهّزه",
        "card_downloading": (f"{Z} <b>جاري التحميل</b>{{step}}\n{LINE}\n"
                             f"{{bar}}  <b>{{pct}}%</b>\n💾 {{cur}} / {{total}}"),
        "card_downloading_nototal": f"{Z} <b>جاري التحميل</b>{{step}}\n{LINE}\n💾 {{cur}}",
        "card_processing": f"{SHIELD} <b>جاري المعالجة…</b>{{step}}\n{LINE}\nنجهّز الملف بحجم وجودة مناسبين",
        "card_uploading": f"{MAIL} <b>جاري الإرسال إليك…</b>{{step}}\n{LINE}\nلحظات وتوصلك",
        "card_done": (f"{TROPHY} <b>اكتمل التحميل</b>\n{LINE}\n"
                      f"{EYE} النوع: <b>{{kind}}</b>\n💾 الحجم: <b>{{size}}</b>\n"
                      f"{CLOCK} الوقت: <b>{{secs}}</b>\n{CAL} رصيدك: {{quota}}{{nudge}}"),
        "card_batch": (f"{TROPHY} <b>انتهت الدفعة</b>\n{LINE}\n"
                       f"✅ نجح: <b>{{ok}}</b>   ❌ فشل: <b>{{failed}}</b>\n{CAL} رصيدك: {{quota}}\n"
                       f"{LINE}{{lines}}{{nudge}}"),
        "batch_line_ok": "✅ {n}. {kind} · {size}",
        "batch_line_fail": "❌ {n}. {reason}",
        "cancel_job_btn": "❌ إلغاء الطلب",
        "job_cancelled": f"{FORB} <b>أُلغي طلبك</b> ولم يُحسب من رصيدك.",
        "job_not_cancellable": "بدأ التنفيذ — ما يمكن إلغاؤه الآن",
        "queue_full": f"{WARN} <b>الطابور ممتلئ حالياً</b>\nجرّب بعد دقائق.",
        "too_many_pending": f"{WARN} <b>عندك طلبات كثيرة بالانتظار</b>\nانتظر تنتهي ({{max}} كحد أقصى).",
        "batch_limit": f"{WARN} <b>روابط أكثر من المسموح</b>\nالحد الأقصى بحسابك: <b>{{max}}</b> روابط بالرسالة.",
        "split_part": "📦 الجزء {i}/{n} — ادمج الأجزاء بالترتيب",
        "split_part_video": "🎬 الجزء {i}/{n}",
        "kind_photo": "🖼 صورة",
        "kind_video": "🎬 فيديو",
        "kind_document": "📄 ملف",
        "kind_audio": "🎵 صوت",
        "kind_voice": "🎙 رسالة صوتية",
        "kind_animation": "🎞 GIF",
        "kind_sticker": "🏷 ملصق",
        "kind_text": "📝 نص",
        "kind_album": "🗂 ألبوم ({count})",
        "default_footer": f"{HEART} <b>@{{bot}}</b>",

        "no_video": f"{EYE} <b>لا يوجد ملف</b>\nالرسالة ما تحتوي على وسائط قابلة للتحميل.",
        "story_unavailable": (f"{CLOCK} <b>الستوري غير متاحة</b>\n"
                              f"انتهت صلاحيتها (24 ساعة) أو حُذفت أو الرابط غير صحيح."),
        "private_access": f"{SHIELD} <b>محتوى محمي</b>\nما أقدر أوصل له — خاص أو محذوف أو الحساب مو عضو بالقناة.",
        "flood_wait": f"{CLOCK} <b>ازدحام مؤقت</b>\nتيليجرام يطلب الانتظار {{}} ثانية — جرّب بعدها.",
        "file_too_large": f"{WARN} <b>الملف كبير جداً</b>\nأكبر من الحد المسموح للتحميل (2GB).",
        "quota_exhausted": (f"{CLOCK} <b>خلص رصيدك المجاني</b>\n{LINE}\n"
                            f"🔒 تتجدد تحميلاتك بعد: <b>{{wait}}</b>\n{LINE}\n"
                            f"{MEDAL} <b>مع VIP تفتحها الآن:</b>\n"
                            f"{Z} تحميل بلا حدود وبلا انتظار\n{COMET} أولوية بالطابور\n"
                            f"{PLUS} حتى {{vip_batch}} روابط بالرسالة\n{LINE}\n"
                            f"⭐ من <b>{{per_day}}</b> نجمة لليوم فقط"),
        "downloader_offline": (f"{KEY} <b>حساب التحميل غير متصل</b>\n"
                               f"جرى إبلاغ المالك — جرّب بعد قليل."),
        "login_menu": f"{KEY} <b>تسجيل دخول حساب التحميل</b>\n{LINE}\nاختر طريقة الدخول:",
        "login_new_btn": "🔑 تسجيل دخول حساب",
        "login_by_phone": "📱 برقم الهاتف",
        "login_by_qr": "🔳 برمز QR",
        "login_cancel": "❌ إلغاء",
        "login_ask_phone": f"{PERSON} اكتب رقم الهاتف بصيغة دولية (مثل <code>+9647xxxxxxxx</code>):",
        "login_ask_code": (f"{MAIL} وصلك كود بتيليجرام. اكتبه مع فواصل بين الأرقام "
                           f"(مثال: <code>1 2 3 4 5</code>) حتى ما يُلغى تلقائياً."),
        "login_ask_password": f"{KEY} الحساب عليه تحقق بخطوتين — اكتب كلمة السر:",
        "login_qr_caption": (f"{SEARCH} افتح تيليجرام على هاتفك ← الإعدادات ← الأجهزة ← ربط جهاز، وامسح هذا الرمز.\n"
                             f"{CLOCK} ينتهي خلال 30 ثانية ويتجدد تلقائياً."),
        "login_qr_expired": "🔁 انتهى الرمز، جرى تجديده.",
        "login_candidate": (f"{TROPHY} <b>نجح الدخول</b> — تأكد من الحساب قبل الاعتماد:\n{LINE}\n"
                            f"{PERSON} الاسم: {{name}}\n🔖 اليوزر: {{username}}\n{KEY} الأيدي: <code>{{id}}</code>"),
        "login_activate_btn": "✅ تفعيل هذا الحساب",
        "login_activated": f"{TROPHY} <b>تم اعتماد الحساب</b>\nالتحميل شغّال الآن بـ: {{name}}",
        "login_activate_failed": f"{WARN} تعذّر تفعيل الحساب: {{reason}}",
        "login_no_candidate": f"{WARN} ما فيه حساب بانتظار التفعيل (انتهت صلاحيته أو أُلغي).",
        "login_cancelled": f"{FORB} أُلغيت عملية الدخول.",
        "login_status_on": "🟢 حساب التحميل متصل.",
        "login_status_off": "🔴 حساب التحميل غير متصل — سجّل دخول.",
        "login_logout_btn": "🗑 تسجيل خروج الحساب",
        "login_logged_out": f"{BIN} تم تسجيل خروج حساب التحميل.",


        "spam_blocked": f"{WARN} <b>هدّي شوي!</b>\nضغطات سريعة جداً — انتظر <b>{{}}</b> ثانية وكمّل {HEART}",
        "spam_alert": "⏳ ضغطات كثيرة — انتظر {} ثانية",

        "admin_welcome_btn": "🎞 وسائط الترحيب",
        "welcome_menu": (f"{MAIL} <b>وسائط الترحيب</b>\n{LINE}\nالحالية: <b>{{current}}</b>\n{LINE}\n"
                         f"تظهر مع رسالة /start لكل مستخدم (GIF أو فيديو قصير أو صورة)."),
        "welcome_current_default": "الافتراضية",
        "welcome_current_animation": "GIF مخصّص",
        "welcome_current_video": "فيديو مخصّص",
        "welcome_current_photo": "صورة مخصّصة",
        "welcome_set_btn": "📤 رفع وسائط جديدة",
        "welcome_reset_btn": "♻️ الرجوع للافتراضية",
        "welcome_ask": f"{MAIL} أرسل الآن <b>GIF</b> أو <b>فيديو قصير</b> أو <b>صورة</b> لتظهر مع رسالة الترحيب.",
        "welcome_saved": f"{TROPHY} تم الحفظ — ستظهر مع /start.",
        "welcome_reset_done": f"{TROPHY} رجعت الوسائط للافتراضية.",

        "admin_panel_title": f"{SHIELD} <b>لوحة التحكم</b>\n{LINE}\nاختر الإجراء:",
        "admin_add_vip": "➕ إضافة VIP",
        "admin_remove_vip": "➖ إزالة VIP",
        "admin_ban": "🚫 حظر مستخدم",
        "admin_unban": "✅ إلغاء حظر",
        "admin_broadcast": "📢 بث",
        "admin_stats": "📊 إحصائيات",
        "admin_session": "🔑 جلسة التحميل",
        "admin_maint_off_btn": "🛠 تشغيل وضع الصيانة",
        "admin_maint_on_btn": "✅ إيقاف وضع الصيانة",
        "admin_caption_btn": "✏️ الكابشن والأسماء",
        "enter_user_id": f"{KEY} أدخل آيدي المستخدم:",
        "vip_added": f"{TROPHY} تفعّل VIP للمستخدم <code>{{}}</code> لمدة <b>{{}}</b>.",
        "vip_ask_duration": (f"{MEDAL} <b>مدة الـ VIP</b> للمستخدم <code>{{}}</code>\n{LINE}\n"
                             f"{CLOCK} اكتب المدة المطلوبة:\n"
                             f"<code>يوم</code> · <code>3 ايام</code> · <code>اسبوع</code> · <code>شهر</code> · "
                             f"<code>شهرين</code> · <code>12 ساعة</code>\n"
                             f"{THOUGHT} الرقم وحده = أيام (مثال: <code>10</code>)."),
        "vip_bad_duration": (f"{WARN} <b>ما فهمت المدة</b>\nاكتب مثل: <code>3 ايام</code> أو <code>شهرين</code> "
                             f"أو <code>12 ساعة</code> (الحد الأقصى 10 سنوات)."),
        "vip_gift_notice": (f"{TROPHY} <b>مبروك! تفعّل VIP لحسابك</b>\n{LINE}\n"
                            f"{CLOCK} المدة: <b>{{}}</b>\n{Z} تحميل بلا حدود وبلا انتظار {HEART}"),
        "vip_removed": f"{BIN} أُزيل VIP عن المستخدم <code>{{}}</code>.",
        "user_banned": f"{FORB} انحظر المستخدم <code>{{}}</code>.",
        "user_unbanned": f"{SHIELD} انفك حظر المستخدم <code>{{}}</code>.",
        "user_not_found": f"{WARN} ما لقيت هذا المستخدم بقاعدة البيانات (لازم يكون تفاعل مع البوت قبل).",
        "invalid_id": f"{WARN} اكتب آيدي رقمي صحيح.",
        "broadcast_prompt": f"{MAIL} أرسل الرسالة اللي تريد بثها لكل المستخدمين:",
        "broadcast_started": f"{ROBOT} جاري البث لـ <b>{{}}</b> مستخدم…",
        "broadcast_done": f"{TROPHY} <b>انتهى البث</b>\nنجح: <b>{{}}</b>\nفشل: <b>{{}}</b>",
        "stats_card": (f"{TROPHY} <b>إحصائيات البوت</b>\n{LINE}\n"
                       f"{PERSON} المستخدمون: <b>{{users}}</b>\n{MEDAL} VIP الآن: <b>{{vip}}</b>\n"
                       f"{FORB} المحظورون: <b>{{banned}}</b>\n{LINE}\n"
                       f"{Z} تحميلات اليوم: <b>{{today}}</b> (✅ {{today_ok}} · ❌ {{today_failed}})\n"
                       f"{CAL} الإجمالي: <b>{{total}}</b>\n📈 نسبة النجاح: <b>{{rate}}%</b>\n{LINE}\n"
                       f"🏅 الأكثر تحميلاً:{{top}}\n{WARN} أكثر أسباب الفشل:{{reasons}}\n{LINE}\n"
                       f"{KEY} حساب التحميل: <b>{{account}}</b>\n"
                       f"{COMET} بالطابور: <b>{{queued}}</b> · قيد المعالجة: <b>{{running}}</b>\n"
                       f"⭐ مبيعات النجوم: <b>{{stars}}</b> ({{sales}} عملية)"),
        "stats_none": "\n  —",
        "account_ok": "متصل 🟢",
        "account_off": "غير متصل 🔴",
        "maint_now_on": f"{SHIELD} <b>وضع الصيانة مفعّل</b> — المستخدمون لا يستطيعون التحميل (أنت مستثنى).",
        "maint_now_off": f"{TROPHY} <b>وضع الصيانة متوقف</b> — التحميل يعمل للجميع.",
        "caption_menu": (f"{MAIL} <b>الكابشن والأسماء</b>\n{LINE}\n"
                         f"التذييل: {{footer}}\nالكلمات المحذوفة: {{words}}\n{LINE}\n"
                         f"التذييل يُضاف تحت كابشن كل ملف، والكلمات تُحذف من الكابشن واسم الملف."),
        "caption_footer_btn": "✏️ تغيير التذييل",
        "caption_words_btn": "✂️ تغيير الكلمات المحذوفة",
        "caption_reset_btn": "♻️ إعادة الافتراضي",
        "caption_ask_footer": (f"{MAIL} أرسل نص التذييل الجديد (نص عادي).\n"
                               f"أرسل <code>-</code> لإلغاء التذييل كلياً."),
        "caption_ask_words": (f"{MAIL} أرسل الكلمات اللي تنحذف مفصولة بفاصلة.\n"
                              f"مثال: <code>@channel, www.site.com</code>\nأرسل <code>-</code> لإلغائها."),
        "caption_saved": f"{TROPHY} تم الحفظ.",
        "caption_reset_done": f"{TROPHY} رجعت الإعدادات للافتراضي.",
        "caption_none": "بدون",
        "caption_default": "الافتراضي",

        "vip_price": (f"{MEDAL} <b>الترقية المميزة VIP</b>\n{LINE}\n"
                      f"{Z} تحميل بلا حدود وبلا انتظار\n{COMET} أولوية بالطابور\n"
                      f"{PLUS} حتى {{vip_batch}} روابط بالرسالة\n{LINE}\n"
                      f"⭐ يوم: <b>{{d1}}</b> · أسبوع: <b>{{d7}}</b> · شهر: <b>{{d30}}</b>\n"
                      f"🔥 باقة الشهر الأوفر — بس <b>{{per_day}}</b> نجمة لليوم\n"
                      f"{THOUGHT} الدفع بنجوم تيليجرام — فوري وآمن."),
        "buy_btn": "⭐ {stars} — {plan}",
        "plan_d1": "يوم",
        "plan_d7": "أسبوع",
        "plan_d30": "شهر",
        "invoice_title": "VIP — {plan}",
        "invoice_desc": "تفعيل VIP لمدة {plan}: تحميل بلا حدود وبلا انتظار وأولوية بالطابور.",
        "pay_success": (f"{TROPHY} <b>تم الدفع بنجاح</b>\n{LINE}\n"
                        f"{MEDAL} تفعّل VIP لمدة <b>{{plan}}</b>\n{CLOCK} ينتهي بعد: <b>{{remaining}}</b>\n"
                        f"{HEART} شكراً لدعمك!"),
        "pay_rejected": f"{WARN} تعذّر إتمام الطلب — جرّب لاحقاً.",
        "pay_admin_note": (f"⭐ <b>دفعة جديدة</b>\n{PERSON} <code>{{user_id}}</code> ({{name}})\n"
                           f"{MEDAL} {{plan}} · <b>{{stars}}</b> ⭐\n<code>{{charge}}</code>"),
        "pay_grant_failed": (f"{WARN} <b>دُفع مبلغ ولم يتفعّل VIP!</b>\nالمستخدم <code>{{user_id}}</code> — "
                             f"الخطة {{plan}} — المعرّف <code>{{charge}}</code>"),
        "paysupport_text": (f"{SHIELD} <b>دعم المدفوعات</b>\n{LINE}\n"
                            f"لأي مشكلة بدفعة أو استرداد تواصل مع المالك: @K0_MG\n"
                            f"أرسل معرّف العملية إن وُجد."),
        "terms_text": (f"{SHIELD} <b>الشروط</b>\n{LINE}\n"
                       f"• الدفع بنجوم تيليجرام لخدمة رقمية (VIP لمدة محددة).\n"
                       f"• يتفعّل VIP فور الدفع وينتهي بنهاية المدة.\n"
                       f"• الاسترداد بقرار المالك عبر /paysupport.\n"
                       f"• المحتوى المحمّل مسؤولية المستخدم وحقوق أصحابه."),
        "refund_usage": f"{WARN} الصيغة: <code>/refund USER_ID CHARGE_ID</code>",
        "refund_done": f"{TROPHY} تم استرداد النجوم وأُزيل VIP عن <code>{{}}</code>.",
        "refund_failed": f"{WARN} فشل الاسترداد: {{}}",

        "share_earn_prompt": (f"{HEART} <b>اربح VIP مجاناً</b>\n{LINE}\n"
                              f"شارك رابط البوت وأرسل صورة سكرين شوت كدليل، تحصل VIP ساعة."),
        "share_earn_invalid": f"{WARN} أرسل صورة فقط كدليل مشاركة.",
        "share_earn_pending": f"{CLOCK} طلبك تحت المراجعة.",
        "share_earn_already_pending": f"{CLOCK} <b>عندك طلب قيد المراجعة</b> من قبل — انتظر قرار المالك.",
        "approve_btn": "✅ موافقة",
        "reject_btn": "❌ رفض",
        "share_earn_approved": f"{TROPHY} تفعّل عندك VIP لمدة ساعة.",
        "share_earn_rejected": f"{FORB} انرفض طلب المشاركة.",

        "alert_offline": (f"{WARN} <b>حساب التحميل انقطع</b>\n{LINE}\nالسبب: {{reason}}\n"
                          f"{KEY} سجّل دخول من لوحة التحكم ← جلسة التحميل."),
        "alert_still_offline": f"{WARN} <b>تذكير:</b> حساب التحميل ما زال غير متصل ({{reason}}).",
        "alert_recovered": f"{TROPHY} <b>رجع حساب التحميل للعمل</b>",
        "alert_session_dead": (f"{WARN} <b>الجلسة انسحبت أو استُخدمت من مكانين</b>\n{LINE}\n"
                               f"سجّل دخول من جديد، وتأكد ما في نسخة ثانية تشتغل بنفس الجلسة."),
        "reason_none": "ما فيه جلسة محفوظة",
        "reason_unauthorized": "الجلسة غير صالحة (انسحبت/انتهت)",
        "reason_disconnected": "تعذّر الاتصال بتيليجرام",
        "emoji_fallback_alert": (f"{WARN} رفض تيليجرام الإيموجي المتحرك، فتحوّلت الرسائل لإيموجي عادي تلقائياً. "
                                 f"للتفعيل لاحقاً تأكد من Telegram Premium على حساب المالك."),
    },
    "en": {
        "welcome": (f"{HEART} <b>Welcome {{name}}</b> {IRAQ}\n{LINE}\n"
                    f"{Z} Download any Telegram content in one tap\n"
                    f"{EYE} Posts · Stories · Albums · Private channels\n"
                    f"{LINE}\n{TROPHY} Plan: <b>{{plan}}</b>\n{CAL} Your balance: {{quota}}\n{LINE}\n"
                    f"{THOUGHT} Send a link now and I'll handle the rest{{nudge}}"),
        "quota_meter": "{meter} <b>{left}/{total}</b>",
        "quota_locked": "🔒 <b>Renews in {wait}</b>",
        "nudge_left": f"\n\n{MEDAL} <i>VIP = unlimited downloads, no waiting · from {{per_day}}⭐ a day</i>",
        "nudge_locked": f"\n\n{COMET} <b>Don't wait!</b> VIP unlocks downloads instantly · from {{per_day}}⭐ a day",
        "upgrade_btn": "⚡ Skip the wait — VIP",
        "plan_free": "Standard",
        "plan_vip": "VIP 👑",
        "left_unlimited": "∞ Unlimited",
        "download_btn": "⬇️ Start Download",
        "vip_status_btn": "👑 Account Status",
        "vip_sub_btn": "💎 Upgrade",
        "change_lang_btn": "🌍 Language",
        "share_earn_btn": "👑 Earn VIP",
        "contact_btn": "✉️ Contact",
        "my_id_btn": "🆔 My ID",
        "admin_panel_btn": "🔐 Control Panel",
        "back_btn": "🔙 Back",
        "send_link": (f"{Z} <b>Ready to download</b>\n{LINE}\n"
                      f"{THOUGHT} Send a post or story link — you can send several links in one message."),
        "invalid_link": f"{WARN} <b>Unsupported link</b>\nSend a Telegram post or story link only (<code>t.me/…</code>).",
        "select_language": f"{PERSON} <b>Choose a language</b>",
        "language_changed": f"{TROPHY} Language updated.",
        "error": f"{WARN} <b>Something went wrong</b>\nPlease try again shortly.",
        "you_are_banned": f"{FORB} <b>You are banned</b> from using this bot.",
        "maintenance": (f"{SHIELD} <b>Temporary maintenance</b>\n{LINE}\n"
                        f"We'll be back soon — thanks for your patience {HEART}"),
        "my_id_info": f"{KEY} <b>Your identity</b>\n{LINE}\nID: <code>{{}}</code>\nUsername: @{{}}",
        "my_id_no_username": f"{KEY} <b>Your identity</b>\n{LINE}\nID: <code>{{}}</code>\nUsername: none",
        "vip_active_status": (f"{MEDAL} <b>VIP is active</b>\n{LINE}\n"
                              f"{CLOCK} Remaining: <b>{{remaining}}</b>\n{Z} Unlimited downloads + queue priority"),
        "vip_inactive_status": (f"{PERSON} <b>Standard account</b>\n{LINE}\n"
                                f"{CAL} Your balance: {{quota}}\n{MEDAL} Upgrade to VIP for unlimited downloads, no waiting"),
        "share_earn_vip_active": f"{MEDAL} You already have active VIP.",

        "card_queued": (f"{CLOCK} <b>Your request is queued</b>\n{LINE}\n"
                        f"{COMET} Position: <b>{{pos}}</b> of <b>{{total}}</b>\n"
                        f"{EYE} Links: <b>{{n}}</b>\n{Z} Starts automatically on your turn{{hint}}"),
        "queue_vip_hint": f"\n\n{MEDAL} <i>VIP members skip ahead of everyone in the queue</i>",
        "card_fetching": f"{SEARCH} <b>Checking the link…</b>{{step}}\n{LINE}\nVerifying and preparing the content",
        "card_downloading": (f"{Z} <b>Downloading</b>{{step}}\n{LINE}\n"
                             f"{{bar}}  <b>{{pct}}%</b>\n💾 {{cur}} / {{total}}"),
        "card_downloading_nototal": f"{Z} <b>Downloading</b>{{step}}\n{LINE}\n💾 {{cur}}",
        "card_processing": f"{SHIELD} <b>Processing…</b>{{step}}\n{LINE}\nPreparing the file at a suitable size and quality",
        "card_uploading": f"{MAIL} <b>Sending to you…</b>{{step}}\n{LINE}\nJust a moment",
        "card_done": (f"{TROPHY} <b>Download complete</b>\n{LINE}\n"
                      f"{EYE} Type: <b>{{kind}}</b>\n💾 Size: <b>{{size}}</b>\n"
                      f"{CLOCK} Time: <b>{{secs}}</b>\n{CAL} Your balance: {{quota}}{{nudge}}"),
        "card_batch": (f"{TROPHY} <b>Batch finished</b>\n{LINE}\n"
                       f"✅ Done: <b>{{ok}}</b>   ❌ Failed: <b>{{failed}}</b>\n{CAL} Your balance: {{quota}}\n"
                       f"{LINE}{{lines}}{{nudge}}"),
        "batch_line_ok": "✅ {n}. {kind} · {size}",
        "batch_line_fail": "❌ {n}. {reason}",
        "cancel_job_btn": "❌ Cancel request",
        "job_cancelled": f"{FORB} <b>Request cancelled</b> and not counted toward your balance.",
        "job_not_cancellable": "Already running — can't cancel now",
        "queue_full": f"{WARN} <b>The queue is full</b>\nTry again in a few minutes.",
        "too_many_pending": f"{WARN} <b>Too many pending requests</b>\nWait for them to finish ({{max}} max).",
        "batch_limit": f"{WARN} <b>Too many links</b>\nYour limit: <b>{{max}}</b> links per message.",
        "split_part": "📦 Part {i}/{n} — join the parts in order",
        "split_part_video": "🎬 Part {i}/{n}",
        "kind_photo": "🖼 Photo",
        "kind_video": "🎬 Video",
        "kind_document": "📄 File",
        "kind_audio": "🎵 Audio",
        "kind_voice": "🎙 Voice message",
        "kind_animation": "🎞 GIF",
        "kind_sticker": "🏷 Sticker",
        "kind_text": "📝 Text",
        "kind_album": "🗂 Album ({count})",
        "default_footer": f"{HEART} <b>@{{bot}}</b>",

        "no_video": f"{EYE} <b>No file</b>\nThis message has no downloadable media.",
        "story_unavailable": (f"{CLOCK} <b>Story unavailable</b>\n"
                              f"It expired (24h), was deleted, or the link is wrong."),
        "private_access": f"{SHIELD} <b>Protected content</b>\nCan't reach it — private, deleted, or the account isn't a member.",
        "flood_wait": f"{CLOCK} <b>Temporary rush</b>\nTelegram asks to wait {{}} seconds — try again after.",
        "file_too_large": f"{WARN} <b>File too large</b>\nExceeds the allowed download size (2GB).",
        "quota_exhausted": (f"{CLOCK} <b>Your free balance is used up</b>\n{LINE}\n"
                            f"🔒 Your downloads renew in: <b>{{wait}}</b>\n{LINE}\n"
                            f"{MEDAL} <b>With VIP you unlock them now:</b>\n"
                            f"{Z} Unlimited downloads, no waiting\n{COMET} Queue priority\n"
                            f"{PLUS} Up to {{vip_batch}} links per message\n{LINE}\n"
                            f"⭐ From just <b>{{per_day}}</b> stars a day"),
        "downloader_offline": (f"{KEY} <b>Downloader account offline</b>\n"
                               f"The owner has been notified — try again shortly."),
        "login_menu": f"{KEY} <b>Log in the downloader account</b>\n{LINE}\nChoose a method:",
        "login_new_btn": "🔑 Log in an account",
        "login_by_phone": "📱 Phone number",
        "login_by_qr": "🔳 QR code",
        "login_cancel": "❌ Cancel",
        "login_ask_phone": f"{PERSON} Enter the phone number in international format (e.g. <code>+9647xxxxxxxx</code>):",
        "login_ask_code": (f"{MAIL} You received a code on Telegram. Type it with spaces between digits "
                           f"(e.g. <code>1 2 3 4 5</code>)."),
        "login_ask_password": f"{KEY} This account has 2FA — enter the password:",
        "login_qr_caption": (f"{SEARCH} Open Telegram on your phone → Settings → Devices → Link Device, and scan this.\n"
                             f"{CLOCK} Expires in 30s and auto-refreshes."),
        "login_qr_expired": "🔁 Expired, refreshed.",
        "login_candidate": (f"{TROPHY} <b>Login succeeded</b> — confirm before activating:\n{LINE}\n"
                            f"{PERSON} Name: {{name}}\n🔖 Username: {{username}}\n{KEY} ID: <code>{{id}}</code>"),
        "login_activate_btn": "✅ Activate this account",
        "login_activated": f"{TROPHY} <b>Account activated</b>\nDownloads now run on: {{name}}",
        "login_activate_failed": f"{WARN} Couldn't activate: {{reason}}",
        "login_no_candidate": f"{WARN} No account pending activation (expired or cancelled).",
        "login_cancelled": f"{FORB} Login cancelled.",
        "login_status_on": "🟢 Downloader account connected.",
        "login_status_off": "🔴 Downloader account not connected — log in.",
        "login_logout_btn": "🗑 Log out account",
        "login_logged_out": f"{BIN} Downloader account logged out.",

        "admin_panel_title": f"{SHIELD} <b>Control Panel</b>\n{LINE}\nChoose an action:",
        "admin_add_vip": "➕ Add VIP",
        "admin_remove_vip": "➖ Remove VIP",
        "admin_ban": "🚫 Ban user",
        "admin_unban": "✅ Unban user",
        "admin_broadcast": "📢 Broadcast",
        "admin_stats": "📊 Stats",
        "admin_session": "🔑 Downloader session",
        "admin_maint_off_btn": "🛠 Enable maintenance mode",
        "admin_maint_on_btn": "✅ Disable maintenance mode",
        "admin_caption_btn": "✏️ Captions and names",
        "enter_user_id": f"{KEY} Enter the user ID:",
        "vip_added": f"{TROPHY} VIP activated for <code>{{}}</code> for <b>{{}}</b>.",
        "vip_ask_duration": (f"{MEDAL} <b>VIP duration</b> for <code>{{}}</code>\n{LINE}\n"
                             f"{CLOCK} Type the duration you want:\n"
                             f"<code>1 day</code> · <code>3 days</code> · <code>1 week</code> · <code>1 month</code> · "
                             f"<code>2 months</code> · <code>12 hours</code>\n"
                             f"{THOUGHT} A bare number means days (e.g. <code>10</code>)."),
        "vip_bad_duration": (f"{WARN} <b>Couldn't read the duration</b>\nTry: <code>3 days</code>, "
                             f"<code>2 months</code> or <code>12 hours</code> (max 10 years)."),
        "vip_gift_notice": (f"{TROPHY} <b>Congrats! VIP is now active on your account</b>\n{LINE}\n"
                            f"{CLOCK} Duration: <b>{{}}</b>\n{Z} Unlimited downloads, no waiting {HEART}"),
        "vip_removed": f"{BIN} VIP removed for <code>{{}}</code>.",
        "user_banned": f"{FORB} Banned <code>{{}}</code>.",
        "user_unbanned": f"{SHIELD} Unbanned <code>{{}}</code>.",
        "user_not_found": f"{WARN} User not found (must have interacted with the bot before).",
        "invalid_id": f"{WARN} Enter a valid numeric ID.",
        "broadcast_prompt": f"{MAIL} Send the message to broadcast to all users:",
        "broadcast_started": f"{ROBOT} Broadcasting to <b>{{}}</b> users…",
        "broadcast_done": f"{TROPHY} <b>Broadcast finished</b>\nOK: <b>{{}}</b>\nFailed: <b>{{}}</b>",
        "stats_card": (f"{TROPHY} <b>Bot statistics</b>\n{LINE}\n"
                       f"{PERSON} Users: <b>{{users}}</b>\n{MEDAL} Active VIP: <b>{{vip}}</b>\n"
                       f"{FORB} Banned: <b>{{banned}}</b>\n{LINE}\n"
                       f"{Z} Downloads today: <b>{{today}}</b> (✅ {{today_ok}} · ❌ {{today_failed}})\n"
                       f"{CAL} Total: <b>{{total}}</b>\n📈 Success rate: <b>{{rate}}%</b>\n{LINE}\n"
                       f"🏅 Top downloaders:{{top}}\n{WARN} Top failure reasons:{{reasons}}\n{LINE}\n"
                       f"{KEY} Downloader account: <b>{{account}}</b>\n"
                       f"{COMET} Queued: <b>{{queued}}</b> · Running: <b>{{running}}</b>\n"
                       f"⭐ Stars sales: <b>{{stars}}</b> ({{sales}} payments)"),
        "stats_none": "\n  —",
        "account_ok": "Connected 🟢",
        "account_off": "Offline 🔴",
        "maint_now_on": f"{SHIELD} <b>Maintenance mode ON</b> — users can't download (you're exempt).",
        "maint_now_off": f"{TROPHY} <b>Maintenance mode OFF</b> — downloads work for everyone.",
        "caption_menu": (f"{MAIL} <b>Captions and names</b>\n{LINE}\n"
                         f"Footer: {{footer}}\nRemoved words: {{words}}\n{LINE}\n"
                         f"The footer is appended under every file's caption; the words are stripped from captions and file names."),
        "caption_footer_btn": "✏️ Change footer",
        "caption_words_btn": "✂️ Change removed words",
        "caption_reset_btn": "♻️ Reset to default",
        "caption_ask_footer": (f"{MAIL} Send the new footer text (plain text).\n"
                               f"Send <code>-</code> to remove the footer entirely."),
        "caption_ask_words": (f"{MAIL} Send the words to strip, comma-separated.\n"
                              f"Example: <code>@channel, www.site.com</code>\nSend <code>-</code> to clear them."),
        "caption_saved": f"{TROPHY} Saved.",
        "caption_reset_done": f"{TROPHY} Settings reset to default.",
        "caption_none": "none",
        "caption_default": "default",

        "vip_price": (f"{MEDAL} <b>VIP upgrade</b>\n{LINE}\n"
                      f"{Z} Unlimited downloads, no waiting\n{COMET} Queue priority\n"
                      f"{PLUS} Up to {{vip_batch}} links per message\n{LINE}\n"
                      f"⭐ Day: <b>{{d1}}</b> · Week: <b>{{d7}}</b> · Month: <b>{{d30}}</b>\n"
                      f"🔥 Best value: the monthly plan — only <b>{{per_day}}</b> stars a day\n"
                      f"{THOUGHT} Paid with Telegram Stars — instant and secure."),
        "buy_btn": "⭐ {stars} — {plan}",
        "plan_d1": "1 day",
        "plan_d7": "1 week",
        "plan_d30": "1 month",
        "invoice_title": "VIP — {plan}",
        "invoice_desc": "Activate VIP for {plan}: unlimited downloads, no waiting, queue priority.",
        "pay_success": (f"{TROPHY} <b>Payment successful</b>\n{LINE}\n"
                        f"{MEDAL} VIP activated for <b>{{plan}}</b>\n{CLOCK} Ends in: <b>{{remaining}}</b>\n"
                        f"{HEART} Thank you for your support!"),
        "pay_rejected": f"{WARN} Couldn't complete the request — try again later.",
        "pay_admin_note": (f"⭐ <b>New payment</b>\n{PERSON} <code>{{user_id}}</code> ({{name}})\n"
                           f"{MEDAL} {{plan}} · <b>{{stars}}</b> ⭐\n<code>{{charge}}</code>"),
        "pay_grant_failed": (f"{WARN} <b>Paid but VIP wasn't activated!</b>\nUser <code>{{user_id}}</code> — "
                             f"plan {{plan}} — charge <code>{{charge}}</code>"),
        "paysupport_text": (f"{SHIELD} <b>Payment support</b>\n{LINE}\n"
                            f"For any payment problem or refund, contact the owner: @K0_MG\n"
                            f"Include the charge ID if you have it."),
        "terms_text": (f"{SHIELD} <b>Terms</b>\n{LINE}\n"
                       f"• Paid with Telegram Stars for a digital service (timed VIP).\n"
                       f"• VIP activates right after payment and ends when the period ends.\n"
                       f"• Refunds are at the owner's discretion via /paysupport.\n"
                       f"• Downloaded content is the user's responsibility and its owners' rights."),
        "refund_usage": f"{WARN} Usage: <code>/refund USER_ID CHARGE_ID</code>",
        "refund_done": f"{TROPHY} Stars refunded and VIP removed for <code>{{}}</code>.",
        "refund_failed": f"{WARN} Refund failed: {{}}",

        "share_earn_prompt": (f"{HEART} <b>Earn VIP for free</b>\n{LINE}\n"
                              f"Share the bot link and send a screenshot as proof to earn 1h VIP."),
        "share_earn_invalid": f"{WARN} Send only an image as proof.",
        "share_earn_pending": f"{CLOCK} Your request is under review.",
        "share_earn_already_pending": f"{CLOCK} <b>You already have a pending request</b> — wait for the owner's decision.",
        "approve_btn": "✅ Approve",
        "reject_btn": "❌ Reject",
        "share_earn_approved": f"{TROPHY} You got 1h VIP.",
        "share_earn_rejected": f"{FORB} Share request rejected.",

        "alert_offline": (f"{WARN} <b>Downloader account disconnected</b>\n{LINE}\nReason: {{reason}}\n"
                          f"{KEY} Log in from Control Panel → Downloader session."),
        "alert_still_offline": f"{WARN} <b>Reminder:</b> the downloader account is still offline ({{reason}}).",
        "alert_recovered": f"{TROPHY} <b>Downloader account is back online</b>",
        "alert_session_dead": (f"{WARN} <b>The session was revoked or used from two places</b>\n{LINE}\n"
                               f"Log in again and make sure no other copy runs with the same session."),
        "reason_none": "no saved session",
        "reason_unauthorized": "session invalid (revoked/expired)",
        "reason_disconnected": "couldn't reach Telegram",
        "emoji_fallback_alert": (f"{WARN} Telegram rejected animated emoji, so messages fell back to regular emoji "
                                 f"automatically. To re-enable, make sure the owner account has Telegram Premium."),

        "spam_blocked": f"{WARN} <b>Easy there!</b>\nToo many quick taps — please wait <b>{{}}</b> seconds {HEART}",
        "spam_alert": "⏳ Too many taps — wait {} s",

        "admin_welcome_btn": "🎞 Welcome media",
        "welcome_menu": (f"{MAIL} <b>Welcome media</b>\n{LINE}\nCurrent: <b>{{current}}</b>\n{LINE}\n"
                         f"Shown with the /start message to every user (GIF, short video or photo)."),
        "welcome_current_default": "Default",
        "welcome_current_animation": "Custom GIF",
        "welcome_current_video": "Custom video",
        "welcome_current_photo": "Custom photo",
        "welcome_set_btn": "📤 Upload new media",
        "welcome_reset_btn": "♻️ Back to default",
        "welcome_ask": f"{MAIL} Send a <b>GIF</b>, a <b>short video</b> or a <b>photo</b> now to show with the welcome message.",
        "welcome_saved": f"{TROPHY} Saved — it will show with /start.",
        "welcome_reset_done": f"{TROPHY} Welcome media reset to default.",

    },
}


def text(language: str, key: str, *args, **kwargs) -> str:
    from .ui import render

    t = TEXTS.get(language, TEXTS["ar"]).get(key, TEXTS["ar"].get(key, key))
    if args or kwargs:
        try:
            t = t.format(*args, **kwargs)
        except (IndexError, KeyError):
            pass
    return render(t)
