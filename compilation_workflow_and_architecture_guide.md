# Compilation — kiến trúc, workflow và EditorJS tùy biến

## 1. Kiến trúc tổng thể

```mermaid
flowchart LR
    User[Người dùng] --> Workspace[EditorWorkspace]

    subgraph Frontend[Next.js frontend]
        Workspace --> Standard[StandardEditor cho doclib]
        Workspace --> LatexUI[LatexEditor cho doclibx]
        Standard --> CoreTools[Block cốt lõi trong tools]
        Standard --> Palette[DocumentCommandPalette]
        Palette --> CommandEngine[document-command-engine]
        Workspace --> Preview[Client preview hoặc PDF iframe]
    end

    subgraph Compilation[FastAPI compilation]
        EditorAPI[EditorJS API]
        LatexAPI[LaTeX API]
        ComposeAPI[Composition API]
        EditorEngine[EditorjsEngine]
        LatexEngine[LatexEngine]
        Capability[Capability manifest]
    end

    Standard --> EditorAPI
    LatexUI --> LatexAPI
    Workspace --> ComposeAPI
    EditorAPI --> EditorEngine
    LatexAPI --> LatexEngine
    EditorEngine --> Capability

    EditorEngine --> Weasy[WeasyPrint]
    EditorEngine --> Pandoc[Pandoc]
    LatexEngine --> Tectonic[Tectonic]
    LatexEngine --> Pandoc

    ComposeAPI --> Content[Content service]
    ComposeAPI --> Mongo[(MongoDB)]
    ComposeAPI --> Redis[(Redis)]
    EditorEngine -. kiểm tra URL ảnh .-> MinIO[(MinIO)]
```

## 2. Workflow chọn trình soạn thảo ở frontend

```mermaid
flowchart TD
    Start([Bắt đầu: người dùng mở một tài liệu]) --> LoadDocument[Đọc metadata và nội dung nháp từ Content service]
    LoadDocument --> Loaded{Tải tài liệu thành công?}
    Loaded -->|Không| LoadError([Kết thúc: hiển thị lỗi tải tài liệu])
    Loaded -->|Có| NormalizeFormat[Chuẩn hóa json thành doclib và latex thành doclibx]
    NormalizeFormat --> WhichFormat{Tài liệu dùng định dạng nào?}
    WhichFormat -->|doclib| OpenEditorJS[Khởi tạo StandardEditor bằng dữ liệu EditorJS JSON]
    WhichFormat -->|doclibx| OpenLatex[Mở LatexEditor bằng mã nguồn LaTeX]
    OpenEditorJS --> EditorMode{Người dùng chọn chế độ nào?}
    EditorMode -->|Soạn thảo| EditBlocks[Hiển thị EditorJS và các block DocLib]
    EditorMode -->|Xem trước| RenderClient[Render bản xem trước EditorJS ở frontend]
    EditorMode -->|Dữ liệu JSON| ShowJSON[Hiển thị source JSON]
    OpenLatex --> LatexMode{Người dùng chọn chế độ nào?}
    LatexMode -->|Mã LaTeX| EditLatex[Hiển thị trình sửa mã nguồn]
    LatexMode -->|Xem PDF| CompilePreview[Gửi mã nguồn sang compilation để tạo PDF]
    EditBlocks --> End([Kết thúc: trình soạn thảo sẵn sàng])
    RenderClient --> End
    ShowJSON --> End
    EditLatex --> End
    CompilePreview --> End
```

## 3. Workflow nạp block DocLib cốt lõi vào EditorJS

