# 매뉴얼 — 「빠알리 용어집 근거자료」 사이트를 AI로 그대로 다시 만드는 방법

이 문서는 사람이 읽어도 되고, **AI(Claude, ChatGPT 등)에게 이 저장소와 함께 건네주는 작업 지시서**로도 쓸 수 있게 썼습니다.
AI에게 맡길 때는 「4. AI에게 맡기는 방법」의 지시문을 그대로 붙여 넣으면 됩니다.

- 지금 운영 중인 사이트: https://claude.ai/artifact/W2ahQ8R1NJsYRGYqPXU2UN (Claude 아티팩트, 공개)
- 이 저장소는 그 사이트의 **화면 파일과 자료 전부**, 그리고 자료를 다시 만드는 **도구**를 담고 있습니다.
- 라이선스: [LICENSE.md](LICENSE.md)

---

## 1. 저장소에 든 것

```
index.html            사이트 전체(화면·디자인·검색 프로그램이 한 파일에 들어 있음)
data/
  concepts-index.json 개념정의 목록(표제어·출판사 번역어·다른 표기·조각 번호·일러두기)
  concepts-0..N.json  개념정의 본문(마크다운). 약 3MB씩 나뉨
  build-info.json     개념정의를 만든 원본 파일 목록·표제어 수·만든 날짜
  vri/                6차 결집본(VRI) 빠알리 원문 — 성전·주석서·복주석서·añña
  abd/                미얀마어 삼장사전(Tipiṭaka Pāḷi-Myanmar Abhidhān)
  nsy/                닛사야 텍스트(OCR본, 위치 찾기용)
tools/
  build_concepts.py   개념정의 워드 파일(.docx) → data/concepts-*.json
  vri_parse.py        VRI XML → 문단 자료
  abd_parse.py        삼장사전 DB → 문단 자료
  nsy_parse.py        닛사야 DB → 문단 자료
  my2roman.py         미얀마 글자로 쓴 빠알리 → 로마자
  mkshards.py         문단 자료 → 검색용 조각 파일(data/vri 등)
MANUAL.md             이 문서
LICENSE.md            라이선스 정리
.nojekyll             GitHub Pages가 파일을 그대로 내보내게 하는 빈 파일
```

## 2. 사이트가 동작하는 방식

### 2-1. 한 파일짜리 화면
- `index.html` 하나에 HTML·CSS·JavaScript가 모두 들어 있습니다. 따로 빌드할 것이 없습니다.
- 근거자료 목록·닛사야 목록·저자별 목록·일러두기 같은 작은 자료는 `index.html` 안에 JSON으로 들어 있습니다(변수 `D`).
- 큰 자료는 `data/`에서 필요할 때 `fetch`로 불러옵니다. 그래서 **index.html과 data 폴더가 같은 곳에 있어야** 합니다.

