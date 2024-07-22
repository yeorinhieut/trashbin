# trashbin🗑️

휴지통(혹은 똥통)은 디시인사이드의 특정 갤러리 글을 전부 아카이빙하고, 완장만 몰래 본 삭제된 글을 훔쳐보기 위해 만들어진 프로그램 입니다.

## 빠른 시작

### docker-compose
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
   
### docker cli
1. 저장소 클론:
   ```
   git clone https://github.com/yeorinhieut/trashbin.git
   cd trashbin
   ```

2. 이미지 빌드
   ```
   docker build -t trashbin .
   ```
   
3. 애플리케이션 실행
   ```
   docker run -d --name trashbin -p 8000:8000 -e GALLERY_ID=sff -e DELAY=15 -e DEBUG=false -v path/to/data:/app/data --restart unless-stopped trashbin
   ```

지정한 갤러리의 쓰레기 수집이 시작됩니다. 웹 인터페이스는 `http://ip:port`에서 접근 가능합니다.

## 참고

- 특정 글이 작성되고 30분 뒤 체크하여 삭제되었다면 삭제된 것으로 체크됩니다.
- 혼자 보시는걸 추천드립니다.
- http://ip:port/docs 에 대충 api 문서가 준비되어 있습니다.

## FAQ

**Q: 할머니가 저장되면 잡혀가는거 아닌가요?**

**A:** 디시인사이드는 글을 삭제해도 글에서 사용된 이미지는 서버에서 삭제하지 않는 기괴한 시스템을 사용하고 있습니다.
쓰레기통에선 디시 서버에 남아있는 이미지 링크를 그대로 사용자에게 보내주는 역할만 수행합니다.
즉, 쓰레기통 자체에 할머니 외 여러 이미지들을 저장하지 않습니다.
텍스트 형태로만 저장되기 때문에, 스토리지도 별로 사용하지 않더라구요.


**Q: 왜 sqlite3를 사용했나요?**

**A:** 원래 프로젝트 자체는 mongodb 기반이였는데, 최대한 포터블하게 새로 짜느라 sqlite3로 바꿨습니다.


**Q: 코드가 너무 더럽습니다.**

**A:** 죄송합니다. ChatGPT와 Claude가 대부분의 코드를 저 대신 작성해줬기 때문에 코드가 많이 더러워요.
