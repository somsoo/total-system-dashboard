import os
import requests
import json
import sys
import subprocess
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

GITHUB_USER = "somsoo"
TOKEN = os.environ.get("GITHUB_TOKEN")

headers = {"Accept": "application/vnd.github.v3+json"}
if TOKEN:
    headers["Authorization"] = f"token {TOKEN}"

print("Fetching repository list...")

repos = []
try:
    res = subprocess.run(
        ["gh", "repo", "list", GITHUB_USER, "--limit", "100", "--json", "name,description,isPrivate,pushedAt,url,defaultBranchRef"],
        capture_output=True
    )
    if res.returncode == 0 and res.stdout:
        repos = json.loads(res.stdout.decode('utf-8'))
except Exception as e:
    print(f"gh cli fallback: {e}")

if not repos:
    repos_url = f"https://api.github.com/users/{GITHUB_USER}/repos?per_page=100"
    r = requests.get(repos_url, headers=headers)
    if r.status_code == 200:
        repos = r.json()
    else:
        print(f"Failed to fetch repos: {r.status_code}")
        sys.exit(1)

print(f"Total {len(repos)} repositories loaded.")

def get_raw_file(repo_name, branch, path):
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{repo_name}/{branch}/{path}"
    try:
        resp = requests.get(url, headers=headers, timeout=3)
        if resp.status_code == 200:
            return resp.text.strip().replace('\x00', '')
    except:
        pass
    return None

categories = {
    "coupang": [],
    "cpa": [],
    "expert": [],
    "threads": [],
    "naver": [],
    "utility_legal_finance": [],
    "utility_life_social": [],
    "portal": [],
    "other": []
}

sites_data = []

for idx, r in enumerate(repos):
    name = r["name"]
    branch = r.get("defaultBranchRef", {}).get("name", "main") if isinstance(r.get("defaultBranchRef"), dict) else r.get("default_branch", "main")
    desc = r.get("description") or ""
    pushed_at = r.get("pushedAt", "")[:10]
    is_private = r.get("isPrivate", False)

    cname = get_raw_file(name, branch, "CNAME")
    if not cname and not is_private and name not in ["total-system-dashboard", "pages"]:
        cname = f"{name}.enjoy-onepage.com"
            
    live_url = f"https://{cname}" if cname else None
    extra_info = ""
    
    cat = "other"
    cat_label = "기타 자산"
    badge_color = "gray"
    sched = ""
    
    if name.startswith("cpa-"):
        cat = "cpa"
        cat_label = "📈 CPA 제휴 블로그"
        badge_color = "blue"
        m = (idx * 3) % 60
        sched = f"07:{m:02d} / 13:{m:02d} / 20:{m:02d} (3-Pass)"
        camp_json = get_raw_file(name, branch, "campaigns.json")
        if camp_json:
            try:
                c_data = json.loads(camp_json.encode('utf-8').decode('utf-8-sig'))
                c_item = c_data[0] if isinstance(c_data, list) else c_data
                extra_info = c_item.get("name", "")
            except: pass
        if not extra_info:
            extra_info = desc
        categories["cpa"].append({
            "name": name, "desc": extra_info, "domain": cname, "url": live_url,
            "pushed": pushed_at, "priv": is_private, "gh_url": f"https://github.com/{GITHUB_USER}/{name}"
        })

    elif "coupang" in name.lower():
        cat = "coupang"
        cat_label = "🛒 쿠팡 파트너스"
        badge_color = "emerald"
        sched = "FIFO 롱테일 자동 순환"
        categories["coupang"].append({
            "name": name, "desc": desc or "쿠팡 파트너스 고수익 가전/리빙 니치 블로그", "domain": cname, "url": live_url,
            "pushed": pushed_at, "priv": is_private, "gh_url": f"https://github.com/{GITHUB_USER}/{name}"
        })

    elif name.startswith("blog-") or name in ["economy-blog", "newspic-blog"]:
        cat = "expert"
        cat_label = "📰 전문 시사/뉴스"
        badge_color = "purple"
        sched = "07:xx / 13:xx / 20:xx (실시간 속보)"
        categories["expert"].append({
            "name": name, "desc": desc or "실시간 시사/뉴스 팩트 기반 전문 분석 블로그", "domain": cname, "url": live_url,
            "pushed": pushed_at, "priv": is_private, "gh_url": f"https://github.com/{GITHUB_USER}/{name}"
        })

    elif "threads" in name.lower():
        cat = "threads"
        cat_label = "🧵 Threads 봇"
        badge_color = "rose"
        sched = "Meta Graph API 연동"
        categories["threads"].append({
            "name": name, "desc": desc or "멀티 계정 Threads 공식 API 자동 포스팅 시스템", "domain": cname, "url": live_url,
            "pushed": pushed_at, "priv": is_private, "gh_url": f"https://github.com/{GITHUB_USER}/{name}"
        })

    elif "naver" in name.lower():
        cat = "naver"
        cat_label = "🟢 네이버 블로그"
        badge_color = "green"
        sched = "6-Pass 이미지 세탁"
        categories["naver"].append({
            "name": name, "desc": desc or "네이버 블로그 6-Pass 이미지 세탁 자동 포스팅 봇", "domain": cname, "url": live_url,
            "pushed": pushed_at, "priv": is_private, "gh_url": f"https://github.com/{GITHUB_USER}/{name}"
        })

    elif name in [
        "overtime_calc_site", "parental_calc_site", "unemployed_calc_site",
        "severance_calc_site", "pension_calc_site", "freelancer_tax_site",
        "smallbizcalc_site", "jeonse_renew_calc_site", "jeonse-deposit-calc",
        "stock-average-down-calc", "housing-score-calc", "calc-half-leave",
        "freelance-rate-calc", "insta-margin-calc"
    ]:
        cat = "util_finance"
        cat_label = "⚖️ 법정·금융 계산기"
        badge_color = "amber"
        sched = "구글 애드센스 탑재"
        categories["utility_legal_finance"].append({
            "name": name, "desc": desc, "domain": cname, "url": live_url,
            "pushed": pushed_at, "priv": is_private, "gh_url": f"https://github.com/{GITHUB_USER}/{name}"
        })

    elif name in [
        "wonderweeks_site", "pet_calc_site", "solar_calc_site", "aicostcalc_site",
        "sudokuportal", "fridge-dday-alarm", "dog-walk-weather", "protein-price-calc",
        "shorts-script-timer", "sns-font-converter", "resume-text-counter",
        "ott-party-calc", "color-coordinate-converter", "mbti-job-test",
        "mbti-for-senior", "stop-watch-game", "sudoku", "myip", "csv-to-single-column"
    ]:
        cat = "util_life"
        cat_label = "🍼 라이프·소셜 도구"
        badge_color = "teal"
        sched = "구글 애드센스 탑재"
        categories["utility_life_social"].append({
            "name": name, "desc": desc, "domain": cname, "url": live_url,
            "pushed": pushed_at, "priv": is_private, "gh_url": f"https://github.com/{GITHUB_USER}/{name}"
        })

    elif name in ["news-hub", "adpick-portal", "pages"]:
        cat = "portal"
        cat_label = "🌐 미디어 포털"
        badge_color = "indigo"
        categories["portal"].append({
            "name": name, "desc": desc or "통합 미디어 및 포털 서비스", "domain": cname, "url": live_url,
            "pushed": pushed_at, "priv": is_private, "gh_url": f"https://github.com/{GITHUB_USER}/{name}"
        })
    else:
        categories["other"].append({
            "name": name, "desc": desc, "domain": cname, "url": live_url,
            "pushed": pushed_at, "priv": is_private, "gh_url": f"https://github.com/{GITHUB_USER}/{name}"
        })

    sites_data.append({
        "name": name,
        "desc": extra_info or desc,
        "cat": cat,
        "cat_label": cat_label,
        "badge_color": badge_color,
        "domain": cname,
        "url": live_url,
        "gh_url": f"https://github.com/{GITHUB_USER}/{name}",
        "pushed": pushed_at,
        "priv": is_private,
        "sched": sched
    })

