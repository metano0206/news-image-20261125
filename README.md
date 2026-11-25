# news-image-20261125

[![make.fun · news-image-20261125](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![rank](https://make.fun/badge/news-image-20261125/metano0206/news-image-20261125/rank.svg)](https://make.fun/bounty/news-image-20261125/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![reward](https://make.fun/badge/news-image-20261125/metano0206/news-image-20261125/reward.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)

**The World on Wednesday 25 November 2026, in one picture.** A Python 3.13 program (standard library only) that draws a one-page newspaper poster summing up the day's world news, and writes it to `/output/entry.png`. No network, no clock, no randomness: it runs twice and writes the same bytes both times.

Draft state: the poster's NEWS DATA block currently prints the previous day's (24 November's) stories as a placeholder while 25 November is still unfolding. The final submission swaps that one block — date line and stories — for 25 November's news; nothing else in the program changes.

How it works: `main.py` holds the whole entry. The day's news lives in one clearly marked NEWS DATA block at the top of the file (date line, lead story, four panel stories, one ticker line); below it sits a small software printing press — a hand-authored vector stroke font (each glyph a set of polylines, rasterised by distance-to-segment coverage so the letterforms stay smooth at any size), scanline shapes and drawn scenes (a Kyiv skyline at night, a microchip, a warming globe, the US Capitol, a burning factory), rendered at twice size and averaged down, then encoded as a PNG with zlib.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Without `MAKEFUN_OUTPUT_DIR` the program writes to `/output/entry.png`, as the grader expects. The image is 1024 by 1024 pixels, well under the 1 MiB cap, and takes about six seconds to draw.

License: MIT (see LICENSE).
