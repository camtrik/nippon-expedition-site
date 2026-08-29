# AGENTS.md

## 这是什么仓库

《Total War: WARHAMMER III》mod **「远征尼朋 · 玉海舰队 / Nippon Expedition · The Jade Sea Fleet」** 的**公开更新记录站点**。中英双语，Python 静态构建，GitHub Pages 部署。

- 线上：<https://camtrik.github.io/nippon-expedition-site/>（英文 `/en/`）
- 这是个**内容仓库，不是 mod 仓库**。这里没有一行游戏数据；mod 本体在隔壁 `../nippon_expedition/`。
- 目前只有一个更新记录页。以后可能加兵种、机制说明等页面，结构留了位置。

## ⚠️ 内容来源在另一个仓库，而且那个仓库是私有的

写更新记录的原料**全部不在本仓库里**，在同级目录的私有仓库 `wh3-mod-projects` 中。下面所有路径都相对本仓库根目录，**只在维护者本机成立**；在 CI、在别人 clone 下来的副本里都不存在。

| 要什么 | 去哪拿 |
| --- | --- |
| **公开更新记录的原料**（一条改动一行，玩家视角） | [`../nippon_expedition/_docs/backlog/version.md`](../nippon_expedition/_docs/backlog/version.md) |
| 原版专名中英对照（CA 官方译名，148 行） | [`../nippon_expedition/_docs/translation/术语对照_原版专名.tsv`](../nippon_expedition/_docs/translation/术语对照_原版专名.tsv) |
| 本项目自造专名中英对照（358 行） | [`../nippon_expedition/_docs/translation/术语对照_自造专名.tsv`](../nippon_expedition/_docs/translation/术语对照_自造专名.tsv) |
| 自造专名的定名政策（为什么这么译） | [`../nippon_expedition/_docs/translation/术语对照_自造专名_说明.md`](../nippon_expedition/_docs/translation/术语对照_自造专名_说明.md) |
| IEE 地名英文（行省 / 定居点） | [`../nippon_expedition/_docs/references/IEE尼朋行省与定居点清单.md`](../nippon_expedition/_docs/references/IEE尼朋行省与定居点清单.md) |
| 工坊描述双语成稿（大段介绍的现成译文） | `../nippon_expedition/steam_description_{zh,en}.txt`、`steam_description_stronger_ai.txt` |
| NRS 兼容包说明 | [`../nippon_expedition_nrs_compat/README_zh.md`](../nippon_expedition_nrs_compat/README_zh.md) |

**`version.md` 是唯一权威原料。** 它由 mod 仓库那边按「一条改动 = 一行、只写玩家看得懂的功能变化」的规则维护，正好就是公开 changelog 需要的粒度，直接改写即可。

**不要从 [`../nippon_expedition/_docs/log.md`](../nippon_expedition/_docs/log.md) 搬内容到公开站。** 那是开发流水账，写的是表名、字段、key、根因排查过程，1500 行以上，是给开发者看的。玩家不关心 `campaign_character_arts_tables.land_animation` 改成了什么。

## 怎么加一条更新记录

### 1. 建文件

`content/releases/<日期>-v<版本>.md`，中英正文写在同一个文件里：

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

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `version` | ✅ | 显示为 `v1.1.0`。排序按数字段比较，`1.10.0` 在 `1.9.0` 之上 |
| `date` | | `YYYY-MM-DD`。**留空 = 还没定发布日期**，该条排在所有有日期的之上，页面上不显示日期。工坊真发布了再补上 |
| `type` | | `release` / `content` / `balance` / `hotfix`，默认 `release`。决定右上角徽章 |
| `tags` | | 逗号分隔：`main`（本体）、`stronger-ai`（AI 强化）、`nrs-compat`（NRS 兼容包） |

新增 `type` 或 `tags` 取值时，要同时改三处：`content/i18n.json` 的 `TYPE` / `TAGS` 两张表（中英各一份）、`scripts/build.py` 顶部的 `KNOWN_TYPES`。漏了会在构建时报错，不会静默。

### 2. 写中文

对着 `version.md` 那一版的条目改写，按「新增 / 修复 / 调整」分组。写玩家视角的「加了什么、修了什么」，**不写表名、key、字段、实装细节**——判据是读者不打开 pack 能不能看懂。

### 3. 翻英文——专名必须查表，不许现编

这是本仓库最容易出错的一步。mod 里的专名早就定过案了，凭语感另译会和游戏内文本对不上，玩家看不懂。

**流程**：先查 `术语对照_自造专名.tsv`（本项目自造的，如 沈长风 = Shen Changfeng、武者屋形 = Warrior's Manor），再查 `术语对照_原版专名.tsv`（CA 官方译名，如 黎山 = Mount Li、尚武造诣 = Martial Prowess），地名另查 IEE 清单（如 橙色神華大社 = Temple of the Orange Simca）。都查不到再去 `steam_description_en.txt` 里找现成表述。

```bash
grep -h "长牙之路\|尚武造诣\|武者屋形" ../nippon_expedition/_docs/translation/术语对照_*.tsv
grep "神華" ../nippon_expedition/_docs/references/IEE尼朋行省与定居点清单.md
```

中文专名同样要留神：更新记录是给玩家看的引导文案，地名要用**玩家在地图上看到的那个**。例如 `cr_combi_region_nippon_2_1`，IEE 官中作**竜舰海港**，而项目文档惯写「龙舰海港」——公开文案用前者。这类冲突在 IEE 清单里以「译名冲突提醒」引用块标出。`version.md` 原文通常已经用对了，照抄比自己换词安全。

