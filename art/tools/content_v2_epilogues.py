"""Epilogue stills of the content v2 side quests (Q10 1962 Ivanka, Q11 1995 Sokolikovsky dvor):
EPILOGUE_10 and EPILOGUE_11 (world_ext epilogue entries 10 and 11; SOKOLIKOVA_YARD.md 6.5, ZUZANA.md 6).

Same prompt assembly as art/tools/cutscenes.py (preamble, numbered references, character briefs, rules, the canonical
style sentence) with the shots defined here, one Nano Banana Pro 2K 16:9 call each behind the content v2 task guard
(asset prefix cutscenes/content_v2/). Likeness: only the approved generated sheets (char refs), never the family
photo. Masters: art/cutscenes/EPILOGUE_1x_v<N>.png; export with
`python cutscenes.py export EPILOGUE_10 <N>` (fit to 1920x1080 WebP).

  python content_v2_epilogues.py prompt EPILOGUE_11
  python content_v2_epilogues.py paint EPILOGUE_10 EPILOGUE_11 [--seed N]
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import json

import content_v2_budget as guard
import cutscene_shots as cs
import cutscenes
import fal_api

cs.shot("EPILOGUE_10", kind="epilogue",
        refs=[(cs.char("ZUZANA", "Zuzana, 7, the first-grade girl from Ivanka pri Dunaji in June 1962")[0],
               "character reference: Zuzana, 7, a first-grade girl from Ivanka pri Dunaji in June 1962"),
              ("item:BELL_FIXED", "prop reference: the repaired brass class hand bell with the turned wooden handle"),
              ("src/game/assets/bg_natural/S32.webp", "place and era reference: the village square of Ivanka pri "
                                                      "Dunaji in June 1962 in our game (houses, colours, light); use "
                                                      "it for the village look, do not copy its composition")],
        shot=("The last day of the school year at the end of June 1962 at the door of a small village primary "
              "school (a generic one-storey whitewashed village school building with a plain wooden double door "
              "standing open, two steps, a window with geraniums; no sign, no lettering). Seven-year-old Zuzana "
              "stands on the top step beside the open door in her navy summer dress with the white round collar, "
              "white knee socks and sandals, and rings the brass hand bell high above her head with her whole arm, "
              "proud and happy, her short light-brown bob swinging. Past her, five or six first-grade children of "
              "1962 run out of the door down the steps into the summer holidays with their satchels flying, "
              "laughing, one boy already tossing his cap. On the beaten path in front of the steps a hopscotch is "
              "chalked. A few paper scraps flutter. Summer trees around."),
        light="Bright warm early-afternoon June sun, the end of the school year; joyful.",
        characters=["ZUZANA"])

cs.shot("EPILOGUE_11", kind="epilogue",
        refs=[("src/game/assets/bg_natural/S69.webp",
               "place reference: the walled courtyard playground between the Sokolikova panel blocks in Dubravka, "
               "Bratislava, in our game (room S69, June 1995): keep its concrete panel walls, the painted panels "
               "with the four shapes, the birch, the blue spruce, the globe lamp, the worn asphalt court with the "
               "chalk hopscotch and the green bench"),
              (cs.char("ZUZANA95", "Zuzana, 40")[0], "character reference: Zuzana, 40, in June 1995"),
              (cs.char("KUBO", "Kubo, 7")[0], "character reference: Kubo, a 7-year-old first-grader of the estate"),
              ("item:BELLCAP", "prop reference: the brass top cap of a child's bicycle bell")],
        shot=("End of June 1995 in the walled courtyard playground: the summer holidays have begun. A cheerful ring "
              "of five children of the housing estate rides round the asphalt court on small bicycles, one behind "
              "the other, ringing their handlebar bells; Kubo leads them on his small red bike with stabiliser "
              "wheels, ringing his bell loudest, mouth wide open with joy. At the green bench at the edge of the "
              "court stands Zuzana, 40, in her navy blouse with the small white round collar and her light beige "
              "skirt, a stick of white chalk in her hand, smiling warmly and watching them; the chalk hopscotch on "
              "the court behind them. The children are seen from the side and from behind as they curve round the "
              "court; nobody looks into the camera."),
        light="Warm late-afternoon June sun with soft long shadows, the birch leaves glowing; a happy, light mood.",
        characters=["ZUZANA95", "KUBO"])


def paint(shot_id: str, seed: int | None) -> str:
    shot = cs.SHOTS[shot_id]
    prompt, paths = cutscenes.build_prompt(shot)
    version = cutscenes.next_version(shot_id)
    out = cutscenes.MASTERS / f"{shot_id}_v{version}.png"
    out.touch()
    asset = f"cutscenes/content_v2/{shot_id}_v{version}"
    arguments = {"prompt": prompt,
                 "image_urls": [fal_api.image_data_uri(p, max_side=1536,
                                                       fmt="JPEG" if p.suffix.lower() in (".jpg", ".jpeg", ".webp")
                                                       else "PNG") for p in paths],
                 "aspect_ratio": "16:9", "resolution": cutscenes.RESOLUTION, "output_format": "png", "num_images": 1}
    if seed is not None:
        arguments["seed"] = seed
    try:
        result = guard.run(cutscenes.MODEL, arguments, asset, cutscenes.PRICE, timeout_s=900)
    except Exception:
        out.unlink(missing_ok=True)
        raise
    out.with_suffix(".result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    fal_api.download(result["images"][0]["url"], out)
    meta = {"shot": shot_id, "model": cutscenes.MODEL, "resolution": cutscenes.RESOLUTION, "usd": cutscenes.PRICE,
            "seed": result.get("seed", seed), "prompt": prompt, "spend_log_asset": asset,
            "references": [str(p.relative_to(cutscenes.ROOT)).replace("\\", "/") for p in paths],
            "at": datetime.datetime.now().isoformat(timespec="seconds")}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["prompt", "paint"])
    ap.add_argument("shots", nargs="+")
    ap.add_argument("--seed", type=int)
    args = ap.parse_args()
    if args.cmd == "prompt":
        for s in args.shots:
            text, paths = cutscenes.build_prompt(cs.SHOTS[s])
            print(text, "\n", [str(p) for p in paths])
        return
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(args.shots)) as pool:
        futures = {pool.submit(paint, s, args.seed): s for s in args.shots}
        for f in concurrent.futures.as_completed(futures):
            try:
                print(futures[f], f.result())
            except Exception as error:
                print(futures[f], "FAILED", error)


if __name__ == "__main__":
    main()
