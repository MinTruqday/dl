# Agentic AI — kiến trúc và workflow hiện hành

## 1. Kiến trúc tổng thể

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
    Router --> Content
    Tools --> Web
    API --> WS
```

## 2. Workflow chung của một lượt hội thoại

```mermaid
flowchart TD
    Start([Bắt đầu: người dùng gửi tin nhắn]) --> ReadIdentity[Đọc người dùng, vai trò và gói từ JWT]
    ReadIdentity --> AllowedMode{Gói hiện tại có được dùng chế độ đã chọn?}
    AllowedMode -->|Không| TierError([Kết thúc: trả lỗi 403 về quyền sử dụng])
    AllowedMode -->|Có| HasUpload{Yêu cầu có tệp hoặc thư mục đính kèm?}
    HasUpload -->|Có| ReserveUpload[Giữ trước dung lượng tải lên]
    ReserveUpload --> UploadAllowed{Dung lượng còn đủ?}
    UploadAllowed -->|Không| QuotaError([Kết thúc: trả lỗi hết hạn mức])
    UploadAllowed -->|Có| ValidateMedia[Kiểm tra loại tệp, ảnh và âm thanh]
    HasUpload -->|Không| ScanInput[Quét prompt injection, PII và bí mật]
    ValidateMedia --> ScanInput
    ScanInput --> SafeInput{Đầu vào có an toàn?}
    SafeInput -->|Không| SecurityError([Kết thúc: trả lỗi bảo mật])
    SafeInput -->|Có| PrepareSession[Tạo hoặc cập nhật workspace của phiên]
    PrepareSession --> CheckAIQuota[Kiểm tra hạn mức sử dụng AI]
    CheckAIQuota --> HasAIQuota{Còn hạn mức hoặc là ADMIN?}
    HasAIQuota -->|Không| QuotaError
    HasAIQuota -->|Có| LoadContext[Nạp lịch sử, tùy chọn cá nhân và tài liệu]
    LoadContext --> HasDocuments{Có mã tài liệu cần sử dụng?}
    HasDocuments -->|Có| CheckAccess[Kiểm tra quyền đọc qua Content service]
    CheckAccess --> CanRead{Người dùng được đọc toàn bộ tài liệu?}
    CanRead -->|Không| DocumentError([Kết thúc: trả lỗi truy cập tài liệu])
    CanRead -->|Có| SelectFlow[Chọn workflow Chat, Plan, Knowledge hoặc Work/Goal]
    HasDocuments -->|Không| SelectFlow
    SelectFlow --> RunFlow[Thực thi workflow đã chọn]
    RunFlow --> SanitizeOutput[Loại dữ liệu nhạy cảm khỏi câu trả lời]
    SanitizeOutput --> SaveResult[Lưu lịch sử, bộ nhớ, tiêu đề và telemetry]
    SaveResult --> RecordUsage[Ghi nhận token và hạn mức đã dùng]
    RecordUsage --> End([Kết thúc: trả JSON hoặc đóng luồng SSE])
```

## 3. Quy tắc chọn mode và route

```mermaid
flowchart TD
    Start([Bắt đầu: đầu vào đã qua kiểm tra an toàn]) --> WhichMode{Người dùng chọn chế độ nào?}
    WhichMode -->|Plan| MakePlan[Tạo và lưu kế hoạch, không thực thi]
    WhichMode -->|Work hoặc Goal| RunSupervisor[Chuyển sang workflow Supervisor DAG]
    WhichMode -->|Learn| RunKnowledge[Chuyển sang workflow Knowledge RAG]
    WhichMode -->|Chat| HasAttachment{Có tài liệu, tệp hoặc thư mục đính kèm?}
    HasAttachment -->|Có| RunKnowledge
    HasAttachment -->|Không| UseWeb{Người dùng có bật tìm kiếm web?}
    UseWeb -->|Không| RunDirect[Trả lời bằng workflow Chat trực tiếp]
    UseWeb -->|Có| ClassifyIntent[Phân loại ý định bằng semantic router]
    ClassifyIntent --> BestFlow{Workflow nào phù hợp nhất?}
    BestFlow -->|Chat| RunDirect
    BestFlow -->|Tra cứu kiến thức| RunKnowledge
    BestFlow -->|Thực hiện công việc| RunSupervisor
    MakePlan --> End([Kết thúc: trả kết quả của chế độ đã chọn])
    RunSupervisor --> End
    RunKnowledge --> End
    RunDirect --> End
