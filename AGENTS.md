# AGENTS.md

## 这是什么仓库

《Total War: WARHAMMER III》mod **「远征尼朋 · 玉海舰队 / Nippon Expedition · The Jade Sea Fleet」** 的**公开站点**。中英双语，Python 静态构建，GitHub Pages 部署。线上：<https://camtrik.github.io/nippon-expedition-site/>

| 页面 | 内容来源 | 中文 | English |
| --- | --- | --- | --- |
| **简介** | `content/home.json`，与创意工坊描述同步 | `/` | `/en/` |
| **更新记录** | `content/releases/*.md` | `/changelog/` | `/en/changelog/` |

这是**内容仓库，不是 mod 仓库**——这里没有一行游戏数据，mod 本体在隔壁 `../nippon_expedition/`。

## ⚠️ 内容原料在隔壁的私有仓库里

写正文的原料**全部不在本仓库**，在同级的私有仓库 `wh3-mod-projects` 中。下面路径相对本仓库根目录，**只在维护者本机成立**；CI 和别人 clone 的副本里都没有。

| 要什么 | 去哪拿（`../nippon_expedition/` 下） |
| --- | --- |
| **更新记录的原料**（一条改动一行，玩家视角） | `_docs/backlog/version.md` |
| 原版专名中英对照（CA 官方译名） | `_docs/translation/术语对照_原版专名.tsv` |
| 自造专名中英对照 + 定名政策 | `_docs/translation/术语对照_自造专名{,_说明}.*` |
| IEE 地名英文（行省 / 定居点） | `_docs/references/IEE尼朋行省与定居点清单.md` |
| 工坊描述双语成稿 | `steam_description_{zh,en}.txt` |
| NRS 兼容包说明 | `../nippon_expedition_nrs_compat/README_zh.md` |

`version.md` 是更新记录的**唯一权威原料**，已经是「一条改动 = 一行、只写玩家看得懂的功能变化」的粒度，直接改写即可。

**不要从 `_docs/log.md` 搬内容过来**——那是开发流水账（表名、字段、key、排查过程），给开发者看的，不属于公开站。

## 两条内容红线

**1. 专名必须查表，不许现编。** mod 里的专名早就定过案，凭语感另译会和游戏内文本对不上。顺序：自造专名表 → 原版专名表 → 地名查 IEE 清单 → 工坊描述英文稿。全都查不到才可以自己拟，拟完**回填**进 `术语对照_自造专名.tsv`。

```bash
grep -h "长牙之路\|尚武造诣\|武者屋形" ../nippon_expedition/_docs/translation/术语对照_*.tsv
grep "神華" ../nippon_expedition/_docs/references/IEE尼朋行省与定居点清单.md
```

中文专名同样要留神：地名用**玩家在地图上看到的那个**（如 `cr_combi_region_nippon_2_1`，IEE 官中作**竜舰海港**，不是项目文档惯写的「龙舰海港」）。冲突在 IEE 清单里以「译名冲突提醒」标出；`version.md` 通常已经用对，照抄比换词安全。

**2. 写玩家视角，不写实装细节。** 判据是读者不打开 pack 能不能看懂。表名、key、字段一律不写。

## 简介页

正文全在 `content/home.json`，**中英文写在同一个字段里**，这样漏译一眼可见：

```json
"name": { "zh": "『无冕提督』沈长风", "en": "Shen Changfeng, the Uncrowned Admiral" }
```

- 原料是 `steam_description_zh.txt` 与 `steam_description_main_en.txt`，**两边都是作者定过稿的成文**，直接沿用，别重译。
- 工坊描述里没有、页面上有的东西（同伴的四章标题、羁绊四档）来自 mod 仓库 `text/db/*.loc.tsv` 的实装文本，英文取 `术语对照_自造专名.tsv` 里标「已定」的行。**不要自己编章节名。**
- **两条长期胜利路线（海外帝国 / 天朝守护）不是二选一，两条都能打完。** 工坊描述的「（路线A）/（路线B）」写法容易让人误会——这里错过一次。并排版式不表示互斥，文案必须明说。
- 区块 HTML 由 `build.py` 的 `render_*()` 生成，顺序在 `site/_templates/home.html`，样式在 `home.css`。

## 加一条更新记录

完整流程见 skill **`changelog-entry`**。文件是 `content/releases/<日期>-v<版本>.md`，中英同文件：

```markdown
---
version: 1.1.0
date: 2026-09-15
type: content
tags: main
---

<!-- lang: zh -->

### 新增
- ……

<!-- lang: en -->

### Added
- ...
```