```mermaid
flowchart TD
    Start([Bắt đầu: React mount StandardEditor]) --> CreateHolder[Tạo holder cho EditorJS]
    CreateHolder --> ImportEditor[Nạp EditorJS ở phía trình duyệt]
    ImportEditor --> ImportTools[Nạp song song các block và tune DocLib cốt lõi]
    ImportTools --> ImportsOK{Tất cả module bắt buộc nạp thành công?}
    ImportsOK -->|Không| InitError([Kết thúc: editor không khởi tạo])
    ImportsOK -->|Có| BuildToolMap[Ánh xạ tool key sang class, toolbar và tune]
    BuildToolMap --> ParseInitial[Parse và sanitize nội dung ban đầu]
    ParseInitial --> ValidJSON{Nội dung có EditorJS blocks hợp lệ?}
    ValidJSON -->|Không| ConvertText[Chuyển từng dòng văn bản thành paragraph]
    ValidJSON -->|Có| CreateEditor[Khởi tạo EditorJS với tools đã đăng ký]
    ConvertText --> CreateEditor
    CreateEditor --> RestoreState[Khôi phục documentCommandState nếu có]
    RestoreState --> Ready{Editor báo isReady?}
    Ready -->|Không| InitError
    Ready -->|Có| End([Kết thúc: cho phép người dùng soạn thảo])
```

## 4. Workflow tạo và đưa command DocLib vào frontend

### 4.1 Hai lớp mở rộng khác nhau

| Lớp                 | Cách tích hợp                                                     | Trạng thái runtime hiện tại                                                 |
| -------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Block/tune cốt lõi | Import và khai báo trực tiếp trong`StandardEditor.tools`       | 32 module được nạp khi mở editor                                           |
| Document command     | File`DocLib*.ts` + generated JSON + command palette + event bridge | 2.296 command trong catalog; 26 command đã được hiển thị có chủ đích |
| Capability manifest  | Metadata đồng bộ frontend/backend                                 | 2.449 feature; backend dùng để tra cứu và xác minh command block          |

Không nên gọi cả 2.449 feature là “EditorJS tools đang được nạp”. Phần lớn là
khả năng/command độc lập; chỉ module nằm trong `tools` mới là tool khởi tạo cùng
EditorJS.

### 4.2 Quy trình build catalog command

```mermaid
flowchart TD
    Start([Bắt đầu: thêm hoặc sửa file DocLib command]) --> ImplementContract[Triển khai id, title, category, mode, render, save, validate và execute]
    ImplementContract --> GenerateCatalog[Chạy generate:document-commands]
    GenerateCatalog --> ScanFiles[Quét các file DocLib TS có mode và execute]
    ScanFiles --> PreserveType[Giữ loại thực thi direct hoặc bridge từ catalog hiện tại]
    PreserveType --> WriteCatalog[Ghi document-command-catalog.generated.json]
    WriteCatalog --> RunAudit[Chạy audit:document-commands]
    RunAudit --> ValidCatalog{ID, file, class và event bridge đều hợp lệ?}
    ValidCatalog -->|Không| FixCommand[Chỉnh file command hoặc metadata]
    FixCommand --> GenerateCatalog
    ValidCatalog -->|Có| BuildFrontend[Chạy type-check và build Next.js]
    BuildFrontend --> BuildOK{Frontend build thành công?}
    BuildOK -->|Không| FixCommand
    BuildOK -->|Có| End([Kết thúc: command đủ điều kiện đưa vào giao diện])
```

## 5. Workflow thực thi một command trong EditorJS

```mermaid
flowchart TD
    Start([Bắt đầu: người dùng mở Chức năng tài liệu]) --> LoadCatalog[Đọc generated command catalog]
    LoadCatalog --> FilterCommands[Lọc command có nhãn tiếng Việt và được phép hiển thị]
    FilterCommands --> SelectCommand[Người dùng tìm và chọn một command]
    SelectCommand --> NeedSelection{Command có yêu cầu chọn nội dung?}
    NeedSelection -->|Có| HasSelection{Người dùng đã chọn nội dung?}
    HasSelection -->|Không| SelectionError([Kết thúc: yêu cầu chọn nội dung trước])
    HasSelection -->|Có| ImportCommand[Nạp động class DocLib tương ứng]
    NeedSelection -->|Không| ImportCommand
    ImportCommand --> RegisterEvents[Đăng ký tạm các event bridge DocLib]
    RegisterEvents --> ExecuteCommand[Gọi execute của command]
    ExecuteCommand --> EventHandled{Command đã tạo hiệu ứng trực tiếp hoặc qua bridge?}
    EventHandled -->|Không| CommandError([Kết thúc: hiển thị lỗi command])
    EventHandled -->|Có| UpdateState[Cập nhật mode, enabled và appliedAt]
    UpdateState --> SaveEditor[Đính documentCommandState vào EditorJS output]
    SaveEditor --> End([Kết thúc: lưu tài liệu và thông báo kết quả])
```

