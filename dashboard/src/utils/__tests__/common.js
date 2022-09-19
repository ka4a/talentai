import { replaceHttps } from '../common';

describe('replaceHttps', () => {
  it('inserts https at the beginning', () => {
    expect(replaceHttps('example.com')).toEqual('https://example.com');
  });

  it('replaces http at the beginning', () => {
    expect(replaceHttps('http://example.com')).toEqual('https://example.com');
  });

  it('given not a string, returns value as', () => {
    expect(replaceHttps(3)).toEqual(3);
  });
});
