import DocLibSmallCaps from '../DocLibSmallCaps';

describe('DocLibSmallCaps', () => {
  
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


  it('should render inline tool button', () => {
    const tool = new DocLibSmallCaps({ api: mockApi as any });
    const el = tool.render();
    expect(el).toBeInstanceOf(HTMLElement);
    expect(el.tagName).toBe('BUTTON');
  });
});
