# `ad_config/manage.py`

원본 소스 경로: `ad_config/manage.py` · 광고 작업 폴더 기준. [전체 라우팅](../../README.md)

## 책임과 경계

Django 관리 명령의 프로세스 진입점이다. 광고 앱의 구현을 직접 조립하거나 MongoDB에 연결하지 않는다.

## 호출자와 직접 의존

광고 작업 폴더에서 `python ad_config/manage.py <command>`를 실행하는 CLI.

관련 문서: [ad_config/ad_config/settings.py](ad_config/settings.py.md).

## `def main()`

Signature: `def main()` · 소스 7행.

1. **검증·변환:** `DJANGO_SETTINGS_MODULE`이 없을 때 `ad_config.settings`로 설정한다. Django import가 실패하면 가상환경·설치를 확인하라는 `ImportError`를 원인 예외와 함께 발생시킨다.
2. **직접 호출:** `os.environ.setdefault()` → Django의 `execute_from_command_line(sys.argv)`. 실행 인수는 Django 명령 처리기로 그대로 넘긴다.
3. **반환·상태:** 명시적 반환값은 없다. 관리 명령의 실행·종료·오류 처리는 Django에 맡긴다. `__name__ == "__main__"`일 때 이 함수가 호출된다.
