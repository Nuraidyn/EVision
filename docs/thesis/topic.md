# Thesis topic (fixed 2026-11-19, contributions revised after the hold-out run)

Status: the title, the research question and the setting are fixed. The title was changed on
2026-11-19 to name the machine-learning forecasts explicitly and to say that the study assesses
the calibration of existing methods (it does not propose a new calibration method); the
"Kazakhstan as a case study" subtitle was dropped because the main results contain no separate
Kazakhstan analysis (a post hoc descriptive section exists in `results-addenda-v1.md`). The
contribution text was revised after the hold-out result (`results-holdout-v1.md`) and the
robustness analyses so that it claims no more than the evidence shows.

## English

**Assessing the Calibration of Prediction Intervals for Machine-Learning Inflation Forecasts in
Commodity-Dependent Economies: A Multi-Horizon Panel Benchmark of Conformal Methods**

Research question. Do prediction intervals for monthly inflation in commodity-dependent
economies keep their nominal coverage across forecast horizons (1, 3, 6, 12 months), and do
adaptive conformal methods shown to work on euro-area and US data transfer to this setting?

Contribution. (1) A calibration benchmark of split, rolling, adaptive (ACI, FACI), conformal
PID and regime-aware (DRACP) intervals on 20 economies (13 used to design the study and 7
hold-out economies that were untouched until the pre-specified run), with calibration
error, width and power-aware inference. (2) Results with their null outcomes recorded in
advance: adaptive methods are better calibrated than a calibration performed once and than
the native intervals of the forecasting model (consistent direction in both samples; the
registered threshold for the first comparison was met only at the longer warm-up), no
advantage of ACI over a rolling window and no advantage of DRACP over ACI was established,
and pooled coverage is below nominal for every method at the 12-month horizon, where delayed
feedback explains only part of the shortfall. (3) An exploratory analysis of coverage against exchange-rate stress.
(4) An open, reproducible pipeline (hashed data snapshots, tests, committed protocol) and a
platform module that serves calibrated inflation intervals.

## Русский

**Оценка калибровки интервалов прогноза инфляции ML-моделей в сырьевых экономиках:
многогоризонтный панельный бенчмарк конформных методов**

Исследовательский вопрос. Сохраняют ли интервалы прогноза месячной инфляции в сырьевых
экономиках заявленное покрытие на горизонтах 1, 3, 6 и 12 месяцев и переносятся ли на эту
среду адаптивные conformal-методы, показавшие себя на данных еврозоны и США?

Вклад. (1) Бенчмарк калибровки интервалов split, rolling, адаптивных (ACI, FACI), conformal
PID и режимно-адаптивного DRACP на 20 экономиках (13 использованы при проектировании
исследования и 7 контрольных, не тронутых до заранее зафиксированного прогона) с ошибкой
калибровки, шириной интервалов и выводами, учитывающими мощность. (2) Результаты с заранее
записанными нулевыми исходами: адаптивные методы калиброваны лучше, чем калибровка,
выполненная один раз, и лучше нативных интервалов самой модели (направление согласуется в
обеих выборках; заранее заданный порог для первого сравнения достигнут лишь при более длинном
разогреве); преимущество ACI над скользящим окном и преимущество DRACP над ACI не установлены;
на горизонте 12 месяцев покрытие всех методов ниже номинала, и запаздывание обратной связи
объясняет лишь часть недопокрытия. (3) Разведочный анализ покрытия в зависимости от
валютного стресса. (4) Открытый воспроизводимый конвейер (снимки данных с хешами, тесты,
зафиксированный протокол) и модуль платформы, выдающий калиброванные интервалы инфляции.

## Қазақша

**Шикізатқа тәуелді экономикалардағы инфляцияның машиналық оқыту болжамдары
интервалдарының калибрленуін бағалау: конформды әдістердің көпгоризонтты панельдік
салыстырмалы талдауы**

Зерттеу сұрағы. Шикізатқа тәуелді экономикалардағы айлық инфляция болжамының интервалдары
1, 3, 6 және 12 айлық горизонттарда мәлімделген қамтуды сақтай ма және еуроаймақ пен АҚШ
деректерінде жақсы көрсеткен бейімделгіш конформды әдістер бұл ортаға қолданыла ала ма?

Үлесі. (1) 20 экономикада (13-і зерттеуді жобалауда пайдаланылды, 7-і алдын ала
бекітілген есептеуге дейін қолданылмаған бақылау экономикалары) split, rolling, бейімделгіш
(ACI, FACI), conformal PID және режимді ескеретін DRACP интервалдарын калибрлеудің
салыстырмалы талдауы: калибрлеу қатесі, интервал ені және қуатты ескеретін қорытындылар.
(2) Нөлдік нәтижелері алдын ала жазылған нәтижелер: бейімделгіш әдістер бір рет жасалған
калибрлеуден және модельдің өзінің нативті интервалдарынан жақсырақ калибрленген (бағыты
екі таңдамада да сәйкес келеді; бірінші салыстыру үшін алдын ала белгіленген шекке тек ұзағырақ
бастапқы кезеңде жетілді); ACI әдісінің жылжымалы терезеден артықшылығы және DRACP әдісінің
ACI әдісінен артықшылығы дәлелденбеді; 12 айлық горизонтта барлық әдістердің қамтуы номиналдан
төмен, ал кері байланыстың кешігуі бұл кемшіліктің тек бір бөлігін түсіндіреді.
(3) Қамтудың валюталық күйзеліске тәуелділігін барлау талдауы. (4) Ашық, қайта
жаңғыртылатын құбыр (хэшті деректер снимоктары, тесттер, бекітілген хаттама) және
калибрленген инфляция интервалдарын беретін платформа модулі.

Note on the Kazakh text: the terminology ("конформды", "калибрлеу", "бенчмарк") should be
checked with the thesis supervisor or a Kazakh-speaking colleague before submission.
