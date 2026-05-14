# SkyPort 체크인 카운터 스케줄러

운영체제 텀 프로젝트로 구현한 **비선점형 다중 프로세서 체크인 카운터 스케줄링 시뮬레이터**입니다. 공항 체크인 카운터를 CPU에, 승객을 프로세스에 대응시켜 여러 스케줄링 정책을 시뮬레이션하고 평균 대기 시간(ATT)을 비교합니다.

## 디렉터리 구조

```
skyport/
├── core/         # 시뮬레이션 엔진, 데이터 모델
├── io/           # 입력 파서, 결과 리포터
├── schedulers/   # FCFS, Priority, SJF, HybridMLQ
├── gui/          # Tkinter GUI / HTML 웹 GUI
└── main.py       # CLI 진입점
tests/            # pytest 단위 테스트
input.txt         # 예제 입력
DESIGN_SPEC.md    # 설계 명세
```

## 실행 방법

### 헤드리스 실행 (기본: HybridMLQ)

```bash
python3 -m skyport.main --input input.txt --scheduler hybrid
```

### 모든 스케줄러 ATT 비교

```bash
python3 -m skyport.main --input input.txt --compare
```

### Tkinter GUI 실행

```bash
python3 -m skyport.main --input input.txt --gui
```

### 브라우저용 HTML GUI 생성

```bash
python3 -m skyport.main --input input.txt --scheduler hybrid --web skyport_gui.html
```

생성된 HTML은 스케줄러 선택, Play / Pause / Step / Reset, 시간 직접 입력(`Go`), 타임라인 슬라이더 탐색을 지원합니다.

### 이벤트 로그 출력

```bash
python3 -m skyport.main --input input.txt --scheduler hybrid --log
```

## 지원 스케줄러

| 키 | 이름 | 설명 |
| --- | --- | --- |
| `fcfs` | FCFS | 도착 순 처리 (baseline) |
| `priority` | Priority | 고정 클래스 우선순위 (baseline) |
| `sjf` | SJF | 비선점형 최단 작업 우선 (baseline) |
| `hybrid` | HybridMLQ | 클래스별 큐 + 우선순위 보호 + spill-over + HRRN |

## 입력 형식

두 가지 형식을 모두 지원합니다.

**CSV 형식**

```csv
passenger_id,arrival_time,class,service_time
P01,0,ECONOMY,7
```

**공백 구분 형식 (과제 제공 포맷)**

```text
1 0 3 7
2 0 1 12
```

열 순서는 `id`, `arrival_time`, `class`(1=FIRST, 2=BUSINESS, 3=ECONOMY), `service_time` 입니다.

## 테스트

```bash
python3 -m pytest tests/
```

## 참고 문서

- [DESIGN_SPEC.md](DESIGN_SPEC.md) — 설계 명세 및 HybridMLQ 알고리즘 상세
- `과제.pdf` — 원본 과제 명세
- `보고서.docx` — 최종 보고서
