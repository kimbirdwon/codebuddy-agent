# CodeBuddy Agent

Amazon Bedrock 기반 GitHub Pull Request 자동 리뷰 프로젝트입니다.  
CloudFormation 템플릿 1회 실행으로 전체 리소스를 배포하는 원클릭 방식으로 구성했습니다.

## 1. 개요

CodeBuddy는 생성된 GitHub PR을 입력으로 받아 다음 작업을 수행합니다.

- PR 정보 조회
- 코드 리뷰 결과 생성
- 복잡도 분석
- 단위 테스트 초안 생성
- 리팩터링 제안
- GitHub PR 댓글 등록
- Slack 알림 전송

## 2. 구조

```text
codebuddy-agent/
├── README.md
├── cloudformation/
│   └── template.yaml
├── docs/
│   ├── api-spec.yaml
│   └── agent-instructions.md
├── lambda/
│   ├── orchestrator.py
│   ├── tools_executor.py
│   ├── tools/
│   │   ├── github_pr.py
│   │   ├── complexity.py
│   │   ├── testgen.py
│   │   └── refactor.py
│   └── shared/
│       ├── github_api.py
│       └── review.py
├── tests/
│   └── test_review.py
└── requirements.txt
```

## 3. 배포 방법

사전 준비:

- AWS CLI 설정
- GitHub Token
- Slack Webhook URL

배포 명령:

```powershell
aws cloudformation deploy `
  --template-file cloudformation/template.yaml `
  --stack-name CodeBuddyDemoStack `
  --parameter-overrides `
    GitHubToken=YOUR_GITHUB_TOKEN `
    SlackWebhookUrl=YOUR_SLACK_WEBHOOK_URL `
  --capabilities CAPABILITY_NAMED_IAM `
  --region ap-northeast-2
```

위 명령 1회 실행으로 Bedrock Agent, Lambda, API Gateway, IAM Role을 포함한 전체 리소스를 배포합니다.

배포 리소스:

- Bedrock Agent
- Bedrock Agent Alias
- Bedrock Action Group
- Tools Executor Lambda
- Orchestrator Lambda
- API Gateway
- IAM Role

출력값 확인:

```powershell
aws cloudformation describe-stacks `
  --stack-name CodeBuddyDemoStack `
  --region ap-northeast-2 `
  --query "Stacks[0].Outputs" `
  --output table
```

## 4. 사용 방법

PR 생성은 사용자가 직접 수행합니다.

배포 후 `ReviewApiUrl`로 PR 정보를 전달하면 자동 리뷰를 수행합니다.

요청 예시:

```json
{
  "repository": {
    "full_name": "kimbirdwon/codebuddy-agent"
  },
  "pull_request": {
    "number": 1,
    "title": "CodeBuddy test PR",
    "html_url": "https://github.com/kimbirdwon/codebuddy-agent/pull/1",
    "body": "PR for testing Bedrock Agent review",
    "user": {
      "login": "kimbirdwon"
    },
    "base": {
      "ref": "main"
    },
    "head": {
      "ref": "feature/codebuddy-test"
    }
  },
  "files": [
    {
      "filename": "README.md",
      "additions": 1,
      "deletions": 0
    }
  ]
}
```

## 5. API 문서

Review API:

- Method: `POST`
- Path: `/review`
- Content-Type: `application/json`

Action Group API:

- `get_pull_request`
- `list_repositories`
- `post_pr_comment`
- `send_slack_message`
- `analyze_complexity`
- `generate_unit_test`
- `suggest_refactor`

상세 스키마는 [docs/api-spec.yaml](C:/git_clone/codebuddy-agent/docs/api-spec.yaml)에 정의되어 있습니다.

## 6. 테스트

```powershell
python -m unittest discover -s tests -p "test_*.py"
```
