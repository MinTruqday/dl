# DRM — kiến trúc và workflow hiện hành

## 1. Kiến trúc tổng thể

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

## 2. Xác thực và phân quyền

```mermaid
flowchart TD
    Start([Bắt đầu: DRM nhận HTTP request]) --> RequestType{Request đến từ người dùng hay service nội bộ?}
    RequestType -->|Người dùng| DecodeJWT[Giải mã JWT bằng HS256]
    DecodeJWT --> ValidClaims{Token có đủ sub, sid và uid?}
    ValidClaims -->|Không| Unauthorized([Kết thúc: trả lỗi 401])
    ValidClaims -->|Có| CheckSession[Đối chiếu session id trong Redis]
    CheckSession --> ActiveSession{Session còn hiệu lực?}
    ActiveSession -->|Không| Unauthorized
    ActiveSession -->|Có| CheckPermission[Kiểm tra role và permission của endpoint]
    CheckPermission --> Allowed{Người dùng có quyền thực hiện?}
    Allowed -->|Không| Forbidden([Kết thúc: trả lỗi 403])
    Allowed -->|Có| Continue[Chuyển request vào workflow nghiệp vụ tương ứng]
    RequestType -->|Service nội bộ| CompareToken[So sánh X-Internal-Token bằng constant-time compare]
    CompareToken --> ValidInternalToken{Internal token chính xác?}
    ValidInternalToken -->|Không| Forbidden
    ValidInternalToken -->|Có| Continue
    Continue --> End([Kết thúc bước xác thực])
```

## 3. Workflow kết xuất tài liệu DRM

```mermaid
flowchart TD
    Start([Bắt đầu: người dùng yêu cầu kết xuất tài liệu]) --> Authenticate[Kiểm tra JWT và session]
    Authenticate --> LoadDocument[Đọc tài liệu và quyền truy cập từ Content service]
    LoadDocument --> DocumentExists{Tài liệu tồn tại và người dùng được đọc?}
    DocumentExists -->|Không| NotFound([Kết thúc: trả lỗi 404 hoặc 403])
    DocumentExists -->|Có| EvaluatePolicy[Gửi ngữ cảnh sang Agentic AI để đánh giá policy]
    EvaluatePolicy --> PolicyAvailable{Agentic AI trả policy hợp lệ?}
    PolicyAvailable -->|Không| ApplySafePolicy[Áp dụng policy LEVEL_2 an toàn]
    PolicyAvailable -->|Có| IsBlocked{Policy có chặn kết xuất?}
    IsBlocked -->|Có| Denied([Kết thúc: trả lỗi 403])
    IsBlocked -->|Không| NeedPurchase{Đây là tài liệu premium của người khác?}
    ApplySafePolicy --> NeedPurchase
    NeedPurchase -->|Có| CheckPurchase[Kiểm tra giao dịch mua qua Finance service]
    CheckPurchase --> Purchased{Người dùng đã mua tài liệu?}
    Purchased -->|Không| Denied
    Purchased -->|Có| ChooseFormat{Định dạng nguồn của tài liệu là gì?}
    NeedPurchase -->|Không| ChooseFormat
    ChooseFormat -->|EditorJS| AddEditorWatermark[Chèn zero-width watermark nếu policy bật]
    ChooseFormat -->|LaTeX| PrepareLatex[Chuẩn bị mã nguồn LaTeX]
    AddEditorWatermark --> CompileEditor[Biên dịch EditorJS thành PDF]
    PrepareLatex --> CompileLatex[Biên dịch LaTeX thành PDF]
    CompileEditor --> Compiled{Biên dịch thành công?}
    CompileLatex --> Compiled
    Compiled -->|Không| CompileError([Kết thúc: trả lỗi biên dịch])
    Compiled -->|Có| AddVisualMarks[Đóng watermark hiển thị và micro-dot bằng PyMuPDF]
    AddVisualMarks --> EncryptRequired{Policy có yêu cầu mã hóa AES?}
    EncryptRequired -->|Không| ReturnPDF([Kết thúc: trả file PDF])
    EncryptRequired -->|Có| CreateLicense[Tạo license, file id và khóa AES]
    CreateLicense --> EncryptPDF[Mã hóa PDF bằng AES-256-GCM]
    EncryptPDF --> BuildContainer[Đóng gói file id, SHA-256, nonce và ciphertext]
    BuildContainer --> OriginalFormat{Định dạng nguồn ban đầu là gì?}
    OriginalFormat -->|EditorJS| ReturnDoclib([Kết thúc: trả container .doclib])
    OriginalFormat -->|LaTeX| ReturnDoclibx([Kết thúc: trả container .doclibx])
```

