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

### Ranh giới dữ liệu

| Thành phần             | Dữ liệu chịu trách nhiệm                                                          |
| ------------------------ | -------------------------------------------------------------------------------------- |
| Content service          | Tài liệu, nội dung nháp, trạng thái xuất bản và version snapshot              |
| MongoDB của compilation | Gợi ý chỉnh sửa, bình luận và phiên Pomodoro                                   |
| Redis                    | Session, rate limit, LaTeX draft, keystroke snapshot và pub/sub                       |
| MinIO                    | Nguồn ảnh được phép khi EditorJS render; compilation không tự quản lý object |
| Thư mục tạm           | `main.tex`, HTML trung gian và tệp kết xuất; xóa khi request kết thúc         |

## 3. Workflow chọn trình soạn thảo ở frontend

Frontend chuẩn hóa định dạng cũ `json → doclib` và `latex → doclibx` trước khi
chọn giao diện.

```mermaid
flowchart TD
    Start([Bắt đầu mở tài liệu]) --> LoadDocument[Đọc thông tin và nội dung bản nháp]
    LoadDocument --> Loaded{Tải tài liệu thành công}
    Loaded -->|Không| LoadError([Kết thúc hiển thị lỗi tải tài liệu])
    Loaded -->|Có| NormalizeFormat[Nhận diện loại tài liệu]
    NormalizeFormat --> WhichFormat{Tài liệu thuộc loại nào}
    WhichFormat -->|Tài liệu thường| OpenEditorJS[Mở trình soạn thảo nội dung]
    WhichFormat -->|Tài liệu công thức| OpenLatex[Mở trình soạn thảo công thức]
    OpenEditorJS --> EditorMode{Người dùng chọn chế độ nào}
    EditorMode -->|Soạn thảo| EditBlocks[Hiển thị nội dung theo từng khối]
    EditorMode -->|Xem trước| RenderClient[Hiển thị bản xem trước]
    EditorMode -->|Dữ liệu gốc| ShowJSON[Hiển thị dữ liệu gốc của tài liệu]
    OpenLatex --> LatexMode{Người dùng chọn chế độ nào}
    LatexMode -->|Soạn công thức| EditLatex[Hiển thị trình sửa nội dung công thức]
    LatexMode -->|Xem PDF| CompilePreview[Tạo bản PDF để xem trước]
    EditBlocks --> End([Kết thúc trình soạn thảo sẵn sàng])
    RenderClient --> End
    ShowJSON --> End
    EditLatex --> End
    CompilePreview --> End
```

`.doclib` là EditorJS JSON; `.doclibx` là LaTeX source. Hai loại tài liệu dùng
chung workspace nhưng không dùng chung editor hoặc định dạng nội dung.

## 4. Workflow nạp block DocLib cốt lõi vào EditorJS

`StandardEditor.tsx` hiện dynamic-import 31 module cốt lõi đã có hành vi, sau đó đăng ký chúng
trong `tools` của EditorJS. Đây mới là nhóm block/tune thực sự được nạp khi editor
khởi tạo; không phải toàn bộ 2.449 file `DocLib*`.

```mermaid
flowchart TD
    Start([Bắt đầu chuẩn bị trình soạn thảo]) --> CreateHolder[Tạo vùng hiển thị nội dung]
    CreateHolder --> ImportEditor[Nạp bộ soạn thảo trên trình duyệt]
    ImportEditor --> ImportTools[Nạp các công cụ soạn thảo đã được kiểm tra]
    ImportTools --> ImportsOK{Tất cả công cụ bắt buộc đã nạp thành công}
    ImportsOK -->|Không| InitError([Kết thúc không thể mở trình soạn thảo])
    ImportsOK -->|Có| BuildToolMap[Đăng ký công cụ vào đúng vị trí sử dụng]
    BuildToolMap --> ParseInitial[Kiểm tra và làm sạch nội dung ban đầu]
    ParseInitial --> ValidJSON{Nội dung có cấu trúc hợp lệ}
    ValidJSON -->|Không| ConvertText[Chuyển văn bản thường thành các đoạn]
    ValidJSON -->|Có| CreateEditor[Khởi tạo trình soạn thảo với công cụ đã đăng ký]
    ConvertText --> CreateEditor
    CreateEditor --> RestoreState[Khôi phục documentCommandState nếu có]
    RestoreState --> Ready{Trình soạn thảo đã sẵn sàng}
    Ready -->|Không| InitError
    Ready -->|Có| End([Kết thúc cho phép người dùng soạn thảo])
```

