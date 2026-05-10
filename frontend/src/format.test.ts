import { describe, expect, it } from 'vitest';
import { formatDistance, formatDuration } from './format';

describe('formatDistance', () => {
  it('formats meters below one kilometer', () => {
    expect(formatDistance(850)).toBe('850 m');
  });

  it('formats kilometers with one decimal place', () => {
    expect(formatDistance(1234)).toBe('1.2 km');
  });
});

describe('formatDuration', () => {
  it('formats short durations in minutes', () => {
    expect(formatDuration(300)).toBe('5 min');
  });

  it('formats long durations in hours and minutes', () => {
    expect(formatDuration(5460)).toBe('1 hr 31 min');
  });
});
