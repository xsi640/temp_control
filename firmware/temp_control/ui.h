/*
 * OLED 界面绘制（固件与离线预览共用）。
 *
 * 布局（128x64）：
 *   0–21   顶部：SET 大号设定值 + 回差 + 加热路数
 *   22     分隔线
 *   23–63  五路温度 / 状态
 *
 * 坐标与字体度量按 U8g2 实测值固定，docs/oled 的截图由同一份代码渲染。
 */
#ifndef TEMP_CONTROL_UI_H
#define TEMP_CONTROL_UI_H

#include <U8g2lib.h>
#include <stdio.h>
#include <string.h>

/*
 * Arduino AVR 的 printf 默认不支持 %f，固件统一用 dtostrf 做定点转换。
 * 离线仿真（主机 g++）没有 dtostrf，这里补一个等价实现。
 */
#ifndef ARDUINO
static inline char *dtostrf(double val, signed char width, unsigned char prec, char *sout) {
  char fmt[16];
  snprintf(fmt, sizeof(fmt), "%%%d.%df", (int)width, (int)prec);
  sprintf(sout, fmt, val);
  return sout;
}
#endif

#define UI_CHANNELS 5

enum UiMode : uint8_t { UI_RUN = 0, UI_SET_TEMP = 1, UI_SET_HYST = 2 };

struct UiChannelState {
  float   temp;
  bool    valid;
  bool    on;
};

struct UiFrameState {
  uint8_t        mode;
  float          target;
  float          hyst;
  uint8_t        heatCount;
  UiChannelState ch[UI_CHANNELS];
};

/*
 * 顶部（0–21）：
 *   左侧：SET 小标签 + 大号设定值
 *   右侧：HY 一行、HEAT 一行，数值右对齐
 */
static inline void uiDrawHeader(U8G2 &g, const UiFrameState &st) {
  char setBuf[12];
  char hyBuf[16];
  char heatBuf[12];

  char tmp[12];
  dtostrf(st.target, 4, 1, setBuf);
  dtostrf(st.hyst, 3, 1, tmp);
  snprintf(hyBuf, sizeof(hyBuf), "%sC", tmp);
  snprintf(heatBuf, sizeof(heatBuf), "%u/%u", (unsigned)st.heatCount,
           (unsigned)UI_CHANNELS);

  const bool editSet = (st.mode == UI_SET_TEMP);
  const bool editHy  = (st.mode == UI_SET_HYST);

  /* 左：SET 标签 + 大号数值 */
  g.setFont(u8g2_font_5x7_tf);
  g.drawStr(2, 6, "SET");

  /* 大号数字宽度随正负号变化，单位 C 紧跟在数字后面，避免负温度重叠。 */
  g.setFont(u8g2_font_7x14B_tn);
  const int setW  = g.getStrWidth(setBuf);
  const int setCX = setW + 3;
  const int setBoxW = setCX + 7;

  if (editSet) {
    g.drawRBox(0, 7, setBoxW, 14, 2);
    g.setDrawColor(0);
  }
  g.drawStr(0, 20, setBuf);
  g.setFont(u8g2_font_5x7_tf);
  g.drawStr(setCX, 20, "C");
  if (editSet) g.setDrawColor(1);

  /* 右：HY / HEAT 两行，标签紧贴右对齐的数值 */
  g.setFont(u8g2_font_6x10_tf);
  const int hyW = g.getStrWidth(hyBuf);
  g.setFont(u8g2_font_5x7_tf);
  const int hyLabelW = g.getStrWidth("HY");
  const int hyLabelX = 127 - hyW - hyLabelW - 4;
  const int hyBoxX   = hyLabelX - 4;
  const int hyBoxW   = 128 - hyBoxX;

  if (editHy) {
    /* 只高亮 HY 这一项，不要铺满整个右上角。 */
    g.drawRBox(hyBoxX, 0, hyBoxW, 11, 2);
    g.setDrawColor(0);
  }
  g.setFont(u8g2_font_6x10_tf);
  g.drawStr(127 - hyW, 8, hyBuf);
  g.setFont(u8g2_font_5x7_tf);
  g.drawStr(hyLabelX, 8, "HY");
  if (editHy) g.setDrawColor(1);

  const int heatW = g.getStrWidth(heatBuf);
  g.drawStr(127 - heatW, 19, heatBuf);
  g.drawStr(127 - heatW - g.getStrWidth("HEAT") - 4, 19, "HEAT");
}

/* 单通道：反色通道号 + 温度 + 状态胶囊。 */
static inline void uiDrawChannel(U8G2 &g, uint8_t i, int base,
                                 const UiChannelState &ch) {
  char buf[16];
  char num[2] = {(char)('1' + i), '\0'};

  g.setFont(u8g2_font_5x7_tf);
  g.drawRBox(0, base - 6, 8, 7, 1);
  g.setDrawColor(0);
  g.drawStr(2, base, num);
  g.setDrawColor(1);

  g.setFont(u8g2_font_5x7_tf);

  if (!ch.valid) {
    g.drawStr(11, base, "ERR");
    const int offW = g.getStrWidth("OFF");
    g.drawStr(127 - offW, base, "OFF");
    return;
  }

  dtostrf(ch.temp, 4, 1, buf);
  const int tempW = g.getStrWidth(buf);
  g.drawStr(11, base, buf);
  g.drawStr(12 + tempW, base, "C");

  /* 状态文字统一右对齐，HEAT 前加一个实心指示块。 */
  const char *state = ch.on ? "HEAT" : "IDLE";
  const int stateW = g.getStrWidth(state);
  const int stateX = 127 - stateW;
  if (ch.on) g.drawBox(stateX - 6, base - 5, 3, 5);
  g.drawStr(stateX, base, state);
}

static inline void uiDrawFrame(U8G2 &g, const UiFrameState &st) {
  uiDrawHeader(g, st);
  g.drawHLine(0, 22, 128);
  for (uint8_t i = 0; i < UI_CHANNELS; i++) {
    uiDrawChannel(g, i, 30 + i * 8, st.ch[i]);
  }
}

#endif
