import os
import re

components = [
    # Group 1: Asian Layout & Font Advanced
    "DocLibHorizontalInVertical",
    "DocLibTwoLinesInOne",
    "DocLibFitText",
    "DocLibCharacterSpacingExpanded",
    "DocLibCharacterSpacingCondensed",
    "DocLibPositionRaised",
    "DocLibPositionLowered",
    "DocLibOpenTypeStandardOnly",
    "DocLibOpenTypeStandardAndContextual",
    "DocLibOpenTypeHistoricalAndDiscretionary",
    "DocLibOpenTypeAllLigatures",
    "DocLibNumberSpacingProportional",
    "DocLibNumberSpacingTabular",
    "DocLibNumberFormsLining",
    "DocLibNumberFormsOldStyle",
    "DocLibStylisticSets",
    "DocLibUseContextualAlternates",
    "DocLibHighlightColorYellow",
    "DocLibHighlightColorGreen",
    "DocLibHighlightColorPink",

    # Group 2: Layout & Background
    "DocLibLineNumbersRestartEachPage",
    "DocLibLineNumbersRestartEachSection",
    "DocLibLineNumbersOptions",
    "DocLibHyphenationAutomatic",
    "DocLibHyphenationManual",
    "DocLibHyphenationOptions",
    "DocLibColumnsMoreColumns",
    "DocLibColumnsLineBetween",
    "DocLibPageBordersBox",
    "DocLibPageBordersShadow",
    "DocLibPageBorders3D",
    "DocLibPageBordersCustom",
    "DocLibPageColorFillEffects",
    "DocLibPageColorGradient",
    "DocLibPageColorTexture",
    "DocLibPageColorPattern",
    "DocLibPageColorPicture",
    "DocLibWatermarkPicture",
    "DocLibWatermarkText",
    "DocLibWatermarkWashout",

    # Group 3: Picture & Shape Details
    "DocLibShapeFillSolid",
    "DocLibShapeFillGradient",
    "DocLibShapeFillPicture",
    "DocLibShapeFillTexture",
    "DocLibShapeOutlineWeight",
    "DocLibShapeOutlineDashes",
    "DocLibShapeOutlineArrows",
    "DocLibPictureEffectsShadow",
    "DocLibPictureEffectsReflection",
    "DocLibPictureEffectsGlow",
    "DocLibPictureEffectsSoftEdges",
    "DocLibPictureEffectsBevel",
    "DocLibPictureEffects3DRotation",
    "DocLibWrapTextSquare",
    "DocLibWrapTextTight",
    "DocLibWrapTextThrough",
    "DocLibWrapTextTopAndBottom",
    "DocLibWrapTextBehindText",
    "DocLibWrapTextInFrontOfText",
    "DocLibWrapTextEditWrapPoints",

    # Group 4: Advanced Table Design
    "DocLibTableDesignHeaderRow",
    "DocLibTableDesignTotalRow",
    "DocLibTableDesignBandedRows",
    "DocLibTableDesignFirstColumn",
    "DocLibTableDesignLastColumn",
    "DocLibTableDesignBandedColumns",
    "DocLibTableBordersAll",
    "DocLibTableBordersOutside",
    "DocLibTableBordersInside",
    "DocLibTableBordersDiagonal",
    "DocLibTableCellAlignmentTopLeft",
    "DocLibTableCellAlignmentTopCenter",
    "DocLibTableCellAlignmentTopRight",
    "DocLibTableCellAlignmentCenterLeft",
    "DocLibTableCellAlignmentCenterRight",
    "DocLibTableCellAlignmentBottomLeft",
    "DocLibTableCellAlignmentBottomCenter",
    "DocLibTableCellAlignmentBottomRight",
    "DocLibTextDirectionHorizontal",
    "DocLibTextDirectionVertical",

    # Group 5: ActiveX & Go To
    "DocLibLegacyFormsText",
    "DocLibLegacyFormsCheck",
    "DocLibLegacyFormsDrop",
    "DocLibActiveXCommandButton",
    "DocLibActiveXComboBox",
    "DocLibActiveXCheckBox",
    "DocLibActiveXListBox",
    "DocLibActiveXTextBox",
    "DocLibActiveXOptionButton",
    "DocLibActiveXToggleButton",
    "DocLibActiveXSpinButton",
    "DocLibActiveXScrollBar",
    "DocLibActiveXLabel",
    "DocLibActiveXImage",
    "DocLibGoToPage",
    "DocLibGoToSection",
    "DocLibGoToLine",
    "DocLibGoToBookmark",
    "DocLibGoToComment",
    "DocLibGoToFootnote"
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
    # Correct Doc Lib -> DocLib
    if spaced_name.startswith("Doc Lib"):
        spaced_name = "DocLib" + spaced_name[7:]
    
    # Convert CamelCase to lowercase-hyphen
    lower = re.sub(r"([A-Z])", r"-\1", name).lower().lstrip("-")
    
    filepath = os.path.join(directory, f"{name}.ts")
    with open(filepath, "w") as f:
        f.write(template.format(name=name, spaced_name=spaced_name, lower=lower))
    print(f"Generated {filepath}")
