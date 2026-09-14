# Style research: what tituli's defaults encode, and why

This is the evidence behind the presets in `tituli/style.py`, `tituli/compose.py` and `tituli/credits.py`. Every number in the code that came from here is named, not inlined.

## Safe areas

SMPTE ST 2046-1 defines the safe action area as 93 % × 93 % and the safe title area as 90 % × 90 % of the production aperture; EBU R95 uses 93 % / 88 % [1][2][3]. tituli uses **90 %** (`TITLE_SAFE`) as the placement region for every block and 93 % (`ACTION_SAFE`) is exported for callers that place graphics rather than type. Netflix's partner guidance is the same 90 % for titles [4].

## Contrast

WCAG 2.x AA: 4.5:1 for normal text, 3:1 for large text (≥ 18 pt regular / ≥ 14 pt bold) [5]. Everything tituli sets on a 1080p frame is "large" by that definition, so 3:1 is the floor and 4.5:1 the target (`WCAG_NORMAL_MIN`). Ink is chosen by relative luminance of the sampled patch; a scrim is added when even the better ink falls short, or when the patch is busy (luminance stddev above `_BUSY_STD`), because a well-contrasted mean does not keep every glyph readable over hatching.

White text on a dark backdrop is the universal default when nothing is known about the picture (rung a): it is what every caption-design guide converges on, and a dark overlay whose opacity is adjusted to the footage is the standard method for difficult backgrounds [6][7].

## Overlay type

Clear sans-serifs — Helvetica Neue, Inter, Roboto, Open Sans — at bold/semi-bold weights for small sizes; a minimum of ~36 px-equivalent at 1080p; lower thirds within the bottom 20 % of frame while leaving room for captions [6][7][8]. tituli: `CAPTION` 0.04 × height (43 px at 1080p, semi-bold), `ATTRIBUTION` 0.02 (22 px — deliberately below the "read" threshold: it is there to credit, not to compete), `LOWER_THIRD_NAME` 0.042 bold.

The bottom of the frame is **not** free on YouTube: the platform draws its subtitle track and control bar there, so a film that ships an SRT collides with its own captions if it uses a lower third. tituli models this as `DELIVERY_RESERVED["youtube"]` (bottom 22 %), which `Frame.place` excludes. That is why the museum-label caption defaults to the **top-left** on a YouTube delivery (the convention the Hamilton film arrived at by collision).

Reveals: 300–500 ms; slower reads as sluggish on a text card [8]. tituli: 0.4–0.45 s.

## Credits

