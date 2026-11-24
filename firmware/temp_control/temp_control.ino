/*
五层爬柜温控系统 - 主控代码（上拉电阻接法 + 旋转编码器 + OLED）

功能概述：
  通过 5 路 NTC 热敏电阻采集爬柜温度，经 ADC 多次采样、滑动平均滤波后，
  与设定温度比较，采用带回差的开关控制驱动 SSR 加热。
  旋转编码器可在线调节「设定温度」与「回差」，OLED 实时显示各层温度与加热状态，
  无操作时自动息屏，任意按键或旋转即唤醒。

【接线方式：上拉电阻】
  VCC ── 10kΩ 上拉电阻 ──┬── ADC 引脚
                          │
                         NTC
                          │
                         GND
  温度↑ → NTC阻值↓ → ADC引脚电压↓ → ADC值下降
  NTC 阻值公式：R_NTC = R_上拉 × ADC / (1023 - ADC)

引脚分配（Arduino Pro Mini 5V/16MHz）：
  NTC   ：层1 A0 / 层2 A1 / 层3 A2 / 层4 A3 / 层5 A6（A6 仅作模拟输入）
  SSR   ：层1 D5 / 层2 D6 / 层3 D7 / 层4 D8 / 层5 D9（高电平导通）
  编码器：A 相 D2 / B 相 D3 / 按键 D4（按键另一端接 GND，使用内部上拉）
  OLED  ：I2C，SDA = A4 / SCL = A5，地址 0x3C

依赖库：U8g2（Arduino 库管理器搜索 "U8g2" by oliver）

安全机制：
  1. ADC 多次采样取平均        —— 抑制随机干扰
  2. NTC 电阻/温度合理性校验    —— 识别断线、短路、干扰
  3. 滑动平均滤波              —— 平滑温度曲线，防误动作
  4. 首读预填缓冲              —— 防止启动瞬间缓冲区为 0 导致误加热
  5. 回差控制                  —— 防止 SSR 在目标温度附近频繁抖动
  6. 超温/低温软件保护          —— 温度越界立即强制关闭加热
  7. NAN 统一处理              —— 任何异常读数均视为不安全，直接关断
*/

#include <math.h>
#include <U8g2lib.h>

// ====================== 基础参数 ======================

#define LAYER_COUNT     5     // 温控层数
#define FILTER_SAMPLES  8     // 滑动平均滤波窗口长度（每层独立缓冲）
#define ADC_SAMPLES     5     // 每次测温的 ADC 采样次数（取平均抗干扰）

#define R_REF      10000.0    // 上拉电阻阻值（Ω），接在 VCC 与 ADC 引脚之间
#define R_NTC      10000.0    // NTC 在 25℃ 时的标称阻值（Ω）
#define T25        25.0       // NTC 标称温度（℃）
#define B_VALUE    3950.0     // NTC 的 B 值（K）
#define ADC_MAX    1023.0     // 10 位 ADC 满量程值
#define R_NTC_MIN  50.0       // NTC 电阻下限（Ω），低于视为短路/异常

#define TEMP_MAX_LIMIT  45.0  // 软件超温保护上限（℃）
#define TEMP_MIN_LIMIT  0.0   // 软件低温保护下限（℃）

#define TARGET_MIN      10.0  // 设定温度可调下限（℃）
#define TARGET_MAX      40.0  // 设定温度可调上限（℃）
#define TARGET_STEP     0.1   // 设定温度调节步进（℃）
#define HYST_MIN        0.2   // 回差可调下限（℃）
#define HYST_MAX        5.0   // 回差可调上限（℃）
#define HYST_STEP       0.1   // 回差调节步进（℃）

#define DEFAULT_TARGET  32.0  // 上电默认设定温度（℃）
#define DEFAULT_HYST    0.8   // 上电默认回差（℃）

// ====================== 引脚定义 ======================

// NTC 模拟输入：层1→A0，层2→A1，层3→A2，层4→A3，层5→A6
const uint8_t NTC_PINS[LAYER_COUNT] = {A0, A1, A2, A3, A6};

// SSR 控制：层1→D5，层2→D6，层3→D7，层4→D8，层5→D9（高电平导通）
const uint8_t SSR_PINS[LAYER_COUNT] = {5, 6, 7, 8, 9};

#define ENC_A_PIN    2   // 编码器 A 相（INT0）
#define ENC_B_PIN    3   // 编码器 B 相（INT1）
#define ENC_BTN_PIN  4   // 编码器按键（内部上拉，按下为低）

// ====================== 时间参数 ======================