Nhóm cốt lõi gồm paragraph, header, list, checklist, table, quote, code, raw,
delimiter, image, file, alert, toggle, math, Mermaid, embed, các inline tool,
alignment/indent, shape, video, audio, AI text, form, macro, label và citation.

## 5. Workflow tạo và đưa command DocLib vào frontend

### 5.1 Hai lớp mở rộng khác nhau

| Lớp                 | Cách tích hợp                                                     | Trạng thái runtime hiện tại                                                 |
| -------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Block/tune cốt lõi | Import và khai báo trực tiếp trong`StandardEditor.tools`       | 31 module được nạp khi mở editor; MacroButton giả lập không được đăng ký    |
| Chức năng tài liệu   | Danh sách sinh tự động và bộ thực thi đã xác minh                  | 2.296 chức năng trong danh sách và 55 chức năng đã được hiển thị           |
| Capability manifest  | Metadata đồng bộ frontend/backend                                 | 2.449 feature; backend dùng để tra cứu và xác minh command block          |

Không nên gọi cả 2.449 feature là “EditorJS tools đang được nạp”. Phần lớn là
khả năng/command độc lập; chỉ module nằm trong `tools` mới là tool khởi tạo cùng
EditorJS.

### 5.2 Quy trình build catalog command

```mermaid
flowchart TD
    Start([Bắt đầu thêm hoặc sửa một chức năng]) --> ImplementContract[Viết đầy đủ cách hiển thị lưu kiểm tra và thực hiện]
    ImplementContract --> GenerateCatalog[Tạo lại danh sách chức năng]
    GenerateCatalog --> ScanFiles[Kiểm tra các tệp chức năng]
    ScanFiles --> PreserveType[Ghi nhận cách thực hiện của từng chức năng]
    PreserveType --> WriteCatalog[Lưu danh sách chức năng mới]
    WriteCatalog --> RunAudit[Chạy bộ kiểm tra tự động]
    RunAudit --> ValidCatalog{Mã chức năng tệp và hành vi có khớp nhau}
    ValidCatalog -->|Không| FixCommand[Sửa chức năng hoặc thông tin mô tả]
    FixCommand --> GenerateCatalog
    ValidCatalog -->|Có| BuildFrontend[Kiểm tra kiểu dữ liệu và tạo bản chạy giao diện]
    BuildFrontend --> BuildOK{Giao diện được tạo thành công}
    BuildOK -->|Không| FixCommand
    BuildOK -->|Có| End([Kết thúc chức năng đủ điều kiện đưa vào giao diện])
```

`prebuild` hiện chạy audit nhưng **không tự generate catalog**. Vì vậy sau khi
thêm command phải chạy generate trước; nếu chỉ chạy build, catalog cũ vẫn có thể
được audit mà chưa chứa command mới.

Script [`rebuild_word_feature_catalog.py`](scripts/rebuild_word_feature_catalog.py)
là đường tạo hàng loạt từ spreadsheet: sinh file class, metadata, icon và hai
manifest frontend/backend. Script này không phải bước tự động trong frontend
build hiện tại.

## 6. Workflow thực thi một command trong EditorJS

`DocumentCommandPalette` chỉ hiển thị command có nhãn tiếng Việt, mang
`implementation: direct` và nằm trong `verifiedInteractiveCommands`. Catalog có
2.296 command, nhưng giao diện hiện chỉ công khai 55 command đã có hành vi thật.
Tám command cấp tài liệu có hiệu ứng bền vững còn phải đồng bộ tuyệt đối với
`VERIFIED_DOCUMENT_COMMANDS` của compilation service trước khi Agentic AI được
phép gọi.

