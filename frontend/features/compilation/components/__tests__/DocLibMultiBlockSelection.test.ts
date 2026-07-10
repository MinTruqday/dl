import DocLibMultiBlockSelection from '../DocLibMultiBlockSelection';

describe('DocLibMultiBlockSelection', () => {
  
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


  it('should instantiate without error', () => {
    const tool = new DocLibMultiBlockSelection({ api: mockApi as any, data: {} });
    expect(tool).toBeDefined();
  });
});
