import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { logger } from './logger';

describe('logger', () => {
  const originalConsole = { ...console };

  beforeEach(() => {
    console.log = vi.fn();
    console.info = vi.fn();
    console.warn = vi.fn();
    console.error = vi.fn();
  });

  afterEach(() => {
    console.log = originalConsole.log;
    console.info = originalConsole.info;
    console.warn = originalConsole.warn;
    console.error = originalConsole.error;
  });

  it('debug 로그 출력 (개발 환경)', () => {
    logger.debug('테스트 메시지');
    expect(console.log).toHaveBeenCalled();
    const logCall = (console.log as unknown as { mock: { calls: string[][] } }).mock.calls[0];
    expect(logCall[0]).toContain('[DEBUG]');
    expect(logCall[0]).toContain('테스트 메시지');
  });

  it('info 로그 출력 (개발 환경)', () => {
    logger.info('정보 메시지');
    expect(console.info).toHaveBeenCalled();
    const logCall = (console.info as unknown as { mock: { calls: string[][] } }).mock.calls[0];
    expect(logCall[0]).toContain('[INFO]');
    expect(logCall[0]).toContain('정보 메시지');
  });

  it('warn 로그 출력 (개발 환경)', () => {
    logger.warn('경고 메시지');
    expect(console.warn).toHaveBeenCalled();
    const logCall = (console.warn as unknown as { mock: { calls: string[][] } }).mock.calls[0];
    expect(logCall[0]).toContain('[WARN]');
    expect(logCall[0]).toContain('경고 메시지');
  });

  it('error 로그는 항상 출력', () => {
    logger.error('에러 메시지');
    expect(console.error).toHaveBeenCalled();
    const logCall = (console.error as unknown as { mock: { calls: string[][] } }).mock.calls[0];
    expect(logCall[0]).toContain('[ERROR]');
    expect(logCall[0]).toContain('에러 메시지');
  });

  it('데이터와 함께 로그 출력', () => {
    const data = { key: 'value' };
    logger.debug('테스트', data);
    expect(console.log).toHaveBeenCalledWith(
      expect.stringContaining('테스트'),
      data
    );
  });
});