```

## 4. Workflow Knowledge RAG

```mermaid
flowchart TD
    Start([Bắt đầu: nhận câu hỏi]) --> RewriteFromHistory[Viết lại câu hỏi theo lịch sử gần]
    RewriteFromHistory --> NeedKnowledge{Câu hỏi có cần tra cứu kiến thức?}
    NeedKnowledge -->|Không| AnswerDirectly[Để model trả lời trực tiếp]
    AnswerDirectly --> End([Kết thúc: trả câu trả lời])
    NeedKnowledge -->|Có| DecodeAttachments[Giải mã nội dung tệp và thư mục đính kèm]
    DecodeAttachments --> RetrieveEvidence[Truy xuất bằng RAG service]
    RetrieveEvidence --> RerankEvidence[Sắp hạng lại kết quả bằng CrossEncoder nếu khả dụng]
    RerankEvidence --> SmartMode{Có bật kiểm tra thông minh?}
    SmartMode -->|Có| GradeEvidence[Chấm độ liên quan của từng bằng chứng]
    SmartMode -->|Không| HasEvidence{Đã có bằng chứng để trả lời?}
    GradeEvidence --> HasEvidence
    HasEvidence -->|Có| GenerateAnswer[Sinh câu trả lời kèm nguồn]
    HasEvidence -->|Không| WebAllowed{Người dùng có cho phép tìm web?}
    WebAllowed -->|Có| SearchWeb[Tìm thêm nguồn bằng Tavily]
    SearchWeb --> GradeEvidence
    WebAllowed -->|Không| GenerateAnswer
    GenerateAnswer --> NeedVerification{Có bật kiểm chứng thông minh?}
    NeedVerification -->|Không| End
    NeedVerification -->|Có| VerifyAnswer[Kiểm chứng bằng reasoner và NLI]
    VerifyAnswer --> Verified{Câu trả lời đạt yêu cầu?}
    Verified -->|Có| End
    Verified -->|Không, còn lượt thử| ImproveQuery[Tối ưu lại câu hỏi truy xuất]
    ImproveQuery --> RetrieveEvidence
    Verified -->|Không, đã hết lượt thử| EndWithWarning([Kết thúc: trả kết quả tốt nhất kèm trạng thái kiểm chứng])
```

## 5. Workflow tiếp nạp tri thức

```mermaid
flowchart TD
    Start([Bắt đầu: nhận yêu cầu tiếp nạp tài liệu]) --> Authenticate[Kiểm tra người dùng và vai trò]
    Authenticate --> SendToRAG[Gửi tài liệu sang RAG service để chia đoạn và lập chỉ mục]
    SendToRAG --> Ingested{RAG service tiếp nạp thành công?}
    Ingested -->|Không| Fail([Kết thúc: trả lỗi tiếp nạp])
    Ingested -->|Có| ReadGraphText[Nhận phần văn bản dùng để xây dựng knowledge graph]
    ReadGraphText --> ExtractRelations[Trích xuất thực thể và quan hệ có cấu trúc]
    ExtractRelations --> ReplaceGraph[Đề nghị RAG service thay graph của tài liệu]
    ReplaceGraph --> GraphSaved{Graph được cập nhật thành công?}
    GraphSaved -->|Có| End([Kết thúc: trả số đoạn và số quan hệ])
    GraphSaved -->|Không| DeleteIndex[Xóa chỉ mục vừa tạo để tránh dữ liệu nửa chừng]
    DeleteIndex --> Fail
