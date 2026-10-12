# `ads/management/commands/write_cdc_readiness.py`

원본 소스 경로: `ads/management/commands/write_cdc_readiness.py` · [전체 라우팅](../../../../README.md)

## 책임과 경계

[snapshot_intake.readiness](../../snapshot_intake.py.md#def-readinessmysql_confignone-connect_homenone-debezium_dirnone)가 만든 CDC 준비 기록을 JSON 파일로 저장하고 같은 결과를 표준 출력하는 Django 관리 명령이다. 입력 경로의 제공 여부·존재 여부와 CDC 구성·관찰 상태를 분리한다. 경로가 존재해도 MySQL binlog 설정, Kafka Connect worker, Debezium connector, 플레이어 변경 topic의 구성이나 실동작을 확인한 것으로 처리하지 않는다.

## `class Command`

Signature: `class Command(BaseCommand)`

1. **검증·변환:** Django BaseCommand를 상속하며 옵션 등록과 실행 진입점을 정의한다.
2. **직접 호출:** 클래스 선언 자체의 직접 호출은 없다. Django가 add_arguments·handle을 실행한다.
3. **반환·상태:** help는 경로 존재와 CDC 미구성 상태를 분리한 준비 기록을 저장하는 명령임을 설명한다.

## `def add_arguments(self, parser)`

Signature: `def add_arguments(self, parser)`

1. **검증·변환:** --output은 필수 옵션이다. --mysql-config·--connect-home·--debezium-dir는 선택 옵션이며 생략하면 각각 None이다. 별도 type·경로 종류·내용 검증을 등록하지 않는다.
2. **직접 호출:** parser.add_argument를 네 번 호출한다.
3. **반환·상태:** parser에 옵션을 등록하며 반환값은 없다. Django가 옵션 이름의 하이픈을 밑줄로 바꾸므로 handle에서는 mysql_config·connect_home·debezium_dir 키를 사용한다.

## `def handle(self, *args, **options)`

Signature: `def handle(self, *args, **options)`

1. **검증·변환:** options.get으로 세 선택 경로를 readiness에 전달한다. 각 입력은 bool(value)로 supplied를 판정하고, 값이 있을 때만 Path(value).exists()로 exists를 판정한다. 생략되거나 빈 문자열이면 두 값 모두 False다. exists는 파일·디렉터리를 구분하거나 내용을 검사하지 않는다. options["output"]을 Path로 바꾸고 부모 디렉터리를 parents=True·exist_ok=True로 생성한다. 이 준비·파일 저장 구간의 OSError·ValueError·TypeError는 원인 예외를 유지한 CommandError로 바꾼다.
2. **직접 호출:** [readiness](../../snapshot_intake.py.md#def-readinessmysql_confignone-connect_homenone-debezium_dirnone) → Path(options["output"]) → target.parent.mkdir → json.dumps(ensure_ascii=False, sort_keys=True, indent=2) → target.write_text(encoding="utf-8") → json.dumps(ensure_ascii=False, sort_keys=True) → self.stdout.write.
3. **반환·상태:** 출력 파일을 UTF-8의 2칸 들여쓰기 JSON과 마지막 개행으로 기록한다. 기존 파일은 덮어쓰며, 성공한 뒤 같은 사전을 정렬된 키의 JSON 한 줄로 표준 출력한다. 명시적 반환값은 없다. DB나 CDC 구성 명령을 실행하지 않는다. output과 세 선택 입력 경로의 동일 여부는 검사하지 않으므로 해당 입력 파일을 출력 경로로 지정하면 덮어쓸 수 있다. stdout 쓰기는 try 바깥에 있어 해당 실패는 위 CommandError 변환 대상이 아니며, 필수 output 키를 직접 호출에서 누락한 KeyError도 잡지 않는다. 파일 교체는 원자적이지 않다.

### JSON 출력 계약

| 필드 | 값·기본 상태 |
| --- | --- |
| schema_version | `"cdc-readiness/v1"` |
| paths | `mysql_config`·`connect_home`·`debezium_dir` 각각에 `supplied`·`exists` bool을 담은 사전. 세 옵션을 생략하면 모두 `False`다. 입력 경로 문자열 자체는 저장하지 않는다. |
| mysql_binlog | `"not-verified"` |
| cdc_reader | `"not-configured"` |
| connect_worker | `"not-configured"` |
| debezium_connector | `"not-configured"` |
| player_change_topic | `"not-configured"` |
| common_input | `"player-snapshot/v1"` (`snapshot_intake.SCHEMA_VERSION`) |
| binlog_cdc_observed | `False` |

세 경로를 모두 제공하고 모두 존재하더라도 CDC 상태 문자열과 binlog_cdc_observed는 위 값 그대로다. readiness는 경로 존재만 검사하며 binlog 원문이나 CDC 이벤트를 읽지 않는다.
