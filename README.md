# temp_control

三层爬柜温控系统：NTC 热敏电阻测温 + SSR 开关加热，适用于 Arduino（10 位 ADC）。

## 目录结构

```
temp_control/                       仓库根目录
├── README.md
├── .gitignore
└── firmware/
    └── temp_control/               Arduino sketch 目录
        └── temp_control.ino        主程序
```

Arduino 要求 sketch 目录名与 `.ino` 文件名一致，因此必须打开 `firmware/temp_control/`，而不是仓库根目录。

```bash
# 编译（示例：Arduino Uno）
arduino-cli compile --fqbn arduino:avr:uno firmware/temp_control

# 上传（COM 口按实际修改）
arduino-cli upload --fqbn arduino:avr:uno -p COM3 firmware/temp_control
```

Arduino IDE 2.x 用「文件 → 打开」选择 `firmware/temp_control/temp_control.ino` 即可。

## 接线

NTC 采用上拉接法：`VCC → 10kΩ → ADC 引脚 → NTC → GND`。

| 层   | NTC 模拟输入 | SSR 控制 | 目标温度 |
| ---- | ------------ | -------- | -------- |
| 层 1 | A2           | D2       | 32 ℃     |
| 层 2 | A1           | D3       | 32 ℃     |
| 层 3 | A0           | D4       | 32 ℃     |

SSR 高电平导通。上电时所有 SSR 引脚先置低，避免误加热。

> 注意：`temp_control.ino` 中引脚数组为 `{A2, A1, A0}`，与文件头注释「层1→A0 … 层3→A2」相反。
> 上表以代码数组为准，实际接线前请再核对一次。

## 关键参数

均在 `temp_control.ino` 顶部宏定义中调整：

| 参数               | 值           | 说明                  |
| ------------------ | ------------ | --------------------- |
| `R_REF`            | 10 kΩ        | 上拉电阻              |
| `R_NTC` / `T25`    | 10 kΩ / 25 ℃ | NTC 标称值            |
| `B_VALUE`          | 3950         | NTC B 值              |
| `TEMP_HYSTERESIS`  | 0.8 ℃        | 回差带                |
| `TEMP_MAX_LIMIT`   | 45 ℃         | 超温保护上限          |
| `TEMP_MIN_LIMIT`   | 0 ℃          | 低温保护下限          |
| `FILTER_SAMPLES`   | 8            | 滑动平均窗口          |
| `ADC_SAMPLES`      | 5            | 单次测温 ADC 采样次数 |

各层目标温度见 `targetTemp[LAYER_COUNT]`，默认 `{32.0, 32.0, 32.0}`。

## 保护机制

- ADC 多次采样取平均，抑制随机干扰
- NTC 断线 / 短路 / 阻值异常 / 非有限数统一返回 `NAN`，并强制关闭对应层加热
- 8 点滑动平均滤波，异常读数不写入缓冲区
- 回差控制，避免 SSR 在目标温度附近频繁通断
- 超出 0–45 ℃ 范围立即关断加热

## 串口

波特率 `9600`，每秒打印一次三层温度、目标值与加热状态。
