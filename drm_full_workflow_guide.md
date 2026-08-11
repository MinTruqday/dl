# DRM — kiến trúc và workflow hiện hành

> Tài liệu này bám theo implementation trong `backend/drm`. DRM ưu tiên luật xác
> định, mật mã và audit. Agentic AI chỉ tham gia nhánh đánh giá policy rủi ro cao;
> không được mô tả mọi bước DRM như một tác vụ của agent.

## 1. Phạm vi dịch vụ

DRM chịu trách nhiệm:

- xác thực JWT, session và phân quyền cho API người dùng;
- cấp, kiểm tra, giới hạn thiết bị/lượt mở và thu hồi giấy phép;
- kết xuất EditorJS/LaTeX, đóng thủy ấn hiển thị và thủy ấn ẩn;
- mã hóa tài liệu bằng AES-256-GCM và bọc khóa AES bằng RSA-OAEP SHA-256;
- giữ đúng loại container bảo vệ: `.doclib` cho EditorJS và `.doclibx` cho LaTeX;
- cấu hình bảo vệ theo BASIC, PRO và PREMIUM; ADMIN được chuẩn hóa về khả năng
  PREMIUM nhưng vẫn giữ quyền quản trị riêng;
- giải quyết tranh chấp bản quyền;
- phát hiện bất thường mạng, tính trust score và risk score;
- cấp khóa AES tạm, kiểm tra fingerprint và cung cấp nội dung cho AI nội bộ;
- lưu audit log và metrics vận hành.

Điểm vào chính: [`backend/drm/src/main.py`](backend/drm/src/main.py).

## 2. Kiến trúc tổng thể

Sơ đồ này là bản đồ thành phần và dependency, **không phải workflow nghiệp vụ**.
Node ở đây được phép mang tên service/module; từ mục 3 trở đi, mỗi node workflow
phải là một hành động hoặc một câu hỏi quyết định.

```mermaid
flowchart LR
    Client[Frontend hoặc dịch vụ DocLib] -->|JWT| Gateway[Traefik]
    Internal[Dịch vụ nội bộ] -->|X-Internal-Token| Gateway
    Gateway --> API[FastAPI DRM]

    subgraph Modules[Module nghiệp vụ]
        API --> License[License API]
        API --> Watermark[Watermark API]
        API --> Copyright[Copyright API]
        API --> Protection[Protection API]
    end

    subgraph Storage[Dữ liệu]
        Mongo[(MongoDB)]
        Redis[(Redis)]
    end

    subgraph Services[Dịch vụ phụ thuộc]
        Content[Content service]
        Finance[Finance service]
        Humanity[Humanity service]
        Compile[Compilation API]
        Agentic[Agentic AI policy]
    end

    License --> Mongo
    License --> Redis
    Watermark --> Mongo
    Copyright --> Mongo
    Protection --> Mongo
    Protection --> Redis
    License --> Content
    License --> Finance
    Copyright --> Content
    Protection --> Content
    Protection --> Humanity
    Watermark --> Compile
    Watermark --> Agentic
```

### Ranh giới dữ liệu

| Nơi lưu/nguồn | Dữ liệu |
|---|---|
| MongoDB DRM | `drm_licenses`, `document_drm_settings`, `copyright_disputes`, `audit_logs` |
| Redis | session đã đăng nhập, rate limit, thống kê IP/request 60 giây, khóa AES tạm |
| Content service | tài liệu, quyền đọc/sửa và policy DRM phản chiếu sang content |
| Finance service | giao dịch mua tài liệu premium |
| Humanity service | trạng thái và tier của người dùng |

DRM không trực tiếp phụ thuộc RabbitMQ, MinIO, Qdrant hay Neo4j trong runtime hiện
tại; không đưa các thành phần đó vào workflow DRM.

## 3. Xác thực và phân quyền

