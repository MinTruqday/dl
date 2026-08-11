# Agentic AI — kiến trúc và workflow hiện hành

> Nguồn sự thật của tài liệu này là mã nguồn trong `backend/agentic_ai`, cấu hình
> `docker-compose.yml` và các API nội bộ đang được gọi. Tài liệu mô tả thành phần
> đã triển khai; không xem một container hạ tầng tồn tại trong Compose là bằng
> chứng rằng Agentic AI trực tiếp sử dụng container đó.

## 1. Phạm vi dịch vụ

Agentic AI là lớp điều phối AI của DocLib. Dịch vụ chịu trách nhiệm:

- hội thoại đồng bộ và phát trực tiếp bằng SSE;
- phân luồng Chat, Plan, Learn, Work và Goal;
- RAG, tìm kiếm web, đọc tệp và xử lý đa phương thức;
- lập kế hoạch và thực thi DAG đa agent;
- công cụ nội bộ, MCP, sandbox và cơ chế phê duyệt;
- lịch sử, bộ nhớ người dùng và workspace của phiên;
- giới hạn gói, thống kê token, bảo vệ đầu vào/đầu ra;
- sự kiện chủ động, quan sát vận hành và vòng cải tiến có phê duyệt;
- tạo dữ liệu, QLoRA/LoRA, đánh giá và triển khai model tinh chỉnh;
- đánh giá chính sách DRM rủi ro cao cho dịch vụ DRM.

Điểm vào chính: [`backend/agentic_ai/src/main.py`](backend/agentic_ai/src/main.py).

## 2. Kiến trúc tổng thể

Sơ đồ này chỉ mô tả thành phần và quan hệ phụ thuộc, **không phải workflow nghiệp
vụ**. Vì vậy node dùng tên module/dịch vụ; các phần từ mục 3 trở đi mới dùng
quy ước bước xử lý và nút quyết định.

```mermaid
flowchart LR
    Client[Frontend hoặc dịch vụ nội bộ] -->|JWT hoặc X-Internal-Token| API[FastAPI Agentic AI]

    subgraph Entry[Biên API]
        API --> Auth[Xác thực và phân quyền]
        Auth --> Quota[Kiểm tra gói và hạn mức]
        Quota --> GuardIn[Guardrails đầu vào]
    end

    subgraph Core[Điều phối]
        GuardIn --> Router{Chọn mode và route}
        Router --> Direct[Chat trực tiếp]
        Router --> Plan[Plan khô]
        Router --> Knowledge[Đồ thị Knowledge RAG]
        Router --> Supervisor[Đồ thị Supervisor Work và Goal]
        Supervisor --> Tools[Tool registry, MCP, sandbox]
    end

    subgraph Model[Model runtime]
        Direct --> LLM[Model chính]
        Plan --> LLM
        Knowledge --> LLM
        Supervisor --> LLM
        LLM --> Ollama[Ollama]
        LLM --> OpenAICompat[API tương thích OpenAI]
    end

    subgraph State[Dữ liệu và trạng thái]
        Mongo[(MongoDB)]
        Redis[(Redis)]
        Qdrant[(Qdrant)]
        MinIO[(MinIO)]
        MQ[(RabbitMQ)]
    end

    subgraph Services[Dịch vụ DocLib và bên ngoài]
        RagSvc[RAG service]
        Content[Content service]
        Usage[Usage service]
        DRM[DRM service]
        WS[WebSocket service]
        Web[Tavily và MCP server]
        Neo4j[(Neo4j qua RAG service)]
    end

    Supervisor --> Mongo
    Auth --> Redis
    Knowledge --> RagSvc
    RagSvc --> Qdrant
    RagSvc --> Neo4j
    API -. readiness .-> MinIO
    API -. readiness .-> MQ
    Quota --> Usage
    Router --> Content
    Tools --> DRM
    Tools --> Web
    API --> WS
```

### Ranh giới quan trọng

- Agentic AI gọi RAG service để tiếp nạp, truy xuất và cập nhật graph; việc ghi
  Qdrant/Neo4j nằm sau ranh giới RAG service.
- `PRIMARY_MODEL_STYLE` quyết định runtime model là Ollama hoặc API tương thích
  OpenAI. Không có fallback model âm thầm: model đã cấu hình lỗi thì request lỗi.
