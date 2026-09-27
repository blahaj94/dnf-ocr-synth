# dnf-ocr-synth

로컬 폰트로 던전앤파이터 닉네임을 렌더링하는 작은 Python 패키지입니다. OCR 파인튜닝 파이프라인에서 import하거나 Git 서브모듈로 가져와 사용합니다. 투명 배경 PNG에 원본 정답 문자열과 렌더링 메타데이터를 함께 저장합니다.

## 설치와 실행

Python 3.11 이상이 필요합니다. 저장소 루트에서 설치합니다.

```powershell
python -m pip install -e .
python -m dnf_ocr_synth 'ァÐぎ★' --gulim 'C:/Windows/Fonts/gulim.ttc' --layout reference --ui-percent 100 --output output/dotum.png
python -m dnf_ocr_synth 'ァÐぎ★' --profile nanum-neo --batang 'C:/Windows/Fonts/batang.ttc' --nanum 'C:/path/to/NanumSquareNeoOTF-cBd.otf' --layout reference --ui-percent 100 --output output/nanum.png
```

`C:/path/to/...`는 직접 준비한 폰트 경로로 바꿉니다. 설치 후 `dnf-ocr-synth` 명령도 사용할 수 있습니다. CLI는 출력 폴더를 만들고 같은 경로의 PNG를 덮어씁니다.

```python
from pathlib import Path

from dnf_ocr_synth import FontPaths, Renderer, estimate_ui_scale

renderer = Renderer(
    FontPaths(
        gulim=Path("C:/Windows/Fonts/gulim.ttc"),
        batang=Path("C:/Windows/Fonts/batang.ttc"),
        nanum=Path("C:/path/to/NanumSquareNeoOTF-cBd.otf"),
    )
)
sample = renderer.render(
    "ァÐぎ★",
    profile="dotum",
    layout="reference",
    scale=estimate_ui_scale(100, client_height=1080),
)
sample.save("nickname.png")
# sample.image: RGBA 이미지, sample.native_mask: 확대 전 획 마스크
# sample.metadata["text"]: 변경하지 않은 OCR 정답 문자열
```

한 `Renderer`를 재사용하면 폰트와 문자 지원 정보를 다시 읽지 않습니다. 실제 사용되는 폰트 경로만 필요합니다. `dotum`은 `gulim`, `nanum-neo`는 `nanum`과 누락 문자용 `batang`을 사용합니다. 폰트를 자동 다운로드하거나 시스템에서 임의로 대체하지 않습니다.

## 렌더링 범위

| 옵션 | 동작 |
| --- | --- |
| `profile="dotum"` | 돋움 11px의 1비트 래스터를 사용합니다. |
| `profile="nanum-neo"` | 나눔스퀘어 네오 Bold 11px을 우선 사용합니다. 없는 문자는 궁서 12px 1비트 래스터에 가로 1px 굵기를 더해 시도합니다. |
| `layout="metrics"` (기본) | 각 글자의 advance와 공통 baseline으로 배치합니다. 일반 닉네임 생성용 실험 모드입니다. |
| `layout="reference"` | `ァÐぎ★`의 글자 위치와 간격을 원본 화면에 맞춘 비교용 설정입니다. 다른 닉네임을 입력하면 오류가 납니다. |
| `scale` / `--scale` | 폰트 크기를 바꾸지 않고 완성된 래스터를 등방 확대합니다. 유한한 `0 < scale <= 16`을 받습니다. |
| `--ui-percent` | `dfragon`의 경험적 배율 추정식을 적용합니다. `--scale`과 함께 사용할 수 없습니다. |

청록색 `#4BD1FF`, 원래 크기 기준 1px 검은 테두리, 획 바깥 2px 여백을 사용합니다. 확대는 premultiplied alpha의 bilinear 보간이며 출력 가로·세로는 각각 올림합니다. 게임 UI 배경은 생성하지 않습니다. 학습 파이프라인에서 `sample.image`를 원하는 배경에 합성하면 됩니다.

**일반 닉네임의 자간과 대체 폰트 동작은 아직 게임 화면과 검증되지 않았습니다.** `reference` 모드의 원본 크기 획 마스크는 기존 실험과 동일하지만, 확대 후 화면 전체가 픽셀 단위로 같다는 뜻은 아닙니다.

## 닉네임 검사와 dfragon 참고