```

## 6. Workflow Work và Goal: Supervisor DAG

```mermaid
flowchart TD
    Start([Bắt đầu: nhận yêu cầu Work hoặc Goal]) --> BuildDAG[Lập kế hoạch thành DAG gồm task và dependency]
    BuildDAG --> ValidatePlan[Kiểm tra cấu trúc, giới hạn và quy tắc governance]
    ValidatePlan --> ValidPlan{Kế hoạch hợp lệ?}
    ValidPlan -->|Không| PlanError([Kết thúc: trả lỗi kế hoạch])
    ValidPlan -->|Có| PickReadyTask[Chọn task có dependency đã hoàn tất]
    PickReadyTask --> HasReadyTask{Có task sẵn sàng chạy?}
    HasReadyTask -->|Không| AllFinished{Tất cả task đã kết thúc?}
    AllFinished -->|Không| Deadlock([Kết thúc: báo deadlock hoặc dependency lỗi])
    HasReadyTask -->|Có| ChooseCapability{Task cần năng lực nào?}
    ChooseCapability -->|Hiểu yêu cầu| RunInterpreter[Giao task cho agent diễn giải]
    ChooseCapability -->|Tìm kiếm| RunSearch[Giao task cho agent tìm kiếm]
    ChooseCapability -->|Thao tác công cụ| RunTool[Giao task cho action tools]
    ChooseCapability -->|Nghiên cứu| RunResearch[Giao task cho knowledge researcher]
    ChooseCapability -->|Lập luận| RunReasoning[Giao task cho reasoning agent]
    RunInterpreter --> RecordTask
    RunSearch --> RecordTask
    RunTool --> RecordTask
    RunResearch --> RecordTask
    RunReasoning --> RecordTask[Ghi trạng thái và kết quả của task]
    RecordTask --> AllFinished
    AllFinished -->|Không| PickReadyTask
    AllFinished -->|Có| TrimResult[Rút gọn artifact vượt giới hạn]
    TrimResult --> SanitizeResult[Kiểm tra và làm sạch đầu ra]
    SanitizeResult --> AggregateResult[Tổng hợp kết quả cuối cùng]
    AggregateResult --> End([Kết thúc: trả kết quả Work hoặc Goal])
```

## 7. Workflow công cụ và MCP

```mermaid
flowchart TD
    Start([Bắt đầu: agent yêu cầu dùng công cụ]) --> FindTool[Tra cứu công cụ trong registry]
    FindTool --> Found{Tìm thấy công cụ?}
    Found -->|Không| ToolError([Kết thúc: báo công cụ không tồn tại])
    Found -->|Có| IsMCP{Đây có phải công cụ MCP?}
    IsMCP -->|Có| LoadMCP[Đọc cấu hình MCP của người dùng]
    LoadMCP --> ValidateMCP[Kiểm tra command, URL và chính sách mạng]
    ValidateMCP --> ValidMCP{Cấu hình và kết nối hợp lệ?}
    ValidMCP -->|Không| MCPError([Kết thúc: báo MCP không khả dụng])
    ValidMCP -->|Có| DiscoverTools[Kết nối và đọc schema công cụ từ MCP server]
    DiscoverTools --> CheckGovernance[Kiểm tra input và quyền thực thi]
    IsMCP -->|Không| CheckGovernance
    CheckGovernance --> NeedApproval{Thao tác có cần người dùng phê duyệt?}
    NeedApproval -->|Có| AskApproval[Tạm dừng và gửi yêu cầu phê duyệt]
    AskApproval --> Approved{Người dùng chấp thuận?}
    Approved -->|Không| Denied([Kết thúc: không thực thi công cụ])
    Approved -->|Có| ExecuteTool[Thực thi công cụ với timeout]
    NeedApproval -->|Không| ExecuteTool
    ExecuteTool --> Successful{Công cụ chạy thành công?}
    Successful -->|Không| ToolError
    Successful -->|Có| RecordTelemetry[Ghi telemetry và lượng token công cụ]
    RecordTelemetry --> End([Kết thúc: trả kết quả về cho agent])
