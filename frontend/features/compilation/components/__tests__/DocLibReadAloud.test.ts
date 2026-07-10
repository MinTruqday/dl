import DocLibReadAloud from '../DocLibReadAloud';

describe('DocLibReadAloud', () => {
  
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


  it('should render block correctly', () => {
    const tool = new DocLibReadAloud({ api: mockApi as any, data: {} });
    const el = tool.render();
    expect(el).toBeInstanceOf(HTMLElement);
  });
});