## 6. Workflow lưu tài liệu EditorJS

```mermaid
flowchart TD
    Start([Bắt đầu: người dùng thay đổi một block]) --> Debounce[Chờ 300 ms để gom thay đổi trong StandardEditor]
    Debounce --> SaveEditorJS[Gọi editor.save]
    SaveEditorJS --> AttachState[Đính trạng thái document command]
    AttachState --> Sanitize[Sanitize toàn bộ EditorJS output]
    Sanitize --> ValidOutput{Dữ liệu sau sanitize hợp lệ?}
    ValidOutput -->|Không| SaveError([Kết thúc: hiển thị trạng thái Chưa lưu])
    ValidOutput -->|Có| ComputeStats[Tính số từ, số ký tự, thời gian đọc và mục lục]
    ComputeStats --> UpdateContent[Cập nhật content trong React state]
    UpdateContent --> WaitAutosave[Chờ 1.600 ms ở workspace]
    WaitAutosave --> SendDraft[Gửi content và content_format sang Content service]
    SendDraft --> Saved{Content service lưu thành công?}
    Saved -->|Không| SaveError
    Saved -->|Có| End([Kết thúc: hiển thị trạng thái Đã lưu])
```

## 7. Workflow biên dịch và kết xuất EditorJS

```mermaid
flowchart TD
    Start([Bắt đầu: nhận EditorJS JSON và định dạng đích]) --> Authenticate[Kiểm tra JWT, session và rate limit]
    Authenticate --> CheckSize[Kiểm tra kích thước request]
    CheckSize --> ParseJSON[Parse JSON và lấy danh sách blocks]
    ParseJSON --> ValidBlocks{Có từ 1 đến 5.000 block đúng schema?}
    ValidBlocks -->|Không| Invalid([Kết thúc: trả lỗi 400])
    ValidBlocks -->|Có| ValidateCommands[Xác minh command block theo capability manifest]
    ValidateCommands --> CommandsValid{Metadata feature, mode và applied có khớp manifest?}
    CommandsValid -->|Không| Invalid
    CommandsValid -->|Có| RenderBlocks[Sanitize và chuyển từng content block thành HTML]
    RenderBlocks --> Target{Người dùng xuất định dạng nào?}
    Target -->|PDF| RunWeasyPrint[Chạy WeasyPrint trong thư mục tạm]
    Target -->|DOCX hoặc HTML| RunPandoc[Chạy Pandoc từ HTML trung gian]
    RunWeasyPrint --> ProcessOK{Tiến trình hoàn tất trong 30 giây?}
    RunPandoc --> ProcessOK
    ProcessOK -->|Không| CompileError([Kết thúc: trả lỗi biên dịch])
    ProcessOK -->|Có| CheckOutput[Kiểm tra tệp tồn tại và kích thước đầu ra]
    CheckOutput --> ValidOutput{Tệp kết quả hợp lệ?}
    ValidOutput -->|Không| CompileError
    ValidOutput -->|Có| End([Kết thúc: trả PDF, DOCX hoặc HTML])
```

## 8. Workflow biên dịch và kết xuất LaTeX

