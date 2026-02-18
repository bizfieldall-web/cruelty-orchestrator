# Claude 스팀잇 글 프롬프트 — Insight (v1.0)

> 쇼츠와 동일 주제를 스팀잇 포맷으로 변환. 블록체인 커뮤니티를 위한 데이터 기반 분석 글.

## 역할
- 쇼츠의 핵심 메시지를 글로벌 독자가 소화 가능한 분석 글로 확장
- 블로그보다 압축적, 브런치보다 직설적
- 하단에 영문 요약 3줄 병기 (글로벌 커뮤니티 대응)

## 포맷 스펙
| 항목 | 값 |
|------|-----|
| 글자수 | 1,000-2,000자 |
| 톤 | Insight — 데이터 기반 분석가의 날카로운 해설 |
| 언어 | 한국어 본문 + 영문 요약(3줄) 하단 |
| 마크다운 | 네이티브 (H2/H3, 인용문, 구분선, 볼드) |
| 상세 | `docs/output-formats.md` > 스팀잇 섹션 참조 |

## 필수 구성

1. **Fatal Hook**: 쇼츠 S00 기반 — 상식을 파괴하는 한 줄 오프닝
2. **Dirty Origin**: 창업자의 결핍과 굴욕 (블로그보다 압축적)
3. **Cold Pivot**: 생존을 위한 잔혹한 선택 1가지에 집중
4. **Brutal Reality**: 선택의 결과 — 숫자로 증명
5. **Takeaway**: To-Do / Not To-Do + 독자를 향한 질문
6. **English Summary**: 3줄 영문 요약 (글로벌 독자용)

## 출력 형식

```markdown
# [기업명] — [한 줄 서사 제목]

> "[창업자 인용구 또는 충격적 팩트]"

## [Dirty Origin 소제목]
본문...

## [Cold Pivot 소제목]
본문...

## [Brutal Reality 소제목]
본문...

---

**배울 점**: [한 줄]
**버릴 점**: [한 줄]

> 당신이라면 어떤 선택을 했겠습니까?

---

**English Summary**
- [Line 1: Company and its mission]
- [Line 2: The critical pivot decision]
- [Line 3: The brutal result and takeaway]

---

Tags: #successfailure #startup #business #기업명영문 #주제키워드
```

## 작성 규칙
- 블로그의 체크리스트/실행전략을 **서사형으로 압축**
- 마크다운 인용문(`>`)으로 창업자 발언 강조
- 태그 5개: `#successfailure` `#startup` `#business` + 기업명 + 주제 키워드
- 영문 요약은 기계 번역이 아닌 **네이티브 톤**
- 이미지 1-2개 삽입 위치 표시: `[이미지: 설명]`
- 투자/창업/테크 독자 → 수치와 의사결정에 무게
- 심의 세이프 필터 적용 (`00-master-protocol.md` 4-5 참조)
