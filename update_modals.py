import os
import glob
import re

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    original = content
    
    # 1. `<Modal ...>` tags might have `className="max-w-md rounded-[18px] bg-[#F5F5F7] p-0 border-none"` in thu-vien
    # Or in dang-ky/page.tsx: `className="max-w-md rounded-[24px] bg-white p-0 border border-[#E8E8ED]"`
    # But wait, we just want to remove the specific classes on ModalHeader, ModalContent, ModalFooter
    # Actually, ModalHeader is often `<ModalHeader className="p-6">` or `className="p-6 pb-2"`
    content = re.sub(r'<ModalHeader[^>]*>', '<ModalHeader>', content)
    
    # ModalContent is often `<ModalContent className="px-6 pb-6 text-[15px]...">` or similar
    # Wait, some ModalContents have `space-y-4` or `max-h-[300px] overflow-y-auto`. We shouldn't remove ALL classes!
    # Instead, remove specific hardcoded styles from ModalFooter:
    # ModalFooter is often `<ModalFooter className="p-4 bg-white rounded-b-[24px] flex justify-end gap-3">`
    content = re.sub(r'<ModalFooter[^>]*>', '<ModalFooter>', content)

    # ModalTitle is often `<ModalTitle className="text-[20px] font-semibold text-[#1D1D1F]">`
    content = re.sub(r'<ModalTitle[^>]*>', '<ModalTitle>', content)

    # Let's clean up ModalContent manually for now, or just leave it since the new default handles basic padding,
    # but removing all classes from ModalContent might break scrolling (overflow-y-auto).
    # What if we just replace the exact known footer/header strings?

    with open(filepath, 'w') as f:
        f.write(content)

# We will run this script
