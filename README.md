# trashbin🗑️

휴지통(혹은 똥통)은 디시인사이드의 특정 갤러리 글을 전부 아카이빙하고, 완장만 몰래 본 삭제된 글을 훔쳐보기 위해 만들어진 프로그램 입니다.

## 빠른 시작

1. 저장소 클론:
   ```
   git clone https://github.com/yeorinhieut/trashbin.git
   cd trashbin
   ```

2. `docker-compose.yml` 수정:
   - `GALLERY_ID`를 원하는 갤러리 ID로 설정
   - `DELAY`를 적당히 알아서 잘 설정(10~15 권장)

3. 애플리케이션 실행:
   ```
   docker compose up -d
   ```

지정한 갤러리의 쓰레기 수집이 시작됩니다. 웹 인터페이스는 `http://ip:8000`에서 접근 가능합니다.

## 참고

- 특정 글이 작성되고 30분 뒤 체크하여 삭제되었다면 삭제된 것으로 체크됩니다.
- 혼자 보시는걸 추천드립니다.