#define CONTROL_INTERVAL_MS  1000UL  // 测温 + 控制周期
#define SCREEN_SLEEP_MS     30000UL  // 无操作息屏时间
#define EDIT_TIMEOUT_MS     10000UL  // 编辑模式无操作退回时间
#define LONG_PRESS_MS         800UL  // 长按判定
#define BTN_DEBOUNCE_MS        30UL  // 按键消抖
#define ENC_COUNTS_PER_STEP     4    // 编码器每档对应的正交计数

// ====================== 全局状态 ======================

static float   filterBuf[LAYER_COUNT][FILTER_SAMPLES];
static uint8_t filterIdx[LAYER_COUNT];
static bool    filterSeeded[LAYER_COUNT];

static float layerTemp[LAYER_COUNT];
static bool  layerValid[LAYER_COUNT];
static bool  ssrOn[LAYER_COUNT];

static float   targetTemp = DEFAULT_TARGET;
static float   hysteresis = DEFAULT_HYST;
static uint8_t heatCount  = 0;
static uint8_t faultCount = 0;
static uint8_t prevFaultCount = 0;

// 编码器（中断内更新）
static volatile int32_t encRaw  = 0;
static volatile uint8_t encPrev = 0;
static int32_t encLastRaw   = 0;
static int32_t encRemainder = 0;

// 按键状态
static bool     btnRawPrev = false;
static bool     btnStable  = false;
static uint32_t btnChangedAt = 0;
static uint32_t btnPressedAt = 0;
static bool     btnLongFired = false;

// 界面状态
enum UiMode : uint8_t { UI_RUN, UI_SET_TEMP, UI_SET_HYST };
static UiMode   uiMode = UI_RUN;
static bool     displayOn = true;
static bool     displayDirty = true;
static uint32_t lastActivity = 0;
static uint32_t lastEditAt = 0;
static uint32_t lastControlAt = 0;

// OLED：SSD1306 128x64，硬件 I2C，页缓冲模式（省 RAM）
U8G2_SSD1306_128X64_NONAME_1_HW_I2C oled(U8G2_R0, /* reset=*/ U8X8_PIN_NONE);

// ====================== ADC 稳定读取 ======================

/*
 * 连续采样 ADC_SAMPLES 次取平均，每次间隔 2ms 错开噪声。
 */
static int readAdcStable(uint8_t pin) {
  long sum = 0;
  for (uint8_t i = 0; i < ADC_SAMPLES; i++) {
    sum += analogRead(pin);
    delay(2);
  }
  return (int)(sum / ADC_SAMPLES);
}

// ====================== NTC 测温（上拉接法） ======================

/*
 * 读取 NTC 温度（℃）。
 *   V_adc = VCC × R_NTC / (R_上拉 + R_NTC)
 *   → R_NTC = R_上拉 × ADC / (1023 - ADC)
 * 异常（断线/短路/超范围/非有限数）返回 NAN。
 */
static float readNtcTemp(uint8_t pin) {
  int adcValue = readAdcStable(pin);

  // 上拉接法：ADC 接近 0 表示 NTC 短路或强干扰；接近 1023 表示 NTC 断路
  if (adcValue < 5 || adcValue > 1018) {
    return NAN;
  }

  float ntcResistance = R_REF * (float)adcValue / (ADC_MAX - (float)adcValue);

  if (!isfinite(ntcResistance) || ntcResistance < R_NTC_MIN) {
    return NAN;
  }

  // B 值公式：1/T = 1/T25 + ln(R/R25)/B
  float tempK = 1.0 / (1.0 / (T25 + 273.15) + log(ntcResistance / R_NTC) / B_VALUE);

  if (!isfinite(tempK) || tempK < 100.0 || tempK > 500.0) {
    return NAN;
  }

  return tempK - 273.15;
}

// ====================== 温度有效性 ======================

static bool isTempValid(float t) {
  if (isnan(t)) return false;
  if (t < TEMP_MIN_LIMIT || t > TEMP_MAX_LIMIT) return false;
  return true;
}

// ====================== 采样 + 滑动平均 ======================

/*
 * 采样单层并更新滤波值。
 * 首次得到有效读数时用它填满整个缓冲区，避免启动瞬间均值偏低导致误加热。
 * NAN 读数不写入缓冲区，直接标记该层无效。
 */
static void sampleLayer(uint8_t layer) {
  float t = readNtcTemp(NTC_PINS[layer]);

  if (isnan(t)) {
    layerTemp[layer]  = NAN;
    layerValid[layer] = false;
    return;
  }

  if (!filterSeeded[layer]) {
    for (uint8_t i = 0; i < FILTER_SAMPLES; i++) {
      filterBuf[layer][i] = t;
    }
    filterIdx[layer]  = 0;
    filterSeeded[layer] = true;
  } else {
    filterBuf[layer][filterIdx[layer]] = t;
    filterIdx[layer] = (uint8_t)((filterIdx[layer] + 1) % FILTER_SAMPLES);
  }

  float sum = 0;
  for (uint8_t i = 0; i < FILTER_SAMPLES; i++) {
    sum += filterBuf[layer][i];
  }
  float avg = sum / FILTER_SAMPLES;

  layerTemp[layer]  = avg;
  layerValid[layer] = isTempValid(avg);
}