**全都查不到才可以自己拟**，拟完把这条回填进 `术语对照_自造专名.tsv`，别让下次再拟一遍。

中文块必填；英文块可以缺——缺了英文页会自动回落到中文正文并显示一条「尚未翻译」提示，支持先发中文、之后补译。

### 4. 构建并肉眼看

```bash
python3 scripts/build.py
python3 -m http.server 8000 --directory site/_dist
```

中文 <http://localhost:8000/>，英文 `/en/`。**要真的打开看**，别只看构建没报错。

## 正文写法的坑：列表里不能有空行

Python-Markdown 会在列表项内部的**空行处直接结束整个列表**，后面的 `- ` 会变成段落里的裸横线——这个坑踩过一次，五条 bullet 被折进一个段落，构建不报错、只有看截图才发现。

补充说明要写成**缩进 4 空格的嵌套子条目**：

```markdown
- 新增可选子 mod「XX 兼容包」。
    - ⚠️ 装上后旧存档会失效。
- 下一条正常继续
```

`scripts/build.py` 现在有护栏：渲染后一旦在段落里检出行首裸 `- `，构建直接报错并指出文件与语种。别把这个检查删了。

## 字体：中文栈不要动

`site/assets/css/base.css` 的 `--font-sans` 里，**简体中文字体必须排在任何日文字体之前**：

```
"Sofia Sans", -apple-system, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif
```

原因（这个 bug 修过一次）：Sofia Sans 是纯拉丁字体，`-apple-system` 也没有汉字，所以中文会落到栈里第一个有汉字的字体。之前那版把 `Hiragino Sans`（日文）排在 `PingFang SC` 前面，结果中日共有的汉字（直、骨、真、麒麟）用日文字形，而简体独有字（铳、羁、阵、舰、队）日文字库没有、只能再往后落到 PingFang SC——**同一句话里两套字体**。

`Hiragino Sans GB` 名字里带 Hiragino，但它是简体面孔，可以留；`Hiragino Sans` 和 `Yu Gothic` 是日文，不要加回来。

## 构建与部署

`scripts/build.py` 干的事：读 `content/i18n.json` + `content/releases/*.md`，用 `site/_templates/log.html` 渲染两遍，输出 `site/_dist/{index.html, en/index.html}`，`site/assets/` 原样拷过去。语言切换是**构建期算好的静态链接，零 JS**。

- 唯一依赖是 `markdown`（`pip install markdown`）。front matter 是手写解析的，**不要为了省事引入 PyYAML**。
- `site/_dist/` 不入库，由 Actions 现场构建。
- 环境变量：`SITE_BASE_PATH`（子路径前缀）、`SITE_ORIGIN`（canonical / og:image 用的 scheme+host）。`.github/workflows/pages.yml` 从 `actions/configure-pages` 的 `base_path` / `origin` 输出自动传入。
- 改动了链接、模板或资源路径后，**务必跑一次带子路径的构建**再推——这是项目站点最容易翻车的一环：

```bash
SITE_BASE_PATH=/nippon-expedition-site SITE_ORIGIN=https://camtrik.github.io python3 scripts/build.py
grep -oE '(href|src|content)="/[^"]*"' site/_dist/en/index.html | sort -u   # 应全部带前缀
```

推到 `main` 即自动构建部署。

## 目录结构

```
.github/workflows/pages.yml   构建 + 部署
.claude/skills/               本仓库可用的 skill（见下）
content/i18n.json             页面界面文案（zh / en 两份）
content/releases/*.md         更新记录，一条一个文件
scripts/build.py              渲染到 site/_dist/
site/_templates/log.html      页面骨架
site/partials/*.html          <!-- include: NAME.html --> 片段
site/assets/css/base.css      设计 token + 全局 + 通用组件
site/assets/css/log.css       更新记录页专属
site/assets/{favicon.svg,preview.png}
```

视觉体系照抄自同作者的 investment 站点（奶油底 + 墨黑页脚 + 悬浮 nav pill + Sofia Sans），强调色换成玉海舰队自家的碧玉绿 `#1F8A70` + 金 `#D4AF37`（取自 mod 的 `db/factions_tables/cth_npex`）。

## 可用 skill

`.claude/skills/` 下：

- **`changelog-entry`** —— 本仓库的核心工作流：从 `version.md` 取料 → 写中文 → 查表译英文 → 构建验证。加更新记录时用这个。
- **`translate-polisher`** —— 中英日互译的四步精翻工作流（分析→初译→审校→终稿）。外部 vendored 内容（MIT，见目录内 `LICENSE` 与 `UPSTREAM.md`），**不要就地改**。译大段正文时用；译几条 bullet 用 `changelog-entry` 里的流程即可。

隔壁私有仓库 `../../.agents/skills/` 还有几个只在本机可用的：`warhammer-mod-translation`（loc/TSV 翻译规范）、`chinese-writing`（中文写作风格）、`humanizer-zh`。

## 不要做的事

- **不要把 `_docs/log.md` 的开发细节搬到公开站**——表名、key、根因排查过程都不属于这里。
- **不要凭语感译专名**——先查两张对照表，查不到再拟，拟完回填。
- **不要提交 `site/_dist/`**——已在 `.gitignore`，构建产物由 Actions 生成。
- **不要在列表项里用空行分段**——见上面那节。
- **不要把日文字体加回 `--font-sans`**——见上面那节。
- **不要给还没发布的版本编一个日期**——`date` 留空即可，页面会正确处理。
- 本仓库是**公开**的，隔壁 `wh3-mod-projects` 是**私有**的。往这边写东西前想一下该不该公开。
