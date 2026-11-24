# 烧录指南

适用于 **Arduino Pro Mini 5V / 16MHz（ATmega328P）**。Pro Mini 没有 USB 接口，
需要通过 USB-TTL 转接板（FTDI 6P 排针）或 ISP 烧录。

> 烧录和调试时先断开 220V，只给主板接 5V。确认接线无误后再接 SSR 和加热负载。

## 目标配置

| 项目 | 值 |
| ---- | -- |
| 开发板 | Arduino Pro Mini（ATmega328P） |
| 工作电压 / 时钟 | **5V / 16MHz** |
| FQBN | `arduino:avr:pro:cpu=16MHzatmega328` |
| 上传波特率 | `57600`（Pro Mini 标准引导程序） |
| 依赖库 | `U8g2`（by oliver） |
| 串口日志 | `9600`，8N1 |

不要选成「ATmega328P (3.3V, 8 MHz)」：程序仍可能烧进去，但时钟配置错误会导致
`millis()` 计时、串口波特率和控制周期全部偏离。

## 准备

- Arduino Pro Mini 5V/16MHz 一块。
- USB-TTL 转接板：CH340、CP2102 或 FT232，**5V 电平**，最好带 DTR 引脚。
- 杜邦线若干；如果转接板没有 DTR，准备一个轻触按键或直接用板载 RST。
- 5V 稳压电源（调试阶段可用 USB-TTL 的 5V 供电）。
- 0.1µF 电容（仅在板子没有 DTR 隔直电容时需要）。
- 任意串口监视器均可；推荐 Arduino IDE 2.x 或 `arduino-cli`。

## 安装工具

### Arduino IDE 2.x

1. 打开「开发板管理器」，安装 **Arduino AVR Boards**。
2. 打开「库管理器」，搜索并安装 **U8g2**（作者 oliver）。
3. 打开 `firmware/temp_control/temp_control.ino`。
4. 开发板选择 **Arduino Pro or Pro Mini** → **ATmega328P (5V, 16 MHz)**。
5. 选择正确的 COM 口，先点「验证」，再点「上传」。

### arduino-cli

安装好 `arduino-cli` 后执行：

```bash
arduino-cli core update-index
arduino-cli core install arduino:avr
arduino-cli lib install U8g2
arduino-cli board list
```

编译并上传（把 `COM3` 换成实际端口）：

```bash
arduino-cli compile --fqbn arduino:avr:pro:cpu=16MHzatmega328 --warnings all firmware/temp_control
arduino-cli compile --fqbn arduino:avr:pro:cpu=16MHzatmega328 -u -p COM3 firmware/temp_control
```

也可以先导出二进制，再用 `upload` 单独烧录：

```bash
arduino-cli compile --fqbn arduino:avr:pro:cpu=16MHzatmega328 --output-dir build/flashing firmware/temp_control
arduino-cli upload --fqbn arduino:avr:pro:cpu=16MHzatmega328 -p COM3 -i build/flashing/temp_control.ino.hex
```

Linux 端口通常是 `/dev/ttyUSB0` 或 `/dev/ttyACM0`，macOS 通常是
`/dev/cu.usbserial-*`。Linux 若提示权限不足，把当前用户加入 `dialout` 组后重新登录：

```bash
sudo usermod -aG dialout 你的用户名
```

当前版本（U8g2 2.36.x、Arduino AVR 1.8.8）编译结果参考：

```text
Sketch uses 21640 bytes (70%) of program storage space. Maximum is 30720 bytes.
Global variables use 1236 bytes (60%) of dynamic memory, leaving 812 bytes for local variables. Maximum is 2048 bytes.
```

## USB-TTL 接线

Pro Mini 的 6P FTDI 排针以板上丝印为准，常见信号对应关系如下：

| USB-TTL | Pro Mini | 说明 |
| ------- | -------- | ---- |
| DTR | DTR / RST | 自动复位；经 0.1µF 电容接 RST |
| RXD | TXO | **交叉连接** |
| TXD | RXI | **交叉连接** |
| VCC | VCC | 5V；只在没有其他电源时连接 |
| GND | GND | 必须共地 |
| CTS | 不接 | 本项目不需要硬件流控 |

注意事项：

- USB-TTL 的电压选择跳线必须放在 **5V** 档；3.3V 电平可能无法可靠烧录。
- **TX/RX 必须交叉**：转接板 RXD 接板子 TXO，转接板 TXD 接板子 RXI。
- 一定要共地，否则会出现「programmer is not responding」或随机失败。
- 如果板子已经由外部 7–12V 接 `RAW` 供电，**不要再接 USB-TTL 的 VCC**，只接
  DTR、RXD、TXD、GND 四根信号线。
- 如果用外部稳压 5V 直接接 `VCC`，同样不要并联 USB-TTL 的 VCC。
- 5V 不要接 `RAW`；`RAW` 需要 7–12V，5V 进入板载稳压器会欠压。

### 自动复位

标准 Pro Mini 在 FTDI 座附近有一颗 **0.1µF 电容**，把 DTR 的负脉冲耦合到 RST，
实现「点上传后自动复位并进入引导程序」。如果自动复位不稳定：

1. 确认 DTR 已接（不是只接 TX/RX/VCC/GND）。
2. 确认板上有 DTR→RST 的 0.1µF 电容；没有则串联一颗，**不要直接短接 DTR 和 RST**。
3. 仍失败时改用手动复位，见下一节。

## 烧录步骤

### 自动复位

1. 接好 USB-TTL，插上 USB。
2. 选择正确的开发板和 COM 口。
3. 点击「上传」。
4. 等待出现 `Uploading...` 或 avrdude 连接提示；正常情况下无需按 RST。

