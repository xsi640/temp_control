/*
三层爬柜温控系统 - 主控代码（上拉电阻接法版，控制1-3层）

【接线方式：上拉电阻】
  VCC ── 10kΩ 上拉电阻 ──┬── ADC 引脚（A0/A1/A2）
                          │
                         NTC
                          │
                         GND

  温度↑ → NTC阻值↓ → ADC引脚电压↓ → ADC值下降
  NTC 阻值公式：R_NTC = R_上拉 × ADC / (1023 - ADC)

功能概述：
  通过 NTC 热敏电阻采集 3 层爬柜温度，经 ADC 多次采样、滑动平均滤波后，
  与目标温度比较，采用带回差的开关控制驱动 SSR 加热，实现恒温控制。

安全机制：
  1. ADC 多次采样取平均        —— 抑制随机干扰
  2. NTC 电阻/温度合理性校验    —— 识别断线、短路、干扰
  3. 滑动平均滤波              —— 平滑温度曲线，防误动作
  4. 滤波预热                  —— 防止启动瞬间缓冲区为 0 导致误加热
  5. 回差控制                  —— 防止 SSR 在目标温度附近频繁抖动
  6. 超温/低温软件保护          —— 温度越界立即强制关闭加热
  7. NAN 统一处理              —— 任何异常读数均视为不安全，直接关断
*/

#include <math.h>

// ====================== 基础参数 ======================

#define FILTER_SAMPLES 8      // 滑动平均滤波窗口长度（每层独立缓冲）
#define ADC_SAMPLES    5      // 每次测温的 ADC 采样次数（取平均抗干扰）
#define LAYER_COUNT    3      // 温控层数

#define R_REF     10000.0     // 上拉电阻阻值（Ω），接在 VCC 与 ADC 引脚之间
#define R_NTC     10000.0     // NTC 在 25℃ 时的标称阻值（Ω）
#define T25       25.0        // NTC 标称温度（℃）
#define B_VALUE   3950.0      // NTC 的 B 值（K）
#define ADC_MAX   1023.0      // 10 位 ADC 满量程值

#define TEMP_HYSTERESIS 0.8   // 回差带（℃）
#define TEMP_MAX_LIMIT  45.0  // 软件超温保护上限（℃）
#define TEMP_MIN_LIMIT  0.0   // 软件低温保护下限（℃）
#define R_NTC_MIN       50.0  // NTC 电阻下限（Ω），低于视为短路/异常

// 各层目标温度（℃）
float targetTemp[LAYER_COUNT] = {32.0, 32.0, 32.0};

// ====================== 引脚定义 ======================

// NTC 模拟输入引脚：层1→A0，层2→A1，层3→A2
const int ntcPins[LAYER_COUNT] = {A2, A1, A0};

// SSR 控制引脚：层1→D2，层2→D3，层3→D4（高电平导通）
const int ssrPins[LAYER_COUNT] = {2, 3, 4};

// ====================== 全局状态 ======================

float filterBuffer[LAYER_COUNT][FILTER_SAMPLES];   // 每层滑动平均缓冲区
int   filterIndex[LAYER_COUNT]  = {0, 0, 0};        // 环形缓冲写入索引
bool  filterReady[LAYER_COUNT]  = {false, false, false}; // 是否已获得有效读数
bool  ssrState[LAYER_COUNT]     = {false, false, false}; // SSR 锁存状态

// ====================== ADC 稳定读取 ======================

/*
 * 连续采样 ADC_SAMPLES 次取平均，每次间隔 2ms 错开噪声。
 */
int readAdcStable(int pin) {
  long sum = 0;
  for (int i = 0; i < ADC_SAMPLES; i++) {
    sum += analogRead(pin);
    delay(2);
  }
  return sum / ADC_SAMPLES;
}

// ====================== NTC 测温（上拉接法） ======================

/*
 * 读取 NTC 温度（℃）。
 * 上拉接法：ADC 读的是 NTC 两端电压，NTC 与上拉电阻分压。
 *   V_adc = VCC × R_NTC / (R_上拉 + R_NTC)
 *   → R_NTC = R_上拉 × ADC / (1023 - ADC)
 * 温度↑ → R_NTC↓ → ADC↓，此公式方向正确。
 * 异常（断线/短路/超范围/非有限数）返回 NAN。
 */
