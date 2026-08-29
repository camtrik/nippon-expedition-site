# 远征尼朋 · 站点

《Total War: WARHAMMER III》mod **「远征尼朋 · 玉海舰队 / Nippon Expedition · The Jade Sea Fleet」** 的公开站点，中英双语。两个页面：

| | 中文 | English |
|---|---|---|
| 简介（与创意工坊描述同步） | <https://camtrik.github.io/nippon-expedition-site/> | [`/en/`](https://camtrik.github.io/nippon-expedition-site/en/) |
| 更新记录 | [`/changelog/`](https://camtrik.github.io/nippon-expedition-site/changelog/) | [`/en/changelog/`](https://camtrik.github.io/nippon-expedition-site/en/changelog/) |

首次访问根路径时，浏览器语言里没有中文的读者会被自动送到 `/en/`。用导航栏的语言开关切过一次之后就不再自动跳——这个自动判断一辈子只做一次。

创意工坊：[本体（中文）](https://steamcommunity.com/workshop/filedetails/?id=3790908242) ·
[English Translation](https://steamcommunity.com/workshop/filedetails/?id=3790908523) ·
[周边 AI 强化子 mod](https://steamcommunity.com/workshop/filedetails/?id=3790907897)

---

> 用 AI agent 维护本仓库请先读 [`AGENTS.md`](./AGENTS.md)：原料在哪、术语怎么查、有哪些坑。

---

## 改简介页

简介页的正文在 `content/home.json`，**中英文写在同一个字段里**（`{"zh": "…", "en": "…"}`），这样漏译一眼就能看出来。内容对着创意工坊描述 `../nippon_expedition/steam_description_{zh,main_en}.txt` 同步即可。

专名不要现编，先查 `../nippon_expedition/_docs/translation/术语对照_*.tsv`，详见 [`AGENTS.md`](./AGENTS.md)。

版式在 `site/_templates/home.html`（各区块的顺序）和 `site/assets/css/home.css`（样式）里；每个区块的 HTML 由 `scripts/build.py` 里对应的 `render_*()` 生成。

## 加一条更新记录

在 `content/releases/` 下新建 `<日期>-v<版本>.md`，中英文写在同一个文件里：

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

front matter 字段：

| 字段 | 必填 | 说明 |
|---|---|---|
| `version` | ✅ | 版本号，页面上显示为 `v1.1.0`。排序时按数字段比较，`1.10.0` 排在 `1.9.0` 之上 |
| `date` | | `YYYY-MM-DD`。列表按日期倒序，同日再按版本号倒序。留空表示还没定日期，该条目排在所有有日期的之上，页面上不显示日期 |
| `type` | | `release` / `content` / `balance` / `hotfix`，默认 `release`。决定右上角徽章 |
| `tags` | | 逗号分隔，目前支持 `main`（本体）、`stronger-ai`（AI 强化）、`nrs-compat`（NRS 兼容包） |

正文用 `<!-- lang: zh -->` / `<!-- lang: en -->` 分段，**中文块必填**。缺英文块时英文页会回落到中文正文，并显示一条「尚未翻译」提示——所以可以先发中文、之后再补翻译。正文标题请从 `###` 起（`#`/`##` 留给页面本身）。

徽章、标签、导航、页脚等界面文案在 `content/i18n.json` 里改；新增 `type` 或 `tags` 取值时，记得同时补 `i18n.json` 的 `TYPE` / `TAGS` 两张表，以及 `scripts/build.py` 顶部的 `KNOWN_TYPES`。

推到 `main` 后 GitHub Actions 自动构建并部署。

## 本地预览

```bash
pip install markdown
python3 scripts/build.py
python3 -m http.server 8000 --directory site/_dist
```

打开 <http://localhost:8000/>：简介页在 `/`，更新记录在 `/changelog/`，英文各自加 `/en` 前缀。

模拟线上的子路径（GitHub Pages 项目站点是 `/nippon-expedition-site/`）：

```bash
SITE_BASE_PATH=/nippon-expedition-site SITE_ORIGIN=https://camtrik.github.io python3 scripts/build.py
```

此时产物里所有站内链接都会带上前缀，需要用 `--directory site` 之类的方式挂到对应路径下才能直接点开；平时本地预览用不带环境变量的那条命令即可。

## 结构

```
.github/workflows/pages.yml   构建 + 部署
content/i18n.json             页面界面文案（中英）
content/releases/*.md         更新记录，一条一个文件
content/home.json             简介页正文（中英同字段）
scripts/build.py              渲染 site/_dist/
scripts/subset_fonts.py       把 LXGW WenKai GB 裁到站点用到的字
site/_templates/home.html     简介页骨架
site/_templates/log.html      更新记录页骨架
site/partials/*.html          <!-- include: NAME.html --> 片段
site/assets/css/base.css      设计 token、导航、页脚
site/assets/css/home.css      简介页
site/assets/css/log.css       更新记录页
site/assets/img/              取自 mod 本体的美术资源
site/assets/fonts/            字体子集（由 subset_fonts.py 生成）
```

产物 `site/_dist/` 不入库，由 Actions 现场构建。

视觉体系与构建做法沿用同作者的 investment 站点，强调色换成玉海舰队的碧玉绿 `#1F8A70` + 金 `#D4AF37`。简介页在此之上多了一套「夜色」token（`--deep` / `--foam` / `--ember`），取色自 mod 自己的战役读取图与阵营徽记，详见 `base.css` 里的注释。

### 正文写法的一个坑

Python-Markdown 会在列表项内部的**空行处直接结束整个列表**，后面的 `- ` 会变成段落里的裸横线。所以补充说明要写成缩进 4 空格的**嵌套子条目**，不要用空行分段：

```markdown
- 主条目
    - ⚠️ 补充说明写在这里
- 下一条
```

构建脚本对这种情况有护栏——一旦渲染结果里出现段落内的裸 `- `，构建会直接报错并指出是哪个文件、哪个语种。
