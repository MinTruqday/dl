import os
import re

DIR = "frontend/features/compilation/components"
TEST_DIR = "frontend/features/compilation/components/__tests__"

os.makedirs(TEST_DIR, exist_ok=True)

files = [f for f in os.listdir(DIR) if f.endswith(".ts") and not f.endswith("d.ts") and not f.endswith(".test.ts")]

mock_api = """
const mockApi = {
  styles: {
    block: "ce-block",
    inlineToolButton: "ce-inline-tool",
    settingsButton: "ce-settings-btn",
    settingsButtonActive: "ce-settings-btn--active"
  },
  blocks: {
    insert: jest.fn(),
    getCurrentBlockIndex: jest.fn().mockReturnValue(0)
  },
  caret: {
    setToBlock: jest.fn()
  },
  tooltip: {
    onHover: jest.fn(),
    hide: jest.fn()
  }
};
"""

for file in files:
    filepath = os.path.join(DIR, file)
    with open(filepath, 'r') as f:
        content = f.read()
    
    match = re.search(r'class\s+([A-Za-z0-9_]+)', content)
    if not match:
        continue
    
    class_name = match.group(1)
    
    is_block = "render()" in content and "save(" in content
    is_inline = "surround(" in content or "InlineTool" in content
    is_tune = "isTune" in content
    
    test_content = f"""import {class_name} from '../{file.replace(".ts", "")}';

describe('{class_name}', () => {{
  {mock_api}
"""

    has_test = False

    if is_inline:
        test_content += f"""
  it('should render inline tool button', () => {{
    const tool = new {class_name}({{ api: mockApi as any }});
    const el = tool.render();
    expect(el).toBeInstanceOf(HTMLElement);
    expect(el.tagName).toBe('BUTTON');
  }});
"""
        has_test = True
    elif is_block:
        test_content += f"""
  it('should render block correctly', () => {{
    const tool = new {class_name}({{ api: mockApi as any, data: {{}} }});
    const el = tool.render();
    expect(el).toBeInstanceOf(HTMLElement);
  }});
"""
        has_test = True
    elif is_tune:
        test_content += f"""
  it('should render settings tune correctly', () => {{
    const tune = new {class_name}({{ api: mockApi as any, data: {{}} }});
    const el = tune.render();
    expect(el).toBeInstanceOf(HTMLElement);
  }});
"""
        has_test = True

    if not has_test:
        test_content += f"""
  it('should instantiate without error', () => {{
    const tool = new {class_name}({{ api: mockApi as any, data: {{}} }});
    expect(tool).toBeDefined();
  }});
"""

    test_content += "});\n"
    
    test_filepath = os.path.join(TEST_DIR, file.replace(".ts", ".test.ts"))
    with open(test_filepath, 'w') as f:
        f.write(test_content)

print(f"Generated tests in {TEST_DIR}")