- MinIO và RabbitMQ là dependency readiness/runtime; không nên vẽ chúng như một
  bước bắt buộc trong mọi cuộc trò chuyện.
- DRM service gọi ngược Agentic AI ở nhánh đánh giá policy; Agentic AI cũng có
  tool gọi các API bảo vệ nội bộ của DRM.
- Định dạng tài liệu được giữ xuyên suốt: `doclib` là EditorJS JSON, `doclibx` là
  LaTeX. Khi DRM mã hóa, file xuất vẫn lần lượt mang đuôi `.doclib` hoặc
  `.doclibx`; Agentic AI không tự đổi loại tài liệu.

## 3. Workflow chung của một lượt hội thoại

Hai endpoint `/tro-chuyen` và `/tro-chuyen/phat-truc-tiep` dùng cùng logic nghiệp
vụ; endpoint thứ hai phát sự kiện SSE (`start`, `model`, `plan`, `message`,
`tool`, `error`, `done`).

```mermaid
flowchart TD
    Start([Bắt đầu người dùng gửi tin nhắn]) --> ReadIdentity[Đọc tài khoản vai trò và gói sử dụng]
    ReadIdentity --> AllowedMode{Gói hiện tại có được dùng chế độ đã chọn}
    AllowedMode -->|Không| TierError([Kết thúc thông báo chế độ không thuộc gói hiện tại])
    AllowedMode -->|Có| HasUpload{Yêu cầu có tệp hoặc thư mục đính kèm}
    HasUpload -->|Có| ReserveUpload[Giữ trước dung lượng tải lên]
    ReserveUpload --> UploadAllowed{Dung lượng còn đủ}
    UploadAllowed -->|Không| QuotaError([Kết thúc thông báo đã hết hạn mức])
    UploadAllowed -->|Có| ValidateMedia[Kiểm tra loại tệp ảnh và âm thanh]
    HasUpload -->|Không| ScanInput[Kiểm tra lệnh đánh lừa AI thông tin cá nhân và dữ liệu bí mật]
    ValidateMedia --> ScanInput
    ScanInput --> SafeInput{Đầu vào có an toàn}
    SafeInput -->|Không| SecurityError([Kết thúc thông báo nội dung không an toàn])
    SafeInput -->|Có| PrepareSession[Tạo hoặc cập nhật không gian làm việc]
    PrepareSession --> CheckAIQuota[Kiểm tra hạn mức sử dụng AI]
    CheckAIQuota --> HasAIQuota{Còn hạn mức hoặc là quản trị viên}
    HasAIQuota -->|Không| QuotaError
    HasAIQuota -->|Có| LoadContext[Nạp lịch sử tùy chọn cá nhân và tài liệu]
    LoadContext --> HasDocuments{Có tài liệu cần sử dụng}
    HasDocuments -->|Có| CheckAccess[Kiểm tra quyền đọc tài liệu]
    CheckAccess --> CanRead{Người dùng được đọc toàn bộ tài liệu}
    CanRead -->|Không| DocumentError([Kết thúc thông báo không có quyền đọc tài liệu])
    CanRead -->|Có| SelectFlow[Chọn quy trình trò chuyện lập kế hoạch tra cứu hoặc thực hiện công việc]
    HasDocuments -->|Không| SelectFlow
    SelectFlow --> RunFlow[Thực hiện quy trình đã chọn]
    RunFlow --> SanitizeOutput[Loại dữ liệu nhạy cảm khỏi câu trả lời]
    SanitizeOutput --> SaveResult[Lưu lịch sử bộ nhớ tiêu đề và dữ liệu vận hành]
    SaveResult --> RecordUsage[Ghi nhận lượng sử dụng và hạn mức đã dùng]
    RecordUsage --> End([Kết thúc trả câu trả lời cho người dùng])
```

## 4. Quy tắc chọn mode và route