```mermaid
flowchart TD
    Start([Bắt đầu mở danh sách chức năng]) --> LoadCatalog[Đọc danh sách chức năng]
    LoadCatalog --> FilterCommands[Chỉ giữ chức năng tiếng Việt đã kiểm tra hành vi]
    FilterCommands --> SelectCommand[Người dùng tìm và chọn chức năng]
    SelectCommand --> NeedSelection{Chức năng có yêu cầu chọn nội dung}
    NeedSelection -->|Có| HasSelection{Người dùng đã chọn nội dung}
    HasSelection -->|Không| SelectionError([Kết thúc yêu cầu chọn nội dung trước])
    HasSelection -->|Có| Persistent{Chức năng có thay đổi bố cục toàn tài liệu}
    NeedSelection -->|Không| Persistent
    Persistent -->|Có| UpdateState[Cập nhật và áp dụng thiết lập bố cục]
    Persistent -->|Không| ExecuteCommand[Chạy hàm thực hiện đã được xác minh]
    ExecuteCommand --> EventHandled{Chức năng đã tạo đúng thay đổi}
    EventHandled -->|Không| CommandError([Kết thúc hiển thị lỗi chức năng])
    EventHandled -->|Có| SaveEditor[Lưu nội dung đã thay đổi]
    UpdateState --> SaveEditor
    SaveEditor --> End([Kết thúc lưu tài liệu và hiện thông báo kết quả])
```

Bridge hiện ánh xạ một số mode sang `document.execCommand`, zoom, line spacing
hoặc page break. Đường ghi `data-document-mode` và thông báo thành công chung đã
bị loại bỏ. Command chưa có handler và chưa vượt audit bị chặn ngay cả khi file
class hoặc record catalog vẫn tồn tại.

## 7. Workflow lưu tài liệu EditorJS

```mermaid
flowchart TD
    Start([Bắt đầu người dùng thay đổi nội dung]) --> Debounce[Chờ một khoảng ngắn để gom thay đổi]
    Debounce --> SaveEditorJS[Đọc toàn bộ nội dung hiện tại]
    SaveEditorJS --> AttachState[Đính kèm thiết lập bố cục]
    AttachState --> Sanitize[Kiểm tra và làm sạch dữ liệu]
    Sanitize --> ValidOutput{Dữ liệu sau khi làm sạch có hợp lệ}
    ValidOutput -->|Không| SaveError([Kết thúc hiển thị trạng thái chưa lưu])
    ValidOutput -->|Có| ComputeStats[Tính số từ số ký tự thời gian đọc và mục lục]
    ComputeStats --> UpdateContent[Cập nhật nội dung trên giao diện]
    UpdateContent --> WaitAutosave[Chờ để tránh gửi quá nhiều lần]
    WaitAutosave --> SendDraft[Gửi bản nháp sang nơi lưu tài liệu]
    SendDraft --> Saved{Bản nháp đã được lưu thành công}
    Saved -->|Không| SaveError
    Saved -->|Có| End([Kết thúc hiển thị trạng thái đã lưu])
```

Composition API còn có luồng `/soan-thao/{document_id}/tu-dong-luu` riêng để
kiểm tra tối đa 5.000 block, tạo mục lục/thời gian đọc và cập nhật Content bằng
internal token.

## 8. Workflow biên dịch và kết xuất EditorJS

```mermaid
flowchart TD
    Start([Bắt đầu tạo tệp từ tài liệu thường]) --> Authenticate[Kiểm tra đăng nhập và giới hạn sử dụng]
    Authenticate --> CheckSize[Kiểm tra dung lượng nội dung gửi lên]
    CheckSize --> ParseJSON[Đọc danh sách khối nội dung]
    ParseJSON --> ValidBlocks{Số lượng và cấu trúc khối có hợp lệ}
    ValidBlocks -->|Không| Invalid([Kết thúc báo dữ liệu không hợp lệ])
    ValidBlocks -->|Có| ValidateCommands[Kiểm tra từng chức năng đã dùng trong tài liệu]
    ValidateCommands --> CommandsValid{Thông tin chức năng có khớp danh sách được phép}
    CommandsValid -->|Không| Invalid
    CommandsValid -->|Có| RenderBlocks[Làm sạch và chuyển từng khối thành nội dung có thể xuất]
    RenderBlocks --> Target{Người dùng muốn nhận loại tệp nào}
    Target -->|PDF| RunWeasyPrint[Tạo tệp PDF trong vùng xử lý tạm]
    Target -->|Tài liệu Word| RunPandoc[Tạo tệp Word từ nội dung trung gian]
    Target -->|Trang web| ReturnHTML[Giữ nguyên nội dung và kiểu trình bày đã tạo]
    RunWeasyPrint --> ProcessOK{Việc tạo tệp hoàn tất đúng thời gian}
    RunPandoc --> ProcessOK
    ReturnHTML --> CheckOutput
    ProcessOK -->|Không| CompileError([Kết thúc báo không thể tạo tệp])
    ProcessOK -->|Có| CheckOutput[Kiểm tra tệp tồn tại và dung lượng phù hợp]
    CheckOutput --> ValidOutput{Tệp kết quả có hợp lệ}
    ValidOutput -->|Không| CompileError
    ValidOutput -->|Có| End([Kết thúc trả tệp theo định dạng đã chọn])
```