```mermaid
flowchart TD
    Start([Bắt đầu nhận yêu cầu]) --> RequestType{Yêu cầu đến từ đâu}
    RequestType -->|Người dùng| DecodeJWT[Kiểm tra thông tin đăng nhập]
    DecodeJWT --> ValidClaims{Thông tin đăng nhập có đầy đủ và hợp lệ}
    ValidClaims -->|Không| Unauthorized([Kết thúc yêu cầu đăng nhập lại])
    ValidClaims -->|Có| CheckSession[Kiểm tra phiên đăng nhập còn tồn tại]
    CheckSession --> ActiveSession{Phiên đăng nhập còn hiệu lực}
    ActiveSession -->|Không| Unauthorized
    ActiveSession -->|Có| CheckPermission[Kiểm tra vai trò và quyền thực hiện]
    CheckPermission --> Allowed{Người dùng có quyền thực hiện}
    Allowed -->|Không| Forbidden([Kết thúc từ chối yêu cầu])
    Allowed -->|Có| Continue[Chuyển sang quy trình phù hợp]
    RequestType -->|Dịch vụ DocLib| CompareToken[Kiểm tra khóa xác thực nội bộ]
    CompareToken --> ValidInternalToken{Khóa xác thực nội bộ chính xác}
    ValidInternalToken -->|Không| Forbidden
    ValidInternalToken -->|Có| Continue
    Continue --> End([Kết thúc bước xác thực])
```

- API giấy phép, thủy ấn và cấu hình bản quyền dùng JWT người dùng.
- Toàn bộ `/bao-ve/*` dùng `X-Internal-Token` và chỉ dành cho service-to-service.
- API giải quyết tranh chấp yêu cầu ADMIN.

## 4. Workflow kết xuất tài liệu DRM

Đây là luồng đầy đủ của `GET /thuy-an/{document_id}`.

```mermaid
flowchart TD
    Start([Bắt đầu xuất tài liệu]) --> Authenticate[Kiểm tra đăng nhập]
    Authenticate --> LoadDocument[Đọc tài liệu và quyền truy cập]
    LoadDocument --> DocumentExists{Tài liệu tồn tại và người dùng được phép đọc}
    DocumentExists -->|Không| NotFound([Kết thúc không tìm thấy hoặc không có quyền])
    DocumentExists -->|Có| EvaluatePolicy[Đánh giá mức bảo vệ cần áp dụng]
    EvaluatePolicy --> PolicyAvailable{Kết quả đánh giá có hợp lệ}
    PolicyAvailable -->|Không| ApplySafePolicy[Áp dụng mức bảo vệ an toàn mặc định]
    PolicyAvailable -->|Có| IsBlocked{Quy tắc bảo vệ có chặn việc xuất tài liệu}
    IsBlocked -->|Có| Denied([Kết thúc từ chối xuất tài liệu])
    IsBlocked -->|Không| NeedPurchase{Đây là tài liệu trả phí của người khác}
    ApplySafePolicy --> NeedPurchase
    NeedPurchase -->|Có| CheckPurchase[Kiểm tra giao dịch mua tài liệu]
    CheckPurchase --> Purchased{Người dùng đã mua tài liệu}
    Purchased -->|Không| Denied
    Purchased -->|Có| ChooseFormat{Tài liệu được soạn theo định dạng nào}
    NeedPurchase -->|Không| ChooseFormat
    ChooseFormat -->|Tài liệu thường| AddEditorWatermark[Chèn dấu nhận dạng ẩn nếu cần]
    ChooseFormat -->|Tài liệu công thức| PrepareLatex[Chuẩn bị nội dung công thức]
    AddEditorWatermark --> CompileEditor[Tạo tệp PDF]
    PrepareLatex --> CompileLatex[Tạo tệp PDF]
    CompileEditor --> Compiled{Tạo tệp thành công}
    CompileLatex --> Compiled
    Compiled -->|Không| CompileError([Kết thúc không thể tạo tệp])
    Compiled -->|Có| AddVisualMarks[Thêm hình mờ và dấu nhận dạng chống sao chép]
    AddVisualMarks --> EncryptRequired{Tệp có cần được khóa để bảo vệ}
    EncryptRequired -->|Không| ReturnPDF([Kết thúc trả tệp PDF])
    EncryptRequired -->|Có| CreateLicense[Tạo giấy phép mở tệp và khóa bảo vệ]
    CreateLicense --> EncryptPDF[Khóa nội dung tệp]
    EncryptPDF --> BuildContainer[Đóng gói dữ liệu kiểm tra và nội dung đã khóa]
    BuildContainer --> OriginalFormat{Định dạng ban đầu của tài liệu}
    OriginalFormat -->|Tài liệu thường| ReturnDoclib([Kết thúc trả tệp doclib])
    OriginalFormat -->|Tài liệu công thức| ReturnDoclibx([Kết thúc trả tệp doclibx])
```