```

## 8. Workflow tinh chỉnh DocLib Metis

```mermaid
flowchart TD
    Start([Bắt đầu: nhập mẫu huấn luyện]) --> BuildDataset[Tạo dataset từ mẫu thủ công, feedback hoặc tài liệu]
    BuildDataset --> EnoughSamples{Dataset có ít nhất 10 mẫu hợp lệ?}
    EnoughSamples -->|Không| Reject([Kết thúc: yêu cầu bổ sung dữ liệu])
    EnoughSamples -->|Có| CreateJob[Tạo training job ở trạng thái chờ]
    CreateJob --> RunTraining[Khởi chạy tiến trình huấn luyện có thể hủy]
    RunTraining --> WhichBase{Base model thuộc loại nào?}
    WhichBase -->|Gemma 4| TrainQLoRA[Huấn luyện QLoRA NF4 cho model đa phương thức]
    WhichBase -->|Model được hỗ trợ khác| TrainLoRA[Huấn luyện bằng pipeline LoRA phù hợp]
    TrainQLoRA --> TrainingOK{Huấn luyện thành công?}
    TrainLoRA --> TrainingOK
    TrainingOK -->|Không hoặc bị hủy| Failed([Kết thúc: lưu trạng thái lỗi hoặc đã hủy])
    TrainingOK -->|Có| SaveAdapter[Lưu adapter đã huấn luyện]
    SaveAdapter --> MergeModel[Ghép adapter vào base model]
    MergeModel --> ConvertGGUF[Chuyển model Hugging Face sang GGUF F16]
    ConvertGGUF --> QuantizeModel[Lượng tử hóa Q4_K_M hoặc Q8_0]
    QuantizeModel --> EvaluateModel[Đánh giá chất lượng model]
    EvaluateModel --> Passed{Model đạt điều kiện triển khai?}
    Passed -->|Không| Failed
    Passed -->|Có| PublishModel[Đẩy artifact lên Hugging Face private repository]
    PublishModel --> End([Kết thúc: ghi nhận model đã triển khai])
```

## 9. Sự kiện và bộ nhớ

### 9.1 Xử lý sự kiện

```mermaid
flowchart TD
    Start([Bắt đầu: nhận webhook, lịch chạy hoặc trigger ADMIN]) --> QueueEvent[Đưa sự kiện vào vòng xử lý]
    QueueEvent --> HandleEvent[Thực thi handler phù hợp với loại sự kiện]
    HandleEvent --> NeedIndex{Sự kiện có yêu cầu tiếp nạp tài liệu?}
    NeedIndex -->|Có| IngestDocument[Chạy workflow tiếp nạp tài liệu]
    NeedIndex -->|Không| RecordTrace[Ghi trace vận hành]
    IngestDocument --> RecordTrace
    RecordTrace --> End([Kết thúc: lưu kết quả xử lý sự kiện])
```

### 9.2 Ghi nhớ sau hội thoại

```mermaid
flowchart TD
    StartMemory([Bắt đầu: hoàn tất một lượt hội thoại]) --> SaveShortTerm[Lưu tin nhắn vào bộ nhớ ngắn hạn]
    SaveShortTerm --> WorthRemembering{Thông tin có hữu ích cho các lượt sau?}
    WorthRemembering -->|Không| EndMemory([Kết thúc: không tạo ký ức dài hạn])
    WorthRemembering -->|Có| ExtractPreference[Trích xuất sở thích hoặc dữ kiện ổn định]
    ExtractPreference --> SafeMemory{Nội dung có an toàn và được phép lưu?}
    SafeMemory -->|Không| EndMemory
    SafeMemory -->|Có| SaveLongTerm[Lưu bộ nhớ dài hạn và vector vào Qdrant]
    SaveLongTerm --> NextTurn[Khi có lượt mới, truy xuất ký ức liên quan]
    NextTurn --> AddContext[Chèn ký ức phù hợp vào ngữ cảnh model]
    AddContext --> EndContext([Kết thúc: tiếp tục xử lý lượt hội thoại mới])
