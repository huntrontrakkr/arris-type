#!/bin/bash
# Rebuild every font, check them, package them.
#
#   tools/rebuild.sh          fonts, pytest, fontbakery, the release zip
#   tools/rebuild.sh extras   and the proofs, specimens and presentation
#
# The static families first, every weight of every family in a process of its
# own (build_fonts.py), then the two variable fonts side by side on the
# machine's cores, then the checks side by side. Logs and a timing line per
# phase in build/scripts/logs/.
cd "$(dirname "$0")/.." || exit 1
L=build/scripts/logs
mkdir -p $L
rm -f $L/*.log build/scripts/*.done
CORES=$(nproc)
T0=$(date +%s)
stamp() { echo "$(( ($(date +%s) - T0) / 60 )) min: $*" | tee -a $L/time.log; }
run() { tag=$1; shift; "$@" > $L/$tag.log 2>&1; echo "rc=$?" >> $L/$tag.log; }

stamp start
# drawings kept from other versions of the engine go (src/arris/font.py's cache)
uv run python -c "from arris.font import prune_cache; print('cache: dropped', prune_cache(), 'old drawings')" >> $L/time.log 2>&1
for fam in "" "watch" "mono" "italic" "mono italic"; do
    tag=$(echo "arris $fam" | tr ' ' '_' | sed 's/_$//')
    run "$tag" uv run python tools/build_fonts.py all $fam &
done
wait
stamp "static families built"

export ARRIS_VF_WORKERS=$(( CORES / 2 ))
run vf uv run python tools/build_vf.py &
run vfital uv run python tools/build_vf.py italic &
wait
stamp "variable fonts built"
date > build/scripts/fonts.done

FB="uvx --quiet --from fontbakery fontbakery check-universal -l WARN"
{ echo "== pytest"; uv run python -m pytest -q tests 2>&1 | tail -n 1; } > $L/post_pytest.log 2>&1 &
{ echo "== fontbakery static"; timeout 1800 $FB build/Arris-Regular.ttf build/Arris-Italic.ttf build/Arris-Black.ttf build/Arris-BlackItalic.ttf 2>&1 | grep -E "ERROR:|FAIL:"; } > $L/post_static.log 2>&1 &
# (both at once: the italic's checks look for its roman)
{ echo "== fontbakery vf"; timeout 3600 $FB "build/Arris[GRAD,WTCH,wght].ttf" "build/Arris-Italic[GRAD,WTCH,wght].ttf" 2>&1 | grep -E "ERROR:|FAIL:" || echo "  (no summary: timed out?)"; } > $L/post_vf.log 2>&1 &
{ echo "== fontbakery mono"; timeout 1800 $FB build/ArrisMono-Regular.ttf build/ArrisMono-Black.ttf 2>&1 | grep -E "ERROR:|FAIL:"; } > $L/post_mono.log 2>&1 &
# the variable fonts everywhere between their masters (on the GPU if there is one)
{ echo "== vf spikes"; timeout 1800 uv run --group gpu python tools/vf_spikes.py 2>&1 | grep -v "Warning\|return lib"; } > $L/post_spikes.log 2>&1 &
wait
cat $L/post_pytest.log $L/post_static.log $L/post_vf.log $L/post_mono.log $L/post_spikes.log > $L/post.log
uv run python tools/package.py >> $L/post.log 2>&1
stamp "checked and packaged"

if [ "$1" = "extras" ]; then
    # the proofs, the specimen's web fonts and pages, the presentation (as
    # build/scripts/rebuild.sh did): review the deck before publishing it
    S1='!"#$%&'"'"'()*+,-./:;<=>?@[\]^_`{|}~ ¡¢£¤¥¦§¨©ª«¬®¯°±' ; S2='²³´µ¶·¸¹º»¼½¾¿×÷–—‘’‚“”„†‡•…‰‹›€™№∞√≠≤≥′″' ; S3='← ↑ → ↓ ↖ ↗ ↘ ↙ ↔ ↕  ˆ ˇ ˘ ˙ ˚ ˜ ˝ ¨ ´ ¯ ¸ ˛'
    {
    uv run python tools/hbspec.py proofs/symbols-weights.png 56 \
     "build/Arris-Regular.ttf::$S1" "build/Arris-Regular.ttf::$S2" "build/Arris-Regular.ttf::$S3" \
     "build/Arris-Bold.ttf::$S1" "build/Arris-Bold.ttf::$S2" \
     "build/Arris-Black.ttf::$S1" "build/Arris-Black.ttf::$S2" "build/Arris-Black.ttf::$S3" \
     "build/Arris-BlackItalic.ttf::$S1" "build/Arris-BlackItalic.ttf::$S2" "build/Arris-BlackItalic.ttf::$S3" 2>&1 | tail -1
    uv run python tools/ligature_sheet.py proofs/mono-ligatures.png 2>&1 | tail -1
    uv run python tools/demo.py proofs/demo.png 2>&1 | tail -1
    uv run python - <<'PY'
from fontTools.ttLib import TTFont
for src, dst in [('build/Arris[GRAD,WTCH,wght].ttf', 'specimen/fonts/Arris-VF.woff2'),
                 ('build/Arris-Italic[GRAD,WTCH,wght].ttf', 'specimen/fonts/Arris-Italic-VF.woff2'),
                 ('build/ArrisMono-Regular.ttf', 'specimen/fonts/ArrisMono-Regular.woff2'),
                 ('build/ArrisMono-Bold.ttf', 'specimen/fonts/ArrisMono-Bold.woff2'),
                 ('build/ArrisMono-Italic.ttf', 'specimen/fonts/ArrisMono-Italic.woff2')]:
    f = TTFont(src); f.flavor = 'woff2'; f.save(dst); print(dst)
PY
    LD_LIBRARY_PATH=$HOME/.local/lib/chromedeps uv run python tools/fox_specimen.py 2>&1 | tail -1
    LD_LIBRARY_PATH=$HOME/.local/lib/chromedeps uv run python tools/magazine_page.py 2>&1 | tail -1
    LD_LIBRARY_PATH=$HOME/.local/lib/chromedeps timeout 3000 uv run python tools/presentation.py 2>&1 | tail -2
    } > $L/extras.log 2>&1
    stamp "extras"
fi
stamp done
