import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { getRelativeTime, formatDate, formatDateTime } from './date';

describe('date utils', () => {
  describe('getRelativeTime', () => {
    beforeEach(() => {
      vi.useFakeTimers();
      vi.setSystemTime(new Date('2024-01-15T12:00:00.000Z'));
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('방금 전 (60초 미만)', () => {
      const date = new Date('2024-01-15T11:59:30.000Z').toISOString();
      expect(getRelativeTime(date)).toBe('방금 전');
    });

    it('N분 전', () => {
      const date = new Date('2024-01-15T11:30:00.000Z').toISOString();
      expect(getRelativeTime(date)).toBe('30분 전');
    });

    it('N시간 전', () => {
      const date = new Date('2024-01-15T09:00:00.000Z').toISOString();
      expect(getRelativeTime(date)).toBe('3시간 전');
    });

    it('N일 전', () => {
      const date = new Date('2024-01-13T12:00:00.000Z').toISOString();
      expect(getRelativeTime(date)).toBe('2일 전');
    });

    it('7일 이상이면 날짜 포맷', () => {
      const date = new Date('2024-01-01T12:00:00.000Z').toISOString();
      const result = getRelativeTime(date);
      expect(result).toContain('2024');
      expect(result).toContain('1');
    });
  });

  describe('formatDate', () => {
    it('한국어 날짜 포맷', () => {
      const date = '2024-01-15T12:00:00.000Z';
      const result = formatDate(date);
      expect(result).toContain('2024');
    });
  });

  describe('formatDateTime', () => {
    it('한국어 날짜+시간 포맷', () => {
      const date = '2024-01-15T12:00:00.000Z';
      const result = formatDateTime(date);
      expect(result).toContain('2024');
    });
  });
});