Khi Agentic AI lỗi, hệ thống không bỏ bảo vệ mà dùng mặc định an toàn: bật
watermark hiển thị, micro-dot và AES.

### Quy ước định dạng

| Định dạng | Nội dung soạn thảo | Khi DRM bật AES |
|---|---|---|
| `.doclib` | EditorJS JSON | Giữ đuôi `.doclib`; payload là container E-DRM đã mã hóa |
| `.doclibx` | LaTeX source | Giữ đuôi `.doclibx`; payload là container E-DRM đã mã hóa |

DRM không chuyển `.doclibx` thành `.doclib`. Hai container dùng chung envelope
`file_id + SHA-256 + nonce + ciphertext`, còn extension bảo toàn engine cần dùng
sau khi giải mã. Khi policy tắt AES, cả hai nhánh kết xuất trả PDF.

## 5. Workflow cấp quyền mở file `.doclib` hoặc `.doclibx`

Endpoint: `POST /giay-phep/kiem-tra`.

```mermaid
flowchart TD
    Start([Bắt đầu mở tệp được bảo vệ]) --> Authenticate[Kiểm tra đăng nhập]
    Authenticate --> FindLicense[Tra cứu giấy phép mở tệp]
    FindLicense --> LicenseExists{Có giấy phép tương ứng}
    LicenseExists -->|Không| NotFound([Kết thúc không tìm thấy giấy phép])
    LicenseExists -->|Có| LicenseUsable{Giấy phép còn hạn và còn lượt mở}
    LicenseUsable -->|Không| MarkExpired[Cập nhật giấy phép đã hết hạn hoặc hết lượt]
    MarkExpired --> Deny([Kết thúc từ chối mở tệp])
    LicenseUsable -->|Có| IsOwner{Giấy phép thuộc người dùng hiện tại}
    IsOwner -->|Không| Deny
    IsOwner -->|Có| NeedPurchase{Tài liệu trả phí có yêu cầu giao dịch mua}
    NeedPurchase -->|Có| CheckPurchase[Kiểm tra giao dịch mua tài liệu]
    CheckPurchase --> Purchased{Giao dịch hợp lệ}
    Purchased -->|Không| RevokeLicense[Thu hồi giấy phép]
    RevokeLicense --> Deny
    Purchased -->|Có| WrapKey[Bảo vệ khóa mở tệp cho đúng thiết bị]
    NeedPurchase -->|Không| WrapKey
    WrapKey --> RecordNetwork[Theo dõi số lần yêu cầu và địa chỉ mạng]
    RecordNetwork --> IsAnomaly{Có dấu hiệu mở tệp bất thường}
    IsAnomaly -->|Có| RevokeLicense
    IsAnomaly -->|Không| ClaimFingerprint[Gắn tệp với thiết bị và tăng số lượt mở]
    ClaimFingerprint --> FingerprintAccepted{Thiết bị được chấp nhận}
    FingerprintAccepted -->|Không| Deny
    FingerprintAccepted -->|Có| WriteAudit[Ghi lịch sử cấp quyền mở tệp]
    WriteAudit --> End([Kết thúc trả khóa mở tệp quyền sử dụng và hạn dùng])
```

`POST /giay-phep/{file_id}/thu-hoi` cho phép chủ giấy phép hoặc ADMIN đặt trạng
thái `REVOKED` và ghi audit log.

## 6. Workflow cấu hình bảo vệ bản quyền