```mermaid
flowchart TD
    Start([Bắt đầu: nhận mã nguồn LaTeX và định dạng đích]) --> Authenticate[Kiểm tra JWT, session và rate limit nếu endpoint yêu cầu]
    Authenticate --> ValidateSize[Kiểm tra nội dung không rỗng và không vượt giới hạn]
    ValidateSize --> ScanDangerous[Quét input, include, write18, URL và chỉ thị nguy hiểm]
    ScanDangerous --> SafeSource{Mã nguồn an toàn?}
    SafeSource -->|Không| Reject([Kết thúc: trả lỗi cú pháp hoặc bảo mật])
    SafeSource -->|Có| Target{Người dùng yêu cầu kết quả nào?}
    Target -->|PDF| WriteTex[Tạo main.tex trong thư mục tạm]
    WriteTex --> RunTectonic[Chạy Tectonic với chế độ untrusted]
    Target -->|DOCX hoặc HTML| RunPandoc[Chạy Pandoc từ mã nguồn TeX]
    Target -->|Project ZIP| BuildZip[Tạo main.tex, README và gitignore trong ZIP]
    RunTectonic --> ProcessOK{Tiến trình hoàn tất trong 30 giây?}
    RunPandoc --> ProcessOK
    ProcessOK -->|Không| CompileError([Kết thúc: trả lỗi biên dịch])
    ProcessOK -->|Có| CheckOutput[Kiểm tra tệp và kích thước đầu ra]
    BuildZip --> CheckOutput
    CheckOutput --> ValidOutput{Kết quả hợp lệ?}
    ValidOutput -->|Không| CompileError
    ValidOutput -->|Có| End([Kết thúc: trả PDF, DOCX, HTML hoặc ZIP])
```

Tectonic dùng cache volume riêng. Compilation không chạy `shell-escape`, không
cho LaTeX đọc file tùy ý và không cho tải tài nguyên qua URL từ source.

## 9. Workflow giới hạn tiến trình biên dịch

```mermaid
flowchart TD
    Start([Bắt đầu: engine cần chạy công cụ hệ thống]) --> WaitSlot[Chờ một slot trong semaphore biên dịch]
    WaitSlot --> CreateProcess[Khởi chạy process trong session riêng]
    CreateProcess --> ApplyLimits[Giới hạn CPU, RAM, kích thước file, file descriptor và process con]
    ApplyLimits --> WaitResult[Đọc stdout và stderr với giới hạn bộ đệm]
    WaitResult --> Finished{Process kết thúc trong 30 giây?}
    Finished -->|Không| KillGroup[Dừng toàn bộ process group]
    KillGroup --> Timeout([Kết thúc: trả lỗi timeout])
    Finished -->|Có| ExitOK{Exit code bằng 0?}
    ExitOK -->|Không| ProcessError([Kết thúc: trả phần cuối stderr])
    ExitOK -->|Có| ReleaseSlot[Giải phóng slot biên dịch]
    ReleaseSlot --> End([Kết thúc: chuyển sang bước kiểm tra tệp])
```

## 10. Workflow cộng tác và xét duyệt

```mermaid
flowchart TD
    Start([Bắt đầu: người dùng thực hiện thao tác cộng tác]) --> CheckAccess[Kiểm tra quyền đọc hoặc sửa qua Content service]
    CheckAccess --> Allowed{Người dùng có quyền tương ứng?}
    Allowed -->|Không| Deny([Kết thúc: trả lỗi 403 hoặc 404])
    Allowed -->|Có| Action{Người dùng thực hiện thao tác nào?}
    Action -->|Gõ phím| PublishKeystroke[Publish keystroke qua Redis và lưu snapshot 1 giờ]
    Action -->|Gợi ý| SaveSuggestion[Lưu gợi ý pending trong MongoDB]
    Action -->|Bình luận| SaveComment[Lưu bình luận theo block trong MongoDB]
    Action -->|Tìm và thay thế| UpdateContent[Cập nhật nội dung qua Content service và tạo snapshot]
    Action -->|Gửi xét duyệt| SubmitReview[Đổi trạng thái tài liệu sang pending_review]
    Action -->|So sánh phiên bản| LoadVersions[Đọc hai version snapshot từ Content service]
    PublishKeystroke --> End([Kết thúc: trả trạng thái thao tác])
    SaveSuggestion --> End
    SaveComment --> End
    UpdateContent --> End
    SubmitReview --> End
    LoadVersions --> End
```

