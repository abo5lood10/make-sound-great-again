# Third-party components

- **Audiowide** font: SIL Open Font License 1.1 (`msga/web/fonts/OFL-Audiowide.txt`).
- **yt-dlp**: The Unlicense, https://github.com/yt-dlp/yt-dlp
- **pywebview**: BSD-3-Clause, https://github.com/r0x0r/pywebview
- **FFmpeg** (bundled in the Windows build only): an LGPL-2.1+ build (`--disable-gpl`) from
  https://github.com/BtbN/FFmpeg-Builds . FFmpeg source code and licence: https://ffmpeg.org/ and
  https://github.com/FFmpeg/FFmpeg . You can replace the bundled `ffmpeg.exe` / `ffprobe.exe` (in the `bin` folder)
  with any other build.

- **RNNoise noise-suppression models** (`msga/models/mp.rnnn`, `bd.rnnn`): trained models from
  https://github.com/GregorR/rnnoise-models (the repository states they are not subject to copyright), based on
  RNNoise by Xiph.Org (BSD-3-Clause) https://github.com/xiph/rnnoise . They are applied through ffmpeg's `arnndn` filter.

- **Thmanyah (ثمانية) font** © thmanyah Publishing and Distribution: embedded only in the packaged Windows build, in
  obfuscated form, as its licence permits for compiled/packaged/obfuscated software products. The font files are not
  part of this repository, are not available for download here, and may only be obtained from https://thmanyah.com .