Endpoint: `PUT /ban-quyen/{document_id}`.

```mermaid
flowchart TD
    Start([Bắt đầu thiết lập bảo vệ tài liệu]) --> CheckEditRight[Kiểm tra quyền sửa tài liệu]
    CheckEditRight --> CanEdit{Người dùng có quyền sửa}
    CanEdit -->|Không| Deny([Kết thúc từ chối thay đổi])
    CanEdit -->|Có| WhichTier{Người dùng thuộc gói nào}
    WhichTier -->|Cơ bản| ApplyBasic[Áp dụng mức bảo vệ tiêu chuẩn]
    WhichTier -->|Nâng cao| ApplyPro[Thêm hình mờ nhưng vẫn cho phép sao chép và in]
    WhichTier -->|Cao cấp hoặc quản trị viên| ApplyPremium[Cho phép thiết lập đầy đủ các lớp bảo vệ]
    ApplyBasic --> SaveSettings[Lưu thiết lập bảo vệ]
    ApplyPro --> SaveSettings
    ApplyPremium --> PrivateLink{Có cho phép mở bằng liên kết riêng}
    PrivateLink -->|Có| CreatePrivateToken[Tạo mã dùng một lần cho liên kết riêng]
    PrivateLink -->|Không| SaveSettings
    CreatePrivateToken --> SaveSettings
    SaveSettings --> SyncPolicy[Đồng bộ quy tắc bảo vệ với tài liệu]
    SyncPolicy --> Synced{Quy tắc bảo vệ đã được lưu đầy đủ}
    Synced -->|Không| SyncError([Kết thúc báo không thể đồng bộ])
    Synced -->|Có| End([Kết thúc trả thiết lập đang có hiệu lực])
```

Giá trị chung được lưu gồm profile, `AES-256-GCM`, cách giao văn bản, người cập
nhật và thời điểm cập nhật. Token private link chỉ trả một lần; database lưu hash.

## 7. Workflow tranh chấp bản quyền

```mermaid
flowchart TD
    Start([Bắt đầu giải quyết tranh chấp]) --> Authenticate[Kiểm tra đăng nhập]
    Authenticate --> IsAdmin{Người xử lý có phải quản trị viên}
    IsAdmin -->|Không| Deny([Kết thúc từ chối xử lý])
    IsAdmin -->|Có| FindDispute[Tra cứu tranh chấp theo mã]
    FindDispute --> Exists{Tranh chấp có tồn tại}
    Exists -->|Không| NotFound([Kết thúc không tìm thấy tranh chấp])
    Exists -->|Có| ResolveDispute[Cập nhật kết luận người xử lý và thời điểm giải quyết]
    ResolveDispute --> End([Kết thúc trả kết quả giải quyết])
```

Implementation hiện tại giải quyết dispute đã tồn tại; tài liệu không được tuyên
bố có workflow tạo/khiếu nại dispute nếu chưa có endpoint tương ứng trong DRM.

## 8. Workflow bảo vệ nội bộ

Các endpoint dưới `/bao-ve` là API service-to-service.

### 8.1 Bất thường mạng

```mermaid
flowchart TD
    Start([Bắt đầu kiểm tra hoạt động truy cập]) --> ValidateIP[Kiểm tra địa chỉ mạng]
    ValidateIP --> ValidIP{Địa chỉ mạng có hợp lệ}
    ValidIP -->|Không| Invalid([Kết thúc báo dữ liệu không hợp lệ])
    ValidIP -->|Có| CountRequests[Đếm số lần yêu cầu trong một phút]
    CountRequests --> RecordIP[Ghi nhận các địa chỉ mạng đã sử dụng]
    RecordIP --> IsAnomaly{Có dấu hiệu truy cập từ nhiều nơi bất thường}
    IsAnomaly -->|Có| FlagAnomaly[Đặt cờ phát hiện bất thường]
    IsAnomaly -->|Không| ClearAnomaly[Giữ trạng thái truy cập bình thường]
    FlagAnomaly --> End([Kết thúc trả kết quả kiểm tra])
    ClearAnomaly --> End
```