```mermaid
flowchart TD
    Start([Bắt đầu đầu vào đã qua kiểm tra an toàn]) --> WhichMode{Người dùng chọn chế độ nào}
    WhichMode -->|Lập kế hoạch| MakePlan[Tạo và lưu kế hoạch nhưng chưa thực hiện]
    WhichMode -->|Công việc hoặc mục tiêu| RunSupervisor[Chuyển sang quy trình thực hiện công việc]
    WhichMode -->|Học từ tài liệu| RunKnowledge[Chuyển sang quy trình tra cứu kiến thức]
    WhichMode -->|Trò chuyện| HasAttachment{Có tài liệu tệp hoặc thư mục đính kèm}
    HasAttachment -->|Có| RunKnowledge
    HasAttachment -->|Không| UseWeb{Người dùng có bật tìm kiếm trên mạng}
    UseWeb -->|Không| RunDirect[Trả lời trực tiếp]
    UseWeb -->|Có| ClassifyIntent[Xác định nhu cầu của người dùng]
    ClassifyIntent --> BestFlow{Quy trình nào phù hợp nhất}
    BestFlow -->|Trò chuyện| RunDirect
    BestFlow -->|Tra cứu kiến thức| RunKnowledge
    BestFlow -->|Thực hiện công việc| RunSupervisor
    MakePlan --> End([Kết thúc trả kết quả của chế độ đã chọn])
    RunSupervisor --> End
    RunKnowledge --> End
    RunDirect --> End
```

- BASIC được dùng Chat và model chính nhưng không có audio; mode nâng cao hoặc
  `thinking` yêu cầu PRO/PREMIUM, ngoại trừ ADMIN.
- ADMIN dùng cùng khả năng với PREMIUM nhưng bỏ qua việc trừ hạn mức AI.
- `Plan` chỉ sinh và lưu kế hoạch. `Work`/`Goal` mới thực thi kế hoạch.

## 5. Workflow Knowledge RAG

Đây là topology thật trong
[`workflow/graph.py`](backend/agentic_ai/src/workflow/graph.py), không phải một
pipeline nạp dữ liệu.

```mermaid
flowchart TD
    Start([Bắt đầu nhận câu hỏi]) --> RewriteFromHistory[Làm rõ câu hỏi dựa trên nội dung trao đổi gần đây]
    RewriteFromHistory --> NeedKnowledge{Câu hỏi có cần tra cứu kiến thức}
    NeedKnowledge -->|Không| AnswerDirectly[Để AI trả lời trực tiếp]
    AnswerDirectly --> End([Kết thúc trả câu trả lời])
    NeedKnowledge -->|Có| DecodeAttachments[Giải mã nội dung tệp và thư mục đính kèm]
    DecodeAttachments --> RetrieveEvidence[Tìm thông tin liên quan trong kho kiến thức]
    RetrieveEvidence --> RerankEvidence[Sắp xếp kết quả theo mức liên quan]
    RerankEvidence --> SmartMode{Có bật kiểm tra nâng cao}
    SmartMode -->|Có| GradeEvidence[Chấm độ liên quan của từng bằng chứng]
    SmartMode -->|Không| HasEvidence{Đã có thông tin đủ để trả lời}
    GradeEvidence --> HasEvidence
    HasEvidence -->|Có| GenerateAnswer[Sinh câu trả lời kèm nguồn]
    HasEvidence -->|Không| WebAllowed{Người dùng có cho phép tìm trên mạng}
    WebAllowed -->|Có| SearchWeb[Tìm thêm nguồn trên mạng]
    SearchWeb --> GradeEvidence
    WebAllowed -->|Không| GenerateAnswer
    GenerateAnswer --> NeedVerification{Có bật kiểm chứng nâng cao}
    NeedVerification -->|Không| End
    NeedVerification -->|Có| VerifyAnswer[Đối chiếu câu trả lời với thông tin đã tìm được]
    VerifyAnswer --> Verified{Câu trả lời đạt yêu cầu}
    Verified -->|Có| End
    Verified -->|Không còn lượt thử| EndWithWarning([Kết thúc trả kết quả tốt nhất kèm cảnh báo])
    Verified -->|Không và còn lượt thử| ImproveQuery[Điều chỉnh cách tìm kiếm]
    ImproveQuery --> RetrieveEvidence
```

## 6. Workflow tiếp nạp tri thức