Cards hold ≥ 3 s (the DGA requires the director's card to hold 3 s clean) [9][10]. Crawl speed: 50–70 px/s at 1080p for a two-column roll, 80–120 px/s the comfortable range; reading comfort is ~3–4 words/s [9][10]. tituli: `DEFAULT_CARD_HOLD_S = 3.5`, `DEFAULT_CRAWL_SPEED = 0.09` frame-heights/s (≈ 97 px/s at 1080p).

Typefaces: the overwhelming majority of rolling credits are sans; Helvetica Neue and its derivatives dominate below-the-line crawls; thin strokes shimmer and fine serifs disintegrate in motion, so regular/semi-bold weights at moderate tracking [11][12]. White on black is the industry standard; centred alignment for the roll, with role/name on a shared gutter [10][12]. The classic failure is the dense wall of words — hence section headings as tracked small caps with generous space above, role/name pairs at 1.55 em leading, and prose lines (licence strings) in a lighter, smaller style.

**Credits are a licence surface.** Reusing a CC BY / CC BY-SA image is conditional on the credit, so a roll that silently drops lines past what fits is a rights failure that is invisible to the person responsible for it (a real bug in `braidio.video.credits_card` before braidio#61). tituli paginates onto more cards and raises only when the caller caps the count.

## Taxonomy of on-screen text (what tituli covers)

| kind | what it is | tituli |
|---|---|---|
| title card / opening card | the name of the thing, optional subtitle and kicker | `title_card` |
| intertitle | silent-film narrative card [13] | `intertitle` |
| lower third / chyron | who is speaking, a place [14][15] | `lower_third` |
| caption / museum label | what is on screen and where it came from | `caption` |
| context card / explainer | what the audio assumes and a cold viewer lacks | `note` |
| attribution / source line | the small credit under a caption | `caption(attribution=)` |
| end credits: cards, crawl | [9][10] | `credits_cards`, `credits_crawl` + `video.crawl` |
| kinetic typography / lyric video | text as the picture, in motion [16] | `Layout.staggered` + `frames_to_video`; the lyric vocabulary stays in `muvid` |
| calligram / concrete poem | text whose shape is part of the meaning | `on_path`, `rain`, `in_shape` |
| subtitles (SRT) | timed dialogue | **not tituli** — `mixing` burns SRT |
| bug / watermark (DOG) | a persistent station/brand mark [17] | not built; an anchored `block` on a `TimedOverlay` covers it |
| ticker / crawl (horizontal) | [18] | not built; `video.crawl` is vertical only |
| slate | pre-roll metadata card [19] | `title_card` with `kicker` |

## Fonts and licensing

No typeface ships in the package. Fonts are discovered from the platform directories (macOS, Linux, Windows; `TITULI_FONT_DIRS` prepends more) and resolved through a preference list; the last resort is Aileron, which Pillow embeds and exposes through `ImageFont.load_default(size)` — a real scalable face, so a fontless CI runner renders correctly, if plainer. A project that has licensed a typeface points `TITULI_FONT_DIRS` at it or passes the file path as `family`.

## References

1. [SMPTE ST 2046-1](https://global.ihs.com/doc_detail.cfm?document_name=SMPTE+ST+2046-1&item_s_key=00534999)
2. [NAB — Television Safe Areas Redefined (2010)](https://www.nab.org/xert/scitech/pdfs/tv031510.pdf)
3. [Wikipedia — Safe area (television)](https://en.wikipedia.org/wiki/Safe_area_(television))
4. [Netflix Partner Help — Title Safe and Safe Action Best Practices](https://partnerhelp.netflixstudios.com/hc/en-us/articles/4406208331923-Title-Safe-and-Safe-Action-Best-Practices)
5. [W3C — Understanding WCAG SC 1.4.3 Contrast (Minimum)](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
6. [OpusClip — Best Practices for Video Caption Design](https://www.opus.pro/blog/video-caption-design-placement)
7. [Frame.io — How to Make Lower Third Titles That Don't Suck](https://blog.frame.io/2017/12/04/create-lower-thirds-titles-that-dont-suck/)
8. [Vimeo — Guide to Lower Thirds Design](https://vimeo.com/blog/post/what-is-lower-thirds)
9. [endcredits.pro — How to Make End Credits](https://endcredits.pro/blog/how-to-make-end-credits/)
10. [ScrollX — Film End Credits Format Guide](https://scrollx.io/blog/the-ultimate-guide-to-film-end-credits-format/)
11. [endcredits.pro — Best Fonts for Film Credits](https://endcredits.pro/blog/best-fonts-for-film-credits/)
12. [Font Orbit — Film Credit Font](https://fontorbit.com/film-credit-font/)
13. [Wikipedia — Intertitle](https://en.wikipedia.org/wiki/Intertitle)
14. [Wikipedia — Lower third](https://en.wikipedia.org/wiki/Lower_third)
15. [No Film School — What Is a Chyron?](https://nofilmschool.com/what-is-chyron-in-film)
16. [Linearity — Kinetic typography: the what, why, and how](https://www.linearity.io/blog/kinetic-typography/)
17. [Wikipedia — Digital on-screen graphic](https://en.wikipedia.org/wiki/Digital_on-screen_graphic)
18. [Wikipedia — News ticker](https://en.wikipedia.org/wiki/News_ticker)
19. [Wikipedia — Slate (broadcasting)](https://en.wikipedia.org/wiki/Slate_(broadcasting))
