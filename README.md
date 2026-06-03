# PhantomFrame

把文字或圖片藏在一組看起來完全像隨機雜訊的幀序列裡，或直接混入一張照片中。
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
| `random` | 每像素獨立隨機選幀（**預設**） | 自然雜訊感 | — |
| `bluenoise` | IGN 藍噪聲時間抖動 | 單幀空間均勻 | 低對比下與 random 差異不大 |
| `sparse` | 部分幀帶訊號，其餘純雜訊 | 誘餌幀零洩漏 | 訊號幀對比較高 |
| `partition` | 每幀凸顯空間一段 | 可支援多訊號切換 | 部分幀仍有微弱訊號 |

> **混入背景（不是一種 `--method`）**：只要加上 `--bg photo.jpg`（藏進照片）或 `--bg-color 80`（藏進純色色塊），
> 就會自動切到背景混合模式，把訊號藏成底片顆粒。詳見下方 [Blend 背景混合](#blend-背景混合)。

---

## 安裝

```bash
# 方式一：只裝依賴，直接跑腳本
pip install -r requirements.txt

# 方式二：裝成套件（提供 phantomframe 指令，import 也能被工具正確解析）
pip install -e .
```

**依賴：** Python 3.9+、NumPy 1.24+、Pillow 10.0+

---

## 使用方式

兩種等價的執行方式：

```bash
python encode.py --help      # 直接跑腳本
phantomframe --help          # 裝成套件後（pip install -e .）
```

### 基本（文字）

```bash
python encode.py --text "Secret" -n 6 -o output --preview-gif
```

### 比較不同算法

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

### Blend 背景混合

加 `--bg` 或 `--bg-color` 即自動進入背景混合模式（不需指定 `--method`）：

```bash
# 背景照片 + 隱藏文字（單幀看起來像加了底片顆粒的真實照片）
python encode.py --text "Secret" -n 16 -o output --bg photo.jpg --preview-gif

# 無照片時，用純色色塊（灰階 0-255）
python encode.py --text "Secret" -n 16 -o output --bg-color 80
```

> **原理：** 只在文字周圍的「柔邊光暈」內加入零均值高斯顆粒（背景照片其餘部分完全不動）。
> 文字像素帶一個極小的亮度偏移 = `contrast × 顆粒強度`，小到單幀被顆粒淹沒；
> 但時間平均會把顆粒縮小 ~√幀數 倍，偏移浮現 → 文字顯影。
>
> 四個關鍵參數：
> - `--contrast`：訊號相對顆粒的比例（0-1）。越小單幀越藏得住，但要更多幀才讀得到。單幀/平均的可見度差距 ≈ √幀數。
> - `--amplitude`：每幀顆粒深度（預設 0.12）。越高單幀越藏得住、但顆粒越明顯。
> - `--halo`：文字周圍光暈半徑（像素，預設 8；設 0 = 整張畫面都加顆粒）。
> - `--texture`：顆粒隨局部細節自適應（0-1，預設 1）。**視覺遮蔽**原理——複雜花紋處放滿顆粒（藏得住），平坦單色區自動降顆粒（不然會很明顯）。顆粒與訊號在平坦區同比例縮小，所以單幀隱蔽比例不變。設 0 = 整張均勻顆粒（舊行為）。
>
> 彩色背景的顆粒會依 Rec.709 亮度等比縮放各通道，**保留色相**（紅色區域只會變亮紅/暗紅，不偏白）。
>
> **小提醒：** 文字盡量放在背景有紋理的地方。純單色區（如天空、白牆）因為沒有細節可遮蔽，藏字效果天生較差。

### 圖片輸入

```bash
python encode.py --image logo.png -n 6 -o output --method random
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
  --canvas W H            畫布尺寸（預設：有 --bg 時取背景圖尺寸，否則 400 150）
  --contrast FLOAT        訊號強度 0~1（預設：雜訊算法 0.4；blend 為訊號/顆粒比例 0.3）
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

背景混合（加任一個即啟用 blend）：
  --bg PATH               背景圖片路徑（藏進照片）
  --bg-color INT          純色背景灰階值 0-255（藏進單色色塊）
  --amplitude FLOAT       每幀顆粒深度（預設 0.12）
  --halo INT              文字光暈半徑 px（預設 8；0 = 整張加顆粒）
  --texture FLOAT         顆粒隨局部細節自適應 0-1（預設 1；0 = 均勻）

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
from phantomframe import (
    encode_random, encode_blend,
    make_text_signal, load_background, save_outputs,
)

# 純雜訊模式
sig = make_text_signal("Hi", canvas_size=(400, 150))
sig_arr = np.array(sig, dtype=np.float32) / 255.0
frames = encode_random(sig_arr, n_frames=6, contrast=0.4, seed=42)
save_outputs(frames, sig_arr, "output", gif=True)

# Blend：藏進照片
bg = load_background("photo.jpg", canvas_size=(800, 600), color=True)
sig = make_text_signal("Hi", canvas_size=(800, 600))
sig_arr = np.array(sig, dtype=np.float32) / 255.0
frames = encode_blend(sig_arr, bg, n_frames=16, contrast=0.3,
                      amplitude=0.12, halo=8, texture=1.0, seed=42)
save_outputs(frames, sig_arr, "output", gif=True)
```

---

## 原理說明

### 時間抖動（random，預設）

每個像素在 N 幀中亮起的次數 ∝ 訊號亮度值。任何單幀的亮點是隨機散布的純雜訊，
但 N 幀疊加平均後，每像素的平均亮度 = 訊號值，圖案完整重現。
純白雜訊跟相機感光雜訊同性質，疊在照片上最自然。

### Blend 背景混合（藏進照片的主力）

只在文字周圍的柔邊光暈內加入零均值高斯顆粒，背景照片其餘部分完全不動：

```
delta = alpha × (signal × contrast × grain_std + grain)        # grain ~ Normal(0, grain_std)
frame = background + delta            （彩色則依 Rec.709 亮度等比縮放，保留色相）
```

- 顆粒零均值 → 時間平均後相互抵消 → 背景完整還原
- 訊號偏移僅為顆粒的 `contrast` 比例 → 單幀被顆粒淹沒，平均 ~√幀數 倍降噪後才浮現
- `grain_std` 隨局部紋理自適應（視覺遮蔽）→ 複雜處藏得住、平坦單色區自動安靜

### 藍噪聲時間抖動（bluenoise，選用）

對每一幀生成一張 **Interleaved Gradient Noise (IGN)** 閾值圖：

```
threshold(x, y) = fract(52.9829189 × fract(0.06711056×(x+ox) + 0.00583715×(y+oy)))
frame[f][x,y] = 255  if  threshold < signal[x,y]
```

每幀亮點空間均勻分散、無結塊；但在低對比實務上與 random 差異不大，故預設用 random。

---

## License

Apache 2.0 — see [LICENSE](LICENSE).