## 4. Workflow cấp quyền mở file `.doclib` hoặc `.doclibx`

```mermaid
flowchart TD
    Start([Bắt đầu: ứng dụng gửi file id, public key và fingerprint]) --> Authenticate[Kiểm tra JWT và session]
    Authenticate --> FindLicense[Tra cứu license theo file id]
    FindLicense --> LicenseExists{Có license tương ứng?}
    LicenseExists -->|Không| NotFound([Kết thúc: trả lỗi 404])
    LicenseExists -->|Có| LicenseUsable{License đang ACTIVE, chưa hết hạn và còn lượt mở?}
    LicenseUsable -->|Không| MarkExpired[Cập nhật trạng thái EXPIRED hoặc EXHAUSTED]
    MarkExpired --> Deny([Kết thúc: trả lỗi 403])
    LicenseUsable -->|Có| IsOwner{License thuộc người dùng hiện tại?}
    IsOwner -->|Không| Deny
    IsOwner -->|Có| NeedPurchase{Tài liệu premium có yêu cầu giao dịch mua?}
    NeedPurchase -->|Có| CheckPurchase[Kiểm tra giao dịch qua Finance service]
    CheckPurchase --> Purchased{Giao dịch hợp lệ?}
    Purchased -->|Không| RevokeLicense[Thu hồi license]
    RevokeLicense --> Deny
    Purchased -->|Có| WrapKey[Bọc khóa AES bằng public key với RSA-OAEP]
    NeedPurchase -->|Không| WrapKey
    WrapKey --> RecordNetwork[Đếm request và địa chỉ IP trong Redis]
    RecordNetwork --> IsAnomaly{Có trên 5 request từ nhiều hơn 1 IP?}
    IsAnomaly -->|Có| RevokeLicense
    IsAnomaly -->|Không| ClaimFingerprint[Gắn fingerprint và tăng lượt mở theo phép cập nhật nguyên tử]
    ClaimFingerprint --> FingerprintAccepted{Fingerprint được chấp nhận?}
    FingerprintAccepted -->|Không| Deny
    FingerprintAccepted -->|Có| WriteAudit[Ghi audit license_access_granted]
    WriteAudit --> End([Kết thúc: trả khóa AES đã bọc, quyền, profile và hạn dùng])
```

## 5. Workflow cấu hình bảo vệ bản quyền

```mermaid
flowchart TD
    Start([Bắt đầu: chủ tài liệu gửi cấu hình bảo vệ]) --> CheckEditRight[Kiểm tra quyền sửa tài liệu qua Content service]
    CheckEditRight --> CanEdit{Người dùng có quyền sửa?}
    CanEdit -->|Không| Deny([Kết thúc: trả lỗi 403])
    CanEdit -->|Có| WhichTier{Người dùng thuộc gói nào?}
    WhichTier -->|BASIC| ApplyBasic[Áp dụng profile chuẩn, không watermark và không khóa copy/print]
    WhichTier -->|PRO| ApplyPro[Áp dụng watermark, không ghost font và không khóa copy/print]
    WhichTier -->|PREMIUM hoặc ADMIN| ApplyPremium[Cho phép cấu hình bảo vệ đầy đủ và ghost font]
    ApplyBasic --> SaveSettings[Lưu cấu hình DRM hiệu lực]
    ApplyPro --> SaveSettings
    ApplyPremium --> PrivateLink{Có miễn trừ bằng liên kết riêng?}
    PrivateLink -->|Có| CreatePrivateToken[Tạo token một lần và chỉ lưu SHA-256]
    PrivateLink -->|Không| SaveSettings
    CreatePrivateToken --> SaveSettings
    SaveSettings --> SyncPolicy[Đồng bộ policy sang Content service]
    SyncPolicy --> Synced{Content service nhận policy thành công?}
    Synced -->|Không| SyncError([Kết thúc: trả lỗi đồng bộ])
    Synced -->|Có| End([Kết thúc: trả cấu hình bảo vệ hiệu lực])
```