Command block nằm trong capability manifest được xác minh nhưng không render như
nội dung tài liệu. Các block nội dung không nhận diện hoặc không hợp lệ bị bỏ qua
và ghi warning thay vì thực thi mã tùy ý.

## 9. Workflow biên dịch và kết xuất LaTeX

```mermaid
flowchart TD
    Start([Bắt đầu tạo tệp từ tài liệu công thức]) --> Authenticate[Kiểm tra đăng nhập và giới hạn sử dụng]
    Authenticate --> ValidateSize[Kiểm tra nội dung không rỗng và không vượt giới hạn]
    ValidateSize --> ScanDangerous[Kiểm tra lệnh đọc ghi và liên kết không an toàn]
    ScanDangerous --> SafeSource{Nội dung có an toàn}
    SafeSource -->|Không| Reject([Kết thúc báo nội dung không hợp lệ hoặc không an toàn])
    SafeSource -->|Có| Target{Người dùng muốn nhận loại tệp nào}
    Target -->|PDF| WriteTex[Tạo tệp nguồn trong vùng xử lý tạm]
    WriteTex --> RunTectonic[Tạo PDF trong chế độ hạn chế quyền]
    Target -->|Tài liệu Word hoặc trang web| RunPandoc[Chuyển nội dung sang định dạng đã chọn]
    Target -->|Gói dự án| BuildZip[Đóng gói tệp nguồn và hướng dẫn sử dụng]
    RunTectonic --> ProcessOK{Việc tạo tệp hoàn tất đúng thời gian}
    RunPandoc --> ProcessOK
    ProcessOK -->|Không| CompileError([Kết thúc báo không thể tạo tệp])
    ProcessOK -->|Có| CheckOutput[Kiểm tra tệp và dung lượng đầu ra]
    BuildZip --> CheckOutput
    CheckOutput --> ValidOutput{Kết quả có hợp lệ}
    ValidOutput -->|Không| CompileError
    ValidOutput -->|Có| End([Kết thúc trả tệp theo định dạng đã chọn])
```

Tectonic dùng cache volume riêng. Compilation không chạy `shell-escape`, không
cho LaTeX đọc file tùy ý và không cho tải tài nguyên qua URL từ source.

## 10. Workflow giới hạn tiến trình biên dịch

EditorJS và LaTeX dùng chung semaphore và hàm chạy subprocess.

```mermaid
flowchart TD
    Start([Bắt đầu chạy công cụ tạo tệp]) --> WaitSlot[Chờ đến lượt xử lý]
    WaitSlot --> CreateProcess[Khởi chạy công cụ trong vùng riêng]
    CreateProcess --> ApplyLimits[Giới hạn tài nguyên và quyền truy cập]
    ApplyLimits --> WaitResult[Theo dõi kết quả với giới hạn dung lượng]
    WaitResult --> Finished{Công cụ hoàn tất đúng thời gian}
    Finished -->|Không| KillGroup[Dừng toàn bộ tiến trình liên quan]
    KillGroup --> Timeout([Kết thúc báo quá thời gian])
    Finished -->|Có| ExitOK{Công cụ kết thúc thành công}
    ExitOK -->|Không| ProcessError([Kết thúc trả thông tin lỗi cần thiết])
    ExitOK -->|Có| ReleaseSlot[Nhường lượt xử lý cho yêu cầu khác]
    ReleaseSlot --> End([Kết thúc chuyển sang kiểm tra tệp])
```

## 11. Workflow cộng tác và xét duyệt