## 11. API hiện hành

| Nhóm       | Endpoint chính                                               | Chức năng                                                       |
| ----------- | ------------------------------------------------------------- | ----------------------------------------------------------------- |
| EditorJS    | `/soan-thao/editorjs/bien-dich`                             | EditorJS → PDF                                                   |
| EditorJS    | `/soan-thao/editorjs/ket-xuat/{format}`                     | EditorJS → PDF, DOCX hoặc HTML                                  |
| Capability  | `/soan-thao/editorjs/capabilities`                          | Tìm và phân trang feature manifest                             |
| LaTeX       | `/soan-thao/latex/bien-dich`                                | LaTeX → PDF                                                      |
| LaTeX       | `/soan-thao/latex/ket-xuat/{format}`                        | LaTeX → PDF, DOCX hoặc HTML                                     |
| LaTeX       | `/soan-thao/latex/dinh-dang`                                | Chuẩn hóa thụt dòng LaTeX                                     |
| LaTeX       | `/soan-thao/latex/ket-xuat-zip`                             | Tạo project ZIP                                                  |
| LaTeX draft | `/soan-thao/latex/tu-dong-luu`, `/ban-nhap`, `/don-dep` | Lưu, đọc và xóa draft trong Redis                            |
| Composition | `/soan-thao/{document_id}/*`                                | Autosave, keystroke, review, comment, suggestion và version diff |
| Vận hành  | `/health`, `/ready`, `/metrics`                         | Liveness, Mongo/Redis readiness và metrics                       |

## 12. Công nghệ đang sử dụng

| Lớp               | Công nghệ                                                       | Vai trò thực tế                                                   |
| ------------------ | ----------------------------------------------------------------- | -------------------------------------------------------------------- |
| Frontend           | Next.js, React, TypeScript                                        | Workspace, trạng thái editor, lazy loading và tải tệp           |
| Trình soạn thảo | Editor.js, DocLib BlockTool/InlineTool/BlockTune                  | Soạn`.doclib` theo block                                          |
| Command runtime    | Dynamic import, CustomEvent, DOM Selection,`execCommand` bridge | Nạp và thực thi command tài liệu                                |
| Catalog            | JSON manifest, Node.js generator, Python bulk generator           | Đồng bộ feature và command metadata                              |
| API                | Python 3.11, FastAPI, Uvicorn, Pydantic                           | HTTP API, schema và dependency injection                            |
| EditorJS render    | Bleach, HTML/CSS, WeasyPrint                                      | Sanitize block và tạo PDF                                          |
| Chuyển đổi      | Pandoc                                                            | EditorJS/LaTeX sang DOCX hoặc HTML                                  |
| LaTeX              | Tectonic 0.15 ở chế độ untrusted                              | Biên dịch`.doclibx` thành PDF                                   |
| Dữ liệu          | MongoDB, Motor, Redis                                             | Comment, suggestion, Pomodoro, draft, rate limit và realtime buffer |
| Giao tiếp         | HTTPX                                                             | Đọc quyền/nội dung và cập nhật Content service                |
| Bảo mật          | PyJWT, Bleach, URL allowlist, RLIMIT, timeout, semaphore          | Xác thực và cô lập tiến trình biên dịch                     |
| Quan sát          | Loguru, Prometheus middleware, trace ID                           | Log, metrics và correlation                                         |
| Triển khai        | Docker Compose, Traefik, non-root container                       | Route`/soan-thao`, health check và runtime tools                  |