## 6. Workflow tranh chấp bản quyền

```mermaid
flowchart TD
    Start([Bắt đầu: gửi yêu cầu giải quyết tranh chấp]) --> Authenticate[Kiểm tra JWT và session]
    Authenticate --> IsAdmin{Người xử lý có vai trò ADMIN?}
    IsAdmin -->|Không| Deny([Kết thúc: trả lỗi 403])
    IsAdmin -->|Có| FindDispute[Tra cứu tranh chấp theo mã]
    FindDispute --> Exists{Tranh chấp có tồn tại?}
    Exists -->|Không| NotFound([Kết thúc: trả lỗi 404])
    Exists -->|Có| ResolveDispute[Cập nhật kết luận, người xử lý và thời điểm giải quyết]
    ResolveDispute --> End([Kết thúc: trả kết quả đã giải quyết])
```

## 7. Workflow bảo vệ nội bộ

### 7.1 Bất thường mạng

```mermaid
flowchart TD
    Start([Bắt đầu: nhận người dùng và địa chỉ IP]) --> ValidateIP[Kiểm tra địa chỉ IP hợp lệ]
    ValidateIP --> ValidIP{IP có đúng định dạng?}
    ValidIP -->|Không| Invalid([Kết thúc: trả lỗi dữ liệu đầu vào])
    ValidIP -->|Có| CountRequests[Tăng bộ đếm request trong cửa sổ 60 giây]
    CountRequests --> RecordIP[Thêm IP vào tập địa chỉ của người dùng trong 60 giây]
    RecordIP --> IsAnomaly{Có trên 5 request từ nhiều hơn 1 IP?}
    IsAnomaly -->|Có| FlagAnomaly[Đặt cờ phát hiện bất thường]
    IsAnomaly -->|Không| ClearAnomaly[Giữ trạng thái truy cập bình thường]
    FlagAnomaly --> End([Kết thúc: trả kết quả kiểm tra])
    ClearAnomaly --> End
```

### 7.2 Trust score người dùng

```mermaid
flowchart TD
    Start([Bắt đầu: yêu cầu tính trust score]) --> LoadUser[Đọc trạng thái người dùng từ Humanity service]
    LoadUser --> IsActive{Tài khoản đang hoạt động?}
    IsActive -->|Không| SetZero[Đặt điểm cơ sở bằng 0]
    IsActive -->|Có| SetHundred[Đặt điểm cơ sở bằng 100]
    SetZero --> CountRevoked[Đếm license đã bị thu hồi]
    SetHundred --> CountRevoked
    CountRevoked --> DeductRevoked[Trừ điểm theo license bị thu hồi, tối đa 60]
    DeductRevoked --> CountDenied[Đếm audit truy cập bị từ chối]
    CountDenied --> DeductDenied[Trừ tiếp theo audit bị từ chối, tối đa 40]
    DeductDenied --> ClampScore[Giới hạn điểm cuối trong khoảng 0 đến 100]
    ClampScore --> End([Kết thúc: trả trust score và số liệu giải thích])
```

### 7.3 Risk score tài liệu

```mermaid
flowchart TD
    Start([Bắt đầu: yêu cầu tính risk score tài liệu]) --> LoadDocument[Đọc metadata tài liệu và cấu hình DRM]
    LoadDocument --> Exists{Tài liệu có tồn tại?}
    Exists -->|Không| NotFound([Kết thúc: trả lỗi không tìm thấy])
    Exists -->|Có| AddBaseRisk[Cộng điểm nếu tài liệu premium hoặc private]
    AddBaseRisk --> AddProtectionRisk[Cộng điểm theo các biện pháp bảo vệ đang bật]
    AddProtectionRisk --> CheckDisputes[Đếm tranh chấp bản quyền đang mở]
    CheckDisputes --> AddDisputeRisk[Cộng điểm theo số tranh chấp]
    AddDisputeRisk --> CheckRevoked[Đếm license đã bị thu hồi]
    CheckRevoked --> AddRevokedRisk[Cộng điểm theo số license bị thu hồi]
    AddRevokedRisk --> ClampRisk[Giới hạn tổng điểm tối đa 100]
    ClampRisk --> ClassifyRisk{Điểm thuộc mức nào?}
    ClassifyRisk -->|Thấp| Low([Kết thúc: trả mức LOW])
    ClassifyRisk -->|Trung bình| Medium([Kết thúc: trả mức MEDIUM])
    ClassifyRisk -->|Cao| High([Kết thúc: trả mức HIGH])
```