```mermaid
flowchart TD
    Start([Bắt đầu thao tác cộng tác]) --> CheckAccess[Kiểm tra quyền đọc hoặc sửa tài liệu]
    CheckAccess --> Allowed{Người dùng có quyền tương ứng}
    Allowed -->|Không| Deny([Kết thúc từ chối thao tác])
    Allowed -->|Có| Action{Người dùng muốn làm gì}
    Action -->|Gõ phím| PublishKeystroke[Chia sẻ thay đổi tức thời và giữ bản tạm]
    Action -->|Gợi ý| SaveSuggestion[Lưu gợi ý đang chờ xử lý]
    Action -->|Bình luận| SaveComment[Lưu bình luận tại đúng phần nội dung]
    Action -->|Tìm và thay thế| UpdateContent[Cập nhật nội dung và tạo bản lưu tạm]
    Action -->|Gửi xét duyệt| SubmitReview[Chuyển tài liệu sang trạng thái chờ xét duyệt]
    Action -->|So sánh phiên bản| LoadVersions[Đọc hai bản lưu để so sánh]
    PublishKeystroke --> End([Kết thúc trả trạng thái thao tác])
    SaveSuggestion --> End
    SaveComment --> End
    UpdateContent --> End
    SubmitReview --> End
    LoadVersions --> End
```

## 12. API hiện hành

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

## 13. Công nghệ đang sử dụng

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

Ghostscript và các bộ font được cài trong image để hỗ trợ toolchain, nhưng mã
engine hiện không gọi Ghostscript như một bước trực tiếp.

## 14. Trạng thái và giới hạn cần hiểu đúng

- Có 2.449 file feature không có nghĩa 2.449 tính năng đều đang hiện cho người dùng.
- `StandardEditor` chỉ đăng ký nhóm block cốt lõi trong `tools`.
- Tệp `document-command-catalog.generated.json` có 2.296 mục gồm 347 mục direct và 1.949 mục bridge
- Nhãn direct và bridge chỉ mô tả nguồn danh mục chứ không phải bằng chứng chức năng đã chạy được
- Giao diện chỉ cho thực hiện các chức năng nằm trong danh sách xác minh và không còn nạp động ghost class
- Palette hiện công khai 55 command đã vượt kiểm thử hành vi; Agentic AI được
  gọi 12 command bền vững, 6 command cấu trúc, 12 command định dạng văn bản,
  2 command theo khối và 4 command phân tích có
  registry chung với compilation service, cùng 2 command block dành cho bảng
  và hình ảnh, cùng 4 command phân tích không làm thay đổi nội dung.
- `generate:document-commands` không tự chạy trong `prebuild`; phải chạy chủ động
  khi thêm/xóa command.
- Manifest frontend và backend hiện cùng 2.449 feature và phải giống nhau tuyệt đối.
- Backend bỏ command block khỏi luồng văn bản nhưng xác minh
  `documentCommandState` và áp hiệu ứng bền vững như số cột, hình mờ và tỷ lệ
  khi kết xuất.
- Frontend phải giữ `.doclibx` khi tải container DRM của tài liệu LaTeX; không
  được đổi mọi protected export thành `.doclib`.

## 15. Nguồn kiểm chứng chính

- [Khởi tạo compilation service](backend/compilation/src/main.py)
- [EditorJS API](backend/compilation/src/api/editorjs.py)
- [LaTeX API](backend/compilation/src/api/latex.py)
- [EditorJS engine](backend/compilation/src/engines/editorjs.py)
- [LaTeX engine](backend/compilation/src/engines/latex.py)
- [Capability validation](backend/compilation/src/engines/editorjs_capabilities.py)
- [Frontend workspace](frontend/features/compilation/components/EditorWorkspace.tsx)
- [StandardEditor](frontend/features/compilation/components/StandardEditor.tsx)
- [Command palette](frontend/features/compilation/components/DocumentCommandPalette.tsx)
- [Command runtime](frontend/features/compilation/components/document-command-engine.ts)
- [Catalog generator](frontend/scripts/generate-document-command-catalog.mjs)
- [Compilation component audit](scripts/audit_compilation_components.py)

## 16. Quy tắc cập nhật tài liệu

Khi thêm engine, định dạng xuất, core block, command, manifest field hoặc API
composition, phải cập nhật workflow liên quan, bảng API, số liệu catalog và bảng
công nghệ. Không mô tả file class tồn tại như một tính năng đã hiển thị nếu nó
chưa được đăng ký trong `tools` hoặc chưa vượt qua bộ lọc của command palette.