```mermaid
flowchart TD
    Start([Bắt đầu đưa tài liệu vào kho kiến thức]) --> Authenticate[Kiểm tra người dùng và vai trò]
    Authenticate --> SendToRAG[Chia tài liệu thành các phần nhỏ và lập danh mục tìm kiếm]
    SendToRAG --> Ingested{Tài liệu đã được đưa vào kho thành công}
    Ingested -->|Không| Fail([Kết thúc báo không thể tiếp nhận tài liệu])
    Ingested -->|Có| ReadGraphText[Đọc nội dung dùng để tạo mạng lưới kiến thức]
    ReadGraphText --> ExtractRelations[Trích xuất thực thể và quan hệ có cấu trúc]
    ExtractRelations --> ReplaceGraph[Cập nhật mạng lưới kiến thức của tài liệu]
    ReplaceGraph --> GraphSaved{Mạng lưới kiến thức được cập nhật thành công}
    GraphSaved -->|Có| End([Kết thúc trả số phần nội dung và số mối liên hệ])
    GraphSaved -->|Không| DeleteIndex[Xóa chỉ mục vừa tạo để tránh dữ liệu nửa chừng]
    DeleteIndex --> Fail
```

Xóa tài liệu bằng `DELETE /tiep-nap/tai-lieu/{document_id}` cũng được ủy quyền
cho RAG service. Agentic AI không trực tiếp đọc MinIO hoặc ghi Qdrant/Neo4j trong
endpoint này.

## 7. Workflow Work và Goal: Supervisor DAG

```mermaid
flowchart TD
    Start([Bắt đầu nhận công việc hoặc mục tiêu]) --> BuildDAG[Chia yêu cầu thành các bước theo đúng thứ tự phụ thuộc]
    BuildDAG --> ValidatePlan[Kiểm tra cấu trúc giới hạn và quy tắc an toàn]
    ValidatePlan --> ValidPlan{Kế hoạch có hợp lệ}
    ValidPlan -->|Không| PlanError([Kết thúc báo kế hoạch không hợp lệ])
    ValidPlan -->|Có| PickReadyTask[Chọn bước đã đủ điều kiện để thực hiện]
    PickReadyTask --> HasReadyTask{Có bước sẵn sàng thực hiện}
    HasReadyTask -->|Không| Deadlock([Kết thúc báo các bước đang phụ thuộc lẫn nhau hoặc thiếu điều kiện])
    HasReadyTask -->|Có| AssignExecutor[Chọn AI hoặc công cụ phù hợp với bước hiện tại]
    AssignExecutor --> ExecuteTask[Thực hiện bước trong giới hạn thời gian và an toàn]
    ExecuteTask --> TaskSucceeded{Bước hiện tại hoàn tất thành công}
    TaskSucceeded -->|Có| RecordTask[Ghi trạng thái hoàn tất và kết quả]
    TaskSucceeded -->|Không| CanRetry{Lỗi có thể thử lại hoặc điều chỉnh kế hoạch}
    CanRetry -->|Có| ReplanTask[Điều chỉnh bước trong giới hạn cho phép]
    ReplanTask --> PickReadyTask
    CanRetry -->|Không| RecordFailure[Ghi trạng thái thất bại và nguyên nhân]
    RecordFailure --> AllFinished{Tất cả bước đã kết thúc}
    RecordTask --> AllFinished
    AllFinished -->|Không| PickReadyTask
    AllFinished -->|Có| TrimResult[Rút gọn kết quả nếu quá dài]
    TrimResult --> SanitizeResult[Kiểm tra và làm sạch đầu ra]
    SanitizeResult --> AggregateResult[Tổng hợp kết quả cuối cùng]
    AggregateResult --> End([Kết thúc trả kết quả công việc hoặc mục tiêu])
```

Việc chọn bộ thực thi ở bước “Chọn agent hoặc công cụ” tuân theo bảng sau; đây
là ánh xạ thành phần, không phải các bước chạy nối tiếp nhau:

| Nhu cầu của task | Bộ thực thi |
|---|---|
| Diễn giải yêu cầu | Interpreter agent |
| Tìm kiếm | Engine agent |
| Thao tác hệ thống | Action tools |
| Nghiên cứu tri thức | Knowledge researcher |
| Lập luận | Reasoning agent hoặc MCTS |
| Mã nguồn, review, bảo mật | Coder, Reviewer hoặc SecOps |
| Chuyên môn động | Domain specialist |

Các chốt an toàn gồm timeout toàn phiên, giới hạn replan, phát hiện deadlock,
phát hiện lặp task, recursion limit, governance theo tool và cơ chế ngắt/phê
duyệt từ người dùng.

