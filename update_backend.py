import re

components = [
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

ignore_names = []
for c in components:
    name = re.sub('^doclib', '', c, flags=re.IGNORECASE)
    name = name[:1].lower() + name[1:]
    ignore_names.append(f'"{name}"')

chunk = ",\n            ".join([", ".join(ignore_names[i:i+5]) for i in range(0, len(ignore_names), 5)])
print("Chunk to append:")
print(chunk)

with open("backend/compilation/src/engines/editorjs.py", "r") as f:
    content = f.read()

target = '            "mailMergeRecipients", "citationStyle", "kerningForFonts"'
replacement = target + ",\n            " + chunk

content = content.replace(target, replacement)

with open("backend/compilation/src/engines/editorjs.py", "w") as f:
    f.write(content)
print("Updated editorjs.py")