### 手动复位

适合没有 DTR、自动复位失效或使用裸板的情况：

1. 先按住板载 **RST** 不放。
2. 在 IDE/CLI 中启动上传。
3. 看到 `Uploading...` 或 avrdude 开始连接时，松开 RST。
4. 若仍失败，重复一次，稍微调整松开时机；引导程序等待窗口只有约 1 秒。

### avrdude 直烧

不推荐新手使用，但在批量或脚本化烧录时很方便。先找到 Arduino 安装目录下的
`avrdude` 和 `avrdude.conf`（通常在 `Arduino15/packages/arduino/tools/avrdude/` 下）：

```bash
avrdude -C /path/to/avrdude.conf -v -p atmega328p -c arduino -P COM3 -b 57600 -D -U flash:w:build/flashing/temp_control.ino.hex:i
```

`-D` 表示不执行芯片擦除，通常可以保留 EEPROM 中的设定值；如果怀疑 EEPROM 数据损坏，
可以去掉 `-D` 或按调试指南擦除 EEPROM。不要烧写
`*.with_bootloader.hex`，串口烧录应使用 `temp_control.ino.hex`。

## 首次上电自检

烧录完成后打开串口监视器，波特率 **9600**：

```text
5-channel temp controller ready
SET 32.0 HY 0.8 HEAT 0 | L1 ERR | L2 ERR | L3 ERR | L4 ERR | L5 ERR
```

- 第一行出现 `5-channel temp controller ready`，说明固件已运行。
- 之后每秒输出一行状态；没有接 NTC 时显示 `ERR` 且 SSR 关闭，这是正常现象。
- OLED 顶部应显示大号 `32.0C`，右上角为 `HY 0.8C` 和 `HEAT 0/5`，下面 5 行对应 5 个通道。
- 如果之前保存过设定值，`SET` 可能不是 32.0，这是 EEPROM 恢复的结果，不是烧录失败。

## 常见烧录错误

| 现象 | 常见原因 | 处理 |
| ---- | -------- | ---- |
| `avrdude: ser_open(): can't open device` | 串口被占用、端口选错、驱动未装 | 关闭串口监视器/其他串口工具；设备管理器确认 COM 口；重装 CH340/CP2102 驱动 |
| `programmer is not responding` / `not in sync` | TX/RX 未交叉、未共地、没供电、自动复位失败 | 按「USB-TTL 接线」逐根核对；改手动复位；换一根 USB 线 |
| `invalid device signature 0x000000` | 板子没供电、接线错误、芯片型号不对 | 测 VCC 5V；确认是 ATmega328P；检查 GND |
| `verification error` | 电源不稳、晶振/时钟不对、波特率不匹配 | 换 5V/1A 电源；确认是 16MHz 板；上传速度用 57600（或该引导程序的实际波特率） |
| `stk500_getsync(): not in sync: resp=0x00` | 没抓到引导程序窗口 | 按住 RST → 点上传 → 出现 Uploading 后松开 |
| `can't set com-state` | CH340 驱动/线材问题 | 换 USB 口、换线、重装驱动 |
| `Permission denied`（Linux） | 当前用户没有串口权限 | 加入 `dialout` 组并重新登录 |
| 上传成功但串口乱码 | 选成 8MHz、USB-TTL 3.3V、波特率不对 | 改回 5V/16MHz；串口设为 9600 8N1 |
| 提示找不到 `U8g2lib.h` | 库未安装或装错 | 库管理器安装 **U8g2 by oliver**，重新编译 |

补充：

- Pro Mini 标准引导程序使用 **57600** 波特率。若板子被重新烧过 Optiboot 且使用 115200，
  可在上传时覆盖速度：
  ```bash
  arduino-cli upload --fqbn arduino:avr:pro:cpu=16MHzatmega328 -p COM3 --upload-property upload.speed=115200 -i build/flashing/temp_control.ino.hex
  ```
- 烧录时不要同时打开串口监视器；串口被占用会导致打不开端口。
- USB-TTL 只输出 3.3V 时，不要用它给 5V Pro Mini 供电；可改用外部 5V 供电；若只有 3.3V 模块，需要电平转换后再接 5V 板。
- 若板子接在 `RAW` 12V 上，USB-TTL 的 VCC 悬空，避免两路电源冲突。

## 引导程序损坏时用 ISP 恢复

串口始终无法同步，且确认接线/供电没问题时，可能是引导程序损坏或被改坏：

1. 用 USBasp，或另一块 Arduino 烧录「Arduino as ISP」。
2. 连接 ISP 的 `MOSI / MISO / SCK / RESET / VCC / GND`。
3. 在 IDE 中选择 **Arduino Pro or Pro Mini / ATmega328P (5V, 16 MHz)**，选择对应编程器。
4. 执行「烧录引导程序」（Burn Bootloader）。
5. 恢复后重新用 USB-TTL 串口烧录固件。

注意：烧录引导程序通常会执行芯片擦除，**EEPROM 中的设定值也会丢失**；恢复后第一次上电会写回默认值。

## 烧录检查清单

- [ ] 开发板选的是 **5V / 16MHz**
- [ ] FQBN 是 `arduino:avr:pro:cpu=16MHzatmega328`
- [ ] U8g2 库已安装
- [ ] TX/RX 已交叉，GND 已共地
- [ ] USB-TTL 是 5V 档
- [ ] 只使用一路电源（USB-TTL VCC / 外部 5V / RAW 三选一）
- [ ] 烧录时 220V 已断开
- [ ] 烧录后串口出现 `5-channel temp controller ready`
