import os
import re

components = [
    # Nhóm 1: Canvas Typography
    "DocLibClearFormatting",
    "DocLibWordUnderline",
    "DocLibDottedUnderline",
    "DocLibDashedUnderline",
    "DocLibWavyUnderline",
    "DocLibDoubleUnderline",
    "DocLibTextShadow",
    "DocLibTextEngrave",
    "DocLibTextEmboss",
    "DocLibAllCaps",
    "DocLibSentenceCase",
    "DocLibToggleCase",
    "DocLibNonbreakingSpace",
    "DocLibNonbreakingHyphen",
    "DocLibOptionalHyphen",
    "DocLibEmDash",
    "DocLibEnDash",
    "DocLibCharacterShading",
    "DocLibCharacterBorder",
    "DocLibEncloseCharacters",

    # Nhóm 2: Paragraph & Layout
    "DocLibFirstLineIndent",
    "DocLibHangingIndent",
    "DocLibLineSpacingSingle",
    "DocLibLineSpacing15",
    "DocLibLineSpacingDouble",
    "DocLibParagraphBorders",
    "DocLibParagraphShading",
    "DocLibMultilevelList",
    "DocLibDefineNewBullet",
    "DocLibDefineNewNumberFormat",
    "DocLibSetNumberingValue",
    "DocLibSortText",
    "DocLibColumnsOne",
    "DocLibColumnsTwo",
    "DocLibColumnsThree",
    "DocLibColumnsLeft",
    "DocLibColumnsRight",
    "DocLibColumnBreak",
    "DocLibTextWrappingBreak",
    "DocLibLineNumbersContinuous",

    # Nhóm 3: Header/Footer & Section
    "DocLibDifferentFirstPage",
    "DocLibDifferentOddAndEvenPages",
    "DocLibLinkToPrevious",
    "DocLibHeaderFromTop",
    "DocLibFooterFromBottom",
    "DocLibInsertAlignmentTab",
    "DocLibPageNumberFormat",
    "DocLibRemovePageNumbers",
    "DocLibPageNumberCurrentPosition",
    "DocLibPageNumberPageMargins",
    "DocLibNextPageSectionBreak",
    "DocLibContinuousSectionBreak",
    "DocLibEvenPageSectionBreak",
    "DocLibOddPageSectionBreak",
    "DocLibStyleInspector",
    "DocLibManageStyles",
    "DocLibCreateStyle",
    "DocLibUpdateStyleToMatch",
    "DocLibDropCapInMargin",
    "DocLibCombineCharacters",

    # Nhóm 4: Equations & Add-ins
    "DocLibAutoText",
    "DocLibEquationMatrixRow",
    "DocLibEquationMatrixColumn",
    "DocLibBuildingBlocksOrganizer",
    "DocLibSaveSelectionToQuickPart",
    "DocLibCameo",
    "DocLibEquationFraction",
    "DocLibEquationScript",
    "DocLibEquationRadical",
    "DocLibEquationIntegral",
    "DocLibEquationLargeOperator",
    "DocLibEquationMatrix",
    "DocLibWatermarkConfidential",
    "DocLibCustomWatermark",
    "DocLibRemoveWatermark",
    "DocLibDocumentFormattingThemes",
    "DocLibThemeColors",
    "DocLibThemeFonts",
    "DocLibThemeEffects",
    "DocLibParagraphSpacingSet",

    # Nhóm 5: Review & Markup
    "DocLibAcceptChange",
    "DocLibRejectChange",
    "DocLibNextChange",
    "DocLibTranslateSelection",
    "DocLibTranslateDocument",
    "DocLibSetProofingLanguage",
    "DocLibNewComment",
    "DocLibReplyToComment",
    "DocLibResolveComment",
    "DocLibShowComments",
    "DocLibSimpleMarkup",
    "DocLibAllMarkup",
    "DocLibNoMarkup",
    "DocLibShowMarkupReviewers",
    "DocLibOnlineVideo",
    "DocLibTableAutoFitWindow",
    "DocLibTableAutoFitContents",
    "DocLibTableFixedColumnWidth",
    "DocLibTableCellAlignmentCenter",
    "DocLibTableDistributeEvenly"
]

template = """import {{ API, BlockTool }} from "@editorjs/editorjs";

export default class {name} implements BlockTool {{
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: {{ content: string }};

  static get toolbox() {{
    return {{
      title: "{spaced_name}",
      icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>'
    }};
  }}

  constructor({{ api, data }}: {{ api: API; data: any }}) {{
    this.api = api;
    this.data = {{ content: data.content || "" }};
  }}

  render() {{
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-{lower}");
    this.wrapper.contentEditable = "true";
    this.wrapper.innerHTML = this.data.content;
    this.wrapper.dataset.placeholder = "{spaced_name}";

    this.wrapper.addEventListener("input", (e: any) => {{
      this.data.content = e.target.innerHTML;
    }});

    return this.wrapper;
  }}

  save(blockContent: HTMLElement) {{
    return {{
      content: blockContent.innerHTML
    }};
  }}
}}
"""

directory = "features/compilation/components"
os.makedirs(directory, exist_ok=True)

for name in components:
    # Convert CamelCase to Spaced Words
    spaced_name = re.sub(r"([A-Z])", r" \1", name).strip()
    # Convert CamelCase to lowercase-hyphen
    lower = re.sub(r"([A-Z])", r"-\1", name).lower().lstrip("-")
    
    filepath = os.path.join(directory, f"{name}.ts")
    with open(filepath, "w") as f:
        f.write(template.format(name=name, spaced_name=spaced_name, lower=lower))
    print(f"Generated {filepath}")