## 8. Workflow công cụ và MCP

```mermaid
flowchart TD
    Start([Bắt đầu AI yêu cầu dùng công cụ]) --> FindTool[Tìm công cụ trong danh sách được phép]
    FindTool --> Found{Tìm thấy công cụ}
    Found -->|Không| ToolError([Kết thúc báo công cụ không tồn tại])
    Found -->|Có| IsMCP{Đây có phải công cụ được kết nối từ bên ngoài}
    IsMCP -->|Có| LoadMCP[Đọc cấu hình kết nối của người dùng]
    LoadMCP --> ValidateMCP[Kiểm tra cách khởi chạy địa chỉ và quyền truy cập mạng]
    ValidateMCP --> ValidMCP{Cấu hình và kết nối có hợp lệ}
    ValidMCP -->|Không| MCPError([Kết thúc báo kết nối ngoài không khả dụng])
    ValidMCP -->|Có| DiscoverTools[Kết nối và đọc danh sách chức năng bên ngoài]
    DiscoverTools --> CheckGovernance[Kiểm tra dữ liệu đầu vào và quyền thực hiện]
    IsMCP -->|Không| CheckGovernance
    CheckGovernance --> NeedApproval{Thao tác có cần người dùng phê duyệt}
    NeedApproval -->|Có| AskApproval[Tạm dừng và gửi yêu cầu phê duyệt]
    AskApproval --> Approved{Người dùng chấp thuận}
    Approved -->|Không| Denied([Kết thúc không thực hiện công cụ])
    Approved -->|Có| ExecuteTool[Thực hiện công cụ trong thời gian cho phép]
    NeedApproval -->|Không| ExecuteTool
    ExecuteTool --> Successful{Công cụ chạy thành công}
    Successful -->|Không| ToolError
    Successful -->|Có| RecordTelemetry[Ghi dữ liệu vận hành và lượng sử dụng]
    RecordTelemetry --> End([Kết thúc trả kết quả cho AI])
```

MCP preset chỉ được hiển thị/kết nối sau khi server vượt qua kiểm tra cấu hình và
khả năng kết nối. Hai preset tích hợp sẵn là Reqwise Figma và Chrome DevTools.
Khi người dùng kết nối lại một preset đã tồn tại, backend luôn probe lại và thay
cấu hình cũ bằng command/args bất biến hiện hành trước khi đánh dấu kết nối.
Cấu hình được lưu theo người dùng trong MongoDB.

## 9. Workflow tinh chỉnh DocLib Metis

```mermaid
flowchart TD
    Start([Bắt đầu nhập mẫu huấn luyện]) --> BuildDataset[Tạo bộ dữ liệu từ mẫu thủ công phản hồi hoặc tài liệu]
    BuildDataset --> EnoughSamples{Bộ dữ liệu có ít nhất mười mẫu hợp lệ}
    EnoughSamples -->|Không| Reject([Kết thúc yêu cầu bổ sung dữ liệu])
    EnoughSamples -->|Có| CreateJob[Tạo công việc huấn luyện ở trạng thái chờ]
    CreateJob --> RunTraining[Khởi chạy quá trình huấn luyện có thể hủy]
    RunTraining --> WhichBase{Mô hình nền thuộc loại nào}
    WhichBase -->|Gemma 4| TrainQLoRA[Huấn luyện phần cần thiết cho mô hình đa phương thức]
    WhichBase -->|Mô hình được hỗ trợ khác| TrainLoRA[Huấn luyện bằng phương pháp phù hợp]
    TrainQLoRA --> TrainingOK{Huấn luyện thành công}
    TrainLoRA --> TrainingOK
    TrainingOK -->|Không hoặc bị hủy| Failed([Kết thúc lưu trạng thái lỗi hoặc đã hủy])
    TrainingOK -->|Có| SaveAdapter[Lưu phần mô hình đã huấn luyện]
    SaveAdapter --> MergeModel[Ghép kết quả huấn luyện vào mô hình nền]
    MergeModel --> ConvertGGUF[Chuyển mô hình sang định dạng chạy cục bộ]
    ConvertGGUF --> QuantizeModel[Giảm dung lượng mô hình]
    QuantizeModel --> EvaluateModel[Đánh giá chất lượng mô hình]
    EvaluateModel --> Passed{Mô hình đạt điều kiện triển khai}
    Passed -->|Không| Failed
    Passed -->|Có| PublishModel[Lưu kết quả vào kho mô hình riêng]
    PublishModel --> End([Kết thúc ghi nhận mô hình đã triển khai])
```