### 2-2. 탭
| 탭 | 하는 일 |
|---|---|
| 개념정의 (#concepts) | 표제어를 빠알리 자모순으로 보이고, 표제어·출판사 번역어·본문으로 검색. 본문 안 표제어 링크, 다른 판본 표기 표시 |
| 원문 검색 (#corpus) | VRI 원문·삼장사전·닛사야에서 낱말 앞부분 일치 검색. 결과마다 전체 보기·출처 복사·AI로 번역하기 |
| AI에게 묻기 (#ask) | ① Claude에게 바로 묻기 ② 다른 AI용 자료 찾기·복사 ③ 자료 파일 내려받기. 질문 기록, 답 복사(질문과 답 / 답만) |
| 근거자료 · 닛사야 목록 · 저자별 · 일러두기 | 자료 설명, 인용 원칙, 라이선스 |

### 2-3. 자료 파일 형식
- **개념정의**
  - `concepts-index.json` = `{updated, n, chunks, intro:[{title,md}], sources:[{title,n}], terms:[{t, tr, c, av?, ag?}]}`
    - `t` 표제어, `tr` 출판사 번역어 줄, `c` 본문이 든 조각 번호, `av` 다른 판본 표기, `ag` 문헌 철자로 보이는 형태(추정)
  - `concepts-N.json` = `[[순번, 본문 마크다운], ...]`
- **원문 검색 자료**(vri·abd·nsy 공통) — `tools/mkshards.py`가 만듭니다.
  - `NAME-sK.txt`: 문단 묶음(JSON 배열)을 **gzip으로 압축한 뒤 base64 글자로 바꾼 것**. (아티팩트 저장소가 .gz 파일을 받지 않아 글자로 바꿨습니다.)
  - `NAME-i-N.txt`: 낱말 → 그 낱말이 든 조각 번호 목록(같은 방식으로 압축).
  - `NAME-meta.json`: `pmap`(낱말 앞 두 글자 → 색인 파일 번호), 조각 수 등.
  - 브라우저는 `atob` → `DecompressionStream('gzip')`으로 풉니다.
  - 문단 모양: VRI `[책번호, M쪽, V쪽, §, 소제목, 본문]`, 삼장사전 `[표제어, 로마자, 본문, 출처]`, 닛사야 `[이름표, 책, 문단, 본문, 로마자]`.
- **검색 정규화(fold)**: 유니코드 NFD → 구별부호 제거 → NFC → 소문자. 그래서 ā와 a, ṃ과 m이 같게 검색됩니다.
  - 판본 차이도 함께 찾습니다: 띄어쓰기·하이픈 무시, 겹자음 = 홑자음(kk=k), vy = by.

### 2-4. Claude 기능과, 그것이 없을 때
사이트는 Claude 아티팩트의 기능을 `window.claude.use(...)`로 불러 씁니다. **이 기능은 claude.ai 안에서만 있습니다.**

| 기능 | 쓰는 곳 | claude.ai 밖(예: GitHub Pages)에서는 |
|---|---|---|
| `sample` | Claude에게 바로 묻기, AI로 번역하기 | 버튼이 숨겨지고, 다른 AI에 붙여 넣을 글을 복사하는 방식으로 바뀜 |
| `db` + `user` | 내 질문 기록(계정별 `data/users/<uid>`) | 브라우저 localStorage에 저장 |
| `downloads` | 자료 파일 내려받기 | "이 화면에서는 내려받을 수 없습니다" 안내 |

이 기능들이 없을 때도 사이트가 멈추지 않도록 이미 만들어져 있습니다. 개념정의·원문 검색·자료 복사는 어디서나 됩니다.

## 3. 그대로 띄우는 방법

### 3-1. GitHub Pages (무료, 공개 주소)
1. 저장소 → **Settings** → **Pages**
2. Source: **Deploy from a branch**, Branch: **main**, 폴더: **/(root)** → Save
3. 몇 분 뒤 `https://<계정>.github.io/<저장소>/`에서 열립니다.
4. 자기 도메인(예: `glossary.dhammadana.kr`)을 쓰려면 같은 화면의 **Custom domain**에 주소를 넣고, 도메인 관리처에서 CNAME 레코드를 `<계정>.github.io`로 걸어 줍니다.

### 3-2. 내 컴퓨터에서
```
python3 -m http.server 8000
```
를 저장소 폴더에서 실행하고 브라우저로 `http://localhost:8000` 을 엽니다. (`index.html`을 더블클릭해 열면 브라우저 보안 규칙 때문에 data를 못 불러옵니다.)

### 3-3. Claude 아티팩트로(지금 운영 방식)
- Claude에게 "이 저장소의 index.html과 data 폴더 전체를 아티팩트로 올려 줘"라고 하면 됩니다.
- 기존 사이트를 고칠 때는 artifact slug `eb1187f8-6aee-462f-8c47-b935dd3be5af`에 `publish_files`(mode `patch`)로 올립니다. 공개 사이트라서 `shared_live: "public"`, `artifact_title: "빠알리 용어집 근거자료"`가 필요합니다.
- Claude 기능(묻기·질문 기록·내려받기)은 이 방식에서만 모두 동작합니다.

## 4. AI에게 맡기는 방법

아래 지시문을 AI에게 저장소 주소와 함께 주면 됩니다.

> 이 GitHub 저장소(https://github.com/…)는 「빠알리 용어집 근거자료」 검색 사이트의 원본이다. 먼저 MANUAL.md와 LICENSE.md를 끝까지 읽어라.
> 1. `index.html`과 `data/` 폴더를 고치지 말고 그대로 써서 사이트를 띄워라(MANUAL.md 3장).
> 2. 동작을 확인해라: 개념정의 탭에서 `sati` 검색, 원문 검색 탭에서 `satipaṭṭhāna` 검색, 일러두기 탭의 라이선스 문장.
> 3. 고칠 것이 있으면 `index.html`만 고치고, 자료는 `tools/`의 스크립트로 다시 만든다. 손으로 data 파일을 고치지 않는다.
> 4. 어떤 경우에도 근거 없는 말을 지어내지 말고, 확인하지 못한 것은 확인하지 못했다고 밝혀라.

AI에게 **새로 짜게** 하고 싶을 때(같은 기능, 다른 코드)는 2장 전체를 사양서로 주고, "data 폴더 형식은 그대로 두고 화면만 새로 만들어라"라고 하면 자료를 그대로 다시 쓸 수 있습니다.

## 5. 자료를 다시 만드는 방법

필요한 것: Python 3, `pandoc`(개념정의 변환용), `unzip`.

### 5-1. 개념정의
1. 원본: Google Drive 「새번역 빠알리 용어집」 폴더의 `빠알리_용어_개념정의_*.docx` (번역어 검증·평가 파일은 넣지 않음).
2. 파일을 내려받고 `manifest.json`을 만듭니다.
   ```json
   [{"path":"/내려받은/빠알리_용어_개념정의_195어.docx","id":"드라이브 파일 id","name":"빠알리_용어_개념정의_195어.docx","modifiedTime":"2026-11-18T08:19:57Z"}]
   ```
3. `python3 tools/build_concepts.py data manifest.json`
4. 결과: `data/concepts-index.json`, `data/concepts-*.json`, `data/build-info.json`.

규칙(스크립트 안에 들어 있음):
- 같은 표제어가 여러 파일에 있으면 표제어가 가장 많은 파일(통합본)의 내용을 씁니다.
- `FIX`: 분명한 표제어 철자 오류를 문헌 철자로 바꾸고, 같은 철자가 되면 합칩니다. 출판사 번역어도 합칩니다.
- `EXCLUDE`: 사이트에서 빼는 표제어.
- `ALTV`: 다른 판본 표기. `ALTG`: 문헌 철자로 보이는 형태(추정).
- `SAME`: 같은 낱말의 다른 표제어 짝.
- `TRANSLIT`: 한글 음역 교정(출판사 번역어 줄은 고치지 않음).
- 큰 워드 파일(document.xml 30MB 넘음)은 표제어 경계에서 나눠 변환합니다.

### 5-2. 원문 검색 자료
| 자료 | 원본 | 순서 |
|---|---|---|
| VRI 원문 | GitHub `VipassanaTech/tipitaka-xml` 의 `romn` | `vri_parse.py` → `mkshards.py vri vri_units.jsonl data/vri` |
| 삼장사전 | `tipi_mm_abhidhan.db`, `pndaza/tipitaka_abidan` 색인 | `abd_parse.py` → `mkshards.py abd abd_units.jsonl data/abd` |
| 닛사야 | `epitaka_my_nissaya.db` | `nsy_parse.py` → `mkshards.py nsy nsy_units.jsonl data/nsy` |

- 스크립트 안의 파일 경로(`/home/claude/...`)는 처음 만든 작업 환경의 경로입니다. 내 환경에 맞게 바꿔서 실행합니다.
- `vri-books.json`, `vri-ranges.json`, `abd-vols.json`은 보조 목록입니다. 원문을 새로 만들지 않으면 그대로 둡니다.

## 6. 자동 업데이트와 이 저장소

- 매일 새벽 3시 41분(한국 시간)에 Claude 예약 작업이 Drive 폴더의 개념정의 파일을 확인합니다. 바뀐 것이 있으면 `data/concepts-*` 를 다시 만들어 사이트에 올리고, **같은 파일을 이 저장소에도 올립니다(commit·push)**.
- 사이트 화면(`index.html`)을 고칠 때도 같은 내용을 이 저장소에 올립니다.
- 그래서 이 저장소가 늘 사이트와 같은 상태를 유지합니다. 어긋났다면 사이트 쪽이 최신일 수 있으니, 사이트의 파일 목록(sha256)과 비교해 맞춥니다.

## 7. 다른 언어로 만드는 방법

### 7-1. 화면을 다른 언어(영어·미얀마어·태국어 등)로
지금 화면 글자는 한국어로 `index.html` 안에 직접 적혀 있습니다. 다른 언어판을 만드는 순서는 다음과 같습니다.

1. **화면 글자 모으기**: `index.html`에서 한국어 글자(버튼, 안내문, 탭 이름, 오류 문구, 일러두기)를 찾아 낱말표로 뽑습니다.
   - 예: `const T={ko:{tabConcepts:'개념정의',...}, en:{tabConcepts:'Concepts',...}}`
   - 화면에서는 `T[lang].tabConcepts`처럼 불러 씁니다.
   - 언어는 주소(`?lang=en`)나 화면 위 선택 상자로 고르게 합니다.
2. **한국어에 맞춘 부분 고치기**
   - `KSTEM`(조사 떼기: 은·는·이·가…)과 `QSTOP`(질문어 빼기: 의미·차이·설명…)은 한국어 전용입니다. 다른 언어에서는 그 언어의 불용어 목록으로 바꾸거나 끕니다.
   - `toLocaleString('ko-KR')`(질문 기록 날짜)를 고른 언어로 바꿉니다.
   - Claude에게 주는 지시문 `RULES`와 번역 요청문은 한국어로 "한국어로 답하라"고 되어 있습니다. 답할 언어를 고른 언어로 바꿉니다.
3. **글꼴**: 지금 Noto Sans·Noto Sans KR·Noto Sans Myanmar를 불러옵니다. 태국 문자는 Noto Sans Thai, 싱할라 문자는 Noto Sans Sinhala를 더합니다. 빠알리 구별부호(ṭ ḍ ṇ ṅ ṃ ḷ)가 보이는 글꼴을 맨 앞에 둡니다.
4. **자료(내용)의 언어**
   - 빠알리 원문·삼장사전·닛사야는 언어와 상관없이 그대로 씁니다.
   - **개념정의 본문은 한국어**입니다. 다른 언어판에서 개념정의를 보이려면 개념정의 문서를 그 언어로 번역한 .docx를 만들고, 같은 형식(표제어 = `### 제목`, `**출판사 번역어** — …` 줄)을 지켜 `build_concepts.py`로 `data/<언어>/concepts-*` 를 따로 만듭니다. 화면은 고른 언어의 폴더를 불러오게 합니다.
   - 출판사 번역어는 한국 출판사의 번역어이므로 번역하지 않고 그대로 둡니다(필요하면 "Korean publishers' renderings"라고 설명만 붙임).
   - 번역은 지침대로 근거를 바꾸지 않고, 인용(서명·쪽·§)은 그대로 둡니다.
5. **빠알리를 다른 문자로 보이기**(선택): 미얀마 글자 → 로마자는 `my2roman.py`와 화면의 `my2rom`이 있습니다. 태국·싱할라·데바나가리 문자 화면이 필요하면 로마자 → 해당 문자 변환 함수를 더하고, 검색은 지금처럼 로마자로 맞춰 비교합니다.

### 7-2. 다른 프로그래밍 방식으로
- 자료가 모두 평범한 JSON과 gzip이라 어떤 언어로도 읽을 수 있습니다(Python, Node.js, Go, Swift, Kotlin 등).
- **앱(안드로이드·iOS)**: `data/`를 앱에 넣거나 GitHub Pages 주소에서 내려받고, 2-3의 형식대로 풀어서 검색합니다. 검색 규칙(fold, 판본 차이)은 2-3을 그대로 옮깁니다.
- **서버를 두는 방식**: 서버에서 조각을 미리 풀어 SQLite FTS 같은 검색 색인을 만들면 더 빠르게 찾을 수 있습니다.
- **Claude에게 묻기 기능**은 claude.ai 밖에서는 `window.claude`가 없으므로, 따로 AI API(예: Anthropic API)를 연결해야 합니다. 이때 사용 요금은 사이트 운영자에게 청구되고, API 키를 브라우저에 그대로 두면 안 되므로 서버를 거쳐야 합니다.

## 8. 고칠 때 지켜야 할 원칙
- 거짓을 쓰지 않고, 근거 없는 말을 지어내지 않습니다. 확인하지 못한 판단은 "(추정)"으로 밝힙니다.
- 출판사 번역어는 출판사 표기 그대로 둡니다(입력 흔적 정리·번호 빼기만 예외).
- 닛사야를 인용할 때는 항상 저자를 밝힙니다.
- 번역어 검증·평가 자료는 사이트에 넣지 않습니다.
- 라이선스 문구: "개념정의 파일 등 이 프로젝트에서 새롭게 기여한 내용은 모두 CC BY-NC-SA 4.0 라이선스에 따라 제공됩니다. 원문 텍스트의 권리는 해당 저자와 출판사의 소유이며 각각의 라이선스에 따릅니다."

## 9. 알려진 한계
- 닛사야 텍스트는 OCR본이라 글자 오류가 있습니다(위치 찾기용). 인용은 스캔본에서 확인해야 합니다.
- 연음으로 철자가 크게 달라진 낱말(pañca upādāna- ↔ pañcupādāna-)은 판본 차이 검색 규칙으로 잡히지 않습니다.
- 개념정의 파일에 새 표제어가 생기면 새 철자 오류는 자동으로 고쳐지지 않습니다. 검토해서 `FIX`에 더해야 합니다.