[`dfragon/packages/lib`](https://github.com/blahaj94/dfragon/tree/919c547f3b0f9c0eb510a9b334eaa469764a7aeb/packages/lib)의 `validateDFNickname`과 `estimateDNFUIScale`을 참고했습니다. 참조 revision은 `919c547f3b0f9c0eb510a9b334eaa469764a7aeb`입니다. 런타임에 TypeScript 패키지를 불러오지는 않습니다.

```python
from dnf_ocr_synth import validate_nickname

result = validate_nickname("ァÐぎ★")
assert result.is_valid and result.byte_length == 8

result = validate_nickname("MyGM", banned_words=["gm"])
assert not result.is_valid
```

- CP949로 손실 없이 표현 가능한 닉네임을 최대 12바이트까지 허용합니다. ASCII는 1바이트, 지원하는 비ASCII 문자는 2바이트입니다.
- 입력이 비어 있거나 공백, 제어문자, 보이지 않는 문자, CP949로 표현할 수 없는 문자가 포함되어 있으면 `is_valid=False`를 반환합니다. 입력한 문자열은 수정하지 않습니다.
- 금칙어는 호출자가 전달한 목록만 대소문자 구분 없이 부분 문자열로 검사합니다. 공식 금칙어 목록이나 이름 중복 검사는 제공하지 않습니다.
- 검사 순서는 빈 값 → 공백 → 문자 지원 → 길이 → 호출자 금칙어입니다. Python API는 `is_valid`, `reason`, `byte_length`를 반환하며 오류 문구는 영어입니다.
- `Renderer.render()`에 입력한 닉네임이 형식에 맞지 않거나 폰트에 없는 문자를 포함하면 오류가 납니다. 금칙어도 검사하려면 렌더링 전에 `validate_nickname()`에 금칙어 목록을 전달합니다.

12바이트 규칙은 `dfragon`과 맞춘 **로컬 형식 정책**이며 현재 게임 서버의 생성 허용 여부를 보장하지 않습니다. Python 표준 `cp949` codec과 참조 저장소의 비ASCII 문자 17,048개가 일치하는지 BMP 전체에서 확인했습니다.

UI 배율은 `H / (H - (H - 600) × UI% / 100)`입니다. `H`는 게임 client 높이 600~1080px의 정수, UI%는 0~100의 유한한 수입니다. 기본 1080px·100%는 1.8배입니다. 이 역시 게임 내부의 공식 산식이 아닌 추정 모델입니다.

## OCR 데이터셋과 서브모듈 사용

학습 프로젝트에서 서브모듈을 추가한 후 Python 패키지로 설치합니다. 부모 저장소가 서브모듈의 commit을 고정하므로 동일 버전을 다시 사용할 수 있습니다.

```bash
git submodule add https://github.com/blahaj94/dnf-ocr-synth.git vendor/dnf-ocr-synth
git submodule update --init --recursive
python -m pip install -e ./vendor/dnf-ocr-synth
```

위의 `renderer`로 여러 닉네임을 생성하고 학습 도구용 JSONL을 만들 수 있습니다. 파일 이름에는 원본 닉네임 대신 순번을 사용합니다.

```python
import json
from pathlib import Path

output = Path("output")
output.mkdir(exist_ok=True)
with (output / "labels.jsonl").open("w", encoding="utf-8") as manifest:
    for index, text in enumerate(["검신", "★검신★", "ァÐぎ★"]):
        sample = renderer.render(text, profile="dotum", scale=1.8)
        filename = f"{index:06d}.png"
        sample.save(output / filename)
        record = {"image": filename, **sample.metadata}
        manifest.write(json.dumps(record, ensure_ascii=False) + "\n")
```

PNG 내부에도 `dnf_ocr_synth`라는 iTXt 키로 JSON을 저장합니다. 원본 `text`, 코드포인트, CP949 길이, profile/layout/배율, 글자별 선택 폰트, 폰트 SHA-256·face index·크기, Pillow·FreeType 버전이 들어갑니다. 로컬 절대 경로는 포함하지 않습니다. PNG를 다른 도구로 다시 저장하면 메타데이터가 사라질 수 있으므로 학습 정답은 JSONL에도 보관합니다.

```python
import json

from PIL import Image

with Image.open("nickname.png") as image:
    metadata = json.loads(image.info["dnf_ocr_synth"])
    assert metadata["text"] == "ァÐぎ★"
```

## 개발 및 검증

[PEP 8](https://peps.python.org/pep-0008/)을 기준으로 들여쓰기 4칸, 79자 줄 길이, snake_case와 표준 import 순서를 사용합니다. Ruff로 스타일을 검사하고 표준 `unittest`로 동작을 확인합니다.

```powershell
python -m pip install -e '.[dev]'
$env:DNF_SYNTH_NANUM = 'C:/path/to/NanumSquareNeoOTF-cBd.otf'
python -m unittest discover -s tests -v
python -m ruff check .
python -m ruff format --check .
python -m build
```

폰트 없는 환경에서도 닉네임 규칙과 입력 오류 테스트는 실행됩니다. Windows 폰트가 없거나 `DNF_SYNTH_NANUM`을 지정하지 않으면 해당 렌더링 테스트만 skip합니다. 픽셀 회귀 검사는 보정에 쓴 폰트 해시와 FreeType 버전이 같을 때 실행하므로 검증 시 skip 사유도 확인해야 합니다.

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
