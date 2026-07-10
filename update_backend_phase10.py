import re

components = [
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

ignore_names = []
for c in components:
    name = re.sub('^doclib', '', c, flags=re.IGNORECASE)
    name = name[:1].lower() + name[1:]
    ignore_names.append(f'"{name}"')

chunk = ",\n            ".join([", ".join(ignore_names[i:i+5]) for i in range(0, len(ignore_names), 5)])

with open("backend/compilation/src/engines/editorjs.py", "r") as f:
    content = f.read()

target = '            "tableDistributeEvenly"'
replacement = target + ",\n            " + chunk

content = content.replace(target, replacement)

with open("backend/compilation/src/engines/editorjs.py", "w") as f:
    f.write(content)
print("Updated editorjs.py with Phase 10 new components")
