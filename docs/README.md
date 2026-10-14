# 광고 서버 문서

[`ad-server-routing/README.md`](ad-server-routing/README.md)에서 시작한다. 현재 구현의 HTTP 경로, 관리 명령, 계층별 호출 흐름, Mongo·파일 계약과 파일별 함수 설명을 연결한다. 플레이어 스냅샷 검사·비교·누락 기록·계약 생성·폴더 인계·정규화 미리보기와 CDC 준비 기록, 전체 정규화 파일 생성·최신 context 반영/조회·버전 데모 명령도 포함한다. 체크포인트 일괄 반영·스냅샷 갱신·선택 context 비교와 현재 context API도 연결한다. 런타임 Python 55파일의 함수·클래스·메서드 165개를 연결한다.

파일별 문서는 `ad-server-routing/files/<프로젝트 상대경로>.md`에 있다. 코드 탐색 문서이며 수업에서 앞으로 만들 기능은 현재 구현으로 기록하지 않는다.

context 인계 폴더 생성과 Lake history/current 검사·fixture 데모도 포함한다.

저장 Lake 버전 생성·파일 지문 비교·동일 원본의 Mongo/Lake 상태 대조·대조 fixture와 새 고정 광고 사건 내보내기도 연결한다.
