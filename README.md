# Temporal Dithering Encoder

把文字或圖片藏在一組看起來完全像隨機雜訊的幀序列裡。
單幀毫無訊號——但將全部幀疊加平均（或在螢幕上快速播放），隱藏的內容就會浮現。

## 核心概念

| 單幀（純雜訊） | 多幀平均（訊號顯現） |
|:---:|:---:|
| 🟫🟫🟫🟫🟫 | **SECRET** |

每個像素的「開/關」機率被精心設計成等於訊號亮度值，
因此時間平均後能完整重建訊號。

---

## 算法比較

| 算法 | 說明 | 優點 | 缺點 |
|------|------|------|------|
| `random` | 每像素獨立隨機選幀（v3） | 最簡單 | 單幀有空間結塊 |
| `bluenoise` | IGN 藍噪聲時間抖動（v4，**預設**） | 單幀空間均勻，無結塊 | 略慢 |
| `sparse` | 部分幀帶訊號，其餘純雜訊 | 誘餌幀零洩漏 | 訊號幀對比較高 |
| `partition` | 每幀凸顯空間一段 | 可支援多訊號切換 | 部分幀仍有微弱訊號 |

---

## 安裝

```bash
pip install -r requirements.txt
```

**依賴：** Python 3.9+、NumPy 1.24+、Pillow 10.0+

---

## 使用方式

```bash
python encode.py --help
```

### 基本（文字）

```bash
python encode.py --text "Secret" -n 6 -o output --preview-gif
```

### 比較 random vs bluenoise

```bash
python encode.py --text "Secret" -n 6 -o out_random    --method random
python encode.py --text "Secret" -n 6 -o out_bluenoise --method bluenoise
```

### Sparse 模式（誘餌幀）

```bash
# 8 幀中只有 3 幀帶訊號，其餘 5 幀是純雜訊
python encode.py --text "Secret" -n 8 -o output --method sparse --signal-frames 3
```

### Partition 模式（空間分區）

```bash
# 6 幀各自凸顯一個水平段，次要段帶弱訊號
python encode.py --text "ABCDEF" -n 6 -o output \
    --method partition --contrast 0.8 --passive-contrast 0.15
```

### 圖片輸入

```bash
python encode.py --image logo.png -n 6 -o output --method bluenoise
```

---

## 全部參數

```
輸入（二選一，必填）：
  --text TEXT             要隱藏的文字
  --image IMAGE           要隱藏的圖片路徑

基本設定：
  -n, --frames N          幀數（預設 6）
  -o, --output-dir DIR    輸出資料夾（預設 output/）
  --canvas W H            畫布尺寸（預設 400 150）
  --contrast FLOAT        訊號對比 0~1（預設 0.4）
  --invert                反轉訊號（白底黑字）
  --font-size INT         字型大小（預設自動縮放）
  --font PATH             字型檔路徑
  --seed INT              隨機種子（可重現結果）

預覽：
  --preview-gif           輸出 _preview_animation.gif
  --preview-fps INT       GIF 幀率（預設 24）

算法選擇：
  --method {random,bluenoise,sparse,partition}
  --signal-frames INT     （sparse）帶訊號的幀數
  --direction {horizontal,vertical}  （partition）切割方向
  --passive-contrast FLOAT           （partition）非啟用區對比

訊號前處理：
  --outline               只保留輪廓線
  --outline-width INT     輪廓寬度（預設 2）
  --density FLOAT         隨機稀疏像素（預設 1.0 = 不稀疏）
  --prefilter             編碼前高斯模糊邊緣
  --blur FLOAT            模糊半徑（預設 1.5）
```

---

## 輸出結構

```
output/
├── frame_01.png          ← 單幀（看起來是純雜訊）
├── frame_02.png
├── ...
├── _preview_average.png  ← 所有幀平均（訊號顯現）
├── _signal_processed.png ← 前處理後的原始訊號
└── _preview_animation.gif  ← （加 --preview-gif 才有）
```

---

## 以程式庫方式使用

```python
import numpy as np
from arg_encoder import encode_bluenoise, make_text_signal, save_outputs

sig = make_text_signal("Hi", canvas_size=(400, 150))
sig_arr = np.array(sig, dtype=np.float32) / 255.0

frames = encode_bluenoise(sig_arr, n_frames=6, contrast=0.4, seed=42)
save_outputs(frames, sig_arr, "output", gif=True)
```

---

## 原理說明

### 藍噪聲時間抖動（v4 預設算法）

對每一幀生成一張 **Interleaved Gradient Noise (IGN)** 閾值圖：

```
threshold(x, y) = fract(52.9829189 × fract(0.06711056×(x+ox) + 0.00583715×(y+oy)))
frame[f][x,y] = 255  if  threshold < signal[x,y]
```

- `ox`, `oy` 每幀都不同 → 每幀都是獨立的藍噪聲圖
- 藍噪聲性質 → 任何單幀的亮點空間均勻分散，無結塊
- 時間平均 = 訊號值（機率期望值等式）

相比 v3 random 算法，單幀的空間均勻度提升約 30~50%，訊號更難被察覺。

---

## License

Apache 2.0 — see [LICENSE](LICENSE).