// ====================== 单层温控 ======================

/*
 * 带回差的开关控制：异常强制关断；加热中升到 目标+回差 才停；
 * 停止中降到 目标-回差 才开。
 */
static void controlLayer(uint8_t layer) {
  bool on = ssrOn[layer];

  if (!layerValid[layer]) {
    on = false;
  } else if (on) {
    if (layerTemp[layer] > targetTemp + hysteresis) on = false;
  } else {
    if (layerTemp[layer] < targetTemp - hysteresis) on = true;
  }

  ssrOn[layer] = on;
  digitalWrite(SSR_PINS[layer], on ? HIGH : LOW);
}

// ====================== 编码器 ======================

// 正交解码真值表，索引 = (上一状态 << 2) | 当前状态
static const int8_t ENC_TABLE[16] = {
   0,  1, -1,  0,
  -1,  0,  0,  1,
   1,  0,  0, -1,
   0, -1,  1,  0
};

void encoderISR() {
  uint8_t a = (uint8_t)digitalRead(ENC_A_PIN);
  uint8_t b = (uint8_t)digitalRead(ENC_B_PIN);
  uint8_t cur = (uint8_t)((a << 1) | b);
  uint8_t idx = (uint8_t)((encPrev << 2) | cur);
  encRaw = (int32_t)(encRaw + ENC_TABLE[idx]);
  encPrev = cur;
}

/*
 * 取出自上次调用以来的档位变化（正=顺时针）。
 */
static int readEncoderSteps() {
  int32_t raw;
  noInterrupts();
  raw = encRaw;
  interrupts();

  encRemainder += raw - encLastRaw;
  encLastRaw = raw;

  int steps = (int)(encRemainder / ENC_COUNTS_PER_STEP);
  encRemainder -= (int32_t)steps * ENC_COUNTS_PER_STEP;
  return steps;
}

// ====================== 界面 ======================

static void wakeDisplay(uint32_t now) {
  lastActivity = now;
  if (!displayOn) {
    displayOn = true;
    oled.setPowerSave(0);
    displayDirty = true;
  }
}

static void onShortPress(uint32_t now) {
  wakeDisplay(now);
  lastEditAt = now;

  if (uiMode == UI_RUN) {
    uiMode = UI_SET_TEMP;
  } else if (uiMode == UI_SET_TEMP) {
    uiMode = UI_SET_HYST;
  } else {
    uiMode = UI_RUN;
  }
  displayDirty = true;
}

static void onLongPress(uint32_t now) {
  wakeDisplay(now);
  uiMode = UI_RUN;
  displayDirty = true;
}

static void onRotate(int steps, uint32_t now) {
  wakeDisplay(now);
  if (steps == 0 || uiMode == UI_RUN) return;

  if (uiMode == UI_SET_TEMP) {
    float v = targetTemp + steps * TARGET_STEP;
    if (v < TARGET_MIN) v = TARGET_MIN;
    if (v > TARGET_MAX) v = TARGET_MAX;
    targetTemp = roundf(v * 10.0f) / 10.0f;
  } else {
    float v = hysteresis + steps * HYST_STEP;
    if (v < HYST_MIN) v = HYST_MIN;
    if (v > HYST_MAX) v = HYST_MAX;
    hysteresis = roundf(v * 10.0f) / 10.0f;
  }

  lastEditAt  = now;
  displayDirty = true;
}

static void pollButton(uint32_t now) {
  bool raw = (digitalRead(ENC_BTN_PIN) == LOW);

  if (raw != btnRawPrev) {
    btnRawPrev  = raw;
    btnChangedAt = now;
  }
  if (now - btnChangedAt < BTN_DEBOUNCE_MS) return;

  if (raw != btnStable) {
    btnStable = raw;
    if (btnStable) {
      btnPressedAt = now;
      btnLongFired = false;
      wakeDisplay(now);
    } else if (!btnLongFired) {
      onShortPress(now);
    }
  }

  if (btnStable && !btnLongFired && (now - btnPressedAt) >= LONG_PRESS_MS) {
    btnLongFired = true;
    onLongPress(now);
  }
}

// ====================== 显示 ======================

/*
 * 第一行：设定温度 / 回差（方括号表示当前正在编辑的项）
 * 其余五行：各层温度与加热状态
 */
