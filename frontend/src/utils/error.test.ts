import { describe, it, expect } from 'vitest';
import { getErrorMessage, isNetworkError } from './error';

describe('getErrorMessage', () => {
  it('null/undefined인 경우 기본 메시지 반환', () => {
    expect(getErrorMessage(null)).toBe('오류가 발생했습니다.');
    expect(getErrorMessage(undefined)).toBe('오류가 발생했습니다.');
  });

  it('커스텀 기본 메시지 반환', () => {
    expect(getErrorMessage(null, '커스텀 에러')).toBe('커스텀 에러');
  });

  it('Axios 에러의 detail 메시지 추출', () => {
    const error = {
      response: {
        data: { detail: '인증 토큰이 만료되었습니다.' },
        status: 401,
      },
    };
    expect(getErrorMessage(error)).toBe('인증 토큰이 만료되었습니다.');
  });

  it('Axios 에러의 message 메시지 추출', () => {
    const error = {
      response: {
        data: { message: '서버 점검 중입니다.' },
        status: 500,
      },
    };
    expect(getErrorMessage(error)).toBe('서버 점검 중입니다.');
  });

  it('HTTP 상태 코드별 기본 메시지 반환', () => {
    expect(getErrorMessage({ response: { status: 400 } })).toBe('잘못된 요청입니다.');
    expect(getErrorMessage({ response: { status: 401 } })).toBe('인증이 필요합니다.');
    expect(getErrorMessage({ response: { status: 403 } })).toBe('권한이 없습니다.');
    expect(getErrorMessage({ response: { status: 404 } })).toBe('요청한 항목을 찾을 수 없습니다.');
    expect(getErrorMessage({ response: { status: 500 } })).toBe('서버 오류가 발생했습니다.');
  });

  it('일반 Error 객체의 메시지 추출', () => {
    const error = new Error('테스트 에러 메시지');
    expect(getErrorMessage(error)).toBe('테스트 에러 메시지');
  });

  it('문자열 에러 반환', () => {
    expect(getErrorMessage('문자열 에러')).toBe('문자열 에러');
  });
});

describe('isNetworkError', () => {
  it('null/undefined인 경우 false 반환', () => {
    expect(isNetworkError(null)).toBe(false);
    expect(isNetworkError(undefined)).toBe(false);
  });

  it('ERR_NETWORK 코드인 경우 true 반환', () => {
    const error = { code: 'ERR_NETWORK' };
    expect(isNetworkError(error)).toBe(true);
  });

  it('response가 없는 경우 true 반환', () => {
    const error = { response: undefined };
    expect(isNetworkError(error)).toBe(true);
  });

  it('일반 에러인 경우 false 반환', () => {
    const error = { response: { status: 500 } };
    expect(isNetworkError(error)).toBe(false);
  });
});