## 8. Workflow đánh giá policy với Agentic AI

```mermaid
flowchart TD
    Start([Bắt đầu: DRM yêu cầu đánh giá trước khi kết xuất]) --> SendContext[Gửi người dùng, tài liệu, IP và tier sang Agentic AI]
    SendContext --> ApplyRules[Áp dụng các luật bảo vệ xác định trước]
    ApplyRules --> NeedAI{Mức rủi ro có cần LLM đánh giá thêm?}
    NeedAI -->|Không| ReturnRules[Giữ kết quả từ luật xác định]
    NeedAI -->|Có| AskModel[Yêu cầu LLM trả DRMPolicyOutput có cấu trúc]
    AskModel --> ValidOutput{Model trả cấu trúc hợp lệ?}
    ValidOutput -->|Không| ReturnRules
    ValidOutput -->|Có| MergeDecision[Kết hợp đánh giá model với giới hạn an toàn]
    ReturnRules --> ReturnPolicy[Trả quyết định và các cờ watermark, micro-dot, AES]
    MergeDecision --> ReturnPolicy
    ReturnPolicy --> IsBlocked{Quyết định cuối có phải BLOCKED?}
    IsBlocked -->|Có| Block([Kết thúc: DRM từ chối kết xuất])
    IsBlocked -->|Không| Continue([Kết thúc: DRM tiếp tục workflow kết xuất])
```

## 9. Công nghệ đang sử dụng

| Lớp               | Công nghệ                                              | Vai trò thực tế                                     |
| ------------------ | -------------------------------------------------------- | ------------------------------------------------------ |
| API                | Python 3.11, FastAPI, Uvicorn, Pydantic                  | HTTP API, validation, dependency injection             |
| Xác thực         | PyJWT, OAuth2 bearer, HMAC compare                       | JWT HS256, session và internal token                  |
| Mật mã           | `cryptography`, RSA-OAEP SHA-256, AES-256-GCM, SHA-256 | Bọc khóa, mã hóa file, fingerprint/hash            |
| PDF/watermark      | PyMuPDF`fitz`, zero-width characters, micro-dot        | Đóng watermark hiển thị, ẩn và truy vết         |
| Dữ liệu          | MongoDB, Motor, PyMongo                                  | License, policy, dispute và audit                     |
| Trạng thái nhanh | Redis asyncio                                            | Session, rate limit, anomaly window và key TTL        |
| Giao tiếp service | HTTPX                                                    | Content, Finance, Humanity, Compilation và Agentic AI |
| Quan sát          | Loguru, Prometheus middleware, trace ID                  | Log nghiệp vụ, metrics và correlation               |
| Triển khai        | Docker Compose, Traefik                                  | Container, health check và route theo prefix          |

## 10. API và quyền truy cập

| Prefix                                | Endpoint chính                                          | Quyền                                        |
| ------------------------------------- | -------------------------------------------------------- | --------------------------------------------- |
| `/giay-phep`                        | kiểm tra, thu hồi                                      | JWT; chủ license hoặc ADMIN tùy thao tác  |
| `/thuy-an`                          | kết xuất, giải mã truy vết                          | JWT; giải mã truy vết yêu cầu ADMIN      |
| `/ban-quyen`                        | cập nhật policy, giải quyết dispute                  | Chủ tài liệu; giải quyết yêu cầu ADMIN |
| `/bao-ve`                           | anomaly, trust, risk, key, fingerprint, internal content | `X-Internal-Token`                          |
| `/health`, `/ready`, `/metrics` | liveness, dependency readiness, metrics                  | Vận hành                                    |