- `version` 必填，排序按数字段比较（`1.10.0` 在 `1.9.0` 之上）。
- `date` **留空 = 还没定发布日期**，该条排最上、页面不显示日期，工坊真发布了再补。别编一个日期。
- `type`：`release` / `content` / `balance` / `hotfix`，默认 `release`，决定右上角徽章。
- `tags`：逗号分隔的 `main` / `stronger-ai` / `nrs-compat`。
- 新增 `type` / `tags` 取值要同时改 `content/i18n.json` 的两张表和 `build.py` 的 `KNOWN_TYPES`，漏了构建报错。
- 中文块必填；英文块可缺，缺了英文页自动回落中文并显示「尚未翻译」。

**正文写法的坑：列表里不能有空行。** Python-Markdown 会在列表项内部的空行处结束整个列表，后面的 `- ` 变成段落里的裸横线（踩过一次，构建不报错，只有看页面才发现）。补充说明要写成**缩进 4 空格的子条目**：

```markdown
- 新增可选子 mod「XX 兼容包」。
    - ⚠️ 装上后旧存档会失效。
- 下一条正常继续
```

## 构建与验证

```bash
python3 scripts/build.py
python3 -m http.server 8000 --directory site/_dist   # 中文 /，英文 /en/
```

**要真的打开页面看**，别只看构建没报错。

改动了链接、模板或资源路径后，**务必再跑一次带子路径的构建**——这是最容易翻车的一环：

```bash
SITE_BASE_PATH=/nippon-expedition-site SITE_ORIGIN=https://camtrik.github.io python3 scripts/build.py
grep -oE '(href|src|content)="/[^"]*"' site/_dist/en/index.html | sort -u   # 应全部带前缀
```

- 唯一依赖是 `markdown`。front matter 是手写解析的，**不要引入 PyYAML**。
- `site/_dist/` 不入库，推到 `main` 由 Actions 现场构建部署。
- 加新页面：`build.py` 的 `PAGES` 加一行（`名字: (模板, url 路径)`），补 `i18n.json` 两种语言的 `PAGES` 表，写模板。链接、canonical、hreflang、语言开关会自动按页算好。
- 唯一的 JS 是首访语言判断（`site/partials/head.html`）：根路径上浏览器语言没有中文就跳英文页，用过一次语言开关后写 `localStorage['npex-lang']` 不再自动跳。**这个判断一辈子只做一次**，不要改成每次访问都跳，那会把别人分享的链接顶掉。

## 字体

中文正文用自托管的文楷 GB 子集，**只含站点当前实际渲染的字**。引入了子集里没有的字，构建会报错并列出缺哪几个（护栏是 `build.py` 的 `check_font_coverage()`，别删——缺字不报错就会静默回退系统字体，同一句话里两套字形）。重新生成：

```bash
pip install fonttools brotli      # 只有这个脚本需要，构建本身不需要
python3 scripts/subset_fonts.py
```

生成物（`fonts.css`、两个 woff2、`coverage.txt`）**都要提交**——CI 不装 fonttools，漏提交线上就整站回退系统字体。选型理由见 `subset_fonts.py` 顶部注释，回退栈的顺序（**简体中文字体必须排在任何日文字体之前**）见 `base.css` 里 `--font-sans` 的注释，两处都是修过的 bug，别推翻。

## 目录结构

```
content/i18n.json             界面文案 + 每页 title / description（zh / en）
content/home.json             简介页正文（中英同字段）
content/releases/*.md         更新记录，一条一个文件
scripts/build.py              渲染到 site/_dist/
scripts/subset_fonts.py       切中文字体子集（加了新字才需要跑）
site/_templates/*.html        页面骨架
site/partials/*.html          <!-- include: NAME.html --> 片段
site/assets/css/fonts.css     @font-face，subset_fonts.py 生成，别手改
site/assets/css/base.css      设计 token + 全局 + 导航 + 页脚
site/assets/css/{home,log}.css
site/assets/fonts/            文楷 GB 子集 + coverage.txt，都要提交
site/assets/img/              从 mod 本体拷来压缩的美术资源，要换图去那边取原图重压
```

配色 token 是从 mod 自己的美术里取样的，改之前先看 `base.css` 的注释。

## 可用 skill

- **`changelog-entry`** —— 核心工作流：取料 → 写中文 → 查表译英文 → 构建验证。
- **`translate-polisher`** —— 四步精翻，译大段正文时用。外部 vendored 内容（MIT），**不要就地改**。

隔壁私有仓库 `../../.agents/skills/` 还有只在本机可用的 `warhammer-mod-translation`、`chinese-writing`、`humanizer-zh`。

## 最后

本仓库是**公开**的，隔壁 `wh3-mod-projects` 是**私有**的。往这边写东西前想一下该不该公开。
