import re

components = [
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

ignore_names = []
for c in components:
    name = re.sub('^doclib', '', c, flags=re.IGNORECASE)
    name = name[:1].lower() + name[1:]
    ignore_names.append(f'"{name}"')

chunk = ",\n            ".join([", ".join(ignore_names[i:i+5]) for i in range(0, len(ignore_names), 5)])

with open("backend/compilation/src/engines/editorjs.py", "r") as f:
    content = f.read()

target = '            "smartLookup"'
replacement = target + ",\n            " + chunk

content = content.replace(target, replacement)

with open("backend/compilation/src/engines/editorjs.py", "w") as f:
    f.write(content)
print("Updated editorjs.py with 100 new components")