Pipeline Gemma 4 dùng chung mã nguồn giữa dự án và notebook Colab tại
[`training/gemma4_finetuning.py`](backend/agentic_ai/src/training/gemma4_finetuning.py).

## 10. Sự kiện, bộ nhớ và vòng cải tiến

### 10.1 Xử lý sự kiện và đề xuất cải tiến

```mermaid
flowchart TD
    Start([Bắt đầu nhận sự kiện hoặc đến lịch chạy]) --> QueueEvent[Đưa sự kiện vào hàng chờ xử lý]
    QueueEvent --> HandleEvent[Chọn cách xử lý phù hợp với loại sự kiện]
    HandleEvent --> NeedIndex{Sự kiện có yêu cầu đưa tài liệu vào kho kiến thức}
    NeedIndex -->|Có| IngestDocument[Chạy quy trình tiếp nhận tài liệu]
    NeedIndex -->|Không| RecordTrace[Ghi lịch sử vận hành]
    IngestDocument --> RecordTrace
    RecordTrace --> EnoughData{Đã đủ dữ liệu để đánh giá cải tiến}
    EnoughData -->|Không| End([Kết thúc lưu kết quả xử lý sự kiện])
    EnoughData -->|Có| AnalyzeMetrics[Phân tích số liệu vận hành]
    AnalyzeMetrics --> HasProposal{Có thay đổi cấu hình hoặc hướng dẫn AI đáng đề xuất}
    HasProposal -->|Không| End
    HasProposal -->|Có| CreateProposal[Tạo đề xuất và chờ quản trị viên duyệt]
    CreateProposal --> Approved{Quản trị viên phê duyệt}
    Approved -->|Không| RejectProposal([Kết thúc đánh dấu đề xuất bị từ chối])
    Approved -->|Có| ApplyProposal[Áp dụng thay đổi thuộc phạm vi cho phép]
    ApplyProposal --> ObserveImpact[Theo dõi tác động sau thay đổi]
    ObserveImpact --> NeedRollback{Kết quả xấu hoặc quản trị viên yêu cầu hoàn tác}
    NeedRollback -->|Có| RollbackChange[Khôi phục cấu hình trước đó]
    NeedRollback -->|Không| End
    RollbackChange --> End
```

Vòng cải tiến không tự ý sửa mã nguồn. Các đề xuất nằm trong nhóm cấu hình/prompt
được hỗ trợ và phải đi qua API phê duyệt của ADMIN.

### 10.2 Ghi nhớ sau hội thoại

```mermaid
flowchart TD
    StartMemory([Bắt đầu hoàn tất một lượt hội thoại]) --> SaveShortTerm[Lưu tin nhắn cho cuộc trò chuyện hiện tại]
    SaveShortTerm --> WorthRemembering{Thông tin có hữu ích cho các lượt sau}
    WorthRemembering -->|Không| EndMemory([Kết thúc không lưu vào bộ nhớ dài hạn])
    WorthRemembering -->|Có| ExtractPreference[Trích xuất sở thích hoặc dữ kiện ổn định]
    ExtractPreference --> SafeMemory{Nội dung có an toàn và được phép lưu}
    SafeMemory -->|Không| EndMemory
    SafeMemory -->|Có| SaveLongTerm[Lưu thông tin hữu ích vào bộ nhớ dài hạn]
    SaveLongTerm --> NextTurn[Khi có lượt mới tìm lại thông tin liên quan]
    NextTurn --> AddContext[Đưa thông tin phù hợp vào nội dung AI đang xử lý]
    AddContext --> EndContext([Kết thúc tiếp tục xử lý lượt hội thoại mới])
```

## 11. Nhóm API công khai

