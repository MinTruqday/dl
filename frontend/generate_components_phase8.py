import os

components = [
    # Page & View
    "DocLibOrientation",
    "DocLibPaperSize",
    "DocLibVerticalAlignment",
    "DocLibBlankPage",
    "DocLibPageBreakBefore",
    "DocLibKeepLinesTogether",
    "DocLibSuppressLineNumbers",
    "DocLibDontHyphenate",
    "DocLibZoom",
    "DocLibOnePage",
    "DocLibMultiplePages",
    "DocLibPageWidth",
    "DocLibNewWindow",
    "DocLibViewSideBySide",
    "DocLibSwitchWindows",

    # Table Tools
    "DocLibDrawTable",
    "DocLibEraser",
    "DocLibMergeCells",
    "DocLibSplitCells",
    "DocLibSplitTable",
    "DocLibAutoFit",
    "DocLibDistributeRows",
    "DocLibDistributeColumns",
    "DocLibCellMargins",
    "DocLibSortTable",
    "DocLibRepeatHeaderRows",
    "DocLibTableFormula",
    "DocLibViewGridlinesTable",
    "DocLibInsertAbove",
    "DocLibInsertBelow",

    # Picture Format & Insert
    "DocLib3DRotation",
    "DocLibBevel",
    "DocLibPictureCorrections",
    "DocLibPictureColor",
    "DocLibChangePicture",
    "DocLibResetPicture",
    "DocLibPictureBorder",
    "DocLibPictureLayout",
    "DocLibCropToShape",
    "DocLibCropAspectRatio",
    "DocLibScreenshot",
    "DocLibSymbol",
    "DocLibTextFromFile",
    "DocLibDropCapLinesToDrop",
    "DocLibShowFormattingMarks",

    # Developer
    "DocLibRichTextContentControl",
    "DocLibPlainTextContentControl",
    "DocLibPictureContentControl",
    "DocLibBuildingBlockGallery",
    "DocLibComboBoxContentControl",
    "DocLibDropDownListControl",
    "DocLibDatePickerControl",
    "DocLibCheckBoxControl",
    "DocLibDesignMode",
    "DocLibControlProperties",
    "DocLibGroupControls",
    "DocLibDocumentTemplate",
    "DocLibCOMAddIns",
    "DocLibWordAddIns",
    "DocLibXMLMappingPane",

    # Mailings & References
    "DocLibEditRecipientList",
    "DocLibHighlightMergeFields",
    "DocLibMailMergeRules",
    "DocLibMatchFields",
    "DocLibUpdateLabels",
    "DocLibPreviewResults",
    "DocLibFindRecipient",
    "DocLibAutoCheckForErrors",
    "DocLibFinishAndMerge",
    "DocLibMarkCitation",
    "DocLibMarkEntry",
    "DocLibUpdateTable",
    "DocLibAddTextToTOC",
    "DocLibAltText",
    "DocLibSmartLookup"
]

template = """export class {name} {{
  private data: any;
  private wrapper: HTMLElement | null = null;
  private readonly config: any;

  constructor({{ data, config, api }}: any) {{
    this.data = data;
    this.config = config || {{}};
  }}

  static get toolbox() {{
    return {{
      icon: '<svg viewBox="0 0 24 24"><path d="M12 2L2 22h20L12 2z"/></svg>',
      title: '{name}'
    }};
  }}

  static get isReadOnlySupported() {{
    return true;
  }}

  render() {{
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add("doclib-{lower}-wrapper");

    const input = document.createElement("input");
    input.classList.add("ce-paragraph", "cdx-block");
    input.value = this.data.content || "";
    input.placeholder = "{name}";

    input.addEventListener("input", (e: any) => {{
      this.data.content = e.target.value;
    }});

    this.wrapper.appendChild(input);
    return this.wrapper;
  }}

  save(blockContent: HTMLElement) {{
    const input = blockContent.querySelector("input");
    return {{
      content: input ? input.value : ""
    }};
  }}
}}
"""

directory = "features/compilation/components"
os.makedirs(directory, exist_ok=True)

for name in components:
    lower_name = name.lower()
    filepath = os.path.join(directory, f"{name}.ts")
    with open(filepath, "w") as f:
        f.write(template.format(name=name, lower=lower_name))
    print(f"Generated {filepath}")