float readNtcTemp(int pin) {
  int adcValue = readAdcStable(pin);

  // 上拉接法下：ADC 接近 0 表示 NTC 短路或强干扰；接近 1023 表示 NTC 断路
  if (adcValue < 5 || adcValue > 1018) {
    return NAN;
  }

  // 上拉接法 NTC 阻值公式（与下拉接法相反）
  float ntcResistance = R_REF * (float)adcValue / (ADC_MAX - (float)adcValue);

  // 阻值合理性校验，防止 log() 输入异常
  if (!isfinite(ntcResistance) || ntcResistance < R_NTC_MIN) {
    return NAN;
  }

  // B 值公式：1/T = 1/T25 + ln(R/R25)/B
  float tempK = 1.0 / (1.0 / (T25 + 273.15) + log(ntcResistance / R_NTC) / B_VALUE);

  // 开尔文温度合理性校验（100K~500K）
  if (!isfinite(tempK) || tempK < 100.0 || tempK > 500.0) {
    return NAN;
  }

  return tempK - 273.15;
}

// ====================== 滑动平均滤波 ======================

/*
 * 获取指定层滤波后温度。NAN 读数不写入缓冲区，直接返回 NAN。
 */
float getFilteredTemp(int layer) {
  float temp = readNtcTemp(ntcPins[layer]);

  if (isnan(temp)) {
    return NAN;   // 异常不污染缓冲区
  }

  filterBuffer[layer][filterIndex[layer]] = temp;
  filterIndex[layer] = (filterIndex[layer] + 1) % FILTER_SAMPLES;
  filterReady[layer] = true;

  float sum = 0;
  for (int i = 0; i < FILTER_SAMPLES; i++) {
    sum += filterBuffer[layer][i];
  }
  return sum / FILTER_SAMPLES;
}

// ====================== 温度有效性判断 ======================

bool isValidTemp(float temp) {
  if (isnan(temp)) return false;
  if (temp < TEMP_MIN_LIMIT || temp > TEMP_MAX_LIMIT) return false;
  return true;
}

// ====================== 单层温控逻辑 ======================

/*
 * 带回差的开关控制：异常强制关断；加热中升到 目标+回差 才停；
 * 停止中降到 目标-回差 才开。
 */
void controlLayer(int layer, float temp) {

  if (!isValidTemp(temp)) {
    ssrState[layer] = false;
    digitalWrite(ssrPins[layer], LOW);
    return;
  }

  if (ssrState[layer]) {
    if (temp > targetTemp[layer] + TEMP_HYSTERESIS) {
      ssrState[layer] = false;
    }
  } else {
    if (temp < targetTemp[layer] - TEMP_HYSTERESIS) {
      ssrState[layer] = true;
    }
  }

  digitalWrite(ssrPins[layer], ssrState[layer] ? HIGH : LOW);
}

// ====================== 初始化 ======================

/*
 * 初始化串口与 SSR 引脚，并预热滤波缓冲区。
 * 若开机读数无效，用 25℃ 占位，防止 NAN 污染缓冲区。
 */
void setup() {
  Serial.begin(9600);

  for (int i = 0; i < LAYER_COUNT; i++) {
    pinMode(ssrPins[i], OUTPUT);
    digitalWrite(ssrPins[i], LOW);   // 上电确保不误加热

    float temp = readNtcTemp(ntcPins[i]);
    if (!isValidTemp(temp)) {
      temp = 25.0;
    }
    for (int j = 0; j < FILTER_SAMPLES; j++) {
      filterBuffer[i][j] = temp;
    }
    filterIndex[i] = 0;
    filterReady[i] = false;
  }

  Serial.println("三层温控（1-3层，上拉接法）启动成功");
  Serial.println("========================================");
}

// ====================== 主循环 ======================

void loop() {
  Serial.println("三层温控（1-3层）实时状态：");

  for (int i = 0; i < LAYER_COUNT; i++) {
    float temp = getFilteredTemp(i);
    controlLayer(i, temp);

    Serial.print("层");
    Serial.print(i + 1);
    Serial.print("：");

    if (isValidTemp(temp)) {
      Serial.print(temp, 1);
      Serial.print("℃ | 目标：");
      Serial.print(targetTemp[i], 1);
      Serial.print("℃ | ");
      Serial.print(ssrState[i] ? "加热中" : "已停止");
    } else {
      Serial.print("温度异常 | 加热已关闭");
    }
    Serial.println();
  }

  Serial.println("========================================");
  delay(1000);
}