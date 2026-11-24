/*
 * 离线渲染 OLED 界面：调用固件同一份 ui.h，输出 128x64 的 PBM 位图。
 *
 * 使用 U8g2 全屏缓冲模式：绘制后直接读取 U8g2 内部像素缓冲，
 * 不依赖 I2C 回调，因此得到的是与实机完全一致的字体点阵。
 *
 * 构建（由 render.py 自动完成）：
 *   g++ -std=c++11 -O2 -I../../firmware/temp_control -I<U8g2>/src  *       sim.cpp <U8g2>/src/clib/u8g2_*.c <U8g2>/src/clib/u8x8_*.c -o sim
 */
#include <stdio.h>
#include <string.h>
#include "ui.h"

static uint8_t displayCb(u8x8_t *u8x8, uint8_t msg, uint8_t arg_int, void *arg_ptr) {
  (void)u8x8;
  (void)msg;
  (void)arg_int;
  (void)arg_ptr;
  return 1;
}

static void dumpPbm(const char *name, u8g2_t *u8g2) {
  const uint8_t *buf = u8g2_GetBufferPtr(u8g2);
  const int tiles = u8g2_GetBufferTileHeight(u8g2);
  const int width = 128;

  FILE *f = fopen(name, "wb");
  if (!f) return;
  fprintf(f, "P1\n%d %d\n", width, tiles * 8);
  for (int y = 0; y < tiles * 8; y++) {
    for (int x = 0; x < width; x++) {
      int bit = (buf[(y / 8) * width + x] >> (y % 8)) & 1;
      fputc(bit ? '1' : '0', f);
      fputc(x == width - 1 ? '\n' : ' ', f);
    }
  }
  fclose(f);
  printf("wrote %s\n", name);
}

static void render(const char *name, const UiFrameState &st, bool asleep = false) {
  U8G2 g;
  u8g2_Setup_ssd1306_i2c_128x64_noname_f(g.getU8g2(), U8G2_R0, displayCb, displayCb);
  u8g2_ClearBuffer(g.getU8g2());
  if (!asleep) {
    uiDrawFrame(g, st);
  }
  dumpPbm(name, g.getU8g2());
}

static UiChannelState ch(float t, bool valid, bool on) {
  UiChannelState c;
  c.temp = t;
  c.valid = valid;
  c.on = on;
  return c;
}

int main(void) {
  UiFrameState run;
  run.mode = UI_RUN;
  run.target = 32.0f;
  run.hyst = 0.8f;
  run.heatCount = 2;
  run.ch[0] = ch(31.4f, true, true);
  run.ch[1] = ch(30.9f, true, true);
  run.ch[2] = ch(32.4f, true, false);
  run.ch[3] = ch(31.8f, true, false);
  run.ch[4] = ch(32.1f, true, false);
  render("frame-run-heat.pbm", run);

  UiFrameState idle = run;
  idle.heatCount = 0;
  idle.ch[0] = ch(32.3f, true, false);
  idle.ch[1] = ch(32.1f, true, false);
  idle.ch[2] = ch(32.4f, true, false);
  idle.ch[3] = ch(31.8f, true, false);
  idle.ch[4] = ch(32.1f, true, false);
  render("frame-run-idle.pbm", idle);

  UiFrameState setTemp = run;
  setTemp.mode = UI_SET_TEMP;
  render("frame-edit-temp.pbm", setTemp);

  UiFrameState setHyst = idle;
  setHyst.mode = UI_SET_HYST;
  render("frame-edit-hyst.pbm", setHyst);

  UiFrameState fault = run;
  fault.ch[2] = ch(0.0f, false, false);
  fault.heatCount = 2;
  render("frame-fault.pbm", fault);

  render("frame-sleep.pbm", run, true);
  return 0;
}
