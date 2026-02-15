# 파이프라인 스펙 - 에이전트별 역할 및 지침

## 전체 흐름도

```
주제 선정 → 발굴/탐색 → 검증 → 가공 → 풍성화 → 대본 → 이미지/영상
  [Gemini]   [Gemini]   [Perplexity] [NotebookLM] [GPT]  [Claude] [GenSpark/Vrew]
```

---

## [1단계] Gemini - 마스터 (조율/발굴/탐색)

### 역할
- 전체 파이프라인의 **기획자 및 조율자**
- 주제 발굴, 트렌드 탐색, 카테고리 선정
- 다른 에이전트에 전달할 핵심 키워드와 방향 설정

### 입력
- 카테고리/도메인 지정 (예: AI, 테크, 비즈니스)
- 이전 콘텐츠 히스토리 (중복 방지)

### 출력
- 오늘의 주제 1건
- 핵심 키워드 3-5개
- 탐색 방향 (어떤 각도로 볼 것인지)
- 타겟 오디언스 힌트

### 지침 위치
- `prompts/gemini/01-master.md` — 마스터 조율 프롬프트
- `prompts/gemini/02-discovery.md` — 주제 발굴 프롬프트
- `prompts/gemini/03-exploration.md` — 심화 탐색 프롬프트

---

## [2단계] Perplexity - 팩트 검증

### 역할
- Gemini가 탐색한 내용의 **사실 확인 및 검증**
- 출처/근거 확보
- 최신성 검증 (날짜, 수치 등)

### 입력
- Gemini의 탐색 결과 (주제 + 키워드 + 초기 자료)

### 출력
- 검증된 팩트 리스트
- 출처 URL 및 신뢰도
- 수정이 필요한 부분 플래그

### 지침 위치
- `prompts/perplexity/01-verification.md`

---

## [3단계] NotebookLM - 데이터 가공/구조화

### 역할
- 검증된 데이터를 **구조화된 형태로 가공**
- 핵심 포인트 추출, 논리 흐름 정리
- 콘텐츠 뼈대(outline) 생성

### 입력
- Perplexity 검증 결과
- Gemini 탐색 자료

### 출력
- 구조화된 데이터 (JSON 또는 마크다운)
- 핵심 논점 3-5개
- 콘텐츠 아웃라인

### 지침 위치
- `prompts/notebooklm/01-processing.md`

---

## [4단계] GPT - 데이터 풍성화 (Enrichment)

### 역할
- 가공된 데이터에 **맥락, 사례, 비유 추가**
- 데이터를 '이야기'로 변환할 수 있는 소재 확보
- 수치/통계에 의미 부여

### 입력
- NotebookLM 가공 결과
- Gemini 탐색 데이터
- Perplexity 검증 데이터

### 출력
- 풍성화된 데이터셋
- 활용 가능한 사례/비유 리스트
- 핵심 메시지 후보 2-3개

### 지침 위치
- `prompts/gpt/01-enrichment.md`

---

## [5단계] Claude - 대본 작성

### 역할
- 풍성화된 데이터를 **4가지 포맷의 최종 콘텐츠로 변환**
- 쇼츠 대본 (매일)
- 블로그 글 (매일)
- 브런치 글 (매일)
- 롱폼 분석 (주간)

### 입력
- GPT 풍성화 결과
- 포맷별 스펙 (`docs/output-formats.md`)

### 출력
- 포맷별 완성 원고 (상세 스펙은 `docs/output-formats.md` 참조)

### 지침 위치
- `prompts/claude/01-shorts-script.md` — 쇼츠 대본
- `prompts/claude/02-blog.md` — 블로그
- `prompts/claude/03-brunch.md` — 브런치
- `prompts/claude/04-longform.md` — 주간 롱폼

---

## [6단계] Gemini - 나노바나나 프롬프트 생성

### 역할
- 완성된 대본에서 **이미지 생성용 프롬프트 추출**
- 나노바나나(이미지 생성 도구) 최적화

### 입력
- Claude가 작성한 대본

### 출력
- 장면별 이미지 프롬프트
- 스타일 지시어

### 지침 위치
- `prompts/gemini/04-nanobanana.md`

---

## [7단계] GenSpark - 이미지 생성

### 역할
- 프롬프트 기반 **이미지 생성**

### 입력
- Gemini의 나노바나나 프롬프트

### 출력
- 장면별 이미지 파일

### 지침 위치
- `prompts/genspark/01-image-gen.md`

---

## [8단계] Vrew(브루) - 영상 편집/생성

### 역할
- 대본 + 이미지를 조합하여 **최종 영상 생성**

### 입력
- Claude 대본
- GenSpark 이미지

### 출력
- 완성된 쇼츠 영상
- (롱폼의 경우) 긴 영상

### 지침 위치
- `prompts/vrew/01-video-edit.md`
