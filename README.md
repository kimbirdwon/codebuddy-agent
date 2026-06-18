# CodeBuddy Agent

CodeBuddy PR comment test

Amazon Bedrock 기반 GitHub PR 자동 리뷰 에이전트 프로젝트입니다. `Bedrock05`~`Bedrock09` 노트북 흐름을 실제 제출용 레포 구조로 옮긴 스캐폴드이며, GitHub PR 이벤트를 받아 Bedrock Agent를 호출하고, Action Group을 통해 PR 조회, 댓글 등록, Slack 알림, 복잡도 분석, 테스트 코드 생성, 리팩토링 제안을 수행하도록 구성했습니다.

## 구조

```text
codebuddy-agent/
├── Bedrock/
├── cloudformation/
│   └── template.yaml
├── docs/
│   └── api-spec.yaml
├── lambda/
│   ├── orchestrator.py
│   ├── tools_executor.py
│   └── shared/
│       ├── __init__.py
│       ├── github_api.py
│       └── review.py
├── tests/
│   └── test_review.py
├── .gitignore
└── requirements.txt
```

## 흐름

1. GitHub Webhook 또는 수동 요청이 API Gateway로 들어옵니다.
2. `lambda/orchestrator.py`가 PR 정보를 정리해 Bedrock Agent에 전달합니다.
3. Agent는 필요할 때 Action Group을 호출합니다.
4. `lambda/tools_executor.py`가 GitHub/Slack/코드분석 작업을 실행합니다.
5. Agent가 최종 리뷰 결과를 반환하고, 필요하면 PR 댓글과 Slack 알림까지 남깁니다.

## Bedrock 노트북 매핑

- `Bedrock05.ipynb`: Agent 생성, KB 연결, Alias 생성
- `Bedrock06.ipynb`: GitHub PR 조회 Tool, Action Group 기본 구성
- `Bedrock07.ipynb`: PR 댓글, Slack Tool 통합
- `Bedrock08.ipynb`: 복잡도 분석, 테스트 생성, 리팩토링 제안
- `Bedrock09.ipynb`: API Gateway/Lambda 오케스트레이션

## 먼저 해야 할 설정

### 1. AWS 리소스 준비

- Bedrock Agent 생성
- Agent Alias 생성
- 필요 시 Knowledge Base 생성 및 연결
- GitHub PAT 또는 GitHub App 토큰 준비
- Slack Webhook URL 준비

### 2. Lambda 환경 변수

`orchestrator.py`

- `AGENT_ID`
- `AGENT_ALIAS_ID`
- `AWS_REGION`
- `AGENT_INSTRUCTION_PREFIX` 선택

`tools_executor.py`

- `GITHUB_TOKEN`
- `SLACK_WEBHOOK_URL`
- `TOOL_MODEL_ID` 선택
- `AWS_REGION`

## 배포 방향

### Agent

`Bedrock05.ipynb`를 참고해 아래 순서로 진행합니다.

1. Agent 생성 또는 기존 Agent 조회
2. Instruction 설정
3. Knowledge Base 연결
4. `prepare_agent`
5. Alias 생성 또는 갱신

### Action Group

`docs/api-spec.yaml`을 Agent Action Group 스키마로 업로드하고, 실행 Lambda로 `tools_executor.py`를 연결합니다.

### API 진입점

`cloudformation/template.yaml`은 오케스트레이터 Lambda와 API Gateway 뼈대를 제공합니다. 실제 배포 시에는 역할 ARN, Agent ID, Alias ID, GitHub Secret, Slack Secret 등을 파라미터로 주입하세요.

## 로컬 검증

의존성 설치:

```bash
pip install -r requirements.txt
```

테스트 실행:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## 제출 전략

최소 제출선은 아래 3개입니다.

1. PR URL 또는 GitHub Webhook 입력
2. Agent가 PR 분석 수행
3. PR 댓글 또는 JSON 리뷰 결과 생성

여유가 있으면 아래를 추가하세요.

- Slack 알림
- 복잡도 분석
- 테스트 코드 생성
- 리팩토링 제안
- CloudFormation 배포 자동화

## 주의할 점

- 노트북의 `userdata.get(...)`, `!pip install`, `%%bash` 셀은 그대로 Lambda에 넣으면 안 됩니다.
- Agent Tool 응답 포맷은 Bedrock Action Group 규격을 맞춰야 합니다.
- GitHub Webhook 시그니처 검증이 필요하면 `orchestrator.py`에 `X-Hub-Signature-256` 검증을 추가하세요.
- Lambda 패키징 시 `lambda/shared`도 함께 포함되어야 합니다.