now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

total_sites = len(repos)
cpa_cnt = len(categories["cpa"])
coupang_cnt = len(categories["coupang"])
expert_cnt = len(categories["expert"])
threads_cnt = len(categories["threads"])
naver_cnt = len(categories["naver"])
util_cnt = len(categories["utility_legal_finance"]) + len(categories["utility_life_social"])
portal_cnt = len(categories["portal"])

# 1. Generate README.md
md = f"""# 🏢 Total System Master Control Dashboard

> **전사 디지털 자산 통합 관제 대시보드 (Total System Empire)**  
> **마지막 갱신 일시**: `{now_str} (KST)` | **총 관리 저장소**: **`{total_sites}개`**
>
> 🌐 **웹 대시보드 바로가기**: [https://somsoo.github.io/total-system-dashboard/](https://somsoo.github.io/total-system-dashboard/)

---

## 📊 종합 자산 현황 요약 (Portfolio Overview)

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│  🛒 쿠팡 파트너스 블로그 : {coupang_cnt:>2}개  │  📈 CPA 버티컬 블로그   : {cpa_cnt:>2}개             │
│  📰 전문 시사/뉴스 블로그: {expert_cnt:>2}개  │  🧮 애드센스 원페이지 웹앱: {util_cnt:>2}개             │
│  🧵 쓰레드 자동화 봇     : {threads_cnt:>2}개  │  🟢 네이버 블로그 봇    : {naver_cnt:>2}개             │
│  🌐 미디어 포털 & 인프라 : {portal_cnt:>2}개  │  💼 총 관리 프로젝트    : {total_sites:>2}개             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛒 1. 쿠팡 파트너스 수익형 니치 블로그 ({coupang_cnt} Sites)
| 저장소 (Repository) | 타겟 니치 & 주요 다룸 제품 | 라이브 도메인 (Live Domain) | 최근 업데이트 | 상태 |
| :--- | :--- | :--- | :---: | :---: |
"""

