# dnf-ocr-synth

던전앤파이터 닉네임의 렌더링 조건을 정리하고, OCR 파인튜닝용 합성 샘플 생성에 활용하기 위한 저장소입니다.

## 사용하는 폰트

현재 확인한 닉네임 샘플의 재현에는 아래 세 파일을 사용합니다. **폰트 파일은 이 저장소에 포함하거나 업로드하지 않습니다.** 사용 권한이 있는 로컬 파일을 별도로 준비해야 합니다.

| 파일 | 실제 사용하는 글꼴 | 용도 | 로컬 준비 방법 |
| --- | --- | --- | --- |
| `gulim.ttc` | 돋움(Dotum), face index 2 | 게임에서 돋움을 선택한 샘플 재현 | Windows에 설치된 `C:/Windows/Fonts/gulim.ttc`를 사용합니다. |
| `batang.ttc` | 궁서(Gungsuh), face index 2 | 나눔스퀘어 네오에 없는 `ァ`, `Ð`, `ぎ`의 대체 글리프 재현 | Windows에 설치된 `C:/Windows/Fonts/batang.ttc`를 사용합니다. |
| `NanumSquareNeoOTF-cBd.otf` | 나눔스퀘어 네오 Bold | 나눔스퀘어 네오 설정 샘플의 `★` 재현 | [네이버 공식 배포처](https://campaign.naver.com/nanumsquare_neo/)에서 준비한 로컬 파일을 사용합니다. |

`gulim.ttc`와 `batang.ttc`는 여러 글꼴을 담은 컬렉션입니다. 파일 이름과 달리 현재 재현에서 선택한 글꼴은 각각 돋움과 궁서입니다.

대체 글리프 조합은 `ァÐぎ★` 샘플에서 확인한 재현 조건입니다. 궁서와 궁서체의 12px 및 13px에서 해당 글리프가 동일하게 나왔으므로, 게임 내부의 정확한 글꼴 선택과 모든 문자에 대한 대체 규칙까지 확정한 것은 아닙니다.

## 폰트 보관과 라이선스

- 세 폰트 모두 로컬에서만 준비합니다. 폰트 바이너리와 `fonts/local/` 디렉터리는 `.gitignore`로 제외합니다.
- Windows 폰트는 저장소, 배포 패키지 또는 컨테이너에 복사하지 않고 적법하게 설치된 Windows 환경에서 읽습니다. [Microsoft 폰트 재배포 안내](https://learn.microsoft.com/en-us/typography/fonts/font-faq)를 따릅니다.
- 나눔스퀘어 네오는 OFL 1.1 폰트이지만 이 저장소에서는 동봉하지 않습니다. 사용 조건은 [네이버 나눔글꼴 라이선스](https://help.naver.com/service/30016/contents/18088?osType=PC&lang=ko)를 확인합니다.
- Windows 폰트로 만든 닉네임 문자열 PNG와 문자별 비트맵 폰트는 배포 조건이 다릅니다. 개별 글리프를 모은 비트맵 폰트나 글리프 아틀라스는 저장소에 포함하지 않습니다.