### 8.2 Trust score người dùng

```mermaid
flowchart TD
    Start([Bắt đầu tính điểm tin cậy]) --> LoadUser[Đọc trạng thái tài khoản]
    LoadUser --> IsActive{Tài khoản đang hoạt động}
    IsActive -->|Không| SetZero[Đặt điểm cơ sở bằng 0]
    IsActive -->|Có| SetHundred[Đặt điểm cơ sở bằng 100]
    SetZero --> CountRevoked[Đếm giấy phép đã bị thu hồi]
    SetHundred --> CountRevoked
    CountRevoked --> DeductRevoked[Trừ điểm theo số giấy phép bị thu hồi]
    DeductRevoked --> CountDenied[Đếm số lần truy cập bị từ chối]
    CountDenied --> DeductDenied[Trừ điểm theo số lần bị từ chối]
    DeductDenied --> ClampScore[Giới hạn điểm cuối trong khoảng 0 đến 100]
    ClampScore --> End([Kết thúc trả điểm tin cậy và lý do])
```

Trust score không được gán cố định theo BASIC/PRO/PREMIUM. Tier chỉ được trả kèm
profile người dùng.

### 8.3 Risk score tài liệu

Risk score cộng các yếu tố đang lưu: premium, private, protection đang bật,
dispute đang mở và số license bị thu hồi. Kết quả được chặn tối đa 100 và phân
loại `LOW`, `MEDIUM`, `HIGH`.

```mermaid
flowchart TD
    Start([Bắt đầu tính mức rủi ro của tài liệu]) --> LoadDocument[Đọc thông tin và thiết lập bảo vệ]
    LoadDocument --> Exists{Tài liệu có tồn tại}
    Exists -->|Không| NotFound([Kết thúc không tìm thấy tài liệu])
    Exists -->|Có| AddBaseRisk[Cộng điểm nếu tài liệu trả phí hoặc riêng tư]
    AddBaseRisk --> AddProtectionRisk[Cộng điểm theo các biện pháp bảo vệ đang bật]
    AddProtectionRisk --> CheckDisputes[Đếm tranh chấp bản quyền đang mở]
    CheckDisputes --> AddDisputeRisk[Cộng điểm theo số tranh chấp]
    AddDisputeRisk --> CheckRevoked[Đếm giấy phép đã bị thu hồi]
    CheckRevoked --> AddRevokedRisk[Cộng điểm theo số giấy phép bị thu hồi]
    AddRevokedRisk --> ClampRisk[Giới hạn tổng điểm tối đa 100]
    ClampRisk --> ClassifyRisk{Điểm thuộc mức nào}
    ClassifyRisk -->|Thấp| Low([Kết thúc mức rủi ro thấp])
    ClassifyRisk -->|Trung bình| Medium([Kết thúc mức rủi ro trung bình])
    ClassifyRisk -->|Cao| High([Kết thúc mức rủi ro cao])
```

### 8.4 Các API nội bộ khác

| Endpoint | Chức năng |
|---|---|
| `/bao-ve/thuy-an-dong` | Sinh text watermark, token SHA-256, opacity và font |
| `/bao-ve/cap-khoa-aes` | Tạo khóa ngẫu nhiên tạm thời trong Redis với TTL 60–3600 giây |
| `/bao-ve/xac-minh-van-tay` | So fingerprint/IP với lịch sử license và trả risk multiplier |
| `/bao-ve/noi-bo/giay-phep` | Đọc license theo `file_id` |
| `/bao-ve/noi-bo/cau-hinh` | Đọc policy theo `document_id` |
| `/bao-ve/noi-bo/noi-dung-ai` | Kiểm tra quyền Content + `allow_internal_ai`, ghi audit rồi trả nội dung hạn chế |

## 9. Workflow đánh giá policy với Agentic AI