for s in categories["coupang"]:
    dom_link = f"[{s['domain']}]({s['url']})" if s['url'] else "`N/A`"
    md += f"| [{s['name']}]({s['gh_url']}) | {s['desc']} | {dom_link} | `{s['pushed']}` | ✅ 정상 가동 |\n"

md += f"""
---

## 📈 2. CPA 제휴 마케팅 블로그 ({cpa_cnt} Sites)
| 저장소 (Repository) | 전담 캠페인명 | 라이브 도메인 (Live Domain) | 발행 스케줄 (KST) | 최근 업데이트 |
| :--- | :--- | :--- | :---: | :---: |
"""

for idx, s in enumerate(categories["cpa"]):
    dom_link = f"[{s['domain']}]({s['url']})" if s['url'] else "`N/A`"
    m = (idx * 3) % 60
    sched = f"07:{m:02d} / 13:{m:02d} / 20:{m:02d}"
    md += f"| [{s['name']}]({s['gh_url']}) | {s['desc']} | {dom_link} | `{sched}` | `{s['pushed']}` |\n"

md += f"""
---

## 📰 3. 전문 시사/뉴스 블로그 ({expert_cnt} Sites)
| 저장소 (Repository) | 전문 취재 분야 및 소스 | 라이브 도메인 (Live Domain) | 발행 스케줄 (KST) | 최근 업데이트 |
| :--- | :--- | :--- | :---: | :---: |
"""

for idx, s in enumerate(categories["expert"]):
    dom_link = f"[{s['domain']}]({s['url']})" if s['url'] else "`N/A`"
    m = 45 + (idx * 2)
    sched = f"07:{m:02d} / 13:{m:02d} / 20:{m:02d}" if m < 60 else "07:59 / 13:59 / 20:59"
    md += f"| [{s['name']}]({s['gh_url']}) | {s['desc']} | {dom_link} | `{sched}` | `{s['pushed']}` |\n"

md += f"""
---

## 🧮 4. 애드센스 고단가 원페이지 유틸리티 웹앱 & 계산기 ({util_cnt} Sites)

### ⚖️ 법정·노무·세무 & 부동산·금융 계산기 ({len(categories['utility_legal_finance'])} Sites)
| 서비스명 (Repository) | 계산기 핵심 기능 및 용도 | 라이브 도메인 (Live Domain) | 상태 |
| :--- | :--- | :--- | :---: |
"""

for s in categories["utility_legal_finance"]:
    dom_link = f"[{s['domain']}]({s['url']})" if s['url'] else "`N/A`"
    md += f"| [{s['name']}]({s['gh_url']}) | {s['desc']} | {dom_link} | 🚀 배포 완료 |\n"

md += f"""
### 🍼 라이프·육아·소셜 & 엔터테인먼트 계산기 ({len(categories['utility_life_social'])} Sites)
| 서비스명 (Repository) | 계산기 핵심 기능 및 용도 | 라이브 도메인 (Live Domain) | 상태 |
| :--- | :--- | :--- | :---: |
"""

for s in categories["utility_life_social"]:
    dom_link = f"[{s['domain']}]({s['url']})" if s['url'] else "`N/A`"
    md += f"| [{s['name']}]({s['gh_url']}) | {s['desc']} | {dom_link} | 🚀 배포 완료 |\n"

md += f"""
---

## 🧵 5. SNS & 플랫폼 바이럴 자동화 시스템
| 시스템명 | 저장소 | 형태 | 주요 기능 및 연동 상태 |
| :--- | :--- | :---: | :--- |
| **Threads 멀티 계정 봇** | [`threads-auto`](https://github.com/{GITHUB_USER}/threads-auto) | Private | Meta 공식 Graph API 연동, 멀티 페르소나 자동 포스팅 & 웹 관제 UI |
| **네이버 블로그 자동화** | [`naverblog_auto`](https://github.com/{GITHUB_USER}/naverblog_auto) | Private | 네이버 블로그 6-Pass 이미지 세탁 및 자동 원고 생성 |

---

## 🌐 6. 미디어 포털 및 인프라 서비스
| 서비스명 | 저장소 | 라이브 도메인 | 상세 설명 |
| :--- | :--- | :--- | :--- |
"""

for s in categories["portal"]:
    dom_link = f"[{s['domain']}]({s['url']})" if s['url'] else "`N/A`"
    md += f"| **{s['name']}** | [{s['name']}]({s['gh_url']}) | {dom_link} | {s['desc']} |\n"

readme_path = os.path.join(os.path.dirname(__file__), "README.md")
with open(readme_path, "w", encoding="utf-8") as f:
    f.write(md)

# 2. Render index.html
html_path = os.path.join(os.path.dirname(__file__), "index.html")

# Read current index.html template and update SITES data
with open(html_path, "r", encoding="utf-8") as f:
    orig_html = f.read()

import re
new_html = re.sub(
    r'const SITES = \[[\s\S]*?\];',
    f'const SITES = {json.dumps(sites_data, ensure_ascii=False)};',
    orig_html
)
new_html = re.sub(r'갱신: [^<]+', f'갱신: {now_str}', new_html)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(new_html)

print("generate_dashboard.py: Updated README.md and index.html successfully.")