```

## 10. Nhóm API công khai

| Nhóm        | Prefix                                                 | Trách nhiệm                                                                                |
| ------------ | ------------------------------------------------------ | -------------------------------------------------------------------------------------------- |
| Hội thoại  | `/tro-chuyen`                                        | Chat JSON, SSE, khả năng, workspace và tùy chọn cá nhân                               |
| Lịch sử    | `/lich-su`                                           | Phiên, tiêu đề, trạng thái và tin nhắn                                               |
| Suy luận    | `/suy-luan`                                          | Sinh nội dung, dịch, mã nguồn, tóm tắt, trích xuất, kiểm duyệt và các utility AI |
| Tiếp nạp   | `/tiep-nap`                                          | Thêm/xóa tài liệu khỏi RAG và graph                                                    |
| Phản hồi   | `/phan-hoi`                                          | Ghi nhận đánh giá câu trả lời                                                         |
| Tinh chỉnh  | `/tinh-chinh`                                        | Dataset, sample, job, hủy, đánh giá và triển khai                                      |
| MCP          | `/mcp`                                               | Preset, server, kiểm tra kết nối và callback                                             |
| Sự kiện    | `/su-kien`                                           | Webhook, lịch chạy, lịch sử và trigger                                                  |
| Can thiệp   | `/ngat-qua-trinh`                                    | Hủy phiên và phản hồi yêu cầu phê duyệt                                             |
| Vận hành   | `/health`, `/ready`, `/metrics`, `/evaluate/*` | Liveness, readiness và telemetry                                                            |

## 11. Công nghệ đang sử dụng

| Lớp                  | Công nghệ                                                         | Vai trò thực tế                                                    |
| --------------------- | ------------------------------------------------------------------- | --------------------------------------------------------------------- |
| API                   | Python 3.11, FastAPI, Uvicorn, Pydantic                             | HTTP API, dependency injection, schema và validation                 |
| Streaming             | Server-Sent Events                                                  | Phát model, plan, tool, token và kết quả hội thoại              |
| Agent                 | LangChain, LangGraph                                                | Prompt/model adapter, state graph, checkpoint và DAG orchestration   |
| Model runtime         | Ollama hoặc API tương thích OpenAI                              | Chạy model chính được cấu hình bởi`LLM_MODEL`               |
| Model/NLP             | Transformers, Sentence Transformers, CrossEncoder, NLI, NLLB        | Đa phương thức, rerank, kiểm chứng và dịch                    |
| RAG                   | RAG service, Qdrant, BM25, Neo4j gián tiếp                        | Vector search, hybrid memory và knowledge graph                      |
| Dữ liệu             | MongoDB/Motor/PyMongo, Redis                                        | Lịch sử, checkpoint, cấu hình, cache, memory và session          |
| Hàng đợi/lưu trữ | RabbitMQ, MinIO                                                     | Hạ tầng event/task và object storage của hệ thống               |
| Web/công cụ         | Tavily, MCP SDK, Playwright, HTTPX                                  | Tìm web, công cụ ngoài và gọi microservice                      |
| Bảo mật             | Presidio, spaCy, guardrails nội bộ, JWT, RestrictedPython         | PII, injection, secret leak, auth và sandbox tài nguyên giới hạn |
| Tài liệu            | Docling, MarkItDown, PyMuPDF, pypdfium2, Pillow                     | Trích xuất và xử lý tài liệu/ảnh                              |
| Fine-tuning           | PEFT, TRL, Datasets, Accelerate, bitsandbytes, MLX, llama.cpp, GGUF | LoRA/QLoRA, merge và xuất local model                               |
| Quan sát             | Loguru, Prometheus metrics, AgentOps nội bộ                       | Trace ID, latency, token, tool call và security event                |
| Triển khai           | Docker Compose, Traefik                                             | Container, dependency health và định tuyến service                |