```mermaid
flowchart TD
    Start([Bắt đầu đánh giá trước khi xuất tài liệu]) --> SendContext[Gửi thông tin người dùng tài liệu địa chỉ mạng và gói sử dụng]
    SendContext --> ApplyRules[Áp dụng các quy tắc bảo vệ có sẵn]
    ApplyRules --> NeedAI{Mức rủi ro có cần AI đánh giá thêm}
    NeedAI -->|Không| ReturnRules[Giữ kết quả từ luật xác định]
    NeedAI -->|Có| AskModel[Yêu cầu AI đánh giá theo mẫu kết quả quy định]
    AskModel --> ValidOutput{AI trả kết quả hợp lệ}
    ValidOutput -->|Không| ReturnRules
    ValidOutput -->|Có| MergeDecision[Kết hợp đánh giá của AI với giới hạn an toàn]
    ReturnRules --> ReturnPolicy[Trả quyết định và các lớp bảo vệ cần áp dụng]
    MergeDecision --> ReturnPolicy
    ReturnPolicy --> IsBlocked{Quyết định cuối có chặn việc xuất tài liệu}
    IsBlocked -->|Có| Block([Kết thúc từ chối xuất tài liệu])
    IsBlocked -->|Không| Continue([Kết thúc tiếp tục xuất tài liệu])
```

AI không trực tiếp cấp license hoặc giữ khóa. Quyết định cuối vẫn được DRM áp
dụng bằng luật, mật mã và trạng thái lưu trữ.

## 10. Công nghệ đang sử dụng

| Lớp | Công nghệ | Vai trò thực tế |
|---|---|---|
| API | Python 3.11, FastAPI, Uvicorn, Pydantic | HTTP API, validation, dependency injection |
| Xác thực | PyJWT, OAuth2 bearer, HMAC compare | JWT HS256, session và internal token |
| Mật mã | `cryptography`, RSA-OAEP SHA-256, AES-256-GCM, SHA-256 | Bọc khóa, mã hóa file, fingerprint/hash |
| PDF/watermark | PyMuPDF `fitz`, zero-width characters, micro-dot | Đóng watermark hiển thị, ẩn và truy vết |
| Dữ liệu | MongoDB, Motor, PyMongo | License, policy, dispute và audit |
| Trạng thái nhanh | Redis asyncio | Session, rate limit, anomaly window và key TTL |
| Giao tiếp service | HTTPX | Content, Finance, Humanity, Compilation và Agentic AI |
| Quan sát | Loguru, Prometheus middleware, trace ID | Log nghiệp vụ, metrics và correlation |
| Triển khai | Docker Compose, Traefik | Container, health check và route theo prefix |

## 11. API và quyền truy cập

| Prefix | Endpoint chính | Quyền |
|---|---|---|
| `/giay-phep` | kiểm tra, thu hồi | JWT; chủ license hoặc ADMIN tùy thao tác |
| `/thuy-an` | kết xuất, giải mã truy vết | JWT; giải mã truy vết yêu cầu ADMIN |
| `/ban-quyen` | cập nhật policy, giải quyết dispute | Chủ tài liệu; giải quyết yêu cầu ADMIN |
| `/bao-ve` | anomaly, trust, risk, key, fingerprint, internal content | `X-Internal-Token` |
| `/health`, `/ready`, `/metrics` | liveness, dependency readiness, metrics | Vận hành |

## 12. Nguồn kiểm chứng chính

- [Khởi tạo DRM service](backend/drm/src/main.py)
- [API giấy phép](backend/drm/src/api/license.py)
- [API bảo vệ nội bộ](backend/drm/src/api/protection.py)
- [Watermark và E-DRM export](backend/drm/src/services/watermark.py)
- [Cấu hình bản quyền](backend/drm/src/services/copyright.py)
- [Kho giấy phép](backend/drm/src/repositories/license.py)
- [Xác thực và phân quyền](backend/drm/src/core/dependency.py)
- [Danh sách dependency](backend/drm/requirements.txt)

## 13. Quy tắc cập nhật tài liệu

Mỗi khi thêm endpoint DRM, collection, thuật toán mã hóa hoặc dependency service,
phải cập nhật sơ đồ tương ứng, bảng API và bảng công nghệ. Không dùng URI file
tuyệt đối; mọi liên kết phải tương đối từ root repository.
