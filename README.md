# SkyPort

공항 체크인 카운터를 CPU, 승객을 프로세스로 모델링한 비선점형 다중 프로세서 스케줄링 시뮬레이터입니다. 같은 입력에 대한 스케줄러별 평균 반환 시간(ATT)을 비교합니다.

## 기술 스택

Python 표준 라이브러리 · 정적 HTML

테스트에는 pytest, 논문 그림 생성에는 matplotlib을 사용합니다.

## 시작하기

### 사전 요구사항

- Python 3.10 이상

### 실행

별도 런타임 패키지 설치 없이 저장소 루트에서 실행합니다.

```bash
python3 main.py --input input.txt --scheduler hybrid
```

## 사용 방법

### 실행 옵션

```bash
python3 main.py --input input.txt --compare
python3 main.py --input input.txt --web out.html
python3 main.py --help
```

`--compare`는 스케줄러를 비교하고, `--web`으로 생성한 `out.html`은 브라우저에서 엽니다.
`--log`를 추가하면 도착·배정·완료 이벤트 로그를 출력합니다.

| `--scheduler` 값 | 방식 |
| --- | --- |
| `fcfs` | 도착 순서 |
| `priority` | 등급 우선순위 |
| `sjf` | 서비스 시간이 짧은 순 |
| `hybrid` | 등급별 큐·전용 카운터·work stealing·aging 조합 |

### 입력 파일

샘플은 [input.txt](input.txt)를 사용합니다. 도착 시각만 늘리고 줄여 부하를 바꾼 [input_light.txt](input_light.txt)·[input_heavy.txt](input_heavy.txt)로 부하별 결과를 비교할 수 있습니다. 열 순서와 허용값은 [입력 규약](https://github.com/OS-SkyPort/.github/blob/main/docs/spec.md#요구사항)을 참고합니다.

### 논문 빌드

matplotlib과 XeLaTeX가 설치된 환경에서 실행합니다.

```bash
python3 docs/generate_paper_figures.py
xelatex -output-directory=docs docs/HYBRID_MLQ_PAPER.tex
```

## 테스트

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install pytest
python -m pytest tests/
```

Windows PowerShell에서는 가상환경 활성화에 `.venv\Scripts\Activate.ps1`을 사용합니다.

## 관련 문서

| 문서 | 내용 |
| --- | --- |
| [spec.md](https://github.com/OS-SkyPort/.github/blob/main/docs/spec.md) | 입력·시뮬레이션 규칙·완료 기준 |
| [plan.md](https://github.com/OS-SkyPort/.github/blob/main/docs/plan.md) | 코드 구조·스케줄러 확장·평가 방법 |
| [tasks.md](https://github.com/OS-SkyPort/.github/blob/main/docs/tasks.md) | 진행 현황·부하별 ATT 기준선·aging 스윕 결과 |
| [논문 PDF](docs/HYBRID_MLQ_PAPER.pdf) | 설계 근거·평가·한계 |
| [논문 소스](docs/HYBRID_MLQ_PAPER.tex) | 논문 수정 및 재생성 원본 |
| [작업 지침](https://github.com/OS-SkyPort/.github/blob/main/docs/AGENTS.md) | 문서별 역할·변경 원칙 |