static void drawScreen() {
  char buf[24];
  char f1[8];
  char f2[8];

  oled.firstPage();
  do {
    oled.setFont(u8g2_font_6x10_tf);

    dtostrf(targetTemp, 4, 1, f1);
    dtostrf(hysteresis, 3, 1, f2);

    if (uiMode == UI_SET_TEMP) {
      snprintf(buf, sizeof(buf), "[SET %sC] HY %sC", f1, f2);
    } else if (uiMode == UI_SET_HYST) {
      snprintf(buf, sizeof(buf), "SET %sC [HY %sC]", f1, f2);
    } else {
      snprintf(buf, sizeof(buf), "SET %sC  HY %sC", f1, f2);
    }
    oled.drawStr(0, 9, buf);

    for (uint8_t i = 0; i < LAYER_COUNT; i++) {
      int y = 19 + i * 10;
      if (layerValid[i]) {
        dtostrf(layerTemp[i], 4, 1, f1);
        snprintf(buf, sizeof(buf), "%u %sC %s", (unsigned)(i + 1), f1,
                 ssrOn[i] ? "HEAT" : "----");
      } else {
        snprintf(buf, sizeof(buf), "%u   ERR  OFF", (unsigned)(i + 1));
      }
      oled.drawStr(0, y, buf);
    }
  } while (oled.nextPage());
}

// ====================== 串口日志 ======================

static void logStatus() {
  Serial.print(F("SET "));
  Serial.print(targetTemp, 1);
  Serial.print(F(" HY "));
  Serial.print(hysteresis, 1);
  Serial.print(F(" HEAT "));
  Serial.print(heatCount);

  for (uint8_t i = 0; i < LAYER_COUNT; i++) {
    Serial.print(F(" | L"));
    Serial.print((int)(i + 1));
    if (layerValid[i]) {
      Serial.print(F(" "));
      Serial.print(layerTemp[i], 1);
      Serial.print(ssrOn[i] ? F(" H") : F(" -"));
    } else {
      Serial.print(F(" ERR"));
    }
  }
  Serial.println();
}

// ====================== 控制周期 ======================

static void runControlCycle() {
  heatCount  = 0;
  faultCount = 0;

  for (uint8_t i = 0; i < LAYER_COUNT; i++) {
    sampleLayer(i);
    controlLayer(i);
    if (ssrOn[i]) heatCount++;
    if (!layerValid[i]) faultCount++;
  }

  logStatus();
}

// ====================== 初始化 ======================

void setup() {
  Serial.begin(9600);

  for (uint8_t i = 0; i < LAYER_COUNT; i++) {
    pinMode(SSR_PINS[i], OUTPUT);
    digitalWrite(SSR_PINS[i], LOW);   // 上电确保不误加热

    filterIdx[i]    = 0;
    filterSeeded[i] = false;
    layerTemp[i]    = NAN;
    layerValid[i]   = false;
    ssrOn[i]        = false;
  }

  pinMode(ENC_A_PIN, INPUT_PULLUP);
  pinMode(ENC_B_PIN, INPUT_PULLUP);
  pinMode(ENC_BTN_PIN, INPUT_PULLUP);

  encPrev = (uint8_t)((digitalRead(ENC_A_PIN) << 1) | digitalRead(ENC_B_PIN));
  attachInterrupt(digitalPinToInterrupt(ENC_A_PIN), encoderISR, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENC_B_PIN), encoderISR, CHANGE);

  oled.begin();
  oled.setPowerSave(0);

  uint32_t now = millis();
  lastActivity  = now;
  lastEditAt    = now;
  lastControlAt = now - CONTROL_INTERVAL_MS;   // 首次循环立即测温

  Serial.println(F("5-channel temp controller ready"));
}

// ====================== 主循环 ======================

void loop() {
  uint32_t now = millis();

  pollButton(now);

  int steps = readEncoderSteps();
  if (steps != 0) {
    onRotate(steps, now);
  }

  if (now - lastControlAt >= CONTROL_INTERVAL_MS) {
    lastControlAt = now;
    runControlCycle();
    displayDirty = true;

    // 出现新故障时唤醒屏幕，提醒用户
    if (faultCount > 0 && prevFaultCount == 0) {
      wakeDisplay(now);
    }
    prevFaultCount = faultCount;
  }

  // 编辑模式超时自动退回运行界面
  if (uiMode != UI_RUN && now - lastEditAt >= EDIT_TIMEOUT_MS) {
    uiMode = UI_RUN;
    displayDirty = true;
  }

  if (displayOn) {
    if (now - lastActivity >= SCREEN_SLEEP_MS) {
      displayOn = false;
      oled.setPowerSave(1);      // 息屏，控制继续运行
    } else if (displayDirty) {
      drawScreen();
      displayDirty = false;
    }
  }
}