| Nhóm | Prefix | Trách nhiệm |
|---|---|---|
| Hội thoại | `/tro-chuyen` | Chat JSON, SSE, khả năng, workspace và tùy chọn cá nhân |
| Lịch sử | `/lich-su` | Phiên, tiêu đề, trạng thái và tin nhắn |
| Suy luận | `/suy-luan` | Sinh nội dung, dịch, mã nguồn, tóm tắt, trích xuất, kiểm duyệt và các utility AI |
| Tiếp nạp | `/tiep-nap` | Thêm/xóa tài liệu khỏi RAG và graph |
| Phản hồi | `/phan-hoi` | Ghi nhận đánh giá câu trả lời |
| Tinh chỉnh | `/tinh-chinh` | Dataset, sample, job, hủy, đánh giá và triển khai |
| MCP | `/mcp` | Preset, server, kiểm tra kết nối và callback |
| Sự kiện | `/su-kien` | Webhook, lịch chạy, lịch sử và trigger |
| Tự tối ưu | `/toi-uu` | Vấn đề, đề xuất, phê duyệt và hoàn tác |
| Can thiệp | `/ngat-qua-trinh` | Hủy phiên và phản hồi yêu cầu phê duyệt |
| DRM nội bộ | `/drm` | Đánh giá policy DRM rủi ro cao |
| Vận hành | `/health`, `/ready`, `/metrics`, `/evaluate/*` | Liveness, readiness và telemetry |

## 12. Công nghệ đang sử dụng

| Lớp | Công nghệ | Vai trò thực tế |
|---|---|---|
| API | Python 3.11, FastAPI, Uvicorn, Pydantic | HTTP API, dependency injection, schema và validation |
| Streaming | Server-Sent Events | Phát model, plan, tool, token và kết quả hội thoại |
| Agent | LangChain, LangGraph | Prompt/model adapter, state graph, checkpoint và DAG orchestration |
| Model runtime | Ollama hoặc API tương thích OpenAI | Chạy model chính được cấu hình bởi `LLM_MODEL` |
| Model/NLP | Transformers, Sentence Transformers, CrossEncoder, NLI, NLLB | Đa phương thức, rerank, kiểm chứng và dịch |
| RAG | RAG service, Qdrant, BM25, Neo4j gián tiếp | Vector search, hybrid memory và knowledge graph |
| Dữ liệu | MongoDB/Motor/PyMongo, Redis | Lịch sử, checkpoint, cấu hình, cache, memory và session |
| Hàng đợi/lưu trữ | RabbitMQ, MinIO | Hạ tầng event/task và object storage của hệ thống |
| Web/công cụ | Tavily, MCP SDK, Playwright, HTTPX | Tìm web, công cụ ngoài và gọi microservice |
| Bảo mật | Presidio, spaCy, guardrails nội bộ, JWT, RestrictedPython | PII, injection, secret leak, auth và sandbox tài nguyên giới hạn |
| Tài liệu | Docling, MarkItDown, PyMuPDF, pypdfium2, Pillow | Trích xuất và xử lý tài liệu/ảnh |
| Fine-tuning | PEFT, TRL, Datasets, Accelerate, bitsandbytes, MLX, llama.cpp, GGUF | LoRA/QLoRA, merge và xuất local model |
| Quan sát | Loguru, Prometheus metrics, AgentOps nội bộ | Trace ID, latency, token, tool call và security event |
| Triển khai | Docker Compose, Traefik | Container, dependency health và định tuyến service |

## 13. Nguồn kiểm chứng chính

- [Khởi tạo service và readiness](backend/agentic_ai/src/main.py)
- [Hội thoại đồng bộ](backend/agentic_ai/src/api/interaction/executor.py)
- [Hội thoại SSE](backend/agentic_ai/src/api/interaction/stream.py)
- [Knowledge graph workflow](backend/agentic_ai/src/workflow/graph.py)
- [Supervisor DAG workflow](backend/agentic_ai/src/workflow/orchestration.py)
- [RAG client](backend/agentic_ai/src/services/rag_client.py)
- [MCP service](backend/agentic_ai/src/services/mcp.py)
- [Fine-tuning service](backend/agentic_ai/src/services/finetuning.py)
- [Danh sách dependency](backend/agentic_ai/requirements.txt)

## 14. Quy tắc cập nhật tài liệu

Khi thêm route, node LangGraph, service dependency hoặc backend công nghệ mới,
cần cập nhật đồng thời bảng API, sơ đồ liên quan và bảng công nghệ. Không dùng
URI file tuyệt đối; mọi liên kết phải tương đối từ root repository.
